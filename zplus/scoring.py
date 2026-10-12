"""B1: fingerprint similarity scores and the final combined score."""

from __future__ import annotations

from zplus.types import Fingerprint, Scores

COMBINE_MODES = ("max", "mean", "tiling", "ast")


def score_pair(fa: list[Fingerprint], fb: list[Fingerprint]) -> Scores:
    """Jaccard and containment of two fingerprint lists, as hash sets.

    ``tiling`` and ``ast`` start as None; ``final`` starts as containment until
    ``combine`` runs. Empty input gives 0.0 everywhere.

    Complexity: O(|F_A| + |F_B|).
    """
    ha = {fp.hash for fp in fa}
    hb = {fp.hash for fp in fb}
    if not ha or not hb:
        return Scores(0.0, 0.0, None, None, 0.0)
    inter = len(ha & hb)
    jaccard = inter / len(ha | hb)
    containment = max(inter / len(ha), inter / len(hb))
    return Scores(jaccard, containment, None, None, containment)


def combine(s: Scores, mode: str = "max") -> float:
    """Set and return ``s.final``.

    ``primary`` is tiling when B2 ran, else containment. In the default ``"max"``
    mode, ``final = max(primary, ast)`` when the AST score exists, else
    ``primary``. Other modes exist for B5's ablations: ``"mean"`` averages the
    two, ``"tiling"`` ignores AST, ``"ast"`` uses only AST.

    Complexity: O(1).
    """
    primary = s.tiling if s.tiling is not None else s.containment
    if mode == "max":
        final = primary if s.ast is None else max(primary, s.ast)
    elif mode == "mean":
        final = primary if s.ast is None else (primary + s.ast) / 2
    elif mode == "tiling":
        final = primary
    elif mode == "ast":
        final = s.ast if s.ast is not None else 0.0
    else:
        raise ValueError(f"unknown combine mode: {mode}")
    s.final = final
    return final
