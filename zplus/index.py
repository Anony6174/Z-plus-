"""A4: inverted index from fingerprint hash to submissions, and candidate pairs."""

from __future__ import annotations

import math
from collections import Counter

from zplus.loader import read_source
from zplus.normalize import normalize
from zplus.rollinghash import kgram_hashes
from zplus.types import Candidate, Config, Fingerprint
from zplus.winnow import winnow

MIN_DF_CAP = 3  # never drop a hash found in 3 or fewer submissions


def fingerprints(source: str, cfg: Config, keep_names: bool = False) -> list[Fingerprint]:
    """Normalize, hash and winnow one source text. O(L)."""
    return winnow(kgram_hashes(normalize(source, keep_names), cfg.k), cfg.w)


def template_hashes(template_path: str, cfg: Config) -> set[int]:
    """Fingerprint hashes of the starter file; these are ignored everywhere.

    Complexity: O(L) in the template's length.
    """
    return {fp.hash for fp in fingerprints(read_source(template_path), cfg)}


def df_cap(n_subs: int, max_df: float) -> int:
    """Largest document frequency a hash may have before it counts as boilerplate.

    Complexity: O(1).
    """
    return max(MIN_DF_CAP, math.ceil(max_df * n_subs))


def build_index(
    fps: dict[str, list[Fingerprint]],
    max_df: float,
    ignore: frozenset[int] = frozenset(),
) -> dict[int, set[str]]:
    """Map every fingerprint hash to the set of sids that contain it.

    Hashes in ``ignore`` (template code) are skipped. Hashes found in more than
    ``max(3, ceil(max_df * N))`` submissions are dropped as boilerplate, like
    stop words in a search engine. Submissions without fingerprints never appear.

    Complexity: O(total fingerprints) time and space.
    """
    index: dict[int, set[str]] = {}
    for sid, prints in fps.items():
        for fp in prints:
            if fp.hash not in ignore:
                index.setdefault(fp.hash, set()).add(sid)
    cap = df_cap(len(fps), max_df)
    return {h: sids for h, sids in index.items() if len(sids) <= cap}


def candidate_pairs(index: dict[int, set[str]], min_shared: int) -> list[Candidate]:
    """Pairs of sids that share at least ``min_shared`` distinct hashes.

    Each pair appears once with ``a < b``; results are sorted by shared count,
    highest first, then by sid for determinism.

    Complexity: O(sum over hashes of |posting list|^2).
    """
    counts: Counter[tuple[str, str]] = Counter()
    for sids in index.values():
        ordered = sorted(sids)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                counts[(a, b)] += 1
    pairs = [Candidate(a, b, n) for (a, b), n in counts.items() if n >= min_shared]
    pairs.sort(key=lambda c: (-c.shared, c.a, c.b))
    return pairs
