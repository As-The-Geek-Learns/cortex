# Session Notes: Evaluation Response & Plan Hardening

**Date:** 2026-01-31
**Duration:** ~45 minutes
**Model:** Claude Opus 4.5
**Project Phase:** Post-research, pre-implementation

---

## What Was Accomplished

Received an independent external evaluation of the Cortex research plan and systematically responded to every critique. The evaluation identified 8 holes/gotchas and 10 missing design elements across P0/P1/P2 priorities. All P0 and P1 items were addressed with concrete design changes; P2 items were documented as acknowledged limitations or future work.

### Documents Modified

| Document | What Changed |
|----------|-------------|
| `paper/cortex-research-paper.md` | 6 sections updated, 4 new sections added, 1 new appendix |
| `phases/09-mitigations.md` | 3 mitigations refined (M3, M4, M5) |
| `MASTER-PLAN.md` | 2 new phases added, 5 new decisions (#9-13) |

### Documents Created

| Document | Purpose |
|----------|---------|
| `evaluation/evaluation-response.md` | Point-by-point response to all evaluation items |
| `docs/sessions/SESSION-2026-01-31-evaluation-response.md` | This file |

---

## Key Decisions Made

### Decision #9: Hook API Validated
Researched the Claude Code hook API against official documentation. All 4 hooks (`Stop`, `PreCompact`, `SessionStart`, `UserPromptSubmit`) are confirmed to exist with the payloads the plan assumes. The evaluation was right that this wasn't documented — but the plan's assumptions were correct. Added Appendix E to the paper with full validation evidence.

### Decision #10: Immortal Events with Growth Management
The evaluation correctly identified a latent conflict: "immortal" events (decisions that never decay) vs. token-budget-aware briefings. If you accumulate 500 decisions over a long project, they can't all fit in the briefing. Solution: tiered briefing inclusion — active decisions get full text, aging decisions get one-line summaries, archived decisions move to a separate file. Decisions are never deleted from the event store, only compressed in their briefing representation. Cap: 50 full + 30 summarized, 40% of token budget.

### Decision #11: Bounded Reality Anchoring
The original plan said "compare config files against memorized tech stack" — but that's an NLP entity-matching problem if done in general. Replaced with 4 deterministic, structured-data checks: git branch match, dependency keyword lookup against config files, file existence verification, and recency detection. Deliberately avoids open-ended NLP.

### Decision #12: Evaluation-First Implementation
Added a full evaluation and measurement plan (paper section 11.4). Before building Cortex, collect baseline data from 5-10 sessions without it. After Tier 0, run A/B comparison (10 with, 10 without). Calibrate decay parameters after 20+ real sessions. This was a genuine gap — success criteria existed but no way to measure them.

### Decision #13: Tunable Decay Parameters
All confidence thresholds and decay rates (0.995/hour, 0.5 cutoff, etc.) are explicitly marked as configurable estimates requiring calibration from real session data, not hardcoded constants.

---

## Process & Methodology Notes

### How the Evaluation Response Was Structured

1. **Read everything first** — evaluation, master plan, research paper, mitigations, failure analysis, deep research phase
2. **Independently validated the most critical claim** — researched the Claude Code hook API using official documentation to confirm/deny the P0 concern
3. **Triaged by severity** — P0 items got design changes, P1 items got refinements, P2 items got documentation
4. **Changed the plan in-place** — rather than creating a "v2" document, updated the existing paper/mitigations/master-plan to reflect the improved design
5. **Created a response document** — systematic point-by-point accounting of what was changed and why

This mirrors how you'd handle a code review: address the critical issues, refine the medium ones, acknowledge the nice-to-haves, and document your reasoning.

---

## New Concepts / Patterns Learned

### Tiered Representation vs. Tiered Retention
"Immortal" doesn't have to mean "always fully present." You can retain data permanently in the store while progressively compressing its representation in the output. This is a general pattern: retention policy and presentation policy are independent axes.

### Bounded Mechanism Design
When a plan says "compare X against Y" and X is free text while Y is structured data, that's a hidden NLP problem. Better to constrain both sides to structured data and accept lower recall for much higher reliability. This is a recurring trap in system design.

### Evaluation Plans Are Not Optional
Defining success criteria without measurement infrastructure is like writing unit test assertions without running them. The criteria become decoration rather than engineering. The measurement plan should be designed alongside the success criteria.

---

## ASTGL Content Moments

1. **[ASTGL CONTENT] Independent evaluation before implementation** — Getting a different AI perspective to stress-test your plan catches blind spots you can't see from inside the design. The evaluation caught a genuinely missing measurement strategy and forced vague aspirations into concrete mechanisms. 30 minutes of critique response will save hours of implementation confusion.

2. **[ASTGL CONTENT] The "immortal vs. bounded" design tension** — When two design principles conflict (never lose data vs. respect token budgets), the resolution is often to separate retention from representation. Keep everything in the store; compress what you show. This applies beyond AI memory systems.

3. **[ASTGL CONTENT] Structured data > NLP for reliability** — When you can choose between "understand natural language" and "compare structured fields," always choose structured fields. The reality anchoring redesign (from vague NLP matching to deterministic config parsing) is a great example of constraining the problem to make it solvable.

4. **[ASTGL CONTENT] The meta-irony continues** — We're using an AI assistant with session boundary amnesia to evaluate and refine a plan for solving AI assistant session boundary amnesia. And the evaluation itself was done by an AI that will forget it did the evaluation. The session notes you're reading right now exist precisely because of the problem we're trying to solve.

---

## Open Questions / Next Steps

1. **Implementation starts with baseline collection** — Per the new §11.4, the first implementation step is recording 5-10 sessions without Cortex to establish measurement baselines
2. **Tier 0 prototype** — Single Python script, stdlib only, JSON storage, Layer 1+2 extraction, basic briefing
3. **Should Layer 3 instructions go in `.claude/rules/` or CLAUDE.md?** — The plan says `.claude/rules/cortex-briefing.md` but the [MEMORY:] tag instructions need to be present even when the briefing file doesn't exist yet (cold start). May need a separate static rules file for the instructions vs. the dynamic briefing.
4. **PostToolUse vs Stop for extraction** — The hook research revealed `PostToolUse` fires per-tool-call with full `tool_input` and `tool_response`. This could enable real-time Layer 1 extraction instead of batch extraction at Stop. Worth evaluating for latency vs. accuracy tradeoffs during Tier 0.
5. **How to handle the transcript_path format** — The Stop hook provides `transcript_path` as a `.jsonl` file. Need to understand the exact schema of transcript entries for Layer 2/3 extraction parsing.

---

*Session conducted as part of the memory-context-claude-ai research project.*
*Research phase is complete. Implementation phase begins next.*
