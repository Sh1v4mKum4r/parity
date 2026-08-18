# PARITY

**An Adaptive Horror Game Driven by Online Player-Trajectory Prediction**

A horror antagonist that builds a live behavioural model of *you* and acts on its
predictions — intercepting where you are going rather than chasing where you are,
and quietly degrading the information you have come to depend on.

## Review deliverables

| File | What it is |
|---|---|
| `docs/PARITY-review-deck.pptx` | 22-slide review deck, structured to the marking rubric |
| `docs/PARITY-project-report.pdf` | Full project report with figures and 22 references |
| `docs/PARITY-project-report.md` | Same report, source form |
| `demo/parity-demo.html` | **Playable demo — open in any browser, no server, no internet** |
| `out/*.png` | Result figures and architecture diagram |
| `out/metrics.json` | Raw numbers behind every figure |

Open the demo hands-free with `demo/parity-demo.html?auto=1` — a scripted habitual
player drives it while the model learns on screen.

## Running the model

```
python3 model/evaluate.py        # runs all four experiments, writes out/metrics.json
python3 model/make_figures.py    # regenerates the result figures
python3 model/make_arch.py       # regenerates the architecture diagram
python3 model/make_deck.py       # rebuilds the PPTX from current metrics
```

No dependencies beyond `numpy`, `matplotlib`, and `python-pptx`.

## Module layout

```
model/
  facility.py     room graph, mutation ops, connectivity invariants
  bots.py         scripted players: habitual, explorer, random (the control)
  predictors.py   UniformNeighbour · MarkovOrder1 · VOMM (proposed)
  director.py     turns beliefs into counter-moves; confidence-gated
  test_invariants.py  9 safety and fairness invariants
  evaluate.py     four experiments, all seeded and prequential
```

## Results

Prediction accuracy (top-1 next room, 10 rooms, 1200 steps x 12 seeds):

| Player | No model | Order-1 Markov | **VOMM** |
|---|---|---|---|
| Habitual | 30.6% | 46.2% | **61.1%** |
| Explorer | 31.2% | 53.0% | **69.6%** |
| Evasive *(waits on purpose)* | 26.4% | 45.6% | **55.7%** |
| Random *(control)* | 26.9% | 25.9% | **26.7%** |

The control is the important row: against a random player the model performs
identically to no model at all, which is what a correctly implemented predictor
must do.

Embodied pursuit — an entity that occupies a room and moves one room per step:

| Entity behaviour | Captures / 1000 moves |
|---|---|
| Random walk *(control)* | 108 |
| Camp the busiest junction | 261 |
| Order-1 Markov director | 310 |
| VOMM, one-step targeting | 317 |
| VOMM interceptor (5-step lookahead) | 302 |

Every model-driven antagonist beats the non-learning baselines, but the models sit
within noise of each other, and five-step lookahead is now slightly *worse* than
one-step: at 61% single-step accuracy, rollout error compounds faster than the
extra foresight pays. The advantage over hub-camping widens with facility size —
1.30x at 10 rooms, 1.57x at 32 — so the small-facility number understates it.

World editing, with the entity removed so topology mutation is isolated:

| Condition | Moves per objective lap |
|---|---|
| Facility left alone | 15.7 |
| **Director sealing and rewiring ahead** | **25.2** (60% more) |

Targeted sabotage is a **conditional** result: it gives no advantage over random
targeting when the player relies on every room equally, and an 12% advantage when
their reliance is uneven. Reported as such in the report, section 5.5.

**Waiting does not defend (a negative result).** An evasive player who declines 35%
of windows costs the model 4.7 points of accuracy but reduces their capture risk
by only 1.7%. The antagonist currently observes position perfectly, so standing
still cannot conceal — it only parks you. Next milestone is door motion-sensors and
partial observation, which is what this experiment identified.

**Dwell is learned, not assumed.** How long a player lingers is behaviour, and the
model picks it up: predicting "will they decline this window?" it scores
70% against a 54% majority-class baseline — 100% in rooms with nothing to
record, 67% in rooms holding a codebook. An explicit dwell model adds nothing
on top: once staying is a legal action the sequence model already represents it.

## Verification

```
python3 model/test_invariants.py     # 9 invariants, 25 generated facilities
```

Covers connectivity under mutation, objective reachability (no soft-locks),
distribution well-formedness, absence of leakage on a random player, and both
Director fairness rules.

## Status

M0–M2 complete (simulation core, predictor, director). M3 next: the Godot
first-person vertical slice with a live prediction overlay.
