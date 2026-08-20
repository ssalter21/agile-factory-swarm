"""Turning bytes into text, and text into lines.

The two decoding rules differ, and they are kept side by side so the difference is visible rather
than surprising. A source file is read generously: a byte-order mark an editor left behind is
dropped, which is what guarantees the emitted files carry none. A target file is read exactly,
because the only question being asked of it is whether its bytes are the bytes we would write, and
a mark is a difference like any other.
"""

SOURCE_ENCODING = "utf-8-sig"
TARGET_ENCODING = "utf-8"


def decode_source(data):
    """A declaration or a prompt as text, or None where the bytes are not UTF-8."""
    return _decode(data, SOURCE_ENCODING)


def decode_target(data):
    """An agent file on disk as text, or None where the bytes are not UTF-8."""
    return _decode(data, TARGET_ENCODING)


def _decode(data, encoding):
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        return None


def lines(text):
    """`text` split on CRLF, CR or LF, so a file's own line endings never reach the output."""
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
