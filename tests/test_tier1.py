import time

from aegis.models import TelemetrySnapshot
from aegis.tier1_senses.telemetry import TelemetryHub
from aegis.tier1_senses.watchdog import HardwareWatchdog, WatchdogLimits
from aegis.tier1_senses.actuation.dry_run import DryRunActuator
from aegis.tier1_senses.accessibility import NullAccessibilityBridge


def test_telemetry_sample_shape():
    hub = TelemetryHub()
    snap = hub.sample()
    assert isinstance(snap, TelemetrySnapshot)
    assert 0 <= snap.cpu_percent <= 100
    assert snap.ram_total_gb >= 0
    assert hub.latest is snap


def test_telemetry_streaming_lifecycle():
    hub = TelemetryHub(interval=0.02)
    received: list[TelemetrySnapshot] = []
    hub.subscribe(received.append)
    hub.start()
    try:
        deadline = time.time() + 2.0
        while len(received) < 2 and time.time() < deadline:
            time.sleep(0.02)
    finally:
        hub.stop()
    assert len(received) >= 2
    assert all(isinstance(s, TelemetrySnapshot) for s in received)
    # stop() is idempotent and leaves no live thread
    hub.stop()


def test_watchdog_trips_after_sustained_breach():
    trips: list[str] = []
    wd = HardwareWatchdog(WatchdogLimits(max_cpu_temp_c=80, sustained_breaches=3), on_trip=trips.append)
    hot = TelemetrySnapshot(cpu_temp_c=95)
    assert wd.inspect(hot) is False  # 1
    assert wd.inspect(hot) is False  # 2
    assert wd.inspect(hot) is True   # 3 -> trip
    assert wd.tripped and trips


def test_watchdog_resets_on_cool():
    wd = HardwareWatchdog(WatchdogLimits(max_cpu_temp_c=80, sustained_breaches=2))
    wd.inspect(TelemetrySnapshot(cpu_temp_c=95))
    wd.inspect(TelemetrySnapshot(cpu_temp_c=40))  # cool resets the counter
    assert wd.inspect(TelemetrySnapshot(cpu_temp_c=95)) is False
    assert wd.tripped is False


def test_dry_run_actuator_records_history():
    act = DryRunActuator()
    act.move(10, 20)
    r = act.click(10, 20)
    act.type_text("hello")
    assert r.ok
    assert any("click" in h for h in act.history)
    assert len(act.history) == 3


def test_null_accessibility_bridge():
    bridge = NullAccessibilityBridge({"Export": (5, 6)})
    assert bridge.screen_state() == {"Export": (5, 6)}
    bridge.set_state({"Save": (1, 2)})
    assert bridge.screen_state() == {"Save": (1, 2)}
