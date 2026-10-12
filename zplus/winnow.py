"""A3: winnowing (Schleimer, Wilkerson and Aiken, 2003)."""

from __future__ import annotations

from collections import deque

from zplus.types import Fingerprint


def winnow(hashes: list[tuple[int, int]], w: int) -> list[Fingerprint]:
    """Keep the minimum hash of every window of ``w`` consecutive k-gram hashes.

    Ties go to the rightmost minimum, and a position is recorded only once.
    Guarantee: any shared token run of at least ``w + k - 1`` tokens yields at
    least one shared fingerprint. A list shorter than ``w`` gives its single
    (rightmost) minimum. Raises ValueError if ``w < 1``.

    Returns fingerprints sorted by position.

    Complexity: O(n) time with a monotonic deque (a plain scan is O(nw)).
    """
    if w < 1:
        raise ValueError("w must be at least 1")
    n = len(hashes)
    if n == 0:
        return []
    if n < w:
        best = min(range(n), key=lambda i: (hashes[i][0], -i))
        return [Fingerprint(hashes[best][0], hashes[best][1])]
    out: list[Fingerprint] = []
    dq: deque[int] = deque()  # indices whose hashes increase front to back
    last = -1
    for i in range(n):
        h = hashes[i][0]
        while dq and hashes[dq[-1]][0] >= h:
            dq.pop()
        dq.append(i)
        while dq[0] <= i - w:
            dq.popleft()
        if i >= w - 1 and dq[0] != last:
            last = dq[0]
            out.append(Fingerprint(hashes[last][0], hashes[last][1]))
    return out
