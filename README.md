# Cortex: An Event-Sourced Memory Architecture for AI Coding Assistants

> Solving the context window boundary problem through automatic session continuity.

LLM coding assistants (Claude Code, Copilot, Cursor) lose all accumulated understanding when a session ends. **Cortex** is a memory architecture that captures session context automatically and projects it into future sessions as a token-budget-aware briefing — no model modifications or secondary LLM calls required.

This repository contains the **complete research project** that designed the Cortex architecture through iterative convergence: problem definition, solution survey, architecture design, comparative scoring, adversarial failure analysis, and mitigation engineering.

## The Problem

When an AI coding session ends, the assistant loses:

| Category | What's Lost | Impact |
|----------|------------|--------|
| Mental Model | Codebase understanding built through exploration | 10-30 min re-exploration per session |
| Decision History | Choices made, alternatives rejected with reasoning | Re-suggests rejected approaches |
| Work State | Multi-step plans, progress, partial implementations | Plans fragment across sessions |
| Tool State | Modified files, git state, environment config | Must rediscover current state |
| Conversational Nuance | User preferences, communication style, priorities | Human becomes the memory system |

## The Solution: Cortex

Cortex is an **event-sourced memory system** with three key subsystems:

**Three-Layer Event Extraction** captures context automatically:
- **Layer 1 (Structural)**: Parses tool call metadata from hook payloads — 100% accuracy for its scope
- **Layer 2 (Keyword)**: Pattern-matches Claude's response text for decision markers — confidence-scored
- **Layer 3 (Self-Reporting)**: Claude flags decisions via `[MEMORY:]` tags — highest accuracy, trivially parseable

**Projected Briefings** generate token-budget-aware context summaries:
- Reality-anchored against git state and config files
- Annotated with confidence markers and provenance tracking
- Decisions are immortal (never lost to decay) with tiered representation

**Progressive Tiers** enable incremental adoption:

| Tier | Install Time | What You Get |
|------|-------------|-------------|
| **Tier 0** | 30 seconds | Single Python script, stdlib only, JSON storage, basic briefing |
| **Tier 1** | 2 minutes | SQLite + FTS5, salience scoring, temporal decay |
| **Tier 2** | 5 minutes | Vector embeddings, hybrid search, anticipatory retrieval |
| **Tier 3** | 10 minutes | MCP server, branch alignment, git-tracked projections |

## Research Methodology

The architecture was selected through **iterative convergence**, not designed in isolation:

```
Define problem rigorously (5 categories, 10 FRs, 8 NFRs)
    |
Survey 15+ existing solutions (9 design patterns identified)
    |
Brainstorm 5 candidate architectures
    |
Compare and rank (weighted scoring, 10 criteria) --> Select top 2
    |
Generate 3 hybrid architectures from best ideas
    |
Compare all 5 remaining (11 criteria, 210 points) --> Winner: Cortex (185/210)
    |
Adversarial failure analysis (19 failure modes identified)
    |
Engineer mitigations (all risks reduced to <= 8/25)
    |
External evaluation + response (all P0/P1 gaps addressed)
```

## Research Artifacts

All intermediate work products are preserved for transparency:

| Document | Description |
|----------|-------------|
| [Research Paper](docs/research/paper/cortex-research-paper.md) | Full paper with 15 sections + appendices |
| [Master Plan](docs/research/MASTER-PLAN.md) | Progress tracker and decision log |
| [Problem Definition](docs/research/phases/01-problem-definition.md) | 5 categories of lost context, formal requirements |
| [Existing Solutions Survey](docs/research/phases/02-existing-solutions.md) | 15+ solutions, 9 design patterns |
| [Brainstorm Round 1](docs/research/phases/03-brainstorm-r1.md) | 5 architectures: Journal, Palace, Git, Event Sourcery, Dual-Mind |
| [Comparison Round 1](docs/research/comparisons/04-comparison-r1.md) | Top 2: Event Sourcery + Dual-Mind |
| [Deep Research + Hybrids](docs/research/phases/05-deep-research.md) | 3 hybrids: Cortex, Engram, Chronicle |
| [Comparison Round 2](docs/research/comparisons/06-comparison-r2.md) | Winner: Cortex (185/210, 14-point margin) |
| [Failure Analysis](docs/research/phases/08-failure-analysis.md) | 19 failure modes, 2 critical, 6 high-risk |
| [Mitigations](docs/research/phases/09-mitigations.md) | All risks reduced to max 8/25 |
| [External Evaluation](docs/research/evaluation/external-evaluation.md) | Independent stress-test of the plan |
| [Evaluation Response](docs/research/evaluation/evaluation-response.md) | Point-by-point response to all gaps |

## Key Design Decisions

1. **Event sourcing as foundation** — Separates capture from delivery; audit trail is permanent
2. **No secondary LLM calls** — All extraction is local pattern matching; avoids infinite loops and latency
3. **Three-layer extraction** — Structural + keyword + self-reporting covers >95% of important events
4. **Progressive tiers** — Tier 0 alone provides significant value; users upgrade when ready
5. **Immortal events for decisions** — The "why" behind choices is never lost to temporal decay
6. **`.claude/rules/` for injection** — Additive briefing delivery; never modifies user's CLAUDE.md
7. **SQLite + FTS5 + sqlite-vec** — Single-file hybrid search, zero external dependencies

## Project Status

**Research: COMPLETE** | **Implementation: NOT YET STARTED**

Next step: Implement Tier 0 prototype, starting with baseline data collection (see [evaluation plan](docs/research/paper/cortex-research-paper.md#114-evaluation--measurement-plan)).

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install ruff pytest pre-commit
pre-commit install
```

```bash
ruff check .          # Lint
ruff format .         # Format
pytest tests/         # Test
pre-commit run --all-files  # All hooks
```

## Development Workflow (Ironclad)

This project uses a 4-phase workflow: **PLAN → EXECUTE → VERIFY → SHIP** with human checkpoints.

- **PLAN:** Create `.workflow/sessions/SESSION-YYYY-MM-DD-[slug]/plan.md` from `.workflow/templates/plan-template.md`; get approval before coding.
- **EXECUTE:** Implement tasks; update session docs; run `npm run lint` / `ruff check .` as you go.
- **VERIFY:** Run `npm run workflow:verify` (runs pytest, ruff, pip-audit, and optional Gemini AI review). Complete `.workflow/checklists/verify-checklist.md`; get human approval.
- **SHIP:** Run `npm run workflow:ship` to validate file integrity; then `npm run workflow:ship:pr` to create a PR (optional).

**Commands:**

| Command | Description |
|---------|-------------|
| `npm run workflow:verify` | Full verification (tests, lint, pip-audit, AI review) |
| `npm run workflow:verify:no-ai` | Verification without AI review |
| `npm run workflow:ai-review` | Standalone AI code review (Gemini) |
| `npm run workflow:ship` | Validate integrity vs verify-state.json |
| `npm run workflow:ship:pr` | Validate and create GitHub PR |

**AI review:** Set `GEMINI_API_KEY` for Gemini-powered security and quality review. Results go to `.workflow/state/ai-review.json`.

## About

This research was conducted as part of the [As The Geek Learns](https://astgl.com) project, documenting the journey of building AI-powered developer tools. The entire research process — from problem definition through failure analysis — was conducted using Claude Code, creating a meta-experience: using an AI assistant with the context window problem to design a solution for the context window problem.

> *"The cruelest aspect: the better the AI performs within a session, the MORE painful the loss when the session ends. Excellence within a session amplifies the frustration at its boundary."*

## License

This project is licensed under the [MIT License](LICENSE).
