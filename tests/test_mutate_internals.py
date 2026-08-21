"""Unit identity, mutant numbering, the config subset, and the manifest's storage rules.

The end-to-end tests prove the tool works. These prove it works for the reasons claimed -- that
identity survives edits, that ordinals are per unit, that the manifest reuses exactly what it is
still entitled to reuse.
"""

import ast
import json

import pytest

from mutate import units
from mutate.config import Gate, load_gate, parse_yaml, scalar, strip_comment, unquote
from mutate.manifest import VERSION, Manifest
from mutate.mutants import Mutant, build, collect, docstrings, site_count, statement_slots

NESTED = """
TOP = 1


def outer():
    inner = 2

    def within():
        return 3

    return within


class Box:
    SIZE = 4

    def size(self):
        return self.SIZE
"""


# --------------------------------------------------------------------------- units


def test_every_def_and_class_is_a_unit():
    names = {name for _, name in units.iter_units(ast.parse(NESTED))}
    assert names == {"<module>", "outer", "outer.within", "Box", "Box.size"}


def test_the_module_is_the_first_unit():
    first = next(iter(units.iter_units(ast.parse(NESTED))))[1]
    assert first == "<module>"


def test_qualify_joins_all_but_the_module():
    assert units.qualify("<module>", "f") == "f"
    assert units.qualify("Box", "size") == "Box.size"


def test_a_node_belongs_to_the_unit_it_sits_in():
    tree = ast.parse(NESTED)
    found = units.unit_map(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == 3:
            assert found[id(node)] == "outer.within"


def test_a_def_belongs_to_the_unit_around_it_not_to_itself():
    tree = ast.parse(NESTED)
    found = units.unit_map(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "within":
            assert found[id(node)] == "outer"


def test_a_unit_hash_ignores_what_is_nested_in_it():
    before = units.unit_hashes(NESTED)
    after = units.unit_hashes(NESTED.replace("return 3", "return 300"))
    assert after["outer.within"] != before["outer.within"]
    assert after["outer"] == before["outer"]
    assert after["<module>"] == before["<module>"]


def test_a_class_body_is_its_own_unit():
    before = units.unit_hashes(NESTED)
    after = units.unit_hashes(NESTED.replace("SIZE = 4", "SIZE = 40"))
    assert after["Box"] != before["Box"]
    assert after["Box.size"] == before["Box.size"]


def test_stripping_leaves_a_pass_where_a_body_would_be_empty():
    outer = ast.parse("def f():\n    def g():\n        return 1\n").body[0]
    units.strip_nested(outer)
    assert ast.unparse(ast.fix_missing_locations(outer)).strip() == "def f():\n    pass"


def test_stripping_a_module_of_nothing_but_defs_leaves_it_empty():
    tree = ast.parse("def f():\n    return 1\n")
    units.strip_nested(tree)
    assert ast.unparse(tree).strip() == ""


def test_stripping_reaches_a_def_hidden_inside_a_branch():
    tree = ast.parse("if True:\n    def f():\n        return 1\n")
    units.strip_nested(tree)
    assert "return 1" not in ast.unparse(tree)


def test_stripping_keeps_the_code_around_the_units():
    tree = ast.parse("A = 1\n\ndef f():\n    return 2\n\nB = 3\n")
    units.strip_nested(tree)
    assert ast.unparse(tree).split() == ["A", "=", "1", "B", "=", "3"]


def test_a_hash_is_short_and_stable():
    first = units.digest("hello")
    assert first == units.digest("hello")
    assert first != units.digest("hell0")
    assert len(first) == 16


# --------------------------------------------------------------------------- the test tree


def write_tests(root, files):
    (root / "tests").mkdir(exist_ok=True)
    for name, text in files.items():
        (root / "tests" / name).write_text(text, encoding="utf-8")


def test_the_test_tree_is_keyed_by_path_and_unit(tmp_path):
    write_tests(tmp_path, {"test_a.py": "def test_one():\n    assert True\n"})
    state = units.test_state(tmp_path, ["tests"])
    assert set(state) == {"tests/test_a.py::<module>", "tests/test_a.py::test_one"}


def test_a_helper_that_is_not_a_test_still_counts(tmp_path):
    write_tests(tmp_path, {"conftest.py": "def helper():\n    return 1\n"})
    assert "tests/conftest.py::helper" in units.test_state(tmp_path, ["tests"])


def test_a_single_file_can_be_named_directly(tmp_path):
    write_tests(tmp_path, {"test_a.py": "def test_one():\n    assert True\n"})
    assert units.test_state(tmp_path, ["tests/test_a.py"])


def test_compiled_test_files_are_ignored(tmp_path):
    write_tests(tmp_path, {"test_a.py": "def test_one():\n    assert True\n"})
    cache = tmp_path / "tests" / "__pycache__"
    cache.mkdir()
    (cache / "test_a.py").write_text("def test_ghost():\n    pass\n", encoding="utf-8")
    assert not any("ghost" in key for key in units.test_state(tmp_path, ["tests"]))


def test_a_test_file_that_will_not_parse_is_skipped(tmp_path):
    write_tests(tmp_path, {"test_a.py": "def test_one():\n    assert True\n", "bad.py": "def (\n"})
    state = units.test_state(tmp_path, ["tests"])
    assert not any("bad.py" in key for key in state)
    assert any("test_a.py" in key for key in state)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        ({"a": "1"}, {"a": "1"}, "same"),
        ({"a": "1"}, {"a": "1", "b": "2"}, "additive"),
        ({"a": "1"}, {"a": "2"}, "changed"),
        ({"a": "1"}, {}, "changed"),
        ({}, {"a": "1"}, "additive"),
        ({}, {}, "same"),
    ],
)
def test_the_test_tree_is_classified_three_ways(old, new, expected):
    assert units.compare_tests(old, new) == expected


# --------------------------------------------------------------------------- mutant identity


def test_ordinals_start_again_in_every_unit():
    mutants = collect("def f(a):\n    return a > 1\n\ndef g(b):\n    return b > 1\n")
    for unit in ("f", "g"):
        expression = [m.node for m in mutants if m.unit == unit and m.kind == "expr"]
        assert min(expression) == 0


def test_variants_are_numbered_within_their_site():
    mutants = [m for m in collect("def f(a):\n    return a > 1\n") if m.desc.startswith("Gt")]
    assert [m.variant for m in mutants] == [0, 1, 2]
    assert len({m.node for m in mutants}) == 1


def test_a_site_with_no_mutants_does_not_take_an_ordinal():
    plain = collect("def f(a):\n    return a ** 1\n")
    assert all(m.kind != "expr" or m.desc != "" for m in plain)
    assert site_count(plain) == len({m.site for m in plain})


def test_the_key_names_unit_kind_node_and_variant():
    mutant = Mutant("expr", 4, "Box.size", 2, 1, "Gt -> Lt", 9)
    assert mutant.key == "Box.size#expr#2#1"
    assert mutant.site == ("Box.size", "expr", 2)
    assert mutant.label == "L9 Gt -> Lt"


def test_deletion_mutants_are_all_variant_zero():
    assert {m.variant for m in collect(NESTED) if m.kind == "del"} == {0}


def test_a_docstring_is_neither_mutated_nor_deleted():
    with_doc = collect('def f(a):\n    """Words here."""\n    return a\n')
    assert not [m for m in with_doc if "Words" in m.desc]
    assert not [m for m in with_doc if m.desc == "drop Expr"]


def test_a_string_that_is_not_the_first_statement_is_fair_game():
    mutants = collect('def f(a):\n    a\n    "loose string"\n    return a\n')
    assert [m for m in mutants if "loose string" in m.desc]


def test_docstrings_finds_one_per_holder():
    tree = ast.parse('"""Module."""\n\n\ndef f():\n    """Function."""\n    return 1\n')
    assert len(docstrings(tree)) == 2


def test_statement_slots_never_offers_an_import():
    tree = ast.parse("import os\nfrom sys import path\n\nx = 1\n")
    kinds = {type(stmt).__name__ for _, _, _, stmt in statement_slots(tree)}
    assert kinds == {"Assign"}


def test_building_beyond_the_end_gives_nothing():
    text = "def f(a):\n    return a\n"
    assert build(text, Mutant("expr", 999, "f", 0, 0, "x", 2)) is None
    assert build(text, Mutant("del", 999, "f", 0, 0, "x", 2)) is None


def test_every_mutant_that_is_built_still_parses():
    for mutant in collect(NESTED):
        changed = build(NESTED, mutant)
        assert changed is not None, mutant.label
        ast.parse(changed)


def test_every_mutant_changes_the_code():
    original = ast.unparse(ast.parse(NESTED))
    for mutant in collect(NESTED):
        assert ast.unparse(ast.parse(build(NESTED, mutant))) != original, mutant.label


# --------------------------------------------------------------------------- gate.yaml


def test_unquote_strips_a_matched_pair_only():
    assert unquote('"a"') == "a"
    assert unquote("'a'") == "a"
    assert unquote('"a') == '"a'
    assert unquote("'a\"") == "'a\""
    assert unquote("a") == "a"
    assert unquote("") == ""


def test_a_quoted_value_keeps_its_type():
    assert scalar('"6"') == "6"
    assert scalar("6") == 6
    assert scalar("-2") == -2
    assert scalar("6a") == "6a"
    assert scalar("  spaced  ") == "spaced"


def test_a_comment_only_line_is_dropped():
    assert parse_yaml("# just a comment\nshell: pwsh\n") == {"shell": "pwsh"}


def test_a_line_with_no_colon_is_dropped():
    assert parse_yaml("nonsense\nshell: pwsh\n") == {"shell": "pwsh"}


def test_a_value_may_contain_a_colon():
    assert parse_yaml('tests: "a: b"\n')["tests"] == "a: b"


def test_an_indented_line_with_no_section_is_dropped():
    assert parse_yaml("  stray: 1\nshell: pwsh\n") == {"shell": "pwsh"}


def test_a_scalar_after_a_section_closes_it():
    tree = parse_yaml("steps:\n  tests: a\nshell: pwsh\n")
    assert tree == {"steps": {"tests": "a"}, "shell": "pwsh"}


def test_two_sections_stay_apart():
    tree = parse_yaml("steps:\n  tests: a\ndefaults:\n  crap_max: 6\n")
    assert tree == {"steps": {"tests": "a"}, "defaults": {"crap_max": 6}}


def test_strip_comment_keeps_everything_before_the_hash():
    assert strip_comment("a: b # note").rstrip() == "a: b"
    assert strip_comment("a: b").rstrip() == "a: b"
    assert strip_comment("# all of it") == ""


def test_a_gate_with_no_file_is_all_defaults(tmp_path):
    gate = load_gate(tmp_path / "nothing.yaml")
    assert (gate.shell, gate.tests, gate.mutation_tests, gate.max_sites) == (None, None, None, 250)
    assert gate.command is None


def test_the_mutation_command_wins_over_the_tests_command():
    assert Gate(tests="a", mutation_tests="b").command == "b"
    assert Gate(tests="a").command == "a"
    assert Gate(tests="missing").command is None
    assert Gate(tests="missing", mutation_tests="b").command == "b"


# --------------------------------------------------------------------------- manifest


def saved(tmp_path, data):
    path = tmp_path / "m.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_a_manifest_of_the_wrong_version_is_started_again(tmp_path):
    path = saved(tmp_path, {"version": VERSION + 1, "files": {"a.py": {"sites": {"k": {}}}}})
    assert Manifest(path, {}).data["files"] == {}


def test_a_manifest_that_is_not_json_is_started_again(tmp_path):
    path = tmp_path / "m.json"
    path.write_text("{ not json", encoding="utf-8")
    assert Manifest(path, {}).data["files"] == {}


def test_a_fresh_manifest_reuses_nothing(tmp_path):
    assert Manifest(tmp_path / "m.json", {"a": "1"}).state == "changed"


def test_the_current_test_tree_replaces_the_stored_one(tmp_path):
    path = saved(tmp_path, {"version": VERSION, "tests": {"a": "1"}, "files": {}})
    assert Manifest(path, {"b": "2"}).data["tests"] == {"b": "2"}


def test_asking_about_a_file_with_no_record_is_safe(tmp_path):
    assert Manifest(tmp_path / "m.json", {}).sites_for("nowhere.py") == {}


def test_pruning_a_file_with_no_record_is_safe(tmp_path):
    manifest = Manifest(tmp_path / "m.json", {})
    manifest.prune("nowhere.py", [])
    assert manifest.data["files"] == {}


def test_pruning_keeps_the_mutants_that_still_exist(tmp_path):
    manifest = Manifest(tmp_path / "m.json", {})
    alive = Mutant("expr", 0, "f", 0, 0, "Gt -> Lt", 2)
    gone = Mutant("expr", 1, "f", 9, 0, "Eq -> NotEq", 3)
    manifest.record("a.py", alive, {"f": "h"}, "killed")
    manifest.record("a.py", gone, {"f": "h"}, "killed")
    manifest.prune("a.py", [alive])
    assert list(manifest.sites_for("a.py")) == [alive.key]


def test_a_record_carries_the_verdict_the_unit_hash_and_the_label(tmp_path):
    manifest = Manifest(tmp_path / "m.json", {})
    mutant = Mutant("expr", 0, "f", 0, 0, "Gt -> Lt", 7)
    manifest.record("a.py", mutant, {"f": "hash"}, "survived")
    assert manifest.sites_for("a.py")[mutant.key] == {
        "verdict": "survived",
        "unit": "hash",
        "desc": "L7 Gt -> Lt",
    }


def test_the_file_is_written_sorted_and_indented(tmp_path):
    manifest = Manifest(tmp_path / "deep" / "m.json", {"b": "2", "a": "1"})
    manifest.save()
    text = (tmp_path / "deep" / "m.json").read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert '\n  "files"' in text
    assert text.index('"a"') < text.index('"b"')


def test_a_breach_is_remembered_by_file(tmp_path):
    manifest = Manifest(tmp_path / "m.json", {})
    manifest.breach("big.py", 400)
    assert manifest.breaches == {"big.py": 400}
