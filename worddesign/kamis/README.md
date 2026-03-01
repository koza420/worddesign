# KaMIS Worddesign Artifacts

This directory contains the reproducible artifacts and code/settings used for the DNA-word graph (length 8) KaMIS runs, including:

- run logs/results/plots under `codex/`
- input graph and reference batch/post-processing files under `test/`
- source files modified for target-size early stopping and logging under `source_changes/`
- compile helper script `compile_withcmake.sh`

## Latest Campaign Snapshot

Main run folder:
`codex/runs_20260226_103743_campaign_stream_seed100_to_499`

Latest merged inventory (including backfilled legacy `results8` and `results8_online`):

- total files analyzed: `658`
- files with size `>=136`: `354`
- by method:
  - `full_standard`: `400` total, `291` at `>=136`
  - `full_social`: `58` total, `53` at `>=136`
  - `online`: `200` total, `10` at `>=136`

Key outputs:

- metrics CSV:
  `codex/runs_20260226_103743_campaign_stream_seed100_to_499/analysis/solution_metrics.csv`
- summary:
  `codex/runs_20260226_103743_campaign_stream_seed100_to_499/analysis/summary.txt`
- scatter plot (`>=136`):
  `codex/runs_20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_136_style_size_ge_136.png`
- min-sum scatter (`>=136`):
  `codex/runs_20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_min_sum_size_ge_136.png`
