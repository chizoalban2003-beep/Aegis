"""Headless execution fallback.

When the GUI is blocked (or the CEE renegotiates a heavy GUI trade down to a
cheaper method), Aegis pivots to a headless path: it generates an isolated Python
script and runs it in a fresh subprocess, confined to an allow-listed root
directory and bounded by a timeout drawn from the Budget.

SECURITY MODEL — read this. The in-process guard installed by
``_guard_preamble`` is a *defense-in-depth guardrail*, not a true security
boundary. It confines the common filesystem write vectors (``builtins.open``,
``io.open`` / ``pathlib``, ``os.open`` and the ``os`` mutation calls) to the
allow-listed root and neutralises process-spawning (``os.system``,
``subprocess``) so that *cooperative, semi-trusted* task code cannot accidentally
escape the sandbox. A determined adversary running arbitrary Python can still
escape any pure-Python guard (``ctypes``, re-importing modules, raw syscalls).
For genuinely untrusted code, run this under OS-level isolation (a dedicated low
-privilege user, seccomp/namespaces, or a container) — that is the production
recommendation in ``ARCHITECTURE.md``.
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
        """Code prepended to every generated script to confine filesystem writes.

        Defense-in-depth (see the module docstring): confine every common write
        vector to the allow-listed root and disable process spawning.
        """
        return textwrap.dedent(
            f"""
            import os, io, sys, builtins
            from pathlib import Path

            _ALLOWED_ROOT = Path(r{str(self.allowed_root)!r}).resolve()

            def _confine(path):
                # os.open may pass an int fd (e.g. dir_fd usage) — leave those be.
                if isinstance(path, int):
                    return path
                p = Path(os.fsdecode(path) if isinstance(path, (bytes, bytearray)) else path)
                if not p.is_absolute():
                    p = _ALLOWED_ROOT / p
                p = p.resolve()
                if _ALLOWED_ROOT not in p.parents and p != _ALLOWED_ROOT:
                    raise PermissionError(f"Aegis headless sandbox: {{p}} is outside {{_ALLOWED_ROOT}}")
                return p

            # --- file opens (builtins + io + pathlib all route through these) ---
            _real_open = builtins.open
            def _guarded_open(file, mode="r", *a, **k):
                if any(m in str(mode) for m in ("w", "a", "x", "+")):
                    _confine(file)
                return _real_open(file, mode, *a, **k)
            builtins.open = _guarded_open
            io.open = _guarded_open

            # --- low-level os write/mutation calls ---
            _real_os_open = os.open
            _WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
            def _guarded_os_open(path, flags, *a, **k):
                if flags & _WRITE_FLAGS:
                    _confine(path)
                return _real_os_open(path, flags, *a, **k)
            os.open = _guarded_os_open

            def _wrap_path1(name):
                real = getattr(os, name, None)
                if real is None:
                    return
                def guarded(path, *a, **k):
                    _confine(path)
                    return real(path, *a, **k)
                setattr(os, name, guarded)
            for _n in ("remove", "unlink", "mkdir", "makedirs", "rmdir", "truncate"):
                _wrap_path1(_n)

            def _wrap_path2(name):
                real = getattr(os, name, None)
                if real is None:
                    return
                def guarded(src, dst, *a, **k):
                    _confine(dst)
                    return real(src, dst, *a, **k)
                setattr(os, name, guarded)
            for _n in ("rename", "replace", "link", "symlink"):
                _wrap_path2(_n)

            # --- forbid spawning child processes (would escape the guard) ---
            def _no_spawn(*a, **k):
                raise PermissionError("Aegis headless sandbox: spawning processes is not permitted")
            os.system = _no_spawn
            os.popen = _no_spawn
            for _n in ("execv", "execve", "execvp", "execvpe", "spawnv", "spawnve"):
                if hasattr(os, _n):
                    setattr(os, _n, _no_spawn)
            try:
                import subprocess as _sp
                _sp.Popen = _no_spawn
                _sp.run = _no_spawn
                _sp.call = _no_spawn
                _sp.check_call = _no_spawn
                _sp.check_output = _no_spawn
            except Exception:
                pass

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
