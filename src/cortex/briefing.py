"""Briefing generation for Cortex Tier 0.

Converts stored events into a markdown context document loaded at session start
(e.g. .claude/rules/cortex-briefing.md). Respects config briefing budget and
tiered inclusion (immortal, active plan, recent).
"""

from pathlib import Path

from cortex.config import CortexConfig, load_config
from cortex.models import Event
from cortex.project import get_project_hash
from cortex.store import EventStore

# Approximate characters per token for budget enforcement (conservative for English/code).
CHARS_PER_TOKEN = 4


def generate_briefing(
    project_hash: str | None = None,
    project_path: str | None = None,
    config: CortexConfig | None = None,
    branch: str | None = None,
) -> str:
    """Generate a markdown briefing from stored events for the given project.

    Uses EventStore.load_for_briefing() and applies the config briefing budget.
    Sections: Decisions & Rejections (immortal), Active Plan, Recent Context.

    Args:
        project_hash: 16-char project hash. If None, project_path must be set.
        project_path: Project directory path. If set, project_hash is derived
                      via get_project_hash(project_path). Ignored if project_hash set.
        config: Optional config. Defaults to load_config().
        branch: Optional git branch filter for events.

    Returns:
        Markdown string suitable for cortex-briefing.md.

    Raises:
        ValueError: If neither project_hash nor project_path is provided.
    """
    if project_hash is None and project_path is None:
        raise ValueError("Either project_hash or project_path must be provided")
    if project_hash is None:
        assert project_path is not None  # Guaranteed by check above
        project_hash = get_project_hash(project_path)

    config = config or load_config()
    store = EventStore(project_hash, config)
    data = store.load_for_briefing(branch=branch)

    immortal = data["immortal"]
    active_plan = data["active_plan"]
    recent = data["recent"]

    max_chars = config.max_briefing_tokens * CHARS_PER_TOKEN
    max_full = config.max_full_decisions
    max_summary = config.max_summary_decisions

    parts: list[str] = []
    used = 0

    def add(s: str) -> bool:
        nonlocal used
        if used + len(s) > max_chars:
            return False
        parts.append(s)
        used += len(s)
        return True

    # Section: Decisions & Rejections (immortal)
    full_immortal = immortal[:max_full]
    summary_immortal = immortal[max_full : max_full + max_summary] if max_summary else []

    if full_immortal or summary_immortal:
        if not add("# Decisions & Rejections\n\n"):
            return "".join(parts)
        for e in full_immortal:
            line = _format_event_line(e, full=True)
            if not add(line):
                return "".join(parts)
        for e in summary_immortal:
            line = _format_event_line(e, full=False)
            if not add(line):
                return "".join(parts)
        if not add("\n"):
            return "".join(parts)

    # Section: Active Plan
    if active_plan:
        if not add("## Active Plan\n\n"):
            return "".join(parts)
        for e in active_plan:
            line = _format_event_line(e, full=True)
            if not add(line):
                return "".join(parts)
        if not add("\n"):
            return "".join(parts)

    # Section: Recent Context
    if recent:
        if not add("## Recent Context\n\n"):
            return "".join(parts)
        for e in recent:
            line = _format_event_line(e, full=True)
            if not add(line):
                return "".join(parts)

    return "".join(parts)


def _format_event_line(event: Event, full: bool = True) -> str:
    """Format a single event as a markdown list item."""
    if full or not event.content:
        content = event.content.strip() or "(no content)"
        return f"- {content}\n"
    # One-line summary: first line or truncated to 80 chars
    raw = event.content.strip()
    first_line = raw.split("\n")[0][:80] if raw else "(no content)"
    if len(raw.split("\n")[0]) > 80:
        first_line += "..."
    return f"- {first_line}\n"


def write_briefing_to_file(
    output_path: str | Path,
    project_hash: str | None = None,
    project_path: str | None = None,
    config: CortexConfig | None = None,
    branch: str | None = None,
) -> None:
    """Generate a briefing and write it to a file for use by Phase 6 hooks.

    Creates parent directories if needed. Typical output_path:
    .claude/rules/cortex-briefing.md

    Args:
        output_path: File path to write the markdown briefing.
        project_hash: 16-char project hash. If None, project_path must be set.
        project_path: Project directory path (used to derive project_hash if needed).
        config: Optional config. Defaults to load_config().
        branch: Optional git branch filter for events.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = generate_briefing(
        project_hash=project_hash,
        project_path=project_path,
        config=config,
        branch=branch,
    )
    output_path.write_text(content, encoding="utf-8")
