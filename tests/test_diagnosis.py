from swarm_doctor import steps
from swarm_doctor.diagnosis import StepState, Verdict, diagnose

ALL_DECLARED = tuple((name, f"run {name}") for name in steps.ORDER)


def entries_with(**overrides):
    """The all-declared mapping with named steps replaced, and None meaning an absent key."""
    return tuple(
        (name, overrides.get(name, f"run {name}"))
        for name in steps.ORDER
        if overrides.get(name, "") is not None
    )


def state_of(d, key):
    return next(row.state for row in d.rows if row.key == key)


def test_all_six_declared_is_intact_with_nothing_owed():
    d = diagnose(ALL_DECLARED)
    assert d.verdict is Verdict.INTACT
    assert d.missing == 0
    assert d.defects == 0
    assert d.floor_breaches == ()
    assert all(row.state is StepState.DECLARED for row in d.rows)


def test_a_declared_row_carries_its_command_whole():
    command = "run the suite; report --fail-under=0 --and-then-some"
    d = diagnose(entries_with(coverage=command))
    assert next(row.command for row in d.rows if row.key == "coverage") == command


def test_the_literal_word_missing_is_a_debt_and_carries_no_command():
    d = diagnose(entries_with(crap="missing"))
    row = next(row for row in d.rows if row.key == "crap")
    assert row.state is StepState.MISSING
    assert row.command is None


def test_a_command_that_merely_contains_the_word_missing_is_declared():
    d = diagnose(entries_with(crap="report-missing-things"))
    assert state_of(d, "crap") is StepState.DECLARED


def test_a_value_that_is_no_scalar_is_a_defect():
    d = diagnose(entries_with(mutation=""))
    assert state_of(d, "mutation") is StepState.DEFECT


def test_a_value_that_is_not_a_string_is_a_defect():
    d = diagnose((("tests", 6),) + ALL_DECLARED[1:])
    assert state_of(d, "tests") is StepState.DEFECT


def test_an_absent_key_is_a_defect_keyed_with_the_constitutions_spelling():
    d = diagnose(entries_with(crap=None))
    row = next(row for row in d.rows if row.key == "crap")
    assert row.state is StepState.DEFECT
    assert row.command is None


def test_a_defect_is_never_rendered_as_declared_or_counted_as_missing():
    d = diagnose(entries_with(crap=None, mutation=""))
    assert d.defects == 2
    assert d.missing == 0


def test_key_matching_is_exact_and_case_sensitive():
    d = diagnose(entries_with(crap=None) + (("CRAP", "missing"),))
    assert state_of(d, "crap") is StepState.DEFECT
    assert [row.key for row in d.rows] == list(steps.ORDER)


def test_six_rows_in_the_constitutions_order_whatever_order_they_arrive_in():
    d = diagnose(tuple(reversed(ALL_DECLARED)))
    assert tuple(row.key for row in d.rows) == steps.ORDER


def test_one_missing_step_makes_the_verdict_degraded_and_counts_it():
    d = diagnose(entries_with(crap="missing"))
    assert d.verdict is Verdict.DEGRADED
    assert d.missing == 1


def test_this_repos_own_state_counts_four_missing():
    d = diagnose(
        entries_with(
            duplication="missing", mutation="missing", crap="missing", acceptance="missing"
        )
    )
    assert d.verdict is Verdict.DEGRADED
    assert d.missing == 4
    assert d.defects == 0


def test_a_defect_alone_does_not_move_the_verdict_off_intact():
    d = diagnose(entries_with(crap=None))
    assert d.verdict is Verdict.INTACT


def test_unusable_is_never_a_verdict_about_a_readable_declaration():
    verdicts = {
        diagnose(entries_with(**case)).verdict
        for case in ({}, {"crap": "missing"}, {"crap": None}, {"tests": "missing"})
    }
    assert Verdict.UNUSABLE not in verdicts


def test_a_missing_floor_step_is_named_as_a_breach():
    d = diagnose(entries_with(tests="missing"))
    assert d.floor_breaches == ("tests",)


def test_both_floor_steps_are_named_in_the_constitutions_order():
    d = diagnose(entries_with(coverage="missing", tests="missing"))
    assert d.floor_breaches == ("tests", "coverage")


def test_a_missing_step_outside_the_floor_is_no_breach():
    d = diagnose(entries_with(acceptance="missing"))
    assert d.floor_breaches == ()


def test_a_defective_floor_step_is_not_counted_as_a_breach():
    d = diagnose(entries_with(tests=None))
    assert d.floor_breaches == ()
