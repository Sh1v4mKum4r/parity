"""Partial observation: the antagonist senses the player through door motion
detectors rather than by knowing where they are.

This is milestone M6, and it exists because of a negative result. Under perfect
observation an evasive player who declined a third of all windows reduced their
capture risk by only 1.7% -- standing still cannot conceal you from something that
already knows your room, it only makes you a stationary target. The diagnosis was
the observation model, not the algorithm.

Here the antagonist observes one thing per window: which door, if any, tripped a
sensor. It maintains a belief over rooms and updates it with a forward filter:

    predict   b'(c) = sum_r b(r) * T(r -> c)
    update    zero out any state inconsistent with the evidence, renormalise

Silence is the interesting case. It is ambiguous between "they stayed put" and
"they moved through a door with no sensor on it" -- and that ambiguity is what
makes waiting a real tactic rather than a measured failure.
"""
from __future__ import annotations
import random
from collections import defaultdict


def ekey(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a <= b else (b, a)


class SensorNet:
    """Motion detectors on doors. `coverage` is the fraction that are live.

    Coverage below 1.0 stands in for the two ways the fiction takes sensors off
    line: doors the facility never wired, and sensors the player has burned a
    dangerous task to disable.
    """

    def __init__(self, fac, coverage: float = 1.0, seed: int = 0):
        self.fac = fac
        edges = sorted({ekey(a, b) for a in fac.rooms for b in fac.neighbors(a)})
        rng = random.Random(seed)
        rng.shuffle(edges)
        n = int(round(coverage * len(edges)))
        self.wired = set(edges[:n])
        self.all_edges = set(edges)
        self.coverage = coverage

    def is_wired(self, a: int, b: int) -> bool:
        return ekey(a, b) in self.wired

    def event(self, a: int, b: int):
        """What the antagonist hears when the player goes from a to b.

        A detector reports that a door opened. It does NOT report a direction,
        and staying put trips nothing at all.
        """
        if a == b:
            return None
        return ekey(a, b) if self.is_wired(a, b) else None


class BeliefTracker:
    """The antagonist's posterior over the player's room, from door events alone.

    transition_prior:
      "uniform"  -- the filter assumes nothing about habits: every door and
                    staying are equally likely. Pure geometry plus evidence.
      "learned"  -- an order-1 transition model estimated online from the
                    antagonist's own MAP track. Uses its behavioural model to
                    sharpen the predict step, at the risk of compounding its own
                    mistakes when it is already lost.
    """

    def __init__(self, fac, net, transition_prior: str = "uniform", alpha: float = 0.6):
        self.fac, self.net = fac, net
        self.prior = transition_prior
        self.alpha = alpha
        n = len(fac.rooms)
        self.b = {r: 1.0 / n for r in fac.rooms}
        self.counts = defaultdict(lambda: defaultdict(float))
        self.track: list[int] = []

    # ---------- transition model ----------
    def _trans(self, r: int) -> dict[int, float]:
        cands = self.fac.neighbors(r) + [r]
        if self.prior == "learned":
            row = self.counts[r]
            tot = sum(row.get(c, 0.0) for c in cands) + self.alpha * len(cands)
            return {c: (row.get(c, 0.0) + self.alpha) / tot for c in cands}
        p = 1.0 / len(cands)
        return {c: p for c in cands}

    # ---------- the filter ----------
    def step(self, event):
        nb = {r: 0.0 for r in self.fac.rooms}
        for r, w in self.b.items():
            if w <= 0:
                continue
            for c, p in self._trans(r).items():
                if event is None:
                    # nothing tripped: they stayed, or used an unwired door
                    if c != r and self.net.is_wired(r, c):
                        continue
                else:
                    # this door opened: only crossings of that door are possible
                    if c == r or ekey(r, c) != event:
                        continue
                nb[c] += w * p
        z = sum(nb.values())
        if z <= 0:                      # evidence contradicts the belief: restart it
            n = len(self.fac.rooms)
            nb = {r: 1.0 / n for r in self.fac.rooms}
            z = 1.0
        self.b = {r: v / z for r, v in nb.items()}

        m = self.map_room()
        if self.track and self.prior == "learned":
            self.counts[self.track[-1]][m] += 1.0
        self.track.append(m)

    def saw(self, room: int):
        """Direct sighting -- co-location collapses the belief to certainty."""
        self.b = {r: (1.0 if r == room else 0.0) for r in self.fac.rooms}

    # ---------- queries ----------
    def map_room(self) -> int:
        return max(self.b.items(), key=lambda kv: kv[1])[0]

    def confidence(self) -> float:
        return max(self.b.values())

    def entropy(self) -> float:
        import math
        return -sum(p * math.log(p, 2) for p in self.b.values() if p > 0)
