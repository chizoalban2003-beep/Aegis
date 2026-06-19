from aegis.models import Decision, DecisionAction, TelemetrySnapshot, Zone


def test_zone_labels():
    assert Zone.USER_SPACE.label.startswith("Zone 1")
    assert Zone.SYSTEM_SPACE.label.startswith("Zone 2")
    assert Zone.KERNEL_CORE.label.startswith("Zone 3")


def test_thermal_headroom_bounds():
    assert TelemetrySnapshot(cpu_temp_c=None).thermal_headroom == 1.0
    assert TelemetrySnapshot(cpu_temp_c=0).thermal_headroom == 1.0
    assert TelemetrySnapshot(cpu_temp_c=90).thermal_headroom == 0.0
    assert TelemetrySnapshot(cpu_temp_c=120).thermal_headroom == 0.0
    mid = TelemetrySnapshot(cpu_temp_c=45).thermal_headroom
    assert 0.49 < mid < 0.51


def test_decision_viable_and_summary():
    d = Decision(
        instruction_id="x",
        action=DecisionAction.EXECUTE,
        ratio=1.5,
        utility=0.9,
        cost=0.4,
        ideological_weight=1.0,
        zone=Zone.USER_SPACE,
    )
    assert d.viable is True
    assert "EXECUTE" in d.summary()
    assert Decision(
        instruction_id="x",
        action=DecisionAction.DEFER,
        ratio=0.2,
        utility=0.1,
        cost=0.5,
        ideological_weight=1.0,
        zone=Zone.USER_SPACE,
    ).viable is False
