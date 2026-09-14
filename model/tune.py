"""Train the predictor properly: tune it, enrich it, and validate it honestly.

Three things were wrong with how the model was fitted:

  1. alpha and k were chosen by hand (1.6 and 4) and never searched.
  2. Every number so far is prequential on the SAME facilities the model ran on.
     That is leak-free in time, but it never asked whether a configuration
     generalises to facilities it has not seen.
  3. The context was the room sequence alone, when the antagonist can also
     observe things that correlate with the player's intent.

This does a grid search on held-out facilities, compares model variants, and
reports the configuration that actually wins.
"""
from __future__ import annotations
import json, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from facility import Facility
from bots import HabitualBot, ExplorerBot, EvasiveBot, RandomBot
from predictors import VOMM, MarkovOrder1, UniformNeighbour

TRAIN_SEEDS = range(0, 14)        # facilities used to pick the configuration
TEST_SEEDS = range(14, 26)        # facilities it has never seen
STEPS, CTX = 1200, 8
BOTS = {"habitual": HabitualBot, "explorer": ExplorerBot, "evasive": EvasiveBot}


class TaggedVOMM(VOMM):
    """VOMM whose context also carries the last objective room the player touched.

    The room sequence alone cannot express 'they are on their way to the uplink'.
    The last task room they visited is observable to the antagonist and is a cheap
    proxy for intent, so it is folded into the context key.
    """
    name = "vomm+intent"

    def __init__(self, max_order=4, alpha=1.6):
        super().__init__(max_order, alpha)
        self.tag = "-"

    def _key(self, hist, o):
        return (self.tag,) + tuple(hist[len(hist) - o:]) if o else (self.tag,)

    def predict(self, history, candidates):
        if not candidates:
            return {}
        dist = {c: 1.0 / len(candidates) for c in candidates}
        for o in range(0, self.k + 1):
            if o > len(history):
                break
            ctx = self._key(history, o)
            tot = self.ctx_total.get(ctx, 0.0)
            if tot <= 0:
                continue
            row = self.counts[ctx]
            seen = sum(row.get(c, 0.0) for c in candidates)
            if seen <= 0:
                continue
            w = tot / (tot + self.alpha)
            dist = {c: w * (row.get(c, 0.0) / seen) + (1 - w) * dist[c] for c in candidates}
        z = sum(dist.values()) or 1.0
        return {c: v / z for c, v in dist.items()}

    def observe(self, history, actual):
        for o in range(0, self.k + 1):
            if o > len(history):
                break
            ctx = self._key(history, o)
            self.counts[ctx][actual] += 1.0
            self.ctx_total[ctx] += 1.0


def run(model_factory, seeds, bot_name, tagged=False):
    """Prequential accuracy: predict, then observe. Never sees its own outcome first."""
    accs = []
    for seed in seeds:
        fac = Facility(10, seed=seed)
        bot = BOTS[bot_name](fac, seed=seed + 100)
        m = model_factory()
        hist, hit, n = [bot.pos], 0, 0
        for _ in range(STEPS):
            cur = hist[-1]
            cands = fac.neighbors(cur) + [cur]
            if tagged:
                r = fac.rooms[cur]
                if r.has_table or r.has_terminal or r.is_comms:
                    m.tag = cur
            d = m.predict(hist[-CTX:], cands)
            top = max(d.items(), key=lambda kv: kv[1])[0]
            actual = bot.step(); bot.resync(actual)
            n += 1; hit += (top == actual)
            m.observe(hist[-CTX:], actual)
            hist.append(actual)
        accs.append(hit / n)
    return statistics.mean(accs)


def main():
    out = {}

    # ---- grid search on TRAIN facilities only ----
    grid = []
    for k in (1, 2, 3, 4, 5, 6):
        for alpha in (0.2, 0.6, 1.0, 1.6, 3.0, 6.0):
            score = statistics.mean(
                run(lambda k=k, a=alpha: VOMM(k, a), TRAIN_SEEDS, b)
                for b in ("habitual", "explorer")
            )
            grid.append({"k": k, "alpha": alpha, "train_acc": score})
    grid.sort(key=lambda g: -g["train_acc"])
    best = grid[0]
    out["grid"] = grid
    out["best"] = best
    print(f"best on train: k={best['k']} alpha={best['alpha']}  ({best['train_acc']*100:.1f}%)")
    print(f"hand-picked  : k=4 alpha=1.6")

    # ---- confirm on facilities never used for selection ----
    rows = {}
    for label, factory, tagged in (
        ("uniform",      lambda: UniformNeighbour(), False),
        ("markov-1",     lambda: MarkovOrder1(), False),
        ("vomm (hand)",  lambda: VOMM(4, 1.6), False),
        ("vomm (tuned)", lambda: VOMM(best["k"], best["alpha"]), False),
        ("vomm+intent",  lambda: TaggedVOMM(best["k"], best["alpha"]), True),
    ):
        rows[label] = {b: run(factory, TEST_SEEDS, b, tagged)
                       for b in ("habitual", "explorer", "evasive")}
        rows[label]["mean"] = statistics.mean(rows[label][b] for b in ("habitual", "explorer", "evasive"))
    out["held_out"] = rows

    print("\nHELD-OUT facilities (never used to choose anything)")
    print(f"{'model':14} {'habitual':>9} {'explorer':>9} {'evasive':>9} {'mean':>8}")
    for label, r in rows.items():
        print(f"{label:14} {r['habitual']*100:8.1f}% {r['explorer']*100:8.1f}% "
              f"{r['evasive']*100:8.1f}% {r['mean']*100:7.1f}%")

    # ---- the control must still hold after tuning ----
    ctrl = {}
    for label, factory in (("uniform", lambda: UniformNeighbour()),
                           ("vomm (tuned)", lambda: VOMM(best["k"], best["alpha"]))):
        accs = []
        for seed in TEST_SEEDS:
            fac = Facility(10, seed=seed)
            bot = RandomBot(fac, seed=seed + 100)
            m = factory()
            hist, hit, n = [bot.pos], 0, 0
            for _ in range(STEPS):
                cands = fac.neighbors(hist[-1]) + [hist[-1]]
                d = m.predict(hist[-CTX:], cands)
                top = max(d.items(), key=lambda kv: kv[1])[0]
                actual = bot.step(); bot.resync(actual)
                n += 1; hit += (top == actual)
                m.observe(hist[-CTX:], actual); hist.append(actual)
            accs.append(hit / n)
        ctrl[label] = statistics.mean(accs)
    out["control_random_player"] = ctrl
    print(f"\ncontrol, random player: tuned {ctrl['vomm (tuned)']*100:.1f}% "
          f"vs uniform {ctrl['uniform']*100:.1f}%  (must be equal)")

    Path(__file__).parent.parent.joinpath("out", "tuning.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
