"""Where the gate declaration lives, and how its `steps` mapping is read.

The accepted subset of YAML, and nothing wider:

- UTF-8 text, split into lines.
- A `#` at the start of a line, or preceded by a space or tab, starts a comment that runs to
  the end of the line. A `#` inside single or double quotes does not.
- The block begins at a line whose only content, at column 0, is `steps:`, and ends at the next
  non-blank line at column 0.
- Inside the block, lines at the indent of the block's first entry are read as `key: value`.
  Lines indented further belong to something nested and are skipped.
- A value is a scalar: bare text, or text wrapped in a matching pair of quotes. An empty value,
  a value opening `[` or `{`, and an unterminated quote are all reported as no scalar.

Anything outside that subset is not guessed at.
"""

GATE_RELATIVE_PATH: str = ".swarm/gate.yaml"

_STEPS_KEY = "steps:"
_QUOTES = "\"'"
_INDENT_CHARS = " \t"


def parse_steps(raw: bytes) -> tuple[tuple[str, str | None], ...] | None:
    """The entries under `steps:`, in file order, or None when there is no such mapping.

    Each entry is the key exactly as the file spells it and the value's scalar text, or None
    where the value is empty or is not a scalar.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None

    lines = text.splitlines()
    start = _steps_line(lines)
    if start is None:
        return None

    entries: list[tuple[str, str | None]] = []
    block_indent: int | None = None
    for line in lines[start + 1 :]:
        content = _without_comment(line)
        body = content.strip()
        if not body:
            continue
        indent = len(content) - len(content.lstrip(_INDENT_CHARS))
        if indent == 0:
            break
        if block_indent is None:
            block_indent = indent
        if indent != block_indent:
            continue
        key, separator, value = body.partition(":")
        key = key.strip()
        if separator and key:
            entries.append((key, _scalar(value)))

    return tuple(entries) or None


def _steps_line(lines: list[str]) -> int | None:
    """The index of the top-level `steps:` line, or None when the text has no such line."""
    for index, line in enumerate(lines):
        if _without_comment(line).rstrip() == _STEPS_KEY:
            return index
    return None


def _without_comment(line: str) -> str:
    """The line up to an unquoted `#` that opens a comment."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
        elif char in _QUOTES:
            quote = char
        elif char == "#" and (index == 0 or line[index - 1] in _INDENT_CHARS):
            return line[:index]
    return line


def _scalar(value: str) -> str | None:
    """The text of a scalar value, or None where the value is empty or is not a scalar."""
    text = value.strip()
    if not text:
        return None
    if text[0] in _QUOTES:
        if len(text) > 1 and text[-1] == text[0]:
            return text[1:-1] or None
        return None
    if text[0] in "[{":
        return None
    return text
