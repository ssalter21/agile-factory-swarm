"""The command line: what it accepts, what it prints, and what it exits with.

The exit code is the gate's answer, so every one of them is pinned here.
"""

import sys

import pytest

from mutate.__main__ import CLEAN, OVER_CAP, SURVIVORS, UNTRUSTWORTHY
from mutate.__main__ import main, parse_args, report, run_list
from mutate.mutants import Mutant, collect, documented, excluded
from mutate.runner import python_files

SOURCE = "def f(a):\n    return a > 1\n"


@pytest.fixture
def project(tmp_path):
    """A one-function project, with a passing and a failing checker to point the tool at."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(SOURCE, encoding="utf-8")
    for name, code in (("pass.py", 0), ("fail.py", 1)):
        (tmp_path / name).write_text("import sys\nsys.exit(%d)\n" % code, encoding="utf-8")
    return tmp_path


def argv(root, *extra, checker="pass.py"):
    command = "%s %s" % (sys.executable, root / checker)
    return ["src", "--root", str(root), "--test-command", command, "--manifest", "m.json", *extra]


# --------------------------------------------------------------------------- arguments


def test_the_defaults_are_the_cheap_ones():
    options = parse_args(["src"])
    assert options.root == "."
    assert options.tests == ["tests"]
    assert options.manifest == ".swarm/mutation.json"
    assert options.all is False
    assert options.verbose is False
    assert options.list is False
    assert options.max_sites is None


def test_several_paths_are_accepted():
    assert parse_args(["a.py", "b.py"]).paths == ["a.py", "b.py"]


def test_the_flags_are_read():
    options = parse_args(["src", "--all", "--verbose", "--list", "--max-sites", "40"])
    assert (options.all, options.verbose, options.list, options.max_sites) == (True, True, True, 40)


def test_the_overrides_are_read():
    options = parse_args(["src", "--root", "r", "--shell", "bash", "--test-command", "x"])
    assert (options.root, options.shell, options.test_command) == ("r", "bash", "x")


def test_the_test_tree_can_be_several_paths():
    assert parse_args(["src", "--tests", "a", "b"]).tests == ["a", "b"]


def test_a_path_is_required():
    with pytest.raises(SystemExit):
        parse_args([])


# --------------------------------------------------------------------------- exit codes


def test_a_run_with_every_mutant_killed_exits_zero(tmp_path, capsys):
    """A suite strong enough to kill all seven mutants of `a > 1` leaves nothing to report."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(SOURCE, encoding="utf-8")
    checker = tmp_path / "check.py"
    checker.write_text(
        "import sys\n"
        "sys.path.insert(0, 'src')\n"
        "import a\n"
        "assert a.f(2) is True\n"
        "assert a.f(1) is False\n"
        "assert a.f(0) is False\n",
        encoding="utf-8",
    )
    command = "%s %s" % (sys.executable, checker)
    code = main(
        ["src", "--root", str(tmp_path), "--test-command", command, "--manifest", "m.json"]
    )
    out = capsys.readouterr().out
    assert "SURVIVOR" not in out, out
    assert code == CLEAN


def test_survivors_exit_one(project, capsys):
    assert main(argv(project)) == SURVIVORS
    assert "SURVIVOR" in capsys.readouterr().out


def test_a_breach_exits_two(project, capsys):
    assert main(argv(project, "--max-sites", "1")) == OVER_CAP
    assert "OVER CAP" in capsys.readouterr().out


def test_a_failing_baseline_exits_three(project, capsys):
    assert main(argv(project, checker="fail.py")) == UNTRUSTWORTHY
    assert "BASELINE FAILS" in capsys.readouterr().out


def test_nothing_to_mutate_exits_three(project, capsys):
    assert main(["nowhere", "--root", str(project)]) == UNTRUSTWORTHY
    assert "nothing to mutate" in capsys.readouterr().err


def test_no_test_command_exits_three(project, capsys):
    (project / ".swarm").mkdir()
    (project / ".swarm" / "gate.yaml").write_text("steps:\n  tests: missing\n", encoding="utf-8")
    assert main(["src", "--root", str(project)]) == UNTRUSTWORTHY
    assert "no test command" in capsys.readouterr().err


def test_the_exit_codes_are_the_documented_ones():
    assert (CLEAN, SURVIVORS, OVER_CAP, UNTRUSTWORTHY) == (0, 1, 2, 3)


# --------------------------------------------------------------------------- listing


def test_listing_names_sites_and_mutants(project, capsys):
    assert run_list(python_files(project, ["src"]), project, 0) == CLEAN
    line = capsys.readouterr().out.strip()
    assert line.startswith("src/a.py: ")
    assert "sites," in line and "mutants" in line


def test_listing_flags_a_breach_and_exits_two(project, capsys):
    assert run_list(python_files(project, ["src"]), project, 1) == OVER_CAP
    assert "OVER THE CAP OF 1" in capsys.readouterr().out


def test_a_cap_of_zero_never_flags_a_breach(project, capsys):
    assert run_list(python_files(project, ["src"]), project, 0) == CLEAN
    assert "OVER THE CAP" not in capsys.readouterr().out


def test_listing_runs_no_mutants(project, capsys):
    before = (project / "src" / "a.py").read_bytes()
    main(["src", "--root", str(project), "--list", "--max-sites", "0"])
    assert (project / "src" / "a.py").read_bytes() == before
    assert "to run" not in capsys.readouterr().out


# --------------------------------------------------------------------------- reporting


def mutant(desc="Gt -> Lt", line=2):
    return Mutant("expr", 0, "f", 0, 0, desc, line)


def test_a_clean_report_says_so(capsys):
    assert report([], 12, 3, {}) == CLEAN
    assert capsys.readouterr().out.strip() == "mutate: 0 survivors, 12 mutants run, 3 cached"


def test_every_survivor_is_named_with_its_file(capsys):
    assert report([("src/a.py", mutant())], 1, 0, {}) == SURVIVORS
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0] == "mutate: 1 survivors, 1 mutants run, 0 cached"
    assert lines[1] == "  SURVIVOR src/a.py L2 Gt -> Lt"


def test_a_breach_outranks_survivors_in_the_exit_code(capsys):
    assert report([("src/a.py", mutant())], 1, 0, {"big.py": 400}) == OVER_CAP
    out = capsys.readouterr().out
    assert "SURVIVOR src/a.py" in out
    assert "OVER CAP big.py 400 sites" in out


def test_breaches_are_reported_in_a_settled_order(capsys):
    report([], 0, 0, {"z.py": 1, "a.py": 2})
    names = [line.split()[2] for line in capsys.readouterr().out.splitlines() if "OVER CAP" in line]
    assert names == ["a.py", "z.py"]


# --------------------------------------------------------------------------- caching end to end


def test_the_second_run_reuses_the_first(project, capsys):
    main(argv(project))
    capsys.readouterr()
    assert main(argv(project)) == SURVIVORS
    assert "0 mutants run" in capsys.readouterr().out


def test_all_ignores_the_manifest(project, capsys):
    main(argv(project))
    capsys.readouterr()
    main(argv(project, "--all"))
    out = capsys.readouterr().out
    assert "0 cached" in out
    assert "0 mutants run" not in out


def test_the_manifest_lands_where_it_was_asked_to(project):
    main(argv(project))
    assert (project / "m.json").is_file()


# --------------------------------------------------------------------------- documentation


def test_help_text_is_not_a_mutation_site():
    text = 'parser.add_argument("--all", help="ignore the manifest")\n'
    assert not [m for m in collect(text) if "ignore the manifest" in m.desc]
    assert [m for m in collect(text) if "--all" in m.desc]


def test_a_description_is_not_a_mutation_site():
    text = 'ArgumentParser(prog="mutate", description="Mutation testing")\n'
    assert not [m for m in collect(text) if "Mutation testing" in m.desc]
    assert [m for m in collect(text) if "mutate" in m.desc]


def test_documented_finds_the_keywords_it_claims_to():
    for keyword in ("help", "description", "epilog", "usage"):
        assert documented(__import__("ast").parse('f(%s="text")' % keyword))


def test_a_non_documentation_keyword_is_still_mutated():
    assert not documented(__import__("ast").parse('f(prog="text")'))


def test_excluded_covers_docstrings_and_documentation():
    tree = __import__("ast").parse('"""Doc."""\n\nf(help="text")\n')
    assert len(excluded(tree)) == 2
