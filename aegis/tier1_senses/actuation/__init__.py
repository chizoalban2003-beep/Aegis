"""Actuation backends — Aegis's physical hands (mouse/keyboard)."""

from aegis.tier1_senses.actuation.base import Actuator, ActuationResult
from aegis.tier1_senses.actuation.dry_run import DryRunActuator

__all__ = ["Actuator", "ActuationResult", "DryRunActuator"]
