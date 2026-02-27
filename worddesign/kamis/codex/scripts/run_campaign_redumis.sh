#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

# Campaign settings
CONFIGS="${CONFIGS:-full_standard full_social}"
SEED_START="${SEED_START:-100}"
SEED_END="${SEED_END:-499}"
JOBS="${JOBS:-12}"
TIME_LIMIT="${TIME_LIMIT:-50000}"
TARGET_SIZE="${TARGET_SIZE:-136}"
KERNELIZATION="${KERNELIZATION:-full}"
RED_THRES="${RED_THRES:-5000}"
INPUT_FILE="${INPUT_FILE:-$ROOT_DIR/test/dna_word_graph_8.metis}"
MAX_WALLCLOCK_HOURS="${MAX_WALLCLOCK_HOURS:-48}"

# Optional: previous run dir to skip already solved seeds (size >= TARGET_SIZE)
EXISTING_RUN_DIR="${EXISTING_RUN_DIR:-}"

if [[ "$SEED_END" -lt "$SEED_START" ]]; then
  echo "ERROR: SEED_END ($SEED_END) < SEED_START ($SEED_START)" >&2
  exit 1
fi

if [[ ! -x "$ROOT_DIR/deploy/redumis" ]]; then
  echo "ERROR: missing executable $ROOT_DIR/deploy/redumis" >&2
  exit 1
fi

campaign_id="$(date -u +%Y%m%d_%H%M%S)_campaign_stream_seed${SEED_START}_to_${SEED_END}"
campaign_dir="$ROOT_DIR/codex/runs/$campaign_id"
results_dir="$campaign_dir/results"
logs_dir="$campaign_dir/logs"
meta_dir="$campaign_dir/meta"
analysis_dir="$campaign_dir/analysis"
plots_dir="$campaign_dir/plots"
mkdir -p "$campaign_dir" "$results_dir" "$logs_dir" "$meta_dir" "$analysis_dir" "$plots_dir"

campaign_log="$campaign_dir/campaign.log"
jobs_file="$meta_dir/jobs.tsv"
cmds_file="$meta_dir/commands.txt"

is_solved_file() {
  local file="$1"
  local target="$2"
  [[ -f "$file" ]] || return 1
  local size
  size="$(awk '{s+=$1} END{print s+0}' "$file" 2>/dev/null || echo 0)"
  [[ "$size" -ge "$target" ]]
}

echo "Campaign ID: $campaign_id" | tee -a "$campaign_log"
echo "Configs: $CONFIGS" | tee -a "$campaign_log"
echo "Seeds: $SEED_START..$SEED_END" | tee -a "$campaign_log"
echo "JOBS=$JOBS TIME_LIMIT=$TIME_LIMIT TARGET_SIZE=$TARGET_SIZE MAX_WALLCLOCK_HOURS=$MAX_WALLCLOCK_HOURS" | tee -a "$campaign_log"
echo "Input: $INPUT_FILE" | tee -a "$campaign_log"
echo "Existing run dir for skip: ${EXISTING_RUN_DIR:-<none>}" | tee -a "$campaign_log"

{
  echo "CAMPAIGN_ID=$campaign_id"
  echo "CONFIGS=$CONFIGS"
  echo "SEED_START=$SEED_START"
  echo "SEED_END=$SEED_END"
  echo "JOBS=$JOBS"
  echo "TIME_LIMIT=$TIME_LIMIT"
  echo "TARGET_SIZE=$TARGET_SIZE"
  echo "KERNELIZATION=$KERNELIZATION"
  echo "RED_THRES=$RED_THRES"
  echo "INPUT_FILE=$INPUT_FILE"
  echo "MAX_WALLCLOCK_HOURS=$MAX_WALLCLOCK_HOURS"
  echo "EXISTING_RUN_DIR=$EXISTING_RUN_DIR"
  echo "START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >"$meta_dir/campaign_config.env"

total_jobs=0
skipped_jobs=0
>"$jobs_file"

for config in $CONFIGS; do
  for ((seed = SEED_START; seed <= SEED_END; seed++)); do
    out_file="$results_dir/${config}_seed${seed}.txt"

    # Skip if already solved in current campaign outputs (resume safety).
    if is_solved_file "$out_file" "$TARGET_SIZE"; then
      skipped_jobs=$((skipped_jobs + 1))
      continue
    fi

    # Skip if solved in an existing run dir.
    if [[ -n "$EXISTING_RUN_DIR" ]]; then
      prev_file="$EXISTING_RUN_DIR/results/${config}_seed${seed}.txt"
      if is_solved_file "$prev_file" "$TARGET_SIZE"; then
        skipped_jobs=$((skipped_jobs + 1))
        continue
      fi
    fi

    printf "%s\t%s\n" "$config" "$seed" >>"$jobs_file"
    total_jobs=$((total_jobs + 1))
  done
done

{
  while IFS=$'\t' read -r config seed; do
    out_file="$results_dir/${config}_seed${seed}.txt"
    log_file="$logs_dir/${config}_seed${seed}.log"
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
  done <"$jobs_file"
} >"$cmds_file"

echo "Prepared jobs: $total_jobs (skipped pre-solved: $skipped_jobs)" | tee -a "$campaign_log"

approach_file="$ROOT_DIR/codex/approach.md"
if [[ -f "$approach_file" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Started stream campaign \`$campaign_id\`."
    echo "- Scheduler mode: continuous queue (no chunk barriers)."
    echo "- Jobs prepared: \`$total_jobs\`, skipped pre-solved: \`$skipped_jobs\`."
    echo "- Settings: configs=\`$CONFIGS\`, seeds=\`$SEED_START..$SEED_END\`, jobs=\`$JOBS\`, time_limit=\`$TIME_LIMIT\`, target_size=\`$TARGET_SIZE\`, max_wallclock_hours=\`$MAX_WALLCLOCK_HOURS\`."
  } >>"$approach_file"
fi

if [[ "$total_jobs" -eq 0 ]]; then
  echo "No pending jobs after skip filtering. Exiting." | tee -a "$campaign_log"
  exit 0
fi

set +e
timeout "${MAX_WALLCLOCK_HOURS}h" parallel -j "$JOBS" <"$cmds_file"
parallel_rc=$?
set -e

if [[ "$parallel_rc" -eq 124 ]]; then
  echo "Campaign stopped by wallclock timeout (${MAX_WALLCLOCK_HOURS}h)." | tee -a "$campaign_log"
elif [[ "$parallel_rc" -ne 0 ]]; then
  echo "parallel exited with code $parallel_rc" | tee -a "$campaign_log"
else
  echo "parallel completed all queued jobs." | tee -a "$campaign_log"
fi

# Produce campaign-level analysis on currently available results.
bash "$ROOT_DIR/codex/scripts/analyze_and_plot.sh" "$campaign_dir" 136 | tee -a "$campaign_log" || true

echo "END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$meta_dir/campaign_config.env"

if [[ -f "$approach_file" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Stream campaign \`$campaign_id\` finished with parallel exit code \`$parallel_rc\`."
    echo "- Log: \`$campaign_log\`."
  } >>"$approach_file"
fi

echo "Campaign done. Log: $campaign_log"

