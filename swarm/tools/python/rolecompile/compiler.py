"""The whole compile, as two pure functions.

Sources in, agent files out; agent files and what is on disk in, an outcome out. Nothing here
opens a file, so the rules can be tested by handing them bytes rather than by building a
repository first.

Every source is read and validated before a single byte is offered for writing, which is what
makes a half-written set of agent files impossible.
"""

from dataclasses import dataclass

from rolecompile import compare, declaration, emit, report, validate
from rolecompile.compare import Status
from rolecompile.model import CLAUDE_DIR, CLAUDE_SUFFIX, GITHUB_DIR, GITHUB_SUFFIX, TargetFile

SUCCESS = 0
OUT_OF_DATE = 1
PROBLEM = 2


@dataclass(frozen=True)
class Outcome:
    """What one run amounts to: what to print, what to write, and what to exit with."""

    lines: list
    to_write: list
    code: int


def targets(sources):
    """(the first problem or None, every agent file the sources compile to, sorted by path)."""
    try:
        definitions = [declaration.parse(source) for source in sources]
    except declaration.SourceProblem as problem:
        return str(problem), []
    message = validate.first_problem(definitions)
    if message is not None:
        return message, []
    return None, sorted(_files(definitions), key=lambda target: target.path)


def outcome(targets_, on_disk, present, check):
    """One line per agent file considered, the files to write, and the exit code.

    `on_disk` maps every target's path to its bytes, or to None where there is no file. `present`
    is the destination directories that exist. In check mode a destination that is not on disk is
    out of the run: it produces no lines and cannot fail the check, which is what lets the run
    that builds this tool pass before `.github/agents/` exists. Once a destination is there, a
    file missing from it counts as a difference like any other.

    In check mode nothing is ever added to `to_write`. That is the only place the promise lives.
    """
    lines = []
    to_write = []
    code = SUCCESS
    for target in targets_:
        if check and _directory(target.path) not in present:
            continue
        state = compare.status(target.data, on_disk.get(target.path))
        if state is Status.SAME:
            lines.append(report.unchanged(target.path))
        elif check:
            lines.append(report.out_of_date(target.path, state is Status.LINE_ENDINGS))
            code = OUT_OF_DATE
        else:
            to_write.append(target)
            lines.append(report.written(target.path))
    return Outcome(lines=lines, to_write=to_write, code=code)


def _files(definitions):
    """The two agent files each role definition produces, under its declared name."""
    for definition in definitions:
        name = definition.fields[validate.NAME]
        yield TargetFile(
            path="%s/%s%s" % (CLAUDE_DIR, name, CLAUDE_SUFFIX),
            data=emit.claude_file(definition.fields, definition.prompt),
        )
        yield TargetFile(
            path="%s/%s%s" % (GITHUB_DIR, name, GITHUB_SUFFIX),
            data=emit.github_file(definition.fields, definition.prompt),
        )


def _directory(path):
    return path.rsplit("/", 1)[0]
