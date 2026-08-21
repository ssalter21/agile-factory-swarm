"""What each operator offers at a site.

These assert the exact candidate list, description text and resulting code. An operator that
quietly offers one fewer mutant, or a differently worded one, is a change in what the gate
measures, so it should fail a test rather than pass unnoticed.
"""

import ast

import pytest

from mutate import operators


def node(text, kind):
    for found in ast.walk(ast.parse(text)):
        if isinstance(found, kind):
            return found
    raise AssertionError("no %s in %r" % (kind.__name__, text))


def offered(candidates):
    return [desc for desc, _ in candidates]


def produced(candidates):
    return [ast.unparse(ast.fix_missing_locations(factory())) for _, factory in candidates]


# --------------------------------------------------------------------------- comparisons


def test_a_less_than_offers_three_neighbours():
    found = operators.compare_candidates(node("a < b", ast.Compare))
    assert offered(found) == ["Lt -> GtE", "Lt -> Gt", "Lt -> LtE"]
    assert produced(found) == ["a >= b", "a > b", "a <= b"]


def test_equality_offers_only_its_negation():
    assert offered(operators.compare_candidates(node("a == b", ast.Compare))) == ["Eq -> NotEq"]


def test_identity_and_membership_flip():
    assert offered(operators.compare_candidates(node("a is b", ast.Compare))) == ["Is -> IsNot"]
    assert offered(operators.compare_candidates(node("a in b", ast.Compare))) == ["In -> NotIn"]


def test_a_chained_comparison_is_left_alone():
    assert operators.compare_candidates(node("a < b < c", ast.Compare)) == []


def test_an_unknown_comparison_offers_nothing():
    assert operators.compare_candidates(node("a @ b == 1", ast.Compare)) != []
    assert operators.compare_candidates(node("a < b", ast.Compare)) != []


# --------------------------------------------------------------------------- operators


def test_and_becomes_or_and_back():
    assert offered(operators.boolop_candidates(node("a and b", ast.BoolOp))) == ["And -> Or"]
    assert produced(operators.boolop_candidates(node("a and b", ast.BoolOp))) == ["a or b"]
    assert offered(operators.boolop_candidates(node("a or b", ast.BoolOp))) == ["Or -> And"]


def test_arithmetic_swaps_are_the_declared_ones():
    assert offered(operators.binop_candidates(node("a + b", ast.BinOp))) == ["Add -> Sub"]
    assert offered(operators.binop_candidates(node("a - b", ast.BinOp))) == ["Sub -> Add"]
    assert offered(operators.binop_candidates(node("a * b", ast.BinOp))) == ["Mult -> Add"]
    assert offered(operators.binop_candidates(node("a / b", ast.BinOp))) == ["Div -> Mult"]
    assert offered(operators.binop_candidates(node("a % b", ast.BinOp))) == ["Mod -> Mult"]
    assert produced(operators.binop_candidates(node("a + b", ast.BinOp))) == ["a - b"]


def test_an_unswapped_operator_offers_nothing():
    assert operators.binop_candidates(node("a ** b", ast.BinOp)) == []
    assert operators.binop_candidates(node("a // b", ast.BinOp)) == []


def test_not_is_dropped_and_other_unary_operators_are_not():
    found = operators.unaryop_candidates(node("not a", ast.UnaryOp))
    assert offered(found) == ["drop not"]
    assert produced(found) == ["a"]
    assert operators.unaryop_candidates(node("-a", ast.UnaryOp)) == []
    assert operators.unaryop_candidates(node("~a", ast.UnaryOp)) == []


# --------------------------------------------------------------------------- constants


def test_a_bool_flips_and_says_so():
    found = operators.constant_candidates(ast.Constant(True))
    assert offered(found) == ["True -> False"]
    assert produced(found) == ["False"]
    assert offered(operators.constant_candidates(ast.Constant(False))) == ["False -> True"]


def test_an_integer_offers_both_neighbours_and_zero():
    found = operators.constant_candidates(ast.Constant(7))
    assert offered(found) == ["7 -> 8", "7 -> 6", "7 -> 0"]
    assert produced(found) == ["8", "6", "0"]


def test_zero_does_not_offer_itself():
    found = operators.constant_candidates(ast.Constant(0))
    assert offered(found) == ["0 -> 1", "0 -> -1"]
    assert produced(found) == ["1", "-1"]


def test_one_offers_two_zero_and_nothing_else():
    assert offered(operators.constant_candidates(ast.Constant(1))) == ["1 -> 2", "1 -> 0"]


def test_a_long_string_offers_emptying_and_lengthening_only():
    found = operators.constant_candidates(ast.Constant("hello world"))
    assert offered(found) == ["'hello world' -> empty", "'hello world' -> mutated"]
    assert produced(found) == ["''", "'Xhello world'"]


def test_a_short_string_also_offers_each_character_removed():
    found = operators.constant_candidates(ast.Constant("abc"))
    assert offered(found) == [
        "'abc' -> empty",
        "'abc' -> mutated",
        "'abc' -> 'bc'",
        "'abc' -> 'ac'",
        "'abc' -> 'ab'",
    ]
    assert produced(found)[2:] == ["'bc'", "'ac'", "'ab'"]


def test_the_short_string_window_is_two_to_four_characters():
    assert len(operators.constant_candidates(ast.Constant("a"))) == 2
    assert len(operators.constant_candidates(ast.Constant("ab"))) == 4
    assert len(operators.constant_candidates(ast.Constant("abcd"))) == 6
    assert len(operators.constant_candidates(ast.Constant("abcde"))) == 2


def test_an_empty_string_offers_nothing():
    assert operators.constant_candidates(ast.Constant("")) == []


def test_a_value_with_no_operator_offers_nothing():
    assert operators.constant_candidates(ast.Constant(None)) == []
    assert operators.constant_candidates(ast.Constant(1.5)) == []
    assert operators.constant_candidates(ast.Constant(b"bytes")) == []


def test_a_bool_is_not_treated_as_an_integer():
    assert offered(operators.constant_candidates(ast.Constant(True))) == ["True -> False"]


# --------------------------------------------------------------------------- statements


def test_an_if_is_forced_both_ways():
    found = operators.if_candidates(node("if a:\n    b\n", ast.If))
    assert offered(found) == ["if -> True", "if -> False"]
    assert [line.splitlines()[0] for line in produced(found)] == ["if True:", "if False:"]


def test_a_return_of_a_value_is_emptied():
    found = operators.return_candidates(node("def f():\n    return 1\n", ast.Return))
    assert offered(found) == ["return -> None"]
    assert produced(found) == ["return None"]


@pytest.mark.parametrize("text", ["def f():\n    return\n", "def f():\n    return None\n"])
def test_a_return_of_nothing_is_left_alone(text):
    assert operators.return_candidates(node(text, ast.Return)) == []


def test_the_undeletable_statements_are_the_ones_that_would_always_be_killed():
    assert ast.Import in operators.UNDELETABLE
    assert ast.ImportFrom in operators.UNDELETABLE
    assert ast.Global in operators.UNDELETABLE
    assert ast.Nonlocal in operators.UNDELETABLE
    assert ast.Pass in operators.UNDELETABLE
    assert ast.FunctionDef in operators.UNDELETABLE
    assert ast.ClassDef in operators.UNDELETABLE
    assert ast.Return not in operators.UNDELETABLE
    assert ast.Assign not in operators.UNDELETABLE


# --------------------------------------------------------------------------- no duplicates


def test_distinct_drops_the_original_and_repeats():
    assert operators.distinct([2, 0, 0], 1) == [2, 0]
    assert operators.distinct(["a", "a"], "aa") == ["a"]
    assert operators.distinct([], 1) == []


def test_a_repeated_short_string_offers_each_result_once():
    found = operators.constant_candidates(ast.Constant("aa"))
    assert offered(found) == ["'aa' -> empty", "'aa' -> mutated", "'aa' -> 'a'"]


def test_no_constant_offers_the_same_replacement_twice():
    for value in [0, 1, -1, 2, 7, "a", "aa", "aaa", "abcd", "hello"]:
        results = produced(operators.constant_candidates(ast.Constant(value)))
        assert len(results) == len(set(results)), value
