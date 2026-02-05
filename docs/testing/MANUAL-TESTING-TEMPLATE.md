# Tier 0 Manual Testing Results

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Test Project:** `~/cortex-test-project`

---

## Phase 2.1: Single Session Flow

**Goal:** Verify extraction and briefing generation after a single Claude Code session.

### Setup

- [ ] Cortex hooks configured in Claude Code settings (see SETUP-VERIFICATION-CHECKLIST.md)
- [ ] Memory instructions copied to test project `.claude/rules/`
- [ ] `cortex status` shows 0 events before testing

### Test Steps

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Start Claude Code session in `~/cortex-test-project` | Session starts | | |
| 2 | Prompt: "Create a Python script that prints 'Hello, Cortex!'" | File created (e.g., `hello.py`) | | |
| 3 | Prompt: "Decision: Use Python 3.11+ for this project. [MEMORY: Use Python 3.11+ for compatibility with modern type hints.]" | Claude acknowledges decision | | |
| 4 | Prompt: "Add a test file for the script" | Test file created | | |
| 5 | Prompt: "Run the test" | Test executed via Bash/shell | | |
| 6 | End session (close Claude Code or wait for stop) | Stop hook runs | | |
| 7 | Run `cortex status` | Event count > 0 | | |
| 8 | Run `cat .claude/rules/cortex-briefing.md` | Briefing file exists with sections | | |

### Results

**Event count after session:** ____

**Briefing content (paste relevant sections):**

```markdown
[Paste briefing content here]
```

**Events extracted (expected):**

| Event Type | Content (summary) | Found? |
|------------|-------------------|--------|
| FILE_MODIFIED | hello.py created | |
| FILE_MODIFIED | test file created | |
| COMMAND_RUN | pytest/python command | |
| DECISION_MADE | Use Python 3.11+ (from [MEMORY:] tag) | |

### Notes

[Any observations about hook execution, timing, errors, etc.]

---

## Phase 2.2: Multi-Session Continuity

**Goal:** Verify briefing is loaded and context persists across sessions.

### Session 2 (continuation)

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Start new Claude Code session in `~/cortex-test-project` | Session starts with briefing loaded | | |
| 2 | Prompt: "What decisions have we made so far?" | Claude references Python 3.11+ decision | | |
| 3 | Prompt: "Let's add logging to the script. Create a plan with these steps: 1) Add logging import, 2) Add log statements, 3) Test logging output." | Plan created | | |
| 4 | Prompt: "Implement step 1: add logging import" | Step 1 completed | | |
| 5 | End session | Stop hook runs | | |
| 6 | Run `cortex status` | Event count increased | | |

### Session 3 (plan continuation)

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Start new Claude Code session in `~/cortex-test-project` | Session starts | | |
| 2 | Check briefing: "What's the current plan?" | Briefing shows plan from session 2 | | |
| 3 | Prompt: "Continue with the plan" | Claude picks up from step 2 | | |
| 4 | End session | | | |

### Results

**Did Claude reference prior decisions?** [ ] Yes [ ] No

**Did Claude continue the plan correctly?** [ ] Yes [ ] No

**Continuity score (1-5):** ____

### Notes

[Observations about context preservation, briefing quality, etc.]

---

## Phase 2.3: Edge Cases

### Test Case 1: Empty Session

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Start Claude Code session | Session starts | | |
| 2 | Immediately end session (no prompts) | Stop hook runs | | |
| 3 | Run `cortex status` | No crash, event count unchanged or minimal | | |

**Result:** [ ] Pass [ ] Fail

### Test Case 2: Large Briefing (Budget Overflow)

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Create 100+ events via repeated sessions or script | Events stored | | |
| 2 | Generate briefing | Briefing stays under token budget (~3000 tokens) | | |
| 3 | Check briefing length | `wc -c .claude/rules/cortex-briefing.md` < 12000 chars | | |

**Result:** [ ] Pass [ ] Fail

### Test Case 3: Reset Command

| Step | Action | Expected | Actual | Pass? |
|------|--------|----------|--------|-------|
| 1 | Run `cortex status` before reset | Shows event count | | |
| 2 | Run `cortex reset` | Confirmation message | | |
| 3 | Run `cortex status` after reset | Event count = 0 | | |

**Result:** [ ] Pass [ ] Fail

---

## Summary

| Test | Status |
|------|--------|
| 2.1 Single Session Flow | [ ] Pass [ ] Fail |
| 2.2 Multi-Session Continuity | [ ] Pass [ ] Fail |
| 2.3.1 Empty Session | [ ] Pass [ ] Fail |
| 2.3.2 Large Briefing | [ ] Pass [ ] Fail [ ] Skipped |
| 2.3.3 Reset Command | [ ] Pass [ ] Fail |

**Overall Phase 2 Result:** [ ] Pass [ ] Fail

**Next Steps:**
- [ ] Proceed to Phase 3 (Baseline Data Collection) if all critical tests pass
- [ ] Fix issues and re-test if failures occurred
