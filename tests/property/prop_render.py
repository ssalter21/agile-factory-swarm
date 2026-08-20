"""Property tests for render: printable ASCII out, whatever came in.

Not collected by the gate's pytest run. testpaths is tests/, which recurses into this directory
and matches no test_*.py file, so these properties sit outside gate steps 1 to 5 (plan A1).
Run them by naming the file:

    .venv/Scripts/pytest.exe tests/property/prop_render.py -q

Stdlib only. One fixed seed, so any failure reproduces from this file alone.
"""

import random

from swarm_doctor import render, steps
from swarm_doctor.diagnosis import Unreadable, diagnose

SEED = 20260820
CASES = 300

# Every kind of character a gate declaration or a Windows path can hand doctor.
POOL = (
    [chr(code) for code in range(0x00, 0x80)]
    + ["\\", "\t", "\n", "\r", "\x1b", "\x7f", " ", "#", chr(34)]
    + ["\u00e9", "\u2014", "\u200b", "\ufffd", "\U0001f600", "\U0010ffff"]
    + ["\u0100", "\uffff", "\U00010000"]  # the widths of the escape, at their edges
)


def texts(count):
    """Random outside text: a command a gate file declares, or a directory doctor looked in."""
    rng = random.Random(SEED)
    for _ in range(count):
        yield "".join(rng.choice(POOL) for _ in range(rng.randrange(1, 14)))


def declaring(command):
    return tuple(
        (name, command if name == "tests" else f"run {name}") for name in steps.ORDER
    )


def row_for(command):
    return render.diagnosis_lines(diagnose(declaring(command)))[1]


# The key column and the state column are the same width in every all-declared report, so a
# one-character command locates where the command starts on the row.
_COMMAND_AT = len(row_for("x")) - 1


def escaped(text):
    """What render prints in place of `text`, taken off the end of a declared row."""
    return row_for(text)[_COMMAND_AT:]


def test_every_character_of_every_line_is_printable_ascii():
    for text in texts(CASES):
        lines = render.diagnosis_lines(diagnose(declaring(text)))
        lines += (render.unreadable_line(Unreadable.ABSENT, text),)
        lines += (render.unreadable_line(Unreadable.UNPARSEABLE, text),)
        for line in lines:
            assert all(" " <= char <= "~" for char in line), (text, line)


def test_every_character_is_rendered_in_place_and_none_is_dropped():
    for text in texts(CASES):
        assert escaped(text) == "".join(escaped(char) for char in text), text


def test_a_printable_character_is_itself_and_any_other_is_a_backslash_escape():
    for char in POOL:
        printed = escaped(char)
        if " " <= char <= "~":
            assert printed == char, char
        else:
            assert printed.startswith("\\") and len(printed) > 1, char


def test_a_looked_in_directory_is_escaped_exactly_as_a_command_is():
    for text in texts(CASES):
        line = render.unreadable_line(Unreadable.ABSENT, text)
        assert line.endswith(f"{escaped(text)}."), text


def test_a_report_is_always_a_summary_and_six_rows_on_seven_physical_lines():
    for text in texts(CASES):
        lines = render.diagnosis_lines(diagnose(declaring(text)))
        assert len(lines) == 7
        assert all("\n" not in line for line in lines)
