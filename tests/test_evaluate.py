import os

import pytest

from zplus.evaluate import (compute_metrics, evaluate, recall_at_precision,
                            recombine, run_experiments, sweep, synthetic_folder)
from zplus.dataset import ground_truth
from zplus.pipeline import run
from zplus.types import Config
from tests.conftest import DATA


def P(a, b):
    return frozenset((a, b))


def test_metrics_on_hand_made_confusion_matrix():
    truth = {P("a", "b"), P("c", "d"), P("e", "f"), P("g", "h")}
    flagged = {P("a", "b"), P("c", "d"), P("x", "y")}
    m = compute_metrics(flagged, truth)
    assert (m.tp, m.fp, m.fn) == (2, 1, 2)
    assert m.precision == pytest.approx(2 / 3)
    assert m.recall == pytest.approx(0.5)
    assert m.f1 == pytest.approx(2 * (2 / 3) * 0.5 / (2 / 3 + 0.5))


def test_nothing_flagged_means_precision_one():
    m = compute_metrics(set(), {P("a", "b")})
    assert m.precision == 1.0 and m.recall == 0.0 and m.f1 == 0.0


def test_recall_by_level():
    truth = {P("p/a", "p/copy1_L1_of_a"), P("p/b", "p/copy2_L3_of_b")}
    levels = {"p/copy1_L1_of_a": 1, "p/copy2_L3_of_b": 3}
    m = compute_metrics({P("p/a", "p/copy1_L1_of_a")}, truth, levels)
    assert m.recall_by_level == {1: 1.0, 2: None, 3: 0.0}


def test_harness_on_two_file_toy_folder(tmp_path):
    src = open(os.path.join(DATA, "p1_merge_intervals", "alice.py")).read()
    (tmp_path / "alice.py").write_text(src)
    (tmp_path / "copy1_L1_of_alice.py").write_text(src.replace("merged", "joined"))
    m = evaluate(str(tmp_path), Config())
    assert (m.tp, m.fp, m.fn) == (1, 0, 0)
    assert m.precision == 1.0 and m.recall == 1.0


def test_raising_threshold_never_raises_recall_on_real_data():
    results = run(DATA, Config()).pairs
    rows = sweep(results, ground_truth(DATA))
    recalls = [m.recall for _, m in rows]
    assert all(a >= b for a, b in zip(recalls, recalls[1:]))


def test_recall_at_precision():
    truth = {P("a", "b"), P("c", "d")}
    scored = [(P("a", "b"), 0.9), (P("x", "y"), 0.8), (P("c", "d"), 0.7)]
    assert recall_at_precision(scored, truth, 1.0) == (0.5, 0.9)
    assert recall_at_precision(scored, truth, 0.6)[0] == 1.0
    assert recall_at_precision([(P("x", "y"), 0.9)], truth, 0.5) == (0.0, None)


def test_recombine_does_not_mutate_input():
    results = run(DATA, Config()).pairs[:5]
    before = [r.scores.final for r in results]
    recombine(results, "ast")
    assert [r.scores.final for r in results] == before


def test_synthetic_folder(tmp_path):
    synthetic_folder(DATA, 5, str(tmp_path / "s"), seed=1)
    files = sorted(os.listdir(tmp_path / "s"))
    assert len(files) == 5
    lines = [(tmp_path / "s" / f).read_text().count("\n") for f in files]
    assert min(lines) >= 60


def test_run_experiments_end_to_end(tmp_path):
    exp = run_experiments(DATA, str(tmp_path), runtime_sizes=(10,))
    for name in ("summary.md", "grid.csv", "sweep.csv", "runtime.csv", "baseline_sweep.csv"):
        assert (tmp_path / name).exists()
    assert len(exp.grid) == 12
    assert exp.test == ["p4_spiral_matrix", "p5_number_of_islands"]
    assert "Held-out results" in (tmp_path / "summary.md").read_text()
