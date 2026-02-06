# Session Notes: Phase 3 Baseline Data Collection Automation

**Date:** 2026-02-05
**Project Phase:** Testing — Phase 3 Automation Scripts

---

## What Was Accomplished

Built a hybrid automation suite for Phase 3 baseline data collection. Phase 3 requires running 5-10 real dev sessions **without** Cortex enabled, then recording 4 metrics per session. Two of those metrics are objective and can be auto-extracted from Claude Code's JSONL transcripts; two are subjective and require human input.

### Key Insight

Phase 3 metrics split cleanly into two categories:

| Metric | Type | Automation |
|--------|------|-----------|
| Cold start time | **Objective** | Auto-extracted: first entry timestamp vs first Write/Edit/Bash tool call |
| Re-exploration count | **Objective** | Auto-extracted: intersection of files explored across sessions |
| Decision regression count | Subjective | Manual input prompt |
| Continuity score (1-5) | Subjective | Manual input prompt |

By reusing `cortex.transcript` as library code (not through hooks), we can parse real transcripts and extract tool calls without needing Cortex hooks enabled. The transcript module is purely a parser — it doesn't depend on hook infrastructure.

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/testing/transcript_analyzer.py` | 232 | `TranscriptAnalyzer` class + `TranscriptMetrics` dataclass |
| `scripts/testing/session_recorder.py` | 252 | `BaselineDataStore` (JSON persistence) + `SessionRecorder` (interactive CLI) |
| `scripts/testing/baseline_reporter.py` | 250 | `BaselineReporter` — generates filled-in BASELINE-DATA-TEMPLATE.md |
| `scripts/testing/run_phase3.py` | 270 | Main entry point with 5 subcommands (record, list, summary, report, reset) |
| **Total** | **1,004** | |

Also updated `.gitignore` to exclude `baseline-data.json` (contains local file paths).

---

## Architecture Decisions

### Decision: Reuse cortex.transcript as library code

**Context:** Phase 3 has Cortex hooks disabled. Could either: (a) duplicate the transcript parsing logic in the test scripts, or (b) import `cortex.transcript` directly.

**Decision:** Import `TranscriptReader`, `extract_tool_calls()`, `find_transcript_path()`, and `find_latest_transcript()` directly from `cortex.transcript`.

**Why:** The transcript module is a pure parser with no side effects — it doesn't depend on hooks, config, or event storage. Using it directly means zero code duplication and automatic compatibility with any future transcript format changes. This also validates that the module's API is clean enough for library-style usage.

### Decision: Hybrid auto-extraction + manual prompts

**Context:** Phase 3 has 4 metrics. Could make everything manual (like the template), or try to fully automate (which would require AI judgment for subjective metrics).

**Decision:** Auto-extract the 2 objective metrics, prompt interactively for the 2 subjective ones.

**Why:** Cold start time is a simple timestamp diff (first entry → first meaningful tool call). Re-exploration is a set intersection across sessions. Both are deterministic and faster/more accurate than human estimation. Decision regression and continuity score genuinely require human judgment about the quality of Claude's responses — there's no objective way to measure "did Claude re-debate a prior decision?"

**Tradeoff:** The interactive prompts mean `run_phase3 record` can't be fully automated in CI. But that's inherent to Phase 3's purpose — it measures human-perceived quality.

### Decision: JSON storage over SQLite

**Context:** Need to persist session data across recording runs. Options: SQLite (like EventStore), JSON file, or CSV.

**Decision:** Plain JSON file (`baseline-data.json`) with automatic summary recomputation on save.

**Why:** The data volume is tiny (5-10 sessions, ~1KB each). JSON is human-readable and debuggable. No external dependencies needed. Summary stats are recomputed on every save, so the data file is always self-consistent. Added to `.gitignore` since it contains local file paths.

### Decision: Cross-session re-exploration in SessionRecorder, not TranscriptAnalyzer

**Context:** Re-exploration count requires comparing files explored in the current session against all prior sessions. Could put this logic in TranscriptAnalyzer or in SessionRecorder.

**Decision:** `TranscriptAnalyzer` returns `files_explored` as a set. `SessionRecorder` computes the intersection with cumulative prior files from `BaselineDataStore`.

**Why:** Single responsibility — the analyzer handles one transcript, the recorder handles cross-session state. This also makes TranscriptAnalyzer independently testable and reusable for Phase 4.

---

## Validation Results

Tested with a real 2.7MB transcript from the current session:

| Metric | Value |
|--------|-------|
| Cold start time | 8.2 minutes |
| Session duration | 53.5 minutes |
| Tool calls | 121 |
| Files explored | 25 |
| Files modified | 13 |
| Re-exploration count | 0 (first session) |

All 5 subcommands work correctly: `record`, `list`, `summary`, `report`, `reset`.

Regression check: **331/331 existing tests passing**, **5/5 Phase 2 tests passing**.

---

## How to Run

```bash
cd /Users/jamescruce/Projects/cortex

# After ending a baseline dev session (Cortex hooks disabled):
python -m scripts.testing.run_phase3 record

# Check progress:
python -m scripts.testing.run_phase3 list
python -m scripts.testing.run_phase3 summary

# Generate final report (after 5-10 sessions):
python -m scripts.testing.run_phase3 report

# Reset all data:
python -m scripts.testing.run_phase3 reset
```

---

## Concepts & Patterns Learned

### Library Code vs. Application Code
The `cortex.transcript` module was written as part of the hook pipeline, but its functions (`TranscriptReader.read_all()`, `extract_tool_calls()`, `find_transcript_path()`) turned out to be clean library code with no side effects. This meant we could reuse it in a completely different context (Phase 3 analysis scripts) without any modification. The lesson: functions that take inputs and return outputs (no global state, no I/O side effects beyond file reading) are naturally reusable.

### Hybrid Automation
Not everything needs to be fully automated. When some metrics are objective and some are subjective, the best UX is to auto-extract what you can and prompt for the rest. This is faster than fully manual (saves ~60% of the data entry) and more accurate than trying to automate judgment calls.

### Data Store Design for Small Datasets
For tiny datasets (5-10 records), JSON files beat databases. They're human-readable (you can `cat` the file to debug), require zero dependencies, and support the exact schema you need without ORM mapping. The key design choice: recompute summary stats on every save so the file is always self-consistent.

---

## ASTGL Content Moments

1. **[ASTGL CONTENT] Reusing application code as library code:** If your functions take inputs and return outputs without side effects, they're automatically reusable. The Cortex transcript parser was built for hooks but works perfectly for standalone analysis scripts. The design principle: avoid global state and I/O side effects in your core logic, and you get library reusability for free.

2. **[ASTGL CONTENT] Hybrid automation — auto-extract what you can:** When measuring both objective and subjective metrics, don't force everything into one approach. Auto-extract timestamps and file sets (objective), prompt for quality judgments (subjective). This pattern applies to any measurement system that mixes quantitative and qualitative data.

3. **[ASTGL CONTENT] JSON for small persistent data:** For datasets under ~100 records, JSON files are superior to databases: human-readable, zero dependencies, version-controllable, and easy to debug with `cat`. The inflection point where databases win is when you need queries, concurrent writes, or thousands of records.

---

## Open Questions / Next Steps

- [x] **Phase 3 automation scripts** — 4 new files (1,004 lines), committed and pushed
- [ ] **Run actual baseline sessions** — Need 5-10 real dev sessions with Cortex disabled, using `run_phase3 record` after each
- [ ] **Phase 4 automation** — A/B comparison scripts could reuse `TranscriptAnalyzer` for the Cortex-enabled sessions, adding briefing token count and event count metrics
- [ ] **Update previous session notes** — Mark Phase 3 automation as done in `SESSION-2026-02-05-phase2-test-automation.md`

---

*Session duration: ~45 minutes (including plan mode + implementation)*
*Files created: 4 (1,004 lines + .gitignore update)*
*Tests: 331/331 existing tests passing, 5/5 Phase 2 tests passing*
