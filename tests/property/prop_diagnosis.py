"""Property tests for diagnose: six rows, counts that conserve, last declaration wins.

Not collected by the gate's pytest run. testpaths is tests/, which recurses into this directory
and matches no test_*.py file, so these properties sit outside gate steps 1 to 5 (plan A1).
Run them by naming the file:

    .venv/Scripts/pytest.exe tests/property/prop_diagnosis.py -q

Stdlib only. One fixed seed, so any failure reproduces from this file alone.
"""

import random

from swarm_doctor import steps
from swarm_doctor.diagnosis import StepState, Verdict, diagnose

SEED = 20260820
CASES = 400

# Legal declarations, illegal ones, and near misses of the one word that means a debt.
VALUES = ("missing", "run it", "MISSING", "missing ", " missing", "", None, 6)

# Keys that are not one of the six, including one that differs only in case.
STRANGERS = ("Tests", "crap_max", "steps", "craps")


def declarations(count):
    """Random step mappings: any subset, any order, repeats, and keys that are not steps."""
    rng = random.Random(SEED)
    for _ in range(count):
        keys = [name for name in steps.ORDER if rng.random() < 0.8]
        keys += [rng.choice(steps.ORDER) for _ in range(rng.randrange(0, 3))]
        keys += [rng.choice(STRANGERS) for _ in range(rng.randrange(0, 2))]
        rng.shuffle(keys)
        yield tuple((key, rng.choice(VALUES)) for key in keys)


def test_always_six_rows_keyed_in_the_constitutions_order():
    for entries in declarations(CASES):
        assert tuple(row.key for row in diagnose(entries).rows) == steps.ORDER


def test_every_step_is_in_exactly_one_state_and_the_counts_conserve():
    for entries in declarations(CASES):
        d = diagnose(entries)
        declared = sum(1 for row in d.rows if row.state is StepState.DECLARED)
        assert declared + d.missing + d.defects == len(steps.ORDER)


def test_the_verdict_follows_the_missing_count_and_nothing_else():
    for entries in declarations(CASES):
        d = diagnose(entries)
        assert d.verdict is (Verdict.DEGRADED if d.missing else Verdict.INTACT)


def test_a_command_is_carried_by_a_declared_row_and_by_no_other():
    for entries in declarations(CASES):
        for row in diagnose(entries).rows:
            assert (row.command is not None) is (row.state is StepState.DECLARED)


def test_a_declared_command_is_the_declared_value_verbatim():
    for entries in declarations(CASES):
        last = dict(entries)
        for row in diagnose(entries).rows:
            if row.state is StepState.DECLARED:
                assert row.command == last[row.key]


def test_a_repeated_key_is_diagnosed_from_its_last_declaration():
    for entries in declarations(CASES):
        last = dict(entries)
        for row in diagnose(entries).rows:
            alone = diagnose(((row.key, last[row.key]),) if row.key in last else ())
            assert row == next(r for r in alone.rows if r.key == row.key)


def test_the_breaches_are_the_missing_floor_steps_in_the_floors_own_order():
    for entries in declarations(CASES):
        d = diagnose(entries)
        state = {row.key: row.state for row in d.rows}
        assert d.floor_breaches == tuple(
            key for key in steps.FLOOR if state[key] is StepState.MISSING
        )
