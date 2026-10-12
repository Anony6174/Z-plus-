import json
import os

from zplus.pipeline import group_by_problem, run
from zplus.report import to_json
from zplus.types import Config
from tests.conftest import FIXTURES

SIX = os.path.join(FIXTURES, "six")


def test_six_file_fixture_flags_the_copies():
    report = run(SIX, Config())
    flagged = {(p.a, p.b) for p in report.flagged()}
    assert flagged == {("six/alice", "six/copy1_L1_of_alice"),
                       ("six/carol", "six/copy2_L2_of_carol")}
    assert report.clusters == [{"six/alice", "six/copy1_L1_of_alice"},
                               {"six/carol", "six/copy2_L2_of_carol"}]
    assert [s.sid for s in report.skipped] == ["six/tiny"]


def test_six_file_fixture_json_is_expected():
    data = to_json(run(SIX, Config()))
    assert [(p["a"], p["b"]) for p in data["pairs"]] == [
        ("six/alice", "six/copy1_L1_of_alice"), ("six/carol", "six/copy2_L2_of_carol")]
    assert data["clusters"] == [["six/alice", "six/copy1_L1_of_alice"],
                                ["six/carol", "six/copy2_L2_of_carol"]]
    assert data["skipped"] == [{"sid": "six/tiny", "reason": "too short to check"}]
    top = data["pairs"][0]
    assert top["scores"]["final"] == 1.0
    assert all(set(m) == {"a_lines", "b_lines", "tokens"} for m in top["matches"])
    json.dumps(data)


def test_no_ast_and_determinism():
    a = run(SIX, Config(use_ast=False))
    assert all(p.scores.ast is None for p in a.pairs)
    b = run(SIX, Config(use_ast=False))
    assert [(p.a, p.b, p.scores, p.matches) for p in a.pairs] == \
           [(p.a, p.b, p.scores, p.matches) for p in b.pairs]


def test_group_by_problem():
    from zplus.loader import load_submissions
    subs = load_submissions(os.path.join(FIXTURES, "toy_truth"))
    groups = group_by_problem(subs)
    assert [p for p, _ in groups] == ["toy_truth"]
