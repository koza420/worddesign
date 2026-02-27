#!/usr/bin/env python3
"""Extract solution metrics from KaMIS DNA-8 MIS bit-vector outputs."""

from __future__ import annotations

import argparse
import csv
import itertools
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


DNA_COMPLEMENT = (3, 2, 1, 0)


def hamming_distance(a: Sequence[int], b: Sequence[int]) -> int:
    return sum(x != y for x, y in zip(a, b))


def reverse_complement(word: Sequence[int]) -> tuple[int, ...]:
    return tuple(DNA_COMPLEMENT[x] for x in reversed(word))


def self_reverse_complement_distance(word: Sequence[int]) -> int:
    return hamming_distance(word, reverse_complement(word))


def generate_valid_words(word_length: int, gc_count: int, min_self_rc_hamming: int) -> list[tuple[int, ...]]:
    valid_words: list[tuple[int, ...]] = []
    for word in itertools.product(range(4), repeat=word_length):
        gc = sum(1 for x in word if x in (1, 2))
        if gc != gc_count:
            continue
        if self_reverse_complement_distance(word) < min_self_rc_hamming:
            continue
        valid_words.append(tuple(word))
    valid_words.sort()
    return valid_words


def load_solution_bits(path: Path) -> list[int]:
    bits: list[int] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_num, line in enumerate(fh, start=1):
            s = line.strip()
            if not s:
                continue
            if s not in {"0", "1"}:
                raise ValueError(f"{path}:{line_num} has invalid bit value {s!r}")
            bits.append(int(s))
    return bits


def parse_output_name(name: str) -> tuple[str, int, str]:
    m = re.match(r"(?P<config>.+)_seed(?P<seed>\d+)\.txt$", name)
    if m:
        config = m.group("config")
        seed = int(m.group("seed"))
        log_name = f"{config}_seed{seed}.log"
        return config, seed, log_name

    m = re.match(r"output_8_(?P<seed>\d+)\.txt$", name)
    if m:
        seed = int(m.group("seed"))
        return "legacy_redumis", seed, f"output_8_log_{seed}.txt"

    m = re.match(r"output_(?P<seed>\d+)\.txt$", name)
    if m:
        seed = int(m.group("seed"))
        return "legacy_online", seed, f"output_log_{seed}.txt"

    raise ValueError(f"Unsupported output filename format: {name}")


def parse_log_metrics(log_path: Path) -> tuple[int | None, float | None]:
    if not log_path.exists():
        return None, None

    best_solution: int | None = None
    time_found: float | None = None

    best_re = re.compile(r"Best solution:\s+(\d+)")
    size_re = re.compile(r"^\s*Size:\s+(\d+)")
    time_re = re.compile(r"Time found:\s+([0-9.]+)")

    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = best_re.search(line)
            if m:
                value = int(m.group(1))
                if best_solution is None or value > best_solution:
                    best_solution = value
            m = size_re.search(line)
            if m:
                value = int(m.group(1))
                if best_solution is None or value > best_solution:
                    best_solution = value
            m = time_re.search(line)
            if m:
                time_found = float(m.group(1))

    return best_solution, time_found


def iter_output_files(results_dir: Path) -> Iterable[Path]:
    for path in sorted(results_dir.glob("*.txt")):
        try:
            parse_output_name(path.name)
        except ValueError:
            continue
        yield path


def compute_metrics(bits: list[int], valid_words: list[tuple[int, ...]]) -> dict[str, int | float | None]:
    if len(bits) != len(valid_words):
        raise ValueError(f"Length mismatch bits={len(bits)} valid_words={len(valid_words)}")

    selected_indices = [i for i, b in enumerate(bits) if b == 1]
    size = len(selected_indices)
    counts = [0, 0, 0, 0]
    min_sum: int | None = None
    max_sum: int | None = None

    for idx in selected_indices:
        word = valid_words[idx]
        for x in word:
            counts[x] += 1
        s = sum(word)
        if min_sum is None or s < min_sum:
            min_sum = s
        if max_sum is None or s > max_sum:
            max_sum = s

    sorted_counts = sorted(counts)

    return {
        "bit_count": len(bits),
        "selected_size": size,
        "a_count": counts[0],
        "c_count": counts[1],
        "g_count": counts[2],
        "t_count": counts[3],
        "count_min1": sorted_counts[0],
        "count_min2": sorted_counts[1],
        "count_min3": sorted_counts[2],
        "count_min4": sorted_counts[3],
        "min_sum": min_sum,
        "max_sum": max_sum,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--word-length", type=int, default=8)
    parser.add_argument("--gc-count", type=int, default=4)
    parser.add_argument("--min-self-rc-hamming", type=int, default=4)
    parser.add_argument("--target-size", type=int, default=136)
    args = parser.parse_args()

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)

    valid_words = generate_valid_words(
        word_length=args.word_length,
        gc_count=args.gc_count,
        min_self_rc_hamming=args.min_self_rc_hamming,
    )

    rows: list[dict[str, int | float | str | None]] = []
    errors: list[str] = []

    for output_file in iter_output_files(args.results_dir):
        try:
            config, seed, log_name = parse_output_name(output_file.name)
            bits = load_solution_bits(output_file)
            metrics = compute_metrics(bits, valid_words)
            log_file = args.logs_dir / log_name
            best_solution, time_found = parse_log_metrics(log_file)

            rows.append(
                {
                    "config": config,
                    "seed": seed,
                    "output_file": str(output_file),
                    "log_file": str(log_file),
                    "best_solution": best_solution,
                    "time_found": time_found,
                    **metrics,
                }
            )
        except Exception as exc:  # pragma: no cover
            errors.append(f"{output_file}: {exc}")

    rows.sort(key=lambda r: (str(r["config"]), int(r["seed"])))

    fieldnames = [
        "config",
        "seed",
        "output_file",
        "log_file",
        "best_solution",
        "time_found",
        "bit_count",
        "selected_size",
        "a_count",
        "c_count",
        "g_count",
        "t_count",
        "count_min1",
        "count_min2",
        "count_min3",
        "count_min4",
        "min_sum",
        "max_sum",
    ]

    with args.output_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    size_counter = Counter(int(r["selected_size"]) for r in rows)
    target_rows = [r for r in rows if int(r["selected_size"]) >= args.target_size]

    with args.output_summary.open("w", encoding="utf-8") as fh:
        fh.write(f"results_dir={args.results_dir}\n")
        fh.write(f"logs_dir={args.logs_dir}\n")
        fh.write(f"files_analyzed={len(rows)}\n")
        fh.write(f"files_with_size_ge_{args.target_size}={len(target_rows)}\n")
        fh.write("size_distribution=\n")
        for size in sorted(size_counter):
            fh.write(f"  {size}: {size_counter[size]}\n")
        if errors:
            fh.write("errors=\n")
            for e in errors:
                fh.write(f"  {e}\n")

    print(f"Wrote CSV: {args.output_csv}")
    print(f"Wrote summary: {args.output_summary}")
    print(f"Analyzed files: {len(rows)}")
    print(f"Size >= {args.target_size}: {len(target_rows)}")
    if errors:
        print(f"Errors: {len(errors)}")


if __name__ == "__main__":
    main()

