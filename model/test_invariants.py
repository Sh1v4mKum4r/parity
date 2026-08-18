"""Invariant tests for the PARITY simulation core.

These back the safety claims made in the report. Run: python3 model/test_invariants.py
"""
from __future__ import annotations
import random, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from facility import Facility
from bots import HabitualBot, ExplorerBot, RandomBot, EvasiveBot
from predictors import VOMM, MarkovOrder1, UniformNeighbour
from director import FullDirector

SEEDS = range(25)
_results = []


def check(name):
    def deco(fn):
        try:
            fn()
            _results.append((name, True, ""))
        except AssertionError as e:
            _results.append((name, False, str(e)))
        except Exception as e:                       # noqa: BLE001
            _results.append((name, False, f"{type(e).__name__}: {e}"))
        return fn
    return deco


@check("facility is connected on construction")
def _():
    for s in SEEDS:
        f = Facility(10, seed=s)
        assert f.is_connected(), f"seed {s} generated a disconnected facility"


@check("seal_door never disconnects the facility")
def _():
    for s in SEEDS:
        f = Facility(10, seed=s)
        rng = random.Random(s)
        for _ in range(60):
            a = rng.choice(list(f.rooms))
            nbs = f.neighbors(a)
            if not nbs:
                continue
            f.seal_door(a, rng.choice(nbs))
            assert f.is_connected(), f"seed {s}: seal_door disconnected the graph"


@check("rewire never disconnects the facility")
def _():
    for s in SEEDS:
        f = Facility(10, seed=s)
        rng = random.Random(s + 1)
        for _ in range(60):
            a = rng.choice(list(f.rooms))
            nbs = f.neighbors(a)
            if not nbs:
                continue
            f.rewire(a, rng.choice(nbs), rng.choice(list(f.rooms)))
            assert f.is_connected(), f"seed {s}: rewire disconnected the graph"


@check("the objective stays reachable from every room after mutation")
def _():
    for s in SEEDS:
        f = Facility(10, seed=s)
        rng = random.Random(s + 2)
        for _ in range(40):
            a = rng.choice(list(f.rooms))
            nbs = f.neighbors(a)
            if nbs:
                f.seal_door(a, rng.choice(nbs))
        for r in f.rooms:
            assert f.reachable(r, f.comms_room), \
                f"seed {s}: uplink unreachable from room {r} -- run is soft-locked"


@check("bots move to an adjacent room or stay put")
def _():
    seen_stay = {}
    for BotCls in (HabitualBot, ExplorerBot, RandomBot, EvasiveBot):
        for s in list(SEEDS)[:10]:
            f = Facility(10, seed=s)
            bot = BotCls(f, seed=s)
            cur = bot.pos
            for _ in range(300):
                nxt = bot.step()
                assert nxt == cur or nxt in f.neighbors(cur), \
                    f"{BotCls.__name__} teleported from {cur} to {nxt}"
                seen_stay[BotCls.__name__] = seen_stay.get(BotCls.__name__, 0) + (nxt == cur)
                bot.resync(nxt); cur = nxt
    for name, n in seen_stay.items():
        assert n > 0, f"{name} never once declined a window -- staying is unexercised"


@check("predictor output is a distribution over exactly the candidate set")
def _():
    for Model in (UniformNeighbour, MarkovOrder1, VOMM):
        f = Facility(10, seed=0)
        m = Model()
        bot = HabitualBot(f, seed=0)
        hist = [bot.pos]
        for _ in range(200):
            cands = f.neighbors(hist[-1]) + [hist[-1]]
            d = m.predict(hist[-8:], cands)
            assert set(d) == set(cands), f"{Model.__name__} predicted outside the candidate set"
            assert abs(sum(d.values()) - 1.0) < 1e-9, f"{Model.__name__} distribution sums to {sum(d.values())}"
            assert all(v >= 0 for v in d.values()), f"{Model.__name__} produced a negative probability"
            nxt = bot.step(); bot.resync(nxt)
            m.observe(hist[-8:], nxt); hist.append(nxt)


@check("VOMM learns nothing from a random player (no leakage)")
def _():
    scores = {"vomm": [], "uniform": []}
    for s in list(SEEDS)[:12]:
        for key, Model in (("vomm", VOMM), ("uniform", UniformNeighbour)):
            f = Facility(10, seed=s)
            bot = RandomBot(f, seed=s + 5)
            m = Model()
            hist, hit, n = [bot.pos], 0, 0
            for _ in range(800):
                cands = f.neighbors(hist[-1]) + [hist[-1]]
                d = m.predict(hist[-8:], cands)
                top = max(d.items(), key=lambda kv: kv[1])[0]
                nxt = bot.step(); bot.resync(nxt)
                n += 1; hit += (top == nxt)
                m.observe(hist[-8:], nxt); hist.append(nxt)
            scores[key].append(hit / n)
    v, u = statistics.mean(scores["vomm"]), statistics.mean(scores["uniform"])
    assert abs(v - u) < 0.05, \
        f"VOMM scored {v:.3f} vs uniform {u:.3f} on a RANDOM player -- that is leakage"


@check("Director never mutates a room visible to the player")
def _():
    for s in list(SEEDS)[:12]:
        f = Facility(10, seed=s)
        bot = HabitualBot(f, seed=s + 3)
        d = FullDirector(VOMM(), f)
        tables = [r for r in f.rooms if f.rooms[r].has_table]
        hist = [bot.pos]
        for t in range(500):
            prev = hist[-1]
            nxt = bot.step(); bot.resync(nxt)
            d.model.observe(hist[-8:], nxt); d.observe_move(prev, nxt)
            hist.append(nxt)
            before = len(d.log)
            visible = d.visible(nxt)
            d.maybe_edit(t, hist[-8:], nxt, recorded=tables)
            if len(d.log) > before:
                entry = d.log[-1]
                touched = entry["arg"] if isinstance(entry["arg"], tuple) else (entry["arg"],)
                assert not (set(touched) & visible), \
                    f"seed {s}: {entry['action']} touched {touched}, visible to player at {nxt}"


@check("Director does not edit the world below its confidence gate")
def _():
    for s in list(SEEDS)[:12]:
        f = Facility(10, seed=s)
        bot = HabitualBot(f, seed=s + 4)
        d = FullDirector(VOMM(), f, gate=0.6)
        hist = [bot.pos]
        for t in range(400):
            prev = hist[-1]
            nxt = bot.step(); bot.resync(nxt)
            d.model.observe(hist[-8:], nxt); d.observe_move(prev, nxt)
            hist.append(nxt)
            before = len(d.log)
            # same candidate set the Director itself decides over: doors + staying
            conf = d.confidence(hist[-8:], f.neighbors(nxt) + [nxt])
            d.maybe_edit(t, hist[-8:], nxt, recorded=[])
            if len(d.log) > before:
                assert conf >= 0.6, f"seed {s}: edited the world at confidence {conf:.3f} < gate 0.6"


if __name__ == "__main__":
    width = max(len(n) for n, _, _ in _results)
    for name, ok, msg in _results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {msg}")
    failed = sum(1 for _, ok, _ in _results if not ok)
    print(f"\n{len(_results) - failed}/{len(_results)} invariants hold")
    sys.exit(1 if failed else 0)
