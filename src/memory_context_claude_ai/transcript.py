"""Incremental JSONL transcript parser for Claude Code sessions.

Reads Claude Code's transcript files from ~/.claude/projects/<encoded-path>/
and provides structured access to conversation entries. Supports incremental
parsing via byte-offset tracking so the Stop hook only processes new content.

The JSONL format was discovered by inspecting real Claude Code v2.0.76
transcripts. Key differences from the Anthropic API message format:
- Each line is a rich envelope with metadata (parentUuid, sessionId, etc.)
- Messages are nested under a "message" key, not at the top level
- Assistant responses stream as multiple JSONL lines per API request
- Additional record types: "summary" and "file-history-snapshot"
- Tool results arrive as "user" type entries, not "human"
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# WHAT: Top-level record types in Claude Code JSONL transcripts.
# WHY: Not all records are conversation messages. summary and
# file-history-snapshot are metadata records that we parse but
# treat differently from user/assistant messages.
RECORD_TYPE_USER = "user"
RECORD_TYPE_ASSISTANT = "assistant"
RECORD_TYPE_SUMMARY = "summary"
RECORD_TYPE_FILE_SNAPSHOT = "file-history-snapshot"

# WHAT: Content block types found inside assistant messages.
# WHY: Each content block type carries different information:
# text = visible output, thinking = reasoning, tool_use = actions.
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_THINKING = "thinking"
CONTENT_TYPE_TOOL_USE = "tool_use"
CONTENT_TYPE_TOOL_RESULT = "tool_result"

# WHAT: Regex to match fenced code blocks (``` or ~~~).
# WHY: When scanning for keywords, we need to ignore code blocks
# because they contain irrelevant variable names and syntax.
_CODE_BLOCK_RE = re.compile(
    r"```[\s\S]*?```|~~~[\s\S]*?~~~",
    re.MULTILINE,
)

# WHAT: Regex to match inline code spans (`...`).
# WHY: Inline code also causes false keyword matches.
_INLINE_CODE_RE = re.compile(r"`[^`]+`")


@dataclass
class ToolCall:
    """A tool invocation extracted from an assistant message.

    Attributes:
        tool_id: The unique ID for this tool call (e.g., "toolu_abc123").
        name: The tool name (e.g., "Bash", "Read", "Write", "Edit", "Task").
        input: The input arguments passed to the tool.
    """

    tool_id: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)


@dataclass
class ToolResult:
    """A tool result extracted from a user message.

    Attributes:
        tool_use_id: The ID of the tool call this result responds to.
        content: The result content (string or list of content blocks).
        is_error: Whether the tool execution failed.
        metadata: Extra metadata from the toolUseResult envelope.
    """

    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class TranscriptEntry:
    """One parsed JSONL line from a Claude Code transcript.

    Represents a single record which can be a user message, assistant
    message, summary, or file-history-snapshot. All fields use defensive
    defaults so malformed records never crash the parser.

    Attributes:
        record_type: One of "user", "assistant", "summary", "file-history-snapshot".
        uuid: Unique ID for this entry.
        parent_uuid: UUID of the parent entry (for tree structure).
        session_id: Session UUID grouping entries.
        timestamp: ISO 8601 timestamp string.
        request_id: API request ID (groups streamed assistant chunks).
        is_sidechain: Whether this is from an agent sub-conversation.
        git_branch: Current git branch when this entry was created.
        cwd: Working directory path.
        role: Message role ("user" or "assistant"), empty for non-message records.
        content_blocks: Raw content blocks from the message.
        summary_text: For summary records, the summary text.
        raw: The original parsed JSON dict (for anything not explicitly modeled).
    """

    record_type: str = ""
    uuid: str = ""
    parent_uuid: str = ""
    session_id: str = ""
    timestamp: str = ""
    request_id: str = ""
    is_sidechain: bool = False
    git_branch: str = ""
    cwd: str = ""
    role: str = ""
    content_blocks: list = field(default_factory=list)
    summary_text: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def is_user(self) -> bool:
        """True if this is a user-type record (human input or tool result)."""
        return self.record_type == RECORD_TYPE_USER

    @property
    def is_assistant(self) -> bool:
        """True if this is an assistant-type record."""
        return self.record_type == RECORD_TYPE_ASSISTANT

    @property
    def is_summary(self) -> bool:
        """True if this is a summary record from compaction."""
        return self.record_type == RECORD_TYPE_SUMMARY

    @property
    def is_file_snapshot(self) -> bool:
        """True if this is a file-history-snapshot record."""
        return self.record_type == RECORD_TYPE_FILE_SNAPSHOT

    @property
    def is_message(self) -> bool:
        """True if this is a user or assistant message (not metadata)."""
        return self.record_type in (RECORD_TYPE_USER, RECORD_TYPE_ASSISTANT)

    @property
    def has_tool_use(self) -> bool:
        """True if any content block is a tool_use."""
        return any(isinstance(b, dict) and b.get("type") == CONTENT_TYPE_TOOL_USE for b in self.content_blocks)

    @property
    def has_tool_result(self) -> bool:
        """True if any content block is a tool_result."""
        return any(isinstance(b, dict) and b.get("type") == CONTENT_TYPE_TOOL_RESULT for b in self.content_blocks)

    @property
    def has_thinking(self) -> bool:
        """True if any content block is a thinking block."""
        return any(isinstance(b, dict) and b.get("type") == CONTENT_TYPE_THINKING for b in self.content_blocks)


def parse_entry(raw: dict) -> TranscriptEntry:
    """Parse a single JSONL-decoded dict into a TranscriptEntry.

    Handles all known record types defensively. Unknown types are
    stored with record_type set to the raw type value.

    Args:
        raw: A dictionary decoded from one JSONL line.

    Returns:
        A populated TranscriptEntry.
    """
    record_type = raw.get("type", "")
    entry = TranscriptEntry(record_type=record_type, raw=raw)

    if record_type == RECORD_TYPE_SUMMARY:
        entry.summary_text = raw.get("summary", "")
        entry.uuid = raw.get("leafUuid", "")
        return entry

    if record_type == RECORD_TYPE_FILE_SNAPSHOT:
        entry.uuid = raw.get("messageId", "")
        return entry

    # User and assistant messages share the same envelope structure
    if record_type in (RECORD_TYPE_USER, RECORD_TYPE_ASSISTANT):
        entry.uuid = raw.get("uuid", "")
        entry.parent_uuid = raw.get("parentUuid") or ""
        entry.session_id = raw.get("sessionId", "")
        entry.timestamp = raw.get("timestamp", "")
        entry.request_id = raw.get("requestId", "")
        entry.is_sidechain = raw.get("isSidechain", False)
        entry.git_branch = raw.get("gitBranch", "")
        entry.cwd = raw.get("cwd", "")

        message = raw.get("message", {})
        entry.role = message.get("role", "")

        # WHAT: Normalize content to always be a list of blocks.
        # WHY: User messages have content as a plain string for human
        # input but as an array for tool results. Normalizing simplifies
        # all downstream code.
        content = message.get("content", [])
        if isinstance(content, str):
            entry.content_blocks = [{"type": "text", "text": content}]
        elif isinstance(content, list):
            entry.content_blocks = content
        else:
            entry.content_blocks = []

    return entry


def extract_text_content(entry: TranscriptEntry) -> str:
    """Extract all visible text from a transcript entry.

    Concatenates all "text" type content blocks, skipping thinking
    blocks, tool_use blocks, and tool_result blocks.

    Args:
        entry: A parsed TranscriptEntry.

    Returns:
        The concatenated text content, or empty string if none.
    """
    if entry.is_summary:
        return entry.summary_text

    parts = []
    for block in entry.content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == CONTENT_TYPE_TEXT:
            text = block.get("text", "")
            # WHAT: Skip the "(no content)" placeholder from streamed chunks.
            # WHY: Claude Code emits an initial assistant chunk with
            # content [{"type":"text","text":"(no content)"}] before the
            # real content arrives. This is noise.
            if text and text != "(no content)":
                parts.append(text)

    return "\n".join(parts)


def extract_thinking_content(entry: TranscriptEntry) -> str:
    """Extract extended thinking text from an assistant entry.

    Args:
        entry: A parsed TranscriptEntry (typically assistant type).

    Returns:
        The thinking text, or empty string if none.
    """
    parts = []
    for block in entry.content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == CONTENT_TYPE_THINKING:
            thinking = block.get("thinking", "")
            if thinking:
                parts.append(thinking)
    return "\n".join(parts)


def extract_tool_calls(entry: TranscriptEntry) -> list[ToolCall]:
    """Extract tool invocations from an assistant entry.

    Args:
        entry: A parsed TranscriptEntry (typically assistant type).

    Returns:
        List of ToolCall objects. Empty if no tool calls found.
    """
    calls = []
    for block in entry.content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == CONTENT_TYPE_TOOL_USE:
            calls.append(
                ToolCall(
                    tool_id=block.get("id", ""),
                    name=block.get("name", ""),
                    input=block.get("input", {}),
                )
            )
    return calls


def extract_tool_results(entry: TranscriptEntry) -> list[ToolResult]:
    """Extract tool results from a user entry.

    Tool results are found in two places:
    1. content_blocks with type "tool_result"
    2. The top-level "toolUseResult" field in the raw data

    Args:
        entry: A parsed TranscriptEntry (typically user type).

    Returns:
        List of ToolResult objects. Empty if no tool results found.
    """
    results = []
    tool_use_result_meta = entry.raw.get("toolUseResult", {})

    for block in entry.content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == CONTENT_TYPE_TOOL_RESULT:
            # WHAT: Flatten content to a string.
            # WHY: Tool result content can be a string or array of
            # text blocks. We normalize to a single string.
            raw_content = block.get("content", "")
            if isinstance(raw_content, list):
                text_parts = []
                for part in raw_content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                content_str = "\n".join(text_parts)
            else:
                content_str = str(raw_content)

            results.append(
                ToolResult(
                    tool_use_id=block.get("tool_use_id", ""),
                    content=content_str,
                    is_error=block.get("is_error", False),
                    metadata=tool_use_result_meta if tool_use_result_meta else {},
                )
            )

    return results


def strip_code_blocks(text: str) -> str:
    """Remove code blocks and inline code from text.

    Used before keyword matching to avoid false positives from
    code examples, variable names, and syntax in code blocks.

    Removes:
    - Fenced code blocks (``` ... ``` and ~~~ ... ~~~)
    - Inline code spans (` ... `)

    Args:
        text: The text to strip code from.

    Returns:
        Text with all code blocks and inline code removed.
    """
    if not text:
        return ""
    # WHAT: Remove fenced blocks first (they may contain backticks).
    # WHY: Order matters — removing inline first would break fenced detection.
    result = _CODE_BLOCK_RE.sub("", text)
    result = _INLINE_CODE_RE.sub("", result)
    return result


class TranscriptReader:
    """Incremental JSONL transcript reader with byte-offset tracking.

    Reads a Claude Code transcript file line-by-line, parsing each
    JSONL line into a TranscriptEntry. Tracks the byte offset after
    the last read so subsequent calls only process new content.

    This is the core mechanism for the Stop hook: when a session ends,
    the hook reads only the new transcript content since the last
    extraction, processes it, and saves the new offset.

    Usage:
        reader = TranscriptReader(Path("transcript.jsonl"))

        # First read: processes everything from start
        entries = reader.read_new(from_offset=0)

        # Save reader.last_offset to HookState

        # Later: read only new content
        entries = reader.read_new(from_offset=saved_offset)
    """

    def __init__(self, path: Path):
        """Initialize with the path to a JSONL transcript file.

        Args:
            path: Path to the .jsonl file. Does not need to exist yet.
        """
        self._path = path
        self._last_offset: int = 0

    @property
    def path(self) -> Path:
        """The path to the transcript file."""
        return self._path

    @property
    def last_offset(self) -> int:
        """Byte offset after the last successful read."""
        return self._last_offset

    def read_new(self, from_offset: int = 0) -> list[TranscriptEntry]:
        """Read and parse new JSONL entries from the given byte offset.

        Seeks to from_offset and reads all complete lines after that
        point. Malformed lines are silently skipped (defensive parsing).

        Args:
            from_offset: Byte offset to start reading from. Pass 0 to
                        read the entire file, or pass a previously
                        saved offset for incremental reads.

        Returns:
            List of parsed TranscriptEntry objects (new entries only).
            Returns empty list if file doesn't exist or offset is past EOF.
        """
        if not self._path.exists():
            return []

        entries = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                f.seek(from_offset)
                while True:
                    line = f.readline()
                    if not line:
                        break

                    stripped = line.strip()
                    if not stripped:
                        continue

                    try:
                        raw = json.loads(stripped)
                        if isinstance(raw, dict):
                            entries.append(parse_entry(raw))
                    except json.JSONDecodeError:
                        # WHAT: Skip malformed lines silently.
                        # WHY: Transcript files may have partial writes
                        # if Claude Code was interrupted. The parser must
                        # be resilient to garbage data.
                        continue

                self._last_offset = f.tell()
        except OSError:
            # WHAT: Return empty on file errors.
            # WHY: The file may be deleted, locked, or permissions changed
            # between the exists() check and the open(). Defensive.
            return []

        return entries

    def read_all(self) -> list[TranscriptEntry]:
        """Read all entries from the transcript file.

        Convenience method equivalent to read_new(from_offset=0).

        Returns:
            List of all parsed TranscriptEntry objects.
        """
        return self.read_new(from_offset=0)


def find_transcript_path(project_cwd: str) -> Path | None:
    """Find the Claude Code transcript directory for a project.

    Claude Code stores transcripts in:
    ~/.claude/projects/<encoded-path>/

    Where <encoded-path> replaces "/" with "-" in the absolute
    project path. For example:
    /Users/james/Projects/myapp -> -Users-james-Projects-myapp

    Args:
        project_cwd: The absolute path to the project working directory.

    Returns:
        Path to the transcript directory, or None if it doesn't exist.
    """
    encoded = project_cwd.replace("/", "-")
    claude_projects = Path.home() / ".claude" / "projects" / encoded
    if claude_projects.exists():
        return claude_projects
    return None


def find_latest_transcript(transcript_dir: Path) -> Path | None:
    """Find the most recently modified main session transcript.

    Main session transcripts are UUID-named .jsonl files (not
    prefixed with "agent-"). Agent transcripts are sub-conversations
    spawned by the Task tool.

    Args:
        transcript_dir: Path to a project's transcript directory.

    Returns:
        Path to the most recent .jsonl file, or None if none found.
    """
    if not transcript_dir.exists():
        return None

    # WHAT: Filter for UUID-pattern JSONL files (main sessions).
    # WHY: Agent files (agent-*.jsonl) are sub-conversations that
    # are already represented in the main session via tool results.
    # Parsing them separately would create duplicates.
    candidates = []
    for f in transcript_dir.glob("*.jsonl"):
        if not f.name.startswith("agent-"):
            candidates.append(f)

    if not candidates:
        return None

    # WHAT: Sort by modification time, most recent first.
    # WHY: The most recently modified file is likely the active session.
    candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return candidates[0]
