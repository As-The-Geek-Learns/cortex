# Copilot Code Review Instructions — Cortex

## Project context

Event-sourced memory architecture for AI coding assistants with automatic session continuity and token-budget-aware briefings.
Stack: Python, event sourcing architecture.

## Review priorities

1. **Security first** — flag hardcoded secrets. Session data may contain sensitive code context — never log raw content.
2. **Data integrity** — event-sourced data must be immutable once written. Flag any mutation of historical events.
3. **Token budget awareness** — flag unbounded string operations that could exceed token limits without truncation.
4. **Type hints** — all public functions must have type annotations.
5. **Error handling** — never use bare except. Events that fail to write must surface errors, not silently drop.

## Code style

- Conventional commits: feat:, fix:, docs:, refactor:, test:, chore:.
- Comments explain *why*, never *what*.
- Follow PEP 8. Prefer dataclasses or Pydantic for structured data.

## Patterns to flag

- Mutable state where immutable events are expected.
- Missing bounds checks on token/character counts.
- Bare except clauses.
- File I/O without context managers.
