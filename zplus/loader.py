"""A1: find and load submissions from a folder."""

from __future__ import annotations

import ast
import logging
import os

from zplus.errors import ZplusError
from zplus.normalize import clean_source, normalize
from zplus.types import Skipped, Submission

log = logging.getLogger(__name__)

TEMPLATE_NAME = "template.py"
LARGE_FILE_TOKENS = 20_000


def _is_hidden(name: str) -> bool:
    return name.startswith(".") or name.startswith("__")


def _py_files(directory: str) -> list[str]:
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".py")
        and f != TEMPLATE_NAME
        and not _is_hidden(f)
        and os.path.isfile(os.path.join(directory, f))
    )


def iter_python_files(folder: str) -> list[tuple[str, str]]:
    """List ``(problem, path)`` for every submission under ``folder``.

    ``folder/<problem>/*.py`` gives one problem per subfolder; ``.py`` files placed
    directly in ``folder`` belong to a problem named after ``folder`` itself.
    ``template.py`` files are never submissions.

    Raises ZplusError if ``folder`` is not a directory.

    Complexity: O(F log F) in the number of files (sorting).
    """
    if not os.path.isdir(folder):
        raise ZplusError(f"not a folder: {folder}")
    folder = os.path.abspath(folder)
    found = [(os.path.basename(folder), p) for p in _py_files(folder)]
    for name in sorted(os.listdir(folder)):
        sub = os.path.join(folder, name)
        if os.path.isdir(sub) and not _is_hidden(name):
            found.extend((name, p) for p in _py_files(sub))
    return found


def problem_dirs(folder: str) -> dict[str, str]:
    """Map each problem name under ``folder`` to its directory. O(F)."""
    out: dict[str, str] = {}
    for problem, path in iter_python_files(folder):
        out.setdefault(problem, os.path.dirname(path))
    return out


def read_source(path: str) -> str:
    """Read a file as UTF-8, replacing undecodable bytes. O(L)."""
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def load_submissions(
    folder: str,
    keep_names: bool = False,
    skipped: list[Skipped] | None = None,
) -> list[Submission]:
    """Load and normalize every submission under ``folder``.

    Unreadable or unparsable files are skipped with a logged warning; when a
    ``skipped`` list is given, a ``Skipped(sid, reason)`` is appended for each.
    Submissions come back sorted by sid, with ``sid = "<problem>/<stem>"``.

    Complexity: O(total characters) for reading and normalizing.
    """
    subs: list[Submission] = []
    for problem, path in iter_python_files(folder):
        author = os.path.splitext(os.path.basename(path))[0]
        sid = f"{problem}/{author}"
        reason = None
        try:
            source = read_source(path)
            ast.parse(clean_source(source))
            tokens = normalize(source, keep_names=keep_names)
        except OSError as exc:
            reason = f"unreadable: {exc.strerror or exc}"
        except (SyntaxError, ValueError) as exc:
            reason = f"syntax error: {exc.msg if isinstance(exc, SyntaxError) else exc}"
        except ZplusError as exc:
            reason = str(exc)
        if reason is not None:
            log.warning("skipping %s: %s", sid, reason)
            if skipped is not None:
                skipped.append(Skipped(sid, reason))
            continue
        if len(tokens) > LARGE_FILE_TOKENS:
            log.warning("%s has %d tokens; tiling will be slow", sid, len(tokens))
        subs.append(Submission(sid, author, problem, path, source, tokens))
    subs.sort(key=lambda s: s.sid)
    return subs
