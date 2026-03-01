#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/vandriel/Documents/GitHub/KaMIS
run_dir="$ROOT/codex/runs/20260226_103743_campaign_stream_seed100_to_499"
fingerprint_csv="/home/vandriel/Documents/GitHub/EoH_network/examples/user_worddesign/evaluation/active_136_search/plots_136_GPT_optuna_refined4_2h_2026-02-25/ac_fingerprint/ac_fingerprint_samples.csv"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] watcher started for first 3 social outputs"
while true; do
  count=$(find "$run_dir/results" -maxdepth 1 -name 'full_social_seed*.txt' | wc -l)
  if [[ "$count" -ge 3 ]]; then
    break
  fi
  sleep 15
done

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] first 3 social outputs detected; refreshing plots"
bash "$ROOT/codex/scripts/analyze_and_plot.sh" "$run_dir" 136 "$fingerprint_csv"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] plot refresh done"
