from aegis.models import Instruction, ResourceCost
from aegis.tier3_governance.pipnb import (
    Budgets,
    GovernancePlane,
    Permissions,
    Policies,
)


def test_permissions_deny_wins():
    perms = Permissions(allow_paths=["~/Documents/**"], deny_paths=["~/.ssh/**"])
    ins = Instruction(description="read key", target_paths=["~/.ssh/id_rsa"])
    assert perms.violations(ins)


def test_permissions_allow_list():
    perms = Permissions(allow_paths=["~/Documents/**"], deny_paths=[])
    ok = Instruction(description="ok", target_paths=["~/Documents/report.csv"])
    bad = Instruction(description="bad", target_paths=["~/Pictures/secret.png"])
    assert perms.violations(ok) == []
    assert perms.violations(bad)


def test_policy_cloud_hard_veto():
    pol = Policies(forbid_cloud=True)
    ins = Instruction(description="upload", requires_cloud=True)
    assert pol.hard_vetoes(ins)
    assert Policies(forbid_cloud=False).hard_vetoes(ins) == []


def test_ideological_weight_privacy_and_thermal():
    pol = Policies(privacy_first=True, privacy_weight=2.5, thermal_priority=True, thermal_weight=2.0)
    ins = Instruction(description="x", touches_personal_data=True)
    cool_w, _ = pol.ideological_weight(ins, thermal_headroom=1.0)
    hot_w, _ = pol.ideological_weight(ins, thermal_headroom=0.0)
    assert cool_w == 2.5  # privacy only when cool
    assert hot_w == 2.5 * 2.0  # privacy × full thermal penalty


def test_budget_violations():
    b = Budgets(max_ram_gb=4, max_seconds=120, max_battery_drain_pct=15, min_battery_to_act_pct=10)
    over = Instruction(description="huge", cost=ResourceCost(ram_gb=8, est_seconds=200, battery_drain_pct=50))
    assert len(b.violations(over, battery_percent=90, plugged=True)) == 3
    low = Instruction(description="x", cost=ResourceCost(ram_gb=1))
    assert b.violations(low, battery_percent=5, plugged=False)
    assert b.violations(low, battery_percent=5, plugged=True) == []


def test_governance_plane_clears_clean_instruction():
    plane = GovernancePlane()
    ins = Instruction(description="organise", target_paths=["~/Documents/a.txt"])
    verdict = plane.evaluate(ins)
    assert verdict.cleared is True
    assert verdict.ideological_weight >= 1.0
