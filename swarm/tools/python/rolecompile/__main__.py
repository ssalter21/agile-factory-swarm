"""Command line for the role compiler. See rolecompile/__init__.py for what it does and why.

The shell, and nothing else: it parses two arguments, moves bytes through the compile, prints, and
exits. Every rule worth testing lives in a module that needs no process to exercise.
"""

import argparse
import os
import sys

# Running a directory puts that directory on sys.path, not its parent, so absolute imports of
# the package need a hand. This keeps `python path/to/rolecompile` and `python -m rolecompile`
# identical.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rolecompile import compiler, files, report  # noqa: E402
from rolecompile.model import CLAUDE_DIR, GITHUB_DIR  # noqa: E402

DESTINATIONS = (CLAUDE_DIR, GITHUB_DIR)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="rolecompile",
        description="Compile swarm/roles/ into the agent file each harness loads.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare only: write nothing, and exit non-zero if anything is out of date",
    )
    parser.add_argument("--root", default=".", help="project root (default: the cwd)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        problem, targets = compiler.targets(files.read_sources(args.root))
        if problem is not None:
            print(problem, file=sys.stderr)
            return compiler.PROBLEM
        outcome = compiler.outcome(
            targets,
            files.read_targets(args.root, [target.path for target in targets]),
            files.destinations_present(args.root, DESTINATIONS),
            args.check,
        )
        # Empty in check mode, by compiler.outcome. The promise is kept there, once.
        files.write(args.root, outcome.to_write)
        for line in outcome.lines:
            print(line)
        return outcome.code
    except OSError as err:
        print(report.unreadable(err.filename, err.strerror), file=sys.stderr)
        return compiler.PROBLEM


if __name__ == "__main__":
    sys.exit(main())
