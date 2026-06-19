"""Aegis command-line entry point.

    python -m aegis status                 # print a live telemetry snapshot
    python -m aegis simulate [opts]        # run one instruction through the CEE
    python -m aegis serve [--port 8787]    # start the localhost control surface
"""

from __future__ import annotations

import argparse
import json
import sys

from aegis.config import AegisConfig
from aegis.daemon import AegisDaemon
from aegis.models import Instruction, ResourceCost, Zone


def _cmd_status(_args: argparse.Namespace) -> int:
    daemon = AegisDaemon(AegisConfig())
    snap = daemon.telemetry.sample()
    print(json.dumps(snap.model_dump(), indent=2, default=str))
    return 0


def _cmd_simulate(args: argparse.Namespace) -> int:
    daemon = AegisDaemon(AegisConfig())
    instruction = Instruction(
        description=args.description,
        zone=Zone(args.zone),
        utility=args.utility,
        requires_cloud=args.requires_cloud,
        touches_personal_data=args.personal_data,
        cost=ResourceCost(
            ram_gb=args.ram,
            est_seconds=args.seconds,
            cpu_load=args.cpu,
            gpu_load=args.gpu,
            battery_drain_pct=args.battery,
        ),
    )
    decision = daemon.evaluate(instruction)
    print(decision.summary())
    for reason in decision.reasons:
        print(f"  - {reason}")
    if decision.suggested_alternative:
        print(f"  ↪ alternative: {decision.suggested_alternative}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:  # pragma: no cover - runtime entry
    from aegis.api.server import serve

    serve(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aegis", description="Project Aegis — the Sovereign Symbiote.")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Print a live telemetry snapshot.").set_defaults(func=_cmd_status)

    sim = sub.add_parser("simulate", help="Run one instruction through the CEE.")
    sim.add_argument("description", nargs="?", default="Analyse the dataset", help="Instruction text.")
    sim.add_argument("--utility", type=float, default=0.8)
    sim.add_argument("--zone", type=int, choices=[1, 2, 3], default=1)
    sim.add_argument("--ram", type=float, default=1.0, help="RAM demand (GiB).")
    sim.add_argument("--seconds", type=float, default=30.0, help="Estimated duration.")
    sim.add_argument("--cpu", type=float, default=20.0, help="Added CPU load %.")
    sim.add_argument("--gpu", type=float, default=0.0, help="Added GPU load %.")
    sim.add_argument("--battery", type=float, default=1.0, help="Battery drain %.")
    sim.add_argument("--requires-cloud", action="store_true")
    sim.add_argument("--personal-data", action="store_true")
    sim.set_defaults(func=_cmd_simulate)

    srv = sub.add_parser("serve", help="Start the localhost control surface.")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8787)
    srv.set_defaults(func=_cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
