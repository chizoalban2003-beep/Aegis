"""Clinical depth zones — execution authority by proximity to the OS core.

The zone gate runs *after* the CEE has produced a viable ratio. It decides
whether a viable trade may execute silently, must be proposed to the Governor,
or is hard-locked behind cryptographic approval.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field

from aegis.models import DecisionAction, Instruction, Zone


@dataclass
class ZoneOutcome:
    action: DecisionAction
    reasons: list[str] = field(default_factory=list)


class ZoneGate:
    """Maps a (zone, viability) pair to the final escalation behaviour."""

    def __init__(self, approval_secret: str = "aegis-governor-key") -> None:
        # In a real deployment this is a hardware-backed key; here it stands in
        # for the Governor's cryptographic authority used to sign Zone 3 actions.
        self._secret = approval_secret.encode("utf-8")

    def issue_token(self, instruction: Instruction) -> str:
        """The Governor signs an instruction id to authorise a Zone 3 action."""
        return hmac.new(self._secret, instruction.id.encode(), hashlib.sha256).hexdigest()

    def _token_valid(self, instruction: Instruction) -> bool:
        if not instruction.approval_token:
            return False
        return hmac.compare_digest(instruction.approval_token, self.issue_token(instruction))

    def escalate(self, instruction: Instruction, viable_action: DecisionAction) -> ZoneOutcome:
        """Apply zone authority on top of a CEE verdict.

        ``viable_action`` is what the CEE wants (EXECUTE / NEGOTIATE). Non-viable
        verdicts are passed straight through unchanged by the caller.
        """
        zone = instruction.zone

        if zone is Zone.USER_SPACE:
            return ZoneOutcome(viable_action, ["Zone 1: total autonomy — execute and log silently"])

        if zone is Zone.SYSTEM_SPACE:
            return ZoneOutcome(
                DecisionAction.CONSULT,
                ["Zone 2: consultative — proposing the trade to the Governor"],
            )

        # Zone 3 — kernel/core hard lock.
        if self._token_valid(instruction):
            return ZoneOutcome(
                viable_action,
                ["Zone 3: valid cryptographic approval present — lock released"],
            )
        return ZoneOutcome(
            DecisionAction.PENDING_APPROVAL,
            ["Zone 3: hard lock — manual cryptographic Governor approval required"],
        )
