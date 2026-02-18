# Cortex memory instructions (Layer 3)

Cortex persists important context across sessions. Use the `[MEMORY: ...]` tag when you want something to be remembered in future sessions.

## When to use [MEMORY:]

- **Decisions:** After choosing an approach, technology, or design (e.g. "Use SQLite for storage", "Prefer double quotes for strings").
- **Rejections:** When you explicitly reject an alternative and why (e.g. "Rejected PostgreSQL — zero-config requirement").
- **Preferences:** User or project preferences that affect future work (e.g. "Tests live in tests/, not test/").
- **Important facts:** One-off discoveries that future sessions should know (e.g. "The API key is read from env X").

## What to put inside the tag

- Keep it short: one sentence or a short bullet list.
- Be specific: "Use SQLite" is better than "We chose a database."
- No code: put the *fact* in the tag; code lives in the codebase.

## Example

- `[MEMORY: Use SQLite for local storage — zero-config, single file.]`
- `[MEMORY: Rejected MongoDB — overkill for single-user; no need for scaling.]`
- `[MEMORY: User prefers pytest over unittest; tests in tests/ with -v.]`

Cortex will extract these and include them in the briefing loaded at the start of each new session.
