"""The Hardware Watchdog — a hard-coded failsafe.

If Aegis's own activity drives the machine into a dangerous thermal/pressure
state, the Watchdog trips and halts the daemon. It is intentionally dumb and
sits *below* the CEE: no trade can ever talk it out of protecting the hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from aegis.models import TelemetrySnapshot


@dataclass
class WatchdogLimits:
    max_cpu_temp_c: float = 95.0
    max_ram_percent: float = 97.0
    sustained_breaches: int = 3  # consecutive breaches before tripping


class HardwareWatchdog:
    def __init__(self, limits: Optional[WatchdogLimits] = None, on_trip: Optional[Callable[[str], None]] = None) -> None:
        self.limits = limits or WatchdogLimits()
        self._on_trip = on_trip
        self._breaches = 0
        self.tripped = False
        self.reason: Optional[str] = None

    def reset(self) -> None:
        self._breaches = 0
        self.tripped = False
        self.reason = None

    def inspect(self, telemetry: TelemetrySnapshot) -> bool:
        """Feed a snapshot. Returns True if the watchdog is currently tripped."""
        breach: Optional[str] = None
        if telemetry.cpu_temp_c is not None and telemetry.cpu_temp_c >= self.limits.max_cpu_temp_c:
            breach = f"CPU temp {telemetry.cpu_temp_c:.1f}°C ≥ {self.limits.max_cpu_temp_c:.1f}°C"
        elif telemetry.ram_percent >= self.limits.max_ram_percent:
            breach = f"RAM pressure {telemetry.ram_percent:.1f}% ≥ {self.limits.max_ram_percent:.1f}%"

        if breach:
            self._breaches += 1
            if self._breaches >= self.limits.sustained_breaches and not self.tripped:
                self.tripped = True
                self.reason = breach
                if self._on_trip:
                    self._on_trip(breach)
        else:
            self._breaches = 0
        return self.tripped
