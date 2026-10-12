"""B6: command-line interface. The only module that prints.

    python -m zplus scan data/p1_merge_intervals --format html --out report.html
    python -m zplus eval data/ --out results/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from zplus.errors import ZplusError
from zplus.types import Config

EXIT_CLEAN, EXIT_FLAGS, EXIT_ERROR = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    """The argparse parser with ``scan``, ``eval``, ``copies`` and ``validate``."""
    d = Config()
    parser = argparse.ArgumentParser(
        prog="zplus", description="Find disguised copies among Python submissions."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a folder and report suspicious pairs")
    scan.add_argument("folder", help="folder of <problem>/<author>.py or <author>.py files")
    scan.add_argument("--k", type=int, default=d.k, help=f"k-gram length (default {d.k})")
    scan.add_argument("--w", type=int, default=d.w, help=f"winnow window (default {d.w})")
    scan.add_argument("--threshold", type=float, default=d.threshold,
                      help=f"flag pairs at or above this score (default {d.threshold})")
    scan.add_argument("--min-shared", type=int, default=d.min_shared,
                      help=f"shared hashes to become a candidate (default {d.min_shared})")
    scan.add_argument("--max-df", type=float, default=d.max_df,
                      help=f"drop hashes in more than this share of files (default {d.max_df})")
    scan.add_argument("--min-match", type=int, default=d.min_match,
                      help=f"shortest tile in tokens (default {d.min_match})")
    scan.add_argument("--no-ast", action="store_true", help="disable the AST score")
    scan.add_argument("--template", help="starter code to ignore")
    scan.add_argument("--format", choices=("text", "json", "html"), default="text")
    scan.add_argument("--out", help="write the report here instead of stdout")
    scan.add_argument("--top", type=int, metavar="N", help="show only the top N pairs")
    scan.add_argument("--verbose", action="store_true", help="log progress and warnings")

    ev = sub.add_parser("eval", help="measure accuracy on a labelled dataset")
    ev.add_argument("folder", help="dataset root, e.g. data/")
    ev.add_argument("--out", default="results", help="output folder (default results/)")
    ev.add_argument("--sizes", default="50,100,200,400",
                    help="runtime experiment sizes, comma separated")
    ev.add_argument("--verbose", action="store_true")

    cp = sub.add_parser("copies", help="write planted copies into a dataset (B4)")
    cp.add_argument("folder")
    cp.add_argument("--per-problem", type=int, default=6)
    cp.add_argument("--seed", type=int, default=2026)
    cp.add_argument("--verbose", action="store_true")

    va = sub.add_parser("validate", help="check every file in a dataset passes its tests")
    va.add_argument("folder")
    va.add_argument("--verbose", action="store_true")
    return parser


def _scan(args: argparse.Namespace) -> int:
    from zplus.pipeline import run
    from zplus.report import to_html, to_json, to_text

    if args.top is not None and args.top < 1:
        raise ZplusError("--top must be at least 1")
    cfg = Config(k=args.k, w=args.w, min_shared=args.min_shared, max_df=args.max_df,
                 min_match=args.min_match, threshold=args.threshold,
                 use_ast=not args.no_ast)
    if cfg.k < 1 or cfg.w < 1 or cfg.min_match < 1:
        raise ZplusError("--k, --w and --min-match must be at least 1")
    if args.template:
        import os

        if not os.path.isfile(args.template):
            raise ZplusError(f"template not found: {args.template}")
    report = run(args.folder, cfg, args.template)
    if args.format == "json":
        text = json.dumps(to_json(report, args.top), indent=2) + "\n"
    elif args.format == "html":
        text = to_html(report, args.top)
    else:
        text = to_text(report, args.top)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out} ({len(report.flagged())} flagged pairs)", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return EXIT_FLAGS if report.flagged() else EXIT_CLEAN


def _eval(args: argparse.Namespace) -> int:
    import os

    from zplus.evaluate import run_experiments

    if not os.path.isdir(args.folder):
        raise ZplusError(f"not a folder: {args.folder}")
    try:
        sizes = tuple(int(x) for x in args.sizes.split(",") if x.strip())
    except ValueError as exc:
        raise ZplusError(f"bad --sizes: {args.sizes}") from exc
    exp = run_experiments(args.folder, args.out, sizes)
    h, c = exp.heldout, exp.chosen
    print(f"chosen: k={c.k} w={c.w} threshold={c.threshold:.2f}")
    print(f"held-out ({', '.join(exp.test)}): precision {h.precision:.2f}  "
          f"recall {h.recall:.2f}  F1 {h.f1:.2f}")
    print("recall by level: " + "  ".join(
        f"L{lv} {'n/a' if v is None else f'{v:.2f}'}" for lv, v in h.recall_by_level.items()))
    print(f"difflib baseline recall {exp.baseline_recall:.2f} vs z-plus "
          f"{exp.zplus_recall_all:.2f} at precision {exp.zplus_precision_all:.2f}")
    for n, secs, _ in exp.runtime:
        print(f"scan of {n} submissions: {secs:.2f}s")
    print(f"wrote {os.path.join(args.out, 'summary.md')}")
    return EXIT_CLEAN


def _copies(args: argparse.Namespace) -> int:
    from zplus.mutate import make_copies

    make_copies(args.folder, args.per_problem, args.seed)
    print(f"wrote {args.per_problem} copies per problem into {args.folder}")
    return EXIT_CLEAN


def _validate(args: argparse.Namespace) -> int:
    from zplus.dataset import validate_dataset

    errors = validate_dataset(args.folder)
    for err in errors:
        print(err)
    print("dataset valid" if not errors else f"{len(errors)} problem(s) found")
    return EXIT_ERROR if errors else EXIT_CLEAN


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns 0 (no flags), 1 (flags found) or 2 (error)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    handlers = {"scan": _scan, "eval": _eval, "copies": _copies, "validate": _validate}
    try:
        return handlers[args.command](args)
    except (ZplusError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
