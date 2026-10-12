"""B5: measure precision, recall and F1, pick parameters, and write results.

Every pair of files inside one problem is a prediction. A pair is flagged if
its final score reaches the threshold; a pair that never became a candidate
counts as not flagged. Truth comes from A5's ``ground_truth``.
"""

from __future__ import annotations

import csv
import difflib
import logging
import os
import random
import shutil
import tempfile
import time
from dataclasses import dataclass, replace
from itertools import combinations

from zplus.dataset import copy_levels, ground_truth
from zplus.loader import load_submissions, read_source
from zplus.mutate import mutate
from zplus.pipeline import run
from zplus.scoring import combine
from zplus.types import Config, Metrics, PairResult

log = logging.getLogger(__name__)

Pair = frozenset[str]
THRESHOLDS = [round(0.10 + 0.05 * i, 2) for i in range(17)]  # 0.10 .. 0.90
GRID_K = (3, 5, 7, 9)
GRID_W = (2, 4, 6)
N_TUNE = 3  # problems 1-3 tune, the rest are held out
RUNTIME_SIZES = (50, 100, 200, 400)

# Reference palette (light chart surface): slot 1 blue, slot 2 orange, chrome inks.
_SURFACE, _INK, _INK2, _MUTED, _GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
_BLUE, _ORANGE = "#2a78d6", "#eb6834"


# ------------------------------------------------------------------- metrics
def problem_of(sid: str) -> str:
    """Problem part of a sid. O(len)."""
    return sid.split("/", 1)[0]


def compute_metrics(
    flagged: set[Pair], truth: set[Pair], levels: dict[str, int] | None = None
) -> Metrics:
    """Precision, recall, F1 and recall by mutation level.

    Precision is defined as 1.0 when nothing is flagged; recall is 0.0 when there
    are no positives (callers skip such problems). A positive pair's level is the
    highest level of the copies in it.

    Complexity: O(|flagged| + |truth|).
    """
    tp = len(flagged & truth)
    fp = len(flagged - truth)
    fn = len(truth - flagged)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    by_level: dict[int, float | None] = {}
    if levels is not None:
        for lv in (1, 2, 3):
            pos = {p for p in truth if max(levels.get(s, 0) for s in p) == lv}
            by_level[lv] = len(pos & flagged) / len(pos) if pos else None
    return Metrics(precision, recall, f1, tp, fp, fn, by_level)


def flagged_pairs(results: list[PairResult], threshold: float) -> set[Pair]:
    """Pairs whose final score reaches ``threshold``. O(P)."""
    return {frozenset((r.a, r.b)) for r in results if r.scores.final >= threshold}


def restrict(pairs, problems: set[str]):
    """Keep pairs (sets or PairResults) whose files belong to ``problems``. O(P)."""
    out = []
    for p in pairs:
        sid = p.a if isinstance(p, PairResult) else next(iter(p))
        if problem_of(sid) in problems:
            out.append(p)
    return type(pairs)(out) if isinstance(pairs, set) else out


def recombine(results: list[PairResult], mode: str) -> list[PairResult]:
    """Copies of ``results`` with ``final`` recomputed by ``combine(mode)``. O(P)."""
    out = []
    for r in results:
        s = replace(r.scores)
        combine(s, mode)
        out.append(PairResult(r.a, r.b, s, r.matches))
    return out


def evaluate(folder: str, cfg: Config) -> Metrics:
    """Run the pipeline on ``folder`` and score it against the ground truth.

    Complexity: one pipeline run plus O(P) bookkeeping.
    """
    results = run(folder, cfg).pairs
    return compute_metrics(
        flagged_pairs(results, cfg.threshold), ground_truth(folder), copy_levels(folder)
    )


def sweep(
    results: list[PairResult], truth: set[Pair], thresholds: list[float] = THRESHOLDS
) -> list[tuple[float, Metrics]]:
    """Metrics at every threshold, reusing one set of scored pairs. O(T * P)."""
    return [(t, compute_metrics(flagged_pairs(results, t), truth)) for t in thresholds]


def best_threshold(rows: list[tuple[float, Metrics]]) -> tuple[float, Metrics]:
    """Threshold with the highest F1 (ties: the higher, more conservative one). O(T)."""
    return max(rows, key=lambda tm: (round(tm[1].f1, 9), tm[0]))


# ------------------------------------------------------------------ baseline
def baseline_scores(folder: str) -> list[tuple[Pair, float]]:
    """difflib ratio on the raw text of every same-problem pair. O(N^2 * L^2) worst case."""
    subs = load_submissions(folder)
    by_problem: dict[str, list] = {}
    for s in subs:
        by_problem.setdefault(s.problem, []).append(s)
    out = []
    for group in by_problem.values():
        for a, b in combinations(group, 2):
            ratio = difflib.SequenceMatcher(None, a.source, b.source).ratio()
            out.append((frozenset((a.sid, b.sid)), ratio))
    return out


def recall_at_precision(
    scored: list[tuple[Pair, float]], truth: set[Pair], min_precision: float
) -> tuple[float, float | None]:
    """Best recall over all thresholds whose precision reaches ``min_precision``.

    Returns ``(recall, threshold)``; ``(0.0, None)`` if no threshold qualifies.
    Complexity: O(P log P).
    """
    ranked = sorted(scored, key=lambda ps: -ps[1])
    best, best_t, tp, fp = 0.0, None, 0, 0
    for i, (pair, score) in enumerate(ranked):
        tp += pair in truth
        fp += pair not in truth
        if i + 1 < len(ranked) and ranked[i + 1][1] == score:
            continue  # a threshold cannot split tied scores
        recall = tp / len(truth) if truth else 0.0
        if tp / (tp + fp) >= min_precision and recall > best:
            best, best_t = recall, score
    return best, best_t


# ------------------------------------------------------------------- runtime
def synthetic_folder(source_folder: str, n: int, dest: str, seed: int = 0) -> None:
    """Write ``n`` files of roughly 100 lines into ``dest`` (one problem).

    Each file concatenates one original from each problem, then mutates it at a
    random level, so files are realistic in size and mostly distinct.

    Complexity: O(n * file size).
    """
    rng = random.Random(seed)
    originals: dict[str, list[str]] = {}
    for s in load_submissions(source_folder):
        if not s.author.startswith("copy"):
            originals.setdefault(s.problem, []).append(s.source)
    os.makedirs(dest, exist_ok=True)
    for i in range(n):
        parts = [rng.choice(originals[p]) for p in sorted(originals)]
        src = "\n\n".join(parts)
        level = rng.choice((0, 1, 2, 3))
        if level:
            src = mutate(src, level, seed * 100_003 + i)
        with open(os.path.join(dest, f"s{i:04d}.py"), "w", encoding="utf-8") as fh:
            fh.write(src)


def time_scans(
    source_folder: str, cfg: Config, sizes=RUNTIME_SIZES, seed: int = 0
) -> list[tuple[int, float, float]]:
    """Seconds to scan synthetic folders of each size: ``(n, seconds, avg lines)``."""
    rows = []
    for n in sizes:
        tmp = tempfile.mkdtemp(prefix="zplus_rt_")
        try:
            synthetic_folder(source_folder, n, os.path.join(tmp, "synthetic"), seed)
            lines = [
                read_source(os.path.join(tmp, "synthetic", f)).count("\n")
                for f in os.listdir(os.path.join(tmp, "synthetic"))
            ]
            start = time.perf_counter()
            run(os.path.join(tmp, "synthetic"), cfg)
            rows.append((n, time.perf_counter() - start, sum(lines) / len(lines)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return rows


# --------------------------------------------------------------------- plots
def _style_axes(ax) -> None:
    ax.set_facecolor(_SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c3c2b7")
    ax.tick_params(colors=_MUTED, labelcolor=_INK2)
    ax.grid(True, color=_GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_pr(curves: dict[str, list[tuple[float, float]]], path: str) -> bool:
    """Precision-recall curves as a PNG; False if matplotlib is unavailable."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not installed; skipping %s", path)
        return False
    fig, ax = plt.subplots(figsize=(6.4, 4.6), facecolor=_SURFACE)
    _style_axes(ax)
    for (label, pts), color in zip(curves.items(), (_BLUE, _ORANGE)):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=4, label=label)
        # Label the lowest-threshold end (bottom of the curve), clear of the top edge.
        right = xs[0] > 0.8
        ax.annotate(label, (xs[0], ys[0]), xytext=(-8 if right else 8, 0),
                    textcoords="offset points", color=_INK2, fontsize=9, va="center",
                    ha="right" if right else "left")
    ax.set_xlabel("Recall", color=_INK2)
    ax.set_ylabel("Precision", color=_INK2)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_title("Precision vs recall, threshold sweep (all problems)", color=_INK, loc="left")
    ax.legend(frameon=False, labelcolor=_INK2, loc="lower center")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


def plot_runtime(rows: list[tuple[int, float, float]], path: str) -> bool:
    """Scan time against file count as a PNG; False if matplotlib is unavailable."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        log.warning("matplotlib not installed; skipping %s", path)
        return False
    fig, ax = plt.subplots(figsize=(6.4, 4.2), facecolor=_SURFACE)
    _style_axes(ax)
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    ax.plot(xs, ys, color=_BLUE, linewidth=2, marker="o", markersize=6)
    for x, y in zip(xs, ys):
        ax.annotate(f"{y:.1f}s", (x, y), xytext=(0, 8), textcoords="offset points",
                    ha="center", color=_INK2, fontsize=9)
    ax.axhline(10, color=_MUTED, linewidth=1, linestyle="--")
    ax.annotate("10 s goal", (xs[0], 10), xytext=(0, 4), textcoords="offset points",
                color=_MUTED, fontsize=9)
    ax.set_xlabel("Submissions in one problem", color=_INK2)
    ax.set_ylabel("Scan time (seconds)", color=_INK2)
    ax.set_ylim(0, max(max(ys) * 1.2, 11))
    ax.set_title("Scan time by folder size (synthetic ~100-line files)", color=_INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return True


# ---------------------------------------------------------------- experiments
@dataclass
class GridCell:
    """One (k, w) setting measured on the tuning problems."""

    f1: float  # best F1 over the threshold sweep
    threshold: float  # where that F1 is reached
    candidate_recall: float  # share of positive pairs that became candidates
    candidates: int  # candidate pairs (a proxy for the work done)


@dataclass
class Experiments:
    """Everything ``run_experiments`` measured, for the summary and the CLI."""

    tune: list[str]
    test: list[str]
    chosen: Config
    grid: dict[tuple[int, int], GridCell]
    sweep_rows: list[tuple[float, Metrics]]
    heldout: Metrics
    overall: Metrics
    ablations: dict[str, tuple[float, Metrics]]  # name -> (tuned threshold, held-out)
    baseline_recall: float
    baseline_threshold: float | None
    zplus_recall_all: float
    zplus_precision_all: float
    runtime: list[tuple[int, float, float]]
    dataset: dict[str, int]


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def _write_csv(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def run_experiments(
    folder: str, out: str, runtime_sizes=RUNTIME_SIZES, seed: int = 0
) -> Experiments:
    """Run every experiment with fixed seeds and write CSVs, PNGs and summary.md.

    1. Grid over k and w on the tuning problems picks k, w and the threshold.
    2. Threshold sweep at the chosen k and w (CSV and PR curve).
    3. Recall by mutation level on the held-out problems.
    4. Ablations: tiling only, AST only, mean instead of max, normalization off.
    5. difflib baseline: recall at the precision z-plus reaches.
    6. Runtime for 50 to 400 synthetic submissions.

    Complexity: 12 grid runs + 2 ablation runs + O(N^2) baseline + runtime scans.
    """
    os.makedirs(out, exist_ok=True)
    truth = ground_truth(folder)
    levels = copy_levels(folder)
    problems = sorted({problem_of(s) for p in truth for s in p} | {
        s.problem for s in load_submissions(folder)
    })
    tune, test = set(problems[:N_TUNE]), set(problems[N_TUNE:])
    truth_tune, truth_test = restrict(truth, tune), restrict(truth, test)

    # 1. Parameter grid on the tuning problems. k and w decide which pairs become
    # candidates (and Jaccard/containment); tiling and AST do not depend on them.
    # Pick the best F1, then the best candidate recall, then the fewest candidates.
    grid: dict[tuple[int, int], GridCell] = {}
    cache: dict[tuple[int, int], list[PairResult]] = {}
    for k in GRID_K:
        for w in GRID_W:
            res = run(folder, replace(Config(), k=k, w=w)).pairs
            cache[(k, w)] = res
            tune_res = restrict(res, tune)
            t, m = best_threshold(sweep(tune_res, truth_tune))
            cands = {frozenset((r.a, r.b)) for r in tune_res}
            cand_recall = len(cands & truth_tune) / len(truth_tune) if truth_tune else 0.0
            grid[(k, w)] = GridCell(m.f1, t, cand_recall, len(cands))
    (k, w) = max(grid, key=lambda kw: (round(grid[kw].f1, 9),
                                        round(grid[kw].candidate_recall, 9),
                                        -grid[kw].candidates, kw))
    threshold = grid[(k, w)].threshold
    chosen = replace(Config(), k=k, w=w, threshold=threshold)
    _write_csv(
        os.path.join(out, "grid.csv"),
        ["k", "w", "best_f1_tune", "threshold", "candidate_recall_tune", "candidates_tune"],
        [[kk, ww, f"{g.f1:.4f}", g.threshold, f"{g.candidate_recall:.4f}", g.candidates]
         for (kk, ww), g in sorted(grid.items())],
    )

    # 2. Threshold sweep at the chosen k, w (all problems, for the PR curve).
    results = cache[(k, w)]
    sweep_rows = sweep(results, truth)
    _write_csv(
        os.path.join(out, "sweep.csv"),
        ["threshold", "precision", "recall", "f1", "tp", "fp", "fn"],
        [[t, f"{m.precision:.4f}", f"{m.recall:.4f}", f"{m.f1:.4f}", m.tp, m.fp, m.fn]
         for t, m in sweep_rows],
    )

    # 3. Held-out metrics and recall by level.
    heldout = compute_metrics(
        flagged_pairs(restrict(results, test), threshold), truth_test, levels
    )
    overall = compute_metrics(flagged_pairs(results, threshold), truth, levels)

    # 4. Ablations at the chosen k and w. Each variant gets its own threshold,
    # tuned on the tuning problems like the main model, and is scored held-out.
    variants = {
        "z-plus (max of tiling, AST)": results,
        "tiling only": recombine(results, "tiling"),
        "AST only": recombine(results, "ast"),
        "mean instead of max": recombine(results, "mean"),
        "normalization off (names kept)": run(folder, chosen, keep_names=True).pairs,
    }
    ablations: dict[str, tuple[float, Metrics]] = {}
    for name, res in variants.items():
        t_v, _ = best_threshold(sweep(restrict(res, tune), truth_tune))
        held = compute_metrics(flagged_pairs(restrict(res, test), t_v), truth_test, levels)
        ablations[name] = (t_v, held)

    # 5. Raw-text baseline at equal precision, all problems.
    base = baseline_scores(folder)
    base_recall, base_t = recall_at_precision(base, truth, overall.precision)
    base_curve = []
    for t in THRESHOLDS:
        m = compute_metrics({p for p, s in base if s >= t}, truth)
        base_curve.append((m.recall, m.precision))
    zplus_curve = [(m.recall, m.precision) for _, m in sweep_rows]
    _write_csv(
        os.path.join(out, "baseline_sweep.csv"),
        ["threshold", "precision", "recall"],
        [[t, f"{p:.4f}", f"{r:.4f}"] for t, (r, p) in zip(THRESHOLDS, base_curve)],
    )
    plot_pr({"z-plus": zplus_curve, "difflib baseline": base_curve},
            os.path.join(out, "pr_curve.png"))

    # 6. Runtime.
    runtime = time_scans(folder, chosen, runtime_sizes, seed)
    _write_csv(
        os.path.join(out, "runtime.csv"),
        ["submissions", "seconds", "avg_lines"],
        [[n, f"{s:.3f}", f"{ln:.0f}"] for n, s, ln in runtime],
    )
    plot_runtime(runtime, os.path.join(out, "runtime.png"))

    n_files = len(load_submissions(folder))
    n_pairs = sum(
        len(list(combinations(range(c), 2)))
        for c in _counts_by_problem(folder).values()
    )
    exp = Experiments(
        tune=sorted(tune), test=sorted(test), chosen=chosen, grid=grid,
        sweep_rows=sweep_rows, heldout=heldout, overall=overall, ablations=ablations,
        baseline_recall=base_recall, baseline_threshold=base_t,
        zplus_recall_all=overall.recall, zplus_precision_all=overall.precision,
        runtime=runtime,
        dataset={"files": n_files, "problems": len(problems), "positives": len(truth),
                 "negatives": n_pairs - len(truth), "copies": len(levels)},
    )
    with open(os.path.join(out, "summary.md"), "w") as fh:
        fh.write(summary_markdown(exp))
    return exp


def _counts_by_problem(folder: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in load_submissions(folder):
        counts[s.problem] = counts.get(s.problem, 0) + 1
    return counts


def summary_markdown(e: Experiments) -> str:
    """Render the experiment results as Markdown. O(size of results)."""
    c, h = e.chosen, e.heldout
    lines = [
        "# z-plus evaluation summary",
        "",
        "Generated by `python -m zplus eval data/ --out results/` (fixed seeds).",
        "",
        "## Dataset",
        "",
        f"- {e.dataset['files']} files in {e.dataset['problems']} problems "
        f"({e.dataset['copies']} planted copies)",
        f"- {e.dataset['positives']} positive pairs, {e.dataset['negatives']} negative pairs",
        f"- Tuning problems: {', '.join(e.tune)}",
        f"- Held-out problems: {', '.join(e.test)}",
        "",
        "## Chosen settings (picked on the tuning problems only)",
        "",
        f"- k = {c.k}, w = {c.w}, threshold = {c.threshold:.2f} "
        f"(min_shared={c.min_shared}, max_df={c.max_df}, min_match={c.min_match})",
        "",
        "## Held-out results",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Precision | {h.precision:.2f} ({h.tp} TP, {h.fp} FP) |",
        f"| Recall | {h.recall:.2f} ({h.fn} missed) |",
        f"| F1 | {h.f1:.2f} |",
        f"| Recall, level 1 copies | {_fmt(h.recall_by_level.get(1))} |",
        f"| Recall, level 2 copies | {_fmt(h.recall_by_level.get(2))} |",
        f"| Recall, level 3 copies | {_fmt(h.recall_by_level.get(3))} |",
        "",
        "## All problems (for reference; includes the tuning data)",
        "",
        f"Precision {e.overall.precision:.2f}, recall {e.overall.recall:.2f}, "
        f"F1 {e.overall.f1:.2f}; recall by level "
        + ", ".join(f"L{lv} {_fmt(e.overall.recall_by_level.get(lv))}" for lv in (1, 2, 3)),
        "",
        "## Baseline: difflib.SequenceMatcher on raw text (all problems)",
        "",
        f"At z-plus's precision of {e.zplus_precision_all:.2f}: z-plus recall "
        f"{e.zplus_recall_all:.2f}, difflib recall {e.baseline_recall:.2f} "
        f"(difference {e.zplus_recall_all - e.baseline_recall:+.2f}"
        + (f", difflib threshold {e.baseline_threshold:.2f})." if e.baseline_threshold
           is not None else "; difflib never reaches that precision)."),
        "",
        "## Parameter grid (tuning problems)",
        "",
        "Each cell: best F1 (at threshold) / share of positive pairs that became "
        "candidates / number of candidate pairs. Ties on F1 go to the higher "
        "candidate recall, then to fewer candidates (less work).",
        "",
        "| k \\ w | " + " | ".join(str(w) for w in GRID_W) + " |",
        "|---|" + "---|" * len(GRID_W),
    ]
    for k in GRID_K:
        cells = [
            f"{g.f1:.2f} (@{g.threshold:.2f}) / {g.candidate_recall:.2f} / {g.candidates}"
            for g in (e.grid[(k, w)] for w in GRID_W)
        ]
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Ablations (threshold tuned per variant on tuning problems, scored held-out)",
        "",
        "| Variant | Threshold | Precision | Recall | F1 | L1 | L2 | L3 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, (t_v, m) in e.ablations.items():
        lv = m.recall_by_level
        lines.append(
            f"| {name} | {t_v:.2f} | {m.precision:.2f} | {m.recall:.2f} | {m.f1:.2f} | "
            f"{_fmt(lv.get(1))} | {_fmt(lv.get(2))} | {_fmt(lv.get(3))} |"
        )
    lines += [
        "",
        "## Threshold sweep (all problems, chosen k and w)",
        "",
        "| Threshold | Precision | Recall | F1 |",
        "|---|---|---|---|",
    ]
    lines += [f"| {t:.2f} | {m.precision:.2f} | {m.recall:.2f} | {m.f1:.2f} |"
              for t, m in e.sweep_rows]
    lines += [
        "",
        "## Runtime (synthetic files, one problem folder)",
        "",
        "| Submissions | Avg lines | Seconds |",
        "|---|---|---|",
    ]
    lines += [f"| {n} | {ln:.0f} | {s:.2f} |" for n, s, ln in e.runtime]
    lines += [
        "",
        "Precision is defined as 1.0 when nothing is flagged. Files: `grid.csv`, "
        "`sweep.csv`, `baseline_sweep.csv`, `runtime.csv`, `pr_curve.png`, `runtime.png`.",
        "",
    ]
    return "\n".join(lines)
