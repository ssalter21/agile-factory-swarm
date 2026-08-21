"""Every line the command prints, in one place, so the whole of what a developer sees can be read
in one sitting.

This module decides nothing. It also speaks in ordinary words: the terms the spec coined for its
own use are not the words a developer wants at a terminal, so none of them appears here.
"""

UNCHANGED = "unchanged"
WRITTEN = "written"
OUT_OF_DATE = "out of date"
LINE_ENDINGS_ONLY = "the line endings differ, nothing else"


def unchanged(path):
    """An agent file that already holds the bytes the compile produced."""
    return "%s %s" % (path, UNCHANGED)


def written(path):
    """An agent file this run put on disk."""
    return "%s %s" % (path, WRITTEN)


def out_of_date(path, line_endings_only):
    """An agent file check mode found differing, saying so when line endings are the whole of it.

    That clause is the difference between twelve unexplained failures on a checkout configured
    differently and one instruction.
    """
    if line_endings_only:
        return "%s %s - %s" % (path, OUT_OF_DATE, LINE_ENDINGS_ONLY)
    return "%s %s" % (path, OUT_OF_DATE)


def duplicate_name(path, first_path, name):
    """Two declarations claiming one name. Both files are named, because either could be wrong."""
    return "%s: the field 'name' is '%s', which %s already declares." % (path, name, first_path)


def name_mismatch(path, declared, stem):
    """A declared name that is not the filename. The name is the filename on both harnesses."""
    if declared is None:
        return "%s: the field 'name' is missing, and the file is named '%s'." % (path, stem)
    return "%s: the field 'name' is '%s', but the file is named '%s'." % (path, declared, stem)


def missing_tools(path):
    """No tools field. Why it matters is part of the message: it is a permission change."""
    return (
        "%s: the field 'tools' is missing. A role with no tools line inherits every tool "
        "on Claude Code." % path
    )


def not_text(path):
    """A source file that is not UTF-8."""
    return "%s: the file is not valid UTF-8." % path


def unreadable(path, reason):
    """A file the command could not read. Named, because a traceback names nothing useful."""
    return "%s: %s" % (path, reason)
