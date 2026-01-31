# Session Notes: Tier 0 Implementation — Phase 6 (Hook Handlers)

**Date:** 2026-01-31
**Project Phase:** Implementation — Tier 0, Phase 6 of 8

---

## What Was Accomplished

Implemented the three Claude Code hook handlers (Stop, PreCompact, SessionStart) that drive event capture and briefing injection. Handlers read JSON payloads from stdin, perform incremental transcript extraction and briefing generation using the existing store, extractors, and briefing modules, and expose a single CLI entry point (`cortex stop`, `cortex precompact`, `cortex session-start`). All handlers are defensive: they never raise, log errors to stderr, and return 0 so Claude Code never blocks on hook failure. All 314 tests pass (13 new in `test_hooks.py`).

### Files Created (3 files)

| File | Lines | Purpose |
|------|-------|---------|
| `src/memory_context_claude_ai/hooks.py` | 196 | read_payload, handle_stop, handle_precompact, handle_session_start |
| `src/memory_context_claude_ai/__main__.py` | 48 | CLI: parse hook name from argv, read JSON from stdin, dispatch, exit with code |
| `tests/test_hooks.py` | 175 | 13 tests for read_payload and all three handlers |

### Files Modified (3 files)

| File | What Changed |
|------|-------------|
| `src/memory_context_claude_ai/__init__.py` | Exported handle_stop, handle_precompact, handle_session_start, read_payload; import order for Ruff |
| `README.md` | Added "Hook setup (Claude Code)" section: command table, payload schema note, link to paper and Claude Code hooks docs |
| `tests/test_config.py` | Ruff import fix (pre-existing, fixed during hook work) |

---

## Key Components Built

### read_payload()

Reads JSON from stdin. On empty or invalid input returns `{}` and does not raise. Single point of payload ingestion for all hooks.

### handle_stop(payload)

- If `stop_hook_active` is true, returns 0 immediately (avoids recursion).
- Resolves project from `payload["cwd"]` via `identify_project()`; gets `project_hash`, `git_branch`, `session_id`, `transcript_path`.
- Loads HookState for `project_hash`; uses `last_transcript_position` and `last_transcript_path`. If transcript path changed, resets position to 0.
- Opens transcript with TranscriptReader, calls `read_new(from_offset=position)`.
- Runs `extract_events(entries, session_id, project, git_branch)`; appends results with `EventStore.append_many()` (dedup built-in).
- Updates HookState: `last_transcript_position`, `last_transcript_path`, `last_session_id`, `session_count`, `last_extraction_time`.
- On exception: log to stderr, return 0.

### handle_precompact(payload)

- PreCompact does not provide `transcript_path`; discovers transcript via `find_transcript_path(cwd)` and `find_latest_transcript(dir)`.
- If transcript found: same incremental extraction as Stop (HookState, read_new, extract_events, append_many, state update).
- Writes briefing to `{cwd}/.claude/rules/cortex-briefing.md` via `write_briefing_to_file(..., project_path=cwd, branch=git_branch)`.
- On exception: log to stderr, return 0.

### handle_session_start(payload)

- Resolves project from `cwd`; writes briefing to `{cwd}/.claude/rules/cortex-briefing.md` so the new session gets current context.
- On exception: log to stderr, return 0.

### CLI (__main__.py)

- Parses first argv as hook name: `stop`, `precompact`, `session-start` (or `sessionstart`).
- Reads JSON from stdin via `read_payload()`; dispatches to the appropriate handler; `sys.exit(return_code)`.
- Usage: `cortex stop`, `cortex precompact`, `cortex session-start` (or `python -m memory_context_claude_ai stop` etc.) with JSON on stdin.

---

## Key Decisions Made

### Handlers always return 0 on failure

**Chosen:** On exception, handlers log to stderr and return 0.
**Why:** Hooks must not block Claude Code session start or response. Returning 0 keeps the IDE responsive; the user can still work even if Cortex fails.
**Tradeoff:** Failures are silent from Claude Code’s perspective; operators must rely on stderr or future heartbeat/health checks.

### PreCompact discovers transcript via cwd

**Chosen:** PreCompact does not receive `transcript_path` in the payload; we use `find_transcript_path(cwd)` and `find_latest_transcript()`.
**Why:** Aligns with research paper: PreCompact payload has `session_id`, `trigger`, `cwd` but not transcript path. Same incremental extraction logic as Stop when a transcript is found.
**Tradeoff:** If Claude Code’s transcript dir layout differs from `~/.claude/projects/<encoded-path>/`, PreCompact extraction may not find a file; briefing still writes from existing store.

### No heartbeat in Tier 0

**Chosen:** Heartbeat file (e.g. `.claude/cortex-heartbeat`) and SessionStart warning when last Stop is stale are out of scope for this phase.
**Why:** Plan marked heartbeat as optional for Tier 0; keeps Phase 6 focused on the core flow.
**Tradeoff:** No built-in signal that Stop failed in the previous session; can be added in a follow-up.

---

## Test Summary

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestReadPayload | 3 | Empty stdin, invalid JSON, valid JSON |
| TestHandleStop | 4 | stop_hook_active skip; full extraction + state update; missing cwd; missing transcript_path |
| TestHandlePrecompact | 3 | Writes briefing with events (tmp_git_repo for branch match); missing cwd; creates briefing dir |
| TestHandleSessionStart | 3 | Writes briefing with events; missing cwd; creates file when no events |

PreCompact and SessionStart “with events” tests use `tmp_git_repo` so `get_git_branch(cwd)` matches the branch on `sample_events` (`main`); otherwise `load_for_briefing(branch="unknown")` would filter out all events and the briefing would be empty.

---

## Phase Tracker

| Phase | Status |
|-------|--------|
| Phase 1: Models | Done |
| Phase 2: Storage (store, hook state) | Done |
| Phase 3: Transcript parser | Done |
| Phase 4: Three-layer extraction | Done |
| Phase 5: Briefing generation | Done |
| **Phase 6: Hook handlers** | **Done** |
| Phase 7: (TBD) | Pending |
| Phase 8: (TBD) | Pending |

---

## Next Steps

- Configure Claude Code to invoke `cortex stop`, `cortex precompact`, and `cortex session-start` with JSON on stdin (see README Hook setup).
- Optional follow-up: heartbeat file and SessionStart warning when last Stop is stale.
- Optional: UserPromptSubmit handler (Tier 2 anticipatory retrieval).
