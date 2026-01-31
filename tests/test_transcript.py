"""Tests for the transcript parser module.

Covers all public functions and classes in transcript.py:
- parse_entry() for all 4 JSONL record types
- TranscriptEntry properties (is_user, is_assistant, has_tool_use, etc.)
- Extraction helpers (text, thinking, tool_calls, tool_results)
- strip_code_blocks() for fenced and inline code
- TranscriptReader incremental byte-offset reading
- find_transcript_path() and find_latest_transcript() path resolution
"""

import json
import time
from pathlib import Path

import pytest

from memory_context_claude_ai.transcript import (
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_THINKING,
    CONTENT_TYPE_TOOL_RESULT,
    CONTENT_TYPE_TOOL_USE,
    RECORD_TYPE_ASSISTANT,
    RECORD_TYPE_FILE_SNAPSHOT,
    RECORD_TYPE_SUMMARY,
    RECORD_TYPE_USER,
    TranscriptEntry,
    TranscriptReader,
    extract_text_content,
    extract_thinking_content,
    extract_tool_calls,
    extract_tool_results,
    find_latest_transcript,
    find_transcript_path,
    parse_entry,
    strip_code_blocks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the tests/fixtures/ directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_transcript(fixtures_dir: Path) -> Path:
    return fixtures_dir / "transcript_simple.jsonl"


@pytest.fixture
def decisions_transcript(fixtures_dir: Path) -> Path:
    return fixtures_dir / "transcript_decisions.jsonl"


@pytest.fixture
def memory_tags_transcript(fixtures_dir: Path) -> Path:
    return fixtures_dir / "transcript_memory_tags.jsonl"


@pytest.fixture
def mixed_transcript(fixtures_dir: Path) -> Path:
    return fixtures_dir / "transcript_mixed.jsonl"


def _load_entries(path: Path) -> list[TranscriptEntry]:
    """Helper to load all entries from a fixture file."""
    reader = TranscriptReader(path)
    return reader.read_all()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify record type and content type constants match expected values."""

    def test_record_types(self):
        assert RECORD_TYPE_USER == "user"
        assert RECORD_TYPE_ASSISTANT == "assistant"
        assert RECORD_TYPE_SUMMARY == "summary"
        assert RECORD_TYPE_FILE_SNAPSHOT == "file-history-snapshot"

    def test_content_types(self):
        assert CONTENT_TYPE_TEXT == "text"
        assert CONTENT_TYPE_THINKING == "thinking"
        assert CONTENT_TYPE_TOOL_USE == "tool_use"
        assert CONTENT_TYPE_TOOL_RESULT == "tool_result"


# ---------------------------------------------------------------------------
# parse_entry — all record types
# ---------------------------------------------------------------------------


class TestParseEntry:
    """Test parse_entry() for each of the 4 known record types."""

    def test_parse_summary_record(self):
        raw = {
            "type": "summary",
            "summary": "Working on test infrastructure",
            "leafUuid": "leaf-001",
        }
        entry = parse_entry(raw)
        assert entry.record_type == "summary"
        assert entry.summary_text == "Working on test infrastructure"
        assert entry.uuid == "leaf-001"
        assert entry.raw is raw

    def test_parse_file_history_snapshot(self):
        raw = {
            "type": "file-history-snapshot",
            "messageId": "snap-001",
            "snapshot": {"trackedFileBackups": {}},
        }
        entry = parse_entry(raw)
        assert entry.record_type == "file-history-snapshot"
        assert entry.uuid == "snap-001"

    def test_parse_user_message_with_string_content(self):
        raw = {
            "type": "user",
            "uuid": "usr-001",
            "parentUuid": None,
            "sessionId": "session-001",
            "timestamp": "2026-01-30T10:00:00.000Z",
            "isSidechain": False,
            "gitBranch": "main",
            "cwd": "/Users/test/project",
            "message": {
                "role": "user",
                "content": "Help me set up the project",
            },
        }
        entry = parse_entry(raw)
        assert entry.record_type == "user"
        assert entry.uuid == "usr-001"
        assert entry.parent_uuid == ""
        assert entry.session_id == "session-001"
        assert entry.timestamp == "2026-01-30T10:00:00.000Z"
        assert entry.is_sidechain is False
        assert entry.git_branch == "main"
        assert entry.cwd == "/Users/test/project"
        assert entry.role == "user"
        # WHAT: String content gets normalized to a text block list.
        # WHY: Simplifies downstream code — always iterate blocks.
        assert len(entry.content_blocks) == 1
        assert entry.content_blocks[0]["type"] == "text"
        assert entry.content_blocks[0]["text"] == "Help me set up the project"

    def test_parse_user_message_with_tool_result_content(self):
        raw = {
            "type": "user",
            "uuid": "usr-002",
            "sessionId": "session-001",
            "message": {
                "role": "user",
                "content": [
                    {
                        "tool_use_id": "toolu_001",
                        "type": "tool_result",
                        "content": "File created successfully",
                        "is_error": False,
                    }
                ],
            },
        }
        entry = parse_entry(raw)
        assert entry.record_type == "user"
        # Array content stays as-is (no normalization needed)
        assert len(entry.content_blocks) == 1
        assert entry.content_blocks[0]["type"] == "tool_result"

    def test_parse_assistant_with_text(self):
        raw = {
            "type": "assistant",
            "uuid": "ast-001",
            "parentUuid": "usr-001",
            "sessionId": "session-001",
            "requestId": "req-001",
            "isSidechain": False,
            "gitBranch": "main",
            "cwd": "/Users/test/project",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "I'll help you."}],
            },
        }
        entry = parse_entry(raw)
        assert entry.record_type == "assistant"
        assert entry.uuid == "ast-001"
        assert entry.parent_uuid == "usr-001"
        assert entry.request_id == "req-001"
        assert entry.role == "assistant"
        assert len(entry.content_blocks) == 1

    def test_parse_assistant_with_thinking(self):
        raw = {
            "type": "assistant",
            "uuid": "ast-002",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Let me analyze this...",
                        "signature": "sig-001",
                    }
                ],
            },
        }
        entry = parse_entry(raw)
        assert entry.has_thinking is True

    def test_parse_assistant_with_tool_use(self):
        raw = {
            "type": "assistant",
            "uuid": "ast-003",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_001",
                        "name": "Bash",
                        "input": {"command": "ls -la"},
                    }
                ],
            },
        }
        entry = parse_entry(raw)
        assert entry.has_tool_use is True

    def test_parse_unknown_type_does_not_crash(self):
        raw = {"type": "unknown_type", "data": "foo"}
        entry = parse_entry(raw)
        assert entry.record_type == "unknown_type"
        assert entry.raw == raw

    def test_parse_empty_dict(self):
        entry = parse_entry({})
        assert entry.record_type == ""
        assert entry.uuid == ""

    def test_parse_null_parent_uuid_becomes_empty_string(self):
        """parentUuid is null in the first message of a session."""
        raw = {
            "type": "user",
            "uuid": "first-msg",
            "parentUuid": None,
            "message": {"role": "user", "content": "Hello"},
        }
        entry = parse_entry(raw)
        assert entry.parent_uuid == ""

    def test_parse_missing_message_key(self):
        """Defensive: record type user/assistant but no message key."""
        raw = {"type": "user", "uuid": "broken-001"}
        entry = parse_entry(raw)
        assert entry.role == ""
        assert entry.content_blocks == []

    def test_parse_non_dict_non_list_content(self):
        """Defensive: content is an unexpected type (int, etc.)."""
        raw = {
            "type": "assistant",
            "uuid": "ast-bad",
            "message": {"role": "assistant", "content": 42},
        }
        entry = parse_entry(raw)
        assert entry.content_blocks == []

    def test_parse_sidechain_true(self):
        raw = {
            "type": "assistant",
            "uuid": "side-001",
            "isSidechain": True,
            "message": {"role": "assistant", "content": []},
        }
        entry = parse_entry(raw)
        assert entry.is_sidechain is True


# ---------------------------------------------------------------------------
# TranscriptEntry properties
# ---------------------------------------------------------------------------


class TestTranscriptEntryProperties:
    """Test computed properties on TranscriptEntry."""

    def test_is_user(self):
        entry = TranscriptEntry(record_type="user")
        assert entry.is_user is True
        assert entry.is_assistant is False
        assert entry.is_message is True

    def test_is_assistant(self):
        entry = TranscriptEntry(record_type="assistant")
        assert entry.is_assistant is True
        assert entry.is_user is False
        assert entry.is_message is True

    def test_is_summary(self):
        entry = TranscriptEntry(record_type="summary")
        assert entry.is_summary is True
        assert entry.is_message is False

    def test_is_file_snapshot(self):
        entry = TranscriptEntry(record_type="file-history-snapshot")
        assert entry.is_file_snapshot is True
        assert entry.is_message is False

    def test_has_tool_use_true(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "tool_use", "id": "t1", "name": "Bash"}],
        )
        assert entry.has_tool_use is True
        assert entry.has_tool_result is False

    def test_has_tool_use_false_when_only_text(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "Hello"}],
        )
        assert entry.has_tool_use is False

    def test_has_tool_result_true(self):
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[{"type": "tool_result", "content": "ok"}],
        )
        assert entry.has_tool_result is True

    def test_has_thinking_true(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "thinking", "thinking": "hmm..."}],
        )
        assert entry.has_thinking is True

    def test_has_thinking_false_when_text_only(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "answer"}],
        )
        assert entry.has_thinking is False

    def test_properties_with_non_dict_blocks_ignored(self):
        """Non-dict items in content_blocks shouldn't crash properties."""
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=["just a string", 42, None],
        )
        assert entry.has_tool_use is False
        assert entry.has_tool_result is False
        assert entry.has_thinking is False


# ---------------------------------------------------------------------------
# extract_text_content
# ---------------------------------------------------------------------------


class TestExtractTextContent:
    """Test visible text extraction from entries."""

    def test_simple_text(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "Hello world"}],
        )
        assert extract_text_content(entry) == "Hello world"

    def test_multiple_text_blocks(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "text", "text": "First part"},
                {"type": "text", "text": "Second part"},
            ],
        )
        assert extract_text_content(entry) == "First part\nSecond part"

    def test_skips_no_content_placeholder(self):
        """Claude Code emits '(no content)' in initial streamed chunks."""
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "(no content)"}],
        )
        assert extract_text_content(entry) == ""

    def test_skips_thinking_blocks(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "thinking", "thinking": "Let me think..."},
                {"type": "text", "text": "Here's my answer"},
            ],
        )
        assert extract_text_content(entry) == "Here's my answer"

    def test_skips_tool_use_blocks(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "text", "text": "Running command"},
                {"type": "tool_use", "name": "Bash", "input": {}},
            ],
        )
        assert extract_text_content(entry) == "Running command"

    def test_summary_entry_returns_summary_text(self):
        entry = TranscriptEntry(
            record_type="summary",
            summary_text="Working on test infrastructure",
        )
        assert extract_text_content(entry) == "Working on test infrastructure"

    def test_empty_entry(self):
        entry = TranscriptEntry(record_type="assistant", content_blocks=[])
        assert extract_text_content(entry) == ""

    def test_non_dict_blocks_skipped(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=["raw string", {"type": "text", "text": "valid"}],
        )
        assert extract_text_content(entry) == "valid"

    def test_text_block_with_empty_string_skipped(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": ""}],
        )
        assert extract_text_content(entry) == ""


# ---------------------------------------------------------------------------
# extract_thinking_content
# ---------------------------------------------------------------------------


class TestExtractThinkingContent:
    """Test thinking block extraction."""

    def test_single_thinking_block(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "thinking", "thinking": "The user needs SQLite"}
            ],
        )
        assert extract_thinking_content(entry) == "The user needs SQLite"

    def test_multiple_thinking_blocks(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "thinking", "thinking": "First thought"},
                {"type": "text", "text": "visible text"},
                {"type": "thinking", "thinking": "Second thought"},
            ],
        )
        assert extract_thinking_content(entry) == "First thought\nSecond thought"

    def test_no_thinking_blocks(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "no thinking here"}],
        )
        assert extract_thinking_content(entry) == ""

    def test_empty_thinking_text_skipped(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "thinking", "thinking": ""}],
        )
        assert extract_thinking_content(entry) == ""


# ---------------------------------------------------------------------------
# extract_tool_calls
# ---------------------------------------------------------------------------


class TestExtractToolCalls:
    """Test tool call extraction from assistant entries."""

    def test_single_tool_call(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {
                    "type": "tool_use",
                    "id": "toolu_001",
                    "name": "Bash",
                    "input": {"command": "ls -la"},
                }
            ],
        )
        calls = extract_tool_calls(entry)
        assert len(calls) == 1
        assert calls[0].tool_id == "toolu_001"
        assert calls[0].name == "Bash"
        assert calls[0].input == {"command": "ls -la"}

    def test_multiple_tool_calls(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[
                {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/a"}},
                {"type": "text", "text": "reading files"},
                {"type": "tool_use", "id": "t2", "name": "Read", "input": {"file_path": "/b"}},
            ],
        )
        calls = extract_tool_calls(entry)
        assert len(calls) == 2
        assert calls[0].tool_id == "t1"
        assert calls[1].tool_id == "t2"

    def test_no_tool_calls(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "text", "text": "just text"}],
        )
        assert extract_tool_calls(entry) == []

    def test_tool_call_missing_fields_use_defaults(self):
        entry = TranscriptEntry(
            record_type="assistant",
            content_blocks=[{"type": "tool_use"}],
        )
        calls = extract_tool_calls(entry)
        assert len(calls) == 1
        assert calls[0].tool_id == ""
        assert calls[0].name == ""
        assert calls[0].input == {}


# ---------------------------------------------------------------------------
# extract_tool_results
# ---------------------------------------------------------------------------


class TestExtractToolResults:
    """Test tool result extraction from user entries."""

    def test_string_content_result(self):
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_001",
                    "content": "File created successfully",
                    "is_error": False,
                }
            ],
            raw={},
        )
        results = extract_tool_results(entry)
        assert len(results) == 1
        assert results[0].tool_use_id == "toolu_001"
        assert results[0].content == "File created successfully"
        assert results[0].is_error is False

    def test_array_content_result(self):
        """Tool results can have content as array of text blocks."""
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_002",
                    "content": [
                        {"type": "text", "text": "Found 2 test files."},
                        {"type": "text", "text": "agentId: agent-001"},
                    ],
                }
            ],
            raw={},
        )
        results = extract_tool_results(entry)
        assert len(results) == 1
        assert results[0].content == "Found 2 test files.\nagentId: agent-001"

    def test_error_result(self):
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_003",
                    "content": "Permission denied",
                    "is_error": True,
                }
            ],
            raw={},
        )
        results = extract_tool_results(entry)
        assert results[0].is_error is True

    def test_metadata_from_tool_use_result(self):
        """toolUseResult field in raw data provides extra metadata."""
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_004",
                    "content": "output here",
                }
            ],
            raw={
                "toolUseResult": {
                    "stdout": "output here",
                    "stderr": "",
                    "interrupted": False,
                }
            },
        )
        results = extract_tool_results(entry)
        assert results[0].metadata["stdout"] == "output here"
        assert results[0].metadata["interrupted"] is False

    def test_no_tool_results(self):
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[{"type": "text", "text": "just a question"}],
            raw={},
        )
        assert extract_tool_results(entry) == []

    def test_missing_fields_use_defaults(self):
        entry = TranscriptEntry(
            record_type="user",
            content_blocks=[{"type": "tool_result"}],
            raw={},
        )
        results = extract_tool_results(entry)
        assert len(results) == 1
        assert results[0].tool_use_id == ""
        assert results[0].content == ""
        assert results[0].is_error is False
        assert results[0].metadata == {}


# ---------------------------------------------------------------------------
# strip_code_blocks
# ---------------------------------------------------------------------------


class TestStripCodeBlocks:
    """Test code block and inline code removal."""

    def test_removes_fenced_code_block(self):
        text = "Before\n```python\ndef foo():\n    pass\n```\nAfter"
        result = strip_code_blocks(text)
        assert "def foo" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_tilde_fenced_block(self):
        text = "Start\n~~~\nsome code\n~~~\nEnd"
        result = strip_code_blocks(text)
        assert "some code" not in result
        assert "Start" in result
        assert "End" in result

    def test_removes_inline_code(self):
        text = "Use the `DataPipeline` class for processing"
        result = strip_code_blocks(text)
        assert "`DataPipeline`" not in result
        assert "DataPipeline" not in result
        assert "Use the" in result
        assert "class for processing" in result

    def test_removes_both_fenced_and_inline(self):
        text = "Call `foo()` like:\n```\nfoo(bar)\n```\nDone"
        result = strip_code_blocks(text)
        assert "foo" not in result
        assert "Done" in result

    def test_empty_string(self):
        assert strip_code_blocks("") == ""

    def test_no_code_blocks(self):
        text = "Just regular text with no code"
        assert strip_code_blocks(text) == text

    def test_multiple_fenced_blocks(self):
        text = "A\n```\nblock1\n```\nB\n```\nblock2\n```\nC"
        result = strip_code_blocks(text)
        assert "block1" not in result
        assert "block2" not in result
        assert "A" in result
        assert "B" in result
        assert "C" in result

    def test_preserves_text_between_backticks_if_not_code(self):
        """Single backtick (not a pair) should not be treated as code."""
        text = "The value is 5` and increasing"
        result = strip_code_blocks(text)
        # Single backtick — no match, text preserved
        assert "5`" in result


# ---------------------------------------------------------------------------
# TranscriptReader — basic operations
# ---------------------------------------------------------------------------


class TestTranscriptReader:
    """Test the incremental JSONL reader."""

    def test_read_all_simple(self, simple_transcript: Path):
        reader = TranscriptReader(simple_transcript)
        entries = reader.read_all()
        # transcript_simple.jsonl has 7 non-empty lines
        assert len(entries) == 7

    def test_read_all_returns_correct_types(self, simple_transcript: Path):
        entries = _load_entries(simple_transcript)
        types = [e.record_type for e in entries]
        assert types[0] == "summary"
        assert types[1] == "file-history-snapshot"
        assert types[2] == "user"
        assert types[3] == "assistant"
        assert types[4] == "assistant"
        assert types[5] == "user"
        assert types[6] == "assistant"

    def test_read_new_from_zero_same_as_read_all(self, simple_transcript: Path):
        reader = TranscriptReader(simple_transcript)
        all_entries = reader.read_all()
        reader2 = TranscriptReader(simple_transcript)
        new_entries = reader2.read_new(from_offset=0)
        assert len(all_entries) == len(new_entries)

    def test_incremental_read(self, simple_transcript: Path):
        reader = TranscriptReader(simple_transcript)

        # First read: get all entries
        first_batch = reader.read_new(from_offset=0)
        offset_after_first = reader.last_offset
        assert len(first_batch) > 0
        assert offset_after_first > 0

        # Second read from saved offset: no new content
        second_batch = reader.read_new(from_offset=offset_after_first)
        assert len(second_batch) == 0

    def test_incremental_read_with_appended_content(self, tmp_path: Path):
        """Simulate a growing transcript file."""
        transcript = tmp_path / "growing.jsonl"

        # Write initial content
        line1 = json.dumps({"type": "summary", "summary": "Start", "leafUuid": "l1"})
        transcript.write_text(line1 + "\n")

        reader = TranscriptReader(transcript)
        batch1 = reader.read_new(from_offset=0)
        assert len(batch1) == 1
        offset1 = reader.last_offset

        # Append more content
        line2 = json.dumps({
            "type": "user",
            "uuid": "u1",
            "message": {"role": "user", "content": "Hello"},
        })
        with open(transcript, "a") as f:
            f.write(line2 + "\n")

        # Read only new content
        batch2 = reader.read_new(from_offset=offset1)
        assert len(batch2) == 1
        assert batch2[0].record_type == "user"

    def test_read_nonexistent_file(self, tmp_path: Path):
        reader = TranscriptReader(tmp_path / "nonexistent.jsonl")
        entries = reader.read_all()
        assert entries == []

    def test_read_empty_file(self, tmp_path: Path):
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        reader = TranscriptReader(empty)
        entries = reader.read_all()
        assert entries == []

    def test_read_malformed_lines_skipped(self, tmp_path: Path):
        """Malformed JSON lines should be silently skipped."""
        transcript = tmp_path / "malformed.jsonl"
        lines = [
            '{"type": "summary", "summary": "ok", "leafUuid": "l1"}',
            "this is not json {{{",
            "",
            '{"type": "user", "uuid": "u1", "message": {"role": "user", "content": "hi"}}',
        ]
        transcript.write_text("\n".join(lines) + "\n")

        reader = TranscriptReader(transcript)
        entries = reader.read_all()
        # Should get 2 valid entries, skipping the malformed line
        assert len(entries) == 2

    def test_read_non_dict_json_skipped(self, tmp_path: Path):
        """JSON arrays or primitives at top level should be skipped."""
        transcript = tmp_path / "arrays.jsonl"
        lines = [
            '[1, 2, 3]',
            '"just a string"',
            '42',
            '{"type": "summary", "summary": "valid", "leafUuid": "l1"}',
        ]
        transcript.write_text("\n".join(lines) + "\n")

        reader = TranscriptReader(transcript)
        entries = reader.read_all()
        assert len(entries) == 1

    def test_last_offset_property(self, simple_transcript: Path):
        reader = TranscriptReader(simple_transcript)
        assert reader.last_offset == 0
        reader.read_all()
        assert reader.last_offset > 0

    def test_path_property(self, simple_transcript: Path):
        reader = TranscriptReader(simple_transcript)
        assert reader.path == simple_transcript

    def test_offset_past_eof(self, simple_transcript: Path):
        """Reading from offset past EOF should return empty."""
        reader = TranscriptReader(simple_transcript)
        entries = reader.read_new(from_offset=999_999_999)
        assert entries == []


# ---------------------------------------------------------------------------
# TranscriptReader — fixture integration tests
# ---------------------------------------------------------------------------


class TestReaderDecisionsFixture:
    """Integration tests using transcript_decisions.jsonl."""

    def test_entry_count(self, decisions_transcript: Path):
        entries = _load_entries(decisions_transcript)
        assert len(entries) == 5

    def test_thinking_block_present(self, decisions_transcript: Path):
        entries = _load_entries(decisions_transcript)
        # Entry at index 1 is assistant with thinking
        thinking_entries = [e for e in entries if e.has_thinking]
        assert len(thinking_entries) == 1
        thinking_text = extract_thinking_content(thinking_entries[0])
        assert "SQLite" in thinking_text

    def test_decision_text_extractable(self, decisions_transcript: Path):
        entries = _load_entries(decisions_transcript)
        # Entry at index 2 is assistant with decision text
        text = extract_text_content(entries[2])
        assert "Decision: Use SQLite" in text
        assert "Rejected: PostgreSQL" in text

    def test_git_branch(self, decisions_transcript: Path):
        entries = _load_entries(decisions_transcript)
        user_entries = [e for e in entries if e.is_user]
        assert user_entries[0].git_branch == "feature/auth"


class TestReaderMemoryTagsFixture:
    """Integration tests using transcript_memory_tags.jsonl."""

    def test_entry_count(self, memory_tags_transcript: Path):
        entries = _load_entries(memory_tags_transcript)
        assert len(entries) == 5

    def test_user_memory_tag(self, memory_tags_transcript: Path):
        entries = _load_entries(memory_tags_transcript)
        user_text = extract_text_content(entries[0])
        assert "[MEMORY:" in user_text

    def test_assistant_memory_tag(self, memory_tags_transcript: Path):
        entries = _load_entries(memory_tags_transcript)
        # Entry 1 is assistant with [MEMORY:] tag
        asst_text = extract_text_content(entries[1])
        assert "[MEMORY:" in asst_text

    def test_write_tool_call(self, memory_tags_transcript: Path):
        entries = _load_entries(memory_tags_transcript)
        # Entry 2 is assistant with Write tool call
        tool_entries = [e for e in entries if e.has_tool_use]
        assert len(tool_entries) == 1
        calls = extract_tool_calls(tool_entries[0])
        assert calls[0].name == "Write"

    def test_write_tool_result_metadata(self, memory_tags_transcript: Path):
        entries = _load_entries(memory_tags_transcript)
        # Entry 3 is user with tool result for Write
        result_entries = [e for e in entries if e.has_tool_result]
        assert len(result_entries) == 1
        results = extract_tool_results(result_entries[0])
        assert results[0].content == "File created successfully at: /Users/test/project/src/pipeline.py"
        # Write tool results have a toolUseResult with type, filePath
        assert results[0].metadata.get("type") == "create"
        assert results[0].metadata.get("filePath") == "/Users/test/project/src/pipeline.py"


class TestReaderMixedFixture:
    """Integration tests using transcript_mixed.jsonl — all record types."""

    def test_entry_count(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        # 15 non-empty lines
        assert len(entries) == 15

    def test_summary_record(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        summaries = [e for e in entries if e.is_summary]
        assert len(summaries) == 1
        assert "test infrastructure" in summaries[0].summary_text

    def test_file_snapshot_records(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        snapshots = [e for e in entries if e.is_file_snapshot]
        assert len(snapshots) == 2

    def test_thinking_block(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        thinking_entries = [e for e in entries if e.has_thinking]
        assert len(thinking_entries) == 1
        text = extract_thinking_content(thinking_entries[0])
        assert "set up CI" in text

    def test_bash_tool_call(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        # Find the Bash tool call
        tool_entries = [e for e in entries if e.has_tool_use]
        bash_calls = []
        for e in tool_entries:
            for call in extract_tool_calls(e):
                if call.name == "Bash":
                    bash_calls.append(call)
        assert len(bash_calls) == 1
        assert "pytest" in bash_calls[0].input.get("command", "")

    def test_bash_tool_result(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        # Find tool result for the Bash call
        result_entries = [e for e in entries if e.has_tool_result]
        for e in result_entries:
            results = extract_tool_results(e)
            for r in results:
                if r.tool_use_id == "toolu_mix_001":
                    assert "2 passed" in r.content
                    assert r.is_error is False
                    return
        pytest.fail("Bash tool result not found")

    def test_todo_write_tool(self, mixed_transcript: Path):
        entries = _load_entries(mixed_transcript)
        tool_entries = [e for e in entries if e.has_tool_use]
        todo_calls = []
        for e in tool_entries:
            for call in extract_tool_calls(e):
                if call.name == "TodoWrite":
                    todo_calls.append(call)
        assert len(todo_calls) == 1
        assert "todos" in todo_calls[0].input

    def test_task_tool_result_with_array_content(self, mixed_transcript: Path):
        """Task tool results have content as array of text blocks."""
        entries = _load_entries(mixed_transcript)
        result_entries = [e for e in entries if e.has_tool_result]
        for e in result_entries:
            results = extract_tool_results(e)
            for r in results:
                if r.tool_use_id == "toolu_mix_004":
                    # Array content should be flattened
                    assert "Found 2 test files" in r.content
                    assert "agentId" in r.content
                    return
        pytest.fail("Task tool result not found")

    def test_code_block_in_assistant_text(self, mixed_transcript: Path):
        """The mixed fixture has assistant text with an embedded code block."""
        entries = _load_entries(mixed_transcript)
        # Last assistant message (mix-012) has a code block
        last_asst = [e for e in entries if e.is_assistant and not e.has_tool_use]
        # Find the one with code block
        for e in last_asst:
            text = extract_text_content(e)
            if "```python" in text:
                stripped = strip_code_blocks(text)
                assert "def test_empty_file" not in stripped
                assert "pipeline" in stripped.lower() or "edge case" in stripped.lower()
                return
        pytest.fail("No assistant entry with code block found")

    def test_all_session_ids_match(self, mixed_transcript: Path):
        """All messages in the mixed fixture share the same session."""
        entries = _load_entries(mixed_transcript)
        message_entries = [e for e in entries if e.is_message]
        session_ids = {e.session_id for e in message_entries}
        assert session_ids == {"session-mix-001"}


# ---------------------------------------------------------------------------
# find_transcript_path
# ---------------------------------------------------------------------------


class TestFindTranscriptPath:
    """Test project path -> Claude transcript directory resolution."""

    def test_finds_existing_directory(self, tmp_path: Path):
        # Simulate ~/.claude/projects/-Users-test-project/
        claude_dir = tmp_path / ".claude" / "projects" / "-Users-test-project"
        claude_dir.mkdir(parents=True)

        # Monkeypatch Path.home() to use our tmp_path
        import memory_context_claude_ai.transcript as transcript_mod

        original_home = Path.home
        Path.home = staticmethod(lambda: tmp_path)
        try:
            result = find_transcript_path("/Users/test/project")
            assert result == claude_dir
        finally:
            Path.home = original_home

    def test_returns_none_for_missing_directory(self, tmp_path: Path):
        import memory_context_claude_ai.transcript as transcript_mod

        original_home = Path.home
        Path.home = staticmethod(lambda: tmp_path)
        try:
            result = find_transcript_path("/nonexistent/path")
            assert result is None
        finally:
            Path.home = original_home

    def test_path_encoding(self):
        """Verify the encoding logic: / becomes -."""
        # WHAT: Test the encoding without filesystem access.
        # WHY: The encoding is a simple string replacement, testable in isolation.
        encoded = "/Users/james/Projects/myapp".replace("/", "-")
        assert encoded == "-Users-james-Projects-myapp"


# ---------------------------------------------------------------------------
# find_latest_transcript
# ---------------------------------------------------------------------------


class TestFindLatestTranscript:
    """Test finding the most recently modified main session transcript."""

    def test_finds_latest_by_mtime(self, tmp_path: Path):
        # Create two transcript files
        old = tmp_path / "aaaa-bbbb-cccc.jsonl"
        new = tmp_path / "dddd-eeee-ffff.jsonl"

        old.write_text('{"type":"summary","summary":"old","leafUuid":"l1"}\n')
        time.sleep(0.05)  # Ensure different mtime
        new.write_text('{"type":"summary","summary":"new","leafUuid":"l2"}\n')

        result = find_latest_transcript(tmp_path)
        assert result == new

    def test_excludes_agent_files(self, tmp_path: Path):
        # Agent files should be filtered out
        agent = tmp_path / "agent-task-001.jsonl"
        main = tmp_path / "aaaa-bbbb-cccc.jsonl"

        main.write_text('{"type":"summary","summary":"main","leafUuid":"l1"}\n')
        time.sleep(0.05)
        agent.write_text('{"type":"summary","summary":"agent","leafUuid":"l2"}\n')

        result = find_latest_transcript(tmp_path)
        # Should return main, not agent (even though agent is newer)
        assert result == main

    def test_returns_none_for_empty_directory(self, tmp_path: Path):
        result = find_latest_transcript(tmp_path)
        assert result is None

    def test_returns_none_for_nonexistent_directory(self, tmp_path: Path):
        result = find_latest_transcript(tmp_path / "nonexistent")
        assert result is None

    def test_returns_none_when_only_agent_files(self, tmp_path: Path):
        agent = tmp_path / "agent-task-001.jsonl"
        agent.write_text('{"type":"summary","summary":"agent","leafUuid":"l1"}\n')
        result = find_latest_transcript(tmp_path)
        assert result is None

    def test_single_file(self, tmp_path: Path):
        only = tmp_path / "single-session.jsonl"
        only.write_text('{"type":"summary","summary":"only","leafUuid":"l1"}\n')
        result = find_latest_transcript(tmp_path)
        assert result == only
