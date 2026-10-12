import pytest

from zplus.scoring import combine, score_pair
from zplus.types import Fingerprint, Scores


def fp(*hashes):
    return [Fingerprint(h, i) for i, h in enumerate(hashes)]


def test_known_scores():
    s = score_pair(fp(1, 2, 3, 4), fp(3, 4, 5, 6, 7, 8))
    assert s.jaccard == pytest.approx(2 / 8)
    assert s.containment == pytest.approx(2 / 4)
    assert s.tiling is None and s.ast is None


def test_identical_and_disjoint():
    s = score_pair(fp(1, 2, 3), fp(3, 2, 1, 1))
    assert s.jaccard == 1.0 and s.containment == 1.0
    d = score_pair(fp(1, 2), fp(3, 4))
    assert d.jaccard == 0.0 and d.containment == 0.0


def test_subset_has_full_containment():
    s = score_pair(fp(1, 2), fp(1, 2, 3, 4, 5))
    assert s.containment == 1.0
    assert s.jaccard < 1.0


def test_empty_input():
    for a, b in ((fp(), fp()), (fp(1), fp()), (fp(), fp(1))):
        s = score_pair(a, b)
        assert (s.jaccard, s.containment, s.final) == (0.0, 0.0, 0.0)


def test_combine_cases():
    s = Scores(0.2, 0.5, None, None, 0.0)
    assert combine(s) == 0.5 and s.final == 0.5  # containment fallback
    s = Scores(0.2, 0.5, 0.7, None, 0.0)
    assert combine(s) == 0.7
    s = Scores(0.2, 0.5, 0.7, 0.9, 0.0)
    assert combine(s) == 0.9
    s = Scores(0.2, 0.5, None, 0.3, 0.0)
    assert combine(s) == 0.5


def test_combine_modes():
    s = Scores(0.2, 0.5, 0.6, 1.0, 0.0)
    assert combine(s, "mean") == pytest.approx(0.8)
    assert combine(s, "tiling") == 0.6
    assert combine(s, "ast") == 1.0
    with pytest.raises(ValueError):
        combine(s, "median")
