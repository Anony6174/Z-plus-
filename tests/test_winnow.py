import random

import pytest

from zplus.rollinghash import kgram_hashes
from zplus.types import Fingerprint, Token
from zplus.winnow import winnow


def brute(hashes, w):
    if not hashes:
        return []
    if len(hashes) < w:
        i = max(range(len(hashes)), key=lambda i: (-hashes[i][0], i))
        return [Fingerprint(*hashes[i])]
    out, last = [], -1
    for s in range(len(hashes) - w + 1):
        window = range(s, s + w)
        best = min(window, key=lambda i: (hashes[i][0], -i))
        if best != last:
            out.append(Fingerprint(*hashes[best]))
            last = best
    return out


def test_deque_equals_brute_force():
    rng = random.Random(1)
    for _ in range(500):
        hs = [(rng.randint(0, 20), i) for i in range(rng.randint(0, 60))]
        w = rng.randint(1, 8)
        assert winnow(hs, w) == brute(hs, w)


def test_guarantee_shared_block_always_found():
    rng = random.Random(2)
    k, w = 5, 4
    vocab = [str(i) for i in range(40)]
    for _ in range(1000):
        block = [rng.choice(vocab) for _ in range(w + k - 1 + rng.randint(0, 5))]
        a = [rng.choice(vocab) for _ in range(rng.randint(0, 50))]
        b = [rng.choice(vocab) for _ in range(rng.randint(0, 50))]
        a[rng.randint(0, len(a)):0] = block
        b[rng.randint(0, len(b)):0] = block
        fa = {f.hash for f in winnow(kgram_hashes([Token("ID", t, 1) for t in a], k), w)}
        fb = {f.hash for f in winnow(kgram_hashes([Token("ID", t, 1) for t in b], k), w)}
        assert fa & fb


def test_density_close_to_two_over_w_plus_one():
    rng = random.Random(3)
    hs = [(rng.getrandbits(61), i) for i in range(20000)]
    for w in (2, 4, 8):
        kept = len(winnow(hs, w)) / len(hs)
        assert abs(kept - 2 / (w + 1)) < 0.03


def test_positions_strictly_increasing():
    rng = random.Random(4)
    hs = [(rng.randint(0, 5), i) for i in range(500)]
    pos = [f.pos for f in winnow(hs, 4)]
    assert all(a < b for a, b in zip(pos, pos[1:]))


def test_edge_cases():
    assert winnow([], 4) == []
    assert winnow([(5, 0), (3, 1), (3, 2)], 4) == [Fingerprint(3, 2)]  # rightmost min
    hs = [(9, 0), (7, 1), (8, 2)]
    assert winnow(hs, 1) == [Fingerprint(*h) for h in hs]
    assert winnow([(1, i) for i in range(10)], 3) == [Fingerprint(1, i) for i in range(2, 10)]
    with pytest.raises(ValueError):
        winnow(hs, 0)
