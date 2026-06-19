# Project Aegis — The Sovereign Symbiote

**Aegis** is a localized, hardware-bound algorithmic execution daemon. It is **not** a
cloud-based Large Language Model, nor a chat-bot. It is an autonomous *"digital hand"*
that lives directly above your operating system kernel and translates your high-level
instructions into physical GUI actuations (mouse clicks, keystrokes, terminal commands)
— while strictly negotiating the cost of every action against your hardware's physical
limits and your ideological boundaries.

It is built *for* the user, *by* the user, and *with* the user. It rejects the
"Corporate Concierge" model in favor of absolute digital sovereignty. Nothing here ever
calls a cloud inference API.

> See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full philosophical + technical
> master document.

---

## Why local, and why an *algorithm* (not just a model)

A Transformer is a pattern-recognition engine: brilliant at reasoning, but it has no
sense of "self" and no physical constraints. The value of Aegis's **Contextual
Equivalence** concept (`O₁ == O₂`) is that it is an **algorithmic execution policy**
rooted in the physical scarcity of *this* machine and the ideology of *this* user. A
cloud model doesn't care that your battery is at 10%.

So Aegis uses a lightweight, local Vision-Language-Action (VLA) model merely as its
**eyes and hands**, while the real brain is the **Contextual Equivalence Engine (CEE)**.

---

## Architecture — the three-tier harness

```
            ┌──────────────────────────────────────────────────────────┐
 Governor ─▶│  TIER 3 · GOVERNANCE PLANE  (the Constitution / PIPNB)     │
            │  Permissions · Instructions · Policies · Notifications ·   │
            │  Budgets  →  hard vetoes + ideological weight              │
            └───────────────▲───────────────────────────┬──────────────┘
                            │ weight / veto              │ clears
            ┌───────────────┴───────────────────────────▼──────────────┐
 Instruction│  TIER 2 · NEURAL CORE  (the Mind & Hands)                  │
   ───────▶ │  Contextual Equivalence Engine (CEE) · VLA model · DNA mem │
            │             ρ = Utility / (Cost · Weight)                  │
            └───────────────▲───────────────────────────┬──────────────┘
                            │ telemetry                  │ actuate / pivot
            ┌───────────────┴───────────────────────────▼──────────────┐
            │  TIER 1 · HARDWARE SYMBIOSIS  (the Senses)                 │
  Machine ─▶│  Telemetry Hub · Watchdog · Accessibility Bridge ·         │
            │  Actuation (desktop / dry-run) · Headless fallback         │
            └───────────────────────────────────────────────────────────┘
```

- **Tier 1 — Senses (read-only):** polls CPU/RAM/battery/GPU telemetry, reads the screen
  via the OS accessibility tree, drives mouse/keyboard, and runs a hard-coded thermal
  **Watchdog** failsafe.
- **Tier 2 — Mind:** the **CEE** computes the Trade, a local **VLA** maps intent to
  screen coordinates, and the encrypted **"DNA"** store crystallises around your workflow.
- **Tier 3 — Governance Plane:** the immutable **PIPNB** control surface. The VLA cannot
  move the mouse without cryptographically passing through this plane.

---

## The algorithmic heart — Contextual Equivalence (the Trade)

Aegis treats every instruction as a localized market negotiation and runs an
equivalence proof before acting:

```
        Utility_Target
ρ  =  ──────────────────────────────
       Cost_Hardware · Weight_Ideology
```

| Condition        | Decision                                                          |
| ---------------- | ---------------------------------------------------------------- |
| `ρ ≥ 1.0`        | **EXECUTE** — the trade is viable.                               |
| `0.7 ≤ ρ < 1.0`  | **NEGOTIATE** — pivot to a cheaper headless method.             |
| `ρ < 0.7`        | **DEFER** — too expensive; retry when conditions improve.        |

`Cost_Hardware` is a weighted average of fractional resource pressure (RAM, time, CPU,
GPU, battery), amplified by *live* scarcity from Tier-1 telemetry. `Weight_Ideology`
starts at 1.0 and grows when Policies are at stake (privacy, thermal stability).
Governance can hard-**VETO** an otherwise viable trade, and the zone gate can escalate it
to **CONSULT** (Zone 2) or **PENDING_APPROVAL** (Zone 3).

### Clinical depth zones

- **Zone 1 · User-Space** — total autonomy; execute and log silently.
- **Zone 2 · System-Space** — consultative; propose the trade to the Governor.
- **Zone 3 · Kernel/Core** — hard lock; requires a cryptographic Governor token.

---

## Repository layout

```
project-aegis/
├── aegis/
│   ├── __init__.py            # package surface
│   ├── __main__.py            # CLI: status | simulate | serve
│   ├── config.py              # AegisConfig + local paths (~/.aegis)
│   ├── daemon.py              # orchestrates the three tiers per instruction
│   ├── models.py              # shared Pydantic models (Instruction, Decision, ...)
│   ├── api/
│   │   └── server.py          # FastAPI control surface (localhost only)
│   ├── tier1_senses/
│   │   ├── telemetry.py       # System Telemetry Hub (psutil)
│   │   ├── watchdog.py        # Hardware Watchdog failsafe
│   │   ├── accessibility.py   # OS Accessibility Bridge (+ headless null impl)
│   │   └── actuation/
│   │       ├── base.py        # Actuator interface
│   │       ├── dry_run.py     # headless-safe default backend
│   │       └── desktop.py     # pyautogui backend (lazy import)
│   ├── tier2_core/
│   │   ├── cee.py             # Contextual Equivalence Engine (the Trade)
│   │   ├── vla.py             # Vision-Language-Action interface + stub
│   │   └── dna/store.py       # encrypted-at-rest SQLite "DNA" memory
│   ├── tier3_governance/
│   │   ├── pipnb.py           # Permissions/Instructions/Policies/Notifications/Budgets
│   │   └── zones.py           # clinical depth-zone escalation
│   └── headless/
│       └── fallback.py        # sandboxed subprocess file/CLI executor
├── examples/
│   └── phase2_cee_demo.py     # GPU-maxed → DEFER, then EXECUTE
├── tests/                     # pytest suite (36 tests)
├── ARCHITECTURE.md            # master architecture document
├── pyproject.toml
└── requirements.txt
```

---

## Install & run

```bash
pip install -r requirements.txt          # core runtime
# or, editable with extras:
pip install -e ".[dev,desktop]"

# 1) Live telemetry snapshot of this machine
python -m aegis status

# 2) Run one instruction through the CEE (act as hardware + Governor)
python -m aegis simulate "Export quarterly report" --utility 0.9 --gpu 0
python -m aegis simulate "Edit bootloader" --zone 3        # -> PENDING_APPROVAL

# 3) The Phase-2 narrative demo (defer under load, execute when idle)
python examples/phase2_cee_demo.py

# 4) The localhost control surface
python -m aegis serve --port 8787        # GET /status, POST /evaluate, /instruct, /digest
```

---

## Testing

```bash
pip install "pytest>=8" "httpx>=0.27"
python -m pytest
```

---

## Build phases, research notes & decisions

This repository was scaffolded in the phases from the build brief.

### Decision: target OS & language split

- **Primary/dev target: Linux** (the current runtime), with **Windows and macOS treated
  as first-class via a pluggable backend layer**. OS-specific concerns (accessibility
  tree, native actuation) sit behind interfaces (`AccessibilityBridge`, `Actuator`) so
  the cross-platform core never hard-depends on a session-bound API.
- **Language split (the hybrid proposal):** the reference implementation is **Python**
  (FastAPI/Pydantic for strict typing and routing) because it makes the CEE, governance,
  and tests immediately runnable and auditable. The recommendation for a production
  build is to **rewrite the Tier-1 hot path (telemetry polling + Watchdog + native
  actuation hooks) in Rust** for latency and a memory-safe failsafe, exposed to the
  Python core over a thin FFI/IPC boundary. Tier 2/3 stay in Python.

### Research: libraries surveyed for Tier 1

| Concern                | Cross-platform           | Windows           | macOS                  | Linux            |
| ---------------------- | ------------------------ | ----------------- | ---------------------- | ---------------- |
| CPU/RAM/battery/temps  | **psutil** (used)        | —                 | —                      | `/sys` sensors   |
| GPU utilisation        | `nvidia-ml-py` (NVML)    | —                 | IOKit                  | NVML / `sysfs`   |
| Accessibility tree     | —                        | UIAutomation / `pywinauto` | AXUIElement (AppKit) | AT-SPI       |
| GUI actuation          | **pyautogui** (optional) | `pywinauto`       | `pyobjc`/Quartz        | `python-xlib`    |
| Local model runtime    | **llama.cpp** family     | —                 | Metal                  | CUDA/CPU         |
| DNA vector memory      | SQLite (used) + **ChromaDB** (optional extra) | — | — | — |

`psutil` was chosen for the senses because it is genuinely cross-platform and degrades
gracefully (no battery on a desktop, no temp sensor in CI). GPU and desktop actuation
are **optional extras** so the daemon imports and the CEE runs on a headless box.

### Phase status

- **Phase 1 — Research & Scaffolding:** repo tree, `requirements.txt`/`pyproject.toml`,
  this README, and the documented OS/language decision. ✔
- **Phase 2 — Governance & Math Engine:** `tier3_governance` (PIPNB, Pydantic), the
  `ContextualEquivalenceEngine`, and the GPU-maxed → DEFER mock (`examples/` + tests). ✔
- **Phase 3 — Telemetry & Actuation:** Tier-1 telemetry workers + Watchdog streaming to
  the CEE, actuation backends, and the sandboxed headless fallback. ✔

### Suggested next steps

- Implement the native Rust Tier-1 hot path + FFI boundary.
- Wire real `AccessibilityBridge`/`DesktopActuator` backends per OS.
- Swap the bundled `XorCipher` placeholder for OS-keychain-backed at-rest encryption,
  and the bag-of-words DNA retrieval for a real local vector store (ChromaDB extra).
