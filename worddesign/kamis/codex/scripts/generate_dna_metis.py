#!/usr/bin/env python3
"""Generate DNA-word incompatibility graphs in METIS format.

The generated graph matches the KaMIS DNA test instances:
- vertices: DNA words of length n with fixed GC count and self reverse-complement
  Hamming distance >= min_self_rc_hamming
- edges: pairs of words that violate at least one pairwise constraint:
  Hamming(w_i, w_j) < distance OR Hamming(w_i, reverse_complement(w_j)) < distance
"""

from __future__ import annotations

import argparse
import itertools
import time
from array import array
from pathlib import Path
from typing import List, Tuple


def encode_word(word: Tuple[int, ...]) -> int:
    code = 0
    for base in word:
        code = (code << 2) | base
    return code


def reverse_complement_encoded(code: int, word_length: int) -> int:
    # Complement mapping on 2-bit DNA alphabet is xor with 0b11.
    rc = 0
    x = code
    for _ in range(word_length):
        base = x & 0b11
        x >>= 2
        rc = (rc << 2) | (base ^ 0b11)
    return rc


def hamming_from_encoded(a: int, b: int, low_bit_mask: int) -> int:
    x = a ^ b
    # For each 2-bit symbol, set the low bit iff the symbol differs.
    return ((x | (x >> 1)) & low_bit_mask).bit_count()


def generate_valid_codes(
    word_length: int,
    gc_count: int,
    min_self_rc_hamming: int,
) -> Tuple[List[int], List[int]]:
    low_bit_mask = sum(1 << (2 * i) for i in range(word_length))
    codes: List[int] = []
    rc_codes: List[int] = []

    for word in itertools.product(range(4), repeat=word_length):
        gc = sum(1 for x in word if x in (1, 2))
        if gc != gc_count:
            continue

        code = encode_word(word)
        rc_code = reverse_complement_encoded(code, word_length)
        if hamming_from_encoded(code, rc_code, low_bit_mask) < min_self_rc_hamming:
            continue

        codes.append(code)
        rc_codes.append(rc_code)

    return codes, rc_codes


def build_adjacency(
    codes: List[int],
    rc_codes: List[int],
    word_length: int,
    distance: int,
) -> Tuple[List[array], int]:
    n = len(codes)
    low_bit_mask = sum(1 << (2 * i) for i in range(word_length))
    adjacency = [array("I") for _ in range(n)]
    edge_count = 0

    for i in range(n - 1):
        ci = codes[i]
        ai = adjacency[i]
        for j in range(i + 1, n):
            cj = codes[j]
            if hamming_from_encoded(ci, cj, low_bit_mask) < distance:
                ai.append(j + 1)
                adjacency[j].append(i + 1)
                edge_count += 1
                continue

            if hamming_from_encoded(ci, rc_codes[j], low_bit_mask) < distance:
                ai.append(j + 1)
                adjacency[j].append(i + 1)
                edge_count += 1

    return adjacency, edge_count


def write_metis(path: Path, adjacency: List[array], edge_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(f"{len(adjacency)} {edge_count}\n")
        for neighbors in adjacency:
            if neighbors:
                fh.write(" ".join(map(str, neighbors)))
            fh.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--word-length",
        type=int,
        default=8,
        help="DNA word length n (default: 8).",
    )
    parser.add_argument(
        "--distance",
        type=int,
        default=None,
        help="Minimum pairwise Hamming distance d (default: n/2).",
    )
    parser.add_argument(
        "--gc-count",
        type=int,
        default=None,
        help="Fixed GC count per word (default: n/2).",
    )
    parser.add_argument(
        "--min-self-rc-hamming",
        type=int,
        default=None,
        help="Minimum Hamming(word, reverse_complement(word)) (default: d).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output METIS file path (default: test/dna_word_graph_<n>.metis).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    n = args.word_length
    if n <= 0:
        raise ValueError("--word-length must be positive")

    d = args.distance if args.distance is not None else n // 2
    gc_count = args.gc_count if args.gc_count is not None else n // 2
    min_self_rc = (
        args.min_self_rc_hamming if args.min_self_rc_hamming is not None else d
    )

    output_path = (
        args.output if args.output is not None else Path(f"test/dna_word_graph_{n}.metis")
    )

    t0 = time.time()
    codes, rc_codes = generate_valid_codes(
        word_length=n,
        gc_count=gc_count,
        min_self_rc_hamming=min_self_rc,
    )
    t1 = time.time()

    adjacency, edge_count = build_adjacency(
        codes=codes,
        rc_codes=rc_codes,
        word_length=n,
        distance=d,
    )
    t2 = time.time()

    write_metis(output_path, adjacency, edge_count)
    t3 = time.time()

    print(f"Wrote: {output_path}")
    print(f"Vertices: {len(codes)}")
    print(f"Edges: {edge_count}")
    print(f"Generate valid words: {t1 - t0:.2f}s")
    print(f"Build incompatibility graph: {t2 - t1:.2f}s")
    print(f"Write METIS file: {t3 - t2:.2f}s")


if __name__ == "__main__":
    main()
