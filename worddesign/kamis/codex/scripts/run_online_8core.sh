#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

SEED_START="${SEED_START:-100}"
SEED_END="${SEED_END:-299}"
JOBS="${JOBS:-8}"
TIME_LIMIT="${TIME_LIMIT:-36000}"
TARGET_SIZE="${TARGET_SIZE:-136}"
MAX_WALLCLOCK_HOURS="${MAX_WALLCLOCK_HOURS:-48}"
INPUT_FILE="${INPUT_FILE:-$ROOT_DIR/test/dna_word_graph_8.metis}"

# Optional explicit run directory. Defaults to the newest codex run.
RUN_DIR="${RUN_DIR:-}"
if [[ -z "$RUN_DIR" ]]; then
  RUN_DIR="$(ls -1dt "$ROOT_DIR"/codex/runs/* 2>/dev/null | head -n1 || true)"
fi

if [[ -z "$RUN_DIR" || ! -d "$RUN_DIR" ]]; then
  echo "ERROR: RUN_DIR is not set and no codex run directory was found." >&2
  echo "Set RUN_DIR=/abs/path/to/codex/runs/<run_id> and retry." >&2
  exit 1
fi

if [[ "$SEED_END" -lt "$SEED_START" ]]; then
  echo "ERROR: SEED_END ($SEED_END) < SEED_START ($SEED_START)" >&2
  exit 1
fi

if [[ ! -x "$ROOT_DIR/deploy/online_mis" ]]; then
  echo "ERROR: missing executable $ROOT_DIR/deploy/online_mis" >&2
  exit 1
fi

bash "$ROOT_DIR/codex/scripts/ensure_dna_metis.sh" "$INPUT_FILE"

RESULTS_DIR="$RUN_DIR/results"
LOGS_DIR="$RUN_DIR/logs"
META_DIR="$RUN_DIR/meta"
mkdir -p "$RESULTS_DIR" "$LOGS_DIR" "$META_DIR"

ONLINE_ID="$(date -u +%Y%m%d_%H%M%S)_online_seed${SEED_START}_to_${SEED_END}"
ONLINE_LOG="$RUN_DIR/online_campaign.log"
JOBS_FILE="$META_DIR/jobs_online_${SEED_START}_${SEED_END}.tsv"
CMDS_FILE="$META_DIR/commands_online_${SEED_START}_${SEED_END}.txt"
PARALLEL_JOBLOG="$META_DIR/parallel_online_${SEED_START}_${SEED_END}.joblog"
RUN_CFG="$META_DIR/online_run_config_${SEED_START}_${SEED_END}.env"

prepared=0
skipped_existing=0
>"$JOBS_FILE"

for ((seed = SEED_START; seed <= SEED_END; seed++)); do
  out_file="$RESULTS_DIR/online_seed${seed}.txt"
  if [[ -f "$out_file" ]]; then
    skipped_existing=$((skipped_existing + 1))
    continue
  fi
  printf "%s\n" "$seed" >>"$JOBS_FILE"
  prepared=$((prepared + 1))
done

{
  while IFS= read -r seed; do
    out_file="$RESULTS_DIR/online_seed${seed}.txt"
    log_file="$LOGS_DIR/online_seed${seed}.log"
    printf "%q " "$ROOT_DIR/deploy/online_mis"
    printf "%q " "$INPUT_FILE"
    printf "%q " "--adaptive_greedy"
    printf "%q " "--time_limit=$TIME_LIMIT"
    if [[ "$TARGET_SIZE" -gt 0 ]]; then
      printf "%q " "--target_size=$TARGET_SIZE"
    fi
    printf "%q " "--seed=$seed"
    printf "%q " "--output=$out_file"
    printf "> %q 2>&1\n" "$log_file"
  done <"$JOBS_FILE"
} >"$CMDS_FILE"

{
  echo "ONLINE_ID=$ONLINE_ID"
  echo "RUN_DIR=$RUN_DIR"
  echo "SEED_START=$SEED_START"
  echo "SEED_END=$SEED_END"
  echo "JOBS=$JOBS"
  echo "TIME_LIMIT=$TIME_LIMIT"
  echo "TARGET_SIZE=$TARGET_SIZE"
  echo "MAX_WALLCLOCK_HOURS=$MAX_WALLCLOCK_HOURS"
  echo "INPUT_FILE=$INPUT_FILE"
  echo "PREPARED_JOBS=$prepared"
  echo "SKIPPED_EXISTING=$skipped_existing"
  echo "START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >"$RUN_CFG"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Online run $ONLINE_ID" | tee -a "$ONLINE_LOG"
echo "RUN_DIR=$RUN_DIR" | tee -a "$ONLINE_LOG"
echo "Seeds=$SEED_START..$SEED_END  jobs=$JOBS  time_limit=$TIME_LIMIT  target_size=$TARGET_SIZE" | tee -a "$ONLINE_LOG"
echo "Prepared jobs: $prepared (skipped existing: $skipped_existing)" | tee -a "$ONLINE_LOG"

APPROACH_FILE="$ROOT_DIR/codex/approach.md"
if [[ -f "$APPROACH_FILE" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Started online batch \`$ONLINE_ID\` in \`$RUN_DIR\`."
    echo "- Settings: seeds=\`$SEED_START..$SEED_END\`, jobs=\`$JOBS\`, time_limit=\`$TIME_LIMIT\`, target_size=\`$TARGET_SIZE\`."
    echo "- Prepared online jobs: \`$prepared\` (skipped existing: \`$skipped_existing\`)."
  } >>"$APPROACH_FILE"
fi

if [[ "$prepared" -eq 0 ]]; then
  echo "No pending online jobs to run." | tee -a "$ONLINE_LOG"
  exit 0
fi

set +e
timeout "${MAX_WALLCLOCK_HOURS}h" parallel --joblog "$PARALLEL_JOBLOG" -j "$JOBS" <"$CMDS_FILE"
parallel_rc=$?
set -e

if [[ "$parallel_rc" -eq 124 ]]; then
  echo "Online run stopped by wallclock timeout (${MAX_WALLCLOCK_HOURS}h)." | tee -a "$ONLINE_LOG"
elif [[ "$parallel_rc" -ne 0 ]]; then
  echo "Online run exited with code $parallel_rc." | tee -a "$ONLINE_LOG"
else
  echo "Online run completed all queued jobs." | tee -a "$ONLINE_LOG"
fi

echo "END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$RUN_CFG"
echo "PARALLEL_RC=$parallel_rc" >>"$RUN_CFG"

if [[ -f "$APPROACH_FILE" ]]; then
  {
    echo ""
    echo "### $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
    echo "- Online batch \`$ONLINE_ID\` finished with parallel exit code \`$parallel_rc\`."
    echo "- Log: \`$ONLINE_LOG\`."
  } >>"$APPROACH_FILE"
fi

echo "Online run done. Log: $ONLINE_LOG"
