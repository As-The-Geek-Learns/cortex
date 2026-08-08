"""Tests that the Phase 2 test sandbox cannot touch the surrounding repository.

Tests cover:
- TestEnvironment.setup() stays hermetic under each ambient git variable
- the guard in setup() raises, rather than proceeding, if the scrub regresses

WHY these exist: git honours GIT_DIR from the environment even when cwd= points
somewhere else, and git exports GIT_DIR to every hook it runs. Before the scrub in
test_environment.py, running this sandbox from inside a hook would have re-initialised
the CALLING repository and then written to it -- overwriting its identity, staging
files into its index, creating a commit, and renaming its branch to main. Every one of
those git calls returns 0 and is run with capture_output=True, so nothing surfaced.
"""

import hashlib
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
    """Capture every property the unscrubbed git calls would have damaged.

    Includes the object store and the raw index, not just the porcelain output:
    GIT_OBJECT_DIRECTORY and GIT_INDEX_FILE redirect writes at those two files
    specifically, and they do it while `git rev-parse --absolute-git-dir` still
    reports the sandbox. A snapshot built only from config and rev-list would
    show no difference.
    """
    objects_dir = repo / ".git" / "objects"
    index = repo / ".git" / "index"
    return {
        "email": _git(["git", "config", "--get", "user.email"], repo),
        "branch": _git(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo),
        "commits": _git(["git", "rev-list", "--count", "HEAD"], repo),
        "staged": _git(["git", "diff", "--cached", "--name-only"], repo),
        "bare": _git(["git", "config", "--get", "core.bare"], repo),
        "objects": sorted(str(p.relative_to(objects_dir)) for p in objects_dir.rglob("*") if p.is_file()),
        "index": hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None,
    }


def _hostile_value(var: str, repo: Path) -> str:
    """The value of `var` that would point git at `repo` instead of the sandbox."""
    return {
        "GIT_DIR": str(repo / ".git"),
        "GIT_INDEX_FILE": str(repo / ".git" / "index"),
        "GIT_OBJECT_DIRECTORY": str(repo / ".git" / "objects"),
    }[var]


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.parametrize(
    "var",
    ["GIT_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"],
)
def test_sandbox_is_hermetic_under_ambient_git_var(victim_repo, monkeypatch, var):
    """No inherited git variable may redirect the sandbox at another repo.

    Parametrised because the git-dir guard in setup() only catches the GIT_DIR case.
    GIT_INDEX_FILE and GIT_OBJECT_DIRECTORY leave --absolute-git-dir pointing at the
    sandbox, so the guard passes while writes land in the victim -- measured
    2026-08-08: with GIT_OBJECT_DIRECTORY set, three sandbox objects (including the
    file's blob) were written into the victim's object store. For those two the env
    scrub is the ONLY protection, so it needs its own regression coverage.
    """
    before = _snapshot(victim_repo)
    monkeypatch.setenv(var, _hostile_value(var, victim_repo))

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
