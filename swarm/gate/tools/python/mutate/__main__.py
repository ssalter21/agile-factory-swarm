"""Command line for the mutation runner. See mutate/__init__.py for what it does and why."""

import argparse
import os
import sys
from pathlib import Path

# Running a directory puts that directory on sys.path, not its parent, so absolute imports of
# the package need a hand. This keeps `python path/to/mutate` and `python -m mutate` identical.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mutate.config import load_gate  # noqa: E402
from mutate.manifest import Manifest  # noqa: E402
from mutate.mutants import collect, site_count  # noqa: E402
from mutate.runner import mutate_file, note, python_files, Suite  # noqa: E402
from mutate.units import test_state  # noqa: E402

CLEAN = 0
SURVIVORS = 1
OVER_CAP = 2
UNTRUSTWORTHY = 3


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="mutate", description="Mutation testing, gate step 4.")
    parser.add_argument("paths", nargs="+", help="files or directories to mutate")
    parser.add_argument("--root", default=".", help="project root (default: the cwd)")
    parser.add_argument("--tests", default=["tests"], nargs="+", help="test tree, for the manifest")
    parser.add_argument("--test-command", help="overrides steps.tests from .swarm/gate.yaml")
    parser.add_argument("--shell", help="overrides shell from .swarm/gate.yaml")
    parser.add_argument("--manifest", default=".swarm/mutation.json")
    parser.add_argument("--all", action="store_true", help="ignore the manifest, run every mutant")
    parser.add_argument("--verbose", action="store_true", help="one line per mutant")
    parser.add_argument("--list", action="store_true", help="count sites, run nothing")
    parser.add_argument("--max-sites", type=int, help="site cap per file; 0 disables the check")
    return parser.parse_args(argv)


def run_list(targets, root, max_sites):
    breached = False
    for path in targets:
        mutants = collect(path.read_text(encoding="utf-8"))
        sites = site_count(mutants)
        over = bool(max_sites) and sites > max_sites
        breached = breached or over
        tail = " OVER THE CAP OF %d" % max_sites if over else ""
        print(
            "%s: %d sites, %d mutants%s"
            % (path.relative_to(root).as_posix(), sites, len(mutants), tail)
        )
    return OVER_CAP if breached else CLEAN


def report(survivors, ran, cached, breaches):
    print("\nmutate: %d survivors, %d mutants run, %d cached" % (len(survivors), ran, cached))
    for relative, mutant in survivors:
        print("  SURVIVOR %s %s" % (relative, mutant.label))
    if breaches:
        for relative, count in sorted(breaches.items()):
            print("  OVER CAP %s %d sites" % (relative, count))
        return OVER_CAP
    return SURVIVORS if survivors else CLEAN


def main(argv=None):
    options = parse_args(argv)
    root = Path(options.root).resolve()
    gate = load_gate(root / ".swarm" / "gate.yaml")
    if options.max_sites is None:
        options.max_sites = gate.max_sites

    targets = python_files(root, options.paths)
    if not targets:
        note("mutate: nothing to mutate in %s" % " ".join(options.paths))
        return UNTRUSTWORTHY
    if options.list:
        return run_list(targets, root, options.max_sites)

    command = options.test_command or gate.command
    if not command:
        note("mutate: no test command. Pass --test-command or declare steps.tests in gate.yaml.")
        return UNTRUSTWORTHY
    suite = Suite(command, options.shell or gate.shell, root)

    manifest = Manifest(root / options.manifest, test_state(root, options.tests))
    if manifest.state != "same" and not options.all:
        note("mutate: the test suite is %s since the last run" % manifest.state)

    survivors = []
    ran = 0
    cached = 0
    for path in targets:
        outcome = mutate_file(path, root, suite, manifest, options)
        manifest.save()
        if outcome is None:
            return UNTRUSTWORTHY
        found, file_ran, file_cached = outcome
        relative = path.relative_to(root).as_posix()
        survivors.extend((relative, mutant) for mutant in found)
        ran += file_ran
        cached += file_cached
    return report(survivors, ran, cached, manifest.breaches)


if __name__ == "__main__":
    sys.exit(main())
