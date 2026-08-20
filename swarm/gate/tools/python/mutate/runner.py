"""Running the suite against one mutant at a time, and putting the file back afterwards."""

import ast
import os
import shlex
import shutil
import subprocess
import sys
import time

from mutate.config import unquote
from mutate.mutants import build, collect, site_count
from mutate.units import unit_hashes

SHELL_SYNTAX = ";|&<>$`(){}"


class Suite:
    """Runs the project's test command and answers one question: did it pass?"""

    def __init__(self, command, shell, root):
        self.root = root
        # Timestamp-based .pyc invalidation records whole seconds and the source size, so two
        # mutants written in the same second at the same size would reuse each other's bytecode
        # and the second would be scored from the first one's run. Write none at all.
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.argv = self.resolve(self.command_argv(command, shell), root)

    @staticmethod
    def resolve(argv, root):
        """Make a relative executable absolute.

        `cwd=` moves the child's working directory but not the search for the executable itself,
        which is resolved against ours. A gate.yaml that says `.venv/Scripts/pytest.exe` means
        the one in the project, so find it there.
        """
        candidate = root / argv[0]
        if not os.path.isabs(argv[0]) and candidate.is_file():
            return [str(candidate)] + argv[1:]
        return argv

    @staticmethod
    def command_argv(command, shell):
        # Spawning a shell per mutant can cost more than the mutant does. Skip it when the
        # command is a plain argv with no shell syntax in it.
        if not any(char in command for char in SHELL_SYNTAX):
            posix = os.name != "nt"
            parts = shlex.split(command, posix=posix)
            if not posix:
                parts = [unquote(part) for part in parts]
            if parts:
                return parts
        if shell in ("pwsh", "powershell", "powershell.exe"):
            return [shell, "-NoProfile", "-NonInteractive", "-Command", command]
        if shell in ("cmd", "cmd.exe"):
            return ["cmd.exe", "/c", command]
        return [shell or "sh", "-c", command]

    def passes(self):
        done = subprocess.run(
            self.argv, cwd=str(self.root), capture_output=True, text=True, env=self.env
        )
        return done.returncode == 0


def python_files(root, entries):
    out = []
    for entry in entries:
        target = (root / entry).resolve()
        found = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for path in found:
            if path.is_file() and "__pycache__" not in path.parts:
                out.append(path)
    return out


def backup(root, path, data):
    """Keep the original outside the file while it is mutated, in case the run is killed."""
    folder = root / ".scratch" / "mutate-backup"
    folder.mkdir(parents=True, exist_ok=True)
    copy_path = folder / path.relative_to(root).as_posix().replace("/", "__")
    copy_path.write_bytes(data)
    return copy_path


def note(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def partition(relative, mutants, manifest, hashes, use_cache):
    """Split mutants into the ones still to run and the survivors we already know about."""
    pending = []
    survivors = []
    cached = 0
    for mutant in mutants:
        verdict = manifest.cached(relative, mutant, hashes) if use_cache else None
        if verdict is None:
            pending.append(mutant)
            continue
        cached += 1
        if verdict == "survived":
            survivors.append(mutant)
    return pending, survivors, cached


def mutate_file(path, root, suite, manifest, options):
    """Run one file. Returns (survivors, ran, cached), or None when the result is untrustworthy."""
    relative = path.relative_to(root).as_posix()
    original_bytes = path.read_bytes()
    source = original_bytes.decode("utf-8")
    mutants = collect(source)
    hashes = unit_hashes(source)
    sites = site_count(mutants)

    if options.max_sites and sites > options.max_sites:
        manifest.breach(relative, sites)
        print(
            "%s: %d sites, over the cap of %d. Split it (constitution section 2). Not mutated."
            % (relative, sites, options.max_sites),
            flush=True,
        )
        return [], 0, 0

    manifest.prune(relative, mutants)
    pending, survivors, cached = partition(relative, mutants, manifest, hashes, not options.all)
    print(
        "%s: %d sites, %d mutants, %d to run, %d cached"
        % (relative, sites, len(mutants), len(pending), cached),
        flush=True,
    )
    if not pending:
        return survivors, 0, cached

    keep = backup(root, path, original_bytes)
    shutil.rmtree(path.parent / "__pycache__", ignore_errors=True)
    started = time.time()
    step = max(1, len(pending) // 4)
    ran = 0
    try:
        # The baseline is the unparsed original, not the original: ast.unparse drops comments
        # and normalises formatting, and a suite that trips over that would score every mutant
        # as noise.
        path.write_text(ast.unparse(ast.parse(source)) + "\n", encoding="utf-8", newline="\n")
        if not suite.passes():
            print(
                "%s: BASELINE FAILS on the unparsed original; results would be noise" % relative,
                flush=True,
            )
            return None
        for mutant in pending:
            changed = build(source, mutant)
            if changed is None:
                continue
            path.write_text(changed, encoding="utf-8", newline="\n")
            alive = suite.passes()
            ran += 1
            manifest.record(relative, mutant, hashes, "survived" if alive else "killed")
            if alive:
                survivors.append(mutant)
            if options.verbose:
                print("  [%s] %s %s" % (mutant.kind, "SURVIVED" if alive else "killed  ", mutant.label))
            elif ran % step == 0:
                note(
                    "  %s %d/%d, %d survivors, %ds"
                    % (relative, ran, len(pending), len(survivors), time.time() - started)
                )
    finally:
        path.write_bytes(original_bytes)
        keep.unlink(missing_ok=True)
    return survivors, ran, cached
