import os
import random
import time

from zplus.index import build_index, candidate_pairs, df_cap, fingerprints, template_hashes
from zplus.pipeline import run
from zplus.types import Config, Fingerprint
from tests.conftest import FIXTURES


def fp(*hashes):
    return [Fingerprint(h, i) for i, h in enumerate(hashes)]


def test_hand_made_counts():
    fps = {"p/a": fp(1, 2, 3, 4), "p/b": fp(2, 3, 4, 9), "p/c": fp(4, 7), "p/d": fp(8)}
    index = build_index(fps, max_df=1.0)
    assert index[4] == {"p/a", "p/b", "p/c"}
    pairs = candidate_pairs(index, min_shared=1)
    assert [(c.a, c.b, c.shared) for c in pairs] == [
        ("p/a", "p/b", 3), ("p/a", "p/c", 1), ("p/b", "p/c", 1)]
    assert [(c.a, c.b) for c in candidate_pairs(index, 2)] == [("p/a", "p/b")]


def test_boilerplate_dropped_only_when_n_is_large():
    small = {f"p/s{i}": fp(42, 100 + i) for i in range(3)}
    assert 42 in build_index(small, max_df=0.3)  # floor of 3 keeps it
    big = {f"p/s{i}": fp(42, 100 + i) for i in range(20)}
    assert df_cap(20, 0.3) == 6
    assert 42 not in build_index(big, max_df=0.3)


def test_ignore_set():
    fps = {"p/a": fp(1, 2, 3), "p/b": fp(1, 2, 3)}
    assert build_index(fps, 1.0, frozenset({1, 2, 3})) == {}


def test_pairs_are_ordered_and_unique():
    rng = random.Random(5)
    fps = {f"p/{n}": fp(*(rng.randint(0, 30) for _ in range(15))) for n in "zyxwvu"}
    pairs = candidate_pairs(build_index(fps, 1.0), 1)
    keys = [(c.a, c.b) for c in pairs]
    assert all(a < b for a, b in keys)
    assert len(keys) == len(set(keys))
    assert [c.shared for c in pairs] == sorted((c.shared for c in pairs), reverse=True)


def test_one_submission_and_identical_files():
    assert candidate_pairs(build_index({"p/a": fp(1, 2)}, 1.0), 1) == []
    same = {"p/a": fp(1, 2, 3), "p/b": fp(1, 2, 3)}
    assert candidate_pairs(build_index(same, 1.0), 1)[0].shared == 3


def test_template_submission_gives_no_candidates():
    folder = os.path.join(FIXTURES, "template_case")
    template = os.path.join(folder, "template.py")
    assert template_hashes(template, Config())
    assert run(folder, Config(), template).pairs == []
    assert run(folder, Config()).pairs  # without the template they match


def test_template_beside_submissions_is_detected(tmp_path):
    template = os.path.join(FIXTURES, "template_case", "template.py")
    problem = tmp_path / "p1"
    problem.mkdir()
    for name in ("template.py", "alice.py", "bob.py"):
        (problem / name).write_text(open(template).read())
    assert run(str(tmp_path), Config()).pairs == []


def test_too_short_is_recorded():
    report = run(os.path.join(FIXTURES, "six"), Config())
    assert any(s.sid == "six/tiny" and "too short" in s.reason for s in report.skipped)


def test_thousand_submissions_quickly():
    rng = random.Random(6)
    fps = {f"p/{i:04d}": fp(*(rng.getrandbits(40) for _ in range(40))) for i in range(1000)}
    for i in range(0, 1000, 10):  # plant some shared fingerprints
        fps[f"p/{i:04d}"] += fp(*range(10))
    start = time.perf_counter()
    pairs = candidate_pairs(build_index(fps, 0.3), 3)
    elapsed = time.perf_counter() - start
    assert elapsed < 5
    assert all(c.shared >= 3 for c in pairs)


def test_fingerprints_helper():
    assert fingerprints("x = 1\n", Config()) == []  # 4 tokens < k
    assert fingerprints(open(os.path.join(FIXTURES, "six", "alice.py")).read(), Config())
