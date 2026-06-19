"""The "DNA" memory — a localized, encrypted store that crystallises around the
Governor's workflow. Records every trade, UI navigation, and Zone-2 approval so
Aegis learns how the Governor values time vs. machine resources over time.
"""

from aegis.tier2_core.dna.store import CrystalRecord, DNAStore

__all__ = ["CrystalRecord", "DNAStore"]
