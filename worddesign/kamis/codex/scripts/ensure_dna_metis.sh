#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT_FILE="${1:-$ROOT_DIR/test/dna_word_graph_8.metis}"
MODE="${METIS_GENERATE:-auto}"  # auto|always|never
GENERATOR="$ROOT_DIR/codex/scripts/generate_dna_metis.py"

case "$MODE" in
  auto|always|never) ;;
  *)
    echo "ERROR: METIS_GENERATE must be one of: auto, always, never (got: $MODE)" >&2
    exit 1
    ;;
esac

if [[ "$MODE" == "never" ]]; then
  if [[ ! -f "$INPUT_FILE" ]]; then
    echo "ERROR: missing METIS file and METIS_GENERATE=never: $INPUT_FILE" >&2
    exit 1
  fi
  exit 0
fi

if [[ ! -x "$GENERATOR" ]]; then
  echo "ERROR: missing generator script: $GENERATOR" >&2
  exit 1
fi

input_name="$(basename "$INPUT_FILE")"
if [[ "$input_name" =~ ^dna_word_graph_([0-9]+)\.metis$ ]]; then
  WORD_LENGTH="${BASH_REMATCH[1]}"
else
  if [[ -f "$INPUT_FILE" ]]; then
    exit 0
  fi
  echo "ERROR: cannot infer word length from filename: $INPUT_FILE" >&2
  echo "Expected pattern: dna_word_graph_<n>.metis" >&2
  exit 1
fi

lock_dir="${INPUT_FILE}.genlock"
while ! mkdir "$lock_dir" 2>/dev/null; do
  sleep 1
done
trap 'rmdir "$lock_dir" 2>/dev/null || true' EXIT

# Re-check after acquiring lock to avoid duplicate generation across concurrent runs.
if [[ "$MODE" == "auto" && -f "$INPUT_FILE" ]]; then
  echo "Using existing METIS file: $INPUT_FILE"
  exit 0
fi

echo "Generating METIS file: $INPUT_FILE (n=$WORD_LENGTH)"
"$GENERATOR" --word-length "$WORD_LENGTH" --output "$INPUT_FILE"

