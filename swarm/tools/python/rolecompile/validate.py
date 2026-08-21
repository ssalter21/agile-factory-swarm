"""The three input checks, in order, over the whole set of role definitions.

There are three and there is no fourth. The compile stops at the first problem it finds rather
than collecting them: with twelve known inputs, a second run costs less than the machinery for
enumerating mistakes.

Each check runs over every definition before the next one starts, so a file that is wrong in two
ways is reported against the earlier check.
"""

from rolecompile import report

NAME = "name"
TOOLS = "tools"


def first_problem(definitions):
    """The message for the first problem found, or None. `definitions` is in filename order."""
    return (
        _duplicate_name(definitions)
        or _name_mismatch(definitions)
        or _missing_tools(definitions)
    )


def _duplicate_name(definitions):
    """Two declarations claiming one name. A name with no declaration is the next check's."""
    claimed = {}
    for definition in definitions:
        declared = definition.fields.get(NAME)
        if declared is None:
            continue
        if declared in claimed:
            path = definition.source.declaration_path
            return report.duplicate_name(path, claimed[declared], declared)
        claimed[declared] = definition.source.declaration_path
    return None


def _name_mismatch(definitions):
    """A declared name that is not the filename stem, an absent name included.

    The name is data rather than something derived from the filename, because the same string is
    the filename on both harnesses, the type the workflow scripts dispatch on, and the voice key
    in the spec configuration. So the two are made to agree here.
    """
    for definition in definitions:
        source = definition.source
        declared = definition.fields.get(NAME)
        if declared != source.name:
            return report.name_mismatch(source.declaration_path, declared, source.name)
    return None


def _missing_tools(definitions):
    """No tools field. An absent allowlist is a permission change dressed as a formatting choice."""
    for definition in definitions:
        if TOOLS not in definition.fields:
            return report.missing_tools(definition.source.declaration_path)
    return None
