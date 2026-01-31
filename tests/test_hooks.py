"""Tests for Cortex hook handlers (Stop, PreCompact, SessionStart)."""

import io
import sys

from memory_context_claude_ai.hooks import (
    handle_precompact,
    handle_session_start,
    handle_stop,
    read_payload,
)
from memory_context_claude_ai.project import get_project_hash
from memory_context_claude_ai.store import EventStore, HookState


class TestReadPayload:
    """Test read_payload() with empty stdin, invalid JSON, and valid JSON."""

    def test_empty_stdin_returns_empty_dict(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO(""))
        assert read_payload() == {}

    def test_invalid_json_returns_empty_dict(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
        assert read_payload() == {}

    def test_valid_json_returns_dict(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"cwd": "/tmp", "session_id": "s1"}'))
        assert read_payload() == {"cwd": "/tmp", "session_id": "s1"}


class TestHandleStop:
    """Test handle_stop with mock payloads and real transcript/store."""

    def test_stop_hook_active_returns_zero_without_extraction(
        self, tmp_path, tmp_cortex_home, sample_config, monkeypatch
    ):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        payload = {
            "cwd": str(tmp_path),
            "transcript_path": str(tmp_path / "transcript.jsonl"),
            "session_id": "s1",
            "stop_hook_active": True,
        }
        assert handle_stop(payload) == 0
        project_hash = get_project_hash(str(tmp_path))
        store = EventStore(project_hash, sample_config)
        assert store.count() == 0

    def test_stop_extracts_events_and_updates_state(
        self, tmp_path, tmp_cortex_home, sample_config, fixtures_dir, monkeypatch
    ):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        transcript_src = fixtures_dir / "transcript_simple.jsonl"
        transcript_path = tmp_path / "transcript.jsonl"
        transcript_path.write_text(transcript_src.read_text())

        payload = {
            "cwd": str(tmp_path),
            "transcript_path": str(transcript_path),
            "session_id": "session-001",
            "stop_hook_active": False,
        }
        assert handle_stop(payload) == 0

        project_hash = get_project_hash(str(tmp_path))
        store = EventStore(project_hash, sample_config)
        state = HookState(project_hash, sample_config)
        assert store.count() > 0
        loaded = state.load()
        assert loaded["last_transcript_position"] > 0
        assert loaded["last_transcript_path"] == str(transcript_path)
        assert loaded["last_session_id"] == "session-001"

    def test_stop_missing_cwd_returns_zero(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        assert handle_stop({}) == 0
        assert handle_stop({"transcript_path": "/tmp/t.jsonl"}) == 0

    def test_stop_missing_transcript_path_returns_zero(self, tmp_path, sample_config, monkeypatch):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        payload = {"cwd": str(tmp_path), "session_id": "s1"}
        assert handle_stop(payload) == 0


class TestHandlePrecompact:
    """Test handle_precompact: optional extraction then write briefing."""

    def test_precompact_writes_briefing_with_events(
        self, tmp_path, tmp_cortex_home, tmp_git_repo, sample_config, sample_events, monkeypatch
    ):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        project_hash = get_project_hash(str(tmp_git_repo))
        store = EventStore(project_hash, sample_config)
        store.append_many(sample_events[:2])

        payload = {"cwd": str(tmp_git_repo)}
        assert handle_precompact(payload) == 0

        briefing_path = tmp_git_repo / ".claude" / "rules" / "cortex-briefing.md"
        assert briefing_path.exists()
        content = briefing_path.read_text()
        assert "Decisions" in content or "Recent" in content or "Plan" in content

    def test_precompact_missing_cwd_returns_zero(self):
        assert handle_precompact({}) == 0

    def test_precompact_creates_briefing_dir(self, tmp_git_repo, tmp_cortex_home, sample_config, monkeypatch):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        payload = {"cwd": str(tmp_git_repo)}
        assert handle_precompact(payload) == 0
        assert (tmp_git_repo / ".claude" / "rules").is_dir()


class TestHandleSessionStart:
    """Test handle_session_start: generate and write briefing."""

    def test_session_start_writes_briefing(
        self, tmp_path, tmp_cortex_home, tmp_git_repo, sample_config, sample_events, monkeypatch
    ):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        project_hash = get_project_hash(str(tmp_git_repo))
        store = EventStore(project_hash, sample_config)
        store.append_many(sample_events[:2])

        payload = {"cwd": str(tmp_git_repo)}
        assert handle_session_start(payload) == 0

        briefing_path = tmp_git_repo / ".claude" / "rules" / "cortex-briefing.md"
        assert briefing_path.exists()
        content = briefing_path.read_text()
        assert "Decisions" in content or "Recent" in content or "Plan" in content

    def test_session_start_missing_cwd_returns_zero(self):
        assert handle_session_start({}) == 0

    def test_session_start_creates_briefing_file_when_no_events(
        self, tmp_path, tmp_cortex_home, sample_config, monkeypatch
    ):
        monkeypatch.setattr(
            "memory_context_claude_ai.hooks.load_config",
            lambda: sample_config,
        )
        payload = {"cwd": str(tmp_path)}
        assert handle_session_start(payload) == 0
        briefing_path = tmp_path / ".claude" / "rules" / "cortex-briefing.md"
        assert briefing_path.exists()
