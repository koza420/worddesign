import argparse
import hashlib
import itertools
import json
import os
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import matplotlib
import numpy as np
import pandas as pd
from tqdm import tqdm

matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import optuna
    import optuna.logging as optuna_logging

    OPTUNA_AVAILABLE = True
    optuna_logging.set_verbosity(optuna_logging.WARNING)
except ModuleNotFoundError:
    optuna = None
    OPTUNA_AVAILABLE = False


BASE_PARAMS = {
    "w_valid": 0.30,
    "w_rev": 0.20,
    "w_comp": 0.25,
    "w_sym": 0.15,
    "w_ratio_A": -0.05,
    "w_ratio_C": 0.02,
    "w_ratio_G": 0.04,
    "w_ratio_T": 0.02,
    "w_half": 0.02,
    "split_threshold": 1,
    "rev_min": 4,
    "comp_min": 4,
}


class FastWordDesignEvaluator:
    """
    Fast evaluator matching the greedy selection + post-filter structure used in
    the local worddesign/evaluation scripts for N=8.
    """

    def __init__(self, n: int = 8):
        self.n = int(n)
        self.d = self.n // 2
        self.comp_map = np.array([3, 2, 1, 0], dtype=np.int8)

        total = 4 ** self.n
        numbers = np.arange(total, dtype=np.int64)
        self.words = np.empty((total, self.n), dtype=np.int8)
        for i in range(self.n):
            self.words[:, self.n - i - 1] = numbers % 4
            numbers //= 4

        self.words_rev = self.words[:, ::-1]
        self.words_rc = self.comp_map[self.words_rev]

        # Features reused across trials.
        self.gc_mask = np.sum((self.words == 1) | (self.words == 2), axis=1) == self.d
        self.pos_diff_rev = np.sum(self.words != self.words_rev, axis=1)
        self.pos_diff_comp = np.sum(self.words != (3 - self.words), axis=1)
        self.eq_rev_count = np.sum(self.words == self.words_rev, axis=1)
        self.half_abs_diff = np.abs(self.words[:, : self.d] - self.words[:, self.d :])
        self.half_mismatch = self.d - np.count_nonzero(
            self.words[:, : self.d] == self.words[:, self.d :], axis=1
        )
        counts = np.stack([(self.words == k).sum(axis=1) for k in range(4)], axis=1)
        self.ratios = counts.astype(np.float64) / float(self.n)

    def _score_priorities(self, params: dict) -> np.ndarray:
        split_threshold = int(params["split_threshold"])
        rev_min = int(params["rev_min"])
        comp_min = int(params["comp_min"])

        symmetry_penalty = np.sum(self.half_abs_diff > split_threshold, axis=1)
        symmetry_score = (self.eq_rev_count - symmetry_penalty) / float(self.n)

        priorities = (
            float(params["w_valid"]) * self.gc_mask.astype(np.float64)
            + float(params["w_rev"]) * (self.pos_diff_rev >= rev_min).astype(np.float64)
            + float(params["w_comp"]) * (self.pos_diff_comp >= comp_min).astype(np.float64)
            + float(params["w_sym"]) * symmetry_score
            + float(params["w_ratio_A"]) * self.ratios[:, 0]
            + float(params["w_ratio_C"]) * self.ratios[:, 1]
            + float(params["w_ratio_G"]) * self.ratios[:, 2]
            + float(params["w_ratio_T"]) * self.ratios[:, 3]
            + float(params["w_half"]) * self.half_mismatch
        )

        priorities = priorities.astype(np.float64, copy=False)
        priorities[~np.isfinite(priorities)] = -np.inf
        return priorities

    def solve(self, params: dict) -> np.ndarray:
        priorities = self._score_priorities(params)
        selected_indices = []

        while np.any(priorities != -np.inf):
            max_index = int(np.argmax(priorities))
            selected_vector = self.words[max_index]

            differences = np.sum(self.words != selected_vector, axis=1)
            mask_complementary = np.sum(self.words_rc != selected_vector, axis=1) >= self.d

            # Mirrors existing behavior: invalidates by constraints after selecting max.
            mask_invalid = (differences < self.d) | (~mask_complementary) | (~self.gc_mask)
            priorities[mask_invalid] = -np.inf
            priorities[max_index] = -np.inf

            selected_indices.append(max_index)

        subset = self.words[np.array(selected_indices, dtype=np.int64)]
        return self.check_conditions_post(subset)

    def is_complementary(self, seq1: np.ndarray, seq2: np.ndarray) -> bool:
        return np.sum(np.flip(seq1) != self.comp_map[seq2]) >= self.d

    def check_conditions_post(self, wordset: np.ndarray) -> np.ndarray:
        n_wordset = len(wordset)
        if n_wordset == 0:
            return wordset

        mask_diffs = np.ones(n_wordset, dtype=bool)
        mask_complementary = np.ones(n_wordset, dtype=bool)
        mask_gc = np.sum((wordset == 1) | (wordset == 2), axis=1) == self.d
        # Enforce self reverse-complement distance (x vs xRC) as a hard constraint.
        self_rc = self.comp_map[wordset[:, ::-1]]
        self_hd = np.sum(wordset != self_rc, axis=1)
        mask_self_rc = self_hd >= self.d

        for i in range(n_wordset):
            for j in range(i + 1, n_wordset):
                if np.sum(wordset[i] != wordset[j]) < self.d:
                    mask_diffs[i] = False
                    mask_diffs[j] = False
                if not self.is_complementary(wordset[i], wordset[j]):
                    mask_complementary[i] = False
                    mask_complementary[j] = False

        return wordset[mask_diffs & mask_complementary & mask_gc & mask_self_rc]

    def subset_metrics(self, subset: np.ndarray) -> dict:
        if len(subset) == 0:
            return {
                "subset_len": 0,
                "self_rc_viol": 0,
                "min_self_hd": self.n,
            }

        subset_rc = self.comp_map[subset[:, ::-1]]
        self_hd = np.sum(subset != subset_rc, axis=1)

        return {
            "subset_len": int(len(subset)),
            "self_rc_viol": int(np.sum(self_hd < self.d)),
            "min_self_hd": int(self_hd.min()),
        }


PARAM_BOUNDS = {
    # Third refinement: move search box away from 136-heavy boundary corners.
    "w_valid": ("float", -0.45, 1.10),
    "w_rev": ("float", 0.05, 1.80),
    "w_comp": ("float", 0.0, 1.70),
    "w_sym": ("float", 0.10, 1.20),
    "w_ratio_A": ("float", -0.75, 0.15),
    "w_ratio_C": ("float", -0.20, 0.55),
    "w_ratio_G": ("float", -0.20, 0.60),
    "w_ratio_T": ("float", -0.20, 0.60),
    "w_half": ("float", 0.01, 0.24),
    "split_threshold": ("int", 1, 1),
    "rev_min": ("int", 2, 6),
    "comp_min": ("int", 3, 11),
}


def suggest_params(trial) -> dict:
    return {
        "w_valid": trial.suggest_float("w_valid", PARAM_BOUNDS["w_valid"][1], PARAM_BOUNDS["w_valid"][2]),
        "w_rev": trial.suggest_float("w_rev", PARAM_BOUNDS["w_rev"][1], PARAM_BOUNDS["w_rev"][2]),
        "w_comp": trial.suggest_float("w_comp", PARAM_BOUNDS["w_comp"][1], PARAM_BOUNDS["w_comp"][2]),
        "w_sym": trial.suggest_float("w_sym", PARAM_BOUNDS["w_sym"][1], PARAM_BOUNDS["w_sym"][2]),
        "w_ratio_A": trial.suggest_float(
            "w_ratio_A", PARAM_BOUNDS["w_ratio_A"][1], PARAM_BOUNDS["w_ratio_A"][2]
        ),
        "w_ratio_C": trial.suggest_float(
            "w_ratio_C", PARAM_BOUNDS["w_ratio_C"][1], PARAM_BOUNDS["w_ratio_C"][2]
        ),
        "w_ratio_G": trial.suggest_float(
            "w_ratio_G", PARAM_BOUNDS["w_ratio_G"][1], PARAM_BOUNDS["w_ratio_G"][2]
        ),
        "w_ratio_T": trial.suggest_float(
            "w_ratio_T", PARAM_BOUNDS["w_ratio_T"][1], PARAM_BOUNDS["w_ratio_T"][2]
        ),
        "w_half": trial.suggest_float("w_half", PARAM_BOUNDS["w_half"][1], PARAM_BOUNDS["w_half"][2]),
        "split_threshold": trial.suggest_int(
            "split_threshold", PARAM_BOUNDS["split_threshold"][1], PARAM_BOUNDS["split_threshold"][2]
        ),
        "rev_min": trial.suggest_int("rev_min", PARAM_BOUNDS["rev_min"][1], PARAM_BOUNDS["rev_min"][2]),
        "comp_min": trial.suggest_int("comp_min", PARAM_BOUNDS["comp_min"][1], PARAM_BOUNDS["comp_min"][2]),
    }


def random_params(rng: np.random.Generator) -> dict:
    out = {}
    for name, (ptype, lo, hi) in PARAM_BOUNDS.items():
        if ptype == "int":
            out[name] = int(rng.integers(lo, hi + 1))
        else:
            out[name] = float(rng.uniform(lo, hi))
    return out


def perturb_params(rng: np.random.Generator, center: dict, frac: float = 0.12) -> dict:
    out = {}
    for name, (ptype, lo, hi) in PARAM_BOUNDS.items():
        if ptype == "int":
            step = int(rng.choice([-1, 0, 1]))
            out[name] = int(np.clip(int(center[name]) + step, lo, hi))
        else:
            span = float(hi - lo)
            val = float(center[name]) + float(rng.normal(0.0, frac * span))
            out[name] = float(np.clip(val, lo, hi))
    return out


_WORKER_EVALUATORS = {}


def evaluate_candidate(task):
    n, params = task
    try:
        evaluator = _WORKER_EVALUATORS.get(n)
        if evaluator is None:
            evaluator = FastWordDesignEvaluator(n=n)
            _WORKER_EVALUATORS[n] = evaluator

        subset = evaluator.solve(params)
        metrics = evaluator.subset_metrics(subset)
        metrics["error"] = ""
        return metrics
    except Exception as exc:  # defensive guard for worker errors
        return {
            "subset_len": 0,
            "self_rc_viol": 10**9,
            "min_self_hd": 0,
            "error": str(exc),
        }


def check_all_constraints(subset: np.ndarray, d: int = 4) -> dict:
    if len(subset) == 0:
        return {
            "min_hd_xy_distinct": None,
            "viol_hd_xy_distinct_lt_d": 0,
            "min_hd_x_yrc_distinct": None,
            "viol_hd_x_yrc_distinct_lt_d": 0,
            "self_hd_hist": {},
            "self_viol_lt_d": 0,
            "gc_violations": 0,
        }

    comp_map = np.array([3, 2, 1, 0], dtype=np.int8)
    n_words = len(subset)

    min_hd_xy = 10**9
    viol_xy = 0
    min_hd_x_yrc = 10**9
    viol_x_yrc = 0

    for i in range(n_words):
        for j in range(i + 1, n_words):
            hd_xy = int(np.sum(subset[i] != subset[j]))
            if hd_xy < min_hd_xy:
                min_hd_xy = hd_xy
            if hd_xy < d:
                viol_xy += 1

            y_rc = comp_map[subset[j][::-1]]
            x_rc = comp_map[subset[i][::-1]]
            hd_iyrc = int(np.sum(subset[i] != y_rc))
            hd_jxrc = int(np.sum(subset[j] != x_rc))

            if hd_iyrc < min_hd_x_yrc:
                min_hd_x_yrc = hd_iyrc
            if hd_jxrc < min_hd_x_yrc:
                min_hd_x_yrc = hd_jxrc

            if hd_iyrc < d:
                viol_x_yrc += 1
            if hd_jxrc < d:
                viol_x_yrc += 1

    subset_rc = comp_map[subset[:, ::-1]]
    self_hd = np.sum(subset != subset_rc, axis=1)
    self_hist = pd.Series(self_hd).value_counts().sort_index().to_dict()

    gc_counts = np.sum((subset == 1) | (subset == 2), axis=1)
    gc_viol = int(np.sum(gc_counts != d))

    return {
        "min_hd_xy_distinct": int(min_hd_xy),
        "viol_hd_xy_distinct_lt_d": int(viol_xy),
        "min_hd_x_yrc_distinct": int(min_hd_x_yrc),
        "viol_hd_x_yrc_distinct_lt_d": int(viol_x_yrc),
        "self_hd_hist": {int(k): int(v) for k, v in self_hist.items()},
        "self_viol_lt_d": int(np.sum(self_hd < d)),
        "gc_violations": gc_viol,
    }


def _extract_run_columns(df: pd.DataFrame):
    subset_col = "user_attrs_subset_len" if "user_attrs_subset_len" in df.columns else "subset_len"
    self_viol_col = "user_attrs_self_rc_viol" if "user_attrs_self_rc_viol" in df.columns else "self_rc_viol"
    param_cols = [c for c in df.columns if c.startswith("params_")]
    return subset_col, self_viol_col, param_cols


def _param_label(col: str) -> str:
    return col.replace("params_", "")


def _select_focus_params(
    df: pd.DataFrame, param_cols: list[str], subset_col: str, self_viol_col: str, max_params: int
) -> list[str]:
    if not param_cols:
        return []

    work = df.copy()
    numeric_cols = [c for c in [subset_col, self_viol_col] + param_cols if c in work.columns]
    for c in numeric_cols:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    work = work.dropna(subset=[subset_col] + param_cols)
    if work.empty:
        return []

    feasible = work[work[self_viol_col] == 0] if self_viol_col in work.columns else work
    base = feasible if len(feasible) >= 20 else work

    scored = []
    for c in param_cols:
        if base[c].nunique() < 2:
            continue
        corr = base[c].corr(base[subset_col], method="spearman")
        if pd.isna(corr):
            corr = 0.0
        scored.append((abs(float(corr)), float(base[c].var()), c))

    if not scored:
        return param_cols[:max_params]

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    selected = [c for _, _, c in scored[:max_params]]

    # Backfill if a few parameters tie out to low variance or NaNs.
    if len(selected) < min(max_params, len(param_cols)):
        for c in param_cols:
            if c not in selected and base[c].nunique() > 1:
                selected.append(c)
                if len(selected) >= max_params:
                    break
    return selected


def generate_param_pair_plots(df: pd.DataFrame, out_dir: str, max_params: int = 6, max_pairs: int = 15) -> dict:
    subset_col, self_viol_col, param_cols = _extract_run_columns(df)
    if subset_col not in df.columns or self_viol_col not in df.columns or not param_cols:
        return {"plot_dir": None, "saved": [], "focus_params": [], "error": "missing required columns"}

    work = df.copy()
    numeric_cols = [c for c in [subset_col, self_viol_col] + param_cols if c in work.columns]
    for c in numeric_cols:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    work = work.dropna(subset=[subset_col, self_viol_col] + param_cols)
    if work.empty:
        return {"plot_dir": None, "saved": [], "focus_params": [], "error": "no numeric rows for plotting"}

    focus_params = _select_focus_params(
        work, param_cols=param_cols, subset_col=subset_col, self_viol_col=self_viol_col, max_params=max_params
    )
    if len(focus_params) < 2:
        return {"plot_dir": None, "saved": [], "focus_params": focus_params, "error": "not enough variable params"}

    pairs = []
    for i in range(len(focus_params)):
        for j in range(i + 1, len(focus_params)):
            pairs.append((focus_params[i], focus_params[j]))
    pairs = pairs[:max_pairs]

    feasible = work[work[self_viol_col] == 0]
    best_len = float(feasible[subset_col].max()) if len(feasible) > 0 else float(work[subset_col].max())
    best_points = feasible[feasible[subset_col] == best_len] if len(feasible) > 0 else work[work[subset_col] == best_len]

    plot_dir = os.path.join(out_dir, "plots_param_pairs")
    os.makedirs(plot_dir, exist_ok=True)

    saved = []
    for x_col, y_col in pairs:
        fig, ax = plt.subplots(figsize=(8, 6))

        if len(work) >= 500:
            hb = ax.hexbin(
                work[x_col],
                work[y_col],
                C=work[subset_col],
                reduce_C_function=np.mean,
                gridsize=35,
                mincnt=3,
                cmap="viridis",
            )
            cbar = fig.colorbar(hb, ax=ax)
            cbar.set_label("Mean subset_len")
        else:
            sc = ax.scatter(
                work[x_col], work[y_col], c=work[subset_col], cmap="viridis", s=20, alpha=0.75, edgecolors="none"
            )
            cbar = fig.colorbar(sc, ax=ax)
            cbar.set_label("Subset length")

        if len(best_points) > 0:
            ax.scatter(
                best_points[x_col],
                best_points[y_col],
                facecolors="none",
                edgecolors="red",
                s=120,
                linewidths=1.6,
                label=f"Best feasible len={int(best_len)}",
            )
            ax.legend(loc="best")

        ax.set_xlabel(_param_label(x_col))
        ax.set_ylabel(_param_label(y_col))
        ax.set_title(f"{_param_label(x_col)} vs {_param_label(y_col)}")
        fig.tight_layout()

        filename = f"pair_{_param_label(x_col)}__{_param_label(y_col)}.png"
        out_path = os.path.join(plot_dir, filename)
        fig.savefig(out_path, dpi=160)
        plt.close(fig)
        saved.append(out_path)

    index_path = os.path.join(plot_dir, "plot_index.txt")
    with open(index_path, "w") as f:
        f.write(f"subset_col={subset_col}\n")
        f.write(f"self_viol_col={self_viol_col}\n")
        f.write(f"focus_params={focus_params}\n")
        f.write(f"best_feasible_len={int(best_len)}\n")
        for p in saved:
            f.write(f"{os.path.basename(p)}\n")
    saved.append(index_path)

    return {"plot_dir": plot_dir, "saved": saved, "focus_params": focus_params, "error": ""}


def _canonical_subset_hash(subset: np.ndarray) -> str:
    if len(subset) == 0:
        return "EMPTY"
    # Stable ordering ensures identical sets map to identical hashes.
    order = np.lexsort(subset.T[::-1])
    canon = subset[order]
    return hashlib.sha1(canon.tobytes()).hexdigest()[:16]


_COMP_PRESERVING_PERMS = [
    np.array(p, dtype=np.int8)
    for p in itertools.permutations([0, 1, 2, 3])
    if all(p[3 - x] == 3 - p[x] for x in [0, 1, 2, 3])
]


def _canonical_count_orbit(a: int, c: int, g: int, t: int) -> tuple[int, int, int, int]:
    vec = np.array([a, c, g, t], dtype=np.int64)
    best = None
    for p in _COMP_PRESERVING_PERMS:
        out = np.empty(4, dtype=np.int64)
        out[p] = vec
        key = (int(out[0]), int(out[1]), int(out[2]), int(out[3]))
        if best is None or key < best:
            best = key
    return best


def generate_ac_fingerprint(
    df: pd.DataFrame,
    out_dir: str,
    n: int,
    workers: int,
    sample_size: int,
    seed: int,
) -> dict:
    subset_col, self_viol_col, param_cols = _extract_run_columns(df)
    if subset_col not in df.columns or self_viol_col not in df.columns or not param_cols:
        return {"dir": None, "saved": [], "error": "missing required columns", "target_len": None}

    work = df.copy()
    numeric_cols = [c for c in [subset_col, self_viol_col, "number"] + param_cols if c in work.columns]
    for c in numeric_cols:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    work = work.dropna(subset=[subset_col, self_viol_col] + param_cols)
    if work.empty:
        return {"dir": None, "saved": [], "error": "no rows after numeric filtering", "target_len": None}

    feasible = work[work[self_viol_col] == 0]
    if feasible.empty:
        return {"dir": None, "saved": [], "error": "no feasible rows", "target_len": None}

    target_len = int(feasible[subset_col].max())
    target = feasible[feasible[subset_col] == target_len].copy()
    if target.empty:
        return {"dir": None, "saved": [], "error": "no rows at target length", "target_len": target_len}

    if sample_size > 0 and len(target) > sample_size:
        target = target.sample(n=sample_size, random_state=seed).copy()

    fp_dir = os.path.join(out_dir, "ac_fingerprint")
    os.makedirs(fp_dir, exist_ok=True)

    local = threading.local()

    def get_evaluator():
        eva = getattr(local, "eva", None)
        if eva is None:
            eva = FastWordDesignEvaluator(n=n)
            local.eva = eva
        return eva

    def solve_row(row):
        params = {c.replace("params_", ""): row[c] for c in param_cols}
        subset = get_evaluator().solve(params)
        counts = np.bincount(subset.reshape(-1), minlength=4)
        return {
            "trial": int(row["number"]) if "number" in row else -1,
            "subset_len_recomputed": int(len(subset)),
            "A": int(counts[0]),
            "C": int(counts[1]),
            "G": int(counts[2]),
            "T": int(counts[3]),
            "hash": _canonical_subset_hash(subset),
        }

    rows = [r for _, r in target.iterrows()]
    recs = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for rec in ex.map(solve_row, rows):
            recs.append(rec)

    sample_df = pd.DataFrame(recs)
    sample_csv = os.path.join(fp_dir, "ac_fingerprint_samples.csv")
    sample_df.to_csv(sample_csv, index=False)

    ac_agg = sample_df.groupby(["A", "C"], as_index=False).size().sort_values("size", ascending=False)
    ac_csv = os.path.join(fp_dir, "ac_point_counts.csv")
    ac_agg.to_csv(ac_csv, index=False)

    hash_agg = (
        sample_df.groupby(["hash", "A", "C", "G", "T"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .reset_index(drop=True)
    )
    orbit_canon = hash_agg.apply(
        lambda r: _canonical_count_orbit(int(r["A"]), int(r["C"]), int(r["G"]), int(r["T"])),
        axis=1,
        result_type="expand",
    )
    orbit_canon.columns = ["orbit_canon_A", "orbit_canon_C", "orbit_canon_G", "orbit_canon_T"]
    hash_agg = pd.concat([hash_agg, orbit_canon.reset_index(drop=True)], axis=1)

    orbit_agg = (
        hash_agg.groupby(
            ["orbit_canon_A", "orbit_canon_C", "orbit_canon_G", "orbit_canon_T"], as_index=False
        )["size"]
        .sum()
        .sort_values("size", ascending=False)
        .reset_index(drop=True)
    )
    orbit_keys = sorted(
        {
            (int(r["orbit_canon_A"]), int(r["orbit_canon_C"]), int(r["orbit_canon_G"]), int(r["orbit_canon_T"]))
            for _, r in orbit_agg.iterrows()
        }
    )
    letters = list(string.ascii_uppercase)
    orbit_to_class = {k: letters[i] if i < len(letters) else f"C{i+1}" for i, k in enumerate(orbit_keys)}
    hash_agg["class"] = hash_agg.apply(
        lambda r: orbit_to_class[
            (
                int(r["orbit_canon_A"]),
                int(r["orbit_canon_C"]),
                int(r["orbit_canon_G"]),
                int(r["orbit_canon_T"]),
            )
        ],
        axis=1,
    )
    orbit_agg["class"] = orbit_agg.apply(
        lambda r: orbit_to_class[
            (
                int(r["orbit_canon_A"]),
                int(r["orbit_canon_C"]),
                int(r["orbit_canon_G"]),
                int(r["orbit_canon_T"]),
            )
        ],
        axis=1,
    )

    hash_csv = os.path.join(fp_dir, "hash_class_counts.csv")
    hash_agg.to_csv(hash_csv, index=False)
    orbit_csv = os.path.join(fp_dir, "orbit_class_counts.csv")
    orbit_agg.to_csv(orbit_csv, index=False)

    half_total = target_len * n // 2
    ac_set = {(int(a), int(c)) for a, c in zip(ac_agg["A"], ac_agg["C"])}
    mirror_rows = []
    for _, r in ac_agg.iterrows():
        a = int(r["A"])
        c = int(r["C"])
        mirror_rows.append(
            {
                "A": a,
                "C": c,
                "count": int(r["size"]),
                "mirror_A": int(half_total - a),
                "mirror_C": int(half_total - c),
                "mirror_present": int((half_total - a, half_total - c) in ac_set),
            }
        )
    mirror_df = pd.DataFrame(mirror_rows)
    mirror_csv = os.path.join(fp_dir, "ac_mirror_pairs.csv")
    mirror_df.to_csv(mirror_csv, index=False)

    # Bubble plot in A/C space.
    fig, ax = plt.subplots(figsize=(8, 6))
    if not ac_agg.empty:
        sc = ax.scatter(
            ac_agg["A"],
            ac_agg["C"],
            s=np.sqrt(ac_agg["size"]) * 26,
            c=ac_agg["size"],
            cmap="viridis",
            alpha=0.85,
            edgecolors="k",
            linewidths=0.4,
        )
        cb = fig.colorbar(sc, ax=ax)
        cb.set_label("Sample count")
        for _, r in ac_agg.iterrows():
            ax.text(int(r["A"]) + 1.0, int(r["C"]) + 1.0, str(int(r["size"])), fontsize=7)

    ax.axvline(half_total / 2.0, color="gray", linestyle="--", linewidth=1)
    ax.axhline(half_total / 2.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Total A count")
    ax.set_ylabel("Total C count")
    ax.set_title(f"A/C fingerprint at subset_len={target_len} (sample n={len(sample_df)})")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    plot_path = os.path.join(fp_dir, "ac_fingerprint_scatter.png")
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    summary = {
        "target_len": int(target_len),
        "n_candidate_rows": int(len(feasible[feasible[subset_col] == target_len])),
        "n_sampled": int(len(sample_df)),
        "n_unique_ac_points": int(ac_agg.shape[0]),
        "n_unique_hash_classes": int(hash_agg["hash"].nunique()),
        "n_orbit_classes": int(orbit_agg.shape[0]),
        "all_points_have_mirror": bool(mirror_df["mirror_present"].all()) if not mirror_df.empty else False,
        "top_ac_points": ac_agg.head(15).to_dict(orient="records"),
        "orbit_class_counts": orbit_agg.to_dict(orient="records"),
    }
    summary_path = os.path.join(fp_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    saved = [sample_csv, ac_csv, hash_csv, orbit_csv, mirror_csv, plot_path, summary_path]
    return {
        "dir": fp_dir,
        "saved": saved,
        "error": "",
        "target_len": int(target_len),
        "n_sampled": int(len(sample_df)),
        "n_unique_ac_points": int(ac_agg.shape[0]),
        "n_unique_hash_classes": int(hash_agg["hash"].nunique()),
        "n_orbit_classes": int(orbit_agg.shape[0]),
        "all_points_have_mirror": bool(mirror_df["mirror_present"].all()) if not mirror_df.empty else False,
    }


def _evaluate_batch(args, trial_params):
    tasks = [(args.n, params) for _, params in trial_params]
    with ThreadPoolExecutor(max_workers=args.workers_eff) as executor:
        return list(executor.map(evaluate_candidate, tasks))


def run_search_with_optuna(args):
    sampler = optuna.samplers.TPESampler(
        seed=args.seed,
        multivariate=True,
        group=True,
        n_startup_trials=min(100, max(10, args.trials // 10)),
    )
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.enqueue_trial(BASE_PARAMS)

    best_feasible_len = -1
    best_feasible_trial_number = None
    start_ts = time.time()

    with ThreadPoolExecutor(max_workers=args.workers_eff) as executor:
        pbar = tqdm(total=args.trials, desc="Optuna 136 search", smoothing=0.1)
        done = 0
        while done < args.trials:
            if args.deadline_ts is not None and time.time() >= args.deadline_ts:
                break
            b = min(args.batch_size_eff, args.trials - done)
            trial_items = []
            for _ in range(b):
                trial = study.ask()
                params = suggest_params(trial)
                trial_items.append((trial, params))

            tasks = [(args.n, params) for _, params in trial_items]
            results = list(executor.map(evaluate_candidate, tasks))

            for (trial, params), metrics in zip(trial_items, results):
                subset_len = int(metrics["subset_len"])
                self_rc_viol = int(metrics["self_rc_viol"])
                min_self_hd = int(metrics["min_self_hd"])
                err = metrics.get("error", "")

                feasible_len = subset_len if self_rc_viol == 0 else subset_len - 1000 - self_rc_viol
                trial.set_user_attr("subset_len", subset_len)
                trial.set_user_attr("self_rc_viol", self_rc_viol)
                trial.set_user_attr("min_self_hd", min_self_hd)
                if err:
                    trial.set_user_attr("error", err)

                study.tell(trial, -float(feasible_len))

                if self_rc_viol == 0 and subset_len > best_feasible_len:
                    best_feasible_len = subset_len
                    best_feasible_trial_number = trial.number
                    pbar.set_description(
                        f"Optuna 136 search (best feasible={best_feasible_len}, trial={best_feasible_trial_number})"
                    )

            done += b
            pbar.update(b)
        pbar.close()

    elapsed_seconds = time.time() - start_ts
    stop_reason = "trial_limit"
    if args.deadline_ts is not None and done < args.trials:
        stop_reason = "time_budget"

    df = study.trials_dataframe(attrs=("number", "value", "params", "user_attrs"))
    if "value" in df.columns:
        df["feasible_len"] = -df["value"]

    feasible_trials = [
        t
        for t in study.trials
        if t.value is not None and int(t.user_attrs.get("self_rc_viol", 10**9)) == 0
    ]
    if feasible_trials:
        best_trial = max(feasible_trials, key=lambda t: int(t.user_attrs.get("subset_len", -1)))
    else:
        best_trial = study.best_trial

    return {
        "mode": "optuna",
        "df": df,
        "best_params": best_trial.params,
        "best_trial_number": int(best_trial.number),
        "n_evaluated": int(done),
        "elapsed_seconds": float(elapsed_seconds),
        "stop_reason": stop_reason,
    }


def run_search_without_optuna(args):
    rng = np.random.default_rng(args.seed)
    records = []
    start_ts = time.time()

    best_feasible_len = -1
    best_feasible_params = dict(BASE_PARAMS)
    best_trial_number = 0

    elites = []

    with ThreadPoolExecutor(max_workers=args.workers_eff) as executor:
        pbar = tqdm(total=args.trials, desc="Fallback search", smoothing=0.1)
        done = 0
        while done < args.trials:
            if args.deadline_ts is not None and time.time() >= args.deadline_ts:
                break
            b = min(args.batch_size_eff, args.trials - done)

            trial_params = []
            for i in range(b):
                trial_number = done + i
                if trial_number == 0:
                    params = dict(BASE_PARAMS)
                    source = "baseline"
                else:
                    if elites and rng.random() < 0.70:
                        center = elites[int(rng.integers(0, len(elites)))]["params"]
                        params = perturb_params(rng, center)
                        source = "local"
                    else:
                        params = random_params(rng)
                        source = "global"
                trial_params.append((trial_number, params, source))

            tasks = [(args.n, params) for _, params, _ in trial_params]
            results = list(executor.map(evaluate_candidate, tasks))

            for (trial_number, params, source), metrics in zip(trial_params, results):
                subset_len = int(metrics["subset_len"])
                self_rc_viol = int(metrics["self_rc_viol"])
                min_self_hd = int(metrics["min_self_hd"])
                err = metrics.get("error", "")

                feasible_len = subset_len if self_rc_viol == 0 else subset_len - 1000 - self_rc_viol
                objective_value = -float(feasible_len)

                row = {
                    "number": int(trial_number),
                    "value": objective_value,
                    "feasible_len": float(feasible_len),
                    "subset_len": subset_len,
                    "self_rc_viol": self_rc_viol,
                    "min_self_hd": min_self_hd,
                    "source": source,
                    "error": err,
                }
                row.update({f"params_{k}": v for k, v in params.items()})
                records.append(row)

                if self_rc_viol == 0:
                    elites.append({"len": subset_len, "params": dict(params)})
                    elites.sort(key=lambda x: x["len"], reverse=True)
                    elites = elites[:20]

                if self_rc_viol == 0 and subset_len > best_feasible_len:
                    best_feasible_len = subset_len
                    best_feasible_params = dict(params)
                    best_trial_number = trial_number
                    pbar.set_description(
                        f"Fallback search (best feasible={best_feasible_len}, trial={best_trial_number})"
                    )

            done += b
            pbar.update(b)
        pbar.close()

    elapsed_seconds = time.time() - start_ts
    stop_reason = "trial_limit"
    if args.deadline_ts is not None and done < args.trials:
        stop_reason = "time_budget"

    df = pd.DataFrame(records)
    if best_feasible_len < 0 and len(df) > 0:
        i_best = int(df["value"].idxmin())
        best_feasible_params = {
            k.replace("params_", ""): df.loc[i_best, k]
            for k in df.columns
            if k.startswith("params_")
        }
        best_trial_number = int(df.loc[i_best, "number"])

    return {
        "mode": "fallback",
        "df": df,
        "best_params": best_feasible_params,
        "best_trial_number": int(best_trial_number),
        "n_evaluated": int(done),
        "elapsed_seconds": float(elapsed_seconds),
        "stop_reason": stop_reason,
    }


def run_search(args):
    os.makedirs(args.out_dir, exist_ok=True)
    args.workers_eff = args.workers if args.workers is not None else (os.cpu_count() or 1)
    args.batch_size_eff = max(1, min(args.batch_size, args.workers_eff))
    args.time_budget_seconds = max(0.0, float(args.time_budget_hours) * 3600.0)
    args.deadline_ts = time.time() + args.time_budget_seconds if args.time_budget_seconds > 0 else None

    if OPTUNA_AVAILABLE:
        run_data = run_search_with_optuna(args)
    else:
        print("Optuna not available. Running local fallback search mode.")
        run_data = run_search_without_optuna(args)

    df = run_data["df"]
    best_params = run_data["best_params"]
    best_trial_number = run_data["best_trial_number"]
    mode = run_data["mode"]
    n_evaluated = int(run_data.get("n_evaluated", len(df)))
    elapsed_seconds = float(run_data.get("elapsed_seconds", 0.0))
    stop_reason = run_data.get("stop_reason", "trial_limit")

    csv_path = os.path.join(args.out_dir, "optuna_136_log.csv")
    df.to_csv(csv_path, index=False, float_format="%.17g")

    plot_info = {"plot_dir": None, "saved": [], "focus_params": [], "error": ""}
    try:
        plot_info = generate_param_pair_plots(
            df, out_dir=args.out_dir, max_params=args.plot_focus_params, max_pairs=args.plot_max_pairs
        )
    except Exception as exc:
        plot_info = {"plot_dir": None, "saved": [], "focus_params": [], "error": str(exc)}

    ac_info = {"dir": None, "saved": [], "error": "disabled by sample size", "target_len": None}
    if args.ac_fingerprint_sample >= 0:
        try:
            # Keep fingerprinting responsive even on high-core machines.
            fp_workers = max(1, min(args.workers_eff, 8))
            ac_info = generate_ac_fingerprint(
                df=df,
                out_dir=args.out_dir,
                n=args.n,
                workers=fp_workers,
                sample_size=args.ac_fingerprint_sample,
                seed=args.seed,
            )
        except Exception as exc:
            ac_info = {"dir": None, "saved": [], "error": str(exc), "target_len": None}

    evaluator = FastWordDesignEvaluator(n=args.n)
    best_subset = evaluator.solve(best_params)
    best_metrics = evaluator.subset_metrics(best_subset)
    full_constraints = check_all_constraints(best_subset, d=args.n // 2)

    subset_file = os.path.join(args.out_dir, "best_subset.txt")
    with open(subset_file, "w") as f:
        for row in best_subset:
            f.write("".join(str(int(x)) for x in row) + "\n")

    summary_path = os.path.join(args.out_dir, "summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"mode={mode}\n")
        f.write(f"trials={args.trials}\n")
        f.write(f"time_budget_hours={args.time_budget_hours}\n")
        f.write(f"workers={args.workers_eff}\n")
        f.write(f"n_evaluated={n_evaluated}\n")
        f.write(f"elapsed_seconds={elapsed_seconds:.3f}\n")
        f.write(f"stop_reason={stop_reason}\n")
        f.write(f"best_trial_number={best_trial_number}\n")
        f.write(f"best_params={best_params}\n")
        f.write(f"subset_len={best_metrics['subset_len']}\n")
        f.write(f"self_rc_viol={best_metrics['self_rc_viol']}\n")
        f.write(f"min_self_hd={best_metrics['min_self_hd']}\n")
        f.write(f"constraints={full_constraints}\n")
        f.write(f"plot_focus_params={plot_info.get('focus_params', [])}\n")
        f.write(f"plot_count={len(plot_info.get('saved', []))}\n")
        f.write(f"plot_dir={plot_info.get('plot_dir', None)}\n")
        if plot_info.get("error"):
            f.write(f"plot_error={plot_info['error']}\n")
        f.write(f"ac_fingerprint_sample={args.ac_fingerprint_sample}\n")
        f.write(f"ac_fingerprint_dir={ac_info.get('dir', None)}\n")
        f.write(f"ac_fingerprint_target_len={ac_info.get('target_len', None)}\n")
        f.write(f"ac_fingerprint_saved={len(ac_info.get('saved', []))}\n")
        if "n_sampled" in ac_info:
            f.write(f"ac_fingerprint_n_sampled={ac_info['n_sampled']}\n")
        if "n_unique_ac_points" in ac_info:
            f.write(f"ac_fingerprint_unique_ac_points={ac_info['n_unique_ac_points']}\n")
        if "n_unique_hash_classes" in ac_info:
            f.write(f"ac_fingerprint_unique_hash_classes={ac_info['n_unique_hash_classes']}\n")
        if "n_orbit_classes" in ac_info:
            f.write(f"ac_fingerprint_n_orbit_classes={ac_info['n_orbit_classes']}\n")
        if "all_points_have_mirror" in ac_info:
            f.write(f"ac_fingerprint_all_points_have_mirror={ac_info['all_points_have_mirror']}\n")
        if ac_info.get("error"):
            f.write(f"ac_fingerprint_error={ac_info['error']}\n")

    print(f"Saved trial log: {csv_path}")
    if plot_info.get("plot_dir"):
        print(f"Saved parameter plots: {plot_info['plot_dir']} ({len(plot_info.get('saved', []))} files)")
    elif plot_info.get("error"):
        print(f"Parameter plot generation skipped: {plot_info['error']}")
    if ac_info.get("dir"):
        print(f"Saved AC fingerprint: {ac_info['dir']} ({len(ac_info.get('saved', []))} files)")
    elif ac_info.get("error"):
        print(f"AC fingerprint generation skipped: {ac_info['error']}")
    print(f"Saved best subset: {subset_file}")
    print(f"Saved summary: {summary_path}")
    print(f"Best subset length: {best_metrics['subset_len']}")
    print(f"Self RC violations (<{args.n // 2}): {best_metrics['self_rc_viol']}")
    print(f"Best trial params: {best_params}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optuna search initialized from heuristic_136-style scoring."
    )
    parser.add_argument("--n", type=int, default=8)
    parser.add_argument("--trials", type=int, default=1200)
    parser.add_argument("--time-budget-hours", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--plot-focus-params", type=int, default=6)
    parser.add_argument("--plot-max-pairs", type=int, default=15)
    parser.add_argument(
        "--ac-fingerprint-sample",
        type=int,
        default=600,
        help="Max feasible best-length trials to fingerprint; 0=all, -1=disable.",
    )
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out-dir", type=str, default="plots_136_GPT")
    return parser.parse_args()


if __name__ == "__main__":
    run_search(parse_args())
