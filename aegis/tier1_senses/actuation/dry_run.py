"""DryRunActuator — records intended actuations without touching the device.

This is the default backend: it is headless-safe, deterministic, and ideal for
tests, audits, and "explain what you would do" previews. A real desktop backend
(``DesktopActuator``) lazily imports ``pyautogui`` and is only constructed when a
GUI session is actually present.
"""

from __future__ import annotations

from aegis.tier1_senses.actuation.base import ActuationResult, Actuator


class DryRunActuator(Actuator):
    def __init__(self) -> None:
        self.history: list[str] = []

    def _record(self, action: str, detail: str) -> ActuationResult:
        entry = f"{action}({detail})"
        self.history.append(entry)
        return ActuationResult(ok=True, action=action, detail=detail, log=[f"[dry-run] {entry}"])

    def move(self, x: int, y: int) -> ActuationResult:
        return self._record("move", f"x={x}, y={y}")

    def click(self, x: int, y: int, button: str = "left") -> ActuationResult:
        return self._record("click", f"x={x}, y={y}, button={button}")

    def type_text(self, text: str) -> ActuationResult:
        return self._record("type", repr(text))

    def hotkey(self, *keys: str) -> ActuationResult:
        return self._record("hotkey", "+".join(keys))
