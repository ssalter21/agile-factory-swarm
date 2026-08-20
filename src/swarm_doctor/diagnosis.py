"""Classifying each step of a gate declaration, counting, and choosing the verdict."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from swarm_doctor import steps

MISSING_WORD = "missing"


class StepState(Enum):
    """What a step's declaration is, as a fact about the file and nothing more."""

    DECLARED = "declared"
    MISSING = "missing"
    DEFECT = "defect"


class Verdict(Enum):
    """Doctor's single conclusion about a gate declaration."""

    INTACT = "INTACT"
    DEGRADED = "DEGRADED"
    UNUSABLE = "UNUSABLE"


class Unreadable(Enum):
    """The two ways doctor is left with no declaration to diagnose."""

    ABSENT = "absent"
    UNPARSEABLE = "unparseable"


@dataclass(frozen=True)
class StepRow:
    key: str
    state: StepState
    command: str | None


@dataclass(frozen=True)
class Diagnosis:
    rows: tuple[StepRow, ...]
    missing: int
    defects: int
    floor_breaches: tuple[str, ...]
    verdict: Verdict


def diagnose(entries: Sequence[tuple[str, str | None]]) -> Diagnosis:
    """Six rows in the constitution's order, whatever order the entries arrive in."""
    values = dict(entries)
    rows = tuple(_row(name, values.get(name)) for name in steps.ORDER)
    missing = sum(1 for row in rows if row.state is StepState.MISSING)
    defects = sum(1 for row in rows if row.state is StepState.DEFECT)
    floor_breaches = tuple(
        row.key
        for row in rows
        if row.key in steps.FLOOR and row.state is StepState.MISSING
    )
    verdict = Verdict.DEGRADED if missing else Verdict.INTACT
    return Diagnosis(rows, missing, defects, floor_breaches, verdict)


def _row(name: str, value: str | None) -> StepRow:
    """One step's row. An absent key arrives here as None and is a defect like any other."""
    if not isinstance(value, str) or not value:
        return StepRow(name, StepState.DEFECT, None)
    if value == MISSING_WORD:
        return StepRow(name, StepState.MISSING, None)
    return StepRow(name, StepState.DECLARED, value)
