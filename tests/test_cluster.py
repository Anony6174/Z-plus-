import random
from collections import deque

from zplus.cluster import UnionFind, cluster
from zplus.types import PairResult, Scores


def pr(a, b, final):
    return PairResult(a, b, Scores(0, 0, None, None, final), [])


def test_chain_gives_one_group():
    assert cluster([pr("A", "B", 0.9), pr("B", "C", 0.8)], 0.6) == [{"A", "B", "C"}]


def test_two_separate_pairs():
    assert cluster([pr("C", "D", 0.9), pr("A", "B", 0.9)], 0.6) == [{"A", "B"}, {"C", "D"}]


def test_threshold_filters():
    pairs = [pr("A", "B", 0.9), pr("B", "C", 0.5)]
    assert cluster(pairs, 0.6) == [{"A", "B"}]
    assert cluster(pairs, 0.95) == []
    assert cluster([], 0.5) == []


def test_repeats_and_self_pairs_ignored():
    pairs = [pr("A", "B", 0.9), pr("A", "B", 0.9), pr("C", "C", 1.0)]
    assert cluster(pairs, 0.6) == [{"A", "B"}]


def test_order_largest_first_then_smallest_sid():
    pairs = [pr("x", "y", 1), pr("a", "b", 1), pr("m", "n", 1), pr("n", "o", 1)]
    assert cluster(pairs, 0.5) == [{"m", "n", "o"}, {"a", "b"}, {"x", "y"}]


def test_union_by_size_and_find():
    uf = UnionFind()
    assert uf.union("a", "b")
    assert not uf.union("b", "a")
    uf.union("c", "a")
    assert uf.find("c") == uf.find("b")
    assert uf.size[uf.find("a")] == 3


def bfs_groups(pairs, threshold):
    adj = {}
    for p in pairs:
        if p.a != p.b and p.scores.final >= threshold:
            adj.setdefault(p.a, set()).add(p.b)
            adj.setdefault(p.b, set()).add(p.a)
    seen, groups = set(), []
    for start in adj:
        if start in seen:
            continue
        group, q = set(), deque([start])
        seen.add(start)
        while q:
            x = q.popleft()
            group.add(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        groups.append(group)
    return sorted(groups, key=lambda g: (-len(g), min(g)))


def test_property_matches_bfs_on_random_graphs():
    rng = random.Random(9)
    for _ in range(500):
        nodes = [f"s{i}" for i in range(rng.randint(1, 25))]
        pairs = [pr(rng.choice(nodes), rng.choice(nodes), rng.random())
                 for _ in range(rng.randint(0, 40))]
        t = rng.random()
        assert cluster(pairs, t) == bfs_groups(pairs, t)
