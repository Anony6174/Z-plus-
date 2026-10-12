# z-plus

z-plus scans a folder of Python submissions for one coding problem and reports
which ones are copies of each other, even after renaming, reordering and
padding. It compares the *structure* of code rather than its text, and every
core algorithm (rolling hash, winnowing, inverted index, greedy string tiling,
union-find, AST hashing) is implemented here with the standard library only.

> A flag is a lead for a human reviewer, never a verdict.

## Quick start

```bash
conda env create -f environment.yml      # Python 3.12 + pytest, pytest-cov, matplotlib
conda activate zplus                     # (the env installs z-plus in editable mode)

# Scan one problem and open the HTML report
python -m zplus scan data/p1_merge_intervals --format html --out report.html

# Same scan as text or JSON, with options
python -m zplus scan data/p1_merge_intervals --k 6 --w 4 --threshold 0.6 \
    --template starter.py --format json --out report.json --top 10

# Regenerate every table and plot in results/
python -m zplus eval data/ --out results/

# Dataset tools
python -m zplus copies data/ --per-problem 6 --seed 2026   # planted copies (B4)
python -m zplus validate data/                             # every file passes its tests

pytest --cov=zplus                                         # 101 tests
```

Without conda: `pip install -e ".[dev]"` in any Python 3.10+ environment.

**Input:** `folder/<problem>/<author>.py` (or a flat folder of `.py` files, whose
problem name is the folder name). A `template.py` next to the submissions, or
`--template path`, is starter code: its fingerprints are ignored.

**Scan options:** `--k`, `--w`, `--threshold`, `--min-shared`, `--max-df`,
`--min-match`, `--no-ast`, `--template`, `--format {text,json,html}`, `--out`,
`--top N`, `--verbose`.

**Exit codes:** 0 when nothing is flagged, 1 when pairs are flagged, 2 on errors
(missing folder, bad option).

**Report contents:** configuration, files read and skipped (with reasons), the
flagged pairs sorted by final score (with tiling, AST and Jaccard), the rings with
their weakest link, and for each flagged pair the matched regions as line ranges.
The HTML page puts both sources side by side with one colour per tile.

JSON shape:

```json
{"config": {...},
 "pairs": [{"a": "p1/alice", "b": "p1/bob", "scores": {...},
            "matches": [{"a_lines": [3, 9], "b_lines": [5, 11], "tokens": 54}]}],
 "clusters": [["p1/alice", "p1/bob"]],
 "skipped": [{"sid": "p1/tiny", "reason": "too short to check"}],
 "stats": {"files": 14, "candidates": 47, "flagged": 5}}
```

## Results

Measured by `python -m zplus eval data/` with fixed seeds. Parameters and
thresholds were tuned on problems 1 to 3 only; the headline numbers are measured
on the **held-out problems 4 and 5** (spiral matrix, number of islands).

| Measure | Target | Measured | Measured on |
|---|---|---|---|
| Recall, level 1 copies (cosmetic) | ≥ 0.95 | **1.00** | held-out p4, p5 |
| Recall, level 2 copies (light structure) | ≥ 0.90 | **1.00** | held-out p4, p5 |
| Recall, level 3 copies (structural) | ≥ 0.70 | **1.00** | held-out p4, p5 |
| Precision at the chosen threshold | ≥ 0.90 | **0.86** (12 TP, 2 FP), missed | held-out p4, p5 |
| z-plus recall minus difflib recall, equal precision | clearly positive | **+0.77** (0.90 vs 0.13 at precision 0.90) | all problems |
| Time to scan 200 submissions | < 10 s | **6.0 s** (≈130-line files) | synthetic set |

Over all five problems (which includes the tuning data) the chosen settings give
precision 0.90, recall 0.90, F1 0.90, with recall by level 1.00 / 0.80 / 0.90.
Held-out sets are small (12 positive pairs), so one pair moves recall by 0.08:
read the held-out numbers as encouraging, not definitive.

Full tables (threshold sweep, k×w grid, ablations, runtime) are in
[results/summary.md](results/summary.md); plots in
[results/pr_curve.png](results/pr_curve.png) and
[results/runtime.png](results/runtime.png).

### Index card

- **Dataset:** 70 files in 5 problems: 40 independent originals and 30 planted
  copies (10 per level); 30 positive pairs and 425 negative pairs.
- **Chosen settings:** k = 9, w = 6, threshold = 0.60. F1 on the tuning problems
  was the same (0.88) for every k and w in the grid, because the final score
  comes from tiling and AST, which do not depend on k or w. Those two only decide
  which pairs become candidates, and every grid cell kept 100% of positive pairs
  as candidates. So the tie-break picks the cheapest cell: k = 9, w = 6 gives the
  fewest candidates (69 on the tuning problems, against 181 for k = 5, w = 2). The
  library defaults stay at the specification's k = 6, w = 4, which give the same
  accuracy.
- **Recall by level, held-out:** 1.00 / 1.00 / 1.00.
- **Precision / F1 at the chosen threshold, held-out:** 0.86 / 0.92.
- **Improvement over raw-text diff:** +0.77 recall at equal precision.
- **Scan time, 200 files:** 6.0 s (400 files: 22.7 s; the synthetic set is a
  worst case, since every file shares code with every other).
- **One false positive:** `p5/bob` (BFS with a deque) and `p5/erin` (recursive
  flood fill) score 0.66 by tiling, but only 0.15 by AST. Grid problems share long
  generic runs such as `for r in range(rows): for c in range(cols): if 0 <= nr <
  rows and 0 <= nc < cols ...`, and once names become `ID` those runs are
  identical. Through union-find, this one false edge also merges the two true
  pairs (bob and bob's copy, erin and erin's copy) into a ring of 4. The report's
  "weakest link" column exists for exactly this case.
- **One miss:** `p2/bob` and its level 2 copy score 0.52. bob's solution is 16
  lines long, and the copy adds about as many lines of dead code (an unused
  helper, an `if False:` block). Tiling divides the covered tokens by the size of
  *both* files, so padding a short file dilutes the score. Containment-style
  normalization (dividing by the smaller file) would catch it, at some cost to
  precision.

### Ablations (held-out, each variant's threshold tuned on problems 1 to 3)

| Variant | Threshold | Precision | Recall | F1 |
|---|---|---|---|---|
| z-plus: `max(tiling, AST)` | 0.60 | 0.86 | 1.00 | 0.92 |
| tiling only | 0.60 | 0.86 | 1.00 | 0.92 |
| AST only | 0.55 | 1.00 | 0.92 | 0.96 |
| `mean(tiling, AST)` instead of max | 0.60 | 1.00 | 1.00 | 1.00 |
| normalization off (names kept) | 0.65 | 1.00 | 0.50 | 0.67 |

What this says, honestly:

- **Normalization is what makes the tool work.** Keeping identifiers halves recall,
  because every level of disguise renames things.
- **On this data, `mean` beats `max`.** The specification chose `max` so that a
  cheater who beats one view is still caught by the other. Here the planted copies
  never beat both views, while honest look-alikes sometimes fool tiling (high
  tiling, low AST). Averaging the two removes those false positives. `max` remains
  the default because it matches the specification and is the safer choice
  against disguises the generator does not produce. With 12 held-out positives
  this is a signal, not proof; it is the first thing to re-test on real data.
  `combine(scores, mode="mean")` is already implemented.

## How it works

The pipeline runs once per problem. A1 to A4 turn files into candidate pairs.
For each candidate pair, B1, B2 and A6 compute scores. B3 groups the flagged
pairs into rings, B6 reports, and B4 and B5 measure the whole thing on labelled
data.

```
files ─A1─▶ tokens ─A2─▶ k-gram hashes ─A3─▶ fingerprints ─A4─▶ candidate pairs
                                                                     │
          rings ◀─B3─ final score ◀─B1─ (tiling B2, AST A6, Jaccard) ◀┘
            │
            └─B6─▶ text / JSON / HTML        B4 copies ─▶ B5 precision, recall, F1
```

### A1. Loader and normalizer ([loader.py](zplus/loader.py), [normalize.py](zplus/normalize.py))

The loader walks `folder/<problem>/*.py` and gives each file the id
`"<problem>/<stem>"`. It reads files as UTF-8 with undecodable bytes replaced, and
skips files it cannot read, tokenize or parse, recording the reason so the
report can list them. The normalizer runs Python's own `tokenize` and rewrites
each token so cosmetic edits disappear:

- **Keywords keep their text**, because `for`, `while`, `if` and `return` are the
  shape of the program.
- **Builtins keep their text**, because using `sorted` instead of `min` is a real
  difference, not a cosmetic one.
- **Every other name becomes `ID`.** Renaming must not matter.
- **Numbers become `NUM` and strings `STR`.** Changing a constant or a message
  must not matter.
- **Operators keep their text**, because `+` and `-` mean different things.
- **`NEWLINE`, `INDENT` and `DEDENT` stay**, because they mark statements and
  blocks.
- **Comments, blank lines and the `NL` of wrapped lines are dropped**, so
  re-wrapping an expression changes nothing.
- **Docstrings and bare string statements are dropped:** a logical line that
  holds only strings vanishes, along with its `NEWLINE`.

On Python 3.12+, f-strings arrive as several tokens; a depth counter collapses
each whole f-string, nested ones included, into one `STR`. A byte-order mark is
stripped and line endings are unified before tokenizing, so Windows files and
tab-indented files give the same tokens. Every token keeps its original line
number, which is how matches are later highlighted.

*Trade-off:* attribute and method names also become `ID`, so `xs.append(v)` and
`xs.extend(v)` look the same. That raises recall (renamed helper methods still
match) and lowers precision.

### A2. Rolling hash ([rollinghash.py](zplus/rollinghash.py))

Each token text becomes a stable integer: the first 8 bytes of its blake2b
digest, mod M = 2⁶¹−1. Python's built-in `hash()` is never used, because it is
randomized per process. A k-gram's hash is the polynomial
`H_i = Σ t_{i+j}·B^{k−1−j} mod M` with the fixed base B = 911382323. Rather than
recompute every window (O(nk)), the window rolls: subtract the outgoing token
times `B^{k−1}` (precomputed once), multiply by B, add the incoming token. That
is O(1) per step and O(n) in total. With a 61-bit prime modulus, two different
k-grams collide with probability about 1 in 2.3·10¹⁸.

### A3. Winnowing ([winnow.py](zplus/winnow.py))

Keeping every k-gram hash is wasteful, and keeping "hashes divisible by p" can
select nothing across a long copied block. Winnowing slides a window over w
consecutive hashes and keeps the minimum of each window (the rightmost one on
ties), recording a position only once. **Guarantee:** a shared run of at least
`w + k − 1` tokens contains w whole k-grams. Those form one complete window,
identical in both files, so both files pick the same minimum: at least one
shared fingerprint, always. A monotonic deque, whose hashes increase from front
to back, gives each window's minimum in O(1) amortized time, so the whole pass is
O(n). The density is about `2/(w+1)`, which a test checks.

### A4. Inverted index and candidate pairs ([index.py](zplus/index.py))

Comparing every pair of files is O(N²) whole-file comparisons. Instead, the
index maps each fingerprint hash to the set of files containing it, and pairs
are counted only inside posting lists, so files that share nothing are never
touched. Hashes present in more than `max(3, ceil(max_df · N))` files are dropped
like stop words: they are boilerplate (input parsing, common idioms), they make
posting lists explode quadratically, and they create false matches. The floor of
3 keeps small folders from losing real matches. *What `max_df` trades away:* a
real copy whose only shared code is very common goes unseen. Template hashes are
removed before counting, so shared starter code never counts as copying. Files
too short to have a fingerprint are reported as "too short to check".
Measured: building the index and counting pairs for 1,000 synthetic submissions
takes 0.02 s.

### A5. Dataset and ground truth ([dataset.py](zplus/dataset.py), [data/](data/README.md))

There are five problems with eight independent originals each, all written for
this project. Several deliberately use the same approach as another author's
(hard negatives), to test false positives. A planted copy is named
`copy<n>_L<level>_of_<author>.py`; two files are a true pair when they share a
root original. `check_solution` runs a file in a separate interpreter (never in
our own process) with a 5-second timeout, calls `solve` on each case in
`tests.json`, and compares the results as JSON. `validate_dataset` checks that
every file passes, that every copy's origin exists, and that no two files are
byte-identical.

### A6. AST structural hashing ([astsim.py](zplus/astsim.py))

This is a second opinion that ignores token order. After `ast.parse`, an
iterative post-order walk gives each node a structure hash, `blake2b` of
`NodeType(childHash,…)`. Names and constants are ignored, operator node types
are kept (so `Add` ≠ `Sub`), and `Load`/`Store`/`Del` are skipped. `x += y` is
first rewritten as `x = x + y`. Subtrees with at least 8 nodes go into a
multiset. The score is the overlap coefficient, `Σ min(countA, countB) /
min(|A|, |B|)`. Swapping two independent statements changes only their
parents' hashes, so every statement subtree still matches (a test on a real
solution measures ≥ 0.8). Added dead code adds subtrees but removes none, so the
overlap coefficient holds steady where Jaccard would fall. *Limits:* a
`for`→`while` rewrite changes node types, so those subtrees stop matching, and a
tiny file inside a big one can score 1.0, which is why tiling is also used.
Parses are cached per source, so each file is parsed once per scan.

### B1. Scoring ([scoring.py](zplus/scoring.py))

Fingerprint lists become hash sets F_A and F_B:

- Jaccard: `J = |F_A ∩ F_B| / |F_A ∪ F_B|`.
- Containment: `C = max(|F_A ∩ F_B|/|F_A|, |F_A ∩ F_B|/|F_B|)`, which catches a
  small solution pasted inside a bigger program.
- `combine`: `primary` is the tiling score when tiling ran, else containment.
  `final = max(primary, ast)` when the AST score exists, else `primary`.

**Why max:** a cheater who defeats the token view (by reordering) is still caught
by the tree view, and the reverse. Empty sets give 0.0, never a division by
zero. See the ablations above for how this compares with the mean.

### B2. Greedy string tiling ([tiling.py](zplus/tiling.py))

Tiling verifies a candidate pair and finds exactly which regions match. Each
round finds the longest run L of equal, unmarked tokens. If `L < min_match` it
stops. Otherwise every run of length L that does not overlap a tile accepted in
the same round (ties broken by smallest i, then j) becomes a tile, and its tokens
are marked. The score is `2·Σ len(tile) / (|A| + |B|)`. Unlike a longest common
subsequence, tiling finds every copied block wherever it was moved, and never
uses a token twice.

*Implementation:* the textbook version recomputes an n×m `run[i][j]` table every
round; it is kept as `greedy_tiling_reference` and used as the test oracle. The
production version gives identical output (checked on random inputs), but builds
the maximal runs once. Every file gets an index of its `min_match`-token windows,
keyed by exact content. For a pair, the two indexes are intersected, and
consecutive window matches on one diagonal are stitched into maximal runs. Each
round then only splits the runs that a new tile touched. This is the "Running
Karp-Rabin GST" idea with exact keys instead of hashes. It made the 200-file
scan go from 104 s to 6 s. Pairs above 4,000,000 token cells are skipped with a
warning, and `combine` falls back to containment for them.

### B3. Union-find clustering ([cluster.py](zplus/cluster.py))

Every pair at or above the threshold unions its two files. `find` halves the
path as it walks (iteratively), and `union` hangs the smaller tree under the
larger. Edges arrive as a stream, so no adjacency lists are needed, and each
operation costs O(α(n)), effectively constant. Groups of 2 or more come back
largest first. *Limitation:* if A matches B and B matches C, all three are one
ring even when A and C are unrelated. The report shows each ring's weakest link
so a human can judge (the ring of 4 in the false-positive example above is
exactly this).

### B4. Mutation generator ([mutate.py](zplus/mutate.py))

The generator creates disguised copies with known labels, so accuracy is
measured rather than guessed. Each level includes the ones below it.

- **Level 1, cosmetic.** Every user-defined name is renamed consistently:
  functions, arguments, variables, comprehension and lambda variables. Builtins,
  imports, attributes, keyword-argument names, class members, dunders and
  `solve` are never renamed. The output is printed with `ast.unparse`, then
  comments, blank lines and an indentation change are added.
- **Level 2, light structure.** Adjacent assignments are swapped when both are
  free of calls and neither writes a name the other reads or writes. Dead code
  is added: unused variables, `if False:` blocks, `for _ in range(0): pass`, and
  an unused helper. Comparisons are flipped (`a < b` → `b > a`).
- **Level 3, structural.** `for i in range(...)` becomes a `while` loop, with the
  bound hoisted so it is evaluated once, and only when the body has no
  `continue` and never assigns the loop variable. `x += y` becomes `x = x + y`.
  `if c: A else: B` becomes `if not c: B else: A`. Plain top-level defs are
  reordered.

All randomness comes from `random.Random(seed)`, so the same seed gives
byte-identical output. **Safety net:** every copy is compiled and run against
`tests.json`. On failure it retries with seed + 1 (up to 5 times), then drops
operations one at a time and logs which. As measured, all 2,400 raw mutants
(40 originals × 3 levels × 20 seeds) pass their tests.

### B5. Evaluation ([evaluate.py](zplus/evaluate.py))

Every same-problem pair is a prediction. A pair that never became a candidate
counts as not flagged. **Precision is defined as 1.0 when nothing is flagged.**
Problems with no positives are skipped for recall. One command runs:

- a threshold sweep from 0.10 to 0.90 (CSV plus a PR curve);
- the k ∈ {3, 5, 7, 9} × w ∈ {2, 4, 6} grid;
- recall by level;
- the ablations;
- the `difflib.SequenceMatcher` baseline (recall at the precision z-plus
  reaches);
- a runtime curve for 50 to 400 synthetic ~130-line files, each made by
  concatenating one original per problem and mutating it.

**To avoid fooling ourselves,** k, w and every threshold are chosen on problems
1 to 3 only, and the headline numbers come from problems 4 and 5.

### B6. CLI and reports ([cli.py](zplus/cli.py), [report.py](zplus/report.py))

The CLI is built with `argparse` and has the subcommands `scan`, `eval`,
`copies` and `validate`. Only this module prints; the engine uses `logging`.
Each match is mapped to source lines through `Token.line`. The HTML report is
one self-contained file with inline CSS (light and dark), with source shown side
by side and a `<mark>` colour per tile. Every line of source goes through
`html.escape`, so a submission containing `<script>` cannot inject code into the
report (a test checks this).

## Complexity

L = characters in a file, n = tokens, F = fingerprints, N = files, P = the
length of a posting list, C = candidate pairs, S = matching windows in a pair.

| Stage | Time | Space |
|---|---|---|
| A1 normalize | O(L) | O(n) |
| A2 rolling hash | O(n) | O(n) |
| A3 winnowing | O(n) | O(n) |
| A4 index build | O(total F) | O(total F) |
| A4 pair counting | O(Σ P²) | O(pairs) |
| A6 AST hashing | O(AST nodes) | O(AST nodes) |
| B1 scoring | O(F) | O(F) |
| B2 tiling, per pair | O(n + m + S) plus O(runs) per round (reference: O(nm) per round) | O(n + m + S) |
| B3 clustering | O(E α(N)) | O(N) |

## Testing

`pytest --cov=zplus` runs 101 tests in about 7 seconds at 96% line coverage.
The suite has five kinds of tests:

- **Unit:** one file per module, covering every edge case listed in the
  specification.
- **Property:** rolling hash vs naive recomputation (1,000 sequences), deque
  winnowing vs brute force, tiling vs the textbook table, and union-find vs BFS
  (500 random graphs).
- **Guarantee:** winnowing finds a shared block of `w + k − 1` tokens in 1,000
  out of 1,000 trials.
- **Integration:** `run()` on a 6-file fixture gives the expected pairs, rings
  and JSON.
- **Mutation safety:** every mutant across all five problems and 20 seeds passes
  its tests.

The text report has a snapshot test. GitHub Actions
([.github/workflows/test.yml](.github/workflows/test.yml)) runs the suite on
Python 3.10, 3.12 and 3.13, and fails below 85% coverage.

## Limitations and future work

- **Semantic clones** (a different algorithm with the same output) are out of
  scope. They would need program analysis or learned embeddings.
- **Generic idioms raise false positives on small problems** (see the
  false-positive example above). Weighting tokens by rarity, or the `mean`
  combination, would help.
- **Padding a short file with dead code dilutes the tiling score** (see the
  miss).
- **The dataset is small** (12 held-out positive pairs), and the mutation
  generator only produces the disguises we thought of.
- **Scale:** the synthetic runtime grows roughly quadratically, because every
  synthetic file shares code with every other. For very large collections, use
  MinHash with LSH for candidates and a sharded index.
- **Python only.** A generic parser such as tree-sitter would extend this to
  other languages.

## Repository layout

```
zplus/        engine: types, loader, normalize, rollinghash, winnow, index, dataset,
              astsim, scoring, tiling, cluster, mutate, evaluate, report, cli, pipeline
data/         5 problems × (8 originals + 6 planted copies), tests.json, problem.md
tests/        one test file per module, plus fixtures/
results/      output of `python -m zplus eval data/`
```
