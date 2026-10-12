"""A5: dataset layout, ground truth and solution checking."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations

from zplus.loader import iter_python_files

log = logging.getLogger(__name__)

COPY_RE = re.compile(r"^copy\d+_L([123])_of_(.+)\.py$")
TIMEOUT = 5.0

# Runs inside a fresh interpreter: import the file, call the function on every
# case, exit 0 only if all results equal the expected values.
_RUNNER = r"""
import copy, importlib.util, json, sys
path, tests_path = sys.argv[1], sys.argv[2]
with open(tests_path) as fh:
    spec = json.load(fh)
mod_spec = importlib.util.spec_from_file_location("submission", path)
mod = importlib.util.module_from_spec(mod_spec)
mod_spec.loader.exec_module(mod)
fn = getattr(mod, spec.get("function", "solve"))
for case in spec["cases"]:
    got = fn(*copy.deepcopy(case["args"]))
    got = json.loads(json.dumps(got))
    if got != case["expected"]:
        sys.stderr.write(f"case {case['args']!r}: got {got!r}, expected {case['expected']!r}\n")
        sys.exit(1)
"""


def parse_name(filename: str) -> tuple[str, int | None]:
    """``(root author, level)`` for a file name; level is None for originals. O(1)."""
    m = COPY_RE.match(filename)
    if m:
        return m.group(2), int(m.group(1))
    return os.path.splitext(filename)[0], None


def ground_truth(folder: str) -> set[frozenset[str]]:
    """Unordered pairs of sids known to be copies of each other.

    Two files are a pair if they are in the same problem and share the same root
    original (an original and its copies, or two copies of one original).

    Complexity: O(F + P) for F files and P positive pairs.
    """
    roots: dict[tuple[str, str], list[str]] = {}
    for problem, path in iter_python_files(folder):
        name = os.path.basename(path)
        root, _ = parse_name(name)
        sid = f"{problem}/{os.path.splitext(name)[0]}"
        roots.setdefault((problem, root), []).append(sid)
    truth: set[frozenset[str]] = set()
    for sids in roots.values():
        truth.update(frozenset(p) for p in combinations(sorted(sids), 2))
    return truth


def copy_levels(folder: str) -> dict[str, int]:
    """Map the sid of every planted copy to its mutation level. O(F)."""
    out = {}
    for problem, path in iter_python_files(folder):
        name = os.path.basename(path)
        _, level = parse_name(name)
        if level is not None:
            out[f"{problem}/{os.path.splitext(name)[0]}"] = level
    return out


def check_solution(path: str, tests_path: str, timeout: float = TIMEOUT) -> bool:
    """True if the file's solve function passes every case in ``tests_path``.

    The file runs in a separate interpreter (never exec'd in this process) and is
    cut off after ``timeout`` seconds, so infinite loops fail cleanly.

    Complexity: one subprocess; time dominated by the submission itself.
    """
    cmd = [sys.executable, "-I", "-B", "-c", _RUNNER, os.path.abspath(path), os.path.abspath(tests_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.info("%s: timed out after %.0fs", path, timeout)
        return False
    if proc.returncode != 0:
        log.info("%s failed: %s", path, proc.stderr.strip().splitlines()[-1:] or "")
    return proc.returncode == 0


def validate_dataset(folder: str) -> list[str]:
    """Check the dataset; returns a list of problems found (empty means valid).

    Every file must pass its problem's tests.json, every copy's origin must
    exist, and no two files may be byte-identical.

    Complexity: one subprocess per file (run in parallel) plus O(total bytes).
    """
    errors: list[str] = []
    files = iter_python_files(folder)
    jobs = []
    for problem, path in files:
        tests = os.path.join(os.path.dirname(path), "tests.json")
        if not os.path.isfile(tests):
            errors.append(f"{problem}: missing tests.json")
            continue
        jobs.append((path, tests))
        root, level = parse_name(os.path.basename(path))
        if level is not None and not os.path.isfile(
            os.path.join(os.path.dirname(path), root + ".py")
        ):
            errors.append(f"{path}: origin {root}.py does not exist")
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        ok = list(pool.map(lambda job: check_solution(*job), jobs))
    errors.extend(f"{path}: fails its tests" for (path, _), good in zip(jobs, ok) if not good)
    seen: dict[str, str] = {}
    for _, path in files:
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        if digest in seen:
            errors.append(f"{path}: byte-identical to {seen[digest]}")
        seen.setdefault(digest, path)
    return sorted(set(errors))


def load_tests(tests_path: str) -> dict:
    """Read a tests.json file. O(size)."""
    with open(tests_path) as fh:
        return json.load(fh)
