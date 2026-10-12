"""A2: rolling (Karp-Rabin) hash of every k-gram of a token list."""

from __future__ import annotations

import hashlib
from functools import lru_cache

from zplus.types import Token

M = 2**61 - 1  # Mersenne prime modulus
B = 911382323  # fixed base, so results are reproducible across runs


@lru_cache(maxsize=None)
def token_value(text: str) -> int:
    """Stable integer for a token text, in ``[0, M)``.

    Uses blake2b, never the built-in ``hash()`` (randomized per process).
    Results are cached because the vocabulary is tiny after normalization.

    Complexity: O(len(text)) on first sight, O(1) afterwards.
    """
    digest = hashlib.blake2b(text.encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big") % M


def kgram_hashes(tokens: list[Token], k: int) -> list[tuple[int, int]]:
    """Hash every window of ``k`` consecutive tokens.

    Returns ``[(hash, pos)]`` in order, one per k-gram, where ``pos`` is the index
    of the k-gram's first token. ``H_i = sum t_{i+j} * B^(k-1-j) mod M``, rolled as
    ``H_{i+1} = ((H_i - t_i * B^(k-1)) * B + t_{i+k}) mod M``.

    Raises ValueError if ``k < 1``. Fewer than ``k`` tokens gives ``[]``.

    Complexity: O(n) time and space (naive recomputation would be O(nk)).
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    n = len(tokens)
    if n < k:
        return []
    vals = [token_value(t.text) for t in tokens]
    top = pow(B, k - 1, M)  # B^(k-1), used to remove the outgoing token
    h = 0
    for v in vals[:k]:
        h = (h * B + v) % M
    out = [(h, 0)]
    for i in range(n - k):
        h = ((h - vals[i] * top) * B + vals[i + k]) % M
        out.append((h, i + 1))
    return out
