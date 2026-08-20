"""Finding every place a file can be mutated, and building one mutant at a time."""

import ast

from mutate import operators
from mutate.units import UNIT_TYPES, unit_map


class Mutant:
    """One change to try, and enough identity to remember its verdict across runs.

    A *site* is a place in the code that can be mutated; a mutant is one of the changes that can
    be made there. `a > b` is one site with three mutants. The distinction matters: the site cap
    in constitution section 2 asks whether the file does too much, and that is a question about
    places, not about how many operators this tool happens to know.
    """

    __slots__ = ("kind", "index", "unit", "node", "variant", "desc", "line")

    def __init__(self, kind, index, unit, node, variant, desc, line):
        self.kind = kind
        self.index = index
        self.unit = unit
        self.node = node
        self.variant = variant
        self.desc = desc
        self.line = line

    @property
    def site(self):
        return (self.unit, self.kind, self.node)

    @property
    def key(self):
        """Survives edits elsewhere in the file, which is what makes the manifest worth having."""
        return "%s#%s#%d#%d" % (self.unit, self.kind, self.node, self.variant)

    @property
    def label(self):
        return "L%d %s" % (self.line, self.desc)


class Mutator(ast.NodeTransformer):
    """Applies exactly the mutant whose index equals `target`, and records every one it passes."""

    def __init__(self, target=None, skip=(), units=None):
        self.target = target
        self.skip = set(skip)
        self.units = units or {}
        self.n = 0
        self.nodes = {}
        self.mutants = []

    def _pick(self, node, candidates):
        result = node
        if not candidates:
            return result
        unit = self.units.get(id(node), "<module>")
        ordinal = self.nodes.get(unit, 0)
        self.nodes[unit] = ordinal + 1
        line = getattr(node, "lineno", 0)
        for variant, (desc, factory) in enumerate(candidates):
            index = self.n
            self.n += 1
            self.mutants.append(Mutant("expr", index, unit, ordinal, variant, desc, line))
            if index == self.target:
                result = factory()
        return result

    def visit_Compare(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.compare_candidates(node))

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.boolop_candidates(node))

    def visit_BinOp(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.binop_candidates(node))

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.unaryop_candidates(node))

    def visit_Constant(self, node):
        if id(node) in self.skip:
            return node
        return self._pick(node, operators.constant_candidates(node))

    def visit_If(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.if_candidates(node))

    def visit_Return(self, node):
        self.generic_visit(node)
        return self._pick(node, operators.return_candidates(node))


def is_docstring(holder, stmt):
    return (
        isinstance(holder, (ast.Module,) + UNIT_TYPES)
        and isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
    )


def docstrings(tree):
    """The node ids of every docstring constant. A docstring is not a mutation site."""
    found = set()
    for node in ast.walk(tree):
        for _, value in ast.iter_fields(node):
            if isinstance(value, list) and value and is_docstring(node, value[0]):
                found.add(id(value[0].value))
    return found


def documented(tree):
    """The node ids of string constants that are documentation: help text, descriptions.

    The same reasoning that excludes docstrings. Changing the words in a help string cannot
    break anything a test should be checking, so a mutant there is a survivor by construction.
    """
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            documentation = keyword.arg in operators.DOC_KEYWORDS
            if documentation and isinstance(keyword.value, ast.Constant):
                found.add(id(keyword.value))
    return found


def excluded(tree):
    """Every constant that is text about the code rather than part of it."""
    return docstrings(tree) | documented(tree)


def statement_slots(tree):
    """Every deletable statement as (holder, field, index, stmt), depth first, stable order."""

    def walk(node):
        for field, value in ast.iter_fields(node):
            if not isinstance(value, list):
                continue
            for index, item in enumerate(value):
                if not isinstance(item, ast.stmt) or isinstance(item, operators.UNDELETABLE):
                    continue
                if index == 0 and is_docstring(node, item):
                    continue
                yield node, field, index, item
        for child in ast.iter_child_nodes(node):
            yield from walk(child)

    return walk(tree)


def deletions(tree):
    units = unit_map(tree)
    counts = {}
    found = []
    for index, (_, _, _, stmt) in enumerate(statement_slots(tree)):
        unit = units.get(id(stmt), "<module>")
        ordinal = counts.get(unit, 0)
        counts[unit] = ordinal + 1
        desc = "drop " + type(stmt).__name__
        found.append(Mutant("del", index, unit, ordinal, 0, desc, stmt.lineno))
    return found


def collect(source):
    """Every mutant this tool can make in `source`, in a stable order."""
    tree = ast.parse(source)
    mutator = Mutator(None, excluded(tree), unit_map(tree))
    mutator.visit(tree)
    return mutator.mutants + deletions(ast.parse(source))


def site_count(mutants):
    """Places, not changes. This is the number constitution section 2 puts a cap on."""
    return len({mutant.site for mutant in mutants})


def build(source, mutant):
    """The source of one mutant, or None when that site no longer exists."""
    tree = ast.parse(source)
    if mutant.kind == "expr":
        mutator = Mutator(mutant.index, excluded(tree), unit_map(tree))
        tree = mutator.visit(tree)
        if mutant.index >= len(mutator.mutants):
            return None
    else:
        slots = list(statement_slots(tree))
        if mutant.index >= len(slots):
            return None
        holder, field, position, _ = slots[mutant.index]
        getattr(holder, field)[position] = ast.Pass()
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"
