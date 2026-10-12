"""B2: greedy string tiling (Wise), used to verify pairs and locate matches."""

from __future__ import annotations

import logging
from array import array
from dataclasses import dataclass

from zplus.types import Match, Token

log = logging.getLogger(__name__)

MAX_CELLS = 4_000_000  # size guard: len(a) * len(b) above this skips tiling


def too_large(n: int, m: int) -> bool:
    """True when a pair is too big to tile (B2's size guard). O(1)."""
    return n * m > MAX_CELLS


def tiling_score(matches: list[Match], len_a: int, len_b: int) -> float:
    """Share of both files covered by tiles: ``2 * sum(len) / (|A| + |B|)``. O(T)."""
    if len_a + len_b == 0:
        return 0.0
    return 2 * sum(m.length for m in matches) / (len_a + len_b)


def _accept_round(
    runs: list[tuple[int, int, int]],
    marked_a: bytearray,
    marked_b: bytearray,
    min_match: int,
) -> tuple[list[Match], list[tuple[int, int, int]]]:
    """Accept every non-overlapping longest run; return tiles and the split rest.

    ``runs`` are maximal runs ``(i, j, length)`` of equal, unmarked tokens.
    """
    longest = max(r[2] for r in runs)
    tiles: list[Match] = []
    for i, j, length in sorted(r for r in runs if r[2] == longest):
        if 1 in marked_a[i : i + length] or 1 in marked_b[j : j + length]:
            continue  # overlaps a tile accepted earlier in this round
        marked_a[i : i + length] = b"\x01" * length
        marked_b[j : j + length] = b"\x01" * length
        tiles.append(Match(i, j, length))
    # Split every surviving run around newly marked tokens.
    rest: list[tuple[int, int, int]] = []
    for i, j, length in runs:
        if 1 not in marked_a[i : i + length] and 1 not in marked_b[j : j + length]:
            rest.append((i, j, length))  # untouched by this round's tiles
            continue
        start = None
        for off in range(length + 1):
            free = off < length and not marked_a[i + off] and not marked_b[j + off]
            if free and start is None:
                start = off
            elif not free and start is not None:
                if off - start >= min_match:
                    rest.append((i + start, j + start, off - start))
                start = None
    return tiles, rest


@dataclass
class TileIndex:
    """One file prepared for tiling: its length and every ``min_match`` window."""

    n: int
    min_match: int
    windows: dict[bytes, list[int]]  # exact window content -> start positions


def build_tile_index(tokens: list[Token], min_match: int, vocab: dict[str, int]) -> TileIndex:
    """Index every window of ``min_match`` tokens by its exact content.

    ``vocab`` maps token text to a small integer and must be shared by every
    file that will be compared, so equal texts get equal codes. Building the
    index once per file lets a scan reuse it for every pair the file is in.

    Complexity: O(n * min_match) time and space.
    """
    codes = array("I", [vocab.setdefault(t.text, len(vocab)) for t in tokens]).tobytes()
    width = 4  # bytes per token code
    span = min_match * width
    windows: dict[bytes, list[int]] = {}
    for j in range(len(tokens) - min_match + 1):
        windows.setdefault(codes[j * width : j * width + span], []).append(j)
    return TileIndex(len(tokens), min_match, windows)


def _initial_runs(xa: TileIndex, xb: TileIndex) -> list[tuple[int, int, int]]:
    """Every maximal run ``(i, j, length)`` of equal tokens with length >= min_match.

    Instead of scanning all n*m cells, intersect the two window indexes, then
    stitch consecutive window matches on the same diagonal into maximal runs. A
    window match at (i, j) whose predecessor (i-1, j-1) is not a match starts a
    maximal run.

    Complexity: O(min(|windows A|, |windows B|) + S) for S matching windows.
    """
    seeds: set[tuple[int, int]] = set()
    for key in xa.windows.keys() & xb.windows.keys():
        js = xb.windows[key]
        for i in xa.windows[key]:
            seeds.update((i, j) for j in js)
    runs = []
    for i, j in seeds:
        if (i - 1, j - 1) in seeds:
            continue  # not the start of its run
        c = 1
        while (i + c, j + c) in seeds:
            c += 1
        runs.append((i, j, c + xa.min_match - 1))
    return runs


def tile_indexed(xa: TileIndex, xb: TileIndex) -> list[Match]:
    """Greedy string tiling on two prepared files (see ``greedy_tiling``).

    Complexity: O(S) to find the runs, plus O(R) per round.
    """
    if xa.min_match != xb.min_match:
        raise ValueError("indexes were built with different min_match")
    runs = _initial_runs(xa, xb)
    marked_a, marked_b = bytearray(xa.n), bytearray(xb.n)
    tiles: list[Match] = []
    while runs:
        new, runs = _accept_round(runs, marked_a, marked_b, xa.min_match)
        tiles.extend(new)
    return tiles


def greedy_tiling(ta: list[Token], tb: list[Token], min_match: int) -> list[Match]:
    """Cover two token sequences with the longest shared, non-overlapping runs.

    Each round takes the longest run ``L`` of equal unmarked tokens; if
    ``L < min_match`` it stops. Every run of length ``L`` that does not overlap a
    tile accepted in the same round becomes a tile (ties: smallest i, then j),
    and its tokens are marked. Tiles come back in acceptance order.

    Equivalent to recomputing Wise's ``run[i][j]`` table every round, but the
    maximal runs are found once through an index of ``min_match``-token windows
    (in the spirit of Running Karp-Rabin GST) and only split as tokens get marked.
    Pairs with ``len(a) * len(b) > 4,000,000`` are skipped with a warning.

    Complexity: O(n + m + S) to find the initial runs (S matching windows), plus
    O(R) per round over the R surviving runs; the table version is O(nm) per round.
    """
    if min_match < 1:
        raise ValueError("min_match must be at least 1")
    n, m = len(ta), len(tb)
    if n == 0 or m == 0:
        return []
    if too_large(n, m):
        log.warning("tiling skipped: %d x %d tokens exceeds the size guard", n, m)
        return []
    vocab: dict[str, int] = {}
    return tile_indexed(build_tile_index(ta, min_match, vocab),
                        build_tile_index(tb, min_match, vocab))


def greedy_tiling_reference(ta: list[Token], tb: list[Token], min_match: int) -> list[Match]:
    """The textbook table version of greedy string tiling, kept for testing.

    Complexity: O(nm) per round.
    """
    n, m = len(ta), len(tb)
    marked_a, marked_b = [False] * n, [False] * m
    tiles: list[Match] = []
    while True:
        run = [[0] * (m + 1) for _ in range(n + 1)]
        longest = 0
        for i in range(n - 1, -1, -1):
            for j in range(m - 1, -1, -1):
                if ta[i].text == tb[j].text and not marked_a[i] and not marked_b[j]:
                    run[i][j] = run[i + 1][j + 1] + 1
                    longest = max(longest, run[i][j])
        if longest < min_match:
            return tiles
        for i in range(n):
            for j in range(m):
                if run[i][j] != longest:
                    continue
                if any(marked_a[i : i + longest]) or any(marked_b[j : j + longest]):
                    continue
                for off in range(longest):
                    marked_a[i + off] = marked_b[j + off] = True
                tiles.append(Match(i, j, longest))
