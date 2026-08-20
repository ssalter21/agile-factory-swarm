import dataclasses

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


def test_an_empty_file_is_a_parse_failure_and_not_an_absent_declaration():
    report = report_for(b"")
    assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert "could not be parsed" in report.lines[0]
    assert "no gate declaration found" not in report.lines[0]


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


def test_a_report_cannot_be_altered_after_it_is_made():
    report = report_for(ALL_DECLARED)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.exit_code = doctor.EXIT_COULD_NOT_ANSWER


# The declaration this repo actually carries, verbatim. Acceptance criteria are executed through
# the command line by a QA pass (gate step 6 is `missing`, so there is no runner for the Gherkin);
# these pin the same criteria as ordinary tests so they survive the run directory (section 11).
THIS_REPOS_GATE = b"""# The quality gate for this repo. See swarm/constitution.md section 2.

shell: pwsh

steps:
  tests:       ".venv/Scripts/pytest.exe -q"
  coverage:    ".venv/Scripts/coverage.exe run -m pytest -q; .venv/Scripts/coverage.exe report --fail-under=0"
  duplication: missing
  mutation:    missing
  crap:        missing
  acceptance:  missing

defaults:
  crap_max: 6
"""

# Words and glyphs that would say a step ran, passed or works (R11).
CLAIMS_A_STEP_WORKS = ("ok", "pass", "green", "healthy", "good", "fine", "works", "success")


def test_this_repos_own_declaration_reads_exactly_like_this():
    assert report_for(THIS_REPOS_GATE).lines == (
        "DEGRADED 4 of 6 gate steps are missing; a run here would be a degraded run.",
        "  tests        declared  .venv/Scripts/pytest.exe -q",
        "  coverage     declared  .venv/Scripts/coverage.exe run -m pytest -q;"
        " .venv/Scripts/coverage.exe report --fail-under=0",
        "  duplication  missing",
        "  mutation     missing",
        "  crap         missing",
        "  acceptance   missing",
    )


def test_this_repos_own_declaration_answers_at_the_answered_exit_code():
    assert report_for(THIS_REPOS_GATE).exit_code == doctor.EXIT_ANSWERED


def test_nothing_in_this_repos_diagnosis_says_a_step_ran_or_works():
    text = "\n".join(report_for(THIS_REPOS_GATE).lines).lower()
    for word in CLAIMS_A_STEP_WORKS:
        assert word not in text
    assert all(" " <= char <= "~" for char in text.replace("\n", ""))


def test_the_coverage_row_shows_the_threshold_that_cannot_fail():
    coverage_row = report_for(THIS_REPOS_GATE).lines[2]
    assert coverage_row.endswith("--fail-under=0")
