from swarm_doctor import gate

GATE = b"""# a comment at column 0
shell: pwsh

steps:
  tests:       "run the suite"
  coverage:    "run the suite; report --fail-under=0"
  duplication: missing
  mutation:    missing
  crap:        missing
  acceptance:  missing

defaults:
  crap_max: 6
"""


def test_the_path_is_the_one_literal_with_forward_slashes():
    assert gate.GATE_RELATIVE_PATH == ".swarm/gate.yaml"


def test_reads_the_steps_mapping_in_file_order_unquoted():
    assert gate.parse_steps(GATE) == (
        ("tests", "run the suite"),
        ("coverage", "run the suite; report --fail-under=0"),
        ("duplication", "missing"),
        ("mutation", "missing"),
        ("crap", "missing"),
        ("acceptance", "missing"),
    )


def test_reads_nothing_outside_the_steps_mapping():
    keys = [key for key, _ in gate.parse_steps(GATE)]
    assert "shell" not in keys
    assert "crap_max" not in keys


def test_keeps_the_files_order_rather_than_imposing_one():
    raw = b"steps:\n  crap: missing\n  tests: run it\n"
    assert gate.parse_steps(raw) == (("crap", "missing"), ("tests", "run it"))


def test_an_empty_value_is_no_scalar():
    assert gate.parse_steps(b"steps:\n  mutation:\n  crap: missing\n") == (
        ("mutation", None),
        ("crap", "missing"),
    )


def test_an_empty_quoted_value_is_no_scalar():
    assert gate.parse_steps(b'steps:\n  crap: ""\n') == (("crap", None),)


def test_a_flow_collection_value_is_no_scalar():
    assert gate.parse_steps(b"steps:\n  crap: [one, two]\n") == (("crap", None),)


def test_an_unterminated_quote_is_no_scalar():
    assert gate.parse_steps(b'steps:\n  crap: "run it\n') == (("crap", None),)


def test_a_trailing_comment_is_not_part_of_the_value():
    assert gate.parse_steps(b"steps:\n  crap: missing  # a debt\n") == (
        ("crap", "missing"),
    )


def test_a_hash_inside_quotes_stays_in_the_value():
    assert gate.parse_steps(b'steps:\n  crap: "run --tag=#1"\n') == (
        ("crap", "run --tag=#1"),
    )


def test_lines_nested_below_an_entry_are_not_entries():
    raw = b"steps:\n  crap:\n    inner: value\n  tests: run it\n"
    assert gate.parse_steps(raw) == (("crap", None), ("tests", "run it"))


def test_a_block_line_that_is_no_key_and_value_pair_is_not_an_entry():
    raw = b"steps:\n  crap: missing\n  - a list item\n"
    assert gate.parse_steps(raw) == (("crap", "missing"),)


def test_a_block_line_with_an_empty_key_is_not_an_entry():
    raw = b"steps:\n  crap: missing\n  : orphaned\n"
    assert gate.parse_steps(raw) == (("crap", "missing"),)


def test_the_mapping_ends_at_the_next_column_zero_key():
    raw = b"steps:\n  crap: missing\ndefaults:\n  crap_max: 6\n"
    assert gate.parse_steps(raw) == (("crap", "missing"),)


def test_bytes_that_are_not_utf8_yield_no_mapping():
    assert gate.parse_steps(b"steps:\n  crap: \xff\xfe\n") is None


def test_text_with_no_top_level_steps_key_yields_no_mapping():
    assert gate.parse_steps(b"shell: pwsh\ndefaults:\n  crap_max: 6\n") is None


def test_an_indented_steps_key_is_not_the_top_level_one():
    assert gate.parse_steps(b"outer:\n  steps:\n    crap: missing\n") is None


def test_a_steps_key_with_no_entries_beneath_it_yields_no_mapping():
    assert gate.parse_steps(b"steps:\n\ndefaults:\n  crap_max: 6\n") is None
