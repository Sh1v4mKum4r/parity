"""Offline evaluation of the PARITY predictor.

Three experiments, all headless, all seeded:

  E1  Prequential next-room accuracy, every predictor x every player type.
      The control matters as much as the result: against RandomBot the model
      must NOT beat baseline. If it does, something is leaking.
  E2  Learning curve -- accuracy against elapsed steps, showing online learning.
  E3  Capture rate -- does better prediction actually make the game harder?
      Compared against a no-model control AND a strong non-learning heuristic.
"""
from __future__ import annotations
import json, random, sys, statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from facility import Facility
from bots import HabitualBot, ExplorerBot, RandomBot
from predictors import UniformNeighbour, MarkovOrder1, VOMM
from director import ModelDirector, RandomAmbush, DegreeCamp, FullDirector, InterceptDirector

BOTS = {"habitual": HabitualBot, "explorer": ExplorerBot, "random": RandomBot}
STEPS, SEEDS, CTX = 1200, 12, 8


def _make_model(kind):
    return {"uniform": UniformNeighbour, "markov-1": MarkovOrder1, "vomm": VOMM}[kind]()


def _top_k(dist, k):
    return [r for r, _ in sorted(dist.items(), key=lambda kv: -kv[1])[:k]]


def e1_accuracy():
    """Prequential (predict-then-observe) accuracy. No train/test leak by
    construction: every prediction is made before its outcome is seen."""
    out = {}
    for bot_name, BotCls in BOTS.items():
        for kind in ("uniform", "markov-1", "vomm"):
            t1, t3 = [], []
            for seed in range(SEEDS):
                fac = Facility(10, seed=seed)
                bot = BotCls(fac, seed=seed + 100)
                model = _make_model(kind)
                hist, hits1, hits3, n = [bot.pos], 0, 0, 0
                for _ in range(STEPS):
                    cur = hist[-1]
                    cands = fac.neighbors(cur)
                    if not cands:
                        break
                    dist = model.predict(hist[-CTX:], cands)
                    actual = bot.step()
                    bot.resync(actual)
                    if actual in cands:
                        n += 1
                        if _top_k(dist, 1) and _top_k(dist, 1)[0] == actual:
                            hits1 += 1
                        if actual in _top_k(dist, 3):
                            hits3 += 1
                    model.observe(hist[-CTX:], actual)
                    hist.append(actual)
                if n:
                    t1.append(hits1 / n)
                    t3.append(hits3 / n)
            out[f"{bot_name}|{kind}"] = {
                "top1": statistics.mean(t1), "top1_sd": statistics.pstdev(t1),
                "top3": statistics.mean(t3), "n_seeds": len(t1),
            }
    return out


def e2_learning_curve(bot_name="habitual", window=20):
    curves = {}
    for kind in ("uniform", "markov-1", "vomm"):
        per_seed = []
        for seed in range(SEEDS):
            fac = Facility(10, seed=seed)
            bot = BOTS[bot_name](fac, seed=seed + 100)
            model = _make_model(kind)
            hist, marks = [bot.pos], []
            for _ in range(STEPS):
                cands = fac.neighbors(hist[-1])
                if not cands:
                    break
                dist = model.predict(hist[-CTX:], cands)
                actual = bot.step()
                bot.resync(actual)
                marks.append(1.0 if (_top_k(dist, 1) and _top_k(dist, 1)[0] == actual) else 0.0)
                model.observe(hist[-CTX:], actual)
                hist.append(actual)
            per_seed.append([statistics.mean(marks[i:i + window])
                             for i in range(0, len(marks) - window, window)])
        L = min(len(p) for p in per_seed)
        curves[kind] = [statistics.mean(p[i] for p in per_seed) for i in range(L)]
    return {"window": window, "curves": curves}


def e3_capture(bot_name="habitual"):
    """The game-level test: an entity that ambushes where the model points,
    versus no model and versus 'camp the busiest junction'."""
    out = {}
    for label in ("random", "hub-camp", "markov-1", "vomm"):
        rates = []
        for seed in range(SEEDS):
            fac = Facility(10, seed=seed)
            bot = BOTS[bot_name](fac, seed=seed + 100)
            if label == "random":
                d = RandomAmbush(fac.rooms, seed=seed)
            elif label == "hub-camp":
                d = DegreeCamp(fac)
            else:
                d = ModelDirector(_make_model(label))
            hist, caught, n = [bot.pos], 0, 0
            rng = random.Random(seed + 7)
            for _ in range(STEPS):
                cands = fac.neighbors(hist[-1])
                if not cands:
                    break
                ambush = d.choose_ambush(hist[-CTX:], cands)
                actual = bot.step()
                bot.resync(actual)
                n += 1
                if actual == ambush:
                    caught += 1
                    actual = rng.choice(list(fac.rooms))   # respawn after a catch
                    bot.resync(actual)
                if hasattr(d, "model"):
                    d.model.observe(hist[-CTX:], actual)
                hist.append(actual)
            rates.append(1000.0 * caught / n)
        out[label] = {"per_1000": statistics.mean(rates), "sd": statistics.pstdev(rates)}
    return out



def e4_pursuit(bot_name="habitual"):
    """The honest version of E3: the entity is a body, not a teleport.

    It occupies a room, moves one room per step, and must INTERCEPT -- so it
    has to be right about where the player is going, not merely where they are.
    Capture rates here are far lower and far more meaningful than E3's
    idealised placement.
    """
    from bots import _bfs_path
    out = {}
    for label in ("random-walk", "hub-camp", "markov-1", "vomm", "vomm-intercept"):
        rates = []
        for seed in range(SEEDS):
            fac = Facility(10, seed=seed)
            bot = BOTS[bot_name](fac, seed=seed + 100)
            rng = random.Random(seed + 31)
            model = _make_model("vomm" if label == "vomm-intercept" else label) \
                if label in ("markov-1", "vomm", "vomm-intercept") else None
            icept = InterceptDirector(model, fac) if label == "vomm-intercept" else None
            hub = max(fac.rooms, key=lambda r: len(fac.neighbors(r)))
            epos = rng.choice(list(fac.rooms))
            hist, caught, n = [bot.pos], 0, 0
            for _ in range(STEPS):
                cands = fac.neighbors(hist[-1])
                if not cands:
                    break
                if label == "random-walk":
                    target = rng.choice(fac.neighbors(epos)) if fac.neighbors(epos) else epos
                elif label == "hub-camp":
                    target = hub
                elif icept is not None:
                    target = icept.choose_target(hist[-CTX:], hist[-1], epos) or epos
                else:
                    dist = model.predict(hist[-CTX:], cands)
                    target = max(dist.items(), key=lambda kv: kv[1])[0]
                path = _bfs_path(fac, epos, target)
                epos = path[1] if len(path) > 1 else epos

                actual = bot.step()
                bot.resync(actual)
                n += 1
                if actual == epos:
                    caught += 1
                    actual = rng.choice(list(fac.rooms))
                    bot.resync(actual)
                    epos = rng.choice(list(fac.rooms))
                if model is not None:
                    model.observe(hist[-CTX:], actual)
                hist.append(actual)
            rates.append(1000.0 * caught / n)
        out[label] = {"per_1000": statistics.mean(rates), "sd": statistics.pstdev(rates)}
    return out



def e5_disruption(bot_name="habitual", steps=1500):
    """Do the world-editing counter-moves impose a real cost?

    No entity here -- this isolates topology mutation from interception. The bot
    cycles objective rooms; we measure how many moves an objective lap costs when
    the Director is sealing and rewiring ahead of it versus when the facility is
    left alone. Same seeds, same bot, only the Director differs.
    """
    out = {}
    for label in ("no-director", "full-director"):
        cost, acts = [], {"seal": 0, "rewire": 0, "poison": 0}
        for seed in range(SEEDS):
            fac = Facility(10, seed=seed)
            bot = BOTS[bot_name](fac, seed=seed + 100)
            tables = [r for r in fac.rooms if fac.rooms[r].has_table]
            d = FullDirector(VOMM(), fac) if label == "full-director" else None
            hist = [bot.pos]
            for t in range(steps):
                prev = hist[-1]
                nxt = bot.step(); bot.resync(nxt)
                if d is not None:
                    d.model.observe(hist[-CTX:], nxt)
                    d.observe_move(prev, nxt)
                    d.maybe_edit(t, hist[-CTX:], nxt, recorded=tables)
                hist.append(nxt)
            if bot.laps:
                cost.append(steps / bot.laps)
            if d is not None:
                for e in d.log:
                    acts[e["action"]] = acts.get(e["action"], 0) + 1
        out[label] = {"moves_per_lap": statistics.mean(cost),
                      "sd": statistics.pstdev(cost),
                      "actions": acts}
    base = out["no-director"]["moves_per_lap"]
    out["full-director"]["overhead_pct"] = 100.0 * (out["full-director"]["moves_per_lap"] / base - 1)
    return out


def e6_sabotage_precision(bot_name="habitual", steps=1500, cap=80, skew=False):
    """Is sabotage AIMED, or is it noise?

    A poisoned codebook only costs the player if they return to it, and it costs
    them SOONER the better it was chosen. Binary hit-rate saturates on a small
    facility (the bot eventually revisits everything), so we measure how many moves
    elapse before the player walks back into the poisoned room. Lower is a
    better-aimed sabotage. Control: poison a recorded room chosen at random.
    """
    out = {}
    for label in ("random-target", "model-target"):
        delays = []
        for seed in range(SEEDS):
            fac = Facility(10, seed=seed)
            bot = BOTS[bot_name](fac, seed=seed + 100, skew=skew) if skew else BOTS[bot_name](fac, seed=seed + 100)
            tables = [r for r in fac.rooms if fac.rooms[r].has_table]
            d = FullDirector(VOMM(), fac)
            rng = random.Random(seed + 77)
            hist, shots = [bot.pos], []
            for t in range(steps):
                prev = hist[-1]
                nxt = bot.step(); bot.resync(nxt)
                d.model.observe(hist[-CTX:], nxt); d.observe_move(prev, nxt)
                hist.append(nxt)
                for sh in shots:
                    if sh["delay"] is None:
                        if nxt == sh["room"]:
                            sh["delay"] = t - sh["t"]
                        elif t - sh["t"] >= cap:
                            sh["delay"] = cap
                if t % 40 == 0 and t > 60:
                    vis = d.visible(nxt)
                    pool = [r for r in tables if r not in vis]
                    if not pool:
                        continue
                    if label == "random-target":
                        room = rng.choice(pool)
                    else:
                        # the room this player leans on most -- highest visit count,
                        # broken by how soon the model expects them back
                        room = max(pool, key=lambda r: d.room_counts.get(r, 0))
                    shots.append({"t": t, "room": room, "delay": None})
            done = [sh["delay"] for sh in shots if sh["delay"] is not None]
            if done:
                delays.append(statistics.mean(done))
        out[label] = {"moves_until_revisit": statistics.mean(delays),
                      "sd": statistics.pstdev(delays)}
    a = out["random-target"]["moves_until_revisit"]
    b = out["model-target"]["moves_until_revisit"]
    out["model-target"]["faster_pct"] = 100.0 * (1 - b / a)
    return out



def e7_scaling(sizes=(10, 16, 24, 32), seeds=8, steps=1200):
    """How does the value of prediction change with the size of the facility?

    Motivation: on a small graph with one dominant junction, "camp the busiest
    room" is a surprisingly strong strategy -- not because it is clever, but
    because the player has nowhere else to go. As the facility grows, that
    heuristic decays while a predictive interceptor should hold up. This measures
    whether that is actually true.
    """
    from bots import _bfs_path
    out = {}
    for n in sizes:
        row = {}
        for label in ("random-walk", "hub-camp", "markov-1", "vomm-intercept"):
            rates = []
            for seed in range(seeds):
                fac = Facility(n, seed=seed)
                bot = BOTS["habitual"](fac, seed=seed + 100)
                rng = random.Random(seed + 31)
                hub = max(fac.rooms, key=lambda r: len(fac.neighbors(r)))
                model = (MarkovOrder1() if label == "markov-1"
                         else VOMM() if label == "vomm-intercept" else None)
                icept = InterceptDirector(model, fac) if label == "vomm-intercept" else None
                epos = rng.choice(list(fac.rooms))
                hist, caught, cnt = [bot.pos], 0, 0
                for _ in range(steps):
                    cands = fac.neighbors(hist[-1])
                    if not cands:
                        break
                    if label == "random-walk":
                        nbs = fac.neighbors(epos)
                        target = rng.choice(nbs) if nbs else epos
                    elif label == "hub-camp":
                        target = hub
                    elif icept is not None:
                        target = icept.choose_target(hist[-CTX:], hist[-1], epos) or epos
                    else:
                        d = model.predict(hist[-CTX:], cands)
                        target = max(d.items(), key=lambda kv: kv[1])[0]
                    path = _bfs_path(fac, epos, target)
                    epos = path[1] if len(path) > 1 else epos
                    actual = bot.step(); bot.resync(actual); cnt += 1
                    if actual == epos:
                        caught += 1
                        actual = rng.choice(list(fac.rooms)); bot.resync(actual)
                        epos = rng.choice(list(fac.rooms))
                    if model is not None:
                        model.observe(hist[-CTX:], actual)
                    hist.append(actual)
                rates.append(1000.0 * caught / cnt)
            row[label] = statistics.mean(rates)
        row["advantage_vs_hub"] = row["vomm-intercept"] / row["hub-camp"]
        out[str(n)] = row
    return out


def main():
    res = {
        "config": {"rooms": 10, "steps": STEPS, "seeds": SEEDS, "context": CTX},
        "e1_accuracy": e1_accuracy(),
        "e2_learning": e2_learning_curve(),
        "e3_capture": e3_capture(),
        "e4_pursuit": e4_pursuit(),
        "e5_disruption": e5_disruption(),
        "e6_sabotage": e6_sabotage_precision(),
        "e6_sabotage_skewed": e6_sabotage_precision(skew=True),
        "e7_scaling": e7_scaling(),
    }
    out = Path(__file__).parent.parent / "out"
    out.mkdir(exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res["e1_accuracy"], indent=2))
    print("E3 idealised:", json.dumps(res["e3_capture"]))
    print("E4 embodied  :", json.dumps(res["e4_pursuit"]))
    print("E5 disruption:", json.dumps(res["e5_disruption"], indent=2))
    print("E6 uniform reliance:", json.dumps(res["e6_sabotage"]))
    print("E6 uneven reliance :", json.dumps(res["e6_sabotage_skewed"]))
    print("E7 scaling    :", json.dumps(res["e7_scaling"], indent=2))
    return res


if __name__ == "__main__":
    main()
