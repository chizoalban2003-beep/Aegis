from aegis.config import AegisConfig
from aegis.daemon import AegisDaemon
from aegis.models import DecisionAction, Instruction, ResourceCost, TelemetrySnapshot, Zone


def _daemon(tmp_path) -> AegisDaemon:
    cfg = AegisConfig(home=tmp_path / ".aegis")
    return AegisDaemon(cfg)


def idle() -> TelemetrySnapshot:
    return TelemetrySnapshot(
        cpu_percent=10, cpu_temp_c=45, ram_percent=30, ram_available_gb=12,
        ram_total_gb=16, gpu_percent=5, battery_percent=95, battery_plugged=True,
    )


def test_submit_executes_and_crystallises(tmp_path):
    d = _daemon(tmp_path)
    ins = Instruction(description="organise downloads", utility=0.9,
                      cost=ResourceCost(ram_gb=1, est_seconds=5, cpu_load=5))
    decision = d.submit(ins, telemetry=idle())
    assert decision.action is DecisionAction.EXECUTE
    assert d.dna.count() == 1
    assert any(n.level == "info" for n in d.notifications.digest)
    d.stop()


def test_submit_zone2_posts_proposal(tmp_path):
    d = _daemon(tmp_path)
    ins = Instruction(description="change display scaling", zone=Zone.SYSTEM_SPACE, utility=0.9,
                      cost=ResourceCost(ram_gb=1, est_seconds=5, cpu_load=5))
    decision = d.submit(ins, telemetry=idle())
    assert decision.action is DecisionAction.CONSULT
    assert any(n.level == "proposal" for n in d.notifications.digest)
    d.stop()


def test_submit_vetoes_when_watchdog_tripped(tmp_path):
    d = _daemon(tmp_path)
    hot = TelemetrySnapshot(cpu_temp_c=99, ram_percent=50)
    for _ in range(3):  # trip the sustained-breach watchdog
        d.watchdog.inspect(hot)
    ins = Instruction(description="anything", utility=0.9, cost=ResourceCost(ram_gb=1))
    assert d.submit(ins, telemetry=hot).action is DecisionAction.VETO
    d.stop()


def test_api_endpoints(tmp_path):
    from fastapi.testclient import TestClient

    d = _daemon(tmp_path)
    from aegis.api.server import create_app

    client = TestClient(create_app(d))
    assert client.get("/health").json()["ok"] is True
    assert "cpu_percent" in client.get("/status").json()

    payload = {"description": "ping", "utility": 0.9,
               "cost": {"ram_gb": 1, "est_seconds": 5, "cpu_load": 5}}
    r = client.post("/evaluate", json=payload)
    assert r.status_code == 200
    assert r.json()["instruction_id"]
    d.stop()
