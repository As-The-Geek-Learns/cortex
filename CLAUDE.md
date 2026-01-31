# memory-context-claude-ai

## Project Overview

memory-context-claude-ai is a Python project for memory and context management with Claude AI.

**Tech Stack:**
- Language: Python 3.11+
- Linting/Formatting: Ruff
- Testing: pytest
- Build: Standard Python packaging (pyproject.toml)

## Project Structure

```
memory-context-claude-ai/
├── src/
│   └── memory_context_claude_ai/  # Main package
├── tests/
├── docs/
├── .github/
│   ├── workflows/         # CI/CD
│   └── SECURITY-REVIEW.md # Security checklist
├── .cursor/rules/         # Cursor AI rules
├── SECURITY.md            # Security policy
└── pyproject.toml
```

## Development Guidelines

### Code Style

- Use Python 3.11+ with Ruff for linting and formatting
- Line length: 120 characters
- Quote style: double quotes
- Keep modules focused and under 300 lines
- Extract reusable logic to utilities

### Naming Conventions

- Modules: snake_case (`context_manager.py`)
- Classes: PascalCase (`MemoryStore`)
- Functions/variables: snake_case (`get_context`)
- Constants: UPPER_SNAKE_CASE (`MAX_CONTEXT_LENGTH`)

### Security Requirements

1. **Input Validation**: Use centralized validation functions (Pydantic where appropriate)
2. **SQL Queries**: Always use parameterized statements
3. **Error Handling**: Never expose stack traces to users
4. **Dependencies**: Run `pip-audit` before commits

See [SECURITY.md](./SECURITY.md) for full security policy.

## Key Files

| File | Purpose |
|------|---------|
| `src/memory_context_claude_ai/` | Main package |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `.cursor/rules/*.mdc` | Cursor AI context rules |

## Common Tasks

### Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/
```

### Checking Code Quality

```bash
ruff check .
ruff format --check .
pre-commit run --all-files
pip-audit
```

## Architecture Decisions

<!-- Document key technical decisions -->
