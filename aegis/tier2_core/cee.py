"""The Contextual Equivalence Engine (CEE) — the algorithmic heart of Aegis.

Aegis treats every instruction as a localized market negotiation: a *Trade*
between what it must spend (Cost) and what it will achieve (Utility), penalised
by the Governor's ideology (Weight). Before acting it runs the equivalence proof:

                       Utility_Target
        ρ  =  ────────────────────────────────
               Cost_Hardware · Weight_Ideology

    ρ ≥ 1.0          -> EXECUTE   (the trade is mathematically viable)
    negotiate ≤ ρ <1 -> NEGOTIATE (pivot to a cheaper headless method)
    ρ < negotiate    -> DEFER     (too expensive; retry when conditions improve)

Governance (Tier 3) can override an otherwise-viable ρ with a hard VETO, and the
zone gate can escalate a viable trade to CONSULT (Zone 2) or PENDING_APPROVAL
(Zone 3).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from aegis.models import (
    Decision,
    DecisionAction,
    Instruction,
    TelemetrySnapshot,
)
from aegis.tier3_governance.pipnb import GovernancePlane
from aegis.tier3_governance.zones import ZoneGate


class CEEConfig(BaseModel):
    """Tunable weights and thresholds for the Trade computation."""

    execute_threshold: float = Field(1.0, gt=0, description="ρ at/above which the trade executes.")
    negotiate_threshold: float = Field(0.7, gt=0, description="ρ at/above which the trade is renegotiated.")

    # Relative emphasis of each scarcity dimension inside Cost_Hardware.
    w_ram: float = Field(1.0, ge=0)
    w_time: float = Field(1.0, ge=0)
    w_cpu: float = Field(0.8, ge=0)
    w_gpu: float = Field(1.2, ge=0)
    w_battery: float = Field(1.5, ge=0)

    # Floor so ρ never divides by ~0 for a free action.
    min_cost: float = Field(0.05, gt=0)


class ContextualEquivalenceEngine:
    """Computes the equivalence ratio ρ and renders a governed :class:`Decision`."""

    def __init__(
        self,
        governance: GovernancePlane | None = None,
        config: CEEConfig | None = None,
        zone_gate: ZoneGate | None = None,
    ) -> None:
        self.governance = governance or GovernancePlane()
        self.config = config or CEEConfig()
        self.zone_gate = zone_gate or ZoneGate()

    # ------------------------------------------------------------------ #
    # Cost_Hardware
    # ------------------------------------------------------------------ #
    def hardware_cost(self, instruction: Instruction, telemetry: TelemetrySnapshot) -> tuple[float, list[str]]:
        """Cost = weighted average of fractional resource pressure, amplified by
        live scarcity, taken over only the resources the task actually uses.

        A 2GB action is cheap on an idle 16GB box and ruinous on a swapping
        laptop, because each dimension blends *demand* (fraction of the budget)
        with *live scarcity* (how loaded that resource already is). Averaging over
        active dimensions keeps the result interpretable in a 0..~2 band: ~0 is
        free, ~1 is "spends the whole budget under contention".
        """
        cfg = self.config
        cost = instruction.cost
        budgets = self.governance.budgets
        notes: list[str] = []

        # Each entry: (weight, unit_pressure, note). unit_pressure ≈ fraction of
        # the relevant budget/capacity × scarcity multiplier.
        dims: list[tuple[float, float]] = []

        if cost.ram_gb > 0 and budgets.max_ram_gb > 0:
            frac = cost.ram_gb / budgets.max_ram_gb
            scarcity = 1.0 + telemetry.ram_percent / 100.0
            unit = frac * scarcity
            dims.append((cfg.w_ram, unit))
            notes.append(f"RAM {cost.ram_gb:g}/{budgets.max_ram_gb:g}GB @ {telemetry.ram_percent:g}% → {unit:.2f}")

        if cost.est_seconds > 0:
            unit = cost.est_seconds / max(budgets.max_seconds, 1.0)
            dims.append((cfg.w_time, unit))
            notes.append(f"time {cost.est_seconds:g}/{budgets.max_seconds:g}s → {unit:.2f}")

        if cost.cpu_load > 0:
            unit = (cost.cpu_load / 100.0) * (1.0 + telemetry.cpu_percent / 100.0)
            dims.append((cfg.w_cpu, unit))
            notes.append(f"cpu +{cost.cpu_load:g}% @ {telemetry.cpu_percent:g}% load → {unit:.2f}")

        if cost.gpu_load > 0:
            unit = (cost.gpu_load / 100.0) * (1.0 + telemetry.gpu_percent / 100.0)
            dims.append((cfg.w_gpu, unit))
            notes.append(f"gpu +{cost.gpu_load:g}% @ {telemetry.gpu_percent:g}% load → {unit:.2f}")

        if cost.battery_drain_pct > 0:
            urgency = 1.0
            if not telemetry.battery_plugged and telemetry.battery_percent is not None:
                urgency = 1.0 + (100.0 - telemetry.battery_percent) / 100.0
            unit = (cost.battery_drain_pct / 100.0) * urgency
            dims.append((cfg.w_battery, unit))
            notes.append(f"battery {cost.battery_drain_pct:g}% (urgency ×{urgency:.2f}) → {unit:.2f}")

        if not dims:
            return cfg.min_cost, ["no measurable resource demand"]

        weight_sum = sum(w for w, _ in dims)
        total = sum(w * u for w, u in dims) / weight_sum
        return max(total, cfg.min_cost), notes

    # ------------------------------------------------------------------ #
    # The Trade
    # ------------------------------------------------------------------ #
    def evaluate(self, instruction: Instruction, telemetry: TelemetrySnapshot) -> Decision:
        cfg = self.config

        verdict = self.governance.evaluate(
            instruction,
            thermal_headroom=telemetry.thermal_headroom,
            battery_percent=telemetry.battery_percent,
            battery_plugged=telemetry.battery_plugged,
        )

        cost, cost_notes = self.hardware_cost(instruction, telemetry)
        weight = verdict.ideological_weight
        utility = instruction.utility
        ratio = utility / (cost * weight)

        reasons: list[str] = []
        reasons += [f"cost: {n}" for n in cost_notes]
        reasons += [f"weight: {n}" for n in verdict.weight_notes]

        # 1) Hard governance veto trumps everything.
        if not verdict.cleared:
            reasons = [f"VETO: {v}" for v in verdict.hard_vetoes] + reasons
            return Decision(
                instruction_id=instruction.id,
                action=DecisionAction.VETO,
                ratio=ratio,
                utility=utility,
                cost=cost,
                ideological_weight=weight,
                zone=instruction.zone,
                reasons=reasons,
            )

        # 2) The equivalence proof.
        if ratio >= cfg.execute_threshold:
            base_action = DecisionAction.EXECUTE
            reasons.append(f"ρ={ratio:.2f} ≥ {cfg.execute_threshold:g}: trade is viable")
        elif ratio >= cfg.negotiate_threshold:
            base_action = DecisionAction.NEGOTIATE
            reasons.append(
                f"{cfg.negotiate_threshold:g} ≤ ρ={ratio:.2f} < {cfg.execute_threshold:g}: marginal — renegotiate"
            )
        else:
            reasons.append(f"ρ={ratio:.2f} < {cfg.negotiate_threshold:g}: trade too expensive — defer")
            return Decision(
                instruction_id=instruction.id,
                action=DecisionAction.DEFER,
                ratio=ratio,
                utility=utility,
                cost=cost,
                ideological_weight=weight,
                zone=instruction.zone,
                reasons=reasons,
                suggested_alternative=self._cheaper_alternative(instruction),
            )

        # 3) Zone escalation on top of a viable trade.
        outcome = self.zone_gate.escalate(instruction, base_action)
        reasons += outcome.reasons

        suggested = None
        if outcome.action is DecisionAction.NEGOTIATE:
            suggested = self._cheaper_alternative(instruction)

        return Decision(
            instruction_id=instruction.id,
            action=outcome.action,
            ratio=ratio,
            utility=utility,
            cost=cost,
            ideological_weight=weight,
            zone=instruction.zone,
            reasons=reasons,
            suggested_alternative=suggested,
        )

    @staticmethod
    def _cheaper_alternative(instruction: Instruction) -> str:
        """Propose a headless pivot when the GUI trade is too expensive."""
        if instruction.cost.gpu_load > 0:
            return "Defer GPU work until utilisation drops, or run a CPU/headless variant."
        return (
            "Pivot to a headless background script (file/CLI manipulation) instead of "
            "driving a heavy GUI application."
        )
