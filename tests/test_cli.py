"""Tests for Cortex CLI commands: reset, status, init."""

import json
import sys
from io import StringIO

from cortex.cli import cmd_init, cmd_reset, cmd_status, get_init_hook_json, setup_claude_rules
from cortex.project import get_project_hash
from cortex.store import EventStore, HookState


class TestCmdReset:
    """Test cortex reset: clear store + state for project."""

    def test_reset_clears_store_and_state(self, tmp_path, tmp_cortex_home, sample_config, sample_events, monkeypatch):
        monkeypatch.setattr("cortex.cli.load_config", lambda: sample_config)
        project_hash = get_project_hash(str(tmp_path))
        store = EventStore(project_hash, sample_config)
        state = HookState(project_hash, sample_config)
        store.append_many(sample_events[:2])
        state.update(last_transcript_position=100, last_transcript_path="/some/path.jsonl")

        code = cmd_reset(cwd=str(tmp_path))
        assert code == 0
        assert store.count() == 0
        loaded = state.load()
        assert loaded["last_transcript_position"] == 0
        assert loaded["last_transcript_path"] == ""
        assert loaded["last_session_id"] == ""
        assert loaded["session_count"] == 0
        assert loaded["last_extraction_time"] == ""

    def test_reset_prints_confirmation(self, tmp_path, tmp_cortex_home, sample_config, monkeypatch):
        monkeypatch.setattr("cortex.cli.load_config", lambda: sample_config)
        project_hash = get_project_hash(str(tmp_path))
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            code = cmd_reset(cwd=str(tmp_path))
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert code == 0
        assert project_hash in out
        assert "reset" in out.lower()

    def test_reset_empty_cwd_returns_one(self):
        code = cmd_reset(cwd="")
        assert code == 1


class TestCmdStatus:
    """Test cortex status: project hash, event count, last extraction."""

    def test_status_shows_project_and_count(self, tmp_path, tmp_cortex_home, sample_config, sample_events, monkeypatch):
        monkeypatch.setattr("cortex.cli.load_config", lambda: sample_config)
        project_hash = get_project_hash(str(tmp_path))
        store = EventStore(project_hash, sample_config)
        store.append_many(sample_events[:2])

        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            code = cmd_status(cwd=str(tmp_path))
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert code == 0
        assert project_hash in out
        assert "events: 2" in out or "events:2" in out.replace(" ", "")
        assert "project:" in out or "hash:" in out

    def test_status_zero_events(self, tmp_path, tmp_cortex_home, sample_config, monkeypatch):
        monkeypatch.setattr("cortex.cli.load_config", lambda: sample_config)
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            code = cmd_status(cwd=str(tmp_path))
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert code == 0
        assert "events: 0" in out or "events:0" in out.replace(" ", "")
        assert "last_extraction:" in out

    def test_status_empty_cwd_returns_one(self, monkeypatch):
        code = cmd_status(cwd="")
        assert code == 1


class TestGetInitHookJson:
    """Test get_init_hook_json produces valid Claude Code hook config."""

    def test_output_is_valid_json(self):
        out = get_init_hook_json()
        data = json.loads(out)
        assert isinstance(data, dict)
        assert "hooks" in data

    def test_contains_three_hook_names(self):
        out = get_init_hook_json()
        data = json.loads(out)
        hooks = data["hooks"]
        assert "Stop" in hooks
        assert "PreCompact" in hooks
        assert "SessionStart" in hooks

    def test_commands_use_cortex(self):
        out = get_init_hook_json()
        assert "cortex stop" in out
        assert "cortex precompact" in out
        assert "cortex session-start" in out


class TestCmdInit:
    """Test cortex init prints hook JSON to stdout."""

    def test_init_prints_valid_json(self):
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            code = cmd_init()
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert code == 0
        data = json.loads(out)
        assert "hooks" in data
        assert "Stop" in data["hooks"]

    def test_init_with_setup_creates_rules_files(self, tmp_path):
        """Test cortex init --setup creates .claude/rules/ files."""
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            code = cmd_init(cwd=str(tmp_path), setup=True)
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert code == 0

        # Check files were created
        rules_dir = tmp_path / ".claude" / "rules"
        assert rules_dir.exists()

        memory_file = rules_dir / "cortex-memory-instructions.md"
        assert memory_file.exists()
        content = memory_file.read_text()
        assert "[MEMORY:" in content  # Template content check

        briefing_file = rules_dir / "cortex-briefing.md"
        assert briefing_file.exists()
        assert "auto-populated" in briefing_file.read_text()

        # Check output mentions created files
        assert "Created:" in out

    def test_init_with_setup_empty_cwd_returns_one(self):
        """Test cortex init --setup with empty cwd fails."""
        code = cmd_init(cwd="", setup=True)
        assert code == 1


class TestSetupClaudeRules:
    """Test setup_claude_rules creates .claude/rules/ files."""

    def test_creates_rules_directory(self, tmp_path):
        """Test creates .claude/rules/ directory structure."""
        result = setup_claude_rules(str(tmp_path))

        rules_dir = tmp_path / ".claude" / "rules"
        assert rules_dir.exists()
        assert rules_dir.is_dir()
        assert len(result["errors"]) == 0

    def test_creates_memory_instructions_file(self, tmp_path):
        """Test creates cortex-memory-instructions.md from template."""
        result = setup_claude_rules(str(tmp_path))

        memory_file = tmp_path / ".claude" / "rules" / "cortex-memory-instructions.md"
        assert memory_file.exists()
        assert str(memory_file) in result["created"]

        # Check it has expected content from template
        content = memory_file.read_text()
        assert "Cortex" in content
        assert "[MEMORY:" in content
        assert "Layer 3" in content

    def test_creates_briefing_file(self, tmp_path):
        """Test creates empty cortex-briefing.md placeholder."""
        result = setup_claude_rules(str(tmp_path))

        briefing_file = tmp_path / ".claude" / "rules" / "cortex-briefing.md"
        assert briefing_file.exists()
        assert str(briefing_file) in result["created"]

        content = briefing_file.read_text()
        assert "auto-populated" in content
        assert "cortex session-start" in content

    def test_skips_existing_files_without_force(self, tmp_path):
        """Test does not overwrite existing files unless force=True."""
        # Create existing files
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        memory_file = rules_dir / "cortex-memory-instructions.md"
        memory_file.write_text("existing content")

        briefing_file = rules_dir / "cortex-briefing.md"
        briefing_file.write_text("existing briefing")

        result = setup_claude_rules(str(tmp_path), force=False)

        # Files should be skipped
        assert str(memory_file) in result["skipped"]
        assert str(briefing_file) in result["skipped"]
        assert len(result["created"]) == 0

        # Content should be unchanged
        assert memory_file.read_text() == "existing content"
        assert briefing_file.read_text() == "existing briefing"

    def test_overwrites_with_force(self, tmp_path):
        """Test overwrites existing files when force=True."""
        # Create existing files
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        memory_file = rules_dir / "cortex-memory-instructions.md"
        memory_file.write_text("old content")

        briefing_file = rules_dir / "cortex-briefing.md"
        briefing_file.write_text("old briefing")

        result = setup_claude_rules(str(tmp_path), force=True)

        # Files should be created (overwritten)
        assert str(memory_file) in result["created"]
        assert str(briefing_file) in result["created"]
        assert len(result["skipped"]) == 0

        # Content should be new
        assert "[MEMORY:" in memory_file.read_text()
        assert "auto-populated" in briefing_file.read_text()

    def test_handles_existing_claude_directory(self, tmp_path):
        """Test works when .claude/ already exists but not rules/."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text("{}")

        result = setup_claude_rules(str(tmp_path))

        assert len(result["errors"]) == 0
        assert len(result["created"]) == 2
        assert (tmp_path / ".claude" / "rules" / "cortex-memory-instructions.md").exists()
