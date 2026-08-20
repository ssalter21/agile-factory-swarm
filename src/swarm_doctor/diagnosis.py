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
    missing = _counted(rows, StepState.MISSING)
    defects = _counted(rows, StepState.DEFECT)
    return Diagnosis(rows, missing, defects, _floor_breaches(rows), _verdict(missing))


def _counted(rows: tuple[StepRow, ...], state: StepState) -> int:
    """How many of the rows are in that state."""
    return sum(1 for row in rows if row.state is state)


def _floor_breaches(rows: tuple[StepRow, ...]) -> tuple[str, ...]:
    """The floor steps declared missing, named in the floor's own order."""
    missing = {row.key for row in rows if row.state is StepState.MISSING}
    return tuple(key for key in steps.FLOOR if key in missing)


def _verdict(missing: int) -> Verdict:
    """DEGRADED for one debt or more, INTACT for none. A defect never moves it (I-1)."""
    return Verdict.DEGRADED if missing else Verdict.INTACT


def _row(name: str, value: str | None) -> StepRow:
    """One step's row. An absent key arrives here as None and is a defect like any other."""
    if not isinstance(value, str) or not value:
        return StepRow(name, StepState.DEFECT, None)
    if value == MISSING_WORD:
        return StepRow(name, StepState.MISSING, None)
    return StepRow(name, StepState.DECLARED, value)
