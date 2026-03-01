#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/vandriel/Documents/GitHub/KaMIS
run_dir="$ROOT/codex/runs/20260226_103743_campaign_stream_seed100_to_499"
fingerprint_csv="/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv"
seeds=(234 235 236)

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] watcher started for standard seeds: ${seeds[*]}"
while true; do
  missing=0
  for s in "${seeds[@]}"; do
    f="$run_dir/results/full_standard_seed${s}.txt"
    if [[ ! -f "$f" ]]; then
      missing=1
      break
    fi
  done
  if [[ "$missing" -eq 0 ]]; then
    break
  fi
  sleep 30
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] standard seeds completed; refreshing plots"
bash "$ROOT/codex/scripts/analyze_and_plot.sh" "$run_dir" 136 "$fingerprint_csv"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] plot refresh done"
