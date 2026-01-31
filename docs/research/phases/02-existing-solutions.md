# Phase 2: Survey of Existing Solutions
# How Others Are Addressing the Context Window Problem
# Date: 2026-01-31

## 1. Native Platform Approaches

### 1.1 Claude Code's Built-in CLAUDE.md System
- **Mechanism**: File-based memory read at session start
- **Scope**: Project-level (`./CLAUDE.md`) and global (`~/.claude/CLAUDE.md`)
- **Strengths**: Zero-config, always loaded, version-controllable
- **Weaknesses**: Static/manual, no automatic capture, no semantic retrieval
- **Source**: [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)

### 1.2 Anthropic's Context Management Platform (Sept 2025)
- **Mechanism**: File-based memory tool + context editing
- **Key stat**: 84% token reduction, 39% performance improvement
- **Scope**: Developer platform (API-level), not directly in Claude Code CLI
- **Source**: [Anthropic Context Management](https://www.anthropic.com/news/context-management)

### 1.3 Claude Code Auto-Compaction
- **Mechanism**: Automatic summarization when context approaches limit
- **Strengths**: Transparent, preserves recent context
- **Weaknesses**: Lossy — nuanced decisions and exploration history lost
- **Source**: Built into Claude Code

### 1.4 Claude Code Hooks System
- **Events**: PreCompact, PostCompact, SessionStart, SessionEnd, Stop, etc.
- **Mechanism**: Shell commands triggered at lifecycle points
- **Strengths**: Deterministic, customizable, can capture/inject context
- **Key insight**: PreCompact + SessionStart = capture before loss + inject at start
- **Source**: [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)

## 2. Academic / Research Approaches

### 2.1 MemGPT / Letta (UC Berkeley, 2023 → Letta 2024-2025)
- **Paradigm**: LLM as Operating System — virtual context management
- **Architecture**:
  - Primary Context (RAM) = LLM context window
  - External Context (Disk) = vector DB + archival storage
  - The LLM itself manages paging between tiers via tool calls
- **Key innovations**:
  - Self-editing memory (LLM decides what to store/evict)
  - Strategic forgetting (summarize + delete = feature, not bug)
  - Memory pressure interrupts (like OS page faults)
- **16.4K GitHub stars** as of May 2025
- **Source**: [MemGPT Paper](https://arxiv.org/abs/2310.08560), [Letta Docs](https://docs.letta.com/)

### 2.2 MIRIX — Multi-Type Memory Architecture
- **6 memory types**: Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault
- **Each managed by a dedicated agent** coordinated by meta memory controller
- **Source**: Academic research (2025)

### 2.3 LightMem — Lightweight Memory Framework
- **Inspired by**: Atkinson-Shiffrin human memory model
- **Approach**: Filter → Organize → Consolidate information
- **Focus**: Reducing memory system overhead
- **Source**: [LightMem Paper](https://arxiv.org/html/2510.18866v1)

### 2.4 HippoRAG — Neurobiologically Inspired Memory
- **Inspired by**: Hippocampal indexing theory
- **Approach**: Mimics how human hippocampus indexes long-term memory
- **Source**: Gutiérrez et al., 2024

### 2.5 Nemori — Self-Organizing Memory
- **Approach**: Autonomously segments conversations into semantic episodes
- **Uses**: Free-Energy Principle for prediction-calibration loops
- **Key insight**: Prediction errors drive knowledge integration

### 2.6 MemOS — Unified Memory Operating System
- **Approach**: Orchestrates parametric, activation, and plaintext memory
- **Scope**: Multi-agent sharing, lifecycle management

## 3. Community-Built MCP Solutions (Claude-Specific)

### 3.1 memory-mcp (Two-Tier Architecture)
- **Tier 1**: CLAUDE.md (~150 lines) — auto-generated briefing, read at startup
- **Tier 2**: `.memory/state.json` (unlimited) — full knowledge store via MCP tools
- **Claim**: 80% of sessions need only Tier 1
- **Source**: [DEV Community Article](https://dev.to/suede/the-architecture-of-persistent-memory-for-claude-code-17d)

### 3.2 claude-cortex (Brain-Like Memory)
- **3 memory types**: STM (session), LTM (cross-session), Episodic (events)
- **Salience scoring**: 0.0-1.0 based on information type
- **Temporal decay**: `score = base_salience × (0.995 ^ hours_since_access)`
- **Reinforcement**: 1.2× boost on each access
- **Consolidation**: STM → LTM when score > 0.6
- **Knowledge graph**: Semantic linking with cosine similarity ≥ 0.6
- **Contradiction detection**: Flags conflicting memories
- **Source**: [claude-cortex](https://github.com/mkdelta221/claude-cortex)

### 3.3 mcp-memory-service (Semantic Search)
- **Mechanism**: Persistent memory with vector embeddings
- **Speed**: ~5ms retrieval
- **Compatible**: SHODH Unified Memory API Specification v1.0.0
- **Source**: [mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)

### 3.4 mcp-memory-keeper (Checkpoint System)
- **Mechanism**: Manual checkpoint save/restore (like game saves)
- **Simple**: User-triggered, explicit save points
- **Source**: [mcp-memory-keeper](https://github.com/mkreyman/mcp-memory-keeper)

### 3.5 claude-continuity (Auto State Persistence)
- **Mechanism**: Automatic state persistence in `~/.claude_states`
- **Features**: Multi-project support, zero configuration
- **Source**: [claude-continuity](https://github.com/donthemannn/claude-continuity)

### 3.6 claude-mem (Full Capture + Compression)
- **Mechanism**: Captures everything Claude does, compresses with AI
- **Injection**: Injects relevant context into future sessions
- **Source**: [claude-mem](https://github.com/thedotmack/claude-mem)

### 3.7 claude-diary (Session Journaling)
- **Mechanism**: PreCompact hook writes markdown diary entries
- **Sections**: Task summary, work done, design decisions, user preferences
- **Source**: [claude-diary](https://github.com/rlancemartin/claude-diary)

### 3.8 claude-cognitive (Activation-Based File Tracking)
- **Mechanism**: Files decay (0.85 per turn) and activate on mention
- **Co-activation**: Related files activate together
- **Source**: [claude-cognitive](https://github.com/GMaN1911/claude-cognitive)

## 4. Commercial/Industry Approaches

### 4.1 Amazon Bedrock AgentCore Memory (2025)
- **Short-term**: Working memory for current session
- **Long-term**: Persistent insights and preferences
- **Managed service**: AWS handles infrastructure
- **Source**: [AWS Blog](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/)

### 4.2 Pieces (Local-First Developer Memory)
- **Captures**: Snippets, terminal commands, notes, browser research, chats
- **Resurfaces**: Relevant context when needed
- **Privacy**: Data stays on-device by default
- **Source**: [Pieces](https://pieces.app/blog/best-ai-memory-systems)

### 4.3 Windsurf / Trae / Cursor (AI-Native IDEs)
- **Windsurf**: Built-in persistent memory and multi-step agent workflows
- **Trae**: Long-context memory and built-in agents
- **Cursor**: Chat-based agent features (less memory-focused)

## 5. Design Pattern Taxonomy

From the research, the following design patterns emerge:

| Pattern | Example | Automatic? | Semantic? | Scalable? |
|---------|---------|------------|-----------|-----------|
| Static file injection | CLAUDE.md | No | No | Limited |
| Checkpoint/save | mcp-memory-keeper | Manual | No | Medium |
| Hook-based capture | claude-diary | Yes | No | Medium |
| Two-tier (briefing + full store) | memory-mcp | Yes | Partial | Good |
| Salience-scored + decay | claude-cortex | Yes | Yes | Good |
| Full OS-style virtual memory | MemGPT/Letta | Yes | Yes | Excellent |
| Capture + compress + inject | claude-mem | Yes | Yes | Good |
| Multi-type hierarchical | MIRIX | Yes | Yes | Complex |
| Activation-based tracking | claude-cognitive | Yes | Partial | Medium |

## 6. Key Insights from Research

### 6.1 Consensus Points
1. **The problem is real and universal** — #1 pain point across all AI coding tools
2. **Memory must be automatic** — Manual systems get abandoned
3. **Two-tier minimum** — Fast-load summary + deeper retrieval store
4. **The AI should manage its own memory** — Self-editing > rule-based
5. **Hooks are the integration point** for Claude Code specifically

### 6.2 Open Gaps
1. **No solution handles selective relevance well** — Most inject everything or nothing
2. **Cross-project contamination** is poorly addressed
3. **Decision history** (rejected approaches) is rarely captured explicitly
4. **Plan continuity** is the weakest area — in-progress multi-step work
5. **Token budget awareness** — Few solutions optimize for window consumption

### 6.3 The Killer Feature Nobody Has
- **Proactive context injection**: The system anticipates what context will be needed
  based on the user's initial message, and loads ONLY that context
- This requires understanding the task before loading memory — a chicken-and-egg problem

---

## Phase 2 Status: COMPLETE
## Key Finding: The MemGPT/OS paradigm + Claude Code hooks + two-tier architecture
## form the strongest foundation. But no existing solution fully solves the problem
## as defined in Phase 1's requirements. Significant innovation is needed in:
## selective relevance, proactive loading, and decision/plan continuity.
