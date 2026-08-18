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
  evaluate.py     four experiments, all seeded and prequential
```

## Results

Prediction accuracy (top-1 next room, 10 rooms, 1200 steps x 12 seeds):

| Player | No model | Order-1 Markov | **VOMM** |
|---|---|---|---|
| Habitual | 40.6% | 64.5% | **91.4%** |
| Explorer | 38.5% | 61.2% | **94.8%** |
| Random *(control)* | 36.6% | 36.4% | **36.6%** |

The control is the important row: against a random player the model performs
identically to no model at all, which is what a correctly implemented predictor
must do.

Embodied pursuit — an entity that occupies a room and moves one room per step:

| Entity behaviour | Captures / 1000 moves |
|---|---|
| Random walk *(control)* | 93 |
| Camp the busiest junction | 241 |
| Order-1 Markov director | 377 |
| **VOMM director** | **399** |

## Status

M0–M2 complete (simulation core, predictor, director). M3 next: the Godot
first-person vertical slice with a live prediction overlay.
