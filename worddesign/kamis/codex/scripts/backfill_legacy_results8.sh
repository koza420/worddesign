#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

RUN_DIR="${RUN_DIR:-}"
if [[ -z "$RUN_DIR" ]]; then
  RUN_DIR="$(ls -1dt "$ROOT_DIR"/codex/runs/* 2>/dev/null | head -n1 || true)"
fi

if [[ -z "$RUN_DIR" || ! -d "$RUN_DIR" ]]; then
  echo "ERROR: RUN_DIR is not set and no codex run directory was found." >&2
  exit 1
fi

LEGACY_STD_DIR="${LEGACY_STD_DIR:-$ROOT_DIR/test/results8}"
LEGACY_ONLINE_DIR="${LEGACY_ONLINE_DIR:-$ROOT_DIR/test/results8_online}"

RESULTS_DIR="$RUN_DIR/results"
LOGS_DIR="$RUN_DIR/logs"
META_DIR="$RUN_DIR/meta"
mkdir -p "$RESULTS_DIR" "$LOGS_DIR" "$META_DIR"

copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ -f "$dst" ]]; then
    return 1
  fi
  if [[ ! -f "$src" ]]; then
    return 2
  fi
  cp "$src" "$dst"
  return 0
}

std_copied=0
std_missing_src=0
std_skipped_existing=0

for seed in $(seq 100 499); do
  src_out="$LEGACY_STD_DIR/output_8_${seed}.txt"
  src_log="$LEGACY_STD_DIR/output_8_log_${seed}.txt"
  dst_out="$RESULTS_DIR/full_standard_seed${seed}.txt"
  dst_log="$LOGS_DIR/full_standard_seed${seed}.log"

  if copy_if_missing "$src_out" "$dst_out"; then
    std_copied=$((std_copied + 1))
    if [[ -f "$src_log" && ! -f "$dst_log" ]]; then
      cp "$src_log" "$dst_log"
    fi
  else
    rc=$?
    if [[ "$rc" -eq 1 ]]; then
      std_skipped_existing=$((std_skipped_existing + 1))
    else
      std_missing_src=$((std_missing_src + 1))
    fi
  fi
done

online_copied=0
online_missing_src=0
online_skipped_existing=0

for seed in $(seq 100 299); do
  src_out="$LEGACY_ONLINE_DIR/output_${seed}.txt"
  src_log="$LEGACY_ONLINE_DIR/output_log_${seed}.txt"
  dst_out="$RESULTS_DIR/online_seed${seed}.txt"
  dst_log="$LOGS_DIR/online_seed${seed}.log"

  if copy_if_missing "$src_out" "$dst_out"; then
    online_copied=$((online_copied + 1))
    if [[ -f "$src_log" && ! -f "$dst_log" ]]; then
      cp "$src_log" "$dst_log"
    fi
  else
    rc=$?
    if [[ "$rc" -eq 1 ]]; then
      online_skipped_existing=$((online_skipped_existing + 1))
    else
      online_missing_src=$((online_missing_src + 1))
    fi
  fi
done

report_file="$META_DIR/backfill_legacy_results8_$(date -u +%Y%m%d_%H%M%S).txt"
{
  echo "run_dir=$RUN_DIR"
  echo "legacy_std_dir=$LEGACY_STD_DIR"
  echo "legacy_online_dir=$LEGACY_ONLINE_DIR"
  echo "std_copied=$std_copied"
  echo "std_skipped_existing=$std_skipped_existing"
  echo "std_missing_src=$std_missing_src"
  echo "online_copied=$online_copied"
  echo "online_skipped_existing=$online_skipped_existing"
  echo "online_missing_src=$online_missing_src"
} >"$report_file"

echo "Backfill complete."
echo "Report: $report_file"
cat "$report_file"
