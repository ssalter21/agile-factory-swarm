"""The bytes of an agent file, fixed here rather than left to a YAML dumper.

Reproducing the twelve agent files already in the tree, byte for byte, is the whole test of this
tool, and a general-purpose dumper breaks that four ways at once: it sorts keys, folds a long line,
quotes what it feels like quoting, and writes whatever newline the platform prefers. So the output
is stated instead.

    ---EOL
    name: <value>EOL          fields in this order, never sorted, never the declaration's order
    description: <value>EOL   written verbatim: nothing quoted, unquoted, escaped or folded
    tools: <value>EOL
    model: <value>EOL         Claude only
    effort: <value>EOL        Claude only
    ---EOL
    EOL
    <the prompt, every line ended with EOL, the last one included>

EOL is CRLF on every platform. `.gitattributes` pins the same ending for both agent directories,
so a checkout cannot move it and the tool cannot be wrong about it on one machine only.
"""

from rolecompile import text

EOL = "\r\n"
FENCE = "---"
ENCODING = "utf-8"

CLAUDE_FIELDS = ("name", "description", "tools", "model", "effort")
GITHUB_FIELDS = ("name", "description", "tools")


def claude_file(fields, prompt):
    """The Claude Code agent file: all five fields."""
    return agent_file(CLAUDE_FIELDS, fields, prompt)


def github_file(fields, prompt):
    """The GitHub Copilot agent file. `model` and `effort` are dropped: no value there is right."""
    return agent_file(GITHUB_FIELDS, fields, prompt)


def agent_file(order, fields, prompt):
    """One agent file's bytes. A field outside `order`, or absent, is simply not written."""
    written = [FENCE]
    written.extend("%s: %s" % (key, fields[key]) for key in order if key in fields)
    written.append(FENCE)
    written.append("")
    written.extend(body(prompt))
    return (EOL.join(written) + EOL).encode(ENCODING)


def body(prompt):
    """The prompt's lines with trailing blank ones dropped, so the file ends in one newline."""
    found = text.lines(prompt)
    while found and not found[-1]:
        found.pop()
    return found
