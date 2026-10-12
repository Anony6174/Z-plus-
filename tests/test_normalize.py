import os

import pytest

from zplus.errors import ZplusError
from zplus.loader import load_submissions
from zplus.normalize import normalize
from zplus.types import Skipped
from tests.conftest import FIXTURES

BASE = '''def total(values, limit):
    result = 0
    for v in values:
        if v < limit:
            result += v * 2
    return result
'''


def texts(src, **kw):
    return [(t.kind, t.text) for t in normalize(src, **kw)]


def test_renaming_gives_identical_tokens():
    renamed = BASE.replace("values", "xs").replace("limit", "cap").replace(
        "result", "acc").replace("total", "f").replace(" v ", " q ").replace("(v", "(q")
    renamed = renamed.replace("if v", "if q").replace("+= v", "+= q")
    assert texts(BASE) == texts(renamed)


def test_comments_blank_lines_docstrings_vanish():
    padded = '''# header comment
def total(values, limit):
    """A docstring
    over two lines."""

    result = 0  # start at zero

    for v in values:
        # check
        if v < limit:
            "bare string statement"
            result += v * 2
    return result
'''
    assert texts(BASE) == texts(padded)


def test_wrapped_expression_is_identical():
    a = "x = (alpha + beta +\n     gamma)\n"
    b = "x = (alpha + beta + gamma)\n"
    c = "x = (alpha + beta + \\\n     gamma)\n"
    assert texts(a) == texts(b) == texts(c)


def test_fstring_is_one_str():
    toks = normalize('msg = f"{a!r} and {b + c:>{width}} {{x}}"\n')
    assert [t.kind for t in toks] == ["ID", "OP", "STR", "NEWLINE"]


def test_nested_fstring_is_one_str():
    toks = normalize("msg = f'{f\"{x}\"}'\n")
    assert [t.kind for t in toks] == ["ID", "OP", "STR", "NEWLINE"]


def test_mapping_table():
    toks = normalize("if len(x) > 3.5:\n    print('hi')\n")
    assert [(t.kind, t.text) for t in toks] == [
        ("KW", "if"), ("BUILTIN", "len"), ("OP", "("), ("ID", "ID"), ("OP", ")"),
        ("OP", ">"), ("NUM", "NUM"), ("OP", ":"), ("NEWLINE", "NEWLINE"),
        ("INDENT", "INDENT"), ("BUILTIN", "print"), ("OP", "("), ("STR", "STR"),
        ("OP", ")"), ("NEWLINE", "NEWLINE"), ("DEDENT", "DEDENT"),
    ]


def test_keep_names():
    assert ("ID", "values") in texts(BASE, keep_names=True)


def test_line_numbers_point_at_original_lines():
    src = "# c\n\nx = 1\n\n\ny = (2 +\n 3)\n"
    toks = normalize(src)
    assert [(t.text, t.line) for t in toks if t.kind in ("ID", "NUM")] == [
        ("ID", 3), ("NUM", 3), ("ID", 6), ("NUM", 6), ("NUM", 7)]


def test_empty_file():
    assert normalize("") == []
    assert normalize("\n\n# only a comment\n") == []


def test_crlf_bom_and_tabs_give_same_tokens():
    spaces = "def f(a):\n    if a:\n        return 1\n    return 2\n"
    crlf = "\ufeff" + spaces.replace("\n", "\r\n")
    tabs = spaces.replace("        ", "\t\t").replace("    ", "\t")
    assert texts(spaces) == texts(crlf) == texts(tabs)


def test_unrecoverable_syntax_raises():
    with pytest.raises(ZplusError):
        normalize("def f(:\n    x = (1,\n")
    with pytest.raises(ZplusError):
        normalize("if x:\n        a = 1\n    b = 2\n")


def test_syntax_error_file_is_skipped_not_a_crash():
    skipped = []
    subs = load_submissions(os.path.join(FIXTURES, "inject"), skipped=skipped)
    assert "inject/broken" not in {s.sid for s in subs}
    assert [s.sid for s in skipped] == ["inject/broken"]
    assert isinstance(skipped[0], Skipped) and "syntax" in skipped[0].reason


def test_loader_layouts(tmp_path):
    (tmp_path / "p1").mkdir()
    (tmp_path / "p1" / "a.py").write_text("x = 1\n")
    (tmp_path / "p1" / "template.py").write_text("x = 1\n")
    (tmp_path / "top.py").write_text("y = 2\n")
    sids = [s.sid for s in load_submissions(str(tmp_path))]
    assert sids == ["p1/a", f"{tmp_path.name}/top"]


def test_large_file_warns(caplog, tmp_path):
    (tmp_path / "big.py").write_text("x = 1\n" * 5001)
    load_submissions(str(tmp_path))
    assert "tiling will be slow" in caplog.text
