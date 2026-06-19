"""Headless execution fallback.

When the GUI is blocked (or the CEE renegotiates a heavy GUI trade down to a
cheaper method), Aegis pivots to a headless path: it generates an isolated Python
script and runs it in a fresh subprocess. The subprocess is sandboxed to an
allow-listed root directory and bounded by a timeout drawn from the Budget.

This keeps file/CLI work off the expensive VLA+GUI path while still honouring the
Governance Plane: the runner refuses to touch anything outside ``allowed_root``.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HeadlessResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    script_path: str


class HeadlessRunner:
    def __init__(self, allowed_root: str | Path) -> None:
        self.allowed_root = Path(allowed_root).expanduser().resolve()
        self.allowed_root.mkdir(parents=True, exist_ok=True)

    def _guard_preamble(self) -> str:
        """Code prepended to every generated script to confine filesystem writes."""
        return textwrap.dedent(
            f"""
            import os, sys, builtins
            from pathlib import Path

            _ALLOWED_ROOT = Path(r{str(self.allowed_root)!r}).resolve()

            def _confine(path):
                p = Path(path)
                if not p.is_absolute():
                    p = _ALLOWED_ROOT / p
                p = p.resolve()
                if _ALLOWED_ROOT not in p.parents and p != _ALLOWED_ROOT:
                    raise PermissionError(f"Aegis headless sandbox: {{p}} is outside {{_ALLOWED_ROOT}}")
                return p

            _real_open = builtins.open
            def _guarded_open(file, mode="r", *a, **k):
                if any(m in mode for m in ("w", "a", "x", "+")):
                    _confine(file)
                return _real_open(file, mode, *a, **k)
            builtins.open = _guarded_open
            AEGIS_ROOT = _ALLOWED_ROOT
            """
        ).strip()

    def run_snippet(self, body: str, *, timeout: float = 600.0) -> HeadlessResult:
        """Run ``body`` (Python) in a sandboxed subprocess.

        The snippet may reference ``AEGIS_ROOT`` (a ``Path`` to the allowed root)
        and may only open files for writing within that root.
        """
        script = self._guard_preamble() + "\n\n# --- task body ---\n" + textwrap.dedent(body)
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", prefix="aegis_headless_", dir=self.allowed_root, delete=False
        ) as fh:
            fh.write(script)
            script_path = fh.name

        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.allowed_root),
            )
            return HeadlessResult(
                ok=proc.returncode == 0,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                script_path=script_path,
            )
        except subprocess.TimeoutExpired as exc:
            return HeadlessResult(
                ok=False,
                returncode=-1,
                stdout=exc.stdout or "",
                stderr=f"Headless task exceeded budget timeout of {timeout}s",
                script_path=script_path,
            )
