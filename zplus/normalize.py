"""A1: turn Python source into a token list in which cosmetic edits disappear."""

from __future__ import annotations

import builtins
import io
import keyword
import tokenize

from zplus.errors import ZplusError
from zplus.types import Token

BUILTIN_NAMES = frozenset(dir(builtins))

# Token types that never reach the output: they carry no program structure.
_DROPPED = {tokenize.COMMENT, tokenize.NL, tokenize.ENCODING, tokenize.ENDMARKER}

# f-string (3.12+) and t-string (3.14+) pieces, looked up by name so older
# Pythons without these token types still work.
_FSTRING_START = {
    getattr(tokenize, n) for n in ("FSTRING_START", "TSTRING_START") if hasattr(tokenize, n)
}
_FSTRING_END = {
    getattr(tokenize, n) for n in ("FSTRING_END", "TSTRING_END") if hasattr(tokenize, n)
}

_STRUCTURE = {"INDENT", "DEDENT"}


def clean_source(source: str) -> str:
    """Strip a byte-order mark and convert Windows/old-Mac line endings to ``\\n``.

    Complexity: O(L) in the number of characters.
    """
    if source.startswith("﻿"):
        source = source[1:]
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _map_name(text: str, line: int, keep_names: bool) -> Token:
    if keyword.iskeyword(text):
        return Token("KW", text, line)
    if text in BUILTIN_NAMES:
        return Token("BUILTIN", text, line)
    return Token("ID", text if keep_names else "ID", line)


def _raw_tokens(source: str, keep_names: bool) -> list[Token]:
    """Map every tokenize token to a z-plus Token, collapsing f-strings."""
    out: list[Token] = []
    fdepth = 0  # nesting depth inside f-strings; > 0 means "swallow tokens"
    fline = 0
    reader = io.StringIO(source).readline
    for tok in tokenize.generate_tokens(reader):
        ttype = tok.type
        line = tok.start[0]
        if ttype in _FSTRING_START:
            if fdepth == 0:
                fline = line
            fdepth += 1
            continue
        if ttype in _FSTRING_END:
            fdepth -= 1
            if fdepth == 0:
                out.append(Token("STR", "STR", fline))
            continue
        if fdepth > 0 or ttype in _DROPPED:
            continue
        if ttype == tokenize.NAME:
            out.append(_map_name(tok.string, line, keep_names))
        elif ttype == tokenize.NUMBER:
            out.append(Token("NUM", "NUM", line))
        elif ttype == tokenize.STRING:
            out.append(Token("STR", "STR", line))
        elif ttype == tokenize.NEWLINE:
            out.append(Token("NEWLINE", "NEWLINE", line))
        elif ttype == tokenize.INDENT:
            out.append(Token("INDENT", "INDENT", line))
        elif ttype == tokenize.DEDENT:
            out.append(Token("DEDENT", "DEDENT", line))
        else:  # OP, and ERRORTOKEN on old Pythons: keep the text as written
            out.append(Token("OP", tok.string, line))
    return out


def _drop_bare_strings(tokens: list[Token]) -> list[Token]:
    """Remove docstrings and other string-only logical lines (plus their NEWLINE).

    INDENT/DEDENT tokens that precede the string are kept so block structure
    stays intact.
    """
    out: list[Token] = []
    line_buf: list[Token] = []
    for tok in tokens:
        if tok.kind != "NEWLINE":
            line_buf.append(tok)
            continue
        content = [t for t in line_buf if t.kind not in _STRUCTURE]
        if content and all(t.kind == "STR" for t in content):
            out.extend(t for t in line_buf if t.kind in _STRUCTURE)
        else:
            out.extend(line_buf)
            out.append(tok)
        line_buf = []
    out.extend(line_buf)  # trailing DEDENTs
    return out


def normalize(source: str, keep_names: bool = False) -> list[Token]:
    """Tokenize ``source`` and normalize it so renaming and reformatting vanish.

    Keywords, builtins and operators keep their text; other names become ``ID``
    (unless ``keep_names``), numbers ``NUM`` and strings ``STR``. Comments, blank
    lines and docstrings are dropped. Each token keeps its original line number.

    Raises ZplusError when the source cannot be tokenized.

    Complexity: O(L) time in the number of characters, O(n) space in tokens.
    """
    source = clean_source(source)
    if not source.strip():
        return []
    try:
        tokens = _raw_tokens(source, keep_names)
    except (tokenize.TokenError, SyntaxError) as exc:  # includes Indentation/TabError
        raise ZplusError(f"cannot tokenize: {exc}") from exc
    return _drop_bare_strings(tokens)
