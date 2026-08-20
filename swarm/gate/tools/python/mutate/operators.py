"""What a mutant is allowed to change. This is the Python-specific half of the tool.

Adding an operator here is how the tool gets stronger. Adding one is cheap: return more
(description, factory) candidates from a visitor, and the manifest, the runner and the reporting
all follow. A candidate must produce code that still parses, and must change behaviour rather
than only spelling -- an equivalent mutant costs a full test run and teaches nothing.
"""

import ast

CMP_SWAPS = {
    ast.Eq: [ast.NotEq],
    ast.NotEq: [ast.Eq],
    ast.Lt: [ast.GtE, ast.Gt, ast.LtE],
    ast.LtE: [ast.Gt, ast.Lt],
    ast.Gt: [ast.LtE, ast.Lt, ast.GtE],
    ast.GtE: [ast.Lt, ast.Gt],
    ast.Is: [ast.IsNot],
    ast.IsNot: [ast.Is],
    ast.In: [ast.NotIn],
    ast.NotIn: [ast.In],
}

BIN_SWAPS = {
    ast.Add: [ast.Sub],
    ast.Sub: [ast.Add],
    ast.Mult: [ast.Add],
    ast.Div: [ast.Mult],
    ast.Mod: [ast.Mult],
}

# Keyword arguments whose string value is documentation rather than behaviour -- argparse and
# the libraries that follow it. Mutating one produces a survivor that can only be killed by
# asserting help text word for word, which is a worse test than no test.
DOC_KEYWORDS = ("help", "description", "epilog", "usage")

# Statements that are pointless to delete: removing one raises before any assertion can
# discriminate, so the mutant is always killed and the test run is always wasted.
UNDELETABLE = (
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    ast.Pass,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)


def compare_candidates(node):
    if len(node.ops) != 1:
        return []
    op = type(node.ops[0])
    return [
        (
            "%s -> %s" % (op.__name__, other.__name__),
            lambda o=other: ast.Compare(node.left, [o()], node.comparators),
        )
        for other in CMP_SWAPS.get(op, [])
    ]


def boolop_candidates(node):
    other = ast.Or if isinstance(node.op, ast.And) else ast.And
    desc = "%s -> %s" % (type(node.op).__name__, other.__name__)
    return [(desc, lambda: ast.BoolOp(other(), node.values))]


def binop_candidates(node):
    return [
        (
            "%s -> %s" % (type(node.op).__name__, other.__name__),
            lambda o=other: ast.BinOp(node.left, o(), node.right),
        )
        for other in BIN_SWAPS.get(type(node.op), [])
    ]


def unaryop_candidates(node):
    if not isinstance(node.op, ast.Not):
        return []
    return [("drop not", lambda: node.operand)]


def distinct(values, original):
    """The replacements worth trying: not the original, and not each other.

    Two operators can propose the same replacement -- `1 - 1` and the literal zero both give 0,
    and dropping either `a` from `"aa"` gives `"a"`. Each duplicate costs a whole test run and
    tells us exactly what its twin already did.
    """
    kept = []
    for value in values:
        if value != original and value not in kept:
            kept.append(value)
    return kept


def constant_candidates(node):
    value = node.value
    if isinstance(value, bool):
        return [("%s -> %s" % (value, not value), lambda: ast.Constant(not value))]
    if isinstance(value, int):
        return [
            ("%s -> %s" % (value, other), lambda o=other: ast.Constant(o))
            for other in distinct([value + 1, value - 1, 0], value)
        ]
    if isinstance(value, str) and value != "":
        found = [
            ("%r -> empty" % (value,), lambda: ast.Constant("")),
            ("%r -> mutated" % (value,), lambda: ast.Constant("X" + value)),
        ]
        if 2 <= len(value) <= 4:
            shorter = [value[:at] + value[at + 1 :] for at in range(len(value))]
            for text in distinct(shorter, value):
                found.append(("%r -> %r" % (value, text), lambda t=text: ast.Constant(t)))
        return found
    return []


def if_candidates(node):
    return [
        ("if -> True", lambda: ast.If(ast.Constant(True), node.body, node.orelse)),
        ("if -> False", lambda: ast.If(ast.Constant(False), node.body, node.orelse)),
    ]


def return_candidates(node):
    empty = node.value is None or (
        isinstance(node.value, ast.Constant) and node.value.value is None
    )
    if empty:
        return []
    return [("return -> None", lambda: ast.Return(ast.Constant(None)))]
