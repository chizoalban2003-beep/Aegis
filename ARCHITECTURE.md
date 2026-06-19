# PROJECT AEGIS: The Sovereign Symbiote

> **Master Architecture Document**
>
> This document synthesizes every structural, philosophical, and technical layer of
> Project Aegis into a single, cohesive blueprint. For a hands-on view of the ideas
> described here, open [`index.html`](./index.html) — an interactive simulation of the
> Contextual Equivalence Engine and an interactive map of the system architecture.

---

## I. Core Philosophy & Definition

**Aegis** is a localized, hardware-bound algorithmic execution daemon. It is **not** a
cloud-based Large Language Model, nor is it a traditional chat-bot. It is an autonomous
"digital hand" designed to live directly above your operating system kernel.

Its primary function is to translate your high-level instructions into physical GUI
actuations (mouse clicks, keystrokes, terminal commands) while strictly negotiating the
cost of those actions against your hardware's physical limits and your ideological
boundaries.

It is built *for* the user, *by* the user, and *with* the user. It rejects the
"Corporate Concierge" model in favor of absolute digital sovereignty.

### Why this must stay local

A Transformer (the kind powering large cloud assistants) is a pattern-recognition
engine: it predicts the next logical token from vast, generalized human knowledge. It
is brilliant at reasoning, but it has no sense of "self" and no physical constraints.

The **Contextual Equivalence** concept (`O₁ == O₂`) is not a pattern-recognition
architecture — it is an **algorithmic execution policy**. Its entire value proposition
is rooted in the physical scarcity and ideological baseline of the *local* hardware and
the *specific* user. A cloud model does not care if your battery is at 10%, nor does it
respect your personal privacy boundaries.

Therefore Aegis uses a lightweight, localized Transformer (a Vision-Language-Action
model) merely as its "eyes" and "hands," while the true brain of the operation is the
**Equivalence Algorithm**. The moment this logic is uploaded to a centralized Big Data
cluster, you stop being the Governor and become just another node in someone else's
equivalence equation.

---

## II. The System Architecture (The Harness)

Aegis operates on a strictly separated three-tier hierarchy to ensure that reasoning,
execution, and governance never dangerously overlap.

### Tier 1 — Hardware Symbiosis Layer (The Senses)

The lowest level, written in a fast, compiled language (e.g. Rust). It has **read-only**
access to the physical and digital realities of your machine.

- **System Telemetry Hub:** Continuously polls CPU heat, GPU load, RAM pressure, and
  battery life.
- **OS Accessibility Bridge:** Connects to native OS APIs (UIAutomation on Windows,
  Accessibility on macOS) to read the screen state, rendering the digital environment
  into a mathematical matrix.
- **The Hardware Watchdog:** A hard-coded failsafe. If Aegis's own processes spike
  thermal loads dangerously, the Watchdog instantly kills the daemon.

### Tier 2 — The Neural Core (The Mind & Hands)

This layer (primarily Python-based) houses the intelligence.

- **The Contextual Equivalence Engine (CEE):** The master decision algorithm. It
  calculates the viability of every action.
- **Visual-Language-Action (VLA) Model:** A lightweight, local vision model. It maps
  semantic intent (e.g. "Find the export button") to precise X/Y screen coordinates.
- **The "DNA" Vector Database:** A localized, encrypted memory store (using tools like
  `llama.cpp`) that records app-usage patterns, successful UI navigations, and
  ideological preferences over time. This is how the system "crystallizes" around your
  specific workflow.

### Tier 3 — The Governance Plane (The Constitution)

The immutable control surface where you, the Governor, dictate reality. The VLA cannot
physically move the mouse without cryptographically passing through this plane.

---

## III. The PIPNB Governance Framework

The Governance Plane relies on five strict pillars to maintain control over the
autonomous agent.

1. **Permissions (The Boundaries):** The definitive "Allowed / Denied" list for file
   directories, applications, and network access.
2. **Instructions (The Objective):** The active tasks assigned by the Governor
   (e.g. *Compile the post-game performance metrics.*).
3. **Policies (The Ideology):** Conditional rules that shape behavior (e.g. *Never
   process data in the cloud; always prioritize thermal stability over speed.*).
4. **Notifications (The Reporting):** An asynchronous "Daily Digest" inbox where Aegis
   logs failed tasks and UI roadblocks, preventing it from constantly interrupting your
   flow state.
5. **Budgets (The Resources):** Hard caps on what Aegis can spend to solve a problem
   (e.g. *Maximum 4GB RAM, 10 minutes of execution time.*).

---

## IV. The Algorithmic Heart: Contextual Equivalence (The Trade)

Aegis does not blindly follow orders. It treats every instruction as a localized market
negotiation. Before acting, the **Contextual Equivalence Engine** runs a mathematical
proof to determine if the trade is viable.

It calculates the Equivalence Ratio (ρ):

```
        Utility_Target
ρ = ──────────────────────────────
     Cost_Hardware · Weight_Ideology
```

- **Utility** — How important is this task to the Governor right now?
- **Cost** — How much battery, RAM, or time will this consume relative to what is
  available?
- **Weight** — Does this violate a privacy policy or require external cloud calls?

| Condition        | Decision                                                                 |
| ---------------- | ------------------------------------------------------------------------ |
| `ρ ≥ 1.0`        | **EXECUTE** — the trade is mathematically viable.                        |
| `0.7 ≤ ρ < 1.0`  | **NEGOTIATE** — pivot to a cheaper headless method, or ask the Governor. |
| `ρ < 0.7`        | **ABORT / DEFER** — the trade is too expensive or too invasive.          |

Budgets and Zone locks (Section V) can override an otherwise viable ρ.

---

## V. Clinical Escalation (The Depth Zones)

Because Aegis physically interacts with the machine, its authority is strictly tiered
based on how close it gets to the core of the OS.

- **Zone 1 — User-Space (Total Autonomy).** Web browsers, organizing user files,
  manipulating standard applications. Aegis executes and logs silently.
- **Zone 2 — System-Space (Consultative).** System settings, drivers, new persistent
  scripts. Aegis halts, performs the math, and sends a low-profile toast notification
  proposing the trade for your approval.
- **Zone 3 — Kernel / Core (Hard Lock).** Bootloaders, security keys, deep registry
  files. Aegis is mathematically air-gapped; it requires manual, cryptographic Governor
  authorization to proceed.

---

## VI. Crystallization (The Local DNA)

Every successful trade, every failed UI interaction, and every Zone 2 suggestion you
approve or deny is recorded in a highly encrypted, local vector database. Aegis learns
exactly how you value your time versus your machine's resources, becoming a perfectly
fitted symbiote.

---

## VII. The Interactive Blueprint

Open [`index.html`](./index.html) in any modern browser. It contains:

1. **The Contextual Equivalence Engine simulator** — act as the local hardware and the
   Governor. Adjust telemetry, task demand, ideology weights, budgets, and the active
   zone to watch the algorithm decide to *execute*, *negotiate*, or *abort* in real time.
2. **The interactive architecture map** — explore the three tiers, the PIPNB pillars,
   and how a command flows from instruction to physical actuation.

No build step, no dependencies, no network — in keeping with the philosophy of the
project itself.
