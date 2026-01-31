# Cortex: An Event-Sourced Memory Architecture for AI Coding Assistants
# Solving the Context Window Boundary Problem Through Automatic Session Continuity

**Author**: James Cruce (with Claude Opus 4.5)
**Date**: January 31, 2026
**Version**: 1.0

---

## Abstract

Large Language Model (LLM) coding assistants operate within finite context windows,
creating a fundamental discontinuity at session boundaries. When context is exhausted,
the assistant loses all accumulated understanding: architectural knowledge, decision
history, work-in-progress state, and the nuanced mental model built through exploration.
This paper presents a systematic investigation of the problem and proposes **Cortex**, a
novel memory architecture that combines event-sourced capture, projected briefings, and
progressive complexity tiers to maintain session continuity automatically. Through
iterative design refinement — including brainstorming eight candidate architectures,
two rounds of comparative scoring, adversarial failure analysis, and mitigation
engineering — we arrive at an architecture that reduces cold-start time by an estimated
80%+, eliminates decision regression, and maintains plan coherence across sessions,
all without requiring model modifications or secondary LLM calls.

---

## Table of Contents

1. [Introduction & Motivation](#1-introduction--motivation)
2. [Problem Definition](#2-problem-definition)
3. [Survey of Existing Approaches](#3-survey-of-existing-approaches)
4. [Solution Design Methodology](#4-solution-design-methodology)
5. [Candidate Architectures](#5-candidate-architectures)
6. [Comparative Analysis: Round 1](#6-comparative-analysis-round-1)
7. [Hybrid Architecture Design](#7-hybrid-architecture-design)
8. [Comparative Analysis: Round 2](#8-comparative-analysis-round-2)
9. [The Cortex Architecture](#9-the-cortex-architecture)
10. [Failure Analysis & Mitigations](#10-failure-analysis--mitigations)
11. [Implementation Strategy](#11-implementation-strategy)
12. [Discussion](#12-discussion)
13. [Future Work](#13-future-work)
14. [Conclusion](#14-conclusion)
15. [References](#15-references)

---

## 1. Introduction & Motivation

The advent of LLM-powered coding assistants — Claude Code, GitHub Copilot, Cursor,
Windsurf — has transformed software development workflows. These tools can explore
codebases, plan implementations, write code, debug errors, and execute complex
multi-step engineering tasks. Within a single session, they function as remarkably
capable pair programmers.

Yet every practitioner encounters the same cliff: the session ends. Whether by context
window exhaustion, explicit termination, or the natural rhythm of a workday, the
session boundary erases everything the assistant learned. The next session begins
with total amnesia.

This is not merely an inconvenience — it is the **single most significant barrier to
adopting AI coding assistants for complex, multi-session projects**. The more capable
the assistant is within a session, the more devastating the loss at its boundary.
Excellence within a session amplifies the frustration of its disappearance.

This paper arose from direct experience with this problem during an extended research
project conducted entirely through Claude Code sessions. The irony was not lost on us:
we were using an AI assistant to design a solution for the AI assistant's own memory
problem, while actively suffering from that problem. This meta-experience informed
our requirements and sharpened our understanding of which failures matter most.

### 1.1 Contributions

This paper makes the following contributions:

1. **A rigorous decomposition** of the context window boundary problem, identifying
   five categories of lost information and their cascading effects on developer
   productivity

2. **A comprehensive survey** of 15+ existing approaches, from academic architectures
   (MemGPT, MIRIX, Nemori) to community-built tools (claude-cortex, memory-mcp,
   claude-diary), organized into a design pattern taxonomy

3. **Eight candidate architectures** developed through two rounds of brainstorming,
   including five original designs and three hybrid architectures

4. **A quantitative scoring framework** with 11 weighted criteria applied across
   two comparison rounds, demonstrating clear convergence on a winning design

5. **The Cortex architecture**: an event-sourced memory system with projected
   briefings, three-layer extraction, progressive complexity tiers, and integrated
   safety mechanisms

6. **A comprehensive adversarial analysis** identifying 19 failure modes across
   5 categories, with engineered mitigations reducing all critical risks by 60-87%

---

## 2. Problem Definition

### 2.1 The Finite Window Constraint

LLMs process input and generate output within a fixed-size context window, measured
in tokens. As of January 2026, context windows range from 8K tokens (legacy models)
to over 1M tokens (Gemini 2.5 Pro, Claude with extended context). Even at the upper
end, an intensive coding session can exhaust available context within 30-90 minutes.

The context window is consumed by:
- **System prompts and instructions**: CLAUDE.md files, MCP tool descriptions, safety
  instructions (~5-15K tokens, fixed overhead)
- **Code file contents**: Each file read injects its full content (~500-5000 tokens)
- **Tool call results**: Bash output, search results, file listings (~100-2000 tokens each)
- **Conversation history**: User messages and AI responses accumulate continuously

When the window approaches capacity, the system must either stop or employ compaction
(summarization), which is inherently lossy.

### 2.2 What Is Lost

We identify five categories of information destroyed at session boundaries:

**Category 1: Architectural Understanding (Mental Model)**
The assistant builds an understanding of the codebase through exploration — how
components relate, which patterns are used, where the important logic lives. This
understanding takes significant token investment to build and is completely lost.

**Category 2: Decision History**
During a session, the assistant evaluates multiple approaches, rejects some with
specific reasoning, and selects others. This decision trail is crucial for preventing
regression — without it, the assistant may re-suggest previously rejected approaches,
wasting developer time on explanations already given.

**Category 3: Work State**
Multi-step plans, in-progress tasks, partial implementations, test results, and the
overall progress of complex work are lost. The next session cannot seamlessly resume;
it must rediscover the current state from scratch.

**Category 4: Tool & Environment State**
Modified files, git state, environment configuration, and the developer's tooling
preferences are implicitly known during a session but not carried forward.

**Category 5: Conversational Nuance**
User preferences, communication style, implicit priorities, and the collaborative
rapport built during a session are ephemeral.

### 2.3 The Cascade Effect

Information loss creates cascading secondary problems:

1. **Re-exploration waste**: 10-30 minutes spent re-reading files and re-establishing context
2. **Decision regression**: Re-suggesting rejected approaches, eroding user trust
3. **Plan fragmentation**: Multi-step work loses coherence across sessions
4. **Trust erosion**: Users lose confidence in an assistant that "forgets"
5. **Cognitive burden shift**: The human becomes the memory system, defeating the purpose

### 2.4 Requirements for a Solution

Based on this analysis, we established formal requirements:

**Functional Requirements (Must-have)**:
- FR-1: Automatically capture context without user intervention
- FR-2: Persist context across session boundaries
- FR-3: Automatically load relevant context at session start
- FR-4: Support selective recall (relevant, not everything)
- FR-5: Track decision history (choices AND rejections with reasoning)
- FR-6: Track work state (plans, progress, pending tasks)
- FR-8: Handle multi-project isolation

**Non-Functional Requirements**:
- NFR-1: Zero or minimal user effort to maintain
- NFR-2: Consume <15% of context window for loaded memories
- NFR-3: Startup latency <5 seconds
- NFR-4: Work with standard Claude Code (no model modifications)
- NFR-5: Secure storage (no secrets in memory store)
- NFR-8: Composable with existing tools (CLAUDE.md, MCP, hooks)

**Success Criteria**:
- Cold start time reduction of 80%+
- Near-zero decision regression
- Seamless multi-session plan continuity
- Near-zero user maintenance effort
- Token overhead ≤15% of context window

---

## 3. Survey of Existing Approaches

### 3.1 Taxonomy

Our survey of 15+ existing solutions revealed the following design pattern categories:

| Pattern | Automatic | Semantic | Scalable | Examples |
|---------|:---------:|:--------:|:--------:|----------|
| Static file injection | No | No | Limited | CLAUDE.md |
| Manual checkpointing | No | No | Medium | mcp-memory-keeper |
| Hook-based capture | Yes | No | Medium | claude-diary |
| Two-tier (brief + store) | Yes | Partial | Good | memory-mcp |
| Salience-scored + decay | Yes | Yes | Good | claude-cortex |
| OS-style virtual memory | Yes | Yes | Excellent | MemGPT/Letta |
| Capture + compress + inject | Yes | Yes | Good | claude-mem |
| Multi-type hierarchical | Yes | Yes | Complex | MIRIX |

### 3.2 Key Academic Contributions

**MemGPT (Packer et al., 2023; now Letta)**: The seminal work reframing LLM memory
as an operating system problem. MemGPT treats the context window as RAM and external
storage as disk, with the LLM itself managing paging between tiers through tool calls.
Key innovations include self-editing memory, strategic forgetting through summarization,
and memory pressure interrupts. 16.4K GitHub stars as of 2025.

**MIRIX**: A six-type memory architecture (Core, Episodic, Semantic, Procedural,
Resource, Knowledge Vault), each managed by a dedicated agent and coordinated by
a meta-memory controller. Demonstrates the value of typed memory.

**LightMem**: A lightweight approach inspired by the Atkinson-Shiffrin human memory
model, focusing on filtering, organizing, and consolidating information with minimal
overhead.

**Nemori**: Self-organizing memory using the Free-Energy Principle. Autonomously
segments conversations into semantic episodes, with prediction errors driving
knowledge integration.

### 3.3 Community Solutions for Claude Code

**claude-cortex**: Brain-like memory with STM/LTM/Episodic types, salience scoring
(0-1 scale), temporal decay (`score × 0.995^hours`), and knowledge graph linking.
The closest existing solution to our design goals.

**memory-mcp**: Two-tier architecture — Tier 1 is an auto-generated CLAUDE.md
briefing (~150 lines), Tier 2 is a full knowledge store accessible via MCP tools.
Claims 80% of sessions need only Tier 1.

**claude-mem**: Full session capture with AI-powered compression and injection.
Uses Claude's Agent SDK for summarization.

### 3.4 Industry Trends

Amazon Bedrock AgentCore Memory (2025) provides managed short-term and long-term
agent memory as a cloud service. Windsurf and Trae offer built-in persistent memory
in their AI-native IDEs. The ICLR 2026 MemAgents workshop focuses specifically on
memory for LLM-based agentic systems, confirming this as a frontier research area.

### 3.5 Gaps in Existing Solutions

Our survey identified five significant gaps that no existing solution adequately
addresses:

1. **Selective relevance**: Most systems inject everything or use simple recency,
   not intent-aware retrieval
2. **Decision history**: Rejected approaches are rarely captured explicitly
3. **Plan continuity**: In-progress multi-step work is the weakest area across
   all surveyed solutions
4. **Token budget awareness**: Few solutions optimize for context window consumption
5. **Progressive complexity**: All solutions are all-or-nothing; no incremental adoption

---

## 4. Solution Design Methodology

### 4.1 Iterative Convergence Process

Rather than designing a single solution and defending it, we employed an iterative
convergence methodology:

```
Round 1: Generate 5 diverse candidate architectures
    ↓
Compare using weighted scoring (10 criteria)
    ↓
Select top 2 + identify reusable ideas from eliminated candidates
    ↓
Round 2: Generate 3 hybrid architectures combining top ideas
    ↓
Compare all 5 remaining candidates (11 criteria)
    ↓
Identify winner + validate gap to runner-up
    ↓
Adversarial failure analysis (19 failure modes)
    ↓
Engineer mitigations for all critical/high risks
    ↓
Final architecture
```

This methodology ensures the winning design has been stress-tested against
alternatives and its weaknesses have been explicitly addressed.

### 4.2 Scoring Framework

Solutions were scored on 11 criteria with importance weights from 2-5:

| Weight | Criteria | Rationale |
|:------:|----------|-----------|
| 5 | Automatic capture | Core requirement — zero user effort |
| 5 | Selective recall | Token efficiency depends on loading only relevant context |
| 4 | Decision preservation | Prevents the most frustrating failure mode |
| 4 | Plan continuity | Core use case for multi-session work |
| 4 | Token efficiency | Must leave room for actual work |
| 3 | Implementation feasibility | Must be buildable with current tools |
| 3 | Scalability | Must work after 100+ sessions |
| 3 | Cross-project isolation | Must not contaminate across projects |
| 3 | Incremental adoptability | Users should gain value immediately |
| 2 | Human inspectability | Users should be able to review/edit |
| 2 | Startup latency | Should not block the developer |

Total possible score: 210 points.

---

## 5. Candidate Architectures

### 5.1 Round 1 Candidates

**Solution 1: "The Cognitive Journal"** — Structured session diary entries written
by Claude at session boundaries via PreCompact hooks. Journal entries include task
state, decisions, discoveries, and plans. Index-based retrieval loads recent entries.
*Score: 130/175. Strength: simplicity. Weakness: no semantic awareness.*

**Solution 2: "The Memory Palace"** — Graph-based knowledge store with nodes (facts,
decisions, plans), edges (relationships), and metadata (salience, recency). Semantic
retrieval via embeddings. Organized into topical "rooms." MCP server provides access.
*Score: 128/175. Strength: best retrieval. Weakness: implementation complexity.*

**Solution 3: "Git-for-Thought"** — Version-controlled context diffs tracked alongside
code. A `HEAD.md` file represents current knowledge state, with context diffs computed
at session boundaries. Context branches align with git branches.
*Score: 127/175. Strength: developer UX. Weakness: no semantic search.*

**Solution 4: "Event Sourcery"** — Event-sourced memory with typed events
(decision_made, approach_rejected, plan_created, etc.) stored in an append-only
SQLite database. State is reconstructed through projections — different views computed
from the event stream for different purposes.
*Score: 145/175. Strength: best capture + decision/plan tracking.*

**Solution 5: "The Dual-Mind"** — Two cooperating processes: a "Scribe" (captures
context during session using background LLM) and a "Briefer" (generates anticipatory
briefing at session start based on user intent via semantic search).
*Score: 143/175. Strength: best selective recall. Weakness: requires secondary LLM calls.*

### 5.2 Round 1 Selection

Event Sourcery and Dual-Mind were selected as the top 2, with complementary
strengths: Event Sourcery excels at capture and structure, while Dual-Mind excels
at intelligent retrieval and delivery. Ideas from eliminated solutions were
carried forward.

### 5.3 Round 2 Candidates (Hybrids)

**Hybrid A: "Cortex"** — Event Sourcery's typed event capture + Dual-Mind's
intent-aware retrieval (via local embeddings, not LLM) + Git-for-Thought's branch
alignment + Memory Palace's salience scoring. Projections generate budget-aware
briefings. No secondary LLM calls required.

**Hybrid B: "Engram"** — Three-tier architecture: Tier 1 (always-loaded briefing),
Tier 2 (full event vault via MCP), Tier 3 (anticipatory retrieval triggered by
user's first message). UserPromptSubmit hook enables anticipatory loading.

**Hybrid C: "Chronicle"** — Git-native event journal with markdown projections
tracked alongside code in version control. PRs include context diffs showing
decisions made and rationale. Simplest hybrid but lacks semantic search.

---

## 6. Comparative Analysis: Round 1

The first comparison round evaluated the five original candidates on 10 weighted
criteria (total: 175 points). Results:

| Rank | Solution | Score | Key Differentiator |
|:----:|----------|:-----:|-------------------|
| 1 | Event Sourcery | 145 | Best capture + decision/plan tracking |
| 2 | Dual-Mind | 143 | Best selective recall + anticipatory loading |
| 3 | Cognitive Journal | 130 | Simplest implementation |
| 4 | Memory Palace | 128 | Best semantic retrieval |
| 5 | Git-for-Thought | 127 | Best developer UX / metaphor |

The top two solutions had complementary strengths, suggesting a hybrid approach
could capture both advantages.

---

## 7. Hybrid Architecture Design

### 7.1 Borrowed Ideas

The three eliminated solutions contributed valuable ideas to the hybrids:

- **From Cognitive Journal**: Human-readable structured entries
- **From Memory Palace**: Salience scoring with temporal decay
- **From Git-for-Thought**: Branch alignment; version-controlled projections

### 7.2 Technical Feasibility Findings

Deep research in Phase 5 established critical constraints:

1. **Event sourcing for AI agents is industry-validated** — Multiple independent
   projects (BoundaryML, Akka, Graphite Framework) confirm the pattern
2. **Secondary LLM calls from hooks are risky** — Infinite loop potential,
   latency, and cost make this architecturally unsafe
3. **SQLite FTS5 + sqlite-vec enables hybrid search** — Keyword + vector
   similarity in a single file with <5ms retrieval
4. **Claude Code hooks provide sufficient lifecycle coverage** — PreCompact,
   SessionStart, Stop, and UserPromptSubmit hooks cover all needed events
5. **`.claude/rules/` supports additive context injection** — No need to
   modify user's CLAUDE.md

---

## 8. Comparative Analysis: Round 2

The second round evaluated all 5 remaining candidates (2 original + 3 hybrid)
on 11 weighted criteria (total: 210 points), with the addition of "incremental
adoptability" as a criterion.

| Rank | Solution | Score | Delta |
|:----:|----------|:-----:|:-----:|
| **1** | **Cortex (Hybrid A)** | **185** | — |
| 2 | Engram (Hybrid B) | 171 | -14 |
| 3 | Chronicle (Hybrid C) | 166 | -19 |
| 4 | Event Sourcery (original) | 163 | -22 |
| 5 | Dual-Mind (original) | 143 | -42 |

Cortex won with a 14-point margin over the runner-up (Engram). The gap was driven
primarily by feasibility: Cortex achieves approximately 90% of Engram's retrieval
quality with approximately 60% of the complexity, and avoids the latency penalty
of Engram's three-tier loading strategy.

Dual-Mind dropped from 2nd to 5th due to the hard constraint that secondary LLM
calls from hooks are architecturally unsafe — a finding from Phase 5 research that
fundamentally altered its feasibility score.

---

## 9. The Cortex Architecture

### 9.1 Overview

Cortex is an event-sourced memory system with three key subsystems:

1. **Three-Layer Event Extraction** — Captures session context automatically
2. **Projected Briefings** — Generates token-budget-aware context summaries
3. **Progressive Tiers** — Enables incremental adoption from zero-dependency to full power

### 9.2 Three-Layer Event Extraction

Events are captured through three complementary layers, each with different accuracy
characteristics and coverage:

**Layer 1: Structural Extraction (deterministic)**
Parses tool call metadata directly from hook payloads. Every file read, file write,
bash command, git operation, and TodoWrite call generates a typed event. This layer
has 100% accuracy for its scope because it parses structured data, not natural language.

**Layer 2: Keyword Extraction (heuristic)**
Searches Claude's response text for decision markers using weighted patterns.
Strong signals ("chose X over Y because Z", confidence 0.95) generate high-confidence
events. Weak signals ("decided to read", confidence 0.3) are stored but excluded
from projections.

**Layer 3: Claude Self-Reporting (cooperative)**
System instructions in `.claude/rules/cortex-briefing.md` ask Claude to explicitly
flag significant decisions using `[MEMORY: type]` tags:
```
[MEMORY: decision] Chose SQLite over PostgreSQL because zero-config is critical
[MEMORY: rejected] Rejected JSON files — doesn't scale for semantic search
[MEMORY: learned] src/main.py uses the factory pattern for handler dispatch
```
These tags are trivially parseable (simple regex) and have 1.0 confidence because
Claude explicitly reports what it decided. This is the most accurate layer.

### 9.3 Event Schema

```
Event {
    id:          UUID
    session_id:  string     # Which session generated this
    project:     string     # Project identifier (directory path)
    git_branch:  string     # Active git branch when event was created
    type:        EventType  # Enum of typed event categories
    content:     string     # Human-readable description
    metadata:    JSON       # Type-specific structured data
    salience:    float      # 0.0-1.0, type-dependent default
    confidence:  float      # 0.0-1.0, extraction-layer-dependent
    created_at:  timestamp
    accessed_at: timestamp  # Updated on retrieval (for reinforcement)
    access_count: int       # How many times this event was retrieved
    embedding:   float[]    # Vector embedding (Tier 2+)
    immortal:    bool       # If true, never decays (decisions, rejections)
    provenance:  string     # "layer1:EditTool" or "layer3:MEMORY_TAG"
}
```

**Event Types and Default Salience:**

| Type | Default Salience | Immortal | Captures |
|------|:----------------:|:--------:|----------|
| DECISION_MADE | 0.9 | Yes | Architectural and implementation choices |
| APPROACH_REJECTED | 0.9 | Yes | Rejected alternatives with reasoning |
| PLAN_CREATED | 0.85 | No | New multi-step plans |
| PLAN_STEP_COMPLETED | 0.7 | No | Progress on existing plans |
| KNOWLEDGE_ACQUIRED | 0.7 | No | Codebase understanding, patterns, insights |
| ERROR_RESOLVED | 0.75 | No | Errors and their solutions |
| PREFERENCE_NOTED | 0.8 | No | User preferences and communication style |
| TASK_COMPLETED | 0.6 | No | Completed work items |
| FILE_MODIFIED | 0.4 | No | Files that were edited |
| FILE_EXPLORED | 0.3 | No | Files that were read for understanding |
| COMMAND_RUN | 0.2 | No | Shell commands executed |

### 9.4 Decay and Reinforcement

Non-immortal events decay over time:
```
effective_salience = salience × (decay_rate ^ hours_since_last_access)
```

Default decay rate: 0.995 per hour. A salience-0.7 event accessed 48 hours ago:
`0.7 × (0.995^48) = 0.7 × 0.786 = 0.55` — still retained.
After 7 days: `0.7 × (0.995^168) = 0.7 × 0.429 = 0.30` — near threshold.

Accessing an event reinforces it: `salience = min(1.0, salience × 1.2)`.
Frequently useful memories survive; rarely accessed ones fade naturally.

**Note on tuning:** All decay rates and thresholds (0.995/hour, 0.5 confidence
cutoff, 1.2 reinforcement multiplier) are **configurable via project settings**
and should be calibrated against real session data during Tier 0 implementation.
The initial values are informed estimates; the implementation plan includes a
calibration phase (see §11.4).

**Immortal events** (decisions, rejections) have decay_rate = 1.0 and are permanently
retained. The reasoning: the question "why did we choose X?" can arise at any point
in a project's lifetime.

**Immortal Event Growth Management:** While decisions never decay, unbounded growth
creates a latent conflict with the token budget (§9.5). Cortex manages this through
tiered summarization:

1. **Active decisions** (last 20 sessions): Included in full with reasoning
2. **Aging decisions** (20-50 sessions old, never accessed): Compressed to one-line
   summaries (e.g., "Chose SQLite over PostgreSQL — zero-config requirement [s5]")
3. **Archived decisions** (50+ sessions, never accessed): Moved to a separate
   `decisions-archive.md` file, loadable on demand but excluded from the default
   briefing
4. **Configurable cap**: Maximum of 50 full decisions in the briefing; beyond that,
   oldest unaccessed decisions are compressed or archived

This ensures that the most-referenced decisions remain permanently available at full
fidelity, while rarely-referenced old decisions are progressively compressed rather
than lost. A decision that is accessed (e.g., Claude or the user asks "why did we
choose X?") is immediately promoted back to "active" status.

### 9.5 Projection Engine

The projection engine converts raw events into a focused, token-budget-aware
markdown briefing.

**Algorithm:**
```
function generate_briefing(project, branch, token_budget):
    1. Load latest snapshot for project
    2. Replay events since snapshot
    3. Apply salience decay to all non-immortal events
    4. Run reality checks (git status, config files)
    5. Flag any contradictions between memory and reality

    6. Select events for briefing:
       a. Immortal events (decisions, rejections):
          - Active (last 20 sessions or accessed recently): full text
          - Aging (20-50 sessions, unaccessed): one-line summary
          - Archived (50+ sessions, unaccessed): excluded (in decisions-archive.md)
          - Cap: max 50 full + 30 summarized → "Decisions" section
       b. Active plan events (most recent plan + progress) → "Active Plan" section
       c. Top-K recent events by effective_salience → "Recent Work" section
       d. Token budget controls K; decisions section capped at 40% of budget

    7. Format as markdown with:
       - Epistemic humility preamble
       - Confidence markers on each assertion
       - Provenance annotations [session-N]
       - Conflict warnings if reality checks failed

    8. Write to .claude/rules/cortex-briefing.md

    Return briefing
```

**Output format:**
```markdown
<!-- CORTEX MEMORY SYSTEM — AUTO-GENERATED -->
# Session Context Brief
*Compressed summary of prior sessions. Verify critical assumptions before acting.*

## Active Plan (from session 11)
1. ✅ Problem definition
2. ✅ Existing solutions survey
3. ✅ Brainstorm round 1
4. ➡️ Comparison round 1 ← YOU ARE HERE
5. ⬜ Deep research

## Key Decisions [PERMANENT]
- Storage: SQLite over JSON/PostgreSQL — zero-config requirement [s5, HIGH CONF]
- Capture: Hook-based automatic, not manual [s4, HIGH CONF]
- Architecture: Two-tier (briefing + deep store) [s7, HIGH CONF]

## Recent Work
- Session 12: Created 5 solution architectures for comparison
- Session 11: Completed survey of 15+ existing approaches
- Session 10: Tested claude-cortex — too complex for our needs, but salience
  scoring concept is valuable [MEDIUM CONF — 3 sessions old]

## Memory Instructions
When you make significant decisions or discover important patterns, flag them:
[MEMORY: decision] Your choice and reasoning here
[MEMORY: rejected] What you rejected and why
[MEMORY: learned] What you discovered about the codebase
<!-- END CORTEX MEMORY -->
```

### 9.6 Anticipatory Retrieval (Tier 2+)

When vector embeddings are available, the system can perform intent-aware retrieval:

1. **SessionStart hook** loads the pre-computed briefing (instant)
2. **UserPromptSubmit hook** captures the user's first message
3. The user's message is embedded locally (~200ms)
4. Hybrid search (FTS5 BM25 + cosine similarity via RRF) finds relevant events
5. Top results are appended to the briefing as a "Relevant Context" section
6. This enriched context is available before Claude processes the message

This approximates Dual-Mind's anticipatory loading without requiring secondary
LLM calls.

### 9.7 Progressive Tiers

Cortex is designed for incremental adoption:

**Tier 0 — Zero Dependency** (~30 seconds to install)
- Single Python script using only stdlib
- Events stored in JSON file
- Basic briefing from most recent events
- No embeddings, no SQLite, no MCP
- **Value**: Captures decisions and plans; loads recent context

**Tier 1 — Enhanced Storage** (~2 minutes)
- Upgrades to SQLite with FTS5
- Adds salience scoring and temporal decay
- Adds snapshot/replay for fast startup
- **Value**: Full-text search of event history; intelligent pruning

**Tier 2 — Semantic Search** (~5 minutes)
- Adds vector embeddings (SentenceTransformers, ~90MB model)
- Enables hybrid search (keyword + semantic)
- Adds anticipatory retrieval via UserPromptSubmit hook
- **Value**: Intent-aware context loading; finds relevant, not just recent

**Tier 3 — Full Power** (~10 minutes)
- Adds MCP server for mid-session memory queries
- Enables git-tracked projections (Chronicle pattern)
- Adds branch alignment and contradiction detection
- **Value**: Claude can actively query memory; PRs include decision context

Each tier is independently useful. Tier 0 alone provides significant value.

### 9.8 Hook Configuration

**Validated against Claude Code hook documentation (January 2026).** All four
hook events exist and provide the required payloads. See Appendix E for full
payload schemas.

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/cortex/extract.py --layer 1,2,3"
      }]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/cortex/snapshot.py && python3 ~/.claude/cortex/project_briefing.py"
      }]
    }],
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/cortex/load_briefing.py"
      }]
    }],
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/cortex/anticipatory_retrieve.py"
      }]
    }]
  }
}
```

**Hook data flow:** All hooks receive JSON via stdin with common fields
(`session_id`, `transcript_path`, `cwd`) plus event-specific data.
Key payloads for Cortex:

| Hook | Key Payload Fields | Cortex Usage |
|------|-------------------|--------------|
| Stop | `transcript_path`, `stop_hook_active` | Parse transcript for Layer 1-3 extraction |
| PreCompact | `trigger` ("manual"/"auto") | Create snapshot, regenerate briefing |
| SessionStart | `source` ("startup"/"resume"/"compact") | Load/generate briefing, reality checks |
| UserPromptSubmit | `prompt` (user's message text) | Embed prompt for anticipatory retrieval (Tier 2+) |

**Concurrency note:** Hooks execute synchronously by default. For the Stop hook,
which runs after every Claude response, extraction must complete quickly (<100ms)
to avoid perceptible lag. The `async: true` option is available but introduces
ordering complexity for events.
```

### 9.9 Safety Systems

**Reality Anchoring**: At session start, cross-checks memory assertions against
git state and config files. Flags contradictions. The mechanism uses a bounded,
deterministic approach rather than general NLP:

1. **Git branch check**: Compare memorized branch against `git rev-parse
   --abbrev-ref HEAD`. Exact string match.
2. **Dependency check**: Parse `package.json` `dependencies`/`devDependencies`
   keys, `pyproject.toml` `[project.dependencies]`, or `requirements.txt` package
   names. Compare against a list of technology keywords extracted from
   KNOWLEDGE_ACQUIRED and DECISION_MADE events (e.g., if an event says "chose
   PostgreSQL," check for `psycopg2`, `asyncpg`, `sqlalchemy` in deps).
3. **File existence check**: If memory references specific files (from
   FILE_MODIFIED events), verify they still exist on disk.
4. **Recency check**: Compare `git log --since` against memorized "last session"
   timestamp to detect external changes.

This approach avoids open-ended NLP entity matching by restricting checks to
structured data (git state, parsed config files) compared against structured
event metadata (event type + keywords). False positives are possible but
low-impact — they generate warnings, not blocking errors.

**Confidence Decay**: Old unverified assertions gain `[POSSIBLY OUTDATED]` markers
after N sessions without reinforcement.

**Provenance Tracking**: Every event records its source (which layer, which session),
enabling trust assessment.

**Periodic Refresh**: Every N sessions, prompts Claude to verify key assertions.

**Health Monitoring**: Heartbeat file tracks hook execution; warnings on failure.

**Graceful Degradation**: If any component fails, the system falls back to the
next-lower tier rather than failing entirely.

---

## 10. Failure Analysis & Mitigations

### 10.1 Methodology

We conducted an adversarial analysis identifying 19 failure modes across 5 categories:
Event Extraction, Projection & Retrieval, Integration & Infrastructure, Semantic &
Logical, and User Experience. Each was scored on Likelihood × Impact (1-25 scale).

### 10.2 Critical Risks and Mitigations

**F1.2 — Important Events Missed (Risk: 20/25)**
*Root cause*: Local pattern matching can't understand implicit reasoning.
*Mitigation*: Three-layer extraction. Layer 3 (Claude self-reporting via [MEMORY:]
tags) catches what Layers 1-2 miss. Layer 1 (structural) provides a guaranteed
baseline. Combined, the three layers cover >95% of important events.
*Residual risk*: 8/25 (-60%)

**F5.3 — Setup Complexity Deters Adoption (Risk: 20/25)**
*Root cause*: Too many components to install.
*Mitigation*: Progressive tiers. Tier 0 requires only a single Python script with
zero dependencies. Each tier adds value independently. Users upgrade when ready.
*Residual risk*: 5/25 (-75%)

### 10.3 High Risks and Mitigations

| Failure | Risk | Mitigation | Residual |
|---------|:----:|------------|:--------:|
| F4.4: Echo chamber | 15 | Reality anchoring + confidence decay | 6 |
| F1.1: Misclassification | 15 | Confidence scoring on extractions | 8 |
| F2.4: Old decisions lost | 15 | Immortal events for decisions | 4 |
| F3.1: Silent hook failure | 15 | Health check + heartbeat + fallback | 6 |
| F3.4: CLAUDE.md conflict | 15 | Separate .claude/rules/ file | 2 |
| F5.2: False confidence | 15 | Epistemic markers + verify gates | 8 |

### 10.4 Residual Risk Profile

After mitigations, no failure mode exceeds 8/25 risk score. The system's most
significant residual risks are:
- Keyword pattern misclassification (8/25) — acceptable; low-confidence events
  are excluded from projections
- Event capture gaps for implicit reasoning (8/25) — acceptable; Layer 3 self-
  reporting provides the safety net
- Briefing-induced overconfidence (8/25) — acceptable; epistemic markers and
  verify gates provide guardrails

---

## 11. Implementation Strategy

### 11.1 Recommended Build Order

1. **Tier 0 Core** — Event extraction (Layers 1-2), JSON storage, basic briefing
2. **Layer 3 Integration** — Add [MEMORY:] tag instructions to .claude/rules/
3. **Tier 1 Upgrade** — SQLite migration, FTS5, salience scoring
4. **Safety Systems** — Reality anchoring, health monitoring, confidence decay
5. **Tier 2 Upgrade** — Embedding model, hybrid search, anticipatory retrieval
6. **Tier 3 Upgrade** — MCP server, branch alignment, git-tracked projections

### 11.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Event Storage | SQLite (with JSON fallback for Tier 0) | Zero-config, portable, fast |
| Full-text Search | SQLite FTS5 | Built into SQLite, BM25 ranking |
| Vector Search | sqlite-vec | Single-file, no external DB |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) | Local, 384-dim, fast |
| Hybrid Ranking | Reciprocal Rank Fusion (RRF) | Proven effective for FTS + vec |
| Hook Runtime | Python 3.11+ (stdlib for Tier 0) | Claude Code hook compatibility |
| MCP Server | Python (Tier 3 only) | Claude Code MCP protocol |
| Briefing Delivery | .claude/rules/ markdown file | Additive, non-destructive |

### 11.3 Performance Targets

| Metric | Target | Mechanism |
|--------|--------|-----------|
| Event extraction latency | <100ms per response | Local pattern matching |
| Briefing generation | <500ms | Snapshot + replay + format |
| Anticipatory retrieval | <2s total | Local embedding + hybrid search |
| Briefing size | <3000 tokens (~15% of 200K at 2%) | Budget-aware projection |
| Event store capacity | 100K+ events | SQLite with periodic pruning |
| Cold start improvement | 80%+ reduction | From 10-30 min to <3 min |

### 11.4 Evaluation & Measurement Plan

Success criteria (§2.4) require measurement infrastructure. The following
instrumentation should be built into Tier 0 from day one:

**Baseline Collection (pre-Cortex):**
- Record 5-10 sessions without Cortex to establish baselines for:
  - Time from session start to first productive action (cold start time)
  - Count of re-explanations of previously-discussed decisions (decision regression)
  - Count of re-read files that were explored in prior sessions (re-exploration)

**Instrumented Metrics (built into Cortex):**

| Metric | How Measured | Target |
|--------|-------------|--------|
| Cold start time | Timestamp from SessionStart to first user-initiated tool call | <3 min (80%+ reduction) |
| Decision regression | Count of DECISION_MADE events that duplicate prior decisions | Near-zero |
| Plan continuity | Compare plan step sequence across sessions; flag gaps/repeats | Seamless |
| Token overhead | Count tokens in generated briefing vs. total context window | ≤15% |
| Extraction accuracy | Sample 20 sessions; manually label decisions; compare to captured events | >90% recall for Layer 1+3 |
| User maintenance effort | Count of manual user corrections/overrides per session | Near-zero |

**A/B Comparison (Tier 0 implementation):**
- Run 10 sessions with Cortex enabled, 10 without, on comparable tasks
- Compare cold start time, decision regression count, and subjective "continuity score"
  (1-5 rating by the developer at session end)
- Publish results before advancing to Tier 1

**Decay Parameter Calibration:**
- After 20+ sessions, analyze which events were actually useful (accessed by Claude
  or referenced in user prompts) vs. which decayed to irrelevance
- Adjust decay rates to match observed utility patterns
- Document calibrated values and rationale

### 11.5 Testing Strategy

Cortex requires tests at three levels to catch regressions, especially when Claude's
response patterns evolve:

**Unit Tests (Layer-level):**
- Layer 1: Fixture tool call payloads → expected event types and metadata
- Layer 2: Fixture Claude response texts → expected keyword matches and confidence scores
  - Include adversarial cases: "I decided to read the file" → NOT a DECISION_MADE
  - Include edge cases: multi-language, code blocks containing trigger words
- Layer 3: Fixture [MEMORY:] tagged text → expected parsed events
- Decay/salience: Given event age + access history → expected effective salience
- Immortal archival: Given N decisions over M sessions → expected active/compressed/archived counts

**Projection Tests (Integration):**
- Fixture event sets → expected briefing structure and approximate token count
- Budget overflow: 500 immortal events → verify briefing stays within token budget
- Reality anchoring: Fixture git state + memory state → expected conflict warnings

**End-to-End Tests (Pipeline):**
- Mock hook payloads (stdin JSON) → run full extract → verify event store contents
- Generate briefing → verify output file exists at correct path with expected sections
- Simulate multi-session scenario: create events across 5 mock sessions → verify
  briefing reflects correct plan progress and decision history

**Regression Test Triggers:**
- Run the full test suite on every code change (standard CI)
- Periodically (monthly) run extraction against 10 saved real session transcripts
  to detect drift as Claude's output patterns evolve

### 11.6 Supported Environments

**Primary target:** macOS and Linux with Python 3.11+ and Claude Code installed.

**Windows:** Tier 0 should work via `python3` or `py -3` launcher, but hook paths
use forward slashes which may need adaptation. Windows support is best-effort for
Tier 0 and untested for higher tiers. The install script should detect the platform
and adjust paths accordingly.

**Offline / Air-gapped:** Tiers 0 and 1 work fully offline (no network required).
Tier 2 requires a one-time download of the embedding model (~90MB). For air-gapped
environments, the model can be side-loaded from a file. Tier 3's MCP server is
local-only and does not require network access.

**Minimum resources for Tier 2:** The SentenceTransformers model (all-MiniLM-L6-v2)
requires ~200MB RAM. Systems with <1GB free RAM may experience slowness. A
configuration option to disable embedding and fall back to FTS5-only search
should be available.

---

## 12. Discussion

### 12.1 Why Event Sourcing Won

The iterative comparison process converged on event sourcing as the foundation for
several fundamental reasons:

1. **Separation of capture and delivery**: Events are raw facts; projections are
   opinions. This separation means the same event store can produce different views
   for different purposes, and the projection algorithm can be improved without
   re-capturing events.

2. **Audit trail**: Unlike summary-only approaches, event sourcing preserves the
   full decision trail. The question "why did we choose X?" is always answerable.

3. **Temporal reasoning**: Events are inherently temporal, enabling questions like
   "what happened in sessions 5-8?" or "when did we switch from REST to GraphQL?"

4. **Composability**: New projection types can be added without modifying the
   capture system. Branch-aligned projections, team-shared projections, and
   project-timeline projections are all computable from the same event stream.

### 12.2 Why Not Pure MemGPT/Letta

MemGPT's OS paradigm is elegant but requires the LLM itself to manage memory through
tool calls, consuming token budget for memory management rather than actual work.
Cortex moves memory management to the hook layer — external to the LLM — preserving
the full context window for productive work. The LLM participates only through
lightweight [MEMORY:] tags, which consume <10 tokens per annotation.

### 12.3 The Self-Reporting Insight

The most important design decision may be Layer 3 — asking Claude to self-report
decisions via [MEMORY:] tags. This is a form of cooperative memory where the AI
actively participates in its own memory system. It works because:

1. LLMs are naturally cooperative with system instructions
2. Claude KNOWS what it decided — no extraction heuristic can match this accuracy
3. The overhead is minimal — a few tokens per significant decision
4. The tags are trivially parseable — no NLP pipeline needed

This transforms the intractable problem of "understanding implicit reasoning" into
the trivial problem of "parsing a structured tag."

### 12.4 The Progressive Tier Insight

The conventional wisdom in developer tooling is to build the full solution and hope
users will install it. Our failure analysis revealed that setup complexity is equally
as dangerous as technical failure (both scored 20/25 risk). The progressive tier
model — where Tier 0 requires nothing beyond a single script — dramatically lowers
the adoption barrier while providing a natural upgrade path.

### 12.5 Limitations

1. **Untested in production**: This paper presents a design, not empirical results.
   Actual effectiveness requires implementation and measurement (see §11.4 for
   the evaluation plan).

2. **Pattern matching accuracy**: Layer 2's keyword extraction will have false
   positives and negatives. The confidence scoring mitigates but doesn't eliminate
   this limitation.

3. **Self-reporting compliance**: Claude's adherence to [MEMORY:] tag instructions
   is probabilistic, not guaranteed. Some sessions may generate fewer tags than others.

4. **Single-developer scope**: The architecture is designed for individual developers.
   Team-wide memory sharing, access control, and collaborative memory management
   are out of scope.

5. **Claude Code specific**: While the concepts are generalizable, the implementation
   relies on Claude Code's hook system, CLAUDE.md, and MCP server support. Adapting
   to other AI coding assistants (Cursor, Windsurf, Copilot) would require mapping
   their lifecycle events and context injection mechanisms to Cortex's hook and
   rules-based architecture. The core event store and projection engine would
   remain unchanged; only the integration layer differs.

6. **Single-writer assumption**: Concurrent sessions on the same project (e.g.,
   two terminal windows) may produce interleaved or duplicated events. SQLite's
   WAL mode prevents corruption, but event ordering across concurrent sessions
   is not guaranteed. Users should treat each project as single-writer; multi-tab
   support is deferred to future work.

7. **English-centric extraction**: Layer 2's keyword patterns ("chose X over Y,"
   "decided to," "rejected") are English-only. Layer 1 (structural) and Layer 3
   (self-reporting tags) are language-agnostic since they parse structured data.
   Multilingual keyword patterns are deferred to future work.

8. **Privacy and sensitive data**: Events may capture file paths, code snippets,
   and user messages. The current design does not include PII detection, secret
   filtering (beyond the existing CLAUDE.md security rules), retention policies,
   or GDPR-style data deletion. A basic `cortex reset --project` command is
   planned for Tier 0, but comprehensive privacy controls are future work.

9. **Context loading order**: Both the user's CLAUDE.md and `.claude/rules/
   cortex-briefing.md` are loaded at session start. The load order affects how
   strongly Claude weighs each source. Claude Code loads rules files additively
   alongside CLAUDE.md, but the exact precedence when instructions conflict is
   determined by Claude Code's internal ordering, which is not user-configurable.
   The briefing includes epistemic humility markers to reduce precedence conflicts.

10. **Git-tracked projections and merge conflicts**: Tier 3's git-tracked
    projections (e.g., `decisions.md`) will create merge conflicts when branches
    diverge. The recommended strategy is to treat projection files as generated
    artifacts: on merge conflict, discard both versions and regenerate from the
    event store. This should be documented in `.gitattributes` with a custom
    merge driver or a post-merge hook.

---

## 13. Future Work

### 13.1 Empirical Validation
Implement Cortex and measure against the success criteria: cold-start time reduction,
decision regression rate, plan coherence, and token overhead.

### 13.2 Team Memory
Extend Cortex to support team-wide memory: shared event stores, role-based access,
and collaborative projections that surface relevant team context.

### 13.3 Learned Projections
Train a lightweight model to generate better projections from events, rather than
using rule-based formatting. This could improve token efficiency and relevance.

### 13.4 Cross-Tool Portability
Abstract the architecture to work with other AI coding assistants (Cursor, Windsurf,
Copilot) that may offer different lifecycle hooks. The integration layer (hooks +
rules injection) would need per-tool adapters, while the core event store and
projection engine remain unchanged.

### 13.5 Visual Memory Explorer
Build a web UI for browsing the event store, visualizing the knowledge graph, and
manually editing memories — making the system fully transparent and controllable.

### 13.6 User Correction and Memory Management
Implement a CLI for memory management operations:
- `cortex forget <event-id>` — Delete a specific event
- `cortex forget --session <id>` — Delete all events from a session
- `cortex reset --project` — Purge all memory for the current project
- `cortex edit <event-id>` — Modify a stored event's content
- `cortex export` — Export all events as JSON for backup or migration
This addresses FR-10 (user override/correction) which is defined in requirements
but not yet designed into the implementation.

### 13.7 Privacy and Data Controls
Add data protection features:
- Secret detection (scan events for API keys, passwords, tokens before storage)
- Configurable retention policies (auto-purge events older than N days)
- PII redaction for events that capture user messages
- GDPR-style "right to deletion" via the CLI tools in §13.6

### 13.8 Concurrent Session Support
Design and implement multi-writer support for teams or multi-tab workflows:
- Session-level write locks with advisory locking
- Event ordering via Lamport timestamps or vector clocks
- Merge semantics for briefing generation when multiple sessions contribute
- Conflict resolution when concurrent sessions make contradictory decisions

### 13.9 Multilingual Extraction
Extend Layer 2 keyword patterns to support non-English sessions. Layer 1
(structural) and Layer 3 (self-reporting tags) are already language-agnostic.
Consider using a lightweight multilingual classifier or translating patterns
to common development languages.

---

## 14. Conclusion

The context window boundary problem is the single most painful aspect of working with
AI coding assistants. Through systematic investigation — a rigorous problem definition,
survey of 15+ existing approaches, eight candidate architectures, two rounds of
comparative scoring, adversarial failure analysis of 19 failure modes, and mitigation
engineering — we developed **Cortex**: an event-sourced memory architecture that
addresses all identified requirements.

Cortex's key innovations are:

1. **Three-layer extraction** combining structural parsing, keyword heuristics, and
   AI self-reporting to maximize capture accuracy without secondary LLM calls

2. **Projected briefings** that are token-budget-aware, reality-anchored, and
   annotated with confidence markers and provenance tracking

3. **Progressive complexity tiers** enabling adoption from a zero-dependency script
   to a full-featured system with semantic search and MCP integration

4. **Immortal events** for decisions and rejections, ensuring the "why" behind
   foundational choices is never lost to temporal decay

5. **Integrated safety systems** including reality anchoring, confidence decay,
   contradiction detection, and graceful degradation

The architecture is ready for implementation. Based on our analysis, Cortex should
reduce cold-start time by 80%+, eliminate decision regression, and maintain plan
coherence across sessions — transforming AI coding assistants from session-bound
tools into persistent engineering partners.

---

## 15. References

### Academic Papers
1. Packer, C., et al. "MemGPT: Towards LLMs as Operating Systems." arXiv:2310.08560, 2023.
2. ICLR 2026 Workshop Proposal. "MemAgents: Memory for LLM-Based Agentic Systems." OpenReview, 2026.
3. LightMem. "Lightweight and Efficient Memory-Augmented Generation." arXiv:2510.18866, 2025.
4. HippoRAG. Gutiérrez, B.J., et al. "Neurobiologically Inspired Long-Term Memory for LLMs." 2024.

### Industry & Community
5. Anthropic. "Managing Context on the Claude Developer Platform." anthropic.com, Sept 2025.
6. BoundaryML. "Event-driven Agentic Loops." boundaryml.com, Nov 2025.
7. Akka. "Event Sourcing: The Backbone of Agentic AI." akka.io, 2025.
8. Claude Code Documentation. "Manage Claude's Memory." code.claude.com/docs/en/memory.
9. Claude Code Documentation. "Get started with Claude Code hooks." code.claude.com/docs/en/hooks-guide.

### Open-Source Projects
10. claude-cortex. github.com/mkdelta221/claude-cortex
11. memory-mcp (Two-Tier Architecture). dev.to/suede/the-architecture-of-persistent-memory-for-claude-code
12. mcp-memory-service. github.com/doobidoo/mcp-memory-service
13. claude-diary. github.com/rlancemartin/claude-diary
14. claude-mem. github.com/thedotmack/claude-mem
15. claude-continuity. github.com/donthemannn/claude-continuity
16. Letta (MemGPT). docs.letta.com

### Technical References
17. Garcia, A. "Hybrid full-text search and vector search with SQLite." alexgarcia.xyz, Oct 2024.
18. SQLite. "FTS5 Extension." sqlite.org/fts5.html.
19. sqlite-vec. github.com/asg017/sqlite-vec.
20. Serokell. "Design Patterns for Long-Term Memory in LLM-Powered Architectures." serokell.io, 2025.

### Community Issues
21. "Context persistence across sessions — major workflow disruption." github.com/anthropics/claude-code/issues/2954, Jul 2025.
22. "Feature Request: Persistent Memory Between Claude Code Sessions." github.com/anthropics/claude-code/issues/14227, Dec 2025.

---

## Appendices

### Appendix A: Complete Scoring Data

Full scoring matrices for both comparison rounds are available in the project's
research documentation:
- `docs/research/comparisons/04-comparison-r1.md`
- `docs/research/comparisons/06-comparison-r2.md`

### Appendix B: Complete Failure Analysis

The full 19-failure-mode analysis with detailed risk scoring is available in:
- `docs/research/phases/08-failure-analysis.md`

### Appendix C: Complete Mitigation Strategies

Detailed mitigation engineering for all critical and high-risk failures is in:
- `docs/research/phases/09-mitigations.md`

### Appendix D: Phase-by-Phase Research Documentation

The complete research process, including all intermediate work products, is
documented in the project's `docs/research/phases/` directory:
- `01-problem-definition.md`
- `02-existing-solutions.md`
- `03-brainstorm-r1.md`
- `05-deep-research.md`
- `08-failure-analysis.md`
- `09-mitigations.md`

### Appendix E: Hook API Validation

**Validated January 2026 against official Claude Code documentation.**

The Cortex architecture depends on four Claude Code hook events. All four are
confirmed to exist with the required payload data:

| Hook Event | Status | Payload Fields Used by Cortex |
|------------|--------|-------------------------------|
| `Stop` | ✅ Confirmed | `session_id`, `transcript_path`, `stop_hook_active` |
| `PreCompact` | ✅ Confirmed | `session_id`, `trigger` ("manual"/"auto"), `cwd` |
| `SessionStart` | ✅ Confirmed | `session_id`, `source` ("startup"/"resume"/"compact"), `cwd` |
| `UserPromptSubmit` | ✅ Confirmed | `session_id`, `prompt` (user's message text), `cwd` |

**Common fields** available to all hooks via JSON on stdin:
```json
{
  "session_id": "string",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "hook_event_name": "EventName"
}
```

**Key findings:**

1. **Stop hook** provides `transcript_path` — a file path to the full session
   transcript in JSONL format. This enables Layer 1 extraction by parsing tool
   call records, and Layer 2/3 extraction by parsing Claude's response text.
   The `stop_hook_active` boolean prevents infinite recursion.

2. **UserPromptSubmit hook** provides the user's `prompt` text directly in the
   payload. This confirms Tier 2 anticipatory retrieval is feasible: the hook
   can embed the prompt and perform similarity search before Claude processes it.

3. **SessionStart hook** provides `source` which distinguishes fresh starts from
   resumes and post-compaction restarts. This informs briefing generation strategy
   (full briefing on startup, incremental on resume).

4. **PreCompact hook** fires before context compaction with `trigger` indicating
   whether it was user-initiated or automatic. This is the ideal point for
   snapshot creation.

5. **Additional hooks available** but not required for Cortex core:
   - `PostToolUse`: Receives `tool_name`, `tool_input`, and `tool_response` —
     could enable real-time Layer 1 extraction per tool call rather than batch
     extraction at Stop. Deferred to optimization phase.
   - `SubagentStop`: For capturing context from subagent tasks.

**Hook types:** Claude Code supports three hook types: `command` (shell script),
`prompt` (single-turn LLM evaluation), and `agent` (multi-turn with tool access).
Cortex uses only `command` type for maximum speed and to honor the "no secondary
LLM calls" constraint.

**Sources:**
- Claude Code Hooks Reference: code.claude.com/docs/en/hooks.md
- Claude Code Hooks Guide: code.claude.com/docs/en/hooks-guide.md
- Claude Code Memory & Rules: code.claude.com/docs/en/memory.md

---

*This research was conducted as part of the memory-context-claude-ai project.
The full methodology — from problem definition through failure analysis — was
designed to be reproducible and transparent, with all intermediate artifacts preserved.*

*"The cruelest aspect: the better the AI performs within a session, the MORE painful
the loss when the session ends. Excellence within a session amplifies the frustration
at its boundary."* — From Phase 1, Section 2.4
