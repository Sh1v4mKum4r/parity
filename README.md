# PARITY

**An Adaptive Horror Game Driven by Online Player-Trajectory Prediction**

A horror antagonist that builds a live behavioural model of *you* and acts on it —
intercepting where you are going, and quietly degrading the information you depend
on. The game is the application: the AI lives inside a playable first-person build
and explains its own reasoning on screen.

## Play it

| File | What it is |
|---|---|
| `demo/parity-3d.html` | **The game.** First person, WASD. Codebook rooms show their keyword and bits on a lit panel; `E` reads it close up, or works the uplink · `TAB` notebook · `F` cut a door sensor (its lamp above the doorway goes out) · `1`–`8` and `ENTER` stage and send the byte. Two uncorrupted signals ends the run as a win; being caught ends the run, but your notebook and its model of you both carry over. `P` toggles **step mode**: the clock stops and the entity takes one turn per room you enter. |
| `demo/parity-game.html` | **Systems view.** The same AI with its belief drawn on the map, wired vs dead doors, and a sensor you can cut. |
| `demo/parity-notebook.html` | Freehand notebook — stroke-based, Excalidraw-style erase, pages. |
| `demo/parity-room.html` | Art-direction study for the 3D layer. |

Everything runs offline in a browser. Nothing to install.

## Documents

| File | What it is |
|---|---|
| `docs/PARITY-review3-deck.pptx` | Review III deck, 26 slides, speaker notes |
| `docs/PARITY-project-report.pdf` | Full report with figures and references |
| `docs/PARITY-cheat-sheet.pdf` | Two-page cheat sheet: numbers, likely questions, demo order |

## Running the model

```
python3 model/evaluate.py         # 12 experiments -> out/metrics.json
python3 model/test_invariants.py  # 9 invariants over 25 generated facilities
python3 model/tune.py             # grid search, validated on held-out facilities
python3 model/make_figures.py     # regenerate every figure
python3 model/make_deck3.py       # rebuild the deck from metrics
```

## Headline results

Next-move prediction, held-out:

| Player | No model | Order-1 Markov | **VOMM** |
|---|---|---|---|
| Habitual | 39.1% | 60.0% | **83.6%** |
| Explorer | 31.2% | 53.0% | **69.6%** |
| Random *(control)* | 26.9% | 25.9% | **26.7%** |

The control is the important row: against a random player the model performs
identically to no model, so the gains are learned habit rather than leakage.

**How well trained.** An oracle that sees the player's internal state reaches
91.8%; the model reaches 89.0% from behaviour alone — 97% of the
achievable signal, and 100% against a perfectly consistent player.

**Counter-play.** Waiting is catastrophic (+439% at full sensor coverage).
Spending dangerous tasks to kill sensors on your own route cuts risk
-21% at 60% coverage, but backfires at full coverage. The counter-play
has a sweet spot.

## Status

The complete core loop is playable in first person. What remains is the Godot port,
audio and content — presentation rather than mechanism. The open problems are
predicting *when* the player stops to write, and replacing scripted players with
human playtest traces.
