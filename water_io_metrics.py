#!/usr/bin/env python3
"""
water_io_metrics.py

BLS Make–Use Input–Output (IOReal / IONom) utilities

Computes, by year:
  - Linkages (commodity-by-commodity)
  - Hypothetical extraction totals (commodity-by-commodity and industry-by-industry)
  - Economic influence experiments via coefficient perturbation:
      b_{water, target} <- (1 + pct) * b_{water, target}
    for three targets:
      1) water industry (benchmark, "waterind")
      2) crop industry ("crop")
      3) semiconductor industry ("semi")

Outputs:
  - outputs/water_metrics_by_year.csv
      one row per year, including linkages, extraction totals, and influence totals
      for each target scenario (waterind/crop/semi).
  - outputs/influence_detail_commod_<YEAR>_<TARGET>.csv
  - outputs/influence_detail_industr_<YEAR>_<TARGET>.csv

Notes
-----
This script follows the BLS Make–Use derivations:
  B = U g^{-1}
  D = V q^{-1}
  T_cc = (I - B D)^{-1}
  T_ii = (I - D B)^{-1}
and uses the USE table's final demand column as e (commodity final demand).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd


# ----------------------------
# Config
# ----------------------------

IO_DIR = Path(os.environ.get("IO_DIR", ".")).expanduser().resolve()

# Default filenames (BLS zip structure)
USE_XLSX = Path(os.environ.get("USE_XLSX", "REAL_USE.xlsx"))
MAKE_XLSX = Path(os.environ.get("MAKE_XLSX", "REAL_MAKE.xlsx"))

OUT_DIR = Path(os.environ.get("OUT_DIR", "outputs")).expanduser().resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

# BLS sector numbers (as in SectorPlan)
WATER_SECTOR_ID = str(os.environ.get("WATER_SECTOR_ID", "14"))
CROP_SECTOR_ID  = str(os.environ.get("CROP_SECTOR_ID", "1"))
SEMI_SECTOR_ID  = str(os.environ.get("SEMI_SECTOR_ID", "61"))  # adjust if your mapping differs

# Influence experiment: +10% increase in water input coefficient into target industry
INFLUENCE_PCT = float(os.environ.get("INFLUENCE_PCT", "0.10"))  # 0.10 = +10%


# ----------------------------
# Helpers
# ----------------------------

def _to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    """Robust numeric coercion for Excel-imported tables."""
    out = df.copy()
    for c in out.columns:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out

def _invert(mat: np.ndarray, rcond: float = 1e-12) -> np.ndarray:
    """Robust inversion: try inv, else pseudo-inverse."""
    try:
        return np.linalg.inv(mat)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(mat, rcond=rcond)

def _as_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def _strip_totals_if_present(df: pd.DataFrame) -> pd.DataFrame:
    """
    BLS files may include a totals row/column or not, depending on year/file variant.
    We attempt to detect and drop "Total" identifiers if present.
    """
    out = df.copy()
    out = out.dropna(how="all", axis=0).dropna(how="all", axis=1)

    first_col = out.columns[0]
    mask_total_row = out[first_col].astype(str).str.contains(r"total", case=False, na=False)
    if mask_total_row.any():
        out = out.loc[~mask_total_row].copy()

    col_ids = out.columns.astype(str)
    if any(re.search(r"total", c, flags=re.I) for c in col_ids):
        keep_cols = [c for c in out.columns if not re.search(r"total", str(c), flags=re.I)]
        out = out[keep_cols].copy()

    return out

def read_use_make_for_year(use_path: Path, make_path: Path, year: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Read the USE and MAKE sheets for a given year."""
    y = str(year)
    use_raw = pd.read_excel(use_path, sheet_name=y, header=0)
    make_raw = pd.read_excel(make_path, sheet_name=y, header=0)
    use_raw = _strip_totals_if_present(use_raw)
    make_raw = _strip_totals_if_present(make_raw)
    return use_raw, make_raw

def parse_use_table(use_raw: pd.DataFrame) -> Tuple[List[str], List[str], np.ndarray, np.ndarray]:
    """
    Parse BLS USE table with identifiers.

    Returns:
      commodity_ids: length n (typically 176)
      industry_ids: length n (typically 176)
      U: (n x n) intermediate use matrix (commodities x industries)
      e: (n,) commodity final demand vector (from last column)
    """
    df = use_raw.copy()

    row_id_col = df.columns[0]
    row_ids = df[row_id_col].map(_as_str).tolist()

    col_ids_all = [str(c).strip() for c in df.columns[1:]]
    data = _to_numeric_df(df.iloc[:, 1:].copy())

    n_rows, n_cols = data.shape

    if n_rows == n_cols and n_rows >= 2:
        n = n_rows - 1
    else:
        n = min(n_rows, n_cols) - 1

    commodity_ids = row_ids[:n]
    industry_ids = col_ids_all[:n]

    U = data.iloc[:n, :n].to_numpy(dtype=float)
    e = data.iloc[:n, n].to_numpy(dtype=float) if n_cols > n else np.zeros(n)

    return commodity_ids, industry_ids, U, e

def parse_make_table(make_raw: pd.DataFrame) -> Tuple[List[str], List[str], np.ndarray]:
    """
    Parse BLS MAKE table with identifiers.

    Returns:
      industry_ids: length n
      commodity_ids: length n
      V: (n x n) make matrix (industries x commodities)
    """
    df = make_raw.copy()

    row_id_col = df.columns[0]
    industry_ids = df[row_id_col].map(_as_str).tolist()

    col_ids = [str(c).strip() for c in df.columns[1:]]
    data = _to_numeric_df(df.iloc[:, 1:].copy())

    n = min(data.shape[0], data.shape[1])
    industry_ids = industry_ids[:n]
    commodity_ids = col_ids[:n]
    V = data.iloc[:n, :n].to_numpy(dtype=float)

    return industry_ids, commodity_ids, V

def align_ids(commod_use: List[str], industr_use: List[str], industr_make: List[str], commod_make: List[str],
              U: np.ndarray, e: np.ndarray, V: np.ndarray) -> Tuple[List[str], List[str], np.ndarray, np.ndarray, np.ndarray]:
    """Align USE and MAKE on common ids (intersection + ordering by USE)."""
    commod_common = [cid for cid in commod_use if cid in commod_make]
    industr_common = [iid for iid in industr_use if iid in industr_make]

    cu_idx = [commod_use.index(cid) for cid in commod_common]
    cm_idx = [commod_make.index(cid) for cid in commod_common]

    iu_idx = [industr_use.index(iid) for iid in industr_common]
    im_idx = [industr_make.index(iid) for iid in industr_common]

    U2 = U[np.ix_(cu_idx, iu_idx)]
    e2 = e[cu_idx]
    V2 = V[np.ix_(im_idx, cm_idx)]

    return commod_common, industr_common, U2, e2, V2

def drop_zero_outputs(commod_ids: List[str], industr_ids: List[str],
                      U: np.ndarray, e: np.ndarray, V: np.ndarray
                      ) -> Tuple[List[str], List[str], np.ndarray, np.ndarray, np.ndarray]:
    """Drop zero-output commodities/industries to avoid singular diagonal inverses."""
    q = V.sum(axis=0)
    g = V.sum(axis=1)

    keep_c = q > 0
    keep_i = g > 0

    commod_ids2 = [cid for cid, k in zip(commod_ids, keep_c) if k]
    industr_ids2 = [iid for iid, k in zip(industr_ids, keep_i) if k]

    U2 = U[np.ix_(keep_c, keep_i)]
    e2 = e[keep_c]
    V2 = V[np.ix_(keep_i, keep_c)]

    return commod_ids2, industr_ids2, U2, e2, V2

def compute_bd_system(U: np.ndarray, V: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute B, D, A_c=BD, A_i=DB, T_cc, T_ii using BLS equations."""
    q = V.sum(axis=0)
    g = V.sum(axis=1)

    g_hat_inv = np.diag(1.0 / g)
    q_hat_inv = np.diag(1.0 / q)

    B = U @ g_hat_inv
    D = V @ q_hat_inv

    A_c = B @ D
    A_i = D @ B

    T_cc = _invert(np.eye(A_c.shape[0]) - A_c)
    T_ii = _invert(np.eye(A_i.shape[0]) - A_i)

    return B, D, A_c, A_i, T_cc, T_ii

def linkage_measures(T: np.ndarray, target_idx: int) -> Tuple[float, float]:
    """Backward = col sum; Forward = row sum in total requirements matrix."""
    backward = float(T[:, target_idx].sum())
    forward  = float(T[target_idx, :].sum())
    return backward, forward

def hypothetical_extraction_total(A: np.ndarray, y: np.ndarray, target_idx: int) -> float:
    """Dietzenbacher-style hypothetical extraction total impact: sum(x0 - x1)."""
    n = A.shape[0]
    I_n = np.eye(n)
    x0 = _invert(I_n - A) @ y

    A_ex = A.copy()
    diag_val = A_ex[target_idx, target_idx]
    A_ex[target_idx, :] = 0.0
    A_ex[:, target_idx] = 0.0
    A_ex[target_idx, target_idx] = diag_val

    x1 = _invert(I_n - A_ex) @ y
    return float((x0 - x1).sum())

def influence_experiment(B: np.ndarray, D: np.ndarray, e: np.ndarray,
                         commod_ids: List[str], industr_ids: List[str],
                         water_sector_id: str, target_industry_id: str,
                         pct_increase: float = 0.10
                         ) -> Dict[str, object]:
    """
    Influence experiment: increase water input coefficient into TARGET industry in B by pct_increase.

    b_{water, target} <- b_{water, target} * (1 + pct_increase)
    """
    try:
        w_c = commod_ids.index(water_sector_id)
        t_i = industr_ids.index(target_industry_id)
    except ValueError:
        return {"ok": False, "reason": "water or target sector not present after filtering"}

    # Baseline outputs
    A_c0 = B @ D
    T_cc0 = _invert(np.eye(A_c0.shape[0]) - A_c0)
    q0 = T_cc0 @ e

    A_i0 = D @ B
    y_i = D @ e
    T_ii0 = _invert(np.eye(A_i0.shape[0]) - A_i0)
    g0 = T_ii0 @ y_i

    # Perturb
    B1 = B.copy()
    B1[w_c, t_i] *= (1.0 + pct_increase)

    A_c1 = B1 @ D
    T_cc1 = _invert(np.eye(A_c1.shape[0]) - A_c1)
    q1 = T_cc1 @ e

    A_i1 = D @ B1
    T_ii1 = _invert(np.eye(A_i1.shape[0]) - A_i1)
    g1 = T_ii1 @ y_i

    dq = q1 - q0
    dg = g1 - g0

    pct_q = 100.0 * float(dq.sum() / q0.sum()) if q0.sum() != 0 else np.nan
    pct_g = 100.0 * float(dg.sum() / g0.sum()) if g0.sum() != 0 else np.nan

    return {
        "ok": True,
        "target_industry_id": target_industry_id,
        "water_commod_idx": w_c,
        "target_industry_idx": t_i,
        "delta_q": dq,
        "delta_g": dg,
        "delta_q_total": float(dq.sum()),
        "delta_g_total": float(dg.sum()),
        "pct_total_commodity_output": pct_q,
        "pct_total_industry_output": pct_g,
    }


# ----------------------------
# Main run
# ----------------------------

def run(years: List[int]) -> pd.DataFrame:
    use_path = (IO_DIR / USE_XLSX).resolve()
    make_path = (IO_DIR / MAKE_XLSX).resolve()

    rows = []

    for year in years:
        use_raw, make_raw = read_use_make_for_year(use_path, make_path, year)

        commod_use, industr_use, U, e = parse_use_table(use_raw)
        industr_make, commod_make, V = parse_make_table(make_raw)

        commod_ids, industr_ids, U2, e2, V2 = align_ids(commod_use, industr_use, industr_make, commod_make, U, e, V)
        commod_ids3, industr_ids3, U3, e3, V3 = drop_zero_outputs(commod_ids, industr_ids, U2, e2, V2)

        B, D, A_c, A_i, T_cc, T_ii = compute_bd_system(U3, V3)

        # Identify water sector in commodity space
        if WATER_SECTOR_ID in commod_ids3:
            water_idx_c = commod_ids3.index(WATER_SECTOR_ID)
        else:
            water_idx_c = None

        # Linkages from T_cc
        if water_idx_c is not None:
            backward_cc, forward_cc = linkage_measures(T_cc, water_idx_c)
        else:
            backward_cc, forward_cc = (np.nan, np.nan)

        # Extraction totals
        if water_idx_c is not None:
            extraction_cc_total = hypothetical_extraction_total(A_c, e3, water_idx_c)
        else:
            extraction_cc_total = np.nan

        # Industry system extraction uses y_i = D e
        if WATER_SECTOR_ID in industr_ids3:
            water_idx_i = industr_ids3.index(WATER_SECTOR_ID)
            y_i = D @ e3
            extraction_ii_total = hypothetical_extraction_total(A_i, y_i, water_idx_i)
        else:
            extraction_ii_total = np.nan

        # Influence experiments
        infl_waterind = influence_experiment(B, D, e3, commod_ids3, industr_ids3,
                                             WATER_SECTOR_ID, WATER_SECTOR_ID, pct_increase=INFLUENCE_PCT)
        infl_crop     = influence_experiment(B, D, e3, commod_ids3, industr_ids3,
                                             WATER_SECTOR_ID, CROP_SECTOR_ID, pct_increase=INFLUENCE_PCT)
        infl_semi     = influence_experiment(B, D, e3, commod_ids3, industr_ids3,
                                             WATER_SECTOR_ID, SEMI_SECTOR_ID, pct_increase=INFLUENCE_PCT)

        def _totals_or_nan(infl: Dict[str, object]):
            if infl.get("ok", False):
                return (
                    float(infl["delta_q_total"]),
                    float(infl["delta_g_total"]),
                    float(infl["pct_total_commodity_output"]),
                    float(infl["pct_total_industry_output"]),
                )
            return (np.nan, np.nan, np.nan, np.nan)

        dq_w, dg_w, pctq_w, pctg_w = _totals_or_nan(infl_waterind)
        dq_c, dg_c, pctq_c, pctg_c = _totals_or_nan(infl_crop)
        dq_s, dg_s, pctq_s, pctg_s = _totals_or_nan(infl_semi)

        # Write detailed deltas for each target (useful for cross-sectional ranking in 2024)
        def _write_details(infl: Dict[str, object], tag: str):
            if not infl.get("ok", False):
                return
            pd.DataFrame({"sector_id": commod_ids3, "delta_commodity_output": infl["delta_q"]}) \
              .to_csv(OUT_DIR / f"influence_detail_commod_{year}_{tag}.csv", index=False)
            pd.DataFrame({"sector_id": industr_ids3, "delta_industry_output": infl["delta_g"]}) \
              .to_csv(OUT_DIR / f"influence_detail_industr_{year}_{tag}.csv", index=False)

        _write_details(infl_waterind, "waterind")
        _write_details(infl_crop, "crop")
        _write_details(infl_semi, "semi")

        rows.append({
            "year": year,
            "water_sector_id": WATER_SECTOR_ID,

            "backward_linkage_Tcc_colsum": backward_cc,
            "forward_linkage_Tcc_rowsum": forward_cc,

            "extraction_total_Tcc": extraction_cc_total,
            "extraction_total_Tii": extraction_ii_total,

            # input parameter (for transparency)
            "influence_pct_param": INFLUENCE_PCT,

            # computed outcomes by target
            "influence_pct_total_commodity_output_waterind": pctq_w,
            "influence_pct_total_industry_output_waterind": pctg_w,
            "influence_delta_total_commodity_output_waterind": dq_w,
            "influence_delta_total_industry_output_waterind": dg_w,

            "influence_pct_total_commodity_output_crop": pctq_c,
            "influence_pct_total_industry_output_crop": pctg_c,
            "influence_delta_total_commodity_output_crop": dq_c,
            "influence_delta_total_industry_output_crop": dg_c,

            "influence_pct_total_commodity_output_semi": pctq_s,
            "influence_pct_total_industry_output_semi": pctg_s,
            "influence_delta_total_commodity_output_semi": dq_s,
            "influence_delta_total_industry_output_semi": dg_s,

            "n_commodities": len(commod_ids3),
            "n_industries": len(industr_ids3),
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "water_metrics_by_year.csv", index=False)
    return out


if __name__ == "__main__":
    use_path = (IO_DIR / USE_XLSX).resolve()

    try:
        xl = pd.ExcelFile(use_path)
        years = sorted(int(s.strip()) for s in xl.sheet_names if re.fullmatch(r"\d{4}", str(s).strip()))
    except Exception:
        years = list(range(1997, 2025))

    df = run(years)
    print(df.tail())
