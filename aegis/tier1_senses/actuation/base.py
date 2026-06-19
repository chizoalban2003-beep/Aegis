"""Actuator interface — the physical hands of Aegis."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class ActuationResult:
    ok: bool
    action: str
    detail: str = ""
    log: list[str] = field(default_factory=list)


class Actuator(abc.ABC):
    """Drives the mouse/keyboard. Implementations must be cancellable and must
    refuse to act if the daemon's watchdog is tripped (enforced by the caller).
    """

    @abc.abstractmethod
    def move(self, x: int, y: int) -> ActuationResult: ...

    @abc.abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ActuationResult: ...

    @abc.abstractmethod
    def type_text(self, text: str) -> ActuationResult: ...

    @abc.abstractmethod
    def hotkey(self, *keys: str) -> ActuationResult: ...
