"""Tests that the Phase 2 test sandbox cannot touch the surrounding repository.

Tests cover:
- TestEnvironment.setup() stays hermetic when an ambient GIT_DIR is present
- the guard in setup() raises, rather than proceeding, if the scrub regresses

WHY these exist: git honours GIT_DIR from the environment even when cwd= points
somewhere else, and git exports GIT_DIR to every hook it runs. Before the scrub in
test_environment.py, running this sandbox from inside a hook would have re-initialised
the CALLING repository and then written to it -- overwriting its identity, staging
files into its index, creating a commit, and renaming its branch to main. Every one of
those git calls returns 0 and is run with capture_output=True, so nothing surfaced.
"""

import os
import subprocess
from pathlib import Path

import pytest

from scripts.testing import test_environment as te

# Aliased: pytest tries to collect any class named Test* and warns that it cannot,
# because this one takes constructor arguments. It is the subject, not a test case.
from scripts.testing.test_environment import TestEnvironment as SandboxEnvironment

# =============================================================================
# Fixtures
# =============================================================================


def _git(args, cwd):
    """Run a git command against `cwd` and return stripped stdout.

    Scrubs the ambient git variables. These tests deliberately set a hostile GIT_DIR,
    and without scrubbing here the probe answers about THAT repo instead of the one
    being asked about -- which reads as a failure of the code under test rather than
    of the question. (It did, once.)
    """
    env = {k: v for k, v in os.environ.items() if k not in te._AMBIENT_GIT_VARS}
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def victim_repo(tmp_path: Path) -> Path:
    """A real git repo that no test is allowed to modify."""
    repo = tmp_path / "victim"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "real@real.com"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "real"], cwd=repo, capture_output=True)
    (repo / "original.txt").write_text("original\n")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "victim initial"], cwd=repo, capture_output=True)
    return repo


def _snapshot(repo: Path) -> dict:
    """Capture every property the unscrubbed git calls would have damaged."""
    return {
        "email": _git(["git", "config", "--get", "user.email"], repo),
        "branch": _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo),
        "commits": _git(["git", "rev-list", "--count", "HEAD"], repo),
        "staged": _git(["git", "diff", "--cached", "--name-only"], repo),
        "bare": _git(["git", "config", "--get", "core.bare"], repo),
    }


# =============================================================================
# Tests
# =============================================================================


def test_sandbox_is_hermetic_under_ambient_git_dir(victim_repo, monkeypatch):
    """An inherited GIT_DIR must not redirect the sandbox at another repo."""
    before = _snapshot(victim_repo)
    monkeypatch.setenv("GIT_DIR", str(victim_repo / ".git"))

    env = SandboxEnvironment()
    env.setup()

    # The sandbox owns its own git dir.
    #
    # Asserting on --absolute-git-dir, not --show-toplevel: with an ambient GIT_DIR
    # and no GIT_WORK_TREE, git treats the cwd as the work tree, so --show-toplevel
    # reports the sandbox even when the object store belongs to another repo. The
    # git dir is the part that cannot lie.
    git_dir = _git(["git", "rev-parse", "--absolute-git-dir"], env.project_dir)
    assert Path(git_dir).resolve() == (env.project_dir / ".git").resolve()
    assert _git(["git", "rev-list", "--count", "HEAD"], env.project_dir) == "1"

    assert _snapshot(victim_repo) == before, "the sandbox modified the surrounding repo"


def test_guard_raises_if_the_scrub_regresses(victim_repo, monkeypatch):
    """If the env scrub is removed, setup() must abort instead of writing elsewhere.

    The scrub is the fix; this guard is what keeps a regression loud. Without it the
    damage is silent, and the calls after the guard commit and rename branches.
    """
    before = _snapshot(victim_repo)
    monkeypatch.setenv("GIT_DIR", str(victim_repo / ".git"))
    monkeypatch.setattr(te, "_hermetic_git_env", lambda: os.environ.copy())

    with pytest.raises(RuntimeError, match="ambient GIT_DIR"):
        SandboxEnvironment().setup()

    assert _snapshot(victim_repo) == before, "aborted too late — the repo was already modified"
