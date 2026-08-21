"""What the file on disk is, relative to the file the compile produced.

Four answers, and the third is why this module exists at all: a checkout configured for the other
line ending produces twelve files that differ in every line and in nothing that matters, and the
developer deserves to be told that rather than left to diff them.
"""

import enum

from rolecompile import text


class Status(enum.Enum):
    """The four things an agent file on disk can be."""

    SAME = "same"
    ABSENT = "absent"
    LINE_ENDINGS = "line endings"
    DIFFERS = "differs"


def status(compiled, on_disk):
    """`on_disk` is the bytes there, or None where there is no file."""
    if on_disk is None:
        return Status.ABSENT
    if on_disk == compiled:
        return Status.SAME
    theirs = text.decode_target(on_disk)
    if theirs is None:
        return Status.DIFFERS
    if text.lines(text.decode_target(compiled)) == text.lines(theirs):
        return Status.LINE_ENDINGS
    return Status.DIFFERS
