# score136

Curated package for the `n=8` DNA word-design search work around the best known feasible set size `136`.

This folder is a cleaned export from local experiments. Original desktop folders/runs are unchanged.

## What Is Included

- `scripts/optuna_136_GPT.py`
  - Main search/evaluation script used for the latest runs.
  - Enforces hard constraints, including self reverse-complement (`x` vs `xRC`) with distance `>= 4`.
  - Generates parameter-pair plots and A/C (plus orbit-class) fingerprint outputs.
- `scripts/heuristic_136.py`
  - Earlier heuristic baseline script used as starting point.
- `results/run_refined5_12h_2026-02-26/`
  - 12-hour Optuna run outputs (summary, best subset, parameter plots, sampled fingerprint).
- `results/run_refined4_2h_2026-02-25_allrows/`
  - 2-hour run with full-row (`sample_size=0`) fingerprint recomputation.
- `results/class_overview.csv`
  - Compact class totals for the shipped runs.

## Constraints Enforced

For `n=8`, `d=n/2=4`, each accepted set must satisfy:

- Exact GC balance per word: `#(C or G) == 4`
- Distinct-word Hamming: `HD(x,y) >= 4` for all `x != y`
- Distinct-word reverse-complement distance: `HD(x,yRC) >= 4` for all `x != y`
- Self reverse-complement distance: `HD(x,xRC) >= 4` for all `x`

## Class Interpretation

The fingerprint pipeline stores:

- **Hash classes**: exact subset identity (canonical hash).
- **Orbit classes**: hash classes merged under complement-preserving base relabeling symmetry.

For the shipped runs, feasible `136` outcomes collapse to **2 orbit classes** (`A` and `B`), even when multiple hash classes appear.

## Reproduce

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run a long search:

```bash
python scripts/optuna_136_GPT.py \
  --trials 5000000 \
  --time-budget-hours 12 \
  --workers 8 \
  --batch-size 8 \
  --plot-focus-params 8 \
  --plot-max-pairs 24 \
  --ac-fingerprint-sample 600 \
  --out-dir results/new_run_12h
```

Notes:

- `--ac-fingerprint-sample 0` means fingerprint all feasible best-length rows.
- `--ac-fingerprint-sample -1` disables fingerprinting.
- `rev_min`/`comp_min` are discrete because they are integer thresholds applied to integer position-difference counts.

