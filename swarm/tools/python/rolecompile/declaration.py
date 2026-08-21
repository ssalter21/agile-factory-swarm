"""Reading one role definition: the fields of its declaration, and its prompt.

The declarations are written in the flat subset of YAML that a `key: value` per line covers, and
that subset is read by hand. A real YAML parser would be a third-party dependency, and the swarm's
tools install nothing. It would also fold a long value onto a second line on the way out, which
the emitted files cannot have.
"""

from dataclasses import dataclass

from rolecompile import report, text
from rolecompile.model import RoleSource

COMMENT = "#"
SEPARATOR = ":"


class SourceProblem(Exception):
    """A source file that cannot be read as text. Carries the message, naming the file."""


@dataclass(frozen=True)
class RoleDefinition:
    """One declaration plus one prompt: the authoritative statement of a role."""

    source: RoleSource
    fields: dict
    prompt: str


def parse(source):
    """A `RoleSource` read as text. Raises `SourceProblem` naming the file that is not UTF-8."""
    return RoleDefinition(
        source=source,
        fields=fields(_text(source.declaration_path, source.declaration_bytes)),
        prompt=_text(source.prompt_path, source.prompt_bytes),
    )


def fields(declaration_text):
    """The declared fields, in the order they were read.

    A blank line, a line whose first non-space character starts a comment, and a line with no
    separator are all ignored. Everything after the first separator is the value, so a colon
    inside a description survives, and a `#` inside one is part of it.
    """
    found = {}
    for line in text.lines(declaration_text):
        stripped = line.strip()
        if not stripped or stripped.startswith(COMMENT):
            continue
        key, separator, value = line.partition(SEPARATOR)
        if not separator:
            continue
        found[key.strip()] = value.strip()
    return found


def _text(path, data):
    decoded = text.decode_source(data)
    if decoded is None:
        raise SourceProblem(report.not_text(path))
    return decoded
