"""S3: the full pipeline, from a folder of files to a Report."""

from __future__ import annotations

import logging
import os
from itertools import groupby

from zplus.astsim import ast_similarity
from zplus.cluster import cluster
from zplus.index import build_index, candidate_pairs, template_hashes
from zplus.loader import TEMPLATE_NAME, load_submissions, problem_dirs
from zplus.rollinghash import kgram_hashes
from zplus.scoring import combine, score_pair
from zplus.tiling import TileIndex, build_tile_index, tile_indexed, tiling_score, too_large
from zplus.types import Config, PairResult, Report, Skipped, Submission
from zplus.winnow import winnow

log = logging.getLogger(__name__)


def group_by_problem(subs: list[Submission]) -> list[tuple[str, list[Submission]]]:
    """Split submissions by problem, in problem then sid order. O(N log N)."""
    ordered = sorted(subs, key=lambda s: (s.problem, s.sid))
    return [(p, list(g)) for p, g in groupby(ordered, key=lambda s: s.problem)]


def scan(
    subs: list[Submission],
    cfg: Config,
    ignore: dict[str, frozenset[int]] | None = None,
    skipped: list[Skipped] | None = None,
    combine_mode: str = "max",
) -> Report:
    """Score every candidate pair of already-loaded submissions.

    ``ignore`` maps a problem name to template hashes to skip for that problem
    (key ``"*"`` applies to all problems).

    Complexity: O(total tokens) for hashing, plus pair counting in the index,
    plus one tiling and one AST comparison per candidate pair.
    """
    ignore = ignore or {}
    skipped = list(skipped or [])
    tokens = {s.sid: s.tokens for s in subs}
    src = {s.sid: s.source for s in subs}
    results: list[PairResult] = []
    n_candidates = 0
    vocab: dict[str, int] = {}  # shared token codes for tiling
    prepared: dict[str, TileIndex] = {}  # each file is indexed once, reused per pair

    def tile_index(sid: str) -> TileIndex:
        if sid not in prepared:
            prepared[sid] = build_tile_index(tokens[sid], cfg.min_match, vocab)
        return prepared[sid]

    for problem, group in group_by_problem(subs):
        fps = {s.sid: winnow(kgram_hashes(s.tokens, cfg.k), cfg.w) for s in group}
        skipped.extend(Skipped(sid, "too short to check") for sid, f in fps.items() if not f)
        drop = ignore.get(problem, frozenset()) | ignore.get("*", frozenset())
        index = build_index(fps, cfg.max_df, drop)
        for c in candidate_pairs(index, cfg.min_shared):
            n_candidates += 1
            sc = score_pair(fps[c.a], fps[c.b])
            na, nb = len(tokens[c.a]), len(tokens[c.b])
            matches = []
            if too_large(na, nb):
                log.warning("tiling skipped for %s, %s: %d x %d tokens", c.a, c.b, na, nb)
            elif na and nb:
                matches = tile_indexed(tile_index(c.a), tile_index(c.b))
                sc.tiling = tiling_score(matches, na, nb)
            if cfg.use_ast:
                sc.ast = ast_similarity(src[c.a], src[c.b])
            combine(sc, combine_mode)
            results.append(PairResult(c.a, c.b, sc, matches))
    results.sort(key=lambda p: (-p.scores.final, p.a, p.b))
    groups = cluster(results, cfg.threshold)
    return Report(
        pairs=results,
        clusters=groups,
        skipped=sorted(skipped, key=lambda s: s.sid),
        config=cfg,
        submissions={s.sid: s for s in subs},
        n_candidates=n_candidates,
    )


def template_ignore(folder: str, cfg: Config, template: str | None) -> dict[str, frozenset[int]]:
    """Template hashes per problem: ``template`` for all, plus any
    ``<problem>/template.py`` found next to the submissions. O(template size)."""
    ignore: dict[str, frozenset[int]] = {}
    if template:
        ignore["*"] = frozenset(template_hashes(template, cfg))
    for problem, directory in problem_dirs(folder).items():
        path = os.path.join(directory, TEMPLATE_NAME)
        if os.path.isfile(path):
            ignore[problem] = frozenset(template_hashes(path, cfg))
    return ignore


def run(
    folder: str,
    cfg: Config,
    template: str | None = None,
    keep_names: bool = False,
    combine_mode: str = "max",
) -> Report:
    """Run the whole pipeline on ``folder`` and return a Report.

    Raises ZplusError if ``folder`` is missing.

    Complexity: see ``scan``; roughly O(N L) plus the candidate work.
    """
    skipped: list[Skipped] = []
    subs = load_submissions(folder, keep_names=keep_names, skipped=skipped)
    ignore = template_ignore(folder, cfg, template)
    return scan(subs, cfg, ignore, skipped, combine_mode)
