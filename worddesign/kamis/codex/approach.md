# KaMIS DNA-8 Campaign Log

## Goal
- Run KaMIS on `test/dna_word_graph_8.metis` with long enough runtime to reach size `136`.
- Use `12` cores in parallel.
- Keep all new run outputs, analysis artifacts, and plots under `KaMIS/codex`.

## Current Plan
- Batch-run `redumis` with seeds starting at `100`.
- Include both `full_standard` and `full_social` configs.
- Use long time limit (`50000`) and existing kernel settings (`full`, `red_thres=5000`).
- Generate CSV summaries and scatter plots from solution files.

## Step Log
### 2026-02-25 20:09:19 UTC
- Created `codex/` workspace structure for runs, scripts, analysis, and plots.
- Confirmed `gnu parallel` exists locally for 12-core batch execution.
- Verified Python plotting stack (`numpy`/`matplotlib`) is unavailable and cannot be installed due restricted network.
- Switched plotting implementation to local `Rscript` (available) to still produce scatter plots.


### 2026-02-25 20:12:37 UTC
- Analysis+plot run complete for `legacy_redumis` with target size `136`.
- Metrics: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/solution_metrics.csv`.
- Summary: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/summary.txt`.
- Plots: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/plots`.

### 2026-02-25 20:12:48 UTC
- Analysis+plot run complete for `legacy_online` with target size `136`.
- Metrics: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/solution_metrics.csv`.
- Summary: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/summary.txt`.
- Plots: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/plots`.

### 2026-02-25 20:12:59 UTC
- Started run `20260225_201253_seed100_cfgstdsocial_t50000_j12`.
- Settings: configs=`full_standard full_social`, seed_start=`100`, seed_count=`12`, jobs=`12`, time_limit=`50000`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_201253_seed100_cfgstdsocial_t50000_j12`.

### 2026-02-25 20:13:59 UTC
- Started run `debug_run`.
- Settings: configs=`full_standard`, seed_start=`100`, seed_count=`1`, jobs=`1`, time_limit=`1`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/debug_run`.

### 2026-02-25 20:15:46 UTC
- Started run `20260225_211610_seed100_cfgstdsocial_t50000_j12`.
- Settings: configs=`full_standard full_social`, seed_start=`100`, seed_count=`12`, jobs=`12`, time_limit=`50000`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_211610_seed100_cfgstdsocial_t50000_j12`.

### 2026-02-25 20:16:44 UTC
- Started run `debug_dual`.
- Settings: configs=`full_standard full_social`, seed_start=`100`, seed_count=`1`, jobs=`2`, time_limit=`1`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/debug_dual`.

### 2026-02-25 21:17:00 UTC
- Removed FunSearch-specific marker overlays from scatter plotting script per request.
- Plots now focus only on KaMIS solution distributions and multiplicities.

### 2026-02-25 20:17:36 UTC
- Analysis+plot run complete for `legacy_online` with target size `136`.
- Metrics: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/solution_metrics.csv`.
- Summary: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/summary.txt`.
- Plots: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_online/plots`.

### 2026-02-25 20:17:38 UTC
- Analysis+plot run complete for `legacy_redumis` with target size `136`.
- Metrics: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/solution_metrics.csv`.
- Summary: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/summary.txt`.
- Plots: `/home/vandriel/Documents/GitHub/KaMIS/codex/analysis/legacy_redumis/plots`.

### 2026-02-25 20:17:46 UTC
- Started run `20260225_211820_seed100_cfgstdsocial_t50000_j12_main`.
- Settings: configs=`full_standard full_social`, seed_start=`100`, seed_count=`12`, jobs=`12`, time_limit=`50000`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_211820_seed100_cfgstdsocial_t50000_j12_main`.

### 2026-02-25 21:19:00 UTC
- Feasibility check for requested `2 x 400` seeds under 48 hours with 12 cores:
  - Total runs = `800`.
  - Required average runtime per run to finish in 48h: `48*3600*12/800 = 2592s` (~43.2 min).
  - Historical `test/results8` indicates first 136 appears at ~`10004s`; none below `7200s`.
  - Therefore, `800` runs with current quality target (hitting 136) is not feasible within 48h on 12 cores.

### 2026-02-25 20:49:27 UTC
- Started run `20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main`.
- Settings: configs=`full_standard full_social`, seed_start=`100`, seed_count=`12`, jobs=`12`, time_limit=`50000`, target_size=`136`.
- Artifacts: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main`.

### 2026-02-25 21:49:30 UTC
- Implemented `--target_size` early-stop mechanism in `redumis`.
- Rebuilt binaries via `compile_withcmake.sh`.
- Smoke tested target argument on `examples/simple.graph` with `--target_size=1`; run completed successfully and printed `Target size` in configuration.
- Started new 12-core campaign with target stop at 136:
  - Run ID: `20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main`
  - Configs: `full_standard full_social`
  - Seeds: `100..111` per config
  - Time limit: `50000`
  - Target size: `136`

### 2026-02-25 23:24:23 UTC
- Started campaign driver `20260225_232423_campaign_seed112_to_499`.
- Auto-continue seeds from `112` to `499` with chunk size `12`.
- Settings: configs=`full_standard full_social`, jobs=`12`, time_limit=`50000`, target_size=`136`, max_wallclock_hours=`48`.

### 2026-02-26 08:21:58 UTC
- Analysis+plot run complete for `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main` with target size `136`.
- Metrics: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main/analysis/solution_metrics.csv`.
- Summary: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main/analysis/summary.txt`.
- Plots: `/home/vandriel/Documents/GitHub/KaMIS/codex/runs/20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main/analysis/plots`.

### 2026-02-26 10:37:43 UTC
- Started stream campaign `20260226_103743_campaign_stream_seed100_to_499`.
- Scheduler mode: continuous queue (no chunk barriers).
- Jobs prepared: `780`, skipped pre-solved: `20`.
- Settings: configs=`full_standard full_social`, seeds=`100..499`, jobs=`12`, time_limit=`50000`, target_size=`136`, max_wallclock_hours=`48`.

### 2026-02-26 10:38:40 UTC
- Observed old campaign `20260225_232423_campaign_seed112_to_499` stuck in barrier loop: `Waiting for existing redumis jobs to finish before launching seed 112...`.
- Stopped stale barrier-based campaign and previous seed100..111 batch workers.
- Relaunched seed campaign with stream scheduler (continuous refill) and skip-resume:
  - Campaign ID: `20260226_103743_campaign_stream_seed100_to_499`
  - Seeds: `100..499`, configs: `full_standard full_social`, jobs: `12`
  - Target size: `136`, time limit: `50000`, wallclock cap: `48h`
  - Pre-solved skip source: `20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main` (20 solved files).

### 2026-02-26 11:47:30 UTC
- Analyzed finished `redumis` logfiles across:
  - `20260225_214900_seed100_cfgstdsocial_t50000_target136_j12_main`
  - `20260226_103743_campaign_stream_seed100_to_499` (currently finished subset)
- Wrote consolidated metrics and summary:
  - `codex/analysis/finished_runs_log_analysis/finished_runs_metrics.csv`
  - `codex/analysis/finished_runs_log_analysis/summary.txt`
- Key finding so far: all successful 136 runs are finalized by `Combine reduction`; the immediately preceding successful operator is usually `Vertex cover` for `full_standard`, and split between `Vertex cover`/`Multiway` for `full_social`.
- Added narrative interpretation at `codex/analysis/finished_runs_log_analysis/interpretation.md` summarizing successful KaMIS mechanism from finished logs.

### 2026-02-26 18:53:46 UTC
- Analysis+plot run complete for `codex/runs/20260226_103743_campaign_stream_seed100_to_499` with target size `136`.
- Metrics: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/solution_metrics.csv`.
- Summary: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/summary.txt`.
- Plots: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots`.

### 2026-02-26 19:53:30 UTC
- Refreshed analysis and scatter plots for active stream campaign `20260226_103743_campaign_stream_seed100_to_499`.
- Current completed outputs analyzed: `20` (all size `136`).
- Config breakdown in completed outputs: `full_standard=20`, `full_social=0`.
- Updated plots:
  - `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_min_sum_size_ge_136.png`
  - `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_136_style_size_ge_136.png`

### 2026-02-26 19:03:32 UTC
- Analysis+plot run complete for `codex/runs/20260226_103743_campaign_stream_seed100_to_499` with target size `136`.
- Metrics: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/solution_metrics.csv`.
- Summary: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/summary.txt`.
- Plots: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots`.
- Fingerprint overlay source: `/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv`.

### 2026-02-26 20:02:20 UTC
- Updated plotting pipeline to support fingerprint overlay crosses from external CSV.
- `codex/scripts/plot_scatter.R` now accepts optional fingerprint CSV with either:
  - columns `A,C,G,T` (auto symmetry reduction to `(count_min1,count_min2)`), or
  - columns `count_min1,count_min2` directly.
- `codex/scripts/analyze_and_plot.sh` now accepts optional third argument `fingerprint_csv` and forwards it.
- Regenerated stream-campaign plots using:
  - `/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv`
- Overlay result: `2` fingerprint class points shown as black crosses.

### 2026-02-26 19:08:15 UTC
- Analysis+plot run complete for `codex/runs/20260226_103743_campaign_stream_seed100_to_499` with target size `136`.
- Metrics: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/solution_metrics.csv`.
- Summary: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/summary.txt`.
- Plots: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots`.
- Fingerprint overlay source: `/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv`.

### 2026-02-26 20:06:40 UTC
- Restyled scatter plotting for better legibility (closer to reference matplotlib style):
  - larger filled markers and multiplicity labels,
  - thicker fingerprint crosses,
  - gray panel background and clearer grid,
  - continuous viridis-style colorbar,
  - larger axis/title text.
- Re-ran plot generation for `20260226_103743_campaign_stream_seed100_to_499` with fingerprint overlay.

### 2026-02-27 10:43:06 UTC
- Analysis+plot run complete for `codex/runs/20260226_103743_campaign_stream_seed100_to_499` with target size `136`.
- Metrics: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/solution_metrics.csv`.
- Summary: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/summary.txt`.
- Plots: `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots`.
- Fingerprint overlay source: `/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv`.

### 2026-02-27 11:44:30 UTC
- Status refresh for active stream campaign `20260226_103743_campaign_stream_seed100_to_499`.
- Re-ran analysis+plots with fingerprint overlay.
- Current finished outputs: `77` (all `full_standard`), active workers: `12`, queued remaining: `703` out of `780` total jobs.
- Updated plots:
  - `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_min_sum_size_ge_136.png`
  - `codex/runs/20260226_103743_campaign_stream_seed100_to_499/analysis/plots/scatter_136_style_size_ge_136.png`
