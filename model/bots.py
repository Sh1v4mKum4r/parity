"""Scripted players. They stand in for a human so the model can be trained
and evaluated headlessly, without hundreds of hours of playtesting.

HabitualBot  - runs a memorised circuit. Its next room depends on where it is
               in that circuit, i.e. on *history*, not just current room.
               This is the behaviour a real player develops.
ExplorerBot  - systematic sweep, prefers least-recently-seen rooms.
RandomBot    - uniform over neighbours. The control: there is no habit here,
               so a working model must FAIL to beat baseline against it.
"""
from __future__ import annotations
import random
from collections import deque


def _bfs_path(fac, src: int, dst: int) -> list[int]:
    prev, q = {src: None}, deque([src])
    while q:
        cur = q.popleft()
        if cur == dst:
            break
        for nb in fac.neighbors(cur):
            if nb not in prev:
                prev[nb] = cur
                q.append(nb)
    if dst not in prev:
        return []
    path, cur = [], dst
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return path[::-1]


class HabitualBot:
    """Walks a fixed objective circuit: tables -> terminals -> comms, repeat."""
    name = "habitual"

    def __init__(self, fac, seed: int = 0, noise: float = 0.08):
        self.fac, self.rng, self.noise = fac, random.Random(seed), noise
        stops = [r for r in fac.rooms if fac.rooms[r].has_table]
        stops += [r for r in fac.rooms if fac.rooms[r].has_terminal]
        stops += [fac.comms_room]
        self.stops = stops
        self.route = self._build_route()
        self.i = 0

    def _build_route(self) -> list[int]:
        route, cur = [], self.stops[0]
        for nxt in self.stops[1:] + [self.stops[0]]:
            seg = _bfs_path(self.fac, cur, nxt)
            route += seg[1:] if route else seg
            cur = nxt
        return route or [self.stops[0]]

    @property
    def pos(self) -> int:
        return self.route[self.i % len(self.route)]

    def step(self) -> int:
        if self.rng.random() < self.noise:               # occasional deviation
            nbs = self.fac.neighbors(self.pos)
            if nbs:
                return self.rng.choice(nbs)
        self.i += 1
        return self.route[self.i % len(self.route)]

    def resync(self, actual: int) -> None:
        """After a forced/deviated move, snap back onto the circuit."""
        if self.route[self.i % len(self.route)] != actual:
            for k, r in enumerate(self.route):
                if r == actual:
                    self.i = k
                    return


class ExplorerBot:
    name = "explorer"

    def __init__(self, fac, seed: int = 0):
        self.fac, self.rng = fac, random.Random(seed)
        self.pos = min(fac.rooms)
        self.last_seen: dict[int, int] = {}
        self.t = 0

    def step(self) -> int:
        self.t += 1
        self.last_seen[self.pos] = self.t
        nbs = self.fac.neighbors(self.pos)
        if not nbs:
            return self.pos
        nxt = min(nbs, key=lambda r: (self.last_seen.get(r, -1), self.rng.random()))
        self.pos = nxt
        return nxt

    def resync(self, actual: int) -> None:
        self.pos = actual


class RandomBot:
    name = "random"

    def __init__(self, fac, seed: int = 0):
        self.fac, self.rng = fac, random.Random(seed)
        self.pos = min(fac.rooms)

    def step(self) -> int:
        nbs = self.fac.neighbors(self.pos)
        self.pos = self.rng.choice(nbs) if nbs else self.pos
        return self.pos

    def resync(self, actual: int) -> None:
        self.pos = actual
