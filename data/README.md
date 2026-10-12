# z-plus dataset

Five problems, each in its own folder:

| Folder | Problem | Originals | Planted copies |
|---|---|---|---|
| `p1_merge_intervals` | merge overlapping intervals | 8 | 6 |
| `p2_valid_brackets` | balanced `()[]{}` with other characters ignored | 8 | 6 |
| `p3_top_k_words` | k most frequent words, ties alphabetical | 8 | 6 |
| `p4_spiral_matrix` | clockwise spiral traversal | 8 | 6 |
| `p5_number_of_islands` | count 4-connected land regions | 8 | 6 |

That is 70 files, 30 positive pairs and 425 negative pairs.

## Layout

```
p1_merge_intervals/
    problem.md              # the statement
    tests.json              # {"function": "solve", "cases": [{"args": [...], "expected": ...}]}
    alice.py, bob.py, ...   # independent originals
    copy1_L1_of_carol.py    # planted copies, written by `python -m zplus copies data/`
```

## Naming convention and ground truth

- An independent original is `<author>.py`, for example `alice.py`.
- A planted copy is `copy<n>_L<level>_of_<author>.py`, for example
  `copy2_L3_of_alice.py`. It was made from `<author>.py` by the mutation
  generator at disguise level 1, 2 or 3.
- Two files are a true positive pair when they share the same root original:
  an original and its copy, or two copies of the same original. Every other pair
  inside a problem is a negative. `zplus.dataset.ground_truth` implements this
  with the regex `^copy\d+_L([123])_of_(.+)\.py$`.

## Rules every file follows

- It defines `solve`, which returns its answer (printing is a failure).
- Any top-level code sits under `if __name__ == "__main__":`.
- It passes every case in its problem's `tests.json`, run in a separate
  interpreter with a 5-second timeout (`zplus.dataset.check_solution`).
- No two files are byte-identical, and every copy's origin exists.

Check all of this with `python -m zplus validate data/`.

## Hard negatives

Each problem contains honest solutions that deliberately use the same approach
as another author's, written independently (for example `alice.py` and
`erin.py` both sort and sweep in p1; `bob.py` and `grace.py` both use BFS with a
deque in p5). They look alike but are not copies, so they test false positives.
These files say so in a comment.

## Regenerating the copies

```
python -m zplus copies data/ --per-problem 6 --seed 2026
python -m zplus validate data/
```

Copies use levels 1, 2, 3, 1, 2, 3 in order. Every copy is compiled and run
against `tests.json`; if it fails, the generator retries with the next seed (up
to 5 times) and then drops operations until it passes.
