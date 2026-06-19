"""Tier 1 — Hardware Symbiosis Layer (The Senses).

The lowest level. Read-only access to the physical and digital realities of the
machine: the Telemetry Hub (CPU/RAM/battery/GPU), the OS Accessibility Bridge
(screen state), the Hardware Watchdog failsafe, and the actuation backends that
physically drive mouse/keyboard.

In production the hot path here would be a compiled language (Rust) for safety
and latency; this reference implementation uses ``psutil`` so it is portable and
immediately runnable. See ``ARCHITECTURE.md`` for the hybrid rationale.
"""

from aegis.tier1_senses.telemetry import TelemetryHub
from aegis.tier1_senses.watchdog import HardwareWatchdog

__all__ = ["TelemetryHub", "HardwareWatchdog"]
