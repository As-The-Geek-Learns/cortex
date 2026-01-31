"""CLI entry point for Cortex hook handlers and commands.

Usage:
    cortex stop          # JSON payload on stdin
    cortex precompact    # JSON payload on stdin
    cortex session-start # JSON payload on stdin
    cortex reset         # clear store + state for current project
    cortex status        # show project hash, event count, last extraction
    cortex init          # print hook JSON for Claude Code settings

    python -m memory_context_claude_ai stop   # same
"""

import sys

from memory_context_claude_ai.cli import cmd_init, cmd_reset, cmd_status
from memory_context_claude_ai.hooks import (
    handle_precompact,
    handle_session_start,
    handle_stop,
    read_payload,
)

USAGE = "Usage: cortex <stop|precompact|session-start|reset|status|init>\n"


def main() -> None:
    """Parse command from argv, dispatch to handler or hook, exit with return code."""
    if len(sys.argv) < 2:
        sys.stderr.write(USAGE)
        sys.exit(1)

    arg = sys.argv[1].strip().lower()
    if arg in ("-h", "--help"):
        sys.stderr.write(USAGE)
        sys.exit(0)

    if arg == "reset":
        sys.exit(cmd_reset())
    if arg == "status":
        sys.exit(cmd_status())
    if arg == "init":
        sys.exit(cmd_init())

    # Hook commands: require payload on stdin
    hook_name = arg
    if hook_name == "sessionstart":
        hook_name = "session-start"

    if hook_name == "stop":
        code = handle_stop(read_payload())
    elif hook_name == "precompact":
        code = handle_precompact(read_payload())
    elif hook_name == "session-start":
        code = handle_session_start(read_payload())
    else:
        sys.stderr.write(f"Unknown command: {arg}. {USAGE}")
        sys.exit(1)

    sys.exit(code)
