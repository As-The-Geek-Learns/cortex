# Phase 4: Comparison Round 1
# Scoring, Ranking, and Selection of Top 2 Solutions
# Date: 2026-01-31

## Scoring Methodology

Each solution is scored on 10 criteria derived from Phase 1's requirements.
Scale: 1 (poor) to 5 (excellent). Criteria are weighted by importance.

### Criteria & Weights

| # | Criterion | Weight | Rationale |
|---|-----------|--------|-----------|
| C1 | Automatic capture (zero user effort) | 5 | FR-1, NFR-1: Deal-breaker if missing |
| C2 | Selective/relevant recall | 5 | FR-4: Loading everything wastes tokens |
| C3 | Decision history preservation | 4 | FR-5: Prevents regression to rejected ideas |
| C4 | Plan/task continuity | 4 | FR-6: Multi-step work is the core use case |
| C5 | Token efficiency (<15% budget) | 4 | NFR-2: Must leave room for actual work |
| C6 | Implementation feasibility | 3 | NFR-4, NFR-8: Must work with existing tools |
| C7 | Scalability (100+ sessions) | 3 | Long-term viability |
| C8 | Cross-project isolation | 3 | FR-8: Don't contaminate projects |
| C9 | Human inspectability | 2 | NFR-6: User should be able to review/edit |
| C10 | Startup latency (<5s) | 2 | NFR-3: Can't block the developer |

**Total possible weighted score: 175**

---

## Detailed Scoring

### Solution 1: "The Cognitive Journal"

| Criterion | Score | Justification |
|-----------|:-----:|---------------|
| C1: Auto capture | 4 | Hook-triggered, but depends on Claude's ability to self-journal well |
| C2: Selective recall | 2 | Loads recent journal, not semantically relevant content |
| C3: Decision history | 4 | Explicit decision registry is strong |
| C4: Plan continuity | 4 | Journal structure includes plan state explicitly |
| C5: Token efficiency | 4 | Journal entries are structured and compact |
| C6: Feasibility | 5 | Simple hooks + file writes — easiest to implement |
| C7: Scalability | 3 | Index.json helps, but no semantic search for old sessions |
| C8: Cross-project | 4 | Directory-per-project is clean |
| C9: Inspectability | 5 | Human-readable markdown — excellent |
| C10: Latency | 5 | Just file reads — near-instant |

**Weighted Score: 130/175**

**Key Strength**: Simplicity and inspectability.
**Key Weakness**: No semantic awareness — loads recent, not relevant.

---

### Solution 2: "The Memory Palace"

| Criterion | Score | Justification |
|-----------|:-----:|---------------|
| C1: Auto capture | 4 | Stop hook extraction + knowledge graph |
| C2: Selective recall | 5 | Semantic search + salience scoring — best in class |
| C3: Decision history | 4 | Decisions are first-class graph nodes |
| C4: Plan continuity | 3 | Plans are stored but not a primary focus |
| C5: Token efficiency | 4 | Top-K retrieval controls token budget |
| C6: Feasibility | 2 | Complex: MCP server + embeddings + graph DB |
| C7: Scalability | 5 | Graph + vector search scales well |
| C8: Cross-project | 4 | Graph is project-scoped |
| C9: Inspectability | 2 | Graph DB is not easily human-readable |
| C10: Latency | 3 | Embedding computation + search adds time |

**Weighted Score: 128/175**

**Key Strength**: Best semantic retrieval — finds relevant, not just recent.
**Key Weakness**: Implementation complexity and poor inspectability.

---

### Solution 3: "Git-for-Thought"

| Criterion | Score | Justification |
|-----------|:-----:|---------------|
| C1: Auto capture | 4 | PreCompact hook computes diffs automatically |
| C2: Selective recall | 2 | Loads HEAD.md — no semantic search |
| C3: Decision history | 3 | Decisions in HEAD.md but no dedicated registry |
| C4: Plan continuity | 4 | HEAD.md tracks current work state well |
| C5: Token efficiency | 4 | HEAD.md is designed to be compact |
| C6: Feasibility | 4 | Moderate — hooks + file diffs |
| C7: Scalability | 3 | Diff history grows but HEAD stays compact |
| C8: Cross-project | 5 | Lives in project directory — perfect isolation |
| C9: Inspectability | 5 | Markdown + diffs — excellent for developers |
| C10: Latency | 5 | Just file reads |

**Weighted Score: 127/175**

**Key Strength**: Elegant metaphor, git-native, excellent inspectability.
**Key Weakness**: No semantic search — HEAD.md is all you get.
**Novel value**: Branch alignment is genuinely interesting.

---

### Solution 4: "Event Sourcery"

| Criterion | Score | Justification |
|-----------|:-----:|---------------|
| C1: Auto capture | 5 | Every exchange generates typed events — most thorough |
| C2: Selective recall | 4 | Projections are focused; event queries are targeted |
| C3: Decision history | 5 | Decision events are first-class — best in class |
| C4: Plan continuity | 5 | Plan events reconstruct exact task state — best in class |
| C5: Token efficiency | 4 | Projections are compact; only relevant state loaded |
| C6: Feasibility | 3 | Event classification needs accuracy; MCP server required |
| C7: Scalability | 5 | Event stores scale linearly; snapshots prevent replay cost |
| C8: Cross-project | 4 | Project-scoped events |
| C9: Inspectability | 3 | Events are structured but verbose; projections help |
| C10: Latency | 3 | Snapshot + replay adds moderate startup time |

**Weighted Score: 145/175**

**Key Strength**: Most complete capture + best decision/plan continuity.
**Key Weakness**: Event classification accuracy is critical.
**Standout**: The projection concept — different views from same data.

---

### Solution 5: "The Dual-Mind"

| Criterion | Score | Justification |
|-----------|:-----:|---------------|
| C1: Auto capture | 5 | Background scribe captures everything automatically |
| C2: Selective recall | 5 | Anticipatory loading based on user's intent — best in class |
| C3: Decision history | 4 | Captured in session notes, queryable |
| C4: Plan continuity | 5 | Briefing document explicitly includes plan state |
| C5: Token efficiency | 5 | Briefing is custom-generated to fit token budget — best |
| C6: Feasibility | 2 | Requires secondary API calls, background processing |
| C7: Scalability | 4 | Semantic search + summarization handles history well |
| C8: Cross-project | 4 | Project-scoped session notes |
| C9: Inspectability | 4 | Briefing documents are readable; session notes are structured |
| C10: Latency | 2 | Secondary LLM call at startup adds 3-10 seconds |

**Weighted Score: 143/175**

**Key Strength**: Most intelligent loading — anticipates what you need.
**Key Weakness**: Cost and latency from secondary API calls.
**Standout**: Using AI to summarize AI is the optimal compression.

---

## Ranking Summary

| Rank | Solution | Weighted Score | Key Differentiator |
|:----:|----------|:--------------:|-------------------|
| 1 | Event Sourcery | 145/175 | Best capture + decision/plan tracking |
| 2 | Dual-Mind | 143/175 | Best selective recall + anticipatory loading |
| 3 | Cognitive Journal | 130/175 | Simplest implementation |
| 4 | Memory Palace | 128/175 | Best semantic retrieval |
| 5 | Git-for-Thought | 127/175 | Best developer UX / metaphor |

---

## Selection: Top 2

### Selected: Event Sourcery (#4) and Dual-Mind (#5)

**Rationale for selection:**

These two solutions scored highest AND they have **complementary strengths**:

| Aspect | Event Sourcery | Dual-Mind |
|--------|:---:|:---:|
| Capture quality | ✅✅ Best | ✅ Good |
| Recall intelligence | ⚠️ Projection-based | ✅✅ Anticipatory |
| Decision tracking | ✅✅ Best | ✅ Good |
| Token efficiency | ✅ Good | ✅✅ Best |
| Feasibility | ⚠️ Medium | ❌ Complex |

**The ideal solution may be a hybrid** — Event Sourcery's capture and storage
with Dual-Mind's intelligent loading and anticipatory briefing.

### Why not the others?

- **Cognitive Journal** (#1 by simplicity): Good MVP, but no semantic awareness
  means it will fail for non-linear workflows. Could serve as a fallback/baseline.
- **Memory Palace** (#2 by retrieval): Semantic search is powerful, but the
  implementation complexity rivals Dual-Mind with less payoff.
- **Git-for-Thought** (#3 by UX): Beautiful concept, but HEAD.md is just a
  fancier CLAUDE.md. The branch alignment idea should be STOLEN for the hybrid.

---

## Insights for Phase 5

### Elements to carry forward:
1. **Event-sourced capture** from Event Sourcery — typed events are the gold standard
2. **Anticipatory briefing** from Dual-Mind — load what's NEEDED, not what's RECENT
3. **Branch alignment** from Git-for-Thought — context follows code branches
4. **Human-readable output** from Cognitive Journal — inspectability matters
5. **Salience scoring** from Memory Palace / claude-cortex — not all info is equal

### Questions to answer in Phase 5:
1. Can event classification work reliably without a secondary LLM call?
2. Can anticipatory loading work without blocking session start?
3. What's the optimal hybrid architecture?
4. How to handle the Scribe's background process within Claude Code's constraints?
5. What existing infrastructure (hooks, MCP) best supports each component?

---

## Phase 4 Status: COMPLETE
## Top 2 Selected: Event Sourcery + Dual-Mind
## Direction: Explore hybrid architecture combining strengths of both
## Next: Phase 5 — Deep research on top 2 + generate new hybrid ideas
