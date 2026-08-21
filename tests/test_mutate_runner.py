"""The parts that run mutants: the test command, the per-file loop, and what it prints.

These press on the details the end-to-end tests in test_mutate.py step over -- exact argv,
exact output, the file being put back, the backup being cleaned up.
"""

import argparse
import json
import sys

import pytest

from mutate.manifest import Manifest
from mutate.mutants import Mutant, collect
from mutate.runner import Suite, backup, mutate_file, note, partition, python_files
from mutate.units import unit_hashes

SOURCE = "def f(a):\n    return a > 1\n"


def options(**overrides):
    values = {"max_sites": 0, "all": False, "verbose": False}
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.fixture
def project(tmp_path):
    """A one-function project and a test command that always passes."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(SOURCE, encoding="utf-8")
    checker = tmp_path / "pass.py"
    checker.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    return tmp_path, Suite("%s %s" % (sys.executable, checker), None, tmp_path)


def failing(root):
    checker = root / "fail.py"
    checker.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    return Suite("%s %s" % (sys.executable, checker), None, root)


# --------------------------------------------------------------------------- the command


def test_a_plain_command_becomes_argv_untouched():
    assert Suite.command_argv("pytest -q tests", "pwsh") == ["pytest", "-q", "tests"]


def test_a_quoted_argument_keeps_its_spaces():
    assert Suite.command_argv('pytest -k "a b"', "pwsh") == ["pytest", "-k", "a b"]


@pytest.mark.parametrize("char", list(";|&<>$`(){}"))
def test_every_shell_character_sends_the_command_to_the_shell(char):
    assert Suite.command_argv("a %s b" % char, "bash")[0] == "bash"


def test_powershell_gets_the_flags_that_keep_it_quiet():
    argv = Suite.command_argv("a; b", "pwsh")
    assert argv == ["pwsh", "-NoProfile", "-NonInteractive", "-Command", "a; b"]


def test_powershell_is_recognised_by_all_three_names():
    for name in ("pwsh", "powershell", "powershell.exe"):
        assert Suite.command_argv("a; b", name)[0] == name


def test_cmd_is_recognised_by_both_names():
    assert Suite.command_argv("a; b", "cmd") == ["cmd.exe", "/c", "a; b"]
    assert Suite.command_argv("a; b", "cmd.exe") == ["cmd.exe", "/c", "a; b"]


def test_any_other_shell_is_given_dash_c():
    assert Suite.command_argv("a; b", "zsh") == ["zsh", "-c", "a; b"]


def test_no_shell_named_falls_back_to_sh():
    assert Suite.command_argv("a; b", None) == ["sh", "-c", "a; b"]


def test_an_empty_command_is_handed_to_the_shell():
    assert Suite.command_argv("", "bash") == ["bash", "-c", ""]


def test_a_relative_executable_is_resolved_against_the_project(tmp_path):
    (tmp_path / "bin").mkdir()
    exe = tmp_path / "bin" / "run.exe"
    exe.write_bytes(b"")
    assert Suite.resolve(["bin/run.exe", "-q"], tmp_path) == [str(exe), "-q"]


def test_a_relative_path_that_is_not_there_is_left_alone(tmp_path):
    assert Suite.resolve(["bin/missing.exe"], tmp_path) == ["bin/missing.exe"]


def test_an_absolute_executable_is_left_alone(tmp_path):
    exe = tmp_path / "run.exe"
    exe.write_bytes(b"")
    assert Suite.resolve([str(exe)], tmp_path) == [str(exe)]


def test_bytecode_writing_is_switched_off(tmp_path):
    suite = Suite("pytest", None, tmp_path)
    assert suite.env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_the_default_timeout_is_two_minutes(tmp_path):
    assert Suite("pytest", None, tmp_path).timeout == 120


def test_the_suite_reports_what_the_command_returned(project):
    root, suite = project
    assert suite.passes() is True
    assert failing(root).passes() is False


def test_a_command_that_never_returns_counts_as_a_failure(tmp_path):
    # A statement-deletion mutant can turn a loop's own terminating condition into one that
    # never changes, so the suite hangs rather than fails. A hang is not a pass: bound it.
    checker = tmp_path / "hang.py"
    checker.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    suite = Suite("%s %s" % (sys.executable, checker), None, tmp_path, timeout=0.2)
    assert suite.passes() is False


# --------------------------------------------------------------------------- finding files


def test_a_directory_is_walked_and_sorted(tmp_path):
    (tmp_path / "pkg").mkdir()
    for name in ("z.py", "a.py", "m.py"):
        (tmp_path / "pkg" / name).write_text("x = 1\n", encoding="utf-8")
    assert [p.name for p in python_files(tmp_path, ["pkg"])] == ["a.py", "m.py", "z.py"]


def test_a_single_file_is_taken_as_given(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    assert [p.name for p in python_files(tmp_path, ["a.py"])] == ["a.py"]


def test_several_paths_are_all_collected(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("x = 1\n", encoding="utf-8")
    assert len(python_files(tmp_path, ["a.py", "b.py"])) == 2


def test_compiled_files_are_not_targets(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__pycache__").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pkg" / "__pycache__" / "a.py").write_text("x = 1\n", encoding="utf-8")
    assert [p.name for p in python_files(tmp_path, ["pkg"])] == ["a.py"]


def test_a_path_that_is_not_there_yields_nothing(tmp_path):
    assert python_files(tmp_path, ["nowhere"]) == []


# --------------------------------------------------------------------------- backup


def test_the_backup_flattens_the_path_and_holds_the_bytes(tmp_path):
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "a.py"
    target.write_text(SOURCE, encoding="utf-8")
    kept = backup(tmp_path, target, b"original")
    assert kept.name == "src__a.py"
    assert kept.parent == tmp_path / ".scratch" / "mutate-backup"
    assert kept.read_bytes() == b"original"


def test_note_writes_one_line_to_stderr(capsys):
    note("hello")
    captured = capsys.readouterr()
    assert captured.err == "hello\n"
    assert captured.out == ""


# --------------------------------------------------------------------------- partition


SUITE_STATE = {"tests/test_a.py::test_f": "abc"}


def manifest_for(tmp_path, verdicts):
    """A manifest saved by an earlier run, holding `verdicts` in mutant order.

    It goes through the file, because a manifest with nothing behind it is in the `changed`
    state by definition and would reuse nothing.
    """
    mutants = collect(SOURCE)
    hashes = unit_hashes(SOURCE)
    earlier = Manifest(tmp_path / "m.json", SUITE_STATE)
    for mutant, verdict in zip(mutants, verdicts):
        earlier.record("src/a.py", mutant, hashes, verdict)
    earlier.save()
    return Manifest(tmp_path / "m.json", SUITE_STATE), mutants, hashes


def test_partition_runs_everything_when_nothing_is_known(tmp_path):
    manifest, mutants, hashes = manifest_for(tmp_path, [])
    pending, survivors, cached = partition("src/a.py", mutants, manifest, hashes, True)
    assert (len(pending), survivors, cached) == (len(mutants), [], 0)


def test_partition_holds_back_what_the_manifest_settled(tmp_path):
    manifest, mutants, hashes = manifest_for(tmp_path, ["killed", "survived"])
    pending, survivors, cached = partition("src/a.py", mutants, manifest, hashes, True)
    assert cached == 2
    assert len(pending) == len(mutants) - 2
    assert [m.key for m in survivors] == [mutants[1].key]


def test_partition_ignores_the_manifest_when_told_to(tmp_path):
    manifest, mutants, hashes = manifest_for(tmp_path, ["killed", "survived"])
    pending, survivors, cached = partition("src/a.py", mutants, manifest, hashes, False)
    assert (len(pending), survivors, cached) == (len(mutants), [], 0)


# --------------------------------------------------------------------------- the file loop


def run(root, suite, tmp_path, **overrides):
    manifest = Manifest(tmp_path / "m.json", {})
    outcome = mutate_file(root / "src" / "a.py", root, suite, manifest, options(**overrides))
    return outcome, manifest


def test_a_suite_that_never_fails_leaves_every_mutant_alive(project, tmp_path):
    root, suite = project
    (outcome, _) = run(root, suite, tmp_path)
    survivors, ran, cached = outcome
    assert ran == len(collect(SOURCE))
    assert len(survivors) == ran
    assert cached == 0


def test_a_suite_that_always_fails_kills_every_mutant(project, tmp_path):
    root, _ = project
    (outcome, _) = run(root, failing(root), tmp_path)
    assert outcome is None  # the baseline fails too, so nothing can be trusted


def test_the_file_comes_back_byte_for_byte(project, tmp_path):
    root, suite = project
    target = root / "src" / "a.py"
    before = target.read_bytes()
    run(root, suite, tmp_path)
    assert target.read_bytes() == before


def test_the_backup_is_removed_when_the_run_finishes(project, tmp_path):
    root, suite = project
    run(root, suite, tmp_path)
    assert not (root / ".scratch" / "mutate-backup" / "src__a.py").exists()


def test_verbose_prints_a_line_for_every_mutant(project, tmp_path, capsys):
    root, suite = project
    (outcome, _) = run(root, suite, tmp_path, verbose=True)
    lines = [line for line in capsys.readouterr().out.splitlines() if "SURVIVED" in line]
    assert len(lines) == outcome[1]
    assert lines[0].startswith("  [expr] SURVIVED L")


def test_quiet_reports_progress_on_stderr_instead(project, tmp_path, capsys):
    root, suite = project
    run(root, suite, tmp_path)
    captured = capsys.readouterr()
    assert "SURVIVED" not in captured.out
    assert "survivors," in captured.err


def test_the_header_names_sites_mutants_and_what_is_cached(project, tmp_path, capsys):
    root, suite = project
    run(root, suite, tmp_path)
    header = capsys.readouterr().out.splitlines()[0]
    assert header.startswith("src/a.py: ")
    assert "sites," in header and "mutants," in header and "cached" in header


def test_a_file_over_the_cap_is_reported_and_left_alone(project, tmp_path, capsys):
    root, suite = project
    (outcome, manifest) = run(root, suite, tmp_path, max_sites=1)
    assert outcome == ([], 0, 0)
    assert manifest.breaches == {"src/a.py": 4}
    assert "over the cap of 1" in capsys.readouterr().out


def test_a_cap_of_zero_switches_the_check_off(project, tmp_path):
    root, suite = project
    (outcome, manifest) = run(root, suite, tmp_path, max_sites=0)
    assert manifest.breaches == {}
    assert outcome[1] > 0


def test_nothing_is_run_twice(project, tmp_path, capsys):
    root, suite = project
    target = root / "src" / "a.py"
    manifest = Manifest(tmp_path / "m.json", SUITE_STATE)
    first = mutate_file(target, root, suite, manifest, options())
    manifest.save()
    capsys.readouterr()
    manifest = Manifest(tmp_path / "m.json", SUITE_STATE)
    assert manifest.state == "same"
    second = mutate_file(target, root, suite, manifest, options())
    assert second[1] == 0
    assert second[2] == first[1]
    assert [m.key for m in second[0]] == [m.key for m in first[0]]


def test_the_manifest_ends_up_holding_a_verdict_for_every_mutant(project, tmp_path):
    root, suite = project
    (outcome, manifest) = run(root, suite, tmp_path)
    stored = manifest.sites_for("src/a.py")
    assert len(stored) == outcome[1]
    assert {entry["verdict"] for entry in stored.values()} == {"survived"}


def test_a_ghost_mutant_is_skipped_rather_than_run(project, tmp_path):
    root, suite = project
    manifest = Manifest(tmp_path / "m.json", {})
    ghost = Mutant("del", 99, "f", 9, 0, "drop Return", 2)
    assert manifest.cached("src/a.py", ghost, unit_hashes(SOURCE)) is None
