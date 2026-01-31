# Phase 7: Failure Analysis of "Cortex"
# Adversarial Analysis: Every Way This Could Fail
# Date: 2026-01-31

## Methodology

For each failure mode, we assess:
- **Likelihood**: How probable is this failure? (Low / Medium / High)
- **Impact**: If it fails this way, how bad is it? (Low / Medium / High / Critical)
- **Detection**: Would the user notice? (Obvious / Subtle / Silent)
- **Risk Score**: Likelihood × Impact (1-25 scale)

---

## Category 1: Event Extraction Failures

### F1.1 — Pattern Matching Misclassifies Events
**Description**: The local pattern matcher (regex/keyword) incorrectly classifies
Claude's output. E.g., Claude says "I decided to read the file" and the matcher
creates a DECISION_MADE event for a routine file read.

**Likelihood**: HIGH — Natural language is ambiguous; "decided" appears in many contexts.
**Impact**: Medium — Pollutes event store with false positives; projections become noisy.
**Detection**: Subtle — User sees slightly off briefings but may not know why.
**Risk Score**: 15/25

### F1.2 — Important Events Missed (False Negatives)
**Description**: Claude makes a critical decision or discovers something important, but
the pattern matcher doesn't recognize it. E.g., Claude rejects an approach through
implicit reasoning ("X won't work because Y") without using trigger words.

**Likelihood**: HIGH — Implicit decisions are common in nuanced AI responses.
**Impact**: HIGH — The whole point is to capture decisions; missing them is a core failure.
**Detection**: Silent — User won't know what wasn't captured.
**Risk Score**: 20/25 ⚠️ CRITICAL

### F1.3 — Tool Call Metadata Insufficient
**Description**: The Stop hook receives structured data about tool calls but not the
full reasoning context. A file was read, but WHY it was read (to answer question X)
is lost.

**Likelihood**: Medium — Hook payloads vary; some context is available, some isn't.
**Impact**: Medium — Events exist but lack the WHY, reducing projection quality.
**Detection**: Subtle — Projections are factually correct but lack reasoning context.
**Risk Score**: 12/25

### F1.4 — High Event Volume Overwhelms Storage
**Description**: A long, intensive session generates hundreds of events per hour.
Event store grows rapidly; queries slow down; embedding computation becomes expensive.

**Likelihood**: Medium — Power users can have very active sessions.
**Impact**: Low — SQLite handles millions of rows; pruning manages growth.
**Detection**: Obvious — Startup latency increases.
**Risk Score**: 6/25

---

## Category 2: Projection & Retrieval Failures

### F2.1 — Projection Exceeds Token Budget
**Description**: The projection engine selects events that, when formatted as markdown,
exceed the 15% token budget. The briefing is too long and crowds out actual work context.

**Likelihood**: Medium — Budget-aware projection should prevent this, but edge cases exist.
**Impact**: High — Leaves insufficient context window for actual coding work.
**Detection**: Obvious — Claude starts compacting unusually early.
**Risk Score**: 12/25

### F2.2 — Stale Projection Loaded
**Description**: Session crashes or hook fails, so the projection from 2 sessions ago
is loaded instead of the current one. User gets outdated context.

**Likelihood**: LOW — Multiple hook points (PreCompact, Stop) provide redundancy.
**Impact**: Medium — User corrects the AI, but time is wasted.
**Detection**: Obvious — AI references completed work as still in-progress.
**Risk Score**: 6/25

### F2.3 — Semantic Search Returns Irrelevant Results
**Description**: The hybrid search (FTS5 + vector) returns events that are semantically
similar but contextually wrong. E.g., user asks about "authentication" and gets events
about "authorization" from a different project scope.

**Likelihood**: Medium — Embedding models conflate related-but-different concepts.
**Impact**: Medium — AI starts with wrong context; user must correct.
**Detection**: Obvious — AI mentions irrelevant prior work.
**Risk Score**: 9/25

### F2.4 — Salience Decay Removes Important Old Context
**Description**: A critical decision made 50 sessions ago (e.g., "we chose REST over
GraphQL") decays below the salience threshold and is pruned. Later, someone asks
"why did we use REST?" and the answer is gone.

**Likelihood**: Medium — Decay is exponential; old memories fade by design.
**Impact**: HIGH — Losing the "WHY" behind foundational decisions is devastating.
**Detection**: Silent — No one knows the memory existed until they need it.
**Risk Score**: 15/25 ⚠️

---

## Category 3: Integration & Infrastructure Failures

### F3.1 — Hook Execution Fails Silently
**Description**: The PreCompact or SessionStart hook fails (permission error, Python
not found, script crash) but Claude Code continues normally. Events aren't captured
and briefings aren't loaded — the system silently degrades.

**Likelihood**: Medium — Hook failures are logged but easy to miss.
**Impact**: HIGH — Complete memory loss for that session, no briefing loaded.
**Detection**: Subtle — User may not realize memory system is offline.
**Risk Score**: 15/25 ⚠️

### F3.2 — SQLite Database Corruption
**Description**: Concurrent access (e.g., two Claude Code sessions on same project),
unexpected shutdown, or disk error corrupts the event database.

**Likelihood**: LOW — SQLite handles concurrent reads well; WAL mode helps.
**Impact**: Critical — Loss of all event history for the project.
**Detection**: Obvious — Errors on next access.
**Risk Score**: 10/25

### F3.3 — Embedding Model Unavailable
**Description**: The local embedding model (SentenceTransformers) fails to load —
missing dependency, version conflict, out of memory on constrained machines.

**Likelihood**: Medium — Python dependency management is notoriously fragile.
**Impact**: Medium — Falls back to FTS5-only search (keyword, not semantic).
**Detection**: Obvious — Warning at startup.
**Risk Score**: 9/25

### F3.4 — CLAUDE.md Injection Conflict
**Description**: The dynamic briefing injection into CLAUDE.md conflicts with the
user's existing CLAUDE.md content — overwrites their customizations, creates parsing
errors, or exceeds reasonable file size.

**Likelihood**: Medium — Many developers have custom CLAUDE.md files.
**Impact**: HIGH — Could break the user's existing workflow.
**Detection**: Obvious — User notices their CLAUDE.md was modified.
**Risk Score**: 15/25 ⚠️

---

## Category 4: Semantic & Logical Failures

### F4.1 — Contradiction Between Memory and Reality
**Description**: Memory says "using PostgreSQL" but the codebase has switched to SQLite
since the last session. The AI starts with stale architectural assumptions.

**Likelihood**: HIGH — Code changes between sessions are the NORM.
**Impact**: Medium — AI suggests code for wrong database; user corrects.
**Detection**: Obvious — Code doesn't match memory assertions.
**Risk Score**: 12/25

### F4.2 — Memory Pollution Across Projects
**Description**: Events from Project A leak into Project B's context because of
incorrect project scoping (e.g., shared parent directory, renamed project).

**Likelihood**: LOW — Project scoping by directory path is reliable.
**Impact**: HIGH — Wrong context is worse than no context.
**Detection**: Obvious — AI references unrelated project details.
**Risk Score**: 8/25

### F4.3 — Plan State Becomes Inconsistent
**Description**: Plan was updated in one session but the snapshot captured a stale
version. Plan projection shows steps as incomplete that were actually finished.

**Likelihood**: Medium — If compaction happens mid-plan-update.
**Impact**: Medium — AI re-does completed work or skips needed work.
**Detection**: Subtle — User may not notice skipped/repeated plan steps.
**Risk Score**: 12/25

### F4.4 — Circular Reasoning from Self-Generated Context
**Description**: Claude generates a projection → loads it next session → reinforces
its own assumptions → generates a new projection that reinforces them further.
Over many sessions, minor errors compound into entrenched wrong beliefs.

**Likelihood**: Medium — Any self-referential system risks this.
**Impact**: HIGH — Systemic bias that's invisible and self-reinforcing.
**Detection**: SILENT — The most dangerous failure mode.
**Risk Score**: 15/25 ⚠️ CRITICAL

---

## Category 5: User Experience Failures

### F5.1 — Cold Start on New Projects
**Description**: User starts a new project. No events exist. No briefing generated.
The system provides no value until sufficient sessions have accumulated.

**Likelihood**: CERTAIN — Every project starts empty.
**Impact**: Low — System is no worse than no system; it just doesn't help yet.
**Detection**: Obvious — Empty briefing.
**Risk Score**: 5/25

### F5.2 — Briefing Creates False Confidence
**Description**: AI reads the briefing and acts as if it remembers the full session
history. But the briefing is a lossy compression — details are missing. AI makes
confident statements based on incomplete memory.

**Likelihood**: HIGH — LLMs are naturally confident; briefings encourage this.
**Impact**: Medium — AI may make mistakes based on incomplete context.
**Detection**: Subtle — AI sounds correct but may be filling gaps.
**Risk Score**: 15/25 ⚠️

### F5.3 — Setup Complexity Deters Adoption
**Description**: Installing the system requires: Python environment, SQLite extensions,
embedding model download, hook configuration, MCP setup. Too many steps for most users.

**Likelihood**: HIGH — Developer tooling adoption drops sharply with setup complexity.
**Impact**: Critical — If no one installs it, all the design is wasted.
**Detection**: N/A — Users simply don't adopt.
**Risk Score**: 20/25 ⚠️ CRITICAL

---

## Risk Summary Matrix

| # | Failure Mode | Risk Score | Category |
|---|-------------|:----------:|----------|
| **F1.2** | **Important events missed** | **20** | ⚠️ CRITICAL |
| **F5.3** | **Setup complexity deters adoption** | **20** | ⚠️ CRITICAL |
| F1.1 | Pattern matching misclassifies | 15 | HIGH |
| F2.4 | Salience decay removes old decisions | 15 | HIGH |
| F3.1 | Hook execution fails silently | 15 | HIGH |
| F3.4 | CLAUDE.md injection conflict | 15 | HIGH |
| F4.4 | Circular reasoning / echo chamber | 15 | HIGH |
| F5.2 | Briefing creates false confidence | 15 | HIGH |
| F1.3 | Tool metadata insufficient | 12 | MEDIUM |
| F2.1 | Projection exceeds token budget | 12 | MEDIUM |
| F4.1 | Memory contradicts reality | 12 | MEDIUM |
| F4.3 | Plan state inconsistency | 12 | MEDIUM |
| F3.2 | SQLite corruption | 10 | MEDIUM |
| F2.3 | Irrelevant search results | 9 | MEDIUM |
| F3.3 | Embedding model unavailable | 9 | MEDIUM |
| F4.2 | Cross-project pollution | 8 | LOW |
| F1.4 | High event volume | 6 | LOW |
| F2.2 | Stale projection loaded | 6 | LOW |
| F5.1 | Cold start on new projects | 5 | LOW |

**Critical risks requiring mitigation: F1.2, F5.3, F4.4, F2.4**
**High risks requiring mitigation: F1.1, F3.1, F3.4, F5.2**

---

## Phase 7 Status: COMPLETE
## Critical failures identified: 2 (event capture accuracy, setup complexity)
## High-risk failures: 6
## Next: Phase 8 — Mitigations for all HIGH and CRITICAL risks
