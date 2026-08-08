"""Isolated test environment for Phase 2 automation.

# WHAT: Manages temp directories, git repos, and config isolation.
# WHY: Tests must not pollute the real ~/.cortex/ data. This module
#       creates an ephemeral sandbox with proper git init and
#       config monkeypatching so hooks run against temp storage.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from cortex.config import CortexConfig
from cortex.project import get_project_hash

# WHAT: git environment variables that must never reach the sandbox.
# WHY: git honours GIT_DIR from the environment even when cwd= (or -C) points
#      somewhere else, and git exports GIT_DIR to every hook it runs. Under a
#      hook, `git init` below would not create a repo here -- it would
#      re-initialise the CALLING repository, and every command after it would
#      write to that repo instead: `git config` overwrites its identity,
#      `git add .` stages sandbox files into its index, `git commit` creates a
#      real commit, and `git branch -M main` renames its current branch.
#      Verified 2026-08-08: all of them return 0, so capture_output=True hides
#      the whole thing. A sibling repo lost its shared config to this exact
#      mechanism before it was understood.
_AMBIENT_GIT_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_PREFIX",
    "GIT_NAMESPACE",
)


def _hermetic_git_env() -> dict[str, str]:
    """Return a copy of os.environ with every ambient git pointer removed."""
    env = os.environ.copy()
    for var in _AMBIENT_GIT_VARS:
        env.pop(var, None)
    return env


class TestEnvironment:
    """Isolated test environment with temp directories for Cortex data.

    Creates:
    - A temp project directory with an initialized git repo
    - A temp cortex home directory (simulates ~/.cortex/)
    - A CortexConfig pointing at the temp home
    - Helper methods to run hooks with monkeypatched config
    """

    def __init__(self):
        self._tmpdir = tempfile.mkdtemp(prefix="cortex-phase2-")
        self.project_dir = Path(self._tmpdir) / "cortex-test-project"
        self.cortex_home = Path(self._tmpdir) / ".cortex"
        self.config = CortexConfig(cortex_home=self.cortex_home)

    def setup(self):
        """Initialize directories, git repo, and .claude/rules/ structure."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.cortex_home.mkdir(parents=True, exist_ok=True)
        (self.cortex_home / "projects").mkdir(exist_ok=True)

        # WHAT: Initialize a git repo with an initial commit.
        # WHY: identify_project() calls git rev-parse, which needs a repo.
        #
        # Every call passes env=git_env so no ambient GIT_DIR can redirect it at
        # the calling repository -- see _AMBIENT_GIT_VARS above.
        git_env = _hermetic_git_env()
        subprocess.run(
            ["git", "init"],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )

        # WHAT: Confirm the repo we just made is actually HERE before writing to it.
        # WHY: the scrub above is the fix; this is what makes a regression loud.
        #      Every git call in this method returns 0 while silently operating on
        #      another repository, so without this check the damage is invisible --
        #      and the commands below commit and rename branches.
        #
        # Ask for --absolute-git-dir, NOT --show-toplevel. With an ambient GIT_DIR
        # and no GIT_WORK_TREE, git treats the cwd as the work tree, so
        # --show-toplevel cheerfully reports this sandbox while the object store,
        # index and refs all belong to the other repo. Checked 2026-08-08: a guard
        # written against --show-toplevel passes while a commit lands elsewhere.
        # The git dir is the thing that cannot lie about which repo is being written.
        probe = subprocess.run(
            ["git", "rev-parse", "--absolute-git-dir"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            env=git_env,
        )
        actual = Path(probe.stdout.strip()).resolve() if probe.stdout.strip() else None
        expected = (self.project_dir / ".git").resolve()
        if actual != expected:
            raise RuntimeError(
                f"Sandbox git dir is {actual or '<none>'}, expected {expected}. "
                "An ambient GIT_DIR is leaking in; refusing to run git commands "
                "against another repository."
            )

        subprocess.run(
            ["git", "config", "user.email", "test@cortex.dev"],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )
        subprocess.run(
            ["git", "config", "user.name", "Cortex Test"],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )
        readme = self.project_dir / "README.md"
        readme.write_text("# Cortex Test Project\n")
        subprocess.run(
            ["git", "add", "."],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=self.project_dir,
            capture_output=True,
            env=git_env,
        )

        # WHAT: Create the .claude/rules/ directory for briefing output.
        # WHY: handle_session_start writes cortex-briefing.md here.
        (self.project_dir / ".claude" / "rules").mkdir(parents=True, exist_ok=True)

    def get_project_hash(self) -> str:
        """Get the project hash for the test project directory."""
        return get_project_hash(str(self.project_dir))

    def get_briefing_path(self) -> Path:
        """Return .claude/rules/cortex-briefing.md in the project dir."""
        return self.project_dir / ".claude" / "rules" / "cortex-briefing.md"

    def read_briefing(self) -> str:
        """Read the briefing file content, or empty string if missing."""
        path = self.get_briefing_path()
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def run_stop_hook(self, transcript_path: Path, session_id: str) -> int:
        """Run the Stop hook with monkeypatched config.

        # WHAT: Calls handle_stop() directly with a synthetic payload.
        # WHY: Avoids needing a real Claude Code session. The Stop hook
        #       accepts transcript_path in its payload, so we can point
        #       it at our synthetic JSONL file.
        """
        import cortex.hooks

        original_load = cortex.hooks.load_config
        cortex.hooks.load_config = lambda: self.config
        try:
            payload = {
                "cwd": str(self.project_dir),
                "transcript_path": str(transcript_path),
                "session_id": session_id,
                "stop_hook_active": False,
            }
            return cortex.hooks.handle_stop(payload)
        finally:
            cortex.hooks.load_config = original_load

    def run_session_start_hook(self) -> int:
        """Run the SessionStart hook with monkeypatched config.

        # WHAT: Calls handle_session_start() to generate a briefing.
        # WHY: The SessionStart hook writes cortex-briefing.md, which
        #       is the main output a user would check after extraction.
        """
        import cortex.hooks

        original_load = cortex.hooks.load_config
        cortex.hooks.load_config = lambda: self.config
        try:
            payload = {"cwd": str(self.project_dir)}
            return cortex.hooks.handle_session_start(payload)
        finally:
            cortex.hooks.load_config = original_load

    def get_event_store(self):
        """Get an EventStore for the test project."""
        from cortex.store import EventStore

        return EventStore(self.get_project_hash(), self.config)

    def cleanup(self):
        """Remove all temp directories."""
        shutil.rmtree(self._tmpdir, ignore_errors=True)
