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


class DwellModel:
    """Learns how long a specific player lingers, and where.

    Dwell is not a nuisance parameter -- it is one of the most individual things a
    player does. Someone who copies an entire lookup table before moving behaves
    nothing like someone who grabs one row and runs, and the difference is
    learnable from their own play.

    We model it as a hazard: given the player has already declined `k` consecutive
    windows in this room, what is the probability they decline another? That gives
    an expected remaining dwell, which is what an antagonist actually needs -- not
    "where will they be next" but "how long do I have to get there".
    """
    name = "dwell"

    def __init__(self, alpha: float = 1.0, max_k: int = 6):
        self.alpha, self.max_k = alpha, max_k
        self.stay = defaultdict(float)     # (room, k) -> times they stayed again
        self.total = defaultdict(float)    # (room, k) -> times observed at that k

    def observe(self, room, k, stayed):
        key = (room, min(k, self.max_k))
        self.total[key] += 1.0
        if stayed:
            self.stay[key] += 1.0

    def hazard(self, room, k):
        """P(declines another window | already declined k here)."""
        key = (room, min(k, self.max_k))
        tot = self.total.get(key, 0.0)
        return (self.stay.get(key, 0.0) + self.alpha * 0.5) / (tot + self.alpha)

    def expected_remaining(self, room, k, horizon: int = 6) -> float:
        """Expected further windows the player stays put, from a learned hazard."""
        exp, p = 0.0, 1.0
        for i in range(horizon):
            p *= self.hazard(room, k + i)
            exp += p
        return exp

    def confidence(self, room, k) -> float:
        key = (room, min(k, self.max_k))
        n = self.total.get(key, 0.0)
        return n / (n + 4.0)


class GoalVOMM(VOMM):
    """VOMM that also infers WHICH objective the player is walking towards.

    The measured ceiling for a habitual player is about 71%; a plain VOMM reaches
    about 60%. The whole of that gap is intent: an oracle's only real advantage is
    knowing the objective the player is currently heading for, because that fixes
    their next step almost completely.

    Intent is not observable, so it is inferred. Each candidate objective carries a
    score that rises when the player moves closer to it and falls when they move
    away. The prediction is then a mixture of what the player usually does (the
    VOMM) and what someone walking to the most likely objective would do, weighted
    by how strongly the evidence favours that objective.

    MEASURED RESULT: this does not work, and is kept as a documented negative.
    On held-out facilities it scores 56.7% against the plain VOMM's 59.9%, and
    every weighting tried converges to the baseline as the mixture weight goes to
    zero -- which is the tell that the goal signal carries no information the
    sequence model does not already hold. The variable-order context already
    encodes the objective cycle: "after E you go to B" IS the intent, learned in
    counts rather than inferred from geometry.

    This is the third explicit latent-variable module to come out redundant, after
    dwell-duration modelling and intent tagging. The pattern is worth stating: on
    this problem, adding a hand-built estimator on top of the sequence model has
    never paid, because the variable-order context subsumes it.
    """
    name = "goal-vomm"

    def __init__(self, fac, max_order: int = 4, alpha: float = 1.6,
                 gain: float = 0.85, decay: float = 0.90):
        super().__init__(max_order, alpha)
        self.fac = fac
        self.goals = [r for r in fac.rooms
                      if fac.rooms[r].has_table or fac.rooms[r].has_terminal
                      or fac.rooms[r].is_comms]
        self.score = {g: 0.0 for g in self.goals}
        self.gain, self.decay = gain, decay
        self._dist_cache = {}

    def _dist(self, src):
        if src in self._dist_cache:
            return self._dist_cache[src]
        d, q = {src: 0}, [src]
        while q:
            cur = q.pop(0)
            for nb in self.fac.neighbors(cur):
                if nb not in d:
                    d[nb] = d[cur] + 1
                    q.append(nb)
        self._dist_cache[src] = d
        return d

    def note_move(self, prev, cur):
        """Evidence: did this step take them closer to each objective?"""
        dp, dc = self._dist(prev), self._dist(cur)
        for g in self.goals:
            delta = dp.get(g, 99) - dc.get(g, 99)      # +1 closer, -1 further
            self.score[g] = self.score[g] * self.decay + self.gain * delta
        if cur in self.score:
            self.score[cur] = -1.5                      # just arrived: no longer the goal

    def _goal_belief(self):
        import math
        mx = max(self.score.values()) if self.score else 0.0
        exp = {g: math.exp(self.score[g] - mx) for g in self.goals}
        z = sum(exp.values()) or 1.0
        return {g: v / z for g, v in exp.items()}

    def predict(self, history, candidates):
        base = super().predict(history, candidates)
        if not candidates or not history:
            return base
        cur = history[-1]
        gb = self._goal_belief()
        g, gp = max(gb.items(), key=lambda kv: kv[1])
        if gp < 0.30 or g == cur:
            return base
        # where would someone walking to g go from here?
        d = self._dist(cur)
        best, bd = None, 10 ** 9
        for c in candidates:
            if c == cur:
                continue
            dc = self._dist(c).get(g, 99)
            if dc < bd:
                best, bd = c, dc
        if best is None or bd >= d.get(g, 99):
            return base
        w = min(0.72, gp)                               # never fully override habit
        out = {c: (1 - w) * base[c] for c in candidates}
        out[best] += w
        z = sum(out.values()) or 1.0
        return {c: v / z for c, v in out.items()}
