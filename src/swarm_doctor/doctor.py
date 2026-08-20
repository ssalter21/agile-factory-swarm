"""Composing a gate declaration's bytes into lines plus an exit code."""

from collections.abc import Sequence
from dataclasses import dataclass

from swarm_doctor import diagnosis, gate, render
from swarm_doctor.diagnosis import Unreadable

EXIT_ANSWERED = 0
EXIT_COULD_NOT_ANSWER = 2

COMMAND = "doctor"


@dataclass(frozen=True)
class Report:
    lines: tuple[str, ...]
    exit_code: int


def run(args: Sequence[str], gate_bytes: bytes | None, looked_in: str) -> Report:
    """Doctor's whole behaviour: what to print, and whether it answered."""
    if tuple(args) != (COMMAND,):
        return Report((render.usage_line(),), EXIT_COULD_NOT_ANSWER)
    if gate_bytes is None:
        return _unreadable(Unreadable.ABSENT, looked_in)
    entries = gate.parse_steps(gate_bytes)
    if entries is None:
        return _unreadable(Unreadable.UNPARSEABLE, looked_in)
    return Report(render.diagnosis_lines(diagnosis.diagnose(entries)), EXIT_ANSWERED)


def _unreadable(reason: Unreadable, looked_in: str) -> Report:
    return Report((render.unreadable_line(reason, looked_in),), EXIT_COULD_NOT_ANSWER)
