"""Facility: the room graph that PARITY is played on.

Pure data, no rendering. The 3D level is built *from* this structure,
never the reverse. Rooms are nodes; doors are undirected edges.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class Room:
    rid: int
    glyph: str
    neighbors: list[int] = field(default_factory=list)
    has_table: bool = False      # holds a lookup table (keyword -> bits)
    has_terminal: bool = False   # holds an inbound bit sequence to decode
    is_comms: bool = False       # outbound register lives here


class Facility:
    """Connected room graph with runtime mutation ops."""

    def __init__(self, n_rooms: int = 10, seed: int = 0, extra_edge_p: float = 0.35):
        self.rng = random.Random(seed)
        self.n = n_rooms
        self.rooms: dict[int, Room] = {
            i: Room(i, GLYPHS[i % 26]) for i in range(n_rooms)
        }
        self._build_graph(extra_edge_p)
        self._place_features()

    # ---------- construction ----------

    def _build_graph(self, extra_edge_p: float) -> None:
        # random spanning tree guarantees connectivity
        order = list(range(self.n))
        self.rng.shuffle(order)
        for i in range(1, len(order)):
            a = order[i]
            b = order[self.rng.randrange(i)]
            self._link(a, b)
        # a few extra edges so the graph has loops (routes become choices)
        for a in range(self.n):
            for b in range(a + 1, self.n):
                if b not in self.rooms[a].neighbors and self.rng.random() < extra_edge_p / self.n * 4:
                    self._link(a, b)

    def _place_features(self) -> None:
        ids = list(self.rooms)
        self.rng.shuffle(ids)
        self.comms_room = ids[0]
        self.rooms[self.comms_room].is_comms = True
        for r in ids[1:1 + max(3, self.n // 3)]:
            self.rooms[r].has_table = True
        for r in ids[1 + max(3, self.n // 3):1 + 2 * max(3, self.n // 3)]:
            self.rooms[r].has_terminal = True

    def _link(self, a: int, b: int) -> None:
        if b not in self.rooms[a].neighbors:
            self.rooms[a].neighbors.append(b)
            self.rooms[b].neighbors.append(a)

    def _unlink(self, a: int, b: int) -> None:
        if b in self.rooms[a].neighbors:
            self.rooms[a].neighbors.remove(b)
            self.rooms[b].neighbors.remove(a)

    # ---------- queries ----------

    def neighbors(self, rid: int) -> list[int]:
        return list(self.rooms[rid].neighbors)

    def is_connected(self) -> bool:
        seen, stack = {0}, [0]
        while stack:
            for nb in self.rooms[stack.pop()].neighbors:
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return len(seen) == self.n

    def reachable(self, src: int, dst: int) -> bool:
        seen, stack = {src}, [src]
        while stack:
            cur = stack.pop()
            if cur == dst:
                return True
            for nb in self.rooms[cur].neighbors:
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False

    # ---------- mutation (only Sabotage may call these) ----------

    def rewire(self, a: int, b: int, new_b: int) -> bool:
        """Move the door a<->b to a<->new_b. Reverts if it breaks solvability."""
        if b not in self.rooms[a].neighbors or new_b in self.rooms[a].neighbors or new_b == a:
            return False
        self._unlink(a, b)
        self._link(a, new_b)
        if not self.is_connected():
            self._unlink(a, new_b)
            self._link(a, b)
            return False
        return True

    def seal_door(self, a: int, b: int) -> bool:
        """Remove a door. Reverts if it disconnects the facility."""
        if b not in self.rooms[a].neighbors:
            return False
        self._unlink(a, b)
        if not self.is_connected():
            self._link(a, b)
            return False
        return True
