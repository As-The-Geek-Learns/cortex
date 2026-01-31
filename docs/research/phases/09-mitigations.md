# Phase 8: Mitigation Strategies
# Addressing All Critical and High-Risk Failure Modes
# Date: 2026-01-31

## Critical Risk Mitigations

### M1: F1.2 — Important Events Missed (Risk: 20/25)

**Root cause**: Local pattern matching can't understand implicit reasoning.

**Mitigation Strategy: Hybrid Extraction (3-Layer)**

**Layer 1 — Structural Extraction (deterministic, always runs):**
Parse tool calls directly from hook payloads. This captures:
- Every file read/write/edit (from tool use data)
- Every bash command (from tool use data)
- Every TodoWrite call (plan events, directly structured)
- Git operations (branch, commit, diff)

This layer has 100% accuracy for what it captures — it's parsing structured data,
not interpreting natural language.

**Layer 2 — Keyword Extraction (heuristic, always runs):**
Search Claude's response text for high-confidence decision markers:
- Strong signals: "I'll use X instead of Y", "chose X over Y", "rejecting X because"
- Medium signals: "decided to", "the best approach is", "we should use"
- These generate CANDIDATE events with a confidence score

**Layer 3 — Claude Self-Reporting (cooperative, optional):**
Add a system instruction to CLAUDE.md that asks Claude to EXPLICITLY flag decisions:
```markdown
## Memory System Instructions
When you make a significant decision, reject an approach, or discover something
important about the codebase, note it explicitly using this format:
[MEMORY: decision] Chose SQLite over PostgreSQL because zero-config is critical
[MEMORY: rejected] Rejected JSON files — doesn't scale for semantic search
[MEMORY: learned] src/main.py uses the factory pattern for handlers
```

This is the most accurate layer because Claude KNOWS what it decided. The [MEMORY:]
tags are trivially parseable by the extraction engine. The instruction goes in
CLAUDE.md so it's loaded every session automatically.

**Residual risk**: Claude may not always use [MEMORY:] tags. But Layers 1+2 provide
a safety net, and the tags will be used more often than not because Claude is
naturally cooperative with system instructions.

**Revised risk score: 8/25** (down from 20)

---

### M2: F5.3 — Setup Complexity Deters Adoption (Risk: 20/25)

**Root cause**: Too many components to install.

**Mitigation Strategy: Progressive Complexity Model**

**Tier 0 — Zero Install (30 seconds):**
A single shell command that:
1. Creates `.claude/hooks/` directory
2. Copies a single Python script (`cortex.py`) — no dependencies beyond stdlib
3. Configures hooks in `~/.claude/settings.json`
4. Creates initial project context file

```bash
curl -sSL https://raw.githubusercontent.com/.../install.sh | bash
# or
pip install claude-cortex && claude-cortex init
```

At Tier 0, the system:
- Captures events using Layer 1 (structural) + Layer 2 (keyword) only
- Stores events in a simple JSON file (no SQLite)
- Projects a basic briefing to `.claude/context-brief.md`
- No embeddings, no semantic search, no MCP server

**This alone solves 70% of the problem.**

**Tier 1 — Enhanced Storage (2 minutes):**
```bash
claude-cortex upgrade --tier 1
```
- Upgrades storage from JSON to SQLite
- Adds FTS5 full-text search
- Enables salience scoring and decay
- Adds snapshot/replay capability
- Still no embeddings — pure keyword search

**Tier 2 — Semantic Search (5 minutes):**
```bash
claude-cortex upgrade --tier 2
# Downloads ~90MB embedding model on first run
```
- Adds vector embeddings (SentenceTransformers)
- Enables hybrid search (FTS5 + cosine similarity)
- Adds anticipatory context loading from UserPromptSubmit hook

**Tier 3 — Full Power (10 minutes):**
```bash
claude-cortex upgrade --tier 3
```
- Adds MCP server for mid-session memory queries
- Enables branch alignment
- Adds git-tracked projections (Chronicle's PR-visible context)
- Enables contradiction detection

**Key insight**: Each tier is independently useful. Tier 0 alone is valuable.
Users upgrade when they feel the need, not because the system requires it.

**Revised risk score: 5/25** (down from 20)

---

### M3: F4.4 — Circular Reasoning / Echo Chamber (Risk: 15/25)

**Root cause**: Self-referential system reinforces its own biases over time.

**Mitigation Strategy: Reality Anchoring + Provenance Tracking**

**1. Reality Checks at Session Start:**
Before loading the briefing, the system runs automated reality checks using a
bounded, deterministic approach (not open-ended NLP):

**Check 1 — Git branch:** Compare memorized branch against `git rev-parse
--abbrev-ref HEAD`. Exact string match. Mismatch → CONFLICT.

**Check 2 — Git recency:** Compare `git log --since=<last_session_timestamp>
--oneline` to detect external changes since last Cortex session.

**Check 3 — Dependency keywords:** Parse structured config files for known
package names:
- `package.json`: Extract keys from `dependencies` and `devDependencies`
- `pyproject.toml`: Parse `[project.dependencies]` section
- `requirements.txt`: Extract package names (before `==`/`>=`)
Then compare against technology keywords extracted from DECISION_MADE and
KNOWLEDGE_ACQUIRED events. For example, if a decision event says "chose
PostgreSQL," check for `psycopg2`, `asyncpg`, or `sqlalchemy` in deps.
Keyword → dependency mappings are maintained in a configurable lookup table.

**Check 4 — File existence:** For recent FILE_MODIFIED events, verify the
referenced files still exist on disk. Missing files → CONFLICT.

If CONFLICTS detected → add a `[CONFLICT]` warning to the briefing:
  ```markdown
  ## ⚠️ Memory Conflicts Detected
  - Memory says "using PostgreSQL" but pyproject.toml shows "sqlite3" dependency
  - Memory says "branch: feature-auth" but current branch is "main"
  - Memory references src/old_module.py but file no longer exists
  Please verify these before proceeding.
  ```

**Scope note:** This approach restricts checks to structured data (git state,
parsed config files, file system) compared against structured event metadata.
It does not attempt general NLP entity matching. False positives are possible
but low-impact — they generate warnings, not blocking errors.

**2. Provenance Tracking:**
Every event stores which SESSION created it and what TOOL CALL generated it.
Projections include `[source: session-5, confidence: 0.8]` annotations.
This lets Claude (and the user) assess the trustworthiness of each memory.

**3. Confidence Decay:**
In addition to salience decay, add CONFIDENCE decay. Old assertions become
"possibly outdated" after N sessions without reinforcement:
```
confidence = initial_confidence × (0.99 ^ sessions_since_last_reinforced)
```
Memories below confidence threshold get tagged `[POSSIBLY OUTDATED]` in projections.

**4. Periodic Full Refresh:**
Every N sessions (configurable, default 10), the system includes a meta-instruction:
```markdown
## Memory Refresh Due
It's been 10 sessions since a full context refresh. Please verify that
the following key assertions are still accurate by checking the codebase:
- [ ] Storage: SQLite (check pyproject.toml)
- [ ] Framework: FastAPI (check src/main.py)
- [ ] Branch: main (check git status)
```

**Revised risk score: 6/25** (down from 15)

---

## High-Risk Mitigations

### M4: F1.1 — Pattern Matching Misclassifies Events (Risk: 15/25)

**Mitigation**: Confidence scoring on Layer 2 (keyword) extractions.

- Each keyword pattern has a confidence weight
- "I chose X over Y because Z" → 0.95 confidence (very strong signal)
- "I decided to read the file" → 0.3 confidence (weak signal — likely not a decision)
- Events below 0.5 confidence are stored but EXCLUDED from projections
- They remain in the vault for potential retrieval via semantic search

**Additionally**: Layer 3 ([MEMORY:] tags from Claude) always have 1.0 confidence.
Layer 1 (structural/tool-based) always have 1.0 confidence for their event type.

**Tuning note**: All confidence thresholds (0.5 cutoff, pattern weights) and decay
rates (0.995/hour, 0.998/hour, 0.99/session) are **configurable via project
settings** and should be calibrated against real session data during the Tier 0
implementation phase. Initial values are informed estimates. The evaluation plan
(see research paper §11.4) includes a calibration phase after 20+ real sessions.

**Revised risk score: 8/25** (down from 15)

---

### M5: F2.4 — Salience Decay Removes Important Old Decisions (Risk: 15/25)

**Mitigation**: Immortal events for certain types, with growth management.

- Events of type `DECISION_MADE` and `APPROACH_REJECTED` have decay rate = 1.0
  (they NEVER decay). These are permanently retained in the event store.
- Events of type `KNOWLEDGE_ACQUIRED` decay slowly (0.998/hour)
- Events of type `FILE_EXPLORED`, `COMMAND_RUN` decay normally (0.995/hour)
- Users can mark any event as "immortal" via `[MEMORY: permanent]` tag

**Growth management for immortal events** (addresses unbounded growth risk):
While immortal events never leave the event store, their inclusion in the briefing
is tiered to respect the token budget:

1. **Active decisions** (created in last 20 sessions OR accessed recently): Full
   text with reasoning included in briefing
2. **Aging decisions** (20-50 sessions old, never re-accessed): Compressed to
   one-line summaries in briefing
3. **Archived decisions** (50+ sessions old, never re-accessed): Excluded from
   the default briefing; stored in `decisions-archive.md` loadable on demand
4. **Briefing cap**: Maximum 50 full decisions + 30 one-line summaries. The
   "Decisions" section is capped at 40% of the total token budget.
5. **Promotion**: Any accessed archived decision is immediately promoted back
   to "active" status

This resolves the latent conflict between "immortal" (never lose decisions) and
"token-budget-aware" (don't overflow the briefing). Decisions are never deleted
from the event store — only their representation in the briefing changes.

**Additionally**: A persistent `decisions-archive.md` file (Chronicle pattern)
contains all compressed/archived decisions, always available for retrieval even
when excluded from the dynamic briefing.

**Revised risk score: 4/25** (down from 15)

---

### M6: F3.1 — Hook Execution Fails Silently (Risk: 15/25)

**Mitigation**: Health check + graceful degradation.

**1. Health check at SessionStart:**
The SessionStart hook verifies the system is operational:
```bash
#!/bin/bash
# Check if cortex.py exists and is executable
if ! python3 -c "import cortex" 2>/dev/null; then
  echo "[WARNING] Cortex memory system not available. Running without memory."
  exit 0  # Don't block session — graceful degradation
fi
```

**2. Heartbeat file:**
Each hook writes a timestamp to `.claude/cortex-heartbeat`:
```
last_stop_hook: 2026-01-31T14:30:00
last_precompact: 2026-01-31T14:25:00
last_session_start: 2026-01-31T14:00:00
```
If SessionStart finds the heartbeat is stale (no Stop hook in last session),
it flags a warning in the briefing.

**3. Inline fallback:**
If the hook system is completely broken, the system still works at Tier 0 level
because CLAUDE.md with [MEMORY:] instructions is always loaded (it's a static file).
Claude will still self-report decisions even without the extraction engine running.

**Revised risk score: 6/25** (down from 15)

---

### M7: F3.4 — CLAUDE.md Injection Conflict (Risk: 15/25)

**Mitigation**: Additive injection, never overwrite.

**1. Separate file approach:**
Instead of modifying CLAUDE.md, the system writes to:
`.claude/rules/cortex-briefing.md`

Claude Code's `.claude/rules/` directory supports multiple instruction files that
are all loaded at session start. This means:
- User's CLAUDE.md is NEVER touched
- Cortex's briefing is in its own file
- Both are loaded — no conflict possible

**2. Clear delimiters:**
The briefing file includes clear boundaries:
```markdown
<!-- CORTEX MEMORY SYSTEM — AUTO-GENERATED — DO NOT EDIT MANUALLY -->
# Session Context Brief
...
<!-- END CORTEX MEMORY — User's CLAUDE.md is separate and untouched -->
```

**Revised risk score: 2/25** (down from 15)

---

### M8: F5.2 — Briefing Creates False Confidence (Risk: 15/25)

**Mitigation**: Epistemic humility instructions + confidence markers.

**1. Briefing preamble:**
Every generated briefing starts with:
```markdown
# Session Context Brief
*This is a compressed summary of prior sessions. Details may be incomplete.*
*Verify critical assumptions before acting on them. Ask if uncertain.*
```

**2. Confidence markers in content:**
```markdown
## Key Decisions
- Storage: SQLite [HIGH CONFIDENCE — verified in pyproject.toml]
- API style: REST [MEDIUM CONFIDENCE — decided 15 sessions ago, unverified]
```

**3. "Verify before acting" gates:**
For high-impact actions (deleting files, changing architecture, modifying configs),
the briefing includes:
```markdown
## Before Major Changes
If you're about to change the project's architecture, storage, or framework,
first verify the current state by reading the relevant config files.
Do not rely solely on this briefing for destructive operations.
```

**Revised risk score: 8/25** (down from 15)

---

## Mitigation Summary

| Failure | Original Risk | Mitigation | Revised Risk | Reduction |
|---------|:------------:|------------|:------------:|:---------:|
| F1.2: Events missed | 20 | 3-layer extraction + self-reporting | 8 | -60% |
| F5.3: Setup complexity | 20 | Progressive tiers (0-3) | 5 | -75% |
| F4.4: Echo chamber | 15 | Reality anchoring + confidence decay | 6 | -60% |
| F1.1: Misclassification | 15 | Confidence scoring on extractions | 8 | -47% |
| F2.4: Old decisions lost | 15 | Immortal events for decisions | 4 | -73% |
| F3.1: Silent hook failure | 15 | Health check + heartbeat + fallback | 6 | -60% |
| F3.4: CLAUDE.md conflict | 15 | Separate .claude/rules/ file | 2 | -87% |
| F5.2: False confidence | 15 | Epistemic markers + verify gates | 8 | -47% |

**All critical risks reduced below 10/25.**
**All high risks reduced below 10/25.**
**Maximum residual risk: 8/25 (acceptable).**

---

## Refined Architecture (Post-Mitigation)

The final "Cortex" architecture incorporates all mitigations:

```
┌─────────────────────────────────────────────────────────────┐
│                     CORTEX Architecture                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Layer 1: Structural Extraction (100% accuracy)        │   │
│  │ - Parse tool call metadata from hook payloads         │   │
│  │ - FILE_MODIFIED, FILE_EXPLORED, COMMAND_RUN, etc.    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Layer 2: Keyword Extraction (confidence-scored)       │   │
│  │ - Pattern match on Claude's response text             │   │
│  │ - DECISION_MADE, APPROACH_REJECTED, KNOWLEDGE, etc.  │   │
│  │ - Events below 0.5 confidence → vault only            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Layer 3: Claude Self-Reporting (1.0 confidence)       │   │
│  │ - [MEMORY: decision] / [MEMORY: rejected] / etc.     │   │
│  │ - Instruction in .claude/rules/cortex-briefing.md     │   │
│  │ - Parsed by simple regex: \[MEMORY:\s*(\w+)\]\s*(.+) │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Event Store (SQLite)                                  │   │
│  │ - Events with salience, confidence, provenance        │   │
│  │ - Decision/Rejected events are IMMORTAL (no decay)    │   │
│  │ - FTS5 index for keyword search                       │   │
│  │ - Vector index for semantic search (Tier 2+)          │   │
│  │ - Snapshots for fast replay                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Projection Engine                                     │   │
│  │ - Budget-aware briefing generation                    │   │
│  │ - Reality checks (git, config files)                  │   │
│  │ - Confidence markers on all assertions                │   │
│  │ - Epistemic humility preamble                         │   │
│  │ - Outputs to .claude/rules/cortex-briefing.md         │   │
│  │ - Separate from user's CLAUDE.md                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Progressive Tiers                                     │   │
│  │ - Tier 0: JSON events + basic briefing (zero deps)    │   │
│  │ - Tier 1: SQLite + FTS5 + salience scoring            │   │
│  │ - Tier 2: + vector embeddings + semantic search       │   │
│  │ - Tier 3: + MCP server + branch alignment + git track │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Safety Systems                                        │   │
│  │ - Health check + heartbeat monitoring                 │   │
│  │ - Confidence decay on unverified old assertions       │   │
│  │ - Reality anchoring (git state cross-check)           │   │
│  │ - Periodic full refresh prompt                        │   │
│  │ - Contradiction detection and flagging                │   │
│  │ - Graceful degradation on any component failure       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 8 Status: COMPLETE
## All critical and high risks mitigated to ≤8/25
## Architecture refined with mitigations integrated
## Next: Phase 9 — Write the research paper
