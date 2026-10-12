import random
import subprocess
import sys

import pytest

from zplus.rollinghash import B, M, kgram_hashes, token_value
from zplus.types import Token


def toks(words):
    return [Token("ID", w, 1) for w in words]


def naive(tokens, k):
    out = []
    for i in range(len(tokens) - k + 1):
        h = 0
        for j in range(k):
            h = (h + token_value(tokens[i + j].text) * pow(B, k - 1 - j, M)) % M
        out.append((h, i))
    return out


def test_rolling_equals_naive_on_random_sequences():
    rng = random.Random(0)
    for _ in range(1000):
        seq = toks(rng.choice("abcdefg") for _ in range(rng.randint(0, 30)))
        k = rng.randint(1, 8)
        assert kgram_hashes(seq, k) == naive(seq, k)


def test_same_kgram_same_hash():
    hs = kgram_hashes(toks("a b c x a b c".split()), 3)
    assert hs[0][0] == hs[4][0]
    assert hs[0][0] != hs[1][0]


def test_length_and_positions():
    seq = toks(list("abcdefghij"))
    for k in range(1, 11):
        out = kgram_hashes(seq, k)
        assert len(out) == len(seq) - k + 1
        assert [p for _, p in out] == list(range(len(out)))
        assert all(0 <= h < M for h, _ in out)


def test_short_input_and_bad_k():
    assert kgram_hashes(toks("a b".split()), 3) == []
    with pytest.raises(ValueError):
        kgram_hashes(toks("a".split()), 0)


def test_stable_across_processes():
    code = ("from zplus.rollinghash import kgram_hashes;from zplus.types import Token;"
            "print(kgram_hashes([Token('ID', w, 1) for w in 'if x ( ) : return'.split()], 3))")
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           check=True).stdout for _ in range(2)}
    assert len(outs) == 1
