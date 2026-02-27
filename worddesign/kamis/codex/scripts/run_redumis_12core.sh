#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT_FILE="${INPUT_FILE:-$ROOT_DIR/test/dna_word_graph_8.metis}"
CONFIGS="${CONFIGS:-full_standard full_social}"
SEED_START="${SEED_START:-100}"
SEED_COUNT="${SEED_COUNT:-12}"
JOBS="${JOBS:-12}"
TIME_LIMIT="${TIME_LIMIT:-50000}"
TARGET_SIZE="${TARGET_SIZE:-0}"
KERNELIZATION="${KERNELIZATION:-full}"
RED_THRES="${RED_THRES:-5000}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)_seed${SEED_START}_n${SEED_COUNT}_j${JOBS}}"

if [[ ! -x "$ROOT_DIR/deploy/redumis" ]]; then
  echo "ERROR: missing executable $ROOT_DIR/deploy/redumis" >&2
  exit 1
fi

bash "$ROOT_DIR/codex/scripts/ensure_dna_metis.sh" "$INPUT_FILE"

RUN_DIR="$ROOT_DIR/codex/runs/$RUN_ID"
RESULTS_DIR="$RUN_DIR/results"
LOGS_DIR="$RUN_DIR/logs"
META_DIR="$RUN_DIR/meta"
ANALYSIS_DIR="$RUN_DIR/analysis"
PLOTS_DIR="$RUN_DIR/plots"
mkdir -p "$RESULTS_DIR" "$LOGS_DIR" "$META_DIR" "$ANALYSIS_DIR" "$PLOTS_DIR"

JOBS_FILE="$META_DIR/jobs.tsv"
CMDS_FILE="$META_DIR/commands.txt"

{
  for config in $CONFIGS; do
    for ((i = 0; i < SEED_COUNT; i++)); do
      seed=$((SEED_START + i))
      printf "%s\t%s\n" "$config" "$seed"
    done
  done
} >"$JOBS_FILE"

{
  while IFS=$'\t' read -r config seed; do
    out_file="$RESULTS_DIR/${config}_seed${seed}.txt"
    log_file="$LOGS_DIR/${config}_seed${seed}.log"

    printf "%q " "$ROOT_DIR/deploy/redumis"
    printf "%q " "$INPUT_FILE"
    printf "%q " "--config=$config"
    printf "%q " "--time_limit=$TIME_LIMIT"
    if [[ "$TARGET_SIZE" -gt 0 ]]; then
      printf "%q " "--target_size=$TARGET_SIZE"
    fi
    printf "%q " "--seed=$seed"
    printf "%q " "--kernelization=$KERNELIZATION"
    printf "%q " "--red_thres=$RED_THRES"
    printf "%q " "--output=$out_file"
    printf "> %q 2>&1\n" "$log_file"
  done <"$JOBS_FILE"
} >"$CMDS_FILE"

cat >"$META_DIR/run_config.env" <<EOF
RUN_ID=$RUN_ID
INPUT_FILE=$INPUT_FILE
CONFIGS=$CONFIGS
SEED_START=$SEED_START
SEED_COUNT=$SEED_COUNT
JOBS=$JOBS
TIME_LIMIT=$TIME_LIMIT
TARGET_SIZE=$TARGET_SIZE
KERNELIZATION=$KERNELIZATION
RED_THRES=$RED_THRES
START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

APPROACH_FILE="$ROOT_DIR/codex/approach.md"
if [[ -f "$APPROACH_FILE" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Started run \`$RUN_ID\`."
    echo "- Settings: configs=\`$CONFIGS\`, seed_start=\`$SEED_START\`, seed_count=\`$SEED_COUNT\`, jobs=\`$JOBS\`, time_limit=\`$TIME_LIMIT\`, target_size=\`$TARGET_SIZE\`."
    echo "- Artifacts: \`$RUN_DIR\`."
  } >>"$APPROACH_FILE"
fi

echo "Running $((SEED_COUNT * $(wc -w <<<"$CONFIGS"))) jobs with parallel -j $JOBS"
echo "Run directory: $RUN_DIR"
parallel -j "$JOBS" <"$CMDS_FILE"

echo "Completed run: $RUN_ID"
echo "END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$META_DIR/run_config.env"
