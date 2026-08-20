from swarm_doctor import render, steps
from swarm_doctor.diagnosis import Unreadable, Verdict, diagnose

# Words that would say a step ran, passed or works. No prose doctor owns may contain one.
FORBIDDEN = ("ok", "pass", "fail", "green", "healthy", "good", "tick", "check")

# Any absolute directory. Doctor is told where it looked; it never goes there. Every character
# of it is printable ASCII, so doctor prints it back unchanged, backslashes and all (I-8).
LOOKED_IN = r"C:\repos\a-project"


def entries_with(**overrides):
    """The all-declared mapping with named steps replaced, and None meaning an absent key."""
    return tuple(
        (name, overrides.get(name, f"run-{name}"))
        for name in steps.ORDER
        if overrides.get(name, "") is not None
    )


def lines_for(**overrides):
    return render.diagnosis_lines(diagnose(entries_with(**overrides)))


def test_a_summary_line_then_exactly_six_rows():
    lines = lines_for()
    assert len(lines) == 7


def test_the_verdict_word_is_the_first_token_of_the_first_line():
    assert lines_for()[0].split()[0] == Verdict.INTACT.value
    assert lines_for(crap="missing")[0].split()[0] == Verdict.DEGRADED.value


def test_the_first_line_counts_the_missing_steps_out_of_six():
    summary = lines_for(
        duplication="missing", mutation="missing", crap="missing", acceptance="missing"
    )[0]
    assert "4 of 6" in summary


def test_the_first_line_says_a_run_here_would_be_a_degraded_run():
    assert "a run here would be a degraded run" in lines_for(crap="missing")[0]


def test_nothing_is_said_about_a_degraded_run_when_no_step_is_missing():
    assert "degraded" not in lines_for()[0].lower()


def test_the_first_line_counts_defects_beside_the_missing_count():
    assert "1 is a defect" in lines_for(crap=None)[0]
    assert "2 are defects" in lines_for(crap=None, mutation="")[0]


def test_the_first_line_carries_no_defect_count_when_there_is_no_defect():
    assert "defect" not in lines_for(crap="missing")[0]


def test_the_summary_is_one_physical_line_ending_in_a_full_stop():
    summary = lines_for(tests="missing", crap=None)[0]
    assert "\n" not in summary
    assert summary.endswith(".")


def test_a_floor_breach_is_named_on_the_first_line_with_the_rule_it_breaches():
    summary = lines_for(tests="missing")[0]
    assert "tests" in summary
    assert "steps 1 and 2 always apply" in summary


def test_both_floor_steps_are_named_when_both_are_missing():
    summary = lines_for(tests="missing", coverage="missing")[0]
    assert "tests and coverage" in summary


def test_no_floor_rule_is_stated_when_the_floor_is_intact():
    assert "always apply" not in lines_for(acceptance="missing")[0]


def test_each_row_carries_the_step_key_and_its_state():
    rows = lines_for(crap="missing", mutation=None)[1:]
    assert rows[0].split() == ["tests", "declared", "run-tests"]
    assert rows[3].split() == ["mutation", "defect"]
    assert rows[4].split() == ["crap", "missing"]


def test_the_rows_are_indented_under_the_summary_and_their_states_line_up():
    lines = lines_for(coverage="missing", crap=None)
    assert not lines[0].startswith(" ")
    assert all(row.startswith(" ") for row in lines[1:])
    assert len({row.index(row.split()[1]) for row in lines[1:]}) == 1


def test_rows_appear_in_the_constitutions_order():
    keys = [row.split()[0] for row in lines_for()[1:]]
    assert keys == list(steps.ORDER)


def test_a_declared_row_shows_its_command_whole_and_untruncated():
    command = "run the suite; report --fail-under=0 --with-a-very-long-tail-of-arguments"
    assert lines_for(coverage=command)[2].endswith(command)


def test_a_missing_row_shows_no_command_and_no_trailing_space():
    row = lines_for(crap="missing")[5]
    assert row == row.rstrip()
    assert row.split()[1:] == ["missing"]


def test_no_word_in_doctors_own_prose_says_a_step_ran_or_works():
    text = "\n".join(lines_for(crap="missing", mutation=None, tests="missing")).lower()
    for word in FORBIDDEN:
        assert word not in text


def test_every_character_is_plain_printable_ascii():
    for line in lines_for(crap="missing", mutation=None):
        assert all(" " <= char <= "~" for char in line)


def test_the_absent_line_names_the_file_and_the_directory():
    line = render.unreadable_line(Unreadable.ABSENT, LOOKED_IN)
    assert line.split()[0] == Verdict.UNUSABLE.value
    assert ".swarm/gate.yaml" in line
    assert LOOKED_IN in line
    assert "no gate declaration found" in line


def test_the_absent_line_makes_no_claim_about_initiation():
    line = render.unreadable_line(Unreadable.ABSENT, LOOKED_IN).lower()
    assert "initiat" not in line
    assert "parse" not in line


def test_the_unparseable_line_says_the_file_was_there_and_would_not_parse():
    line = render.unreadable_line(Unreadable.UNPARSEABLE, LOOKED_IN)
    assert line.split()[0] == Verdict.UNUSABLE.value
    assert ".swarm/gate.yaml" in line
    assert LOOKED_IN in line
    assert "could not be parsed" in line
    assert "not found" not in line


def test_the_usage_line_refuses_without_giving_a_verdict():
    line = render.usage_line()
    assert line.startswith("usage:")
    assert "swarm doctor" in line
    for verdict in Verdict:
        assert verdict.value not in line


def test_a_control_character_in_a_declared_command_is_escaped_and_never_emitted():
    row = lines_for(tests="run\tit\x1b[0m")[1]
    assert row.endswith(r"run\tit\x1b[0m")
    assert "\t" not in row
    assert "\x1b" not in row


def test_a_non_ascii_character_in_a_declared_command_is_escaped_and_never_emitted():
    row = lines_for(tests="nai\u00e9ve \u2014 \U0001f600")[1]
    assert row.endswith(r"nai\xe9ve \u2014 \U0001f600")


def test_a_backslash_is_printed_as_itself_so_a_windows_path_reads_as_observed():
    row = lines_for(tests=r"cd C:\repos; run \t")[1]
    assert row.endswith(r"cd C:\repos; run \t")


def test_an_escaped_command_still_carries_every_character_it_declared():
    row = lines_for(tests="run\tit \u2014 C:\\dir \x00")[1]
    assert row.endswith(r"run\tit \u2014 C:\dir \x00")


def test_a_declared_command_keeps_the_trailing_space_it_declared():
    assert lines_for(tests="run it  ")[1].endswith("run it  ")


def test_the_looked_in_directory_is_escaped_the_same_way():
    line = render.unreadable_line(Unreadable.ABSENT, "C:\\dr\tnone\u00e9")
    assert line == (
        r"UNUSABLE no gate declaration found at .swarm/gate.yaml, under C:\dr\tnone\xe9."
    )


def test_every_character_stays_printable_ascii_whatever_the_declaration_carried():
    lines = lines_for(tests="run\tit", coverage="\x00\x7f\u2014\U0001f600")
    for line in lines:
        assert all(" " <= char <= "~" for char in line)


def test_the_ends_of_the_printable_range_are_left_exactly_as_they_are():
    command = " !#$%&()*+,-./:;<=>?@[]^_{|}~ "
    assert lines_for(tests=command)[1].endswith(command)


def test_each_escape_carries_the_hex_digits_its_width_calls_for():
    command = "\x00 \u0100 \U00010000 \U0010ffff"
    assert lines_for(tests=command)[1].endswith(r"\x00 \u0100 \U00010000 \U0010ffff")


def test_the_summary_reads_exactly_this_when_every_step_is_declared():
    assert lines_for()[0] == "INTACT 0 of 6 gate steps are missing."


def test_the_summary_reads_exactly_this_when_two_steps_are_defective():
    assert lines_for(crap=None, mutation="")[0] == (
        "INTACT 0 of 6 gate steps are missing and 2 are defects."
    )


def test_the_summary_reads_exactly_this_for_one_missing_floor_step_and_one_defect():
    assert lines_for(tests="missing", crap=None)[0] == (
        "DEGRADED 1 of 6 gate steps are missing and 1 is a defect; "
        "the floor step tests is missing, and steps 1 and 2 always apply; "
        "a run here would be a degraded run."
    )


def test_the_summary_reads_exactly_this_when_both_floor_steps_are_missing():
    summary = lines_for(
        tests="missing", coverage="missing", crap="missing", mutation=None
    )[0]
    assert summary == (
        "DEGRADED 3 of 6 gate steps are missing and 1 is a defect; "
        "the floor steps tests and coverage are missing, and steps 1 and 2 always apply; "
        "a run here would be a degraded run."
    )


def test_a_whole_report_reads_exactly_like_this():
    assert lines_for(crap="missing", mutation=None) == (
        "DEGRADED 1 of 6 gate steps are missing and 1 is a defect; "
        "a run here would be a degraded run.",
        "  tests        declared  run-tests",
        "  coverage     declared  run-coverage",
        "  duplication  declared  run-duplication",
        "  mutation     defect",
        "  crap         missing",
        "  acceptance   declared  run-acceptance",
    )


def test_the_unparseable_line_reads_exactly_this():
    assert render.unreadable_line(Unreadable.UNPARSEABLE, LOOKED_IN) == (
        "UNUSABLE the gate declaration at .swarm/gate.yaml could not be parsed, "
        f"under {LOOKED_IN}."
    )


def test_a_newline_or_a_carriage_return_in_a_command_is_named_by_its_own_escape():
    assert lines_for(tests="run\r\nit")[1].endswith(r"run\r\nit")


def test_the_top_of_each_escape_width_is_escaped_at_that_width():
    assert lines_for(tests="\xff \uffff")[1].endswith(r"\xff \uffff")
