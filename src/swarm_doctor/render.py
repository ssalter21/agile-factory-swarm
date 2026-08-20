"""Every word doctor prints. It formats what it is given and computes nothing."""

from swarm_doctor import gate
from swarm_doctor.diagnosis import Diagnosis, StepRow, StepState, Unreadable, Verdict

_ROW_INDENT = "  "
_COLUMN_GAP = "  "
_STATE_WIDTH = max(len(state.value) for state in StepState)
_CLAUSE_GAP = "; "

_LOWEST_PRINTABLE = " "
_HIGHEST_PRINTABLE = "~"
_NAMED_ESCAPES = {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}


def diagnosis_lines(d: Diagnosis) -> tuple[str, ...]:
    """The summary line, then one line per step row."""
    key_width = max(len(row.key) for row in d.rows)
    return (_summary_line(d),) + tuple(_row_line(row, key_width) for row in d.rows)


def unreadable_line(reason: Unreadable, looked_in: str) -> str:
    """The one line doctor prints when it has no declaration to diagnose."""
    if reason is Unreadable.ABSENT:
        detail = f"no gate declaration found at {gate.GATE_RELATIVE_PATH}"
    else:
        detail = f"the gate declaration at {gate.GATE_RELATIVE_PATH} could not be parsed"
    return f"{Verdict.UNUSABLE.value} {detail}, under {_printable(looked_in)}."


def usage_line() -> str:
    """The one line doctor prints for any invocation other than `swarm doctor`."""
    return "usage: swarm doctor"


def _summary_line(d: Diagnosis) -> str:
    clauses = [_counts(d)]
    if d.floor_breaches:
        clauses.append(_floor(d.floor_breaches))
    if d.missing:
        clauses.append("a run here would be a degraded run")
    return _CLAUSE_GAP.join(clauses) + "."


def _counts(d: Diagnosis) -> str:
    counted = f"{d.verdict.value} {d.missing} of {len(d.rows)} gate steps are missing"
    if not d.defects:
        return counted
    if d.defects == 1:
        return f"{counted} and 1 is a defect"
    return f"{counted} and {d.defects} are defects"


def _floor(breaches: tuple[str, ...]) -> str:
    named = " and ".join(breaches)
    if len(breaches) == 1:
        return f"the floor step {named} is missing, and steps 1 and 2 always apply"
    return f"the floor steps {named} are missing, and steps 1 and 2 always apply"


def _row_line(row: StepRow, key_width: int) -> str:
    prefix = _ROW_INDENT + row.key.ljust(key_width) + _COLUMN_GAP
    if row.command is None:
        return prefix + row.state.value
    state = row.state.value.ljust(_STATE_WIDTH)
    return prefix + state + _COLUMN_GAP + _printable(row.command)


def _printable(text: str) -> str:
    """Text from outside doctor, as printable ASCII with nothing dropped or shortened."""
    return "".join(_escaped(char) for char in text)


def _escaped(char: str) -> str:
    """One character as itself, or as the backslash escape that stands for it."""
    if char in _NAMED_ESCAPES:
        return _NAMED_ESCAPES[char]
    if _LOWEST_PRINTABLE <= char <= _HIGHEST_PRINTABLE:
        return char
    code = ord(char)
    if code < 0x100:
        return f"\\x{code:02x}"
    if code < 0x10000:
        return f"\\u{code:04x}"
    return f"\\U{code:08x}"
