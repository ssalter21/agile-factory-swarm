"""Stable identity for mutants, so a manifest is worth keeping.

A *unit* is a def, a class, or the module. Every mutant belongs to exactly one. The manifest
keys verdicts by unit and by the mutant's position inside it, rather than by line or by a
whole-file hash, so that editing one function throws away only what we knew about that function.

A unit's hash covers its own code with the units nested inside it removed outright. Removed, not
blanked: that way adding a function to a file leaves the file's own hash alone, which is what
lets the runner tell an added test from an edited one.
"""

import ast
import copy
import hashlib

UNIT_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def qualify(parent, name):
    return name if parent == "<module>" else parent + "." + name


def unit_map(tree):
    """{id(node): enclosing unit qualname} for every node in the tree."""
    found = {id(tree): "<module>"}

    def walk(node, unit):
        for child in ast.iter_child_nodes(node):
            found[id(child)] = unit
            walk(child, qualify(unit, child.name) if isinstance(child, UNIT_TYPES) else unit)

    walk(tree, "<module>")
    return found


def iter_units(tree):
    """(node, qualname) for the module and every def and class inside it."""
    yield tree, "<module>"

    def walk(node, unit):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, UNIT_TYPES):
                name = qualify(unit, child.name)
                yield child, name
                yield from walk(child, name)
            else:
                yield from walk(child, unit)

    yield from walk(tree, "<module>")


def strip_nested(node):
    """Remove every unit below `node`, so its hash sees only its own code."""
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            kept = [item for item in value if not isinstance(item, UNIT_TYPES)]
            if len(kept) != len(value):
                if not kept and field == "body" and not isinstance(node, ast.Module):
                    kept = [ast.Pass()]
                setattr(node, field, kept)
            for item in kept:
                if isinstance(item, ast.AST):
                    strip_nested(item)
        elif isinstance(value, ast.AST):
            strip_nested(value)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def unit_hashes(source):
    """{qualname: hash of that unit's own code}, blind to the units nested inside it."""
    tree = ast.parse(source)
    out = {}
    for node, name in iter_units(tree):
        clone = copy.deepcopy(node)
        strip_nested(clone)
        out[name] = digest(ast.unparse(ast.fix_missing_locations(clone)))
    return out


def test_state(root, paths):
    """{path::qualname: hash} over the test tree, so added tests read differently from edits."""
    state = {}
    for entry in paths:
        target = root / entry
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        for path in files:
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                hashes = unit_hashes(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            relative = path.relative_to(root).as_posix()
            for name, value in hashes.items():
                state[relative + "::" + name] = value
    return state


def compare_tests(old, new):
    """`same`; `additive` when every old unit survived untouched; otherwise `changed`."""
    if old == new:
        return "same"
    for key, value in old.items():
        if new.get(key) != value:
            return "changed"
    return "additive"
