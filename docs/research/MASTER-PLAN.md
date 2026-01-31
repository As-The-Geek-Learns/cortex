# Research Project: Solving the AI Context Window Problem
# Master Plan & Progress Tracker
# Created: 2026-01-31

## Project Goal

Design an automatic system that preserves session context (tools, commands, decisions, plans)
across AI coding assistant sessions, enabling seamless workflow continuity despite context
window limitations. Produce a research paper documenting the full design process.

## Research Methodology

Iterative convergence:
1. Define the problem rigorously
2. Survey existing approaches
3. Brainstorm 5+ solutions
4. Compare, rank, select top 2
5. Deep-research top 2, generate new ideas
6. Compare again — repeat until one solution is clearly superior
7. Failure analysis on the winner
8. Mitigate weaknesses
9. Write research paper

## Phase Tracker

| Phase | Status | Output File | Summary |
|-------|--------|-------------|---------|
| 1. Problem Definition | ✅ COMPLETE | `phases/01-problem-definition.md` | 5 categories of lost info; 10 FRs, 8 NFRs; formal success criteria |
| 2. Existing Solutions Survey | ✅ COMPLETE | `phases/02-existing-solutions.md` | 15+ solutions surveyed; 9 design patterns; 5 gaps identified |
| 3. Brainstorm Round 1 | ✅ COMPLETE | `phases/03-brainstorm-r1.md` | 5 architectures: Journal, Palace, Git, Event Sourcery, Dual-Mind |
| 4. Comparison Round 1 | ✅ COMPLETE | `comparisons/04-comparison-r1.md` | Top 2: Event Sourcery (145/175) + Dual-Mind (143/175) |
| 5. Deep Research + New Ideas | ✅ COMPLETE | `phases/05-deep-research.md` | 3 hybrids: Cortex, Engram, Chronicle |
| 6. Comparison Round 2 | ✅ COMPLETE | `comparisons/06-comparison-r2.md` | Winner: Cortex (185/210), 14-pt margin over runner-up |
| 7. (Not needed) | SKIPPED | — | Cortex was clearly superior after Round 2 |
| 8. Failure Analysis | ✅ COMPLETE | `phases/08-failure-analysis.md` | 19 failure modes; 2 critical, 6 high-risk |
| 9. Weakness Mitigations | ✅ COMPLETE | `phases/09-mitigations.md` | All risks reduced to ≤8/25; max reduction 87% |
| 10. Paper Writing | ✅ COMPLETE | `paper/cortex-research-paper.md` | Full research paper with 15 sections + appendices |
| 11. External Evaluation | ✅ COMPLETE | `evaluation/external-evaluation.md` | Independent stress-test: 8 holes, 10 missing items, priority-ranked |
| 12. Evaluation Response | ✅ COMPLETE | `evaluation/evaluation-response.md` | All P0/P1 items addressed; P2 items documented as limitations/future work |

## Key Decisions Log

1. **Event sourcing as foundation** — Validated by industry consensus (BoundaryML, Akka, Graphite)
2. **No secondary LLM calls** — Hard constraint from Phase 5 feasibility research
3. **Three-layer extraction** — Structural + keyword + self-reporting covers >95% of events
4. **Progressive tiers** — Critical mitigation for adoption risk (reduced 20/25 → 5/25)
5. **Immortal events for decisions** — Decisions and rejections never decay
6. **.claude/rules/ for injection** — Additive, never modifies user's CLAUDE.md
7. **SQLite + FTS5 + sqlite-vec** — Single-file hybrid search, zero external dependencies
8. **[MEMORY:] tags for self-reporting** — Most accurate extraction layer, trivially parseable
9. **Hook API validated** — All 4 hooks (Stop, PreCompact, SessionStart, UserPromptSubmit) confirmed against official Claude Code docs with required payloads (Phase 12)
10. **Immortal events with growth management** — Tiered briefing inclusion (active/aging/archived) resolves unbounded growth conflict (Phase 12)
11. **Bounded reality anchoring** — Deterministic checks against structured data (git, config files, filesystem), not open-ended NLP matching (Phase 12)
12. **Evaluation-first implementation** — Baseline collection before Cortex, instrumented metrics, A/B comparison after Tier 0 (Phase 12)
13. **Decay parameters are tunable** — All thresholds configurable and calibrated from real sessions, not hardcoded magic numbers (Phase 12)

## Cross-Session Context Index

### Last Updated: 2026-01-31
### Current Phase: RESEARCH COMPLETE — READY FOR IMPLEMENTATION
### Key Artifacts Created:
- 6 phase documents in `phases/`
- 2 comparison documents in `comparisons/`
- 1 comprehensive research paper in `paper/` (updated with evaluation response)
- 1 external evaluation in `evaluation/`
- 1 evaluation response in `evaluation/`
### Critical Decisions Made: See Key Decisions Log above (13 decisions total)
### Winner: Cortex — Event-Sourced Memory with Projected Briefings
### Next Action: Implementation of Tier 0 prototype (start with baseline collection per §11.4)
