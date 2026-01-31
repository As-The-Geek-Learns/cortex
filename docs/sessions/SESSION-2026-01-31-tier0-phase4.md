# Session Notes: Tier 0 Implementation — Phase 4 (Three-Layer Extraction) + CI Fixes

**Date:** 2026-01-31
**Duration:** ~45 minutes (across two context windows)
**Model:** Claude Opus 4.5
**Project Phase:** Implementation — Tier 0, Phase 4 of 8

---

## What Was Accomplished

Built the complete three-layer event extraction pipeline that converts parsed TranscriptEntries into Cortex Events. This is Phase 4 of the 8-phase implementation plan — the intelligence layer that decides what's worth remembering. Also diagnosed and fixed two CI failures that had been broken since the project's first commit. All 287 tests pass, all 5 CI jobs green.

### Files Created (2 files)

| File | Lines | Purpose |
|------|-------|---------|
| `src/memory_context_claude_ai/extractors.py` | 392 | Three-layer extraction pipeline + deduplicating orchestrator |
| `tests/test_extractors.py` | 838 | 79 comprehensive tests across 10 test classes |

### Files Modified (6 files)

| File | What Changed |
|------|-------------|
| `src/memory_context_claude_ai/__init__.py` | Added 4 new public API exports (extract_events, extract_structural, extract_semantic, extract_explicit) |
| `.github/workflows/ci.yml` | Replaced gitleaks-action@v2 with direct CLI invocation (org license fix) |
| `src/memory_context_claude_ai/transcript.py` | Ruff import sorting fix (I001) |
| `tests/test_config.py` | Ruff formatting fix |
| `tests/test_store.py` | Removed 5 unused imports (F401) |
| `tests/test_transcript.py` | Ruff import sorting + removed 2 unused imports |

---

## Key Components Built

### Three-Layer Extraction Architecture

The pipeline processes TranscriptEntries through three independent layers, each producing `list[Event]`. The orchestrator runs all three and deduplicates by content hash.

```
TranscriptEntry ──┬── Layer 1 (Structural) ──→ Events from tool observations
                  ├── Layer 2 (Semantic)   ──→ Events from keyword patterns
                  └── Layer 3 (Explicit)   ──→ Events from [MEMORY:] tags
                                                    │
                                              _deduplicate()
                                                    │
                                              Final Event List
```

### Layer 1: Structural Extraction (`extract_structural`)
Observes tool calls in assistant entries and maps them to event types:

| Tool | Event Type | Content Example |
|------|-----------|----------------|
| Write, Edit | FILE_MODIFIED | `Modified: src/main.py` |
| Bash | COMMAND_RUN | `npm test` |
| Read, Glob, Grep | FILE_EXPLORED | `Explored: src/main.py` |
| TodoWrite | PLAN_CREATED | `[x] Task A\n[ ] Task B` |

Also extracts PLAN_STEP_COMPLETED from TodoWrite tool results by comparing `oldTodos` vs `newTodos` in the `toolUseResult` metadata envelope.

### Layer 2: Semantic Extraction (`extract_semantic`)
Scans assistant text (after `strip_code_blocks()`) for keyword patterns:

| Pattern | Event Type | Confidence |
|---------|-----------|------------|
| `Decision: ...` | DECISION_MADE | 0.85 |
| `Rejected: ...` | APPROACH_REJECTED | 0.85 |
| `Fixed: ...` | ERROR_RESOLVED | 0.75 |
| `Error resolved: ...` | ERROR_RESOLVED | 0.70 |
| `Learned/Lesson/TIL: ...` | KNOWLEDGE_ACQUIRED | 0.70 |
| `Preference: ...` | PREFERENCE_NOTED | 0.80 |

Patterns match at line start with optional bold markers (`**Decision:**`). Code blocks are stripped first to prevent false positives from variable names and syntax.

### Layer 3: Explicit Extraction (`extract_explicit`)
Extracts `[MEMORY: content]` tags from both user and assistant messages. Gets the highest confidence (1.0) because these represent deliberate intent to preserve information.

### Pipeline Orchestrator (`extract_events`)
Runs all three layers per entry, collects results, and deduplicates via `content_hash()` from Phase 1. Content hash is scoped to `type + content + session_id`, so the same fact repeated in different sessions is preserved (repetition = signal).

---

## Key Decisions Made

### Design Decision: Confidence Scoring for Semantic Patterns
**Chosen:** Different confidence levels per keyword type (0.70–0.85).
**Why:** "Decision:" explicitly signals a decision was made (high confidence). "Learned:" is more ambiguous — it could be a section header, a comment, etc. (lower confidence). The briefing generator will use confidence to prioritize what gets included in the context budget.
**Tradeoff:** Hard-coded confidence values will need tuning based on real-world usage. Could become a config option later.

### Design Decision: Only Scan Assistant Text for Semantics
**Chosen:** Layer 2 only processes `is_assistant` entries.
**Why:** Users don't typically write "Decision: Use SQLite" in their messages — that's assistant output. User intent is captured by Layer 3 ([MEMORY:] tags) instead. This prevents false positives from user messages that might quote documentation or paste code containing these keywords.
**Tradeoff:** If a user writes "Decision: We're going with SQLite" without the [MEMORY:] tag, Layer 2 won't capture it. Acceptable because Layer 3 covers deliberate user input.

### Design Decision: Strip Code Blocks Before Keyword Matching
**Chosen:** Use `strip_code_blocks()` (from Phase 3) before running semantic patterns.
**Why:** Code blocks contain variable names, comments, and syntax that match keyword patterns. A Python comment `# Decision: use dict over list` inside a code block isn't a project decision — it's source code. Stripping prevents false positives.
**Tradeoff:** If an assistant describes a decision inside a code block, it's lost. This is acceptable because decisions should be stated in prose, not buried in code.

### Design Decision: Deduplication at Pipeline Level
**Chosen:** `_deduplicate()` runs after all three layers complete, using `content_hash()`.
**Why:** The same fact could be captured by multiple layers (e.g., an assistant says "Decision: Use SQLite" AND uses a [MEMORY:] tag). Without dedup, the briefing would contain duplicates. Pipeline-level dedup is simpler than cross-layer coordination.
**Tradeoff:** First-writer-wins — if Layer 1 and Layer 3 both produce an event for the same content, whichever ran first is kept. Since layers run in order (structural → semantic → explicit), structural events take priority.

---

## CI Fixes

### Fix 1: Ruff Linting Failures (Python Quality Job)

**Problem:** 12 Ruff errors had been present since the first commit but were never caught because CI wasn't being monitored. Errors included:
- Import sorting (I001): `transcript.py`, `test_transcript.py`, `test_extractors.py`
- Unused imports (F401): `test_store.py` (5 unused: datetime, timedelta, timezone, Path, Event), `test_transcript.py` (2 unused: transcript_mod), `test_extractors.py` (2 unused: pytest, content_hash)
- Formatting inconsistencies in 5 files

**Fix:** `ruff check --fix` + `ruff format .` — all auto-fixable.

[ASTGL CONTENT] **Always run your linter locally before pushing.** These errors were present from commit #1 and accumulated over 3 commits before anyone noticed. Adding `ruff check . && ruff format --check .` to a pre-commit hook (or even just a habit) would have caught them immediately. The earlier you catch lint errors, the smaller the fix.

### Fix 2: Gitleaks License Requirement (Secrets Scan Job)

**Problem:** `gitleaks/gitleaks-action@v2` requires a paid license for GitHub organization accounts. The repo is under `As-The-Geek-Learns` (an org), so the action fails with: `"[As-The-Geek-Learns] is an organization. License key is required."`

**Fix:** Replaced the GitHub Action with direct CLI invocation. The gitleaks CLI tool is free and open-source — only the GitHub Action wrapper requires a paid license for orgs. The new approach downloads a specific gitleaks release binary and runs `gitleaks detect --source . --verbose`.

[ASTGL CONTENT] **GitHub Action ≠ Underlying Tool.** Many security scanning GitHub Actions are monetized wrappers around free open-source CLI tools. When a GitHub Action fails with a license error, check if the underlying tool can be invoked directly. Common examples: gitleaks (CLI free, Action paid for orgs), Snyk (CLI has free tier, Action limits vary), SonarQube (CE free, Action requires license). Running the CLI directly gives you the same scanning at no cost.

---

## Concepts & Patterns Applied

### Multi-Layer Extraction with Independent Layers
Each extraction layer is a standalone pure function: `(TranscriptEntry, context) → list[Event]`. They don't depend on each other, can't interfere with each other, and can be tested independently. The orchestrator is the only point of coordination (dedup). This design makes it trivial to add a Layer 4 later without touching existing code.

[ASTGL CONTENT] **The "many independent extractors" pattern** is common in NLP pipelines, content classification, and log analysis. Each extractor looks for one signal type. They compose through simple aggregation + dedup. The alternative — a single monolithic extractor with complex branching — becomes unmaintainable as the number of signal types grows.

### Regex with Line-Start Anchoring for Keyword Patterns
The semantic patterns use `(?m)^\s*\*{0,2}Keyword:\s*(.+)` which matches at the start of a line (after optional whitespace and bold markers). This dramatically reduces false positives vs. matching anywhere in text. A mid-sentence "we rejected the idea" doesn't match, but `Rejected: the idea` at line start does.

### Confidence as a First-Class Signal
Every event carries a `confidence` float (0.0–1.0). Structural events get 1.0 (tool calls are unambiguous). Semantic events get 0.70–0.85 (keyword matching has uncertainty). Explicit events get 1.0 (deliberate user/assistant intent). The briefing generator (Phase 5) will use this to prioritize within the context budget.

### TodoWrite Diff Detection
PLAN_STEP_COMPLETED events are detected by comparing `oldTodos` vs `newTodos` in the toolUseResult metadata. This is a diff-based approach: find items in `new_completed - old_completed`. The alternative (tracking todo state over time) would require stateful parsing — the diff approach is stateless and simpler.

---

## Test Coverage Summary

```
287 passed in 0.97s

tests/test_config.py       .......................          23 tests
tests/test_extractors.py   ................................ 79 tests  <- NEW
tests/test_models.py       .................................  33 tests
tests/test_placeholder.py  .                                 1 test
tests/test_project.py      .................                17 tests
tests/test_store.py        ......................................  38 tests
tests/test_transcript.py   ................................  96 tests
```

### Test Classes in test_extractors.py (10 classes, 79 tests)

| Class | Tests | What It Covers |
|-------|-------|----------------|
| `TestExtractStructural` | 15 | All 6 tool types (Write, Edit, Bash, Read, Glob, Grep, TodoWrite), unknown tools, session/branch/project propagation |
| `TestExtractPlanStepCompletions` | 6 | Step detection from oldTodos/newTodos diff, empty old, no change, already completed |
| `TestExtractSemantic` | 18 | All 6 keyword patterns, bold markers, code block filtering, non-assistant ignored, thinking blocks, edge cases |
| `TestExtractExplicit` | 8 | User/assistant [MEMORY:] tags, multiple tags per entry, empty/non-message entries |
| `TestFormatTodos` | 4 | Mixed statuses, empty list, non-dict items, missing content |
| `TestDeduplicate` | 6 | Identical events, different content/type/session, empty list, order preservation |
| `TestSemanticPatterns` | 2 | SEMANTIC_PATTERNS constant validation (all tuples, all compiled) |
| `TestExtractEventsPipeline` | 6 | Multi-layer integration, cross-layer dedup, empty entries, session isolation |
| `TestFixtureSimple` + `TestFixtureDecisions` | 5 | End-to-end extraction from simple.jsonl and decisions.jsonl fixtures |
| `TestFixtureMemoryTags` + `TestFixtureMixed` | 9 | End-to-end extraction from memory_tags.jsonl and mixed.jsonl fixtures |

---

## ASTGL Content Moments

1. **[ASTGL CONTENT] Run Your Linter Locally** — 12 Ruff errors accumulated over 3 commits because nobody ran `ruff check .` locally. CI caught them, but nobody was watching CI. Two lessons: (a) add a pre-commit hook for linting, and (b) check CI status after every push, not just when you remember.

2. **[ASTGL CONTENT] GitHub Action ≠ Free CLI Tool** — The gitleaks GitHub Action requires a paid license for org accounts, but the gitleaks CLI is completely free. Many security scanning actions monetize the GitHub integration while the underlying tool remains open-source. Always check if you can run the CLI directly before paying for the wrapper.

3. **[ASTGL CONTENT] The Independent Extractors Pattern** — Building separate extraction layers that each look for one signal type, then aggregating + deduplicating, is simpler and more maintainable than a monolithic extractor. Each layer can be tested independently, added/removed without affecting others, and tuned separately. This pattern appears across NLP, log analysis, and content classification systems.

4. **[ASTGL CONTENT] Confidence as Architecture** — Making confidence a first-class field on every event (not just a boolean "is this relevant?") enables much richer downstream behavior. The briefing generator can sort by confidence, the decay function can weight it, and users can tune the threshold. A little extra data at creation time enables a lot of flexibility at consumption time.

5. **[ASTGL CONTENT] Code Block Stripping Order Matters** — When removing code blocks before keyword matching, fenced blocks (```) must be removed before inline code (`` ` ``). Doing it backwards breaks fenced block detection because the opening/closing triple backticks get consumed as inline code spans first. Order-dependent regex pipelines are a common source of subtle bugs.

---

## What's Next: Phase 5 — Briefing Generation

Phase 5 builds the briefing generator that converts stored events into a markdown context document loaded at session start. This is where the memory system produces its output.

### What Phase 5 Will Build
- `briefing.py` — Markdown briefing generator:
  - Reads events from EventStore using `load_for_briefing()`
  - Formats into structured sections (Decisions, Active Plans, Recent Context)
  - Respects the `briefing_budget` config (max tokens/characters)
  - Renders as markdown for the `cortex-briefing.md` rules file

### Key Design Questions for Phase 5
- How to format events into readable markdown that Claude can consume efficiently?
- Token/character budget management — how to prioritize when events exceed the budget?
- Should the briefing include metadata (timestamps, confidence) or just content?
- How to handle the immortal vs. recent event sections in the markdown structure?

### Preparation Done
- `EventStore.load_for_briefing()` already returns events in three sections: immortal, active_plan, recent
- `CortexConfig.briefing_budget` sets the character limit
- All events carry confidence, salience, and metadata for prioritization
- The extraction pipeline (this phase) provides the events that feed the briefing

---

## Project Status After This Session

```
Phase 1: Foundation (models, config, project)      ████████████████ DONE (33+23+17 tests)
Phase 2: Storage (store, hook state)                ████████████████ DONE (38 tests)
Phase 3: Transcript Parser                          ████████████████ DONE (96 tests)
Phase 4: Three-Layer Extraction                     ████████████████ DONE (79 tests)
Phase 5: Briefing Generation                        ░░░░░░░░░░░░░░░░ NEXT
Phase 6: Hook Handlers                              ░░░░░░░░░░░░░░░░ Pending
Phase 7: CLI + Installer                            ░░░░░░░░░░░░░░░░ Pending
Phase 8: Integration Tests                          ░░░░░░░░░░░░░░░░ Pending
```

**6 source modules built, 287 tests passing, 0 external dependencies, all 5 CI jobs green.**

---

## Next Session Bootstrap Prompt

Copy-paste this to start the next session with full context for Phase 5:

```
Read the project CLAUDE.md, then read these files to understand the project state:

1. docs/sessions/SESSION-2026-01-31-tier0-phase1-2.md (Phases 1-2 context)
2. docs/sessions/SESSION-2026-01-31-tier0-phase3.md (Phase 3 context)
3. docs/sessions/SESSION-2026-01-31-tier0-phase4.md (Phase 4 context, includes Phase 5 preview)
4. src/memory_context_claude_ai/__init__.py (public API surface)

Then start building Phase 5: Briefing Generation (briefing.py).

Phase 5 builds the markdown briefing generator that converts stored events
into a context document loaded at session start via cortex-briefing.md.

Key context:
- 287 tests passing across 6 source modules, all 5 CI jobs green
- store.py provides: EventStore.load_for_briefing() → {immortal, active_plan, recent}
- config.py provides: CortexConfig.briefing_budget (character limit)
- extractors.py provides: extract_events() → deduplicated Event list
- models.py provides: Event with salience, confidence, metadata, effective_salience()
- Run `ruff check . && ruff format --check .` before committing to avoid CI failures
```
