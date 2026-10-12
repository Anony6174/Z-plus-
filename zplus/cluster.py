"""B3: union-find clustering of flagged pairs into rings."""

from __future__ import annotations

from zplus.types import PairResult


class UnionFind:
    """Disjoint sets with union by size and iterative path halving."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.size: dict[str, int] = {}

    def add(self, x: str) -> None:
        """Register ``x`` as its own set if unseen. O(1)."""
        if x not in self.parent:
            self.parent[x] = x
            self.size[x] = 1

    def find(self, x: str) -> str:
        """Root of ``x``'s set, halving the path on the way. Amortized O(alpha(n))."""
        self.add(x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> bool:
        """Merge the sets of ``a`` and ``b``; False if already joined. O(alpha(n))."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra  # smaller tree goes under the larger
        self.size[ra] += self.size[rb]
        return True

    def groups(self) -> list[set[str]]:
        """All sets, in no particular order. O(n alpha(n))."""
        out: dict[str, set[str]] = {}
        for x in self.parent:
            out.setdefault(self.find(x), set()).add(x)
        return list(out.values())


def cluster(pairs: list[PairResult], threshold: float) -> list[set[str]]:
    """Group sids linked by pairs with ``final >= threshold`` into rings.

    Self-pairs are ignored; repeated pairs are harmless. Returns groups of size
    2 or more, largest first, then by smallest sid.

    Complexity: O(E alpha(n)) for the unions plus O(G log G) to sort groups.
    """
    uf = UnionFind()
    for p in pairs:
        if p.a != p.b and p.scores.final >= threshold:
            uf.union(p.a, p.b)
    groups = [g for g in uf.groups() if len(g) >= 2]
    groups.sort(key=lambda g: (-len(g), min(g)))
    return groups
