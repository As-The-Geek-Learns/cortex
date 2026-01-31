"""Tests for the Cortex briefing generator."""

from pathlib import Path

import pytest

from memory_context_claude_ai.briefing import generate_briefing, write_briefing_to_file
from memory_context_claude_ai.config import CortexConfig
from memory_context_claude_ai.models import EventType, create_event
from memory_context_claude_ai.store import EventStore


class TestGenerateBriefingEmpty:
    """Tests for generate_briefing with empty or minimal store."""

    def test_empty_store_returns_empty_or_minimal(
        self,
        sample_project_hash: str,
        sample_config: CortexConfig,
    ) -> None:
        """Empty store produces no sections (or empty sections)."""
        result = generate_briefing(project_hash=sample_project_hash, config=sample_config)
        assert isinstance(result, str)
        # With no events we may get empty string or just newlines
        assert "Decisions & Rejections" not in result or result.strip() == ""

    def test_requires_project_hash_or_path(
        self,
        sample_config: CortexConfig,
    ) -> None:
        """Raises ValueError when neither project_hash nor project_path provided."""
        with pytest.raises(ValueError, match="project_hash or project_path"):
            generate_briefing(config=sample_config)


class TestGenerateBriefingWithEvents:
    """Tests for generate_briefing with events in the store."""

    def test_includes_decisions_and_rejections(
        self,
        event_store: EventStore,
        sample_events: list,
        sample_project_hash: str,
        sample_config: CortexConfig,
    ) -> None:
        """Briefing includes Decisions & Rejections when immortal events exist."""
        # Append only immortal-type events for predictable section
        immortal = [e for e in sample_events if e.type in (EventType.DECISION_MADE, EventType.APPROACH_REJECTED)]
        event_store.append_many(immortal)

        result = generate_briefing(project_hash=sample_project_hash, config=sample_config)
        assert "# Decisions & Rejections" in result
        assert "Chose SQLite" in result or "SQLite" in result
        assert "Rejected MongoDB" in result or "MongoDB" in result

    def test_includes_active_plan(
        self,
        event_store: EventStore,
        sample_events: list,
        sample_project_hash: str,
        sample_config: CortexConfig,
    ) -> None:
        """Briefing includes Active Plan when PLAN_CREATED and steps exist."""
        plan_events = [e for e in sample_events if e.type in (EventType.PLAN_CREATED, EventType.PLAN_STEP_COMPLETED)]
        event_store.append_many(plan_events)

        result = generate_briefing(project_hash=sample_project_hash, config=sample_config)
        assert "## Active Plan" in result
        assert "implement event extraction" in result or "extraction pipeline" in result
        assert "models.py" in result or "Completed" in result

    def test_includes_recent_context(
        self,
        event_store: EventStore,
        sample_project_hash: str,
        sample_config: CortexConfig,
    ) -> None:
        """Briefing includes Recent Context when non-immortal events exist."""
        e = create_event(
            EventType.KNOWLEDGE_ACQUIRED,
            "Learned: use pathlib for paths",
            session_id="s1",
            git_branch="main",
        )
        event_store.append(e)

        result = generate_briefing(project_hash=sample_project_hash, config=sample_config)
        assert "## Recent Context" in result
        assert "pathlib" in result or "paths" in result

    def test_project_path_derives_hash(self, tmp_path: Path) -> None:
        """generate_briefing(project_path=...) accepts path and derives hash; returns str."""
        config = CortexConfig(cortex_home=tmp_path / ".cortex")
        (tmp_path / ".cortex" / "projects").mkdir(parents=True)
        result = generate_briefing(project_path=str(tmp_path), config=config)
        assert isinstance(result, str)


class TestGenerateBriefingBudget:
    """Tests for briefing budget enforcement."""

    def test_respects_small_budget(
        self,
        event_store: EventStore,
        sample_events: list,
        sample_project_hash: str,
        sample_config: CortexConfig,
    ) -> None:
        """Output is truncated when max_briefing_tokens is very small."""
        event_store.append_many(sample_events)
        small_config = CortexConfig(
            cortex_home=sample_config.cortex_home,
            max_briefing_tokens=50,
            max_full_decisions=2,
            max_summary_decisions=1,
        )

        result = generate_briefing(project_hash=sample_project_hash, config=small_config)
        assert len(result) <= 50 * 4 + 200  # CHARS_PER_TOKEN * tokens + some slack for headers
        assert "# Decisions & Rejections" in result


class TestWriteBriefingToFile:
    """Tests for write_briefing_to_file helper."""

    def test_writes_file_and_creates_parent_dirs(
        self,
        event_store: EventStore,
        sample_project_hash: str,
        sample_config: CortexConfig,
        tmp_path: Path,
    ) -> None:
        """write_briefing_to_file creates parent directories and writes markdown."""
        event_store.append(
            create_event(EventType.DECISION_MADE, "Test decision", session_id="s1"),
        )
        output_path = tmp_path / "subdir" / "rules" / "cortex-briefing.md"
        assert not output_path.parent.exists()

        write_briefing_to_file(
            output_path,
            project_hash=sample_project_hash,
            config=sample_config,
        )

        assert output_path.parent.exists()
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# Decisions & Rejections" in content
        assert "Test decision" in content

    def test_write_matches_generate(
        self,
        event_store: EventStore,
        sample_project_hash: str,
        sample_config: CortexConfig,
        tmp_path: Path,
    ) -> None:
        """Written file content equals generate_briefing output."""
        event_store.append(
            create_event(EventType.PREFERENCE_NOTED, "Use type hints", session_id="s1"),
        )
        output_path = tmp_path / "briefing.md"

        write_briefing_to_file(
            output_path,
            project_hash=sample_project_hash,
            config=sample_config,
        )
        expected = generate_briefing(project_hash=sample_project_hash, config=sample_config)
        assert output_path.read_text(encoding="utf-8") == expected
