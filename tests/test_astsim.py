import os

from zplus.astsim import ast_similarity
from tests.conftest import DATA

SRC = '''def solve(items, limit):
    total = 0
    count = 0
    for x in items:
        if x > limit:
            total = total + x * 2
            count += 1
    best = max(items) if items else 0
    return total, count, best
'''


def test_identical_files():
    assert ast_similarity(SRC, SRC) == 1.0


def test_renamed_variables():
    renamed = (SRC.replace("items", "data").replace("limit", "cap")
               .replace("total", "acc").replace("count", "n").replace("best", "top"))
    assert ast_similarity(SRC, renamed) == 1.0


def test_reordered_independent_statements():
    src = open(os.path.join(DATA, "p4_spiral_matrix", "alice.py")).read()
    a = "    top, bottom = 0, len(matrix) - 1\n"
    b = "    left, right = 0, len(matrix[0]) - 1\n"
    assert a + b in src
    swapped = src.replace(a + b, b + a)
    score = ast_similarity(src, swapped)
    assert 0.8 <= score < 1.0  # only the parents (FunctionDef, Module) change


def test_augassign_canonicalized():
    a = "def f(xs):\n    s = 0\n    for v in xs:\n        s += v * 3 - 1\n    return s\n"
    b = a.replace("s += v * 3 - 1", "s = s + (v * 3 - 1)")
    assert ast_similarity(a, b) == 1.0


def test_unrelated_solutions_score_lower():
    p = os.path.join(DATA, "p5_number_of_islands")
    a = open(os.path.join(p, "alice.py")).read()  # recursive DFS
    c = open(os.path.join(p, "carol.py")).read()  # union-find
    score = ast_similarity(a, c)
    assert score < 0.5  # recorded: about 0.1 on this pair


def test_syntax_error_and_tiny_files():
    assert ast_similarity("def f(:\n", SRC) == 0.0
    assert ast_similarity("x = 1\n", "x = 2\n") == 0.0


def test_deep_nesting_does_not_crash():
    deep = "x = " + "(" * 150 + "1" + ")" * 150 + "\n"
    nested = "def f(x):\n" + "".join("    " * (i + 1) + "if x:\n" for i in range(80))
    nested += "    " * 81 + "return 1\n"
    assert ast_similarity(deep, deep) >= 0.0
    assert ast_similarity(nested, nested) == 1.0
