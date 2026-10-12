"""A6: AST structural hashing, a second opinion that survives statement reordering."""

from __future__ import annotations

import ast
import hashlib
import logging
from collections import Counter
from functools import lru_cache

from zplus.normalize import clean_source

log = logging.getLogger(__name__)

_CONTEXTS = (ast.Load, ast.Store, ast.Del)


class _CanonicalizeAugAssign(ast.NodeTransformer):
    """Rewrite ``x += y`` as ``x = x + y`` so both spellings hash the same."""

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        self.generic_visit(node)
        value = ast.BinOp(left=node.target, op=node.op, right=node.value)
        return ast.Assign(targets=[node.target], value=value)


def _children(node: ast.AST) -> list[ast.AST]:
    return [c for c in ast.iter_child_nodes(node) if not isinstance(c, _CONTEXTS)]


def _stable_hash(text: str) -> str:
    return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()


def subtree_hashes(tree: ast.AST, min_nodes: int = 8) -> Counter[str]:
    """Multiset of structure hashes of every subtree with at least ``min_nodes`` nodes.

    A node's hash is a stable hash of ``NodeType(child1,child2,...)``; identifier
    names and constant values are ignored, operator node types are kept, and
    Load/Store/Del contexts are skipped. The walk is iterative (post-order), so
    deeply nested code cannot hit the recursion limit.

    Complexity: O(number of AST nodes).
    """
    kept: Counter[str] = Counter()
    # Frame: (node, its children, (hash, size) results of children done so far)
    stack: list[tuple[ast.AST, list[ast.AST], list[tuple[str, int]]]] = [
        (tree, _children(tree), [])
    ]
    while stack:
        node, children, done = stack[-1]
        if len(done) < len(children):
            child = children[len(done)]
            stack.append((child, _children(child), []))
            continue
        stack.pop()
        label = f"{type(node).__name__}({','.join(h for h, _ in done)})"
        h = _stable_hash(label)
        size = 1 + sum(s for _, s in done)
        if size >= min_nodes:
            kept[h] += 1
        if stack:
            stack[-1][2].append((h, size))
    return kept


@lru_cache(maxsize=4096)
def _profile(source: str, min_nodes: int) -> Counter[str] | None:
    """Parse once per distinct source; ``None`` on a syntax error."""
    try:
        tree = ast.parse(clean_source(source))
    except (SyntaxError, ValueError) as exc:
        log.warning("AST parse failed: %s", exc)
        return None
    tree = _CanonicalizeAugAssign().visit(tree)
    return subtree_hashes(tree, min_nodes)


def ast_similarity(src_a: str, src_b: str, min_nodes: int = 8) -> float:
    """Overlap coefficient of the two files' subtree-hash multisets, 0 to 1.

    ``sum(min(countA, countB)) / min(|A|, |B|)``. A syntax error in either file,
    or no subtree reaching ``min_nodes``, gives 0.0.

    Complexity: O(nodes in A + nodes in B) (parses are cached per source).
    """
    pa = _profile(src_a, min_nodes)
    pb = _profile(src_b, min_nodes)
    if not pa or not pb:
        return 0.0
    shared = sum((pa & pb).values())
    return shared / min(sum(pa.values()), sum(pb.values()))
