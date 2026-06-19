from aegis.models import DecisionAction, Instruction, Zone
from aegis.tier3_governance.zones import ZoneGate


def test_zone1_passes_through():
    gate = ZoneGate()
    ins = Instruction(description="x", zone=Zone.USER_SPACE)
    assert gate.escalate(ins, DecisionAction.EXECUTE).action is DecisionAction.EXECUTE


def test_zone2_consults():
    gate = ZoneGate()
    ins = Instruction(description="x", zone=Zone.SYSTEM_SPACE)
    assert gate.escalate(ins, DecisionAction.EXECUTE).action is DecisionAction.CONSULT


def test_zone3_requires_valid_token():
    gate = ZoneGate(approval_secret="secret")
    ins = Instruction(description="x", zone=Zone.KERNEL_CORE)
    assert gate.escalate(ins, DecisionAction.EXECUTE).action is DecisionAction.PENDING_APPROVAL

    ins.approval_token = gate.issue_token(ins)
    assert gate.escalate(ins, DecisionAction.EXECUTE).action is DecisionAction.EXECUTE


def test_zone3_rejects_forged_token():
    gate = ZoneGate(approval_secret="secret")
    ins = Instruction(description="x", zone=Zone.KERNEL_CORE, approval_token="deadbeef")
    assert gate.escalate(ins, DecisionAction.EXECUTE).action is DecisionAction.PENDING_APPROVAL
