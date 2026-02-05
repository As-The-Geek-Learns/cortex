"""Tests for Cortex CLI commands: reset, status, init."""

import json
import sys
from io import StringIO

from cortex.cli import cmd_init, cmd_reset, cmd_status, get_init_hook_json
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
