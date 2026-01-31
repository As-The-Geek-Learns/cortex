# memory-context-claude-ai

Python project for memory and context management with Claude AI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install ruff pytest pre-commit
pre-commit install
```

## Development

```bash
# Lint
ruff check .

# Format
ruff format .

# Test
pytest tests/

# Run all pre-commit hooks
pre-commit run --all-files
```
