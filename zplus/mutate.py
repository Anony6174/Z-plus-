"""B4: disguised copies with known ground truth, for measuring accuracy.

Level 1 (cosmetic): consistent renaming, comments, blank lines, indentation.
Level 2 (light structure): level 1 plus swapping independent adjacent
assignments, dead code, and flipped comparisons.
Level 3 (structural): level 2 plus ``for i in range`` to ``while``,
``x += y`` to ``x = x + y``, inverted if/else, and reordered top-level defs.
"""

from __future__ import annotations

import ast
import io
import keyword
import logging
import os
import random
import tempfile
import tokenize

from zplus.dataset import check_solution, parse_name
from zplus.loader import read_source
from zplus.normalize import BUILTIN_NAMES

log = logging.getLogger(__name__)

ENTRY = "solve"
LEVEL_OPS = {
    1: ("rename", "cosmetic"),
    2: ("swap", "deadcode", "flip"),
    3: ("loops", "augassign", "invertif", "reorder"),
}
RETRIES = 5

_WORDS = (
    "acc alpha beta buf cell count cur data delta edge elem entry flag front "
    "goal grid head idx item key last left limit mark node num out pair part "
    "pos prev queue rank res right row seen size slot span stack start state "
    "step store tail temp total unit val walk width xs ys zone"
).split()
_COMMENTS = (
    "check the boundary first",
    "main loop",
    "keep track of progress",
    "TODO: tidy this up",
    "edge case",
    "update the running state",
    "this is the important part",
    "helper values",
    "walk through the input",
    "store the answer",
)
_MIRROR = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE,
           ast.Eq: ast.Eq, ast.NotEq: ast.NotEq}


# --------------------------------------------------------------------- names
class _Namer:
    """Fresh identifiers drawn from a word pool with a seeded RNG."""

    def __init__(self, rng: random.Random, taken: set[str]) -> None:
        self.rng = rng
        self.taken = set(taken)

    def fresh(self) -> str:
        while True:
            name = f"{self.rng.choice(_WORDS)}_{self.rng.choice(_WORDS)}"
            if self.rng.random() < 0.3:
                name += str(self.rng.randint(1, 9))
            if (name not in self.taken and not keyword.iskeyword(name)
                    and name not in BUILTIN_NAMES):
                self.taken.add(name)
                return name


def _all_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _bound_names(tree: ast.AST) -> set[str]:
    """Names the program itself defines: assignments, defs, arguments, etc."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            out.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.arg):
            out.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.add(node.name)
    return out


def _protected_names(tree: ast.AST) -> set[str]:
    """Names that must never change: imports, keyword arguments, class members."""
    out = {ENTRY}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                out.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.keyword) and node.arg:
            out.add(node.arg)
        elif isinstance(node, ast.ClassDef):  # members are reached via attributes
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.add(item.name)
                for target in getattr(item, "targets", [getattr(item, "target", None)]):
                    if isinstance(target, ast.Name):
                        out.add(target.id)
    return out


class _Renamer(ast.NodeTransformer):
    def __init__(self, mapping: dict[str, str]) -> None:
        self.m = mapping

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self.m.get(node.id, node.id)
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = self.m.get(node.arg, node.arg)
        self.generic_visit(node)
        return node

    def _rename_def(self, node):
        node.name = self.m.get(node.name, node.name)
        self.generic_visit(node)
        return node

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _rename_def

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if node.name:
            node.name = self.m.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_Global(self, node: ast.Global) -> ast.AST:
        node.names = [self.m.get(n, n) for n in node.names]
        return node

    visit_Nonlocal = visit_Global


def rename_all(tree: ast.AST, rng: random.Random) -> ast.AST:
    """Consistently rename every user-defined name (never builtins, imports,
    attributes, keyword-argument names, dunders or ``solve``). O(nodes)."""
    names = sorted(
        n for n in _bound_names(tree) - _protected_names(tree)
        if n not in BUILTIN_NAMES and not n.startswith("__")
    )
    namer = _Namer(rng, _all_names(tree))
    mapping = {n: namer.fresh() for n in names}
    return _Renamer(mapping).visit(tree)


# ----------------------------------------------------------- level 2 changes
def _names_in(node: ast.AST) -> tuple[set[str], set[str]]:
    """(reads, writes) of a simple statement; subscript/attribute bases count as both."""
    reads, writes = set(), set()
    targets = []
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        targets = [node.target]
    for t in targets:
        for sub in ast.walk(t):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                writes.add(sub.id)
        base = t
        while isinstance(base, (ast.Subscript, ast.Attribute, ast.Starred)):
            base = base.value
        if isinstance(base, ast.Name):
            writes.add(base.id)
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            reads.add(sub.id)
    if isinstance(node, ast.AugAssign):
        reads |= writes
    return reads, writes


_IMPURE = (ast.Call, ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr, ast.Lambda)


def independent(s1: ast.stmt, s2: ast.stmt) -> bool:
    """True if two adjacent statements may be swapped safely. O(size)."""
    simple = (ast.Assign, ast.AugAssign, ast.AnnAssign)
    if not (isinstance(s1, simple) and isinstance(s2, simple)):
        return False
    if isinstance(s1, ast.AnnAssign) and s1.value is None:
        return False
    if isinstance(s2, ast.AnnAssign) and s2.value is None:
        return False
    for s in (s1, s2):
        if any(isinstance(n, _IMPURE) for n in ast.walk(s)):
            return False
    r1, w1 = _names_in(s1)
    r2, w2 = _names_in(s2)
    return not (w1 & (r2 | w2)) and not (w2 & (r1 | w1))


def _statement_lists(tree: ast.AST):
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            stmts = getattr(node, field, None)
            if isinstance(stmts, list) and stmts and isinstance(stmts[0], ast.stmt):
                yield stmts


def swap_statements(tree: ast.AST, rng: random.Random, prob: float = 0.7) -> int:
    """Swap independent adjacent assignments in place; returns the swap count."""
    swaps = 0
    for stmts in list(_statement_lists(tree)):
        i = 0
        while i < len(stmts) - 1:
            if independent(stmts[i], stmts[i + 1]) and rng.random() < prob:
                stmts[i], stmts[i + 1] = stmts[i + 1], stmts[i]
                swaps += 1
                i += 2
            else:
                i += 1
    return swaps


class _FlipCompare(ast.NodeTransformer):
    def __init__(self, rng: random.Random, prob: float) -> None:
        self.rng, self.prob = rng, prob

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if len(node.ops) != 1 or type(node.ops[0]) not in _MIRROR:
            return node
        left, right = node.left, node.comparators[0]
        both_call = all(
            any(isinstance(n, _IMPURE) for n in ast.walk(side)) for side in (left, right)
        )
        if both_call or self.rng.random() >= self.prob:
            return node
        return ast.Compare(left=right, ops=[_MIRROR[type(node.ops[0])]()], comparators=[left])


def _has_docstring(body: list[ast.stmt]) -> bool:
    return bool(body) and isinstance(body[0], ast.Expr) and isinstance(
        getattr(body[0], "value", None), ast.Constant
    ) and isinstance(body[0].value.value, str)


def _dead_snippet(kind: int, namer: _Namer, rng: random.Random) -> list[ast.stmt]:
    a, b = namer.fresh(), namer.fresh()
    if kind == 0:
        code = f"{a} = {rng.randint(0, 99)}"
    elif kind == 1:
        code = (f"if False:\n    {a} = []\n    for {b} in range(10):\n"
                f"        {a}.append({b} * 2)\n")
    elif kind == 2:
        code = "for _ in range(0):\n    pass\n"
    else:
        code = f"{a} = []\n{b} = len({a})"
    return ast.parse(code).body


def insert_dead_code(tree: ast.Module, rng: random.Random, namer: _Namer) -> None:
    """Add unused variables, ``if False`` blocks, empty loops and a helper."""
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for _ in range(rng.randint(2, 3)):
        if not funcs:
            break
        fn = rng.choice(funcs)
        lo = 1 if _has_docstring(fn.body) else 0
        pos = rng.randint(lo, len(fn.body))
        fn.body[pos:pos] = _dead_snippet(rng.randrange(4), namer, rng)
    h, p, q, r = (namer.fresh() for _ in range(4))
    helper = ast.parse(
        f"def {h}({p}, {q}):\n    {r} = {p} + {q}\n    if {r} > 0:\n"
        f"        return {r}\n    return -{r}\n"
    ).body[0]
    first = 1 if _has_docstring(tree.body) else 0
    while first < len(tree.body) and isinstance(tree.body[first], (ast.Import, ast.ImportFrom)):
        first += 1
    tree.body.insert(rng.randint(first, len(tree.body)), helper)


# ----------------------------------------------------------- level 3 changes
def _loop_level_nodes(body: list[ast.stmt]):
    """Nodes in ``body`` that belong to this loop (not nested loops or defs)."""
    stack = list(body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.For, ast.While, ast.AsyncFor, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))


class _ForToWhile(ast.NodeTransformer):
    def __init__(self, rng: random.Random, namer: _Namer, prob: float) -> None:
        self.rng, self.namer, self.prob = rng, namer, prob

    def visit_For(self, node: ast.For):
        self.generic_visit(node)
        it = node.iter
        if not (isinstance(node.target, ast.Name) and isinstance(it, ast.Call)
                and isinstance(it.func, ast.Name) and it.func.id == "range"
                and 1 <= len(it.args) <= 2 and not it.keywords and not node.orelse):
            return node
        if any(isinstance(n, ast.Starred) for n in it.args):
            return node
        var = node.target.id
        if any(isinstance(n, ast.Continue) for n in _loop_level_nodes(node.body)):
            return node
        for n in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if isinstance(n, ast.Name) and n.id == var and not isinstance(n.ctx, ast.Load):
                return node
            if isinstance(n, (ast.Global, ast.Nonlocal)) and var in n.names:
                return node
        if self.rng.random() >= self.prob:
            return node
        start = it.args[0] if len(it.args) == 2 else ast.Constant(0)
        stop = it.args[-1]
        out: list[ast.stmt] = [ast.Assign(targets=[ast.Name(var, ast.Store())], value=start)]
        if not isinstance(stop, ast.Constant):
            lim = self.namer.fresh()  # evaluate the bound once, like range() does
            out.append(ast.Assign(targets=[ast.Name(lim, ast.Store())], value=stop))
            stop = ast.Name(lim, ast.Load())
        step = ast.AugAssign(target=ast.Name(var, ast.Store()), op=ast.Add(),
                             value=ast.Constant(1))
        test = ast.Compare(left=ast.Name(var, ast.Load()), ops=[ast.Lt()], comparators=[stop])
        out.append(ast.While(test=test, body=node.body + [step], orelse=[]))
        return out


class _ExpandAugAssign(ast.NodeTransformer):
    def __init__(self, rng: random.Random, prob: float) -> None:
        self.rng, self.prob = rng, prob

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        if not isinstance(node.target, ast.Name) or self.rng.random() >= self.prob:
            return node
        load = ast.Name(node.target.id, ast.Load())
        value = ast.BinOp(left=load, op=node.op, right=node.value)
        return ast.Assign(targets=[ast.Name(node.target.id, ast.Store())], value=value)


class _InvertIf(ast.NodeTransformer):
    def __init__(self, rng: random.Random, prob: float) -> None:
        self.rng, self.prob = rng, prob

    def visit_If(self, node: ast.If) -> ast.AST:
        self.generic_visit(node)
        if not node.orelse or self.rng.random() >= self.prob:
            return node
        test = node.test
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            test = test.operand
        else:
            test = ast.UnaryOp(op=ast.Not(), operand=test)
        return ast.If(test=test, body=node.orelse, orelse=node.body)


def reorder_defs(tree: ast.Module, rng: random.Random) -> None:
    """Shuffle plain top-level defs (no decorators, no defaults) among their slots."""
    slots = [
        i for i, n in enumerate(tree.body)
        if isinstance(n, ast.FunctionDef) and not n.decorator_list
        and not n.args.defaults and not any(n.args.kw_defaults)
    ]
    if len(slots) < 2:
        return
    defs = [tree.body[i] for i in slots]
    order = defs[:]
    while order == defs:
        rng.shuffle(order)
    for i, d in zip(slots, order):
        tree.body[i] = d


# ---------------------------------------------------------------- cosmetics
def _logical_line_starts(code: str) -> tuple[list[int], bool]:
    """1-based rows where a logical line starts, and whether any string spans lines."""
    starts, multiline = [], False
    at_start = True
    for tok in tokenize.generate_tokens(io.StringIO(code).readline):
        if tok.type == tokenize.STRING and tok.start[0] != tok.end[0]:
            multiline = True
        if tok.type == tokenize.NEWLINE:
            at_start = True
        elif at_start and tok.type not in (tokenize.NL, tokenize.COMMENT, tokenize.INDENT,
                                           tokenize.DEDENT, tokenize.ENDMARKER,
                                           tokenize.ENCODING):
            starts.append(tok.start[0])
            at_start = False
    return starts, multiline


def cosmetic(code: str, rng: random.Random) -> str:
    """Add comments and blank lines, and sometimes change the indent width."""
    starts, multiline = _logical_line_starts(code)
    lines = code.split("\n")
    if not multiline and rng.random() < 0.5:
        lines = [" " * ((len(ln) - len(ln.lstrip(" "))) // 2) + ln.lstrip(" ") for ln in lines]
    safe = set(starts)
    out = []
    for row, line in enumerate(lines, start=1):
        if row in safe:
            indent = line[: len(line) - len(line.lstrip())]
            if rng.random() < 0.15:
                out.append("")
            if rng.random() < 0.2:
                out.append(f"{indent}# {rng.choice(_COMMENTS)}")
        out.append(line)
    if rng.random() < 0.5:
        out.insert(0, f"# {rng.choice(_COMMENTS)}")
    return "\n".join(out).rstrip("\n") + "\n"


# ---------------------------------------------------------------------- API
def ops_for_level(level: int) -> tuple[str, ...]:
    """Every operation a level applies, lower levels included. O(1)."""
    if level not in LEVEL_OPS:
        raise ValueError("level must be 1, 2 or 3")
    return tuple(op for lv in range(1, level + 1) for op in LEVEL_OPS[lv])


def mutate(source: str, level: int, seed: int, skip: frozenset[str] = frozenset()) -> str:
    """Return a disguised copy of ``source`` at ``level`` (1, 2 or 3).

    Deterministic for a given seed. Operations named in ``skip`` are left out
    (used by the safety net in ``make_copies``).

    Complexity: linear in the size of the AST.
    """
    ops = [op for op in ops_for_level(level) if op not in skip]
    rng = random.Random(seed)
    tree = ast.parse(source)
    namer = _Namer(rng, _all_names(tree))
    if "loops" in ops:
        tree = _ForToWhile(rng, namer, 0.8).visit(tree)
    if "invertif" in ops:
        tree = _InvertIf(rng, 0.7).visit(tree)
    if "augassign" in ops:
        tree = _ExpandAugAssign(rng, 0.8).visit(tree)
    if "reorder" in ops:
        reorder_defs(tree, rng)
    if "flip" in ops:
        tree = _FlipCompare(rng, 0.6).visit(tree)
    if "swap" in ops:
        swap_statements(tree, rng)
    if "deadcode" in ops:
        insert_dead_code(tree, rng, namer)
    if "rename" in ops:
        tree = rename_all(tree, rng)
    code = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
    if "cosmetic" in ops:
        code = cosmetic(code, rng)
    return code


def _passes(code: str, tests_path: str) -> bool:
    try:
        compile(code, "<mutant>", "exec")
    except SyntaxError:
        return False
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(code)
        return check_solution(path, tests_path)
    finally:
        os.unlink(path)


def safe_mutate(source: str, level: int, seed: int, tests_path: str) -> str:
    """Mutate with the safety net: compile and test, retry with seed + 1 up to 5
    times, then drop operations (latest first) until the copy passes.

    Raises RuntimeError if even the plainest mutant fails.
    """
    skip: list[str] = []
    for op in [None, *reversed(ops_for_level(level))]:
        if op is not None:
            skip.append(op)
            log.warning("dropping operation %r after %d failed seeds", op, RETRIES)
        for s in range(seed, seed + RETRIES):
            code = mutate(source, level, s, frozenset(skip))
            if _passes(code, tests_path):
                return code
    raise RuntimeError("no passing mutant found")


def make_copies(folder: str, per_problem: int, seed: int) -> None:
    """Write planted copies ``copy<n>_L<level>_of_<author>.py`` into each problem.

    For each problem folder with a tests.json, picks ``per_problem`` different
    originals and applies levels 1, 2, 3, 1, 2, 3, ... Existing copies are
    replaced, so the command is repeatable.

    Complexity: one mutation and one test subprocess per copy (more on retries).
    """
    for problem in sorted(os.listdir(folder)):
        pdir = os.path.join(folder, problem)
        tests = os.path.join(pdir, "tests.json")
        if not os.path.isfile(tests):
            continue
        for f in os.listdir(pdir):
            if f.endswith(".py") and parse_name(f)[1] is not None:
                os.remove(os.path.join(pdir, f))
        originals = sorted(
            f[:-3] for f in os.listdir(pdir) if f.endswith(".py") and f != "template.py"
        )
        if per_problem > len(originals):
            raise ValueError(f"{problem}: only {len(originals)} originals")
        rng = random.Random(f"{seed}:{problem}")
        chosen = rng.sample(originals, per_problem)
        for n, author in enumerate(chosen, start=1):
            level = (n - 1) % 3 + 1
            src = read_source(os.path.join(pdir, author + ".py"))
            code = safe_mutate(src, level, seed * 1000 + n, tests)
            out = os.path.join(pdir, f"copy{n}_L{level}_of_{author}.py")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(code)
            log.info("wrote %s", out)
