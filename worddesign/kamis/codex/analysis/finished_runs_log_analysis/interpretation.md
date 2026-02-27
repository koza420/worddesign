# KaMIS Approach Used and Successful (Finished Runs)

Data basis (as of 2026-02-26 11:47 UTC):
- 25 finished runs with output files present and validated in logs.
- Every finished run achieved independent set size 136.

## What approach is being applied
All successful runs use `redumis` with the same core pipeline:
1. Full reduction kernelization (`Apply all reductions: 1`, `Reductions threshold: 5000`).
2. Evolutionary search with population (`Population size: 250`) and combine operators:
   - `Vertex cover`
   - `Node separator`
   - `Multiway`
3. Partition/separator-driven recombination (`No. of partitions/separators/k-*` all 30).
4. Final acceptance through `Combine reduction`, which is the reported best operator in all successful logs.

Config variants:
- `full_standard` uses `KaHIP mode: 0`.
- `full_social` uses `KaHIP mode: 3`.

## What is successful in practice
Across finished logs:
- Final 136 is always recorded on a `Combine reduction` event.
- The operator that typically produces the final pre-combine 136 differs by config:
  - `full_standard`: mostly `Vertex cover` (11/17), then `Multiway` (3/17), `Node separator` (3/17).
  - `full_social`: `Vertex cover` (5/8) and `Multiway` (3/8).
- `Node separator` is frequently selected but has low improvement counts overall.

Time-to-136 (finished runs only):
- `full_standard` (17 runs): median 9218 s, min 2494 s, max 27351 s.
- `full_social` (8 runs): median 15964 s, min 3285 s, max 45072 s.

Interpretation:
- The successful recipe is not a single operator; it is the reduction + evolutionary-combine loop.
- `full_standard` is currently more time-efficient and less variable to reach 136.
- `full_social` adds diversity and can also hit 136, but with higher variance and longer tail times in the finished sample.
