# Evaluation Response: Addressing the External Critique

**Date:** 2026-01-31
**Purpose:** Systematic response to each item in `external-evaluation.md`, documenting what was changed, what was deferred, and why.

---

## Response Methodology

Each evaluation item was assessed for:
1. **Validity** — Is the critique correct?
2. **Severity** — Does it affect the core architecture or just implementation details?
3. **Action** — Change the plan now, or acknowledge as a known limitation / future work?

Additional research was conducted to validate the P0 hook API concern against official Claude Code documentation (January 2026).

---

## P0 Items: Addressed in Full

### 2.1 — Hook API Not Validated Against Real Claude Code

**Verdict: VALID concern, but the plan's assumptions are CORRECT.**

Research against official Claude Code hook documentation confirms all four hooks exist with the required payloads:

| Hook | Status | Key Payload |
|------|--------|-------------|
| `Stop` | Confirmed | `transcript_path` for conversation access |
| `PreCompact` | Confirmed | `trigger` ("manual"/"auto") |
| `SessionStart` | Confirmed | `source` ("startup"/"resume"/"compact") |
| `UserPromptSubmit` | Confirmed | `prompt` (user's full message text) |

The evaluation was right that the plan didn't cite sources or show validation. This has been fixed:

**Changes made:**
- **Paper §9.8**: Updated hook configuration section with validated payload table and data flow documentation
- **Paper Appendix E**: New appendix with full hook API validation, payload schemas, and source citations
- **MASTER-PLAN.md**: Added Decision #9 (Hook API validated)

**Residual risk:** Hook payloads could change in future Claude Code versions. The implementation should include a version check and graceful degradation if expected fields are missing.

---

### 3.3 — No Evaluation/Measurement Plan

**Verdict: FULLY VALID.**

The plan defined success criteria (cold start -80%, near-zero decision regression) but had zero instrumentation or measurement strategy. This was a genuine gap.

**Changes made:**
- **Paper §11.4**: New section "Evaluation & Measurement Plan" covering:
  - Baseline collection (5-10 sessions without Cortex)
  - Instrumented metrics table (6 metrics with measurement method and targets)
  - A/B comparison protocol (10 sessions with vs. 10 without)
  - Decay parameter calibration plan (after 20+ sessions)
- **MASTER-PLAN.md**: Added Decision #12 (Evaluation-first implementation)
- **MASTER-PLAN.md**: Updated next action to "start with baseline collection per §11.4"

---

## P1 Items: Addressed with Design Changes

### 2.2 — Immortal Events → Unbounded Growth

**Verdict: VALID. Latent conflict between "immortal" and "token-budget-aware."**

The evaluation correctly identified that 500+ immortal decisions could overflow the briefing's token budget, creating a contradiction with the immortality guarantee.

**Changes made:**
- **Paper §9.4**: New "Immortal Event Growth Management" subsection with tiered strategy:
  - Active decisions (last 20 sessions): full text in briefing
  - Aging decisions (20-50 sessions, unaccessed): one-line summaries
  - Archived decisions (50+ sessions, unaccessed): excluded from briefing, stored in `decisions-archive.md`
  - Configurable cap: 50 full + 30 summarized, 40% of token budget
  - Promotion: accessed archived decisions return to "active" status
- **Paper §9.5**: Updated projection algorithm with immortal event budget allocation
- **09-mitigations.md (M5)**: Completely rewritten with growth management strategy
- **MASTER-PLAN.md**: Added Decision #10 (Immortal events with growth management)

**Key insight:** "Immortal" means "never deleted from the event store," not "always in the briefing." Decisions are permanently retained but progressively compressed in their briefing representation.

---

### 2.3 — Reality Anchoring Mechanism Underspecified

**Verdict: VALID. The original description was aspirational.**

"Compare config files against memory" is an NLP entity-matching problem if done in the general case. The evaluation was right to flag this.

**Changes made:**
- **Paper §9.9**: Replaced vague description with four bounded, deterministic checks:
  1. Git branch: exact string match
  2. Dependency keywords: parse structured config files, compare against keyword→package lookup table
  3. File existence: verify referenced files still exist
  4. Recency: detect external changes since last session
- **09-mitigations.md (M3)**: Rewritten with the same concrete mechanism
- **MASTER-PLAN.md**: Added Decision #11 (Bounded reality anchoring)

**Design choice:** We deliberately avoided open-ended NLP matching in favor of structured-data-to-structured-data comparison. This is less powerful but far more reliable and implementable.

---

### 2.4 — Confidence and Decay as Magic Numbers

**Verdict: VALID.**

No tuning strategy was documented. The numbers (0.995/hour, 0.5 cutoff) were presented as if they were empirically derived when they're actually informed estimates.

**Changes made:**
- **Paper §9.4**: Added tuning note — all parameters are configurable and should be calibrated from real session data
- **Paper §11.4**: Calibration phase added to evaluation plan (after 20+ sessions)
- **09-mitigations.md (M4)**: Added tuning note with explicit statement that values are estimates requiring calibration
- **MASTER-PLAN.md**: Added Decision #13 (Decay parameters are tunable)

---

### 3.4 — No Testing Strategy

**Verdict: VALID.**

The implementation strategy had no testing plan, which is a gap for a system whose accuracy depends on pattern matching that could break as Claude's output evolves.

**Changes made:**
- **Paper §11.5**: New section "Testing Strategy" with three levels:
  - Unit tests: fixture-based tests for each extraction layer, decay math, archival logic
  - Projection tests: event sets → expected briefing structure and token counts
  - End-to-end tests: mock hook payloads → full pipeline verification
  - Regression triggers: monthly runs against saved real transcripts

---

## P2 Items: Acknowledged as Limitations or Future Work

These items are valid but don't require changes to the core architecture. They've been documented as known limitations (§12.5) or future work (§13).

### 3.2 — Privacy, Retention, Sensitive Data

**Action:** Added as Limitation #8 and Future Work §13.7 (Privacy and Data Controls).
Basic `cortex reset --project` command planned for Tier 0; comprehensive privacy controls deferred.

### 2.5 — Concurrent Sessions and Event Ordering

**Action:** Added as Limitation #6 (Single-writer assumption). Future Work §13.8 describes multi-writer support with advisory locking and Lamport timestamps.

### 2.6 — Cross-Platform / Environment

**Action:** Added Paper §11.6 "Supported Environments" covering macOS/Linux (primary), Windows (best-effort), offline/air-gapped (Tiers 0-1 work fully offline), and minimum resources for Tier 2.

### 3.5 — User Correction and Reset

**Action:** Added as Future Work §13.6 with specific CLI commands (`cortex forget`, `cortex edit`, `cortex reset`, `cortex export`).

### 3.6 — Offline / Air-Gapped Environments

**Action:** Covered in new §11.6. Tiers 0-1 are fully offline. Tier 2 model can be side-loaded.

### 3.7 — Context Loading Order

**Action:** Added as Limitation #9. Claude Code loads `.claude/rules/` files additively alongside CLAUDE.md. Exact precedence is determined by Claude Code's internals. Epistemic humility markers mitigate conflicts.

### 3.8 — Non-English and Localization

**Action:** Added as Limitation #7 (English-centric extraction) and Future Work §13.9 (Multilingual Extraction). Layers 1 and 3 are already language-agnostic.

### 3.9 — Generalizability Beyond Claude Code

**Action:** Added as Limitation #5 (expanded) and Future Work §13.4 (expanded with adapter architecture note).

### 3.10 — Git-Tracked Projections and Merge Conflicts

**Action:** Added as Limitation #10 with recommended strategy: treat projections as generated artifacts, regenerate from event store on merge conflict.

---

## Summary of Changes Made

### Documents Modified

| Document | Changes |
|----------|---------|
| `paper/cortex-research-paper.md` | §9.4 (immortal growth management), §9.5 (projection algorithm), §9.8 (hook validation), §9.9 (reality anchoring), §11.4 (evaluation plan — NEW), §11.5 (testing strategy — NEW), §11.6 (supported environments — NEW), §12.5 (10 limitations, up from 5), §13 (9 future work items, up from 5), Appendix E (hook API validation — NEW) |
| `phases/09-mitigations.md` | M3 (concrete reality anchoring), M4 (tuning note), M5 (immortal growth management) |
| `MASTER-PLAN.md` | Phase tracker (2 new phases), Key Decisions (5 new decisions, #9-13), Cross-session index updates |

### New Documents Created

| Document | Purpose |
|----------|---------|
| `evaluation/evaluation-response.md` | This document — systematic response to all evaluation items |

### Items NOT Changed

The core architecture (event sourcing, three-layer extraction, projected briefings, progressive tiers) is **unchanged**. The evaluation validated the architectural choices. All changes are additions (new sections, expanded limitations, future work) or refinements (concrete mechanisms replacing vague descriptions).

---

## Conclusion

The external evaluation was high-quality and identified genuine gaps. The two P0 items (hook API validation and evaluation plan) were the most important — one was a validation gap (the assumptions were correct but undocumented) and the other was a genuine design omission (no measurement strategy). Both are now addressed.

The P1 items (immortal event growth, reality anchoring, testing) required design refinements that strengthen the plan without changing the architecture. The P2 items are appropriately scoped as acknowledged limitations and future work.

The Cortex design is now more robust and implementable. The next step remains: **implement Tier 0, starting with baseline data collection per §11.4.**
