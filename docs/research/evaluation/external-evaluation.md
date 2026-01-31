# External Evaluation: Cortex Memory Persistence Research & Plan

**Date:** 2026-01-31  
**Purpose:** An independent evaluation of the Cortex memory-persistence research and plan, identifying holes, gotchas, and missing elements that a different AI perspective would surface.

This evaluation reviews the research in [phases/](../phases/), [comparisons/](../comparisons/), [MASTER-PLAN.md](../MASTER-PLAN.md), and [paper/cortex-research-paper.md](../paper/cortex-research-paper.md) from a deliberately different perspective: challenging assumptions, surfacing implementation risks, and noting omissions. The goal is to stress-test the plan before implementation.

---

## 1. What the Research Got Right (Briefly)

- **Problem definition** ([01-problem-definition.md](../phases/01-problem-definition.md)) is clear and well-scoped: five categories of lost context, formal FRs/NFRs, and success criteria.
- **Event sourcing** as a foundation is justified by industry references and fits "audit trail + projections" well.
- **No secondary LLM in hooks** is a sound constraint; Phase 5's finding avoids infinite loops and latency.
- **Progressive tiers** ([09-mitigations.md](../phases/09-mitigations.md)) directly address adoption risk (F5.3).
- **Three-layer extraction** (structural + keyword + self-reporting) is a reasonable mitigation for F1.2.
- **Separate `.claude/rules/` file** for the briefing avoids CLAUDE.md overwrite (F3.4).
- **Failure analysis** ([08-failure-analysis.md](../phases/08-failure-analysis.md)) is thorough; 19 failure modes across 5 categories is strong.

---

## 2. Holes and Gotchas

### 2.1 Hook API Not Validated Against Real Claude Code

The design depends entirely on what Claude Code actually passes to hooks:

- **Phase 5** states: "PreCompact hook payload includes session info but NOT the conversation content (content must be captured via the Stop hook incrementally)."
- **Phase 2** lists: "PreCompact, PostCompact, SessionStart, SessionEnd, Stop" — **UserPromptSubmit is not listed there.**
- The **paper and Phase 5** use a **UserPromptSubmit** hook for anticipatory retrieval (Tier 2).

**Gotcha:** If UserPromptSubmit does not exist or fires at a different time, Tier 2's "embed user message → search → append to briefing" cannot work as described. The plan should either (a) cite official Claude Code hook docs and payload schemas, or (b) add a "Phase 0: Validate hook API" that confirms event names, payload shape, and whether conversation content is available in Stop/PreCompact.

### 2.2 Immortal Events → Unbounded Growth

- **Mitigation M5** ([09-mitigations.md](../phases/09-mitigations.md)): DECISION_MADE and APPROACH_REJECTED never decay ("immortal").
- Over long-lived projects (hundreds of sessions), the number of immortal events can grow without bound.
- **Risk:** Projection engine must include "ALL immortal events" in the briefing (paper §9.5). If there are 500 decisions, the briefing can exceed the token budget (F2.1), or force heavy truncation that undermines "never lose decisions."

**Gotcha:** The plan does not define: cap on immortal events, summarization of old decisions, or moving them to a separate "decisions.md" that is loaded in a budget-aware way. This is a latent conflict between "immortal" and "token-budget-aware."

### 2.3 Reality Anchoring — Mechanism Underspecified

- **M3** (F4.4): "Compare package.json / pyproject.toml against memorized tech stack" and "If CONFLICTS detected → add [CONFLICT] warning."
- Memory is free text (e.g., "using PostgreSQL"); config files are structured. Matching "memory assertions" to "current stack" is an **NLP/entity-matching problem**, not a simple string compare.

**Gotcha:** Without a specified mechanism (e.g., keyword extraction from memory + parsing of known config fields), the mitigation is aspirational. Implementation could be brittle (false positives/negatives) or never fully built.

### 2.4 Confidence and Decay as Magic Numbers

- "Events below 0.5 confidence are excluded from projections" (M4).
- Decay rates: 0.995/hour, 0.998/hour for some types; "confidence decay" 0.99^sessions.

**Gotcha:** No sensitivity analysis, no tuning strategy, and no data from real sessions. These thresholds could be wrong in practice; the plan would be stronger with "tunable via config" and "evaluate on a small set of real sessions" in the implementation strategy.

### 2.5 Concurrent Sessions and Event Ordering

- **F3.2** mentions "two Claude Code sessions on same project" and SQLite concurrency (WAL).
- The plan does not address: **event ordering** when two sessions write events (e.g., same project, two windows or pair programming), **merge semantics** for the event log, or **briefing consistency** when projections are computed while another session is appending.

**Gotcha:** Multi-tab or multi-user scenarios could produce duplicated, reordered, or confusing events and briefings. At minimum, the implementation strategy should call out "single-writer per project" or document merge/ordering rules.

### 2.6 Tier 0 and Cross-Platform / Environment

- Tier 0: "Single Python script, no dependencies beyond stdlib," "30 seconds" install.
- Assumes `python3` in PATH, and that hook payloads are available to that script (e.g., via stdin/env/file). No mention of **Windows** (paths, Python launcher), **Python 2 vs 3**, or **virtualenv** (user's project may use a venv; hooks might run system Python).

**Gotcha:** "Zero install" could break on Windows or in locked-down environments. A short "Supported environments" and "How hooks receive payloads" would reduce implementation surprises.

---

## 3. What Was Not Included (Should Have Been)

### 3.1 Validation of Claude Code Hook API and Payloads

- No pointer to official docs for hook **names**, **payload schema**, and **when** each hook runs.
- No appendix or table: "We need from Stop: conversation snippet / tool calls / …; we need from PreCompact: …; we need from SessionStart: …."
- **Recommendation:** Add a "Hook API requirements" section and a pre-implementation step to validate against the actual Claude Code (or Cursor) version.

### 3.2 Privacy, Retention, and Sensitive Data

- Events may contain: file paths, code snippets, user messages, repo names.
- No discussion of: **PII**, **secrets** (e.g., in pasted configs), **retention** (how long to keep events), or **deletion** (user wants to "forget" a project).
- **Recommendation:** Add a "Data and privacy" subsection: what is stored, where, retention, and how to purge. FR-10 (user override/correction) implies deletability but it is not designed in mitigations.

### 3.3 Measurable Success and Evaluation

- Success criteria are defined (e.g., cold start −80%, near-zero decision regression).
- There is **no plan for measurement**: no baseline data collection, no A/B design, no instrumentation (e.g., "time to first useful action," "count of re-suggested rejected approaches").
- **Recommendation:** Add "Evaluation plan" to implementation strategy: what to log, how to compute metrics, and how to compare "Cortex on" vs "Cortex off" (or Tier 0 vs Tier 2).

### 3.4 Testing Strategy

- No discussion of: **unit tests** for Layer 2 pattern matching (fixture responses → expected events), **projection tests** (fixture event set → expected briefing shape/size), or **integration tests** (mock hook payloads → full pipeline).
- **Recommendation:** Add "Testing" to implementation strategy so that regressions (e.g., new Claude response styles breaking keyword extraction) are caught.

### 3.5 User Correction and Reset

- FR-10: "Support user override/correction of stored context" (SHOULD).
- Mitigations do not describe: **editing** a stored event, **deleting** an event or a session, or **resetting** all memory for a project.
- **Recommendation:** Specify at least: "User can delete/edit events or reset project memory via CLI or a simple UI," and how that affects snapshots and projections.

### 3.6 Offline / Air-Gapped and Resource-Constrained Environments

- Tier 2 requires downloading an embedding model (~90MB).
- No mention of **air-gapped** or **restricted network** environments (common in enterprises).
- No **minimum system requirements** (e.g., RAM for SentenceTransformers); low-resource machines may OOM or be very slow.
- **Recommendation:** Short subsection on "Offline / locked-down environments" and "Minimum resources for Tier 2/3."

### 3.7 Ordering of Loaded Context

- Both user CLAUDE.md and `.claude/rules/cortex-briefing.md` are loaded; **order** is not specified.
- Order can affect how strongly the model weighs the briefing vs. user rules.
- **Recommendation:** Document the intended load order and, if possible, cite Claude Code behavior so implementers and users can reason about precedence.

### 3.8 Non-English and Localization

- Layer 2 keyword extraction is English-centric ("chose X over Y," "decided to," "rejected").
- No mention of **non-English** sessions or localization of patterns.
- **Recommendation:** Either note "Layer 2 is English-only; Layer 1 and 3 are language-agnostic" or add "Future work: multilingual keyword patterns."

### 3.9 Generalizability Beyond Claude Code

- Solution is tied to **Claude Code** (hooks, CLAUDE.md, .claude/rules/).
- No brief "portability" discussion: what would need to change for **Cursor**, **Windsurf**, or other IDEs (different hooks, different rule injection).
- **Recommendation:** A short "Applicability to other assistants" subsection would make the research more generalizable and clarify scope.

### 3.10 Git-Tracked Projections and Merge Conflicts

- Chronicle's idea of git-tracked projections is "incorporated" into Cortex (Tier 3).
- Machine-generated markdown (e.g., `cortex-briefing.md` or `decisions.md`) in git will **merge conflict** when branches diverge.
- No strategy for: conflict resolution, or "regenerate from event store on merge" vs. "manual resolve."
- **Recommendation:** Add a note under Tier 3: "If projections are git-tracked, define merge strategy (e.g., always take one branch and regenerate, or mark as generated and avoid tracking)."

---

## 4. Summary: Highest-Priority Gaps

| Priority | Issue | Action |
|----------|--------|--------|
| **P0** | Hook API (including UserPromptSubmit) not validated | Validate against real Claude Code docs/runtime before building Tier 2 |
| **P0** | No way to measure success criteria | Add evaluation plan (metrics, baseline, instrumentation) |
| **P1** | Immortal events can grow unbounded | Define cap or summarization/archival for old decisions |
| **P1** | Reality anchoring mechanism unspecified | Specify matching approach (e.g., keywords + config parsing) or scope it to "future work" |
| **P1** | No testing strategy | Add unit/projection/integration test plan to implementation strategy |
| **P2** | Privacy, retention, user correction not designed | Add data/privacy subsection and FR-10 design (edit/delete/reset) |
| **P2** | Concurrent sessions / event ordering | Document single-writer assumption or merge/ordering rules |
| **P2** | Environment and platform (Windows, offline, resources) | Add "Supported environments" and "Offline / resources" notes |

---

## 5. Conclusion

The Cortex research is **strong on problem framing, architecture choice, and failure-mode coverage**. The main risks are **dependency on an unvalidated hook API**, **unbounded growth of immortal events**, **underspecified mechanisms** (reality anchoring, tuning), and **missing operational and evaluation design** (measurement, testing, privacy, user correction). Addressing the P0 and P1 items above would make the plan more robust and implementable without changing the core architecture.
