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

    def __init__(self, fac, seed: int = 0, noise: float = 0.08, skew: bool = False,
                 write_p: float = 0.18, dwell_max: int = 0):
        self.fac, self.rng, self.noise = fac, random.Random(seed), noise
        # A player does not linger at random -- they linger where there is
        # something to record: a codebook to copy, a sequence to decode, the
        # register to stage and verify. Drawing is real-time, so an open door and
        # an unfinished page compete, but only in rooms that gave them work.
        self.write_p = write_p
        self.dwell_max = dwell_max
        self.waits = 0
        self._writing = 0
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

        room = self.fac.rooms[self.pos]
        has_work = room.has_table or room.has_terminal or room.is_comms
        if self._writing > 0:
            self._writing -= 1
            self.waits += 1
            self._intended = None
            return self.pos                      # mid-page, decline the window
        if has_work and self.rng.random() < self.write_p * 1.6:
            self._writing = self.rng.randint(0, self.dwell_max)  # a page can take several windows
            self.waits += 1
            self._intended = None
            return self.pos
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

    def __init__(self, fac, seed: int = 0, **kw):
        self.fac, self.rng = fac, random.Random(seed)
        self.pos = min(fac.rooms)
        self.last_seen: dict[int, int] = {}
        self.t = 0
        self.waits = 0

    def step(self) -> int:
        self.t += 1
        self.last_seen[self.pos] = self.t
        room = self.fac.rooms[self.pos]
        if (room.has_table or room.has_terminal or room.is_comms) and self.rng.random() < 0.29:
            self.waits += 1
            return self.pos                      # stopped to record what is here
        nbs = self.fac.neighbors(self.pos)
        if not nbs:
            return self.pos
        nxt = min(nbs, key=lambda r: (self.last_seen.get(r, -1), self.rng.random()))
        self.pos = nxt
        return nxt

    def resync(self, actual: int) -> None:
        self.pos = actual


class EvasiveBot:
    """A player who deliberately uses waiting to break the pattern.

    This is the counter-play to a predictive antagonist: if it intercepts where
    you are going, do not go. It pursues the same objective circuit as
    HabitualBot but declines windows at random to desynchronise from anything
    modelling it. Included to test whether the player can actually fight back --
    a fair adaptive AI must be beatable by this.
    """
    name = "evasive"

    def __init__(self, fac, seed: int = 0, wait_p: float = 0.35, **kw):
        self.fac, self.rng, self.wait_p = fac, random.Random(seed), wait_p
        stops = [r for r in fac.rooms if fac.rooms[r].has_table]
        stops += [r for r in fac.rooms if fac.rooms[r].has_terminal]
        stops += [fac.comms_room]
        self.stops = stops or [min(fac.rooms)]
        self.stop_i = 0
        self.pos = self.stops[0]
        self.waits = 0
        self.laps = 0

    @property
    def target(self) -> int:
        return self.stops[self.stop_i % len(self.stops)]

    def step(self) -> int:
        if self.pos == self.target:
            self.stop_i += 1
            if self.stop_i % len(self.stops) == 0:
                self.laps += 1
        if self.rng.random() < self.wait_p:
            self.waits += 1
            return self.pos                      # decline the window on purpose
        path = _bfs_path(self.fac, self.pos, self.target)
        self.pos = path[1] if len(path) > 1 else self.pos
        return self.pos

    def resync(self, actual: int) -> None:
        self.pos = actual


class RandomBot:
    name = "random"

    def __init__(self, fac, seed: int = 0, **kw):
        self.fac, self.rng = fac, random.Random(seed)
        self.pos = min(fac.rooms)
        self.waits = 0

    def step(self) -> int:
        # staying is one of the legal choices at every window
        opts = self.fac.neighbors(self.pos) + [self.pos]
        nxt = self.rng.choice(opts)
        if nxt == self.pos:
            self.waits += 1
        self.pos = nxt
        return self.pos

    def resync(self, actual: int) -> None:
        self.pos = actual
