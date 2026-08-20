import pytest

from swarm_doctor import doctor
from swarm_doctor.diagnosis import Verdict

LOOKED_IN = r"C:\repos\a-project"

DECLARED_AND_MISSING = b"""shell: pwsh

steps:
  tests:       "run the suite"
  coverage:    "run the suite; report --fail-under=0"
  duplication: missing
  mutation:    missing
  crap:        missing
  acceptance:  missing
"""

ALL_DECLARED = b"""steps:
  tests: run-tests
  coverage: run-coverage
  duplication: run-duplication
  mutation: run-mutation
  crap: run-crap
  acceptance: run-acceptance
"""


def report_for(raw):
    return doctor.run(["doctor"], raw, LOOKED_IN)


def test_the_two_exit_codes_are_zero_and_two():
    assert doctor.EXIT_ANSWERED == 0
    assert doctor.EXIT_COULD_NOT_ANSWER == 2


def test_a_gate_with_missing_steps_is_still_an_answer():
    report = report_for(DECLARED_AND_MISSING)
    assert report.exit_code == doctor.EXIT_ANSWERED
    assert report.lines[0].startswith(Verdict.DEGRADED.value)
    assert len(report.lines) == 7


def test_an_intact_gate_answers_with_the_intact_verdict():
    report = report_for(ALL_DECLARED)
    assert report.exit_code == doctor.EXIT_ANSWERED
    assert report.lines[0].startswith(Verdict.INTACT.value)


def test_a_defective_step_is_a_row_state_and_still_an_answer():
    report = report_for(b"steps:\n  tests: run-tests\n  crap:\n")
    assert report.exit_code == doctor.EXIT_ANSWERED
    assert len(report.lines) == 7
    assert "defect" in report.lines[0]


def test_a_floor_breach_is_still_an_answer():
    report = report_for(b"steps:\n  tests: missing\n")
    assert report.exit_code == doctor.EXIT_ANSWERED
    assert "always apply" in report.lines[0]


def test_an_absent_declaration_is_one_line_and_no_answer():
    report = doctor.run(["doctor"], None, LOOKED_IN)
    assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert len(report.lines) == 1
    assert report.lines[0].startswith(Verdict.UNUSABLE.value)
    assert "no gate declaration found" in report.lines[0]


def test_a_declaration_that_will_not_parse_is_one_line_and_no_answer():
    report = report_for(b"shell: pwsh\n")
    assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert len(report.lines) == 1
    assert "could not be parsed" in report.lines[0]


def test_bytes_that_are_not_text_are_a_parse_failure_not_a_crash():
    report = report_for(b"steps:\n  crap: \xff\xfe\n")
    assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert "could not be parsed" in report.lines[0]


@pytest.mark.parametrize(
    "args",
    [[], ["doctor", "extra"], ["--help"], ["Doctor"], ["frobnicate"], ["doctor", "--json"]],
)
def test_any_invocation_other_than_doctor_is_one_usage_line(args):
    report = doctor.run(args, DECLARED_AND_MISSING, LOOKED_IN)
    assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert report.lines == ("usage: swarm doctor",)


def test_the_usage_line_wins_before_the_file_is_even_looked_at():
    assert doctor.run([], None, LOOKED_IN).lines == ("usage: swarm doctor",)
