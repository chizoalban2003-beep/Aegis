"""OS Accessibility Bridge — renders the screen into a mathematical matrix.

A production bridge connects to native accessibility APIs (UIAutomation on
Windows, AppKit/AXUIElement on macOS, AT-SPI on Linux) to enumerate on-screen
elements. Those APIs require a desktop session, so this module exposes an
abstract interface plus a ``NullAccessibilityBridge`` that returns a static,
injectable screen state — keeping the daemon importable and testable headlessly.
"""

from __future__ import annotations

import abc
import platform


class AccessibilityBridge(abc.ABC):
    @abc.abstractmethod
    def screen_state(self) -> dict[str, tuple[int, int]]:
        """Return a mapping of element label -> (x, y) screen coordinate."""


class NullAccessibilityBridge(AccessibilityBridge):
    """Headless-safe bridge with an injectable, static screen map."""

    def __init__(self, elements: dict[str, tuple[int, int]] | None = None) -> None:
        self._elements = elements or {}

    def set_state(self, elements: dict[str, tuple[int, int]]) -> None:
        self._elements = dict(elements)

    def screen_state(self) -> dict[str, tuple[int, int]]:
        return dict(self._elements)


def default_bridge() -> AccessibilityBridge:
    """Pick a bridge for the current OS.

    Native bridges are intentionally not imported here (they pull heavy,
    session-bound dependencies). Until those backends are wired, every platform
    falls back to the headless-safe null bridge.
    """
    _ = platform.system()  # reserved for future native dispatch
    return NullAccessibilityBridge()
