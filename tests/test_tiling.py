import random

import pytest

from zplus.tiling import greedy_tiling, greedy_tiling_reference, tiling_score
from zplus.types import Match, Token


def toks(s):
    return [Token("ID", c, 1) for c in s]


def test_identical_files_one_tile():
    a = toks("abcdefghijklmnop")
    tiles = greedy_tiling(a, a, 4)
    assert tiles == [Match(0, 0, 16)]
    assert tiling_score(tiles, 16, 16) == 1.0


def test_unrelated_files():
    tiles = greedy_tiling(toks("aaaaaaaaaa"), toks("bbbbbbbbbb"), 3)
    assert tiles == []
    assert tiling_score(tiles, 10, 10) == 0.0


def test_moved_block_found_with_correct_starts():
    block = "QRSTUVWXYZ"
    a = toks("abc" + block + "defghij")
    b = toks("mnopqrs" + block + "tu")
    assert greedy_tiling(a, b, 5) == [Match(3, 7, 10)]


def test_two_separate_blocks_two_tiles():
    a = toks("ABCDEFGH" + "xx" + "12345678")
    b = toks("12345678" + "yyy" + "ABCDEFGH")
    tiles = greedy_tiling(a, b, 5)
    assert sorted(tiles, key=lambda m: m.a_start) == [Match(0, 11, 8), Match(10, 0, 8)]


def test_ties_broken_by_smallest_i_then_j():
    a = toks("abcdabcd")
    b = toks("abcd")
    assert greedy_tiling(a, b, 2) == [Match(0, 0, 4)]


def test_random_properties_and_reference_equivalence():
    rng = random.Random(7)
    for _ in range(400):
        alphabet = rng.choice(["ab", "abc", "abcdefgh"])
        a = toks("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40))))
        b = toks("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40))))
        mm = rng.randint(1, 5)
        tiles = greedy_tiling(a, b, mm)
        assert tiles == greedy_tiling_reference(a, b, mm)
        used_a, used_b = set(), set()
        for t in tiles:
            assert t.length >= mm
            span_a = set(range(t.a_start, t.a_start + t.length))
            span_b = set(range(t.b_start, t.b_start + t.length))
            assert not (span_a & used_a) and not (span_b & used_b)
            used_a |= span_a
            used_b |= span_b
            assert [x.text for x in a[t.a_start:t.a_start + t.length]] == \
                   [x.text for x in b[t.b_start:t.b_start + t.length]]


def test_deterministic():
    rng = random.Random(8)
    a = toks("".join(rng.choice("abc") for _ in range(200)))
    b = toks("".join(rng.choice("abc") for _ in range(200)))
    assert greedy_tiling(a, b, 3) == greedy_tiling(a, b, 3)


def test_size_guard(caplog):
    a = toks("a" * 2001)
    assert greedy_tiling(a, a, 8) == []
    assert "size guard" in caplog.text


def test_bad_min_match_and_empty():
    with pytest.raises(ValueError):
        greedy_tiling(toks("abc"), toks("abc"), 0)
    assert greedy_tiling([], toks("abc"), 1) == []
    assert tiling_score([], 0, 0) == 0.0
