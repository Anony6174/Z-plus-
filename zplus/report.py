"""B6: text, JSON and HTML writers for a Report."""

from __future__ import annotations

import html
from dataclasses import asdict

from zplus.types import Match, PairResult, Report, Token


def line_range(tokens: list[Token], start: int, length: int) -> list[int]:
    """``[first, last]`` original source lines covered by a token range.

    Trailing DEDENTs are skipped: tokenize stamps them with the line of the
    *next* statement, which would highlight a line that did not match.

    Complexity: O(trailing DEDENTs), effectively O(1).
    """
    end = start + length - 1
    while end > start and tokens[end].kind == "DEDENT":
        end -= 1
    return [tokens[start].line, tokens[end].line]


def match_lines(report: Report, pair: PairResult, m: Match) -> tuple[list[int], list[int]]:
    """Source line ranges of a match in both files. O(1)."""
    ta = report.submissions[pair.a].tokens
    tb = report.submissions[pair.b].tokens
    return line_range(ta, m.a_start, m.length), line_range(tb, m.b_start, m.length)


def weakest_links(report: Report) -> list[tuple[set[str], float]]:
    """Each cluster with the lowest final score among its flagged pairs. O(P * G)."""
    flagged = report.flagged()
    out = []
    for group in report.clusters:
        scores = [p.scores.final for p in flagged if p.a in group and p.b in group]
        out.append((group, min(scores)))
    return out


def _cfg_line(report: Report) -> str:
    c = report.config
    return (f"k={c.k} w={c.w} threshold={c.threshold} min_shared={c.min_shared} "
            f"max_df={c.max_df} min_match={c.min_match} ast={'on' if c.use_ast else 'off'}")


def _num(x: float | None) -> str:
    return "  -  " if x is None else f"{x:.3f}"


# ---------------------------------------------------------------------- text
def to_text(report: Report, top: int | None = None) -> str:
    """Plain-text report for the terminal. O(P + output size)."""
    flagged = report.flagged()
    shown = flagged[:top] if top else flagged
    out = [
        "z-plus scan",
        f"config: {_cfg_line(report)}",
        f"files read: {len(report.submissions)}   skipped: {len(report.skipped)}   "
        f"candidate pairs: {report.n_candidates}   flagged: {len(flagged)}",
        "",
    ]
    if shown:
        wa = max(len(p.a) for p in shown)
        wb = max(len(p.b) for p in shown)
        out.append(f"{'#':>3}  {'file A':<{wa}}  {'file B':<{wb}}  final  tiling  ast    jaccard")
        for i, p in enumerate(shown, 1):
            s = p.scores
            out.append(f"{i:>3}  {p.a:<{wa}}  {p.b:<{wb}}  {s.final:.3f}  {_num(s.tiling)}"
                       f"  {_num(s.ast)}  {s.jaccard:.3f}")
        if top and len(flagged) > top:
            out.append(f"     ... {len(flagged) - top} more flagged pairs not shown")
    else:
        out.append("No pairs reached the threshold.")
    out.append("")
    if report.clusters:
        out.append("Groups (rings):")
        for i, (group, weak) in enumerate(weakest_links(report), 1):
            out.append(f"  {i}. {', '.join(sorted(group))}   (weakest link {weak:.3f})")
        out.append("")
    if shown:
        out.append("Matched regions (lines in A <-> lines in B, tokens):")
        for i, p in enumerate(shown, 1):
            out.append(f"  {i}. {p.a} <-> {p.b}")
            if not p.matches:
                out.append("     (no tiles; score from fingerprints or AST)")
            for m in sorted(p.matches, key=lambda m: m.a_start):
                la, lb = match_lines(report, p, m)
                out.append(f"     {la[0]}-{la[1]} <-> {lb[0]}-{lb[1]}  ({m.length} tokens)")
        out.append("")
    if report.skipped:
        out.append("Skipped files:")
        out.extend(f"  {s.sid}: {s.reason}" for s in report.skipped)
        out.append("")
    out.append("A flag is a lead for a human reviewer, never a verdict.")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------- json
def to_json(report: Report, top: int | None = None) -> dict:
    """JSON-ready dict: ``{config, pairs, clusters, skipped}``. O(P + matches)."""
    flagged = report.flagged()
    shown = flagged[:top] if top else flagged
    pairs = []
    for p in shown:
        matches = []
        for m in p.matches:
            la, lb = match_lines(report, p, m)
            matches.append({"a_lines": la, "b_lines": lb, "tokens": m.length})
        pairs.append({"a": p.a, "b": p.b, "scores": asdict(p.scores), "matches": matches})
    return {
        "config": asdict(report.config),
        "pairs": pairs,
        "clusters": [sorted(g) for g in report.clusters],
        "skipped": [{"sid": s.sid, "reason": s.reason} for s in report.skipped],
        "stats": {
            "files": len(report.submissions),
            "candidates": report.n_candidates,
            "flagged": len(flagged),
        },
    }


# ---------------------------------------------------------------------- html
_CSS = """
:root{--bg:#f9f9f7;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--line:#e1e0d9;--t0:#cfe2f8;--t1:#fbd9c9;--t2:#c8eedd;--t3:#fbe7b5;--t4:#f8d8e4;
--t5:#c9e8c9;--t6:#dcd8f6;--t7:#f7cfcf}
@media (prefers-color-scheme:dark){:root{--bg:#0d0d0d;--card:#1a1a19;--ink:#f0efec;
--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--t0:#1d3b5e;--t1:#5a2a16;--t2:#124432;
--t3:#4d3a07;--t4:#52233a;--t5:#123d12;--t6:#2e2766;--t7:#5a2222}}
*{box-sizing:border-box}
body{margin:0;padding:24px 16px;background:var(--bg);color:var(--ink);
font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}
h3{font-size:15px;margin:0 0 8px}
.meta{color:var(--ink2);margin:0 0 4px}.note{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:14px 16px;margin:12px 0}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line);
white-space:nowrap}
th{color:var(--ink2);font-weight:600}td.n{font-variant-numeric:tabular-nums;text-align:right}
.side{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.src{font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
border:1px solid var(--line);border-radius:6px;overflow-x:auto}
.src .fn{padding:6px 10px;border-bottom:1px solid var(--line);color:var(--ink2);
font-weight:600}
.src table td{border:0;padding:0 8px;white-space:pre}
.src td.ln{color:var(--muted);text-align:right;user-select:none;width:1%}
mark{color:inherit;border-radius:2px;padding:0 1px}
.t0{background:var(--t0)}.t1{background:var(--t1)}.t2{background:var(--t2)}
.t3{background:var(--t3)}.t4{background:var(--t4)}.t5{background:var(--t5)}
.t6{background:var(--t6)}.t7{background:var(--t7)}
.tiles{margin:0 0 10px;padding-left:18px;color:var(--ink2)}
a{color:inherit}
"""


def _source_block(report: Report, sid: str, ranges: list[tuple[int, int, int]]) -> str:
    """One file's source with tile-coloured <mark> lines; every line is escaped."""
    lines = report.submissions[sid].source.splitlines()
    tile_of: dict[int, int] = {}
    for first, last, tile in ranges:
        for ln in range(first, last + 1):
            tile_of.setdefault(ln, tile)
    rows = []
    for n, text in enumerate(lines, 1):
        esc = html.escape(text) or " "
        if n in tile_of:
            esc = f'<mark class="t{tile_of[n] % 8}">{esc}</mark>'
        rows.append(f'<tr><td class="ln">{n}</td><td>{esc}</td></tr>')
    return (f'<div class="src"><div class="fn">{html.escape(sid)}</div>'
            f'<table>{"".join(rows)}</table></div>')


def to_html(report: Report, top: int | None = None) -> str:
    """One self-contained HTML page with inline CSS. All source text is escaped.

    Complexity: O(P + total source size of the shown pairs).
    """
    e = html.escape
    flagged = report.flagged()
    shown = flagged[:top] if top else flagged
    parts = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        f"<title>z-plus report</title><style>{_CSS}</style></head><body><main>",
        "<h1>z-plus report</h1>",
        f'<p class="meta">{e(_cfg_line(report))}</p>',
        f'<p class="meta">{len(report.submissions)} files read, {len(report.skipped)} '
        f"skipped, {report.n_candidates} candidate pairs, {len(flagged)} flagged.</p>",
        '<p class="note">A flag is a lead for a human reviewer, never a verdict.</p>',
        "<h2>Flagged pairs</h2>",
    ]
    if shown:
        rows = []
        for i, p in enumerate(shown, 1):
            s = p.scores
            rows.append(
                f'<tr><td class="n">{i}</td><td><a href="#pair{i}">{e(p.a)}</a></td>'
                f'<td><a href="#pair{i}">{e(p.b)}</a></td><td class="n">{s.final:.3f}</td>'
                f'<td class="n">{_num(s.tiling)}</td><td class="n">{_num(s.ast)}</td>'
                f'<td class="n">{s.jaccard:.3f}</td></tr>'
            )
        parts.append(
            '<div class="card scroll"><table><thead><tr><th>#</th><th>File A</th>'
            "<th>File B</th><th>Final</th><th>Tiling</th><th>AST</th><th>Jaccard</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        )
    else:
        parts.append('<div class="card">No pairs reached the threshold.</div>')
    parts.append("<h2>Groups (rings)</h2>")
    if report.clusters:
        items = "".join(
            f"<li>{e(', '.join(sorted(g)))} <span class=\"note\">(weakest link "
            f"{w:.3f})</span></li>"
            for g, w in weakest_links(report)
        )
        parts.append(f'<div class="card"><ol>{items}</ol></div>')
    else:
        parts.append('<div class="card">No groups.</div>')
    if shown:
        parts.append("<h2>Evidence</h2>")
    for i, p in enumerate(shown, 1):
        ra, rb, legend = [], [], []
        for t, m in enumerate(sorted(p.matches, key=lambda m: m.a_start)):
            la, lb = match_lines(report, p, m)
            ra.append((la[0], la[1], t))
            rb.append((lb[0], lb[1], t))
            legend.append(
                f'<li><mark class="t{t % 8}">tile {t + 1}</mark> lines {la[0]}-{la[1]} '
                f"&harr; {lb[0]}-{lb[1]} ({m.length} tokens)</li>"
            )
        tiles = (f'<ul class="tiles">{"".join(legend)}</ul>' if legend
                 else '<p class="note">No tiles; score comes from fingerprints or AST.</p>')
        parts.append(
            f'<div class="card" id="pair{i}"><h3>{i}. {e(p.a)} &harr; {e(p.b)} '
            f'<span class="note">final {p.scores.final:.3f}</span></h3>{tiles}'
            f'<div class="side">{_source_block(report, p.a, ra)}'
            f"{_source_block(report, p.b, rb)}</div></div>"
        )
    if report.skipped:
        items = "".join(f"<li>{e(s.sid)}: {e(s.reason)}</li>" for s in report.skipped)
        parts.append(f'<h2>Skipped files</h2><div class="card"><ul>{items}</ul></div>')
    parts.append("</main></body></html>\n")
    return "".join(parts)
