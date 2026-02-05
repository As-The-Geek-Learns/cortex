# Cortex Project — Notion Import

**Purpose:** Import this content into Notion on the ASTGL domain to create the Cortex Project with Tier 0 Real-World Testing tasks.

**How to import:** Create a new page in Notion under your ASTGL workspace, title it "Cortex Project", then copy each section below. Use Notion's `/todo` blocks for checkboxes.

---

## Cortex Project

> An event-sourced memory architecture for AI coding assistants. Solving the context window boundary problem through automatic session continuity.

**Repository:** [cortex](https://github.com/As-The-Geek-Learns/cortex)

**Status:** Tier 0 Implementation COMPLETE | Real-World Testing IN PROGRESS

---

## Tier 0 Real-World Testing Tasks

### Phase 1: Setup & Verification — COMPLETE

- [x] Install Cortex (`pip install -e .`)
- [x] Verify `cortex --help` shows all commands
- [x] Generate hook configuration (`cortex init`)
- [x] Copy memory instructions to `.claude/rules/`
- [x] Verify `cortex status` and `cortex reset`
- [x] Create test project at `~/cortex-test-project`

---

### Phase 2: Manual Testing Scenarios — 30–60 minutes

**2.1 Configure Claude Code Hooks**

- [ ] Add hook JSON from `docs/testing/SETUP-VERIFICATION-CHECKLIST.md` to `~/.claude/settings.json`
- [ ] Copy memory instructions to test project: `cp templates/cortex-memory-instructions.md ~/cortex-test-project/.claude/rules/`
- [ ] Verify `cortex status` shows 0 events in test project before testing

**2.2 Single Session Flow**

- [ ] Start Claude Code session in `~/cortex-test-project`
- [ ] Prompt: "Create a Python script that prints 'Hello, Cortex!'"
- [ ] Prompt: "Decision: Use Python 3.11+ for this project. [MEMORY: Use Python 3.11+ for compatibility with modern type hints.]"
- [ ] Prompt: "Add a test file for the script"
- [ ] Prompt: "Run the test"
- [ ] End session (Stop hook runs)
- [ ] Run `cortex status` — verify event count > 0
- [ ] Run `cat .claude/rules/cortex-briefing.md` — verify briefing exists with sections
- [ ] Verify events extracted: FILE_MODIFIED, COMMAND_RUN, DECISION_MADE

**2.3 Multi-Session Continuity**

- [ ] Start new Claude Code session in `~/cortex-test-project`
- [ ] Prompt: "What decisions have we made so far?" — verify Claude references Python 3.11+ decision
- [ ] Prompt: "Let's add logging to the script. Create a plan with these steps: 1) Add logging import, 2) Add log statements, 3) Test logging output."
- [ ] Prompt: "Implement step 1: add logging import"
- [ ] End session
- [ ] Start third session
- [ ] Prompt: "What's the current plan?" — verify briefing shows plan from session 2
- [ ] Prompt: "Continue with the plan" — verify Claude picks up from step 2

**2.4 Edge Cases**

- [ ] Empty session: Start and immediately end session — verify no crash
- [ ] Large briefing: Create 100+ events — verify briefing stays under token budget (~3000 tokens)
- [ ] Reset command: Run `cortex reset` — verify event count returns to 0

**Phase 2 Deliverable**

- [ ] Document results in `docs/sessions/SESSION-YYYY-MM-DD-tier0-manual-testing.md` using `docs/testing/MANUAL-TESTING-TEMPLATE.md`

---

### Phase 3: Baseline Data Collection — 5–10 sessions (~2–5 hours)

**3.1 Prepare for Baseline**

- [ ] Disable Cortex hooks in Claude Code settings (remove or comment out)
- [ ] Open `docs/testing/BASELINE-DATA-TEMPLATE.md`

**3.2 Record Baseline Sessions**

For each of 5–10 sessions (without Cortex), record:

- [ ] Session 1: Task, cold start time (min), decision regression count, re-exploration count, continuity score (1–5)
- [ ] Session 2: Task, cold start time (min), decision regression count, re-exploration count, continuity score (1–5)
- [ ] Session 3: Task, cold start time (min), decision regression count, re-exploration count, continuity score (1–5)
- [ ] Session 4: Task, cold start time (min), decision regression count, re-exploration count, continuity score (1–5)
- [ ] Session 5: Task, cold start time (min), decision regression count, re-exploration count, continuity score (1–5)
- [ ] Session 6 (optional): Same metrics
- [ ] Session 7 (optional): Same metrics
- [ ] Session 8 (optional): Same metrics
- [ ] Session 9 (optional): Same metrics
- [ ] Session 10 (optional): Same metrics

**3.3 Calculate Summary Statistics**

- [ ] Average cold start time
- [ ] Average decision regression count
- [ ] Average re-exploration count
- [ ] Average continuity score

**Phase 3 Deliverable**

- [ ] Complete baseline data in `docs/testing/BASELINE-DATA-TEMPLATE.md` or CSV

---

### Phase 4: A/B Comparison — 10 sessions (~5–10 hours)

**4.1 Prepare for A/B Testing**

- [ ] Re-enable Cortex hooks in Claude Code settings (use JSON from `cortex init`)
- [ ] Open `docs/testing/AB-COMPARISON-TEMPLATE.md`
- [ ] Use same project and comparable tasks as baseline

**4.2 Record Cortex-Enabled Sessions**

For each of 10 sessions (with Cortex), record:

- [ ] Session 1: Task, cold start time, decision regression, re-exploration, continuity score, briefing token count, event count
- [ ] Session 2: Same metrics
- [ ] Session 3: Same metrics
- [ ] Session 4: Same metrics
- [ ] Session 5: Same metrics
- [ ] Session 6: Same metrics
- [ ] Session 7: Same metrics
- [ ] Session 8: Same metrics
- [ ] Session 9: Same metrics
- [ ] Session 10: Same metrics

**4.3 A/B Comparison Analysis**

- [ ] Compare cold start time: Baseline avg vs Cortex avg — target 80%+ reduction
- [ ] Compare decision regression: Target near-zero with Cortex
- [ ] Compare re-exploration count: Target significant reduction
- [ ] Compare continuity score: Target improvement
- [ ] Check token overhead: Briefing length vs context window — target ≤15%

**4.4 Success Criteria Evaluation**

- [ ] Cold start time reduction: 80%+ — Pass / Fail
- [ ] Decision regression: Near-zero — Pass / Fail
- [ ] Plan continuity: Seamless — Pass / Fail
- [ ] Token overhead: ≤15% — Pass / Fail
- [ ] Extraction accuracy: >90% recall — Pass / Fail
- [ ] User maintenance effort: Near-zero — Pass / Fail

**Phase 4 Deliverable**

- [ ] Document results in `docs/sessions/SESSION-YYYY-MM-DD-tier0-ab-comparison.md` using `docs/testing/AB-COMPARISON-TEMPLATE.md`

---

### Phase 5: Decay Parameter Calibration — After 20+ sessions

**5.1 Event Utility Analysis**

- [ ] Export all events from EventStore (add `cortex export` CLI if needed)
- [ ] Classify events: High utility (referenced by Claude) / Medium / Low utility (decayed, irrelevant)
- [ ] Document patterns in event utility

**5.2 Decay Rate Adjustment**

- [ ] Review current parameters: `DECISION_ACTIVE_SESSIONS=20`, `DECISION_AGING_SESSIONS=50`
- [ ] If high-utility events decay too fast → increase `DECISION_ACTIVE_SESSIONS` or adjust decay formula
- [ ] If low-utility events persist too long → decrease thresholds or increase decay rate
- [ ] Update `src/cortex/models.py` with calibrated values

**Phase 5 Deliverable**

- [ ] Document calibrated values in `docs/sessions/SESSION-YYYY-MM-DD-tier0-calibration.md`

---

## Success Criteria (Research Paper §11.4)

| Criterion | Target | Status |
|-----------|--------|--------|
| Cold start time reduction | 80%+ | Pending |
| Decision regression | Near-zero | Pending |
| Plan continuity | Seamless | Pending |
| Token overhead | ≤15% | Pending |
| Extraction accuracy | >90% recall | Pending |
| User maintenance effort | Near-zero | Pending |

---

## Key Files & References

- **Testing docs:** `docs/testing/README.md`
- **Setup checklist:** `docs/testing/SETUP-VERIFICATION-CHECKLIST.md`
- **Manual testing template:** `docs/testing/MANUAL-TESTING-TEMPLATE.md`
- **Baseline template:** `docs/testing/BASELINE-DATA-TEMPLATE.md`
- **A/B comparison template:** `docs/testing/AB-COMPARISON-TEMPLATE.md`
- **Research paper:** `docs/research/paper/cortex-research-paper.md` (§11.4)
- **Test project:** `~/cortex-test-project`

---

## CLI Commands

```bash
cortex status      # Project hash, event count, last extraction
cortex reset       # Clear all events for current project
cortex init        # Print hook configuration JSON
```
