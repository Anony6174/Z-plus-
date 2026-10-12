import os
import time

from zplus.dataset import (check_solution, copy_levels, ground_truth, parse_name,
                           validate_dataset)
from tests.conftest import DATA, FIXTURES

SOL = os.path.join(FIXTURES, "solutions")
TESTS = os.path.join(SOL, "tests.json")


def test_ground_truth_on_toy_folder():
    truth = ground_truth(os.path.join(FIXTURES, "toy_truth"))
    p = "toy_truth/"
    expected = {
        frozenset((p + "alice", p + "copy1_L1_of_alice")),
        frozenset((p + "alice", p + "copy2_L3_of_alice")),
        frozenset((p + "copy1_L1_of_alice", p + "copy2_L3_of_alice")),
        frozenset((p + "bob", p + "copy1_L2_of_bob")),
    }
    assert truth == expected


def test_copy_levels_and_parse_name():
    levels = copy_levels(os.path.join(FIXTURES, "toy_truth"))
    assert levels == {"toy_truth/copy1_L1_of_alice": 1, "toy_truth/copy2_L3_of_alice": 3,
                      "toy_truth/copy1_L2_of_bob": 2}
    assert parse_name("copy12_L2_of_mary_ann.py") == ("mary_ann", 2)
    assert parse_name("copy_of_x.py") == ("copy_of_x", None)


def test_check_solution_accepts_and_rejects():
    assert check_solution(os.path.join(SOL, "good.py"), TESTS)
    assert not check_solution(os.path.join(SOL, "wrong.py"), TESTS)
    assert not check_solution(os.path.join(SOL, "printer.py"), TESTS)


def test_check_solution_cuts_off_infinite_loop():
    start = time.perf_counter()
    assert not check_solution(os.path.join(SOL, "loop.py"), TESTS, timeout=1.0)
    assert time.perf_counter() - start < 5


def test_validate_detects_problems(tmp_path):
    (tmp_path / "tests.json").write_text(open(TESTS).read())
    (tmp_path / "a.py").write_text(open(os.path.join(SOL, "good.py")).read())
    (tmp_path / "b.py").write_text(open(os.path.join(SOL, "good.py")).read())
    (tmp_path / "copy1_L1_of_ghost.py").write_text("def solve(a, b):\n    return b + a\n")
    errors = validate_dataset(str(tmp_path))
    assert any("byte-identical" in e for e in errors)
    assert any("origin ghost.py" in e for e in errors)


def test_real_dataset_is_valid():
    assert validate_dataset(DATA) == []
    truth = ground_truth(DATA)
    assert len(truth) == 30
    problems = {s.split("/")[0] for p in truth for s in p}
    assert len(problems) == 5
