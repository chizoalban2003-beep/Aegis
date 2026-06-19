"""Vision-Language-Action (VLA) model interface.

A lightweight, *local* vision model maps semantic intent ("Find the export
button") to precise X/Y screen coordinates. It is deliberately the agent's
"eyes" — never its brain. The real reasoning lives in the CEE.

This module ships an abstract interface plus a deterministic stub so the rest of
the system is testable headlessly. A production backend would wrap a local model
served via ``llama.cpp``/an on-device VLM — and must never reach the cloud.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class UIElement:
    label: str
    x: int
    y: int
    confidence: float


class VLAModel(abc.ABC):
    """Maps a natural-language target to a screen coordinate."""

    @abc.abstractmethod
    def locate(self, intent: str, screen_state: dict | None = None) -> UIElement | None:
        """Return the best-matching on-screen element for ``intent``."""


class StubVLAModel(VLAModel):
    """Deterministic, dependency-free stub used for local development & tests.

    It "reads" a provided screen_state mapping of ``label -> (x, y)`` and does a
    simple case-insensitive substring match, so behaviour is fully predictable.
    """

    def locate(self, intent: str, screen_state: dict | None = None) -> UIElement | None:
        if not screen_state:
            return None
        needle = intent.lower()
        best: UIElement | None = None
        for label, coord in screen_state.items():
            score = _match_score(needle, label.lower())
            if score <= 0:
                continue
            x, y = coord
            if best is None or score > best.confidence:
                best = UIElement(label=label, x=int(x), y=int(y), confidence=score)
        return best


def _match_score(needle: str, haystack: str) -> float:
    if needle == haystack:
        return 1.0
    if needle in haystack or haystack in needle:
        # crude overlap ratio
        return len(set(needle.split()) & set(haystack.split())) / max(len(needle.split()), 1) or 0.6
    overlap = set(needle.split()) & set(haystack.split())
    return len(overlap) / max(len(needle.split()), 1)
