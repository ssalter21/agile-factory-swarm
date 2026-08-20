"""The pure side of the role compiler: reading a declaration, emitting bytes, comparing, deciding.

No filesystem and no process. Every assertion here is about a rule, and the rules are the reason
recompiling the twelve tracked agent files changes nothing.
"""

import dataclasses

import pytest

from rolecompile import compare, compiler, declaration, emit, report, validate
from rolecompile.compare import Status
from rolecompile.model import RoleSource, TargetFile

DECLARED = "name: qa\ndescription: Verifies.\ntools: Read, Bash\nmodel: opus\neffort: high\n"
PROMPT = "You are QA.\n\nDo the thing.\n"

CLAUDE_BYTES = (
    b"---\r\nname: qa\r\ndescription: Verifies.\r\ntools: Read, Bash\r\nmodel: opus\r\n"
    b"effort: high\r\n---\r\n\r\nYou are QA.\r\n\r\nDo the thing.\r\n"
)
GITHUB_BYTES = (
    b"---\r\nname: qa\r\ndescription: Verifies.\r\ntools: Read, Bash\r\n---\r\n\r\n"
    b"You are QA.\r\n\r\nDo the thing.\r\n"
)


def source(name="qa", declared=DECLARED, prompt=PROMPT):
    """One role definition on disk, as `files` would have read it."""
    return RoleSource(
        name=name,
        declaration_path="swarm/roles/%s.yaml" % name,
        declaration_bytes=declared.encode("utf-8") if isinstance(declared, str) else declared,
        prompt_path="swarm/roles/%s.md" % name,
        prompt_bytes=prompt.encode("utf-8") if isinstance(prompt, str) else prompt,
    )


def definitions(*sources):
    return [declaration.parse(one) for one in sources]


def _named(name, declared=DECLARED):
    """`DECLARED`, claiming a different name."""
    return declared.replace("name: qa", "name: %s" % name)


# --- model -------------------------------------------------------------------------------------


def test_a_role_source_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        source().name = "other"


def test_a_target_file_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        TargetFile(path="a", data=b"a").path = "b"


# --- declaration -----------------------------------------------------------------------------


def test_a_role_definition_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        definitions(source())[0].prompt = "other"


def test_fields_keep_the_order_they_were_read_in():
    assert list(declaration.fields(DECLARED)) == ["name", "description", "tools", "model", "effort"]


def test_a_value_keeps_everything_after_the_first_colon():
    assert declaration.fields("description: Plans, then: checks.")["description"] == (
        "Plans, then: checks."
    )


def test_a_hash_inside_a_value_is_part_of_the_value():
    assert declaration.fields("description: Reads #tags.")["description"] == "Reads #tags."


def test_a_comment_line_is_not_a_field():
    assert declaration.fields("  # name: ghost\nname: qa\n") == {"name": "qa"}


def test_a_blank_line_and_a_line_with_no_colon_are_ignored():
    assert declaration.fields("\nname: qa\nloose text\n\n") == {"name": "qa"}


def test_an_unknown_key_is_kept_rather_than_rejected():
    assert declaration.fields("name: qa\ncolour: red\n")["colour"] == "red"


def test_a_byte_order_mark_on_a_source_file_is_dropped():
    definition = declaration.parse(source(declared=b"\xef\xbb\xbfname: qa\ntools: Read\n"))
    assert definition.fields["name"] == "qa"


def test_a_source_file_that_is_not_utf_8_names_itself():
    with pytest.raises(declaration.SourceProblem) as caught:
        declaration.parse(source(prompt=b"\xff\xfe not text"))
    assert str(caught.value) == "swarm/roles/qa.md: the file is not valid UTF-8."


# --- emit ------------------------------------------------------------------------------------


def test_the_claude_file_is_exactly_these_bytes():
    assert emit.claude_file(declaration.fields(DECLARED), PROMPT) == CLAUDE_BYTES


def test_the_github_file_drops_model_and_effort_and_nothing_else():
    assert emit.github_file(declaration.fields(DECLARED), PROMPT) == GITHUB_BYTES


def test_the_field_order_is_fixed_and_not_the_declaration_s():
    shuffled = "effort: high\ntools: Read, Bash\nname: qa\nmodel: opus\ndescription: Verifies.\n"
    assert emit.claude_file(declaration.fields(shuffled), PROMPT) == CLAUDE_BYTES


def test_a_field_the_format_does_not_define_is_not_emitted():
    fields = declaration.fields(DECLARED + "colour: red\nisolation: worktree\n")
    assert emit.claude_file(fields, PROMPT) == CLAUDE_BYTES


def test_a_long_value_is_written_on_one_line():
    fields = declaration.fields("name: qa\ndescription: %s\ntools: Read\n" % ("word " * 60))
    written = emit.claude_file(fields, PROMPT).decode("utf-8")
    assert written.count("\r\ndescription: ") == 1
    assert len([line for line in written.split("\r\n") if line.startswith("word")]) == 0


def test_the_source_line_ending_never_reaches_the_output():
    for ending in ("\n", "\r\n", "\r"):
        declared = DECLARED.replace("\n", ending)
        assert emit.claude_file(declaration.fields(declared), PROMPT.replace("\n", ending)) == (
            CLAUDE_BYTES
        )


def test_trailing_blank_lines_collapse_to_one_newline():
    assert emit.claude_file(declaration.fields(DECLARED), PROMPT + "\n\n\n") == CLAUDE_BYTES


def test_a_prompt_with_no_final_newline_still_ends_in_one():
    assert emit.claude_file(declaration.fields(DECLARED), PROMPT.rstrip("\n")) == CLAUDE_BYTES


def test_nothing_emitted_carries_a_byte_order_mark():
    assert not emit.claude_file(declaration.fields(DECLARED), PROMPT).startswith(b"\xef\xbb\xbf")


def test_an_absent_optional_field_is_skipped_rather_than_written_empty():
    fields = declaration.fields("name: qa\ndescription: Verifies.\ntools: Read, Bash\n")
    assert b"model" not in emit.claude_file(fields, PROMPT)


# --- validate --------------------------------------------------------------------------------


def test_a_valid_set_has_no_problem():
    assert validate.first_problem(definitions(source(), source("coder", _named("coder")))) is None


def test_two_declarations_with_one_name_name_both_files_and_the_field():
    message = validate.first_problem(definitions(source(), source("probe")))
    assert message == (
        "swarm/roles/probe.yaml: the field 'name' is 'qa', "
        "which swarm/roles/qa.yaml already declares."
    )


def test_a_name_that_is_not_the_filename_names_the_file_and_the_field():
    message = validate.first_problem(definitions(source("probe", _named("prober"))))
    assert message == (
        "swarm/roles/probe.yaml: the field 'name' is 'prober', but the file is named 'probe'."
    )


def test_an_absent_name_is_reported_as_the_mismatch_it_is():
    declared = "description: Verifies.\ntools: Read\n"
    message = validate.first_problem(definitions(source("probe", declared)))
    assert message == (
        "swarm/roles/probe.yaml: the field 'name' is missing, and the file is named 'probe'."
    )


def test_two_declarations_with_no_name_are_not_duplicates_of_each_other():
    declared = "tools: Read\n"
    message = validate.first_problem(definitions(source("a", declared), source("b", declared)))
    assert "already declares" not in message


def test_an_omitted_tools_field_says_why_it_matters():
    declared = "name: qa\ndescription: Verifies.\nmodel: opus\neffort: high\n"
    message = validate.first_problem(definitions(source(declared=declared)))
    assert message == (
        "swarm/roles/qa.yaml: the field 'tools' is missing. A role with no tools line "
        "inherits every tool on Claude Code."
    )


def test_the_duplicate_check_runs_before_the_filename_check():
    # probe.yaml is wrong twice over: it claims qa's name, and that name is not its filename.
    message = validate.first_problem(definitions(source(), source("probe")))
    assert "already declares" in message


def test_the_filename_check_runs_before_the_tools_check():
    declared = "name: prober\n"
    message = validate.first_problem(definitions(source("probe", declared)))
    assert "'name'" in message and "'tools'" not in message


# --- compare ---------------------------------------------------------------------------------


def test_every_status_member_has_its_own_distinct_value():
    # Nothing reads a Status member's .value; what matters is that it stays unique. Two members
    # sharing a value would make Python's Enum alias them, so `Status.DIFFERS is Status.SAME`
    # would silently become true and every `is` comparison in compiler.py would misclassify.
    assert [member.value for member in Status] == [
        "same",
        "absent",
        "line endings",
        "differs",
    ]


def test_the_same_bytes_are_the_same():
    assert compare.status(CLAUDE_BYTES, CLAUDE_BYTES) is Status.SAME


def test_no_file_is_absent():
    assert compare.status(CLAUDE_BYTES, None) is Status.ABSENT


def test_the_other_line_ending_is_named_as_line_endings():
    assert compare.status(CLAUDE_BYTES, CLAUDE_BYTES.replace(b"\r\n", b"\n")) is Status.LINE_ENDINGS


def test_a_lone_carriage_return_counts_as_a_line_ending_difference():
    assert compare.status(CLAUDE_BYTES, CLAUDE_BYTES.replace(b"\r\n", b"\r")) is Status.LINE_ENDINGS


def test_a_content_difference_is_not_a_line_ending_difference():
    assert compare.status(CLAUDE_BYTES, CLAUDE_BYTES + b"Edited by hand.\r\n") is Status.DIFFERS


def test_a_byte_order_mark_on_a_target_is_a_difference():
    assert compare.status(CLAUDE_BYTES, b"\xef\xbb\xbf" + CLAUDE_BYTES) is Status.DIFFERS


def test_a_target_that_is_not_utf_8_differs_rather_than_raising():
    assert compare.status(CLAUDE_BYTES, b"\xff\xfe\x00") is Status.DIFFERS


# --- compiler.targets ------------------------------------------------------------------------


def test_each_role_produces_one_file_per_harness_sorted_by_path():
    problem, targets = compiler.targets([source(), source("coder", _named("coder"))])
    assert problem is None
    assert [target.path for target in targets] == [
        ".claude/agents/coder.md",
        ".claude/agents/qa.md",
        ".github/agents/coder.agent.md",
        ".github/agents/qa.agent.md",
    ]


def test_the_targets_carry_the_emitted_bytes():
    _, targets = compiler.targets([source()])
    assert {target.path: target.data for target in targets} == {
        ".claude/agents/qa.md": CLAUDE_BYTES,
        ".github/agents/qa.agent.md": GITHUB_BYTES,
    }


def test_a_target_is_named_by_the_declared_name():
    problem, targets = compiler.targets([source()])
    assert problem is None
    assert targets[0].path == ".claude/agents/qa.md"


def test_a_validation_problem_produces_no_targets_at_all():
    problem, targets = compiler.targets([source(), source("probe")])
    assert "already declares" in problem
    assert targets == []


def test_an_undecodable_source_produces_no_targets_at_all():
    problem, targets = compiler.targets([source(prompt=b"\xff\xfe")])
    assert problem == "swarm/roles/qa.md: the file is not valid UTF-8."
    assert targets == []


# --- compiler.outcome ------------------------------------------------------------------------


def test_an_outcome_is_frozen():
    outcome = compiler.outcome([], {}, set(), check=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.code = 99


CLAUDE = ".claude/agents"
GITHUB = ".github/agents"
BOTH = {CLAUDE, GITHUB}


def target(path=".claude/agents/qa.md", data=b"a"):
    return TargetFile(path=path, data=data)


def test_check_mode_reports_a_matching_file_as_unchanged_and_exits_zero():
    outcome = compiler.outcome([target()], {".claude/agents/qa.md": b"a"}, BOTH, check=True)
    assert outcome.lines == [".claude/agents/qa.md unchanged"]
    assert outcome.code == 0
    assert outcome.to_write == []


def test_check_mode_never_offers_anything_to_write():
    outcome = compiler.outcome([target()], {".claude/agents/qa.md": b"b"}, BOTH, check=True)
    assert outcome.to_write == []
    assert outcome.code == 1
    assert outcome.lines == [".claude/agents/qa.md out of date"]


def test_check_mode_names_a_line_ending_difference_as_one():
    on_disk = {".claude/agents/qa.md": CLAUDE_BYTES.replace(b"\r\n", b"\n")}
    outcome = compiler.outcome([target(data=CLAUDE_BYTES)], on_disk, BOTH, check=True)
    assert outcome.lines == [
        ".claude/agents/qa.md out of date - the line endings differ, nothing else"
    ]


def test_check_mode_treats_an_absent_file_in_a_present_directory_as_out_of_date():
    outcome = compiler.outcome([target()], {".claude/agents/qa.md": None}, BOTH, check=True)
    assert outcome.code == 1
    assert outcome.lines == [".claude/agents/qa.md out of date"]


def test_check_mode_says_nothing_about_a_destination_that_is_not_on_disk():
    targets = [target(), target(".github/agents/qa.agent.md")]
    on_disk = {".claude/agents/qa.md": b"a", ".github/agents/qa.agent.md": None}
    outcome = compiler.outcome(targets, on_disk, {CLAUDE}, check=True)
    assert outcome.lines == [".claude/agents/qa.md unchanged"]
    assert outcome.code == 0


def test_write_mode_reports_on_a_destination_that_is_not_on_disk_yet():
    targets = [target(".github/agents/qa.agent.md")]
    outcome = compiler.outcome(targets, {".github/agents/qa.agent.md": None}, set(), check=False)
    assert outcome.lines == [".github/agents/qa.agent.md written"]
    assert outcome.to_write == targets
    assert outcome.code == 0


def test_write_mode_leaves_a_matching_file_alone():
    outcome = compiler.outcome([target()], {".claude/agents/qa.md": b"a"}, BOTH, check=False)
    assert outcome.to_write == []
    assert outcome.lines == [".claude/agents/qa.md unchanged"]


def test_write_mode_rewrites_a_file_that_differs_only_in_its_line_endings():
    on_disk = {".claude/agents/qa.md": CLAUDE_BYTES.replace(b"\r\n", b"\n")}
    outcome = compiler.outcome([target(data=CLAUDE_BYTES)], on_disk, BOTH, check=False)
    assert [written.path for written in outcome.to_write] == [".claude/agents/qa.md"]


def test_one_out_of_date_file_among_many_fails_the_whole_check():
    targets = [target(), target(".claude/agents/coder.md", b"b")]
    on_disk = {".claude/agents/qa.md": b"a", ".claude/agents/coder.md": b"different"}
    outcome = compiler.outcome(targets, on_disk, BOTH, check=True)
    assert outcome.code == 1
    assert len(outcome.lines) == 2


# --- report ----------------------------------------------------------------------------------


def test_no_word_the_spec_coined_for_itself_reaches_the_terminal():
    printed = " ".join(
        [
            report.unchanged("a"),
            report.written("a"),
            report.out_of_date("a", True),
            report.out_of_date("a", False),
            report.duplicate_name("a", "b", "c"),
            report.name_mismatch("a", "b", "c"),
            report.missing_tools("a"),
            report.not_text("a"),
            report.unreadable("a", "b"),
        ]
    ).lower()
    for coined in ("stale", "lossy", "fidelity", "dropped field", "harness", "neutral"):
        assert coined not in printed


def test_no_output_narrates_what_the_github_emit_drops():
    printed = " ".join([report.unchanged("a"), report.written("a"), report.out_of_date("a", True)])
    assert "model" not in printed and "effort" not in printed


def test_a_report_line_leads_with_the_path():
    assert report.unchanged(".claude/agents/qa.md").startswith(".claude/agents/qa.md")
    assert report.written(".claude/agents/qa.md").startswith(".claude/agents/qa.md")
    assert report.out_of_date(".claude/agents/qa.md", False).startswith(".claude/agents/qa.md")
