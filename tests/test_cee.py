import pytest

from aegis.models import DecisionAction, Instruction, ResourceCost, TelemetrySnapshot, Zone
from aegis.tier2_core.cee import ContextualEquivalenceEngine
from aegis.tier3_governance.pipnb import Budgets, GovernancePlane


def idle() -> TelemetrySnapshot:
    return TelemetrySnapshot(
        cpu_percent=10, cpu_temp_c=45, ram_percent=30, ram_available_gb=12,
        ram_total_gb=16, gpu_percent=5, battery_percent=95, battery_plugged=True,
    )


def maxed() -> TelemetrySnapshot:
    return TelemetrySnapshot(
        cpu_percent=85, cpu_temp_c=84, ram_percent=72, ram_available_gb=3,
        ram_total_gb=16, gpu_percent=99, battery_percent=40, battery_plugged=False,
    )


def test_high_utility_idle_executes():
    cee = ContextualEquivalenceEngine()
    ins = Instruction(description="quick task", utility=0.9, cost=ResourceCost(ram_gb=1, est_seconds=10, cpu_load=10))
    d = cee.evaluate(ins, idle())
    assert d.action is DecisionAction.EXECUTE
    assert d.ratio >= 1.0


def test_gpu_maxed_defers_same_task():
    """The Phase 2 scenario: GPU-bound task defers when contended, executes when idle."""
    cee = ContextualEquivalenceEngine(
        governance=GovernancePlane(budgets=Budgets(max_ram_gb=4.0, max_seconds=120.0))
    )
    ins = Instruction(
        description="Calculate the model performance immediately post-game",
        utility=0.9,
        cost=ResourceCost(ram_gb=2, est_seconds=45, cpu_load=30, gpu_load=70),
    )
    hot = cee.evaluate(ins, maxed())
    cool = cee.evaluate(ins, idle())
    assert hot.action is DecisionAction.DEFER
    assert cool.action is DecisionAction.EXECUTE
    assert hot.ratio < cool.ratio


def test_negotiate_band():
    cee = ContextualEquivalenceEngine()
    # Tune utility so ρ lands in [0.7, 1.0).
    ins = Instruction(description="marginal", utility=0.2, cost=ResourceCost(ram_gb=1, est_seconds=10, cpu_load=10))
    d = cee.evaluate(ins, idle())
    assert d.action is DecisionAction.NEGOTIATE
    assert 0.7 <= d.ratio < 1.0
    assert d.suggested_alternative


def test_cloud_request_is_vetoed():
    cee = ContextualEquivalenceEngine()
    ins = Instruction(description="cloud infer", utility=5.0, requires_cloud=True)
    d = cee.evaluate(ins, idle())
    assert d.action is DecisionAction.VETO
    assert any("forbid_cloud" in r for r in d.reasons)


def test_budget_overrun_is_vetoed_even_if_useful():
    cee = ContextualEquivalenceEngine(governance=GovernancePlane(budgets=Budgets(max_ram_gb=4)))
    ins = Instruction(description="ram hog", utility=10.0, cost=ResourceCost(ram_gb=64))
    d = cee.evaluate(ins, idle())
    assert d.action is DecisionAction.VETO


@pytest.mark.parametrize("zone,expected", [
    (Zone.USER_SPACE, DecisionAction.EXECUTE),
    (Zone.SYSTEM_SPACE, DecisionAction.CONSULT),
    (Zone.KERNEL_CORE, DecisionAction.PENDING_APPROVAL),
])
def test_zone_escalation_on_viable_trade(zone, expected):
    cee = ContextualEquivalenceEngine()
    ins = Instruction(description="t", zone=zone, utility=0.9, cost=ResourceCost(ram_gb=1, est_seconds=5, cpu_load=5))
    assert cee.evaluate(ins, idle()).action is expected
