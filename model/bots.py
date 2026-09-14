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
                 write_p: float = 0.18, dwell_max: int = 0, **kw):
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


class StealthBot:
    """A player who routes around the sensors.

    The evasive player waits at random, which denies the antagonist a little
    information but nothing it cannot recover. This one knows which doors are
    wired -- the knowledge the fiction says you buy with dangerous tasks -- and
    prefers to travel through the gaps, accepting a longer route to stay off the
    trail. It only waits when every exit would announce it.
    """
    name = "stealth"

    def __init__(self, fac, seed: int = 0, net=None, detour: float = 2.0,
                 disable_budget: int = 0, **kw):
        self.fac, self.rng, self.net, self.detour = fac, random.Random(seed), net, detour
        self.disable_budget = disable_budget
        stops = [r for r in fac.rooms if fac.rooms[r].has_table]
        stops += [r for r in fac.rooms if fac.rooms[r].has_terminal]
        stops += [fac.comms_room]
        self.stops = stops or [min(fac.rooms)]
        self.stop_i = 0
        self.pos = self.stops[0]
        self.waits = 0
        self.laps = 0
        self.quiet_moves = 0
        self.loud_moves = 0
        self._held = 0
        self.disabled = 0
        self.write_p = kw.get("write_p", 0.18)
        self._writing = 0
        if disable_budget and net is not None:
            self._burn_sensors(disable_budget)

    def _burn_sensors(self, budget: int):
        """Spend dangerous tasks to silence sensors on the route you already want.

        The alternative -- detouring around live doors -- costs more exposure than
        it saves. This models the fiction's actual mechanic: you do not avoid the
        sensor, you kill it.
        """
        route, cur = [], self.stops[0]
        for nxt in self.stops[1:] + [self.stops[0]]:
            d, prev = {cur: 0}, {cur: None}
            q = [cur]
            while q:
                c = q.pop(0)
                if c == nxt: break
                for nb in self.fac.neighbors(c):
                    if nb not in d:
                        d[nb] = d[c] + 1; prev[nb] = c; q.append(nb)
            path, c = [], nxt
            while c is not None:
                path.append(c); c = prev.get(c)
            path.reverse()
            route += list(zip(path, path[1:]))
            cur = nxt
        from collections import Counter
        freq = Counter(tuple(sorted(e)) for e in route)
        for e, _ in freq.most_common():
            if self.disabled >= budget: break
            if e in self.net.wired:
                self.net.wired.discard(e)
                self.disabled += 1

    @property
    def target(self) -> int:
        return self.stops[self.stop_i % len(self.stops)]

    def _dist(self, src):
        d, q = {src: 0}, [src]
        while q:
            cur = q.pop(0)
            for nb in self.fac.neighbors(cur):
                if nb not in d:
                    d[nb] = d[cur] + 1
                    q.append(nb)
        return d

    def step(self) -> int:
        if self.pos == self.target:
            self.stop_i += 1
            if self.stop_i % len(self.stops) == 0:
                self.laps += 1
        # same notebook cost as the habitual player: you stop where there is
        # something to record, or the comparison is not like for like
        room = self.fac.rooms[self.pos]
        has_work = room.has_table or room.has_terminal or room.is_comms
        if self._writing > 0:
            self._writing -= 1; self.waits += 1; return self.pos
        if has_work and self.rng.random() < self.write_p * 1.6:
            self._writing = 0; self.waits += 1; return self.pos
        dist = self._dist(self.target)
        here = dist.get(self.pos, 99)
        best, best_score = self.pos, -1e9
        for c in self.fac.neighbors(self.pos) + [self.pos]:
            progress = here - dist.get(c, 99)          # +1 closer, -1 further
            quiet = (c == self.pos) or (self.net is None) or (not self.net.is_wired(self.pos, c))
            score = progress + (self.detour if quiet else 0.0)
            if c == self.pos:
                # waiting is a last resort, and gets rapidly more expensive:
                # a player who never moves never escapes
                score -= 0.9 + 1.6 * self._held
            score += self.rng.random() * 0.01
            if score > best_score:
                best, best_score = c, score
        if best == self.pos:
            self.waits += 1; self._held += 1
        else:
            self._held = 0
        if best == self.pos:
            pass
        elif self.net is not None and self.net.is_wired(self.pos, best):
            self.loud_moves += 1
        else:
            self.quiet_moves += 1
        self.pos = best
        return best

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
