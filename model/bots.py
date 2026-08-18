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
    """Cycles a fixed circuit of objective rooms: codebooks, then the uplink.

    It follows the same stops in the same order every lap, so its trajectory is
    highly regular -- which is precisely the habit a real player develops and the
    signal the predictor feeds on. It navigates by shortest path rather than by a
    memorised route, so when the Director seals or rewires a door the bot re-plans
    around it. That re-planning cost is what E5 measures.
    """
    name = "habitual"

    def __init__(self, fac, seed: int = 0, noise: float = 0.08, skew: bool = False):
        self.fac, self.rng, self.noise = fac, random.Random(seed), noise
        stops = [r for r in fac.rooms if fac.rooms[r].has_table]
        stops += [r for r in fac.rooms if fac.rooms[r].has_terminal]
        stops += [fac.comms_room]
        stops = stops or [min(fac.rooms)]
        if skew:
            # Uneven reliance: a real player leans on some rooms far harder than
            # others. With a uniform circuit every room is equally "relied on" and
            # targeted sabotage has nothing to aim at.
            favourite = stops[0]
            stops = [favourite if i % 2 == 0 else stops[(i // 2) % len(stops)]
                     for i in range(len(stops) * 2)]
        self.stops = stops
        self.stop_i = 0
        self.pos = self.stops[0]
        self.replans = 0
        self.laps = 0
        self._intended = None

    @property
    def target(self) -> int:
        return self.stops[self.stop_i % len(self.stops)]

    def step(self) -> int:
        # the door it was about to use is gone -> forced re-plan
        if self._intended is not None and self._intended not in self.fac.neighbors(self.pos):
            self.replans += 1

        if self.pos == self.target:
            self.stop_i += 1
            if self.stop_i % len(self.stops) == 0:
                self.laps += 1

        if self.rng.random() < self.noise:
            nbs = self.fac.neighbors(self.pos)
            nxt = self.rng.choice(nbs) if nbs else self.pos
        else:
            path = _bfs_path(self.fac, self.pos, self.target)
            nxt = path[1] if len(path) > 1 else self.pos

        self.pos = nxt
        p2 = _bfs_path(self.fac, self.pos, self.target)
        self._intended = p2[1] if len(p2) > 1 else None
        return nxt

    def resync(self, actual: int) -> None:
        self.pos = actual
        self._intended = None


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
