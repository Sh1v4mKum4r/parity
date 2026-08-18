"""Director: turns beliefs into behaviour.

Deliberately separate from the Predictor. The model outputs a distribution;
the Director decides what to *do* with it -- where to lie in wait, which door
to seal, which lookup-table row to poison. Swapping the model never re-tunes
the horror, and vice versa.
"""
from __future__ import annotations
import random


class ModelDirector:
    """Ambushes the room the model says you are most likely to enter."""

    def __init__(self, model, confidence_gate: float = 0.0):
        self.model = model
        self.gate = confidence_gate
        self.name = f"director[{model.name}]"

    def choose_ambush(self, history, candidates):
        if not candidates:
            return None
        dist = self.model.predict(history, candidates)
        room, p = max(dist.items(), key=lambda kv: kv[1])
        return room if p >= self.gate else None

    def choose_sabotage(self, history, candidates, recorded_rooms):
        """Poison what the player has already written down and is about to need.
        Not a mercy rule -- poisoning an unrecorded table disrupts nothing, so a
        utility-maximising director never wastes the move."""
        if not recorded_rooms:
            return None
        dist = self.model.predict(history, candidates)
        ranked = sorted(recorded_rooms, key=lambda r: -dist.get(r, 0.0))
        return ranked[0]


class RandomAmbush:
    """Control: no model at all."""
    name = "random"

    def __init__(self, rooms, seed: int = 0):
        self.rooms, self.rng = list(rooms), random.Random(seed)

    def choose_ambush(self, history, candidates):
        return self.rng.choice(self.rooms)


class DegreeCamp:
    """Strong non-learning heuristic: camp the busiest junction. Included
    because it is the honest baseline -- a model that cannot beat 'sit in the
    hub' has not earned its complexity."""
    name = "hub-camp"

    def __init__(self, fac):
        self.hub = max(fac.rooms, key=lambda r: len(fac.neighbors(r)))

    def choose_ambush(self, history, candidates):
        return self.hub


class FullDirector:
    """The complete counter-move set, with the fairness rules enforced in code.

    Actions: intercept · seal a shortcut · rewire a room ahead · poison a codebook.
    Each is scored by expected disruption x model confidence; the best scoring
    action that satisfies the fairness rules is applied.

    Fairness rules (enforced here, not merely documented):
      1. Nothing currently VISIBLE to the player is ever mutated.
      2. Below the confidence gate the Director does not edit the world at all --
         it falls back to conventional hunting.
      3. Every mutation is applied through Facility, which reverts any edit that
         breaks connectivity, and is recorded in self.log for replay.
    """
    name = "full"

    def __init__(self, model, fac, gate: float = 0.45, cooldown: int = 8):
        self.model, self.fac = model, fac
        self.gate, self.cooldown = gate, cooldown
        self.edge_counts: dict = {}
        self.room_counts: dict = {}
        self.last_edit = -10 ** 6
        self.log: list = []
        self.poisoned: list = []

    # ---- the Director's own telemetry ----
    def observe_move(self, a, b):
        k = (a, b) if a <= b else (b, a)
        self.edge_counts[k] = self.edge_counts.get(k, 0) + 1
        self.room_counts[b] = self.room_counts.get(b, 0) + 1

    def confidence(self, history, candidates) -> float:
        d = self.model.predict(history, candidates)
        return max(d.values()) if d else 0.0

    def choose_ambush(self, history, candidates):
        if not candidates:
            return None
        d = self.model.predict(history, candidates)
        room, p = max(d.items(), key=lambda kv: kv[1])
        return room if p >= self.gate else None

    def visible(self, player) -> set:
        return {player} | set(self.fac.neighbors(player))

    def _lookahead(self, history, player, depth=3):
        """Roll the model forward `depth` steps along its own most-likely path.

        Needed because the first predicted room is adjacent to the player and is
        therefore always visible -- rule 1 forbids editing it. Only rooms further
        along the predicted route are legal targets.
        """
        path, hist, cur = [], list(history), player
        for _ in range(depth):
            c = self.fac.neighbors(cur) + [cur]      # staying is a legal choice
            if not c:
                break
            d = self.model.predict(hist, c)
            cur = max(d.items(), key=lambda kv: kv[1])[0]
            path.append(cur)
            hist = hist + [cur]
        return path

    def maybe_edit(self, t, history, player, recorded=()):
        """Score every legal counter-move; apply the best. Returns the action or None."""
        if t - self.last_edit < self.cooldown:
            return None
        cands = self.fac.neighbors(player) + [player]
        conf = self.confidence(history, cands)
        if conf < self.gate:                       # rule 2: unsure -> hunt conventionally
            return None
        vis = self.visible(player)                 # rule 1: never touch what they can see
        options = []

        for (a, b), n in self.edge_counts.items():
            if a in vis or b in vis:
                continue
            if b in self.fac.neighbors(a):
                options.append((n * conf, "seal", (a, b)))

        path = self._lookahead(history, player)
        for a, b in zip(path, path[1:]):
            if a in vis or b in vis or b not in self.fac.neighbors(a):
                continue
            spare = [c for c in self.fac.rooms
                     if c not in vis and c != a and c not in self.fac.neighbors(a)]
            if spare:
                new_b = min(spare, key=lambda c: self.room_counts.get(c, 0))
                options.append((1.6 * self.room_counts.get(b, 0) * conf, "rewire", (a, b, new_b)))

        recent_poison = {r for tt, r in self.poisoned if t - tt < 60}
        for r in recorded:
            if r in vis or r in recent_poison:
                continue
            options.append((0.8 * self.room_counts.get(r, 0) * conf, "poison", r))

        if not options:
            return None
        score, kind, arg = max(options, key=lambda o: o[0])
        if score <= 0:
            return None

        ok = False
        if kind == "seal":
            ok = self.fac.seal_door(*arg)
        elif kind == "rewire":
            ok = self.fac.rewire(*arg)
        elif kind == "poison":
            self.poisoned.append((t, arg)); ok = True
        if not ok:
            return None
        self.last_edit = t
        self.log.append({"t": t, "action": kind, "arg": arg, "confidence": round(conf, 3)})
        return kind


class InterceptDirector:
    """Aims where the player WILL be when it can get there, not where they go next.

    A one-step director targets the room it expects the player to enter next. But
    the entity moves one room per step too, so that room is usually unreachable in
    time -- it perpetually chases a step behind. This version rolls the model
    forward k steps and picks the earliest predicted room the entity can actually
    reach no later than the player does, weighting by how confident the model is
    that the player will be there.
    """

    def __init__(self, model, fac, depth: int = 5, gate: float = 0.0):
        self.model, self.fac, self.depth, self.gate = model, fac, depth, gate
        self.name = f"intercept[{model.name}]"

    def _dist_from(self, src):
        d = {src: 0}
        q = [src]
        while q:
            cur = q.pop(0)
            for nb in self.fac.neighbors(cur):
                if nb not in d:
                    d[nb] = d[cur] + 1
                    q.append(nb)
        return d

    def predicted_path(self, history, player):
        """Roll the model forward, carrying the probability of staying on it."""
        path, hist, cur, p = [], list(history), player, 1.0
        for _ in range(self.depth):
            c = self.fac.neighbors(cur) + [cur]   # staying is a legal choice
            if not c:
                break
            d = self.model.predict(hist, c)
            nxt, pr = max(d.items(), key=lambda kv: kv[1])
            p *= pr
            cur = nxt
            path.append((cur, p))
            hist = hist + [cur]
        return path

    def choose_target(self, history, player, entity):
        path = self.predicted_path(history, player)
        if not path:
            return None
        ed = self._dist_from(entity)
        best, best_score = None, -1.0
        for step, (room, p) in enumerate(path, start=1):
            reach = ed.get(room)
            if reach is None or reach > step:
                continue                      # cannot be there in time
            score = p / step                  # sooner and likelier is better
            if score > best_score:
                best, best_score = room, score
        if best is None:
            best = max(path, key=lambda rp: rp[1])[0]
        return best if best_score >= self.gate or best_score < 0 else best
