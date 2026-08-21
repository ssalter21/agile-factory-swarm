"""Compiling this repository's own roles reproduces the twelve tracked agent files, byte for byte.

This is the change's own acceptance criterion, run as a test: the twelve files under
`.claude/agents/` were hand-written, they are what the swarm actually loads, and a compiler that
moves a single byte of them has failed. It reads them and writes nothing.

It is not the same property as compiling twice changing nothing. That one holds on every machine;
this one is measured against the bytes in the working tree, which is why `.gitattributes` pins the
line ending for both agent directories.
"""

from pathlib import Path

from rolecompile import compare, compiler, files
from rolecompile.compare import Status
from rolecompile.model import CLAUDE_DIR, GITHUB_DIR

ROOT = Path(__file__).resolve().parents[1]

ROLES = (
    "agile-agent",
    "architect",
    "cleaner",
    "coder",
    "devils-advocate",
    "domain-modeller",
    "hardener",
    "qa",
    "researcher",
    "spec-writer",
    "unblocker",
    "user-voice",
)


def compiled():
    problem, targets = compiler.targets(files.read_sources(ROOT))
    assert problem is None, problem
    return {target.path: target.data for target in targets}


def test_every_role_in_the_repository_compiles_to_two_agent_files():
    assert sorted(compiled()) == sorted(
        ["%s/%s.md" % (CLAUDE_DIR, name) for name in ROLES]
        + ["%s/%s.agent.md" % (GITHUB_DIR, name) for name in ROLES]
    )


def test_the_twelve_tracked_claude_agent_files_are_reproduced_byte_for_byte():
    targets = compiled()
    paths = ["%s/%s.md" % (CLAUDE_DIR, name) for name in ROLES]
    on_disk = files.read_targets(ROOT, paths)
    differing = [
        path for path in paths if compare.status(targets[path], on_disk[path]) is not Status.SAME
    ]
    assert differing == []
