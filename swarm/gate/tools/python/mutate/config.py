"""Reading .swarm/gate.yaml.

Only the handful of values the runner needs, and only the flat subset of YAML that gate.yaml is
written in. A real YAML parser would be a third-party dependency, and the constitution asks for
tools that install nothing.
"""

from pathlib import Path

DEFAULT_MAX_SITES = 250


class Gate:
    """The handful of gate.yaml values this tool needs."""

    def __init__(self, shell=None, tests=None, mutation_tests=None, max_sites=DEFAULT_MAX_SITES):
        self.shell = shell
        self.tests = tests
        self.mutation_tests = mutation_tests
        self.max_sites = max_sites

    @property
    def command(self):
        """The command to judge a mutant by, preferring the one written for this job."""
        chosen = self.mutation_tests or self.tests
        return None if chosen == "missing" else chosen


def strip_comment(line):
    """Drop a trailing `#` comment, respecting quotes."""
    quote = None
    for position, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#":
            return line[:position]
    return line


def unquote(text):
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def scalar(text):
    text = text.strip()
    if text != unquote(text):
        return unquote(text)
    if text.lstrip("-").isdigit():
        return int(text)
    return text


def parse_yaml(text):
    """The flat `key: value` / `section:` plus indented subset that gate.yaml is written in."""
    tree = {}
    section = None
    for raw in text.splitlines():
        line = strip_comment(raw).rstrip()
        if not line.strip() or ":" not in line:
            continue
        indented = line[0] in " \t"
        key, _, value = line.strip().partition(":")
        key = key.strip()
        if not value.strip():
            if not indented:
                section = tree.setdefault(key, {})
            continue
        if indented:
            # An indented key with no section open is malformed. Ignore it rather than promote
            # it to the top level, where it would quietly mean something else.
            if isinstance(section, dict):
                section[key] = scalar(value)
            continue
        tree[key] = scalar(value)
        section = None
    return tree


def load_gate(path):
    path = Path(path)
    if not path.is_file():
        return Gate()
    tree = parse_yaml(path.read_text(encoding="utf-8"))
    steps = tree.get("steps") or {}
    defaults = tree.get("defaults") or {}
    cap = defaults.get("max_mutation_sites_per_file", DEFAULT_MAX_SITES)
    return Gate(
        shell=tree.get("shell"),
        tests=steps.get("tests"),
        mutation_tests=defaults.get("mutation_test_command"),
        max_sites=cap if isinstance(cap, int) else DEFAULT_MAX_SITES,
    )
