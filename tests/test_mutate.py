"""The mutation runner end to end: real files, real mutants, real exit codes.

conftest.py puts the tool on sys.path. The narrower tests live beside this file, one module per
part: operators, runner, internals, cli.
"""

import json
import os
import sys
import textwrap

import pytest

from mutate.__main__ import main
from mutate.config import load_gate, parse_yaml, scalar, strip_comment
from mutate.manifest import Manifest, VERSION
from mutate.mutants import Mutant, build, collect, site_count
from mutate.runner import Suite, python_files
from mutate.units import compare_tests, test_state as suite_state, unit_hashes


def source(text):
    return textwrap.dedent(text).lstrip()


# --------------------------------------------------------------------------- gate.yaml


def test_parse_yaml_reads_sections_and_scalars():
    tree = parse_yaml(
        source(
            """
            # a comment
            shell: pwsh
            steps:
              tests:       "pytest -q"
              mutation:    missing
            defaults:
              crap_max: 6
            """
        )
    )
    assert tree["shell"] == "pwsh"
    assert tree["steps"] == {"tests": "pytest -q", "mutation": "missing"}
    assert tree["defaults"]["crap_max"] == 6


def test_strip_comment_leaves_hashes_inside_quotes():
    kept = strip_comment('tests: "pytest -k \'a#b\'"  # note')
    assert kept.strip() == 'tests: "pytest -k \'a#b\'"'


def test_scalar_keeps_a_quoted_number_as_text():
    assert scalar('"6"') == "6"
    assert scalar("6") == 6
    assert scalar("-2") == -2


def test_load_gate_defaults_when_there_is_no_file(tmp_path):
    gate = load_gate(tmp_path / "gate.yaml")
    assert gate.max_sites == 100
    assert gate.tests is None


def test_load_gate_reads_the_cap_and_the_commands(tmp_path):
    path = tmp_path / "gate.yaml"
    path.write_text(
        source(
            """
            shell: pwsh
            steps:
              tests: "pytest -q"
            defaults:
              max_mutation_sites_per_file: 40
              mutation_test_command: "pytest -q -x"
            """
        ),
        encoding="utf-8",
    )
    gate = load_gate(path)
    assert (gate.shell, gate.tests, gate.mutation_tests, gate.max_sites) == (
        "pwsh",
        "pytest -q",
        "pytest -q -x",
        40,
    )


def test_load_gate_ignores_a_non_numeric_cap(tmp_path):
    path = tmp_path / "gate.yaml"
    path.write_text("defaults:\n  max_mutation_sites_per_file: lots\n", encoding="utf-8")
    assert load_gate(path).max_sites == 100


# --------------------------------------------------------------------------- sites


def test_docstrings_are_not_mutation_sites():
    with_doc = collect(source('''
        def f(a):
            """Docstring with several words."""
            return a
    '''))
    without = collect(source("""
        def f(a):
            return a
    """))
    assert len(with_doc) == len(without)


def test_imports_are_not_deletion_sites():
    sites = collect(source("""
        import os

        def f():
            os.getcwd()
    """))
    assert not [site for site in sites if site.kind == "del" and "Import" in site.desc]


def test_a_return_of_none_is_not_a_return_site():
    sites = collect("def f():\n    return None\n")
    assert not [site for site in sites if site.desc == "return -> None"]


def test_comparison_and_if_sites_are_found():
    descs = {site.desc for site in collect("def f(a):\n    if a > 1:\n        return a\n")}
    assert "Gt -> LtE" in descs
    assert "if -> True" in descs
    assert "return -> None" in descs


def test_sites_carry_their_enclosing_unit():
    sites = collect(source("""
        class Box:
            def size(self):
                return 1 + 2
    """))
    units = {site.unit for site in sites}
    assert "Box.size" in units


def test_build_makes_a_parseable_mutant_that_differs():
    text = "def f(a):\n    return a > 1\n"
    site = [s for s in collect(text) if s.desc == "Gt -> LtE"][0]
    mutant = build(text, site)
    assert "<=" in mutant
    assert collect(mutant)  # still valid Python


def test_build_returns_none_for_a_site_that_no_longer_exists():
    text = "def f(a):\n    return a\n"
    ghost = Mutant("del", 99, "f", 0, 0, "drop Return", 2)
    assert build(text, ghost) is None


def test_deleting_a_statement_replaces_it_with_pass():
    text = "def f(a):\n    a = a + 1\n    return a\n"
    site = [s for s in collect(text) if s.desc == "drop Assign"][0]
    assert "pass" in build(text, site)


# --------------------------------------------------------------------------- unit identity


def test_adding_a_function_leaves_the_other_units_alone():
    before = unit_hashes(source("""
        TOP = 1

        def f():
            return 1
    """))
    after = unit_hashes(source("""
        TOP = 1

        def f():
            return 1

        def g():
            return 2
    """))
    assert after["<module>"] == before["<module>"]
    assert after["f"] == before["f"]
    assert "g" in after


def test_editing_a_function_changes_only_its_own_hash():
    before = unit_hashes("def f():\n    return 1\n\ndef g():\n    return 2\n")
    after = unit_hashes("def f():\n    return 99\n\ndef g():\n    return 2\n")
    assert after["f"] != before["f"]
    assert after["g"] == before["g"]


def test_site_keys_survive_an_edit_elsewhere_in_the_file():
    before = {s.key for s in collect("def f(a):\n    return a > 1\n")}
    after = {
        s.key
        for s in collect("def z():\n    return 0\n\ndef f(a):\n    return a > 1\n")
    }
    assert before <= after


def test_unit_hashes_ignore_comments_and_formatting():
    plain = unit_hashes("def f():\n    return 1\n")
    fancy = unit_hashes("def f():\n    # a note\n    return  1\n")
    assert plain["f"] == fancy["f"]


# --------------------------------------------------------------------------- test suite state


def test_compare_tests_names_the_three_cases():
    old = {"tests/test_a.py::f": "1"}
    assert compare_tests(old, dict(old)) == "same"
    assert compare_tests(old, {**old, "tests/test_a.py::g": "2"}) == "additive"
    assert compare_tests(old, {"tests/test_a.py::f": "2"}) == "changed"
    assert compare_tests(old, {}) == "changed"


def test_test_state_keys_by_path_and_unit(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_one():\n    assert True\n", encoding="utf-8")
    state = suite_state(tmp_path, ["tests"])
    assert "tests/test_a.py::test_one" in state


def test_test_state_skips_a_file_it_cannot_parse(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_broken.py").write_text("def (\n", encoding="utf-8")
    assert suite_state(tmp_path, ["tests"]) == {}


# --------------------------------------------------------------------------- manifest


def manifest_with(tmp_path, verdict, unit_hash="h", tests=None):
    path = tmp_path / "mutation.json"
    path.write_text(
        json.dumps(
            {
                "version": VERSION,
                "tests": tests if tests is not None else {"tests/test_a.py::f": "1"},
                "files": {
                    "src/a.py": {"sites": {"f#expr#0#0": {"verdict": verdict, "unit": unit_hash}}}
                },
            }
        ),
        encoding="utf-8",
    )
    return path



@pytest.fixture
def site():
    return Mutant("expr", 0, "f", 0, 0, "Gt -> LtE", 3)


def test_an_unchanged_suite_reuses_both_verdicts(tmp_path, site):
    tests = {"tests/test_a.py::f": "1"}
    for verdict in ("killed", "survived"):
        manifest = Manifest(manifest_with(tmp_path, verdict), tests)
        assert manifest.state == "same"
        assert manifest.cached("src/a.py", site, {"f": "h"}) == verdict


def test_added_tests_reuse_kills_but_re_run_survivors(tmp_path, site):
    grown = {"tests/test_a.py::f": "1", "tests/test_a.py::g": "2"}
    killed = Manifest(manifest_with(tmp_path, "killed"), grown)
    assert killed.state == "additive"
    assert killed.cached("src/a.py", site, {"f": "h"}) == "killed"

    survived = Manifest(manifest_with(tmp_path, "survived"), grown)
    assert survived.cached("src/a.py", site, {"f": "h"}) is None


def test_edited_tests_reuse_nothing(tmp_path, site):
    manifest = Manifest(manifest_with(tmp_path, "killed"), {"tests/test_a.py::f": "2"})
    assert manifest.state == "changed"
    assert manifest.cached("src/a.py", site, {"f": "h"}) is None


def test_an_edited_function_invalidates_its_own_sites(tmp_path, site):
    manifest = Manifest(manifest_with(tmp_path, "killed"), {"tests/test_a.py::f": "1"})
    assert manifest.cached("src/a.py", site, {"f": "different"}) is None


def test_a_manifest_from_another_version_is_discarded(tmp_path, site):
    path = tmp_path / "mutation.json"
    path.write_text(json.dumps({"version": VERSION + 1, "files": {}}), encoding="utf-8")
    manifest = Manifest(path, {})
    assert manifest.data["files"] == {}


def test_a_corrupt_manifest_is_discarded(tmp_path, site):
    path = tmp_path / "mutation.json"
    path.write_text("{not json", encoding="utf-8")
    assert Manifest(path, {}).data["files"] == {}


def test_prune_forgets_sites_that_no_longer_exist(tmp_path, site):
    manifest = Manifest(manifest_with(tmp_path, "killed"), {"tests/test_a.py::f": "1"})
    manifest.prune("src/a.py", [])
    assert manifest.sites_for("src/a.py") == {}


def test_record_then_save_round_trips(tmp_path, site):
    path = tmp_path / "nested" / "mutation.json"
    manifest = Manifest(path, {})
    manifest.record("src/a.py", site, {"f": "h"}, "survived")
    manifest.save()
    reloaded = Manifest(path, {})
    assert reloaded.cached("src/a.py", site, {"f": "h"}) == "survived"


# --------------------------------------------------------------------------- the suite command


def test_a_plain_command_runs_without_a_shell():
    assert Suite.command_argv("pytest -q tests", "pwsh") == ["pytest", "-q", "tests"]


def test_a_command_with_shell_syntax_goes_through_the_shell():
    argv = Suite.command_argv("coverage run -m pytest; coverage report", "pwsh")
    assert argv[0] == "pwsh"
    assert argv[-1].endswith("coverage report")


def test_cmd_and_posix_shells_are_both_known():
    assert Suite.command_argv("a && b", "cmd")[:2] == ["cmd.exe", "/c"]
    assert Suite.command_argv("a && b", "bash")[:2] == ["bash", "-c"]


@pytest.mark.skipif(os.name != "nt", reason="Windows path quoting")
def test_a_windows_path_is_not_mangled():
    argv = Suite.command_argv(r'"C:\py\python.exe" -q', "pwsh")
    assert argv == [r"C:\py\python.exe", "-q"]


# --------------------------------------------------------------------------- end to end


def project(tmp_path, verdict):
    """A tiny project whose test command always passes or always fails."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "a.py").write_text("def f(a):\n    return a > 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_a.py").write_text("def test_f():\n    assert True\n", encoding="utf-8")
    checker = tmp_path / "check.py"
    checker.write_text("import sys\nsys.exit(%d)\n" % (0 if verdict == "survive" else 1), encoding="utf-8")
    return "%s %s" % (sys.executable, checker)


def test_a_suite_that_never_fails_lets_every_mutant_survive(tmp_path, capsys):
    command = project(tmp_path, "survive")
    code = main(
        ["src", "--root", str(tmp_path), "--test-command", command, "--manifest", "m.json"]
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "SURVIVOR" in out
    assert "0 cached" in out


def test_a_second_run_reuses_the_manifest(tmp_path, capsys):
    command = project(tmp_path, "survive")
    argv = ["src", "--root", str(tmp_path), "--test-command", command, "--manifest", "m.json"]
    main(argv)
    capsys.readouterr()
    main(argv)
    out = capsys.readouterr().out
    assert "0 mutants run" in out


def test_the_target_file_is_restored(tmp_path):
    command = project(tmp_path, "survive")
    before = (tmp_path / "src" / "a.py").read_bytes()
    main(["src", "--root", str(tmp_path), "--test-command", command, "--manifest", "m.json"])
    assert (tmp_path / "src" / "a.py").read_bytes() == before


def test_a_failing_baseline_is_reported_rather_than_scored(tmp_path, capsys):
    command = project(tmp_path, "fail")
    code = main(
        ["src", "--root", str(tmp_path), "--test-command", command, "--manifest", "m.json"]
    )
    assert code == 3
    assert "BASELINE FAILS" in capsys.readouterr().out


def test_a_file_over_the_cap_is_not_mutated(tmp_path, capsys):
    command = project(tmp_path, "survive")
    code = main(
        [
            "src",
            "--root",
            str(tmp_path),
            "--test-command",
            command,
            "--manifest",
            "m.json",
            "--max-sites",
            "1",
        ]
    )
    out = capsys.readouterr().out
    assert code == 2
    assert "over the cap" in out
    assert "OVER CAP" in out


def test_list_counts_sites_without_running_anything(tmp_path, capsys):
    project(tmp_path, "fail")
    code = main(["src", "--root", str(tmp_path), "--list", "--max-sites", "0"])
    assert code == 0
    assert "sites" in capsys.readouterr().out


def test_list_fails_when_a_file_is_over_the_cap(tmp_path, capsys):
    project(tmp_path, "fail")
    assert main(["src", "--root", str(tmp_path), "--list", "--max-sites", "1"]) == 2
    assert "OVER THE CAP" in capsys.readouterr().out


def test_nothing_to_mutate_is_an_error(tmp_path):
    assert main(["src", "--root", str(tmp_path)]) == 3


def test_a_missing_test_command_is_an_error(tmp_path):
    project(tmp_path, "survive")
    (tmp_path / ".swarm").mkdir()
    (tmp_path / ".swarm" / "gate.yaml").write_text("steps:\n  tests: missing\n", encoding="utf-8")
    assert main(["src", "--root", str(tmp_path)]) == 3


def test_pycache_is_not_a_target(tmp_path):
    project(tmp_path, "survive")
    cache = tmp_path / "src" / "__pycache__"
    cache.mkdir()
    (cache / "a.cpython-311.py").write_text("x = 1\n", encoding="utf-8")
    found = [path.name for path in python_files(tmp_path, ["src"])]
    assert found == ["a.py"]


# --------------------------------------------------------------------------- sites vs mutants


def test_one_comparison_is_one_site_with_several_mutants():
    mutants = [m for m in collect("def f(a):\n    return a > 1\n") if m.desc.startswith("Gt")]
    assert len(mutants) == 3
    assert len({m.site for m in mutants}) == 1


def test_site_count_counts_places_not_changes():
    mutants = collect("def f(a):\n    return a > 1\n")
    assert site_count(mutants) < len(mutants)


def test_the_cap_is_measured_in_sites():
    text = "def f(a):\n    return a > 1\n"
    mutants = collect(text)
    assert site_count(mutants) == len({m.site for m in mutants})


def test_gate_command_prefers_the_command_written_for_mutation(tmp_path):
    path = tmp_path / "gate.yaml"
    path.write_text(
        "steps:\n  tests: \"pytest -q\"\ndefaults:\n  mutation_test_command: \"pytest -x\"\n",
        encoding="utf-8",
    )
    assert load_gate(path).command == "pytest -x"


def test_gate_command_is_none_when_the_step_is_missing(tmp_path):
    path = tmp_path / "gate.yaml"
    path.write_text("steps:\n  tests: missing\n", encoding="utf-8")
    assert load_gate(path).command is None


def test_a_relative_executable_is_found_in_the_project(tmp_path):
    (tmp_path / "bin").mkdir()
    exe = tmp_path / "bin" / "runner.exe"
    exe.write_bytes(b"")
    argv = Suite.resolve(["bin/runner.exe", "-q"], tmp_path)
    assert argv == [str(exe), "-q"]


def test_an_executable_on_the_path_is_left_alone(tmp_path):
    assert Suite.resolve(["pytest", "-q"], tmp_path) == ["pytest", "-q"]
