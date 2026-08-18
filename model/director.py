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
