"""Predictors: given the player's recent trajectory, produce a distribution
over the room they will enter next.

All three share one interface so the Director can be handed any of them:

    p = model.predict(history, candidates) -> {room: prob}
    model.observe(history, actual)

UniformNeighbour - control. No learning. 1/degree.
MarkovOrder1     - classic. P(next | current room).
VOMM             - variable-order Markov model with Witten-Bell style
                   interpolated back-off over contexts of length 0..K.
                   Learns online, from the first move, and persists.
"""
from __future__ import annotations
from collections import defaultdict


class UniformNeighbour:
    name = "uniform"
    persists = False

    def predict(self, history, candidates):
        if not candidates:
            return {}
        p = 1.0 / len(candidates)
        return {c: p for c in candidates}

    def observe(self, history, actual):
        pass


class MarkovOrder1:
    name = "markov-1"
    persists = True

    def __init__(self, alpha: float = 1.0):
        self.counts = defaultdict(lambda: defaultdict(float))
        self.alpha = alpha

    def predict(self, history, candidates):
        if not candidates:
            return {}
        ctx = history[-1] if history else None
        row = self.counts[ctx]
        tot = sum(row.get(c, 0.0) for c in candidates) + self.alpha * len(candidates)
        return {c: (row.get(c, 0.0) + self.alpha) / tot for c in candidates}

    def observe(self, history, actual):
        ctx = history[-1] if history else None
        self.counts[ctx][actual] += 1.0


class VOMM:
    """Variable-order Markov model with back-off.

    Context of order o is the last o rooms. We interpolate from the longest
    context down to uniform:

        P_o(x|ctx) = w * f_o(x|ctx) + (1-w) * P_{o-1}(x|ctx[1:])
        w         = C(ctx) / (C(ctx) + alpha)

    Long contexts dominate once they have been seen enough times, and decay
    gracefully to shorter ones when they have not. This is what lets it learn
    "at the junction, after coming from the store room, they go left" -- a
    dependency an order-1 model structurally cannot represent.
    """
    name = "vomm"
    persists = True

    def __init__(self, max_order: int = 4, alpha: float = 1.6):
        self.k = max_order
        self.alpha = alpha
        self.counts = defaultdict(lambda: defaultdict(float))  # ctx tuple -> {room: n}
        self.ctx_total = defaultdict(float)

    def predict(self, history, candidates):
        if not candidates:
            return {}
        dist = {c: 1.0 / len(candidates) for c in candidates}   # order -1: uniform
        for o in range(0, self.k + 1):
            if o > len(history):
                break
            ctx = tuple(history[len(history) - o:]) if o else ()
            tot = self.ctx_total.get(ctx, 0.0)
            if tot <= 0:
                continue
            row = self.counts[ctx]
            seen = sum(row.get(c, 0.0) for c in candidates)
            if seen <= 0:
                continue
            w = tot / (tot + self.alpha)
            emp = {c: row.get(c, 0.0) / seen for c in candidates}
            dist = {c: w * emp[c] + (1 - w) * dist[c] for c in candidates}
        z = sum(dist.values()) or 1.0
        return {c: v / z for c, v in dist.items()}

    def observe(self, history, actual):
        for o in range(0, self.k + 1):
            if o > len(history):
                break
            ctx = tuple(history[len(history) - o:]) if o else ()
            self.counts[ctx][actual] += 1.0
            self.ctx_total[ctx] += 1.0

    # --- introspection, used by the in-game overlay and the death readout ---

    def top_habit(self, min_count: float = 6.0):
        """Strongest learned rule: (context, room, probability, support)."""
        best = None
        for ctx, row in self.counts.items():
            tot = self.ctx_total[ctx]
            if tot < min_count or not ctx:
                continue
            room, n = max(row.items(), key=lambda kv: kv[1])
            p = n / tot
            if best is None or (p, tot) > (best[2], best[3]):
                best = (ctx, room, p, tot)
        return best

    def confidence(self, history, candidates) -> float:
        """Max probability mass on any single candidate -- drives how
        aggressively the Director is allowed to act."""
        d = self.predict(history, candidates)
        return max(d.values()) if d else 0.0
