"""CLI commands for Cortex: reset, status, init.

Used by __main__.py. Reset clears event store and hook state for a project.
Status prints project identity and store counts. Init prints hook JSON for
Claude Code settings.
"""

import json
import os
import sys

from cortex.config import load_config
from cortex.project import identify_project
from cortex.store import EventStore, HookState

# Default state keys for clearing HookState (must match HookState.load() defaults).
_RESET_STATE = {
    "last_transcript_position": 0,
    "last_transcript_path": "",
    "last_session_id": "",
    "session_count": 0,
    "last_extraction_time": "",
}


def cmd_reset(cwd: str | None = None) -> int:
    """Clear event store and hook state for the project in cwd.

    Uses os.getcwd() if cwd is None. Prints one-line confirmation to stdout.
    Returns 0 on success, 1 on error (e.g. invalid path).
    """
    try:
        work_dir = (os.getcwd() if cwd is None else cwd).strip()
        if not work_dir:
            print("Cortex reset: no cwd.", file=sys.stderr)
            return 1
        identity = identify_project(work_dir)
        project_hash = identity["hash"]
        config = load_config()
        store = EventStore(project_hash, config)
        state = HookState(project_hash, config)
        store.clear()
        state.save(_RESET_STATE)
        print(f"Cortex memory reset for project {project_hash}.")
        return 0
    except Exception as e:
        print(f"Cortex reset error: {e}", file=sys.stderr)
        return 1


def cmd_status(cwd: str | None = None) -> int:
    """Print project identity, event count, and last extraction time.

    Uses os.getcwd() if cwd is None. Returns 0 on success, 1 on error.
    """
    try:
        work_dir = (os.getcwd() if cwd is None else cwd).strip()
        if not work_dir:
            print("Cortex status: no cwd.", file=sys.stderr)
            return 1
        identity = identify_project(work_dir)
        project_hash = identity["hash"]
        config = load_config()
        store = EventStore(project_hash, config)
        state = HookState(project_hash, config)
        state_data = state.load()
        count = store.count()
        last_extraction = state_data.get("last_extraction_time") or "none"
        print(f"project: {identity['path']}")
        print(f"hash: {project_hash}")
        print(f"events: {count}")
        print(f"last_extraction: {last_extraction}")
        return 0
    except Exception as e:
        print(f"Cortex status error: {e}", file=sys.stderr)
        return 1


def get_init_hook_json() -> str:
    """Return the hook configuration JSON for Claude Code settings.

    Format matches Claude Code expectations: hooks key with Stop, PreCompact,
    SessionStart entries. Commands use 'cortex' so they work when the package
    is installed (cortex on PATH).
    """
    config = {
        "hooks": {
            "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "cortex stop"}]}],
            "PreCompact": [{"matcher": "", "hooks": [{"type": "command", "command": "cortex precompact"}]}],
            "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "cortex session-start"}]}],
        }
    }
    return json.dumps(config, indent=2)


def cmd_init() -> int:
    """Print hook configuration JSON to stdout for copy-paste into Claude Code settings."""
    print(get_init_hook_json())
    return 0
