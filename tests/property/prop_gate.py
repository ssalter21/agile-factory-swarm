"""Property tests for parse_steps: a block round trips, and no bytes make it raise.

Not collected by the gate's pytest run. testpaths is tests/, which recurses into this directory
and matches no test_*.py file, so these properties sit outside gate steps 1 to 5 (plan A1).
Run them by naming the file:

    .venv/Scripts/pytest.exe tests/property/prop_gate.py -q

Stdlib only. One fixed seed, so any failure reproduces from this file alone.
"""

import random

from swarm_doctor import gate, steps

SEED = 20260820
CASES = 300

KEYS = steps.ORDER + ("extra", "crap_max")

# Values inside the subset gate.py documents: no comment marker, no leading quote or bracket.
COMMANDS = (
    "missing",
    "run it",
    "run --fail-under=0",
    "pwsh -c run it; report",
    "C:/repos/x.exe -q",
)

# Lines of every shape the parser has an opinion about.
FRAGMENTS = (
    "steps:",
    "steps:   # the six",
    "  tests: run it",
    "  crap:",
    "    nested: value",
    "  - a list item",
    "  : orphaned",
    "",
    "# a comment",
    "defaults:",
    "  crap_max: 6",
    chr(9) + "tests: run it",
)


def blocks(count):
    """A well-formed steps block, with random indent, spacing, keys and repeats."""
    rng = random.Random(SEED)
    for _ in range(count):
        pairs = tuple(
            (rng.choice(KEYS), rng.choice(COMMANDS))
            for _ in range(rng.randrange(1, 7))
        )
        indent = " " * rng.randrange(1, 5)
        gap = " " * rng.randrange(1, 4)
        text = "steps:\n" + "".join(f"{indent}{k}:{gap}{v}\n" for k, v in pairs)
        yield text, pairs


def test_a_well_formed_block_round_trips_key_for_key_and_value_for_value():
    for text, pairs in blocks(CASES):
        assert gate.parse_steps(text.encode("utf-8")) == pairs


def test_what_follows_the_block_at_column_zero_changes_nothing_it_read():
    tail = "defaults:\n  crap_max: 6\nshell: pwsh\n"
    for text, pairs in blocks(CASES):
        assert gate.parse_steps((text + tail).encode("utf-8")) == pairs


def test_any_arrangement_of_those_lines_yields_entries_or_nothing_and_never_raises():
    rng = random.Random(SEED)
    for _ in range(CASES):
        lines = [rng.choice(FRAGMENTS) for _ in range(rng.randrange(0, 9))]
        assert_entries(gate.parse_steps("\n".join(lines).encode("utf-8")))


def test_arbitrary_bytes_yield_entries_or_nothing_and_never_raise():
    rng = random.Random(SEED)
    for _ in range(CASES):
        raw = bytes(rng.randrange(0, 256) for _ in range(rng.randrange(0, 80)))
        assert_entries(gate.parse_steps(raw))
        assert_entries(gate.parse_steps(b"steps:\n  tests: " + raw))


def assert_entries(entries):
    """Whatever came back is None, or pairs of a non-empty key and a scalar or None."""
    assert entries is None or all(
        isinstance(key, str) and key and (value is None or isinstance(value, str))
        for key, value in entries
    )
