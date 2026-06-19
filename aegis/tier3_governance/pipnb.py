"""The PIPNB Governance Framework.

Five strict pillars maintain control over the autonomous agent:

    P — Permissions   : the Allowed/Denied list for paths, apps, hosts.
    I — Instructions  : the active objectives assigned by the Governor.
    P — Policies      : conditional ideological rules that shape behaviour.
    N — Notifications : the asynchronous "Daily Digest" reporting channel.
    B — Budgets       : hard caps on what Aegis may spend to solve a problem.

The :class:`GovernancePlane` ties them together and produces a
:class:`GovernanceVerdict` that either clears an instruction for the CEE or
vetoes it outright. It also exposes the *ideological weight* that the CEE folds
into the Trade equation.
"""

from __future__ import annotations

import fnmatch
from pathlib import PurePath
from typing import Optional

from pydantic import BaseModel, Field

from aegis.models import Instruction


# --------------------------------------------------------------------------- #
# P — Permissions
# --------------------------------------------------------------------------- #
class Permissions(BaseModel):
    """The definitive Allowed/Denied boundaries (deny wins over allow)."""

    allow_paths: list[str] = Field(default_factory=lambda: ["~/Documents/**"])
    deny_paths: list[str] = Field(default_factory=lambda: ["/etc/**", "~/.ssh/**"])
    allow_apps: list[str] = Field(default_factory=list)
    deny_apps: list[str] = Field(default_factory=list)
    allow_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost"])
    deny_hosts: list[str] = Field(default_factory=list)

    @staticmethod
    def _matches(value: str, patterns: list[str]) -> bool:
        norm = str(PurePath(value).as_posix())
        expanded = norm.replace("~", "*", 1) if norm.startswith("~") else norm
        for pattern in patterns:
            pat = pattern.replace("~", "*", 1) if pattern.startswith("~") else pattern
            if fnmatch.fnmatch(expanded, pat) or fnmatch.fnmatch(norm, pattern):
                return True
        return False

    def _check(self, items: list[str], allow: list[str], deny: list[str]) -> list[str]:
        violations: list[str] = []
        for item in items:
            if self._matches(item, deny):
                violations.append(f"denied: {item!r}")
            elif allow and not self._matches(item, allow):
                violations.append(f"not in allow-list: {item!r}")
        return violations

    def violations(self, instruction: Instruction) -> list[str]:
        out: list[str] = []
        out += self._check(instruction.target_paths, self.allow_paths, self.deny_paths)
        out += self._check(instruction.target_apps, self.allow_apps, self.deny_apps)
        out += self._check(instruction.target_hosts, self.allow_hosts, self.deny_hosts)
        return out


# --------------------------------------------------------------------------- #
# P — Policies (the ideology)
# --------------------------------------------------------------------------- #
class Policies(BaseModel):
    """Conditional rules that shape behaviour and produce the ideological weight."""

    forbid_cloud: bool = Field(True, description="Never call external cloud inference/APIs.")
    privacy_first: bool = Field(True, description="Penalise actions that touch personal data.")
    privacy_weight: float = Field(2.5, ge=1.0, description="Multiplier when privacy is at stake.")
    thermal_priority: bool = Field(True, description="Prioritise thermal stability over speed.")
    thermal_weight: float = Field(2.0, ge=1.0, description="Multiplier applied as the CPU heats up.")

    def hard_vetoes(self, instruction: Instruction) -> list[str]:
        """Policy violations that can never be traded away."""
        out: list[str] = []
        if self.forbid_cloud and instruction.requires_cloud:
            out.append("policy 'forbid_cloud': instruction requires an external cloud API")
        return out

    def ideological_weight(self, instruction: Instruction, thermal_headroom: float) -> tuple[float, list[str]]:
        """Compute W >= 1.0 — higher means more ideologically expensive."""
        weight = 1.0
        notes: list[str] = []
        if self.privacy_first and instruction.touches_personal_data:
            weight *= self.privacy_weight
            notes.append(f"privacy_first ×{self.privacy_weight:g} (personal data)")
        if self.thermal_priority:
            # headroom 1.0 (cool) -> ×1.0 ; headroom 0.0 (hot) -> ×thermal_weight
            factor = 1.0 + (self.thermal_weight - 1.0) * (1.0 - thermal_headroom)
            if factor > 1.001:
                weight *= factor
                notes.append(f"thermal_priority ×{factor:.2f} (headroom={thermal_headroom:.0%})")
        return weight, notes


# --------------------------------------------------------------------------- #
# N — Notifications
# --------------------------------------------------------------------------- #
class Notification(BaseModel):
    level: str = "info"  # info | warning | error | proposal
    message: str
    instruction_id: Optional[str] = None


class Notifications(BaseModel):
    """Asynchronous 'Daily Digest' inbox — Aegis logs here instead of interrupting."""

    interrupt_threshold: str = Field("error", description="Min level allowed to interrupt flow.")
    digest: list[Notification] = Field(default_factory=list)

    _LEVELS = ("info", "warning", "proposal", "error")

    def post(self, message: str, level: str = "info", instruction_id: Optional[str] = None) -> Notification:
        note = Notification(level=level, message=message, instruction_id=instruction_id)
        self.digest.append(note)
        return note

    def should_interrupt(self, level: str) -> bool:
        try:
            return self._LEVELS.index(level) >= self._LEVELS.index(self.interrupt_threshold)
        except ValueError:
            return False


# --------------------------------------------------------------------------- #
# B — Budgets
# --------------------------------------------------------------------------- #
class Budgets(BaseModel):
    """Hard caps on what Aegis may spend to solve a problem."""

    max_ram_gb: float = Field(4.0, gt=0)
    max_seconds: float = Field(600.0, gt=0)
    max_battery_drain_pct: float = Field(15.0, gt=0)
    min_battery_to_act_pct: float = Field(10.0, ge=0, description="Refuse heavy work below this on battery.")

    def violations(self, instruction: Instruction, battery_percent: Optional[float], plugged: bool) -> list[str]:
        out: list[str] = []
        c = instruction.cost
        if c.ram_gb > self.max_ram_gb:
            out.append(f"budget: needs {c.ram_gb:g}GB RAM > cap {self.max_ram_gb:g}GB")
        if c.est_seconds > self.max_seconds:
            out.append(f"budget: needs {c.est_seconds:g}s > cap {self.max_seconds:g}s")
        if c.battery_drain_pct > self.max_battery_drain_pct:
            out.append(f"budget: drains {c.battery_drain_pct:g}% > cap {self.max_battery_drain_pct:g}%")
        if (
            not plugged
            and battery_percent is not None
            and battery_percent < self.min_battery_to_act_pct
        ):
            out.append(
                f"budget: battery {battery_percent:g}% below floor {self.min_battery_to_act_pct:g}% (unplugged)"
            )
        return out


# --------------------------------------------------------------------------- #
# The plane
# --------------------------------------------------------------------------- #
class GovernanceVerdict(BaseModel):
    """Outcome of pushing an instruction through the Governance Plane."""

    cleared: bool
    hard_vetoes: list[str] = Field(default_factory=list)
    ideological_weight: float = 1.0
    weight_notes: list[str] = Field(default_factory=list)


class GovernancePlane(BaseModel):
    """Tier 3 — binds the five PIPNB pillars into one control surface."""

    permissions: Permissions = Field(default_factory=Permissions)
    policies: Policies = Field(default_factory=Policies)
    notifications: Notifications = Field(default_factory=Notifications)
    budgets: Budgets = Field(default_factory=Budgets)

    def evaluate(
        self,
        instruction: Instruction,
        *,
        thermal_headroom: float = 1.0,
        battery_percent: Optional[float] = None,
        battery_plugged: bool = True,
    ) -> GovernanceVerdict:
        vetoes: list[str] = []
        vetoes += self.permissions.violations(instruction)
        vetoes += self.policies.hard_vetoes(instruction)
        vetoes += self.budgets.violations(instruction, battery_percent, battery_plugged)

        weight, notes = self.policies.ideological_weight(instruction, thermal_headroom)

        return GovernanceVerdict(
            cleared=not vetoes,
            hard_vetoes=vetoes,
            ideological_weight=weight,
            weight_notes=notes,
        )
