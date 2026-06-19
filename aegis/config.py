"""Daemon configuration and on-disk paths.

All state lives locally under ``~/.aegis`` by default — never the cloud.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from aegis.tier3_governance.pipnb import GovernancePlane
from aegis.tier2_core.cee import CEEConfig


def default_home() -> Path:
    return Path.home() / ".aegis"


class AegisConfig(BaseModel):
    """Top-level configuration for an Aegis instance."""

    home: Path = Field(default_factory=default_home)
    telemetry_interval: float = 1.0
    governance: GovernancePlane = Field(default_factory=GovernancePlane)
    cee: CEEConfig = Field(default_factory=CEEConfig)
    dna_filename: str = "dna.sqlite3"
    dna_key: str = "change-me-governor-key"

    @property
    def dna_path(self) -> Path:
        return self.home / self.dna_filename

    @property
    def headless_root(self) -> Path:
        # Constrain headless file work to a sandbox under the Aegis home.
        return self.home / "workspace"

    def ensure_dirs(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.headless_root.mkdir(parents=True, exist_ok=True)
