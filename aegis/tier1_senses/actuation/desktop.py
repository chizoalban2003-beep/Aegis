"""DesktopActuator — drives a real mouse/keyboard via ``pyautogui``.

``pyautogui`` is imported lazily because it requires a desktop session (and on
Linux a running X server plus system packages). On a headless box, constructing
this class raises ``ActuationUnavailable`` so callers can fall back to the
:class:`~aegis.tier1_senses.actuation.dry_run.DryRunActuator` or the headless
file pipeline.
"""

from __future__ import annotations

from aegis.tier1_senses.actuation.base import ActuationResult, Actuator


class ActuationUnavailable(RuntimeError):
    """Raised when no GUI session is available to drive."""


class DesktopActuator(Actuator):
    def __init__(self, move_duration: float = 0.1) -> None:
        try:
            import pyautogui  # type: ignore
        except Exception as exc:  # ImportError or display/env errors
            raise ActuationUnavailable(
                "pyautogui is unavailable (no GUI session or package missing). "
                "Install the 'aegis[desktop]' extra and run inside a desktop session."
            ) from exc
        pyautogui.FAILSAFE = True  # slam mouse to a corner to abort
        self._g = pyautogui
        self._move_duration = move_duration

    def move(self, x: int, y: int) -> ActuationResult:
        self._g.moveTo(x, y, duration=self._move_duration)
        return ActuationResult(ok=True, action="move", detail=f"x={x}, y={y}")

    def click(self, x: int, y: int, button: str = "left") -> ActuationResult:
        self._g.click(x=x, y=y, button=button)
        return ActuationResult(ok=True, action="click", detail=f"x={x}, y={y}, button={button}")

    def type_text(self, text: str) -> ActuationResult:
        self._g.typewrite(text)
        return ActuationResult(ok=True, action="type", detail=repr(text))

    def hotkey(self, *keys: str) -> ActuationResult:
        self._g.hotkey(*keys)
        return ActuationResult(ok=True, action="hotkey", detail="+".join(keys))
