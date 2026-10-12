import ast
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor

import pytest

from zplus.dataset import check_solution, ground_truth, parse_name, validate_dataset
from zplus.loader import iter_python_files, read_source
from zplus.mutate import independent, make_copies, mutate
from zplus.normalize import normalize
from tests.conftest import DATA


def originals():
    out = {}
    for problem, path in iter_python_files(DATA):
        if parse_name(os.path.basename(path))[1] is None:
            out.setdefault(problem, []).append(path)
    return out


ORIGINALS = originals()


def kinds(src):
    return [(t.kind, t.text) for t in normalize(src)]


def test_every_mutant_compiles():
    for paths in ORIGINALS.values():
        for path in paths:
            src = read_source(path)
            for level in (1, 2, 3):
                for seed in range(3):
                    compile(mutate(src, level, seed), path, "exec")


def test_every_mutant_passes_tests_all_problems_20_seeds():
    tmp = tempfile.mkdtemp()
    jobs = []
    try:
        for problem, paths in sorted(ORIGINALS.items()):
            tests = os.path.join(os.path.dirname(paths[0]), "tests.json")
            for seed in range(20):
                path = paths[seed % len(paths)]  # every original gets used
                for level in (1, 2, 3):
                    out = os.path.join(tmp, f"{problem}_{seed}_{level}.py")
                    with open(out, "w") as fh:
                        fh.write(mutate(read_source(path), level, seed))
                    jobs.append((out, tests))
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
            results = list(pool.map(lambda j: check_solution(*j), jobs))
        failed = [j[0] for j, ok in zip(jobs, results) if not ok]
        assert failed == []
    finally:
        shutil.rmtree(tmp)


def test_level1_matches_unparsed_original_after_normalization():
    for paths in ORIGINALS.values():
        for path in paths:
            src = read_source(path)
            plain = ast.unparse(ast.parse(src))
            for seed in range(3):
                assert kinds(mutate(src, 1, seed)) == kinds(plain)


def test_level1_really_renames_and_comments():
    src = read_source(ORIGINALS["p1_merge_intervals"][0])
    out = mutate(src, 1, 0)
    assert out != src
    assert "def solve(" in out  # entry point is never renamed
    assert normalize(out, keep_names=True) != normalize(src, keep_names=True)


def test_same_seed_same_output():
    src = read_source(ORIGINALS["p4_spiral_matrix"][0])
    for level in (1, 2, 3):
        assert mutate(src, level, 42) == mutate(src, level, 42)
    assert mutate(src, 3, 1) != mutate(src, 3, 2)


def test_level3_changes_token_sequence():
    for paths in ORIGINALS.values():
        for path in paths:
            src = read_source(path)
            assert kinds(mutate(src, 3, 0)) != kinds(ast.unparse(ast.parse(src)))


def test_level3_converts_for_to_while():
    src = "def solve(n):\n    t = 0\n    for i in range(1, n):\n        t += i\n    return t\n"
    outs = [mutate(src, 3, s) for s in range(10)]
    assert any("while" in o for o in outs)
    for o in outs:
        ns = {}
        exec(compile(o, "m", "exec"), ns)
        assert ns["solve"](10) == 45


def test_protected_names_survive():
    src = ("import math\n\n\ndef helper(values, reverse):\n"
           "    return sorted(values, reverse=reverse)\n\n\n"
           "def solve(xs):\n    out = []\n    out.append(math.floor(1.5))\n"
           "    return helper(xs, reverse=True) + out\n")
    out = mutate(src, 2, 3)
    assert "math.floor" in out and "reverse=" in out and ".append(" in out
    ns = {}
    exec(compile(out, "m", "exec"), ns)
    assert ns["solve"]([2, 3, 1]) == [3, 2, 1, 1]


def test_independent_rules():
    def stmts(code):
        return ast.parse(code).body

    a, b = stmts("x = 1\ny = 2")
    assert independent(a, b)
    a, b = stmts("x = 1\ny = x")
    assert not independent(a, b)
    a, b = stmts("x = f()\ny = 2")
    assert not independent(a, b)
    a, b = stmts("xs[0] = 1\ny = xs[0]")
    assert not independent(a, b)
    a, b = stmts("x = 1\nif y: pass")
    assert not independent(a, b)


def test_bad_level():
    with pytest.raises(ValueError):
        mutate("x = 1\n", 4, 0)


def test_make_copies_writes_validated_copies(tmp_path):
    src = os.path.join(DATA, "p2_valid_brackets")
    dst = tmp_path / "p2"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("copy*", "__pycache__"))
    make_copies(str(tmp_path), 3, seed=5)
    copies = sorted(f for f in os.listdir(dst) if f.startswith("copy"))
    assert [c.split("_of_")[0] for c in copies] == ["copy1_L1", "copy2_L2", "copy3_L3"]
    assert validate_dataset(str(tmp_path)) == []
    assert len(ground_truth(str(tmp_path))) == 3
    first = {c: (dst / c).read_text() for c in copies}
    make_copies(str(tmp_path), 3, seed=5)  # repeatable
    assert {c: (dst / c).read_text() for c in copies} == first
