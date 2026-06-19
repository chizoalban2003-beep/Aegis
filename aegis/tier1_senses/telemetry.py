"""System Telemetry Hub — polls the machine's physical reality.

Wraps ``psutil`` (cross-platform) and degrades gracefully when a sensor is
unavailable (e.g. no battery on a desktop, no temperature sensor in a VM/CI).
GPU utilisation is best-effort: NVML if present, otherwise reported as 0 and
treated as "unknown / idle" by the CEE.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from aegis.models import TelemetrySnapshot

try:
    import psutil
except Exception:  # pragma: no cover - psutil is a hard dep, but stay defensive
    psutil = None  # type: ignore[assignment]


_BYTES_PER_GIB = 1024 ** 3


def _read_cpu_temp() -> Optional[float]:
    if psutil is None or not hasattr(psutil, "sensors_temperatures"):
        return None
    try:
        temps = psutil.sensors_temperatures()  # type: ignore[attr-defined]
    except Exception:
        return None
    if not temps:
        return None
    # Prefer common package sensors; otherwise take the hottest reading we find.
    preferred = ("coretemp", "k10temp", "cpu_thermal", "acpitz")
    candidates: list[float] = []
    for name, entries in temps.items():
        for entry in entries:
            if entry.current is None:
                continue
            if name in preferred:
                candidates.append(entry.current)
    if not candidates:
        for entries in temps.values():
            candidates += [e.current for e in entries if e.current is not None]
    return max(candidates) if candidates else None


def _read_gpu_percent() -> float:
    """Best-effort GPU utilisation via NVML; 0.0 if unavailable."""
    try:  # pragma: no cover - depends on optional hardware/driver
        import pynvml  # type: ignore

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        pynvml.nvmlShutdown()
        return float(util.gpu)
    except Exception:
        return 0.0


class TelemetryHub:
    """Samples telemetry on demand and (optionally) streams it on a background
    worker thread to subscribers such as the CEE and the Watchdog.
    """

    def __init__(self, interval: float = 1.0) -> None:
        self.interval = interval
        self._subscribers: list[Callable[[TelemetrySnapshot], None]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._latest: Optional[TelemetrySnapshot] = None
        # Prime psutil's cpu_percent so the first real reading isn't 0.0.
        if psutil is not None:
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def sample(self) -> TelemetrySnapshot:
        if psutil is None:
            snap = TelemetrySnapshot()
        else:
            vm = psutil.virtual_memory()
            battery = None
            plugged = True
            try:
                batt = psutil.sensors_battery()
                if batt is not None:
                    battery = float(batt.percent)
                    plugged = bool(batt.power_plugged)
            except Exception:
                pass
            snap = TelemetrySnapshot(
                cpu_percent=float(psutil.cpu_percent(interval=None)),
                cpu_temp_c=_read_cpu_temp(),
                ram_percent=float(vm.percent),
                ram_available_gb=vm.available / _BYTES_PER_GIB,
                ram_total_gb=vm.total / _BYTES_PER_GIB,
                gpu_percent=_read_gpu_percent(),
                battery_percent=battery,
                battery_plugged=plugged,
            )
        self._latest = snap
        return snap

    @property
    def latest(self) -> TelemetrySnapshot:
        return self._latest or self.sample()

    # ------------------------------------------------------------------ #
    def subscribe(self, callback: Callable[[TelemetrySnapshot], None]) -> None:
        self._subscribers.append(callback)

    def _loop(self) -> None:
        while not self._stop.is_set():
            snap = self.sample()
            for cb in list(self._subscribers):
                try:
                    cb(snap)
                except Exception:
                    # A misbehaving subscriber must never take down the senses.
                    pass
            self._stop.wait(self.interval)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="aegis-telemetry", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)
            self._thread = None
