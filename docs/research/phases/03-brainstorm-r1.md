# Phase 3: Brainstorming Round 1
# Five Novel Solution Architectures
# Date: 2026-01-31

## Design Principles (from Phase 1 & 2 synthesis)

Before brainstorming, these principles should guide all solutions:

1. **Automatic capture** — Zero user effort to maintain
2. **Selective recall** — Load only what's relevant, not everything
3. **Decision preservation** — Rejected approaches must be remembered
4. **Plan continuity** — Multi-step work must survive session boundaries
5. **Token efficiency** — Memory loading must consume <15% of context window
6. **Works within Claude Code** — Hooks, MCP, CLAUDE.md, standard tooling only

---

## Solution 1: "The Cognitive Journal" (Structured Session Diary)

### Metaphor
Like a surgeon's operating log — brief, structured, capturing decisions and state.

### Architecture

```
Hooks:
  PreCompact → Trigger Claude to write structured journal entry
  SessionStart → Load most recent journal + relevant past entries

Storage:
  ~/.claude/journal/
  ├── sessions/
  │   ├── 2026-01-31_proj-name_001.md    (structured session log)
  │   ├── 2026-01-31_proj-name_002.md
  │   └── ...
  ├── index.json                          (session metadata index)
  └── decisions/
      └── proj-name.json                  (decision registry)
```

### How It Works

**During Session (PreCompact hook):**
Claude is instructed (via system prompt injection) to write a structured journal entry:
```markdown
## Session Journal Entry
### Task: [what was being worked on]
### Completed: [what got done]
### In-Progress: [current state of unfinished work]
### Decisions Made:
  - Chose X over Y because Z
  - Rejected approach A because B
### Key Discoveries:
  - File X does Y (learned through exploration)
  - Pattern P is used for Q
### Plan (Next Steps):
  1. [step 1]
  2. [step 2]
### Files Modified: [list]
### Open Questions: [unresolved items]
```

**At Session Start (SessionStart hook):**
1. Read `index.json` to find sessions for current project
2. Load the MOST RECENT session journal (full)
3. Load a compressed summary of the last 3-5 sessions
4. Inject into system prompt via CLAUDE.md append

**Decision Registry:**
A separate `decisions.json` accumulates ALL decisions across sessions:
```json
{
  "project": "memory-context-claude-ai",
  "decisions": [
    {
      "date": "2026-01-31",
      "topic": "storage-format",
      "chosen": "SQLite",
      "rejected": ["JSON files", "PostgreSQL"],
      "reasoning": "SQLite is zero-config, portable, sufficient for single-user"
    }
  ]
}
```

### Strengths
- Simple to implement (hooks + file writes)
- Human-readable (can inspect/edit journal entries)
- Decision history is first-class
- Git-trackable

### Weaknesses
- No semantic search — relies on recency, not relevance
- Journal quality depends on Claude's summarization ability
- No proactive loading — loads recent, not relevant
- Could become noisy over many sessions

---

## Solution 2: "The Memory Palace" (Graph-Based Knowledge Store + RAG)

### Metaphor
Like the ancient memory palace technique — information organized spatially (by topic)
with associative links, recalled by walking through relevant rooms.

### Architecture

```
MCP Server: memory-palace-mcp
  ├── Knowledge Graph (SQLite + FTS5)
  │   ├── Nodes: facts, decisions, plans, file knowledge
  │   ├── Edges: relationships (related-to, depends-on, replaces)
  │   └── Metadata: salience, recency, access count, project
  ├── Embedding Index (sqlite-vss or local model)
  │   └── Semantic vectors for all knowledge nodes
  └── Session State Store
      └── Current task, plan state, in-progress work

Hooks:
  PreCompact → Extract knowledge nodes from conversation
  PostCompact → Verify critical knowledge survived compaction
  SessionStart → Query graph for relevant context based on
                 project + recent activity + user's first message
  Stop → Incremental knowledge extraction after each response
```

### How It Works

**Continuous Extraction (Stop hook, every response):**
After each Claude response, a lightweight extractor identifies:
- New facts learned (file X does Y, API Z works like W)
- Decisions made or rejected
- Plan steps completed/added
- Errors encountered and resolutions

These are added as nodes to the knowledge graph with:
- Salience score (architecture decisions = high, temp debug info = low)
- Topic tags (auto-extracted)
- Project scope (from working directory)
- Temporal metadata

**At Session Start (SessionStart hook):**
1. Determine project from working directory
2. Load "core context" — highest-salience nodes for this project
3. Wait for user's first message, then...
4. **Semantic search** the graph using the user's message as query
5. Inject top-K relevant nodes as context

**The "Rooms" of the Palace:**
Knowledge is organized into topical "rooms":
- Architecture Room: system design, component relationships
- Decision Room: all choices made and rejected
- Task Room: plans, progress, open work
- Discovery Room: things learned about the codebase
- Error Room: problems encountered and solutions

### Strengths
- Semantic retrieval — finds relevant context, not just recent
- Graph structure captures relationships between concepts
- Salience scoring prevents noise
- Proactive loading based on user's query

### Weaknesses
- Complex to implement (MCP server, embeddings, graph DB)
- Embedding quality affects retrieval quality
- Extraction accuracy is critical — garbage in, garbage out
- Heavier runtime overhead than simpler solutions

---

## Solution 3: "The Git-for-Thought" (Version-Controlled Context Diffs)

### Metaphor
Like git tracks code changes, track CONTEXT changes — diffs of what the AI knows.

### Architecture

```
Storage: .claude-context/ (git-tracked alongside code)
  ├── HEAD.md              (current context state — the "working tree")
  ├── history/
  │   ├── ctx-001.diff     (context diff: what changed in session 1)
  │   ├── ctx-002.diff     (context diff: what changed in session 2)
  │   └── ...
  ├── branches/
  │   └── feature-auth.md  (context state for specific work branches)
  └── .context-config      (rules for what to track)

Hooks:
  SessionStart → Load HEAD.md (always) + relevant branch context
  PreCompact → Compute context diff, append to history, update HEAD.md
  PostToolUse[git_checkout] → Switch context branch
```

### How It Works

**HEAD.md — The Current State of Knowledge:**
A single markdown file that represents EVERYTHING the AI currently "knows" about
the project, maintained automatically:
```markdown
# Project Context: memory-context-claude-ai
## Architecture
- Python 3.11+, Ruff, pytest
- src/memory_context_claude_ai/ is the main package
## Current Work
- Phase: Research and design
- Active branch: main
- In-progress: Writing brainstorm document
## Key Decisions
- Using SQLite for storage (over JSON, PostgreSQL)
- Hook-based capture (automatic, not manual)
## Known Issues
- (none currently)
## Recent Changes
- Created research directory structure
- Wrote problem definition and existing solutions survey
```

**Context Diffs:**
When a session ends (PreCompact), the system computes what CHANGED:
```diff
## Current Work
- In-progress: Writing brainstorm document
+ In-progress: Comparing solution architectures
+ Completed: Brainstorm round 1 (5 solutions)

## Key Decisions
+ - Two-tier memory (briefing + deep store) is baseline
+ - Hooks are primary integration mechanism

## Recent Changes
+ - Created 5 solution architectures
+ - Completed comparison matrix
```

**Branch Alignment:**
Context branches follow git branches. When you `git checkout feature-auth`,
the system loads `branches/feature-auth.md` — context specific to that feature.

### Strengths
- Familiar mental model (developers know git)
- Context is version-controlled alongside code
- Branch alignment is genuinely novel
- Diffs are compact — only what changed
- HEAD.md is always human-readable and editable

### Weaknesses
- No semantic search — just loads HEAD.md
- Context branches could diverge/conflict
- HEAD.md could grow unbounded without pruning
- Requires discipline in diff computation

---

## Solution 4: "The Event Sourcery" (Event-Sourced Memory with Projection)

### Metaphor
Like event sourcing in distributed systems — store raw events, project current state
from the event stream on demand.

### Architecture

```
MCP Server: context-events-mcp
  ├── Event Store (append-only SQLite)
  │   └── Events: tool_used, decision_made, file_explored,
  │              error_encountered, plan_created, task_completed,
  │              knowledge_acquired, approach_rejected
  ├── Projections (computed views)
  │   ├── current-state.md    (projected from all events)
  │   ├── active-plan.md      (projected from plan events)
  │   └── decision-log.md     (projected from decision events)
  └── Snapshots (periodic full-state captures)
      └── snapshot-{timestamp}.json

Hooks:
  Stop → Classify and store events from the latest exchange
  PreCompact → Create snapshot + project current state
  SessionStart → Load latest snapshot + project state for this project
```

### How It Works

**Event Capture (Stop hook, after every response):**
Each AI response is analyzed for discrete events:
```json
{"type": "decision_made", "topic": "storage", "choice": "SQLite",
 "rejected": ["JSON"], "reason": "zero-config", "confidence": 0.9}
{"type": "file_explored", "path": "src/main.py", "summary": "Entry point,
 uses argparse for CLI", "key_functions": ["main", "parse_args"]}
{"type": "task_completed", "task": "Write problem definition",
 "plan_id": "research-project", "step": 1}
{"type": "approach_rejected", "approach": "fine-tuning per user",
 "reason": "violates requirement NFR-4"}
```

**State Projection (SessionStart):**
At session start, replay events to build current state:
1. Start from most recent snapshot
2. Replay events since snapshot
3. Project into `current-state.md` (compact, <2000 tokens)
4. Load into session via CLAUDE.md injection

**The Projections Are the Magic:**
Different projections answer different questions:
- "What am I working on?" → `active-plan.md`
- "What have I decided?" → `decision-log.md`
- "What do I know about this file?" → query events for that file
- "What went wrong last time?" → filter for error events

**Event types with semantic importance:**
| Event Type | Retention | Importance |
|------------|-----------|------------|
| decision_made | Permanent | Critical |
| approach_rejected | Permanent | Critical |
| plan_created/updated | Until complete | High |
| task_completed | 30 days | Medium |
| file_explored | 7 days | Low |
| error_encountered | Until resolved | High |
| knowledge_acquired | Permanent | Medium |
| tool_used | 1 day | Low |

### Strengths
- Complete audit trail — nothing truly lost
- Projections are focused and compact
- Event-typed retention prevents unbounded growth
- Replay enables any view of history
- Natural fit for "what happened and why" queries

### Weaknesses
- Event classification accuracy is critical
- Projections add computational overhead
- Event volume could be high (every response)
- Requires careful schema design
- Snapshot + replay complexity

---

## Solution 5: "The Dual-Mind" (AI Self-Summarization + Anticipatory Loading)

### Metaphor
Like a human assistant who takes notes during meetings AND prepares briefing
documents before the next meeting based on what they think you'll need.

### Architecture

```
Two processes, one MCP server:

Process 1: "The Scribe" (runs during session)
  - Observes all tool calls and responses
  - Maintains running summary in background
  - Writes structured session notes to disk
  - Captures decisions, plans, discoveries in real-time

Process 2: "The Briefer" (runs at session start)
  - Reads user's initial message
  - Reads project state (git status, recent files, TODOs)
  - Queries past session notes using semantic similarity
  - Constructs a focused briefing document
  - Injects briefing as system context

Storage:
  .claude-memory/
  ├── sessions/
  │   └── {session-id}.json        (structured session notes)
  ├── project-state.json            (accumulated project knowledge)
  ├── briefings/
  │   └── {session-id}-brief.md    (generated briefing docs)
  └── embeddings.db                 (vector store for semantic search)

Hooks:
  SessionStart → Run "The Briefer" process
  Stop → Run "The Scribe" incrementally
  PreCompact → Run "The Scribe" final summary
```

### How It Works

**The Scribe (During Session):**
Uses Claude's own summarization capability (via Agent SDK or a secondary
API call) to process each exchange and extract:
- What was asked
- What was done
- What was decided (and alternatives considered)
- What was learned
- Current plan state

This runs as a BACKGROUND process — the user's session is not interrupted.
The scribe writes to session notes files incrementally.

**The Briefer (At Session Start):**
1. Read git status → understand current code state
2. Read latest session notes → understand where we left off
3. Read user's first message → understand what they want NOW
4. Semantic search past sessions → find relevant historical context
5. **Generate a briefing document** using a secondary LLM call:

```markdown
# Session Briefing — 2026-01-31 14:30

## Where We Left Off
You were working on Phase 3 of the research project. 5 solutions
were brainstormed. The comparison matrix is next.

## Relevant History
- In Session #12, you decided on SQLite for storage (rejected JSON, Postgres)
- In Session #8, you explored the hooks system and found PreCompact ideal
- In Session #10, you tested claude-cortex but found it too complex

## Active Plan
1. ✅ Problem definition
2. ✅ Existing solutions survey
3. ✅ Brainstorm round 1
4. ➡️ Comparison round 1 (CURRENT)
5. ⬜ Deep research on top 2

## Key Files
- docs/research/phases/03-brainstorm-r1.md (just created)
- docs/research/MASTER-PLAN.md (project tracker)

## Decisions in Effect
- Two-tier memory architecture (briefing + deep store)
- Hook-based automatic capture
- Token budget: <15% of context window
```

**The "Anticipatory" Part:**
The Briefer doesn't just load recent context — it PREDICTS what's needed:
- If user says "let's continue" → load most recent session fully
- If user says "fix the auth bug" → search for auth-related sessions
- If user says "review PR #42" → load PR context, not session history
- If no user message yet → load a safe default (recent + high-salience)

### Strengths
- True proactive loading — anticipates needs
- Background processing doesn't interrupt session
- Uses AI to summarize AI (best possible compression)
- Briefing documents are focused and token-efficient
- Most human-like approach (mimics a real assistant)

### Weaknesses
- Requires secondary API calls (cost)
- Background process adds system complexity
- Briefer quality depends on embedding quality + prompt engineering
- Race condition: user's first message triggers briefer, but briefing
  must be ready before the AI starts responding
- Two LLM invocations at startup adds latency

---

## Comparison Preview (Detailed in Phase 4)

| Criterion | Cognitive Journal | Memory Palace | Git-for-Thought | Event Sourcery | Dual-Mind |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Automatic capture | ✅ | ✅ | ✅ | ✅ | ✅ |
| Selective recall | ❌ | ✅ | ❌ | ✅ | ✅ |
| Decision preservation | ✅ | ✅ | ✅ | ✅✅ | ✅ |
| Plan continuity | ✅ | ⚠️ | ✅ | ✅✅ | ✅✅ |
| Token efficiency | ✅ | ⚠️ | ✅ | ✅ | ✅✅ |
| Implementation complexity | Low | High | Medium | Medium-High | High |
| Semantic awareness | ❌ | ✅✅ | ❌ | ⚠️ | ✅✅ |

---

## Phase 3 Status: COMPLETE
## Solutions Generated: 5
## Next: Phase 4 — Detailed comparison, scoring, and selection of top 2
