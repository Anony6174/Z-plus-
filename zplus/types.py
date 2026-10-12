"""Shared data contracts (task S1).

Every module codes against these types. Change them only by agreement.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Token:
    kind: str  # "KW", "BUILTIN", "ID", "NUM", "STR", "OP", "NEWLINE", "INDENT", "DEDENT"
    text: str  # keywords, builtins, operators as written; "ID", "NUM", "STR" otherwise
    line: int  # 1-based line in the ORIGINAL file, used for highlighting


@dataclass
class Submission:
    sid: str  # unique id, e.g. "p1/alice"
    author: str  # file stem, e.g. "alice"
    problem: str  # folder name, e.g. "p1"
    path: str
    source: str  # raw text
    tokens: list[Token]


@dataclass(frozen=True)
class Fingerprint:
    hash: int  # 0 <= hash < 2**61 - 1
    pos: int  # index of the k-gram's first token in Submission.tokens


@dataclass(frozen=True)
class Candidate:
    a: str  # sid; a < b alphabetically so each pair appears once
    b: str
    shared: int  # number of distinct fingerprint hashes the two share


@dataclass(frozen=True)
class Match:
    a_start: int  # token index in submission a
    b_start: int  # token index in submission b
    length: int  # number of tokens


@dataclass
class Scores:
    jaccard: float
    containment: float  # max(|A&B|/|A|, |A&B|/|B|) on fingerprint hashes
    tiling: float | None  # from B2, None if not run
    ast: float | None  # from A6, None if disabled
    final: float  # decided in B1 (combine)


@dataclass
class PairResult:
    a: str
    b: str
    scores: Scores
    matches: list[Match]


@dataclass
class Config:
    k: int = 6  # k-gram length in tokens
    w: int = 4  # winnowing window, in k-grams
    min_shared: int = 3  # A4: fewest shared hashes to become a candidate
    max_df: float = 0.3  # A4: drop hashes found in more than 30% of submissions
    min_match: int = 8  # B2: shortest tile, in tokens
    threshold: float = 0.6  # B3 and B6: score at which a pair is flagged
    use_ast: bool = True  # A6 on or off


@dataclass
class Skipped:
    sid: str
    reason: str


@dataclass
class Report:
    pairs: list[PairResult]  # every scored candidate pair, highest final first
    clusters: list[set[str]]  # rings from B3
    skipped: list[Skipped] = field(default_factory=list)
    config: Config = field(default_factory=Config)
    submissions: dict[str, Submission] = field(default_factory=dict)
    n_candidates: int = 0

    def flagged(self) -> list[PairResult]:
        """Pairs at or above the threshold, highest final first. O(P log P)."""
        hits = [p for p in self.pairs if p.scores.final >= self.config.threshold]
        return sorted(hits, key=lambda p: (-p.scores.final, p.a, p.b))


@dataclass
class Metrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    recall_by_level: dict[int, float | None] = field(default_factory=dict)
