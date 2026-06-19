"""Phase 2 demonstration — the Contextual Equivalence Engine in action.

Scenario (straight from the build brief):

    Instruction: "Calculate the model performance of the app immediately post-game."

We pass it through the CEE twice:

  1. The GPU is MAXED OUT (post-game render still resolving). The Trade is too
     expensive — ρ drops below 1.0 — so Aegis DEFERS the task to respect the
     Budget and thermal policy instead of blindly executing.

  2. Moments later the GPU frees up. The same instruction now clears the Trade
     and EXECUTES.

Run:  python examples/phase2_cee_demo.py
"""

from __future__ import annotations

from aegis.models import Instruction, ResourceCost, TelemetrySnapshot, Zone
from aegis.tier2_core.cee import ContextualEquivalenceEngine
from aegis.tier3_governance.pipnb import Budgets, GovernancePlane


def main() -> None:
    # The Governor's constitution: tight resource budget, thermal-aware ideology.
    governance = GovernancePlane(budgets=Budgets(max_ram_gb=4.0, max_seconds=120.0))
    cee = ContextualEquivalenceEngine(governance=governance)

    instruction = Instruction(
        description="Calculate the model performance of the app immediately post-game",
        zone=Zone.USER_SPACE,
        utility=0.9,
        cost=ResourceCost(ram_gb=2.0, est_seconds=45.0, cpu_load=30.0, gpu_load=70.0),
    )

    print("=" * 72)
    print("STATE 1 — GPU maxed out right after the match (hot, contended)")
    print("=" * 72)
    hot = TelemetrySnapshot(
        cpu_percent=85.0,
        cpu_temp_c=84.0,
        ram_percent=72.0,
        ram_available_gb=3.0,
        ram_total_gb=16.0,
        gpu_percent=99.0,
        battery_percent=40.0,
        battery_plugged=False,
    )
    d1 = cee.evaluate(instruction, hot)
    print(d1.summary())
    for r in d1.reasons:
        print(f"  - {r}")
    if d1.suggested_alternative:
        print(f"  ↪ {d1.suggested_alternative}")

    print()
    print("=" * 72)
    print("STATE 2 — render finished, GPU idle, machine cool and plugged in")
    print("=" * 72)
    cool = TelemetrySnapshot(
        cpu_percent=15.0,
        cpu_temp_c=45.0,
        ram_percent=40.0,
        ram_available_gb=9.0,
        ram_total_gb=16.0,
        gpu_percent=5.0,
        battery_percent=95.0,
        battery_plugged=True,
    )
    d2 = cee.evaluate(instruction, cool)
    print(d2.summary())
    for r in d2.reasons:
        print(f"  - {r}")

    print()
    print("Outcome: Aegis respected the Budget under contention (DEFER), then")
    print("executed the very same trade once the hardware reality changed.")


if __name__ == "__main__":
    main()
