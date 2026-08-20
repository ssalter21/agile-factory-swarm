"""Property tests for the whole reader: doctor answers or declines, always in printable ASCII.

Not collected by the gate's pytest run. testpaths is tests/, which recurses into this directory
and matches no test_*.py file, so these properties sit outside gate steps 1 to 5 (plan A1).
Run them by naming the file:

    .venv/Scripts/pytest.exe tests/property/prop_doctor.py -q

Stdlib only. One fixed seed, so any failure reproduces from this file alone.
"""

import random

from swarm_doctor import doctor, steps

SEED = 20260820
CASES = 300

# Declarations a person could really write, including ones carrying bytes doctor must escape.
VALUES = (
    "missing",
    "run it",
    "",
    "run\tit",
    "run \u2014 it",
    chr(34) + "run it  " + chr(34),
    "C:\\repos\\run.exe -q",
)

PATH_CHARS = "ab -" + chr(92) + "\t\u00e9"


def gate_bytes(rng):
    """A gate declaration, or bytes that are not one at all."""
    if rng.random() < 0.2:
        return bytes(rng.randrange(0, 256) for _ in range(rng.randrange(0, 60)))
    keys = [name for name in steps.ORDER if rng.random() < 0.85]
    body = "".join(f"  {key}: {rng.choice(VALUES)}\n" for key in keys)
    return ("steps:\n" + body).encode("utf-8")


def cases(count):
    rng = random.Random(SEED)
    for _ in range(count):
        looked_in = "C:" + "".join(
            rng.choice(PATH_CHARS) for _ in range(rng.randrange(1, 9))
        )
        yield gate_bytes(rng), looked_in


def test_doctor_either_answers_in_seven_lines_or_declines_in_one():
    for raw, looked_in in cases(CASES):
        report = doctor.run(["doctor"], raw, looked_in)
        assert report.exit_code in (doctor.EXIT_ANSWERED, doctor.EXIT_COULD_NOT_ANSWER)
        answered = report.exit_code == doctor.EXIT_ANSWERED
        assert answered is (len(report.lines) == 7)
        assert answered or len(report.lines) == 1


def test_nothing_doctor_prints_is_ever_outside_printable_ascii():
    for raw, looked_in in cases(CASES):
        for args in (["doctor"], [], ["frobnicate"]):
            for line in doctor.run(args, raw, looked_in).lines:
                assert all(" " <= char <= "~" for char in line), (raw, line)


def test_the_verdict_word_is_the_first_token_of_the_first_line_either_way():
    for raw, looked_in in cases(CASES):
        first = doctor.run(["doctor"], raw, looked_in).lines[0]
        assert first.split()[0] in ("INTACT", "DEGRADED", "UNUSABLE")


def test_an_invocation_doctor_refuses_never_reads_the_declaration():
    for raw, looked_in in cases(CASES):
        report = doctor.run(["doctor", "--json"], raw, looked_in)
        assert report.lines == ("usage: swarm doctor",)
        assert report.exit_code == doctor.EXIT_COULD_NOT_ANSWER
