#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <run_dir_or_legacy_tag> [target_size] [fingerprint_csv]" >&2
  echo "Examples:" >&2
  echo "  $0 /path/to/KaMIS/codex/runs/<run_id> 136" >&2
  echo "  $0 /path/to/KaMIS/codex/runs/<run_id> 136 /path/to/ac_fingerprint_samples.csv" >&2
  echo "  $0 legacy_redumis 136" >&2
  echo "  $0 legacy_online 136" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="${2:-136}"
FINGERPRINT_CSV="${3:-}"
ARG1="$1"

if [[ "$ARG1" == "legacy_redumis" ]]; then
  RESULTS_DIR="$ROOT_DIR/test/results8"
  LOGS_DIR="$ROOT_DIR/test/results8"
  OUT_DIR="$ROOT_DIR/codex/analysis/legacy_redumis"
elif [[ "$ARG1" == "legacy_online" ]]; then
  RESULTS_DIR="$ROOT_DIR/test/results8_online"
  LOGS_DIR="$ROOT_DIR/test/results8_online"
  OUT_DIR="$ROOT_DIR/codex/analysis/legacy_online"
else
  RESULTS_DIR="$ARG1/results"
  LOGS_DIR="$ARG1/logs"
  OUT_DIR="$ARG1/analysis"
fi

mkdir -p "$OUT_DIR"
CSV_FILE="$OUT_DIR/solution_metrics.csv"
SUMMARY_FILE="$OUT_DIR/summary.txt"
PLOTS_DIR="$OUT_DIR/plots"

python3 "$ROOT_DIR/codex/scripts/extract_solution_metrics.py" \
  --results-dir "$RESULTS_DIR" \
  --logs-dir "$LOGS_DIR" \
  --output-csv "$CSV_FILE" \
  --output-summary "$SUMMARY_FILE" \
  --target-size "$TARGET"

if [[ -n "$FINGERPRINT_CSV" ]]; then
  Rscript "$ROOT_DIR/codex/scripts/plot_scatter.R" "$CSV_FILE" "$PLOTS_DIR" "$TARGET" "$FINGERPRINT_CSV"
else
  Rscript "$ROOT_DIR/codex/scripts/plot_scatter.R" "$CSV_FILE" "$PLOTS_DIR" "$TARGET"
fi

APPROACH_FILE="$ROOT_DIR/codex/approach.md"
if [[ -f "$APPROACH_FILE" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Analysis+plot run complete for \`$ARG1\` with target size \`$TARGET\`."
    echo "- Metrics: \`$CSV_FILE\`."
    echo "- Summary: \`$SUMMARY_FILE\`."
    echo "- Plots: \`$PLOTS_DIR\`."
    if [[ -n "$FINGERPRINT_CSV" ]]; then
      echo "- Fingerprint overlay source: \`$FINGERPRINT_CSV\`."
    fi
  } >>"$APPROACH_FILE"
fi

echo "Analysis complete."
echo "CSV: $CSV_FILE"
echo "Summary: $SUMMARY_FILE"
echo "Plots: $PLOTS_DIR"
