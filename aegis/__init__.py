"""Project Aegis — The Sovereign Symbiote.

A localized, hardware-bound algorithmic execution daemon. Aegis acts as the
user's "digital hands": it translates high-level instructions into physical GUI
actuations while strictly negotiating the cost of those actions against the
machine's physical limits (Tier 1), routing every decision through the
Contextual Equivalence Engine (Tier 2) and the PIPNB Governance Plane (Tier 3).

Nothing here ever calls a cloud inference API. Sovereignty is the point.
"""

from aegis.models import (
    Decision,
    DecisionAction,
    Instruction,
    ResourceCost,
    TelemetrySnapshot,
    Zone,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Decision",
    "DecisionAction",
    "Instruction",
    "ResourceCost",
    "TelemetrySnapshot",
    "Zone",
]
