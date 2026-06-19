"""The Aegis daemon — orchestrates the three tiers around a single instruction.

Flow for ``submit(instruction)``:

    Tier 1  sample live telemetry  ──►  feed the Watchdog (failsafe)
    Tier 3  Governance Plane       ──►  hard vetoes + ideological weight
    Tier 2  CEE                    ──►  the Trade (ρ) + zone escalation
            ───────────────────────────────────────────────────────────
            EXECUTE     -> actuate (or headless pivot) and crystallise
            NEGOTIATE   -> headless pivot if possible
            CONSULT     -> post a Zone-2 proposal to Notifications
            PENDING/VETO/DEFER -> log to the Daily Digest
"""

from __future__ import annotations

from typing import Optional

from aegis.config import AegisConfig
from aegis.models import Decision, DecisionAction, Instruction, TelemetrySnapshot
from aegis.tier1_senses.actuation.base import Actuator
from aegis.tier1_senses.actuation.dry_run import DryRunActuator
from aegis.tier1_senses.telemetry import TelemetryHub
from aegis.tier1_senses.watchdog import HardwareWatchdog
from aegis.tier2_core.cee import ContextualEquivalenceEngine
from aegis.tier2_core.dna.store import CrystalRecord, DNAStore, XorCipher
from aegis.headless.fallback import HeadlessRunner


class AegisDaemon:
    def __init__(
        self,
        config: Optional[AegisConfig] = None,
        *,
        actuator: Optional[Actuator] = None,
        dna: Optional[DNAStore] = None,
    ) -> None:
        self.config = config or AegisConfig()
        self.config.ensure_dirs()

        # Tier 1
        self.telemetry = TelemetryHub(interval=self.config.telemetry_interval)
        self.watchdog = HardwareWatchdog(on_trip=self._on_watchdog_trip)
        self.actuator = actuator or DryRunActuator()
        self.headless = HeadlessRunner(self.config.headless_root)

        # Tier 2
        self.cee = ContextualEquivalenceEngine(
            governance=self.config.governance, config=self.config.cee
        )
        self.dna = dna or DNAStore(self.config.dna_path, cipher=XorCipher(self.config.dna_key))

        # Tier 3 lives inside self.config.governance, consumed by the CEE.
        self.telemetry.subscribe(self.watchdog.inspect)

    # ------------------------------------------------------------------ #
    def _on_watchdog_trip(self, reason: str) -> None:
        self.config.governance.notifications.post(
            f"WATCHDOG TRIPPED — halting actuation: {reason}", level="error"
        )

    @property
    def notifications(self):
        return self.config.governance.notifications

    # ------------------------------------------------------------------ #
    def evaluate(self, instruction: Instruction, telemetry: Optional[TelemetrySnapshot] = None) -> Decision:
        snap = telemetry or self.telemetry.sample()
        return self.cee.evaluate(instruction, snap)

    def submit(self, instruction: Instruction, telemetry: Optional[TelemetrySnapshot] = None) -> Decision:
        snap = telemetry or self.telemetry.sample()
        self.watchdog.inspect(snap)

        if self.watchdog.tripped:
            decision = Decision(
                instruction_id=instruction.id,
                action=DecisionAction.VETO,
                ratio=0.0,
                utility=instruction.utility,
                cost=float("inf"),
                ideological_weight=1.0,
                zone=instruction.zone,
                reasons=[f"VETO: watchdog tripped ({self.watchdog.reason})"],
            )
            self.notifications.post(decision.summary(), level="error", instruction_id=instruction.id)
            return decision

        decision = self.cee.evaluate(instruction, snap)
        self._react(instruction, decision)
        return decision

    # ------------------------------------------------------------------ #
    def _react(self, instruction: Instruction, decision: Decision) -> None:
        notes = self.notifications
        if decision.action is DecisionAction.EXECUTE:
            notes.post(f"Executed: {instruction.description}", level="info", instruction_id=instruction.id)
            self._crystallise(instruction, decision, "trade")
        elif decision.action is DecisionAction.NEGOTIATE:
            notes.post(
                f"Renegotiated via headless pivot: {decision.suggested_alternative}",
                level="info",
                instruction_id=instruction.id,
            )
            self._crystallise(instruction, decision, "trade")
        elif decision.action is DecisionAction.CONSULT:
            notes.post(
                f"Zone-2 proposal awaiting Governor approval: {instruction.description} "
                f"({decision.summary()})",
                level="proposal",
                instruction_id=instruction.id,
            )
        elif decision.action is DecisionAction.PENDING_APPROVAL:
            notes.post(
                f"Zone-3 hard lock — cryptographic approval required: {instruction.description}",
                level="warning",
                instruction_id=instruction.id,
            )
        else:  # DEFER / VETO
            notes.post(decision.summary(), level="warning", instruction_id=instruction.id)

    def _crystallise(self, instruction: Instruction, decision: Decision, kind: str) -> None:
        self.dna.remember(
            CrystalRecord(
                kind=kind,
                description=instruction.description,
                payload={
                    "action": decision.action.value,
                    "ratio": decision.ratio,
                    "zone": int(decision.zone),
                },
            )
        )

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self.telemetry.start()

    def stop(self) -> None:
        self.telemetry.stop()
        self.dna.close()
