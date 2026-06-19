"""FastAPI control surface — bound to localhost only.

Exposes a minimal, sovereign API: read live telemetry, submit an instruction for
a Trade evaluation, and read the Daily Digest. There is intentionally no remote
binding and no outbound call anywhere in this module.
"""

from __future__ import annotations

from typing import Optional

from aegis.config import AegisConfig
from aegis.daemon import AegisDaemon
from aegis.models import Decision, Instruction, TelemetrySnapshot


def create_app(daemon: Optional[AegisDaemon] = None):
    """Build the FastAPI app. Imported lazily so the package works without web deps."""
    from fastapi import FastAPI

    daemon = daemon or AegisDaemon(AegisConfig())
    app = FastAPI(
        title="Project Aegis — Local Control Surface",
        version="0.1.0",
        description="Sovereign, local-first daemon. Localhost only; never the cloud.",
    )

    @app.get("/status", response_model=TelemetrySnapshot)
    def status() -> TelemetrySnapshot:
        return daemon.telemetry.sample()

    @app.post("/instruct", response_model=Decision)
    def instruct(instruction: Instruction) -> Decision:
        return daemon.submit(instruction)

    @app.post("/evaluate", response_model=Decision)
    def evaluate(instruction: Instruction) -> Decision:
        # Dry evaluation: compute the Trade without side effects.
        return daemon.evaluate(instruction)

    @app.get("/digest")
    def digest():
        return [n.model_dump() for n in daemon.notifications.digest]

    @app.get("/health")
    def health():
        return {"ok": True, "watchdog_tripped": daemon.watchdog.tripped}

    app.state.daemon = daemon
    return app


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:  # pragma: no cover - runtime entry
    import uvicorn

    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Aegis refuses to bind to a non-local host. Sovereignty is the point.")
    uvicorn.run(create_app(), host=host, port=port)
