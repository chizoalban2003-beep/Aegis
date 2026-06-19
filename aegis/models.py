"""Shared, strictly-typed domain models for Project Aegis.

These Pydantic models are the lingua franca that flows between the three tiers:

    Tier 1 (Senses)  -> emits ``TelemetrySnapshot``
    Tier 2 (Mind)    -> consumes ``Instruction`` + ``TelemetrySnapshot`` -> emits ``Decision``
    Tier 3 (Plane)   -> gates everything via the PIPNB models (see ``tier3_governance``)
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class Zone(int, Enum):
    """Clinical depth zones — execution authority by proximity to the OS core."""

    USER_SPACE = 1   # Browsers, apps, user files. Total autonomy.
    SYSTEM_SPACE = 2  # Config, drivers, persistent scripts. Consultative.
    KERNEL_CORE = 3  # Bootloaders, keys, registry. Hard lock + crypto approval.

    @property
    def label(self) -> str:
        return {
            Zone.USER_SPACE: "Zone 1 · User-Space (Total Autonomy)",
            Zone.SYSTEM_SPACE: "Zone 2 · System-Space (Consultative)",
            Zone.KERNEL_CORE: "Zone 3 · Kernel/Core (Hard Lock)",
        }[self]


class DecisionAction(str, Enum):
    """The terminal verdict of the Contextual Equivalence Engine."""

    EXECUTE = "execute"            # ratio >= 1.0 and all gates passed
    NEGOTIATE = "negotiate"        # marginal ratio; pivot to a cheaper method
    DEFER = "defer"                # too expensive / budget hit; retry later
    CONSULT = "consult"            # Zone 2; propose the trade to the Governor
    PENDING_APPROVAL = "pending_approval"  # Zone 3; awaiting cryptographic sign-off
    VETO = "veto"                  # hard governance violation; never executes


class TelemetrySnapshot(BaseModel):
    """A point-in-time reading of the machine's physical reality (Tier 1)."""

    cpu_percent: float = Field(0.0, ge=0, le=100, description="Aggregate CPU load %.")
    cpu_temp_c: Optional[float] = Field(None, description="Hottest CPU package °C, if available.")
    ram_percent: float = Field(0.0, ge=0, le=100, description="RAM pressure %.")
    ram_available_gb: float = Field(0.0, ge=0, description="Free RAM in GiB.")
    ram_total_gb: float = Field(0.0, ge=0, description="Total RAM in GiB.")
    gpu_percent: float = Field(0.0, ge=0, le=100, description="GPU utilisation %.")
    battery_percent: Optional[float] = Field(None, ge=0, le=100, description="Battery charge %.")
    battery_plugged: bool = Field(True, description="Whether AC power is connected.")
    net_latency_ms: Optional[float] = Field(None, ge=0, description="Local network round-trip ms.")
    timestamp: float = Field(default_factory=time.time)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def thermal_headroom(self) -> float:
        """A 0..1 score; 1.0 = cool, 0.0 = at/over the thermal ceiling (~90°C)."""
        if self.cpu_temp_c is None:
            return 1.0
        ceiling = 90.0
        return max(0.0, min(1.0, (ceiling - self.cpu_temp_c) / ceiling))


class ResourceCost(BaseModel):
    """The estimated resource demand of executing an instruction."""

    ram_gb: float = Field(0.0, ge=0, description="Peak RAM the action needs (GiB).")
    est_seconds: float = Field(0.0, ge=0, description="Estimated wall-clock duration.")
    cpu_load: float = Field(0.0, ge=0, le=100, description="Additional CPU load it imposes %.")
    gpu_load: float = Field(0.0, ge=0, le=100, description="Additional GPU load it imposes %.")
    battery_drain_pct: float = Field(0.0, ge=0, le=100, description="Battery it will consume %.")
    requires_network: bool = Field(False, description="Whether the action touches the network.")


class Instruction(BaseModel):
    """A high-level objective handed to Aegis by the Governor."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    description: str
    zone: Zone = Zone.USER_SPACE

    # How important is this to the Governor *right now*? (0..1, but values >1 allowed
    # to express urgent priority.)
    utility: float = Field(0.5, ge=0, description="Target utility / importance.")

    cost: ResourceCost = Field(default_factory=ResourceCost)

    # Ideological signals consumed by Policies when computing the weight.
    requires_cloud: bool = Field(False, description="Action would call an external cloud API.")
    touches_personal_data: bool = Field(False, description="Action reads/writes private files.")

    # Resources the action wants to touch, checked against Permissions.
    target_paths: list[str] = Field(default_factory=list)
    target_apps: list[str] = Field(default_factory=list)
    target_hosts: list[str] = Field(default_factory=list)

    # Optional cryptographic approval token for Zone 3 actions.
    approval_token: Optional[str] = None


class Decision(BaseModel):
    """The Contextual Equivalence Engine's verdict for one instruction."""

    instruction_id: str
    action: DecisionAction
    ratio: float = Field(..., description="The equivalence ratio ρ = Utility / (Cost · Weight).")
    utility: float
    cost: float
    ideological_weight: float
    zone: Zone
    reasons: list[str] = Field(default_factory=list)
    suggested_alternative: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

    @property
    def viable(self) -> bool:
        return self.action in (DecisionAction.EXECUTE, DecisionAction.NEGOTIATE)

    def summary(self) -> str:
        return (
            f"[{self.action.value.upper()}] ρ={self.ratio:.2f} "
            f"(U={self.utility:.2f} / (C={self.cost:.2f} · W={self.ideological_weight:.2f})) "
            f"· {self.zone.label}"
        )
