#!/usr/bin/env python3
"""
make_results_artifacts.py

Generates LaTeX tables and PDF figures for the Results section.

Inputs:
- panel CSV (one row per year)
- optional cross-sectional CSV (single year, e.g., 2024)
- optional sector lookup CSV (id -> name) for readable ranking tables

This script computes descriptive summary statistics (min/mean/max/std) from
existing panel outputs and formats them as LaTeX tables and figures.

IMPORTANT:
- This script does NOT introduce new model calculations.
- It only summarizes and formats outputs already computed elsewhere.

Expected panel columns (new influence design):
- year
- backward_linkage_Tcc_colsum
- forward_linkage_Tcc_rowsum
- extraction_total_Tcc
- extraction_total_Tii
- influence_delta_total_commodity_output_waterind
- influence_delta_total_industry_output_waterind
- influence_pct_total_commodity_output_waterind
- influence_pct_total_industry_output_waterind
- influence_delta_total_commodity_output_crop
- influence_delta_total_industry_output_crop
- influence_pct_total_commodity_output_crop
- influence_pct_total_industry_output_crop
- influence_delta_total_commodity_output_semi
- influence_delta_total_industry_output_semi
- influence_pct_total_commodity_output_semi
- influence_pct_total_industry_output_semi
- influence_pct_param (input parameter; not a result)
"""

from __future__ import annotations

from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt


# --------------------------------------------------
# Base directory (guaranteed to be script location)
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
TABLE_DIR = RESULTS_DIR / "tables"
FIG_DIR = RESULTS_DIR / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LaTeX table writer (booktabs + caption + label)
# --------------------------------------------------

def write_latex_table(df: pd.DataFrame, path: Path, caption: str, label: str, float_fmt="%.3f"):
    latex_body = df.to_latex(
        index=False,
        escape=False,
        float_format=float_fmt
    )

    latex_full = "\n".join([
        r"\begin{table}[!htbp]",
        r"\centering",
        latex_body.replace(r"\begin{table}", "").replace(r"\end{table}", "").strip(),
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\end{table}",
        ""
    ])

    path.write_text(latex_full)


# --------------------------------------------------
# Plotting helpers
# --------------------------------------------------

def save_figure(fig, name: str) -> Path:
    pdf_path = FIG_DIR / f"{name}.pdf"
    fig.tight_layout()
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return pdf_path


def plot_timeseries(df: pd.DataFrame, x: str, y: str, title: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(
        df[x],
        df[y],
        marker="o",
        linewidth=2,
        markersize=4,
    )
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.set_xlim(df[x].min(), df[x].max())
    return fig


def plot_barh(df: pd.DataFrame, x: str, y: str, title: str, xlabel: str):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(df[x], df[y])
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.3)
    return fig


# --------------------------------------------------
# Summary stats helper
# --------------------------------------------------

def summary_stats(panel: pd.DataFrame, cols: list[str], label_map: dict[str, str] | None = None) -> pd.DataFrame:
    """
    Returns a tidy summary-statistics table (Metric, Minimum, Mean, Maximum, Std. dev.)
    for requested columns if they exist in panel.
    """
    label_map = label_map or {}
    rows = []
    for c in cols:
        if c not in panel.columns:
            continue
        s = pd.to_numeric(panel[c], errors="coerce").dropna()
        if s.empty:
            continue
        rows.append({
            "Metric": label_map.get(c, c),
            "Minimum": s.min(),
            "Mean": s.mean(),
            "Maximum": s.max(),
            "Std. dev.": s.std(ddof=1) if len(s) > 1 else 0.0,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True, help="Path to panel CSV (one row per year)")
    parser.add_argument("--cross", help="Optional cross-sectional CSV (e.g., 2024 ranking)")
    parser.add_argument("--lookup", help="Optional sector lookup CSV with columns: sector_id, sector_name")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--topn", type=int, default=15)
    parser.add_argument(
        "--no_cross_fig",
        action="store_true",
        help="Do not generate the cross-sectional bar figure (default: generate if cross provided)"
    )
    args = parser.parse_args()

    panel = pd.read_csv(args.panel).sort_values("year")

    # Convert extraction totals from millions to billions for plotting and summary tables.
    # This does not change underlying model results; it only harmonizes units with the paper text.
    if "extraction_total_Tcc" in panel.columns:
        panel["extraction_total_Tcc_bn"] = panel["extraction_total_Tcc"] / 1000
    if "extraction_total_Tii" in panel.columns:
        panel["extraction_total_Tii_bn"] = panel["extraction_total_Tii"] / 1000

    # -------------------------
    # 1) Baseline Table (single year) — descriptive only
    # -------------------------

    # NOTE: we treat influence_pct_param as a parameter (not an outcome) and omit it here.
    baseline_cols = [
        "year",
        "backward_linkage_Tcc_colsum",
        "forward_linkage_Tcc_rowsum",
        "extraction_total_Tcc_bn",
        "extraction_total_Tii_bn",
        "influence_delta_total_commodity_output_waterind",
        "influence_delta_total_industry_output_waterind",
        "influence_pct_total_commodity_output_waterind",
        "influence_pct_total_industry_output_waterind",
    ]
    baseline_cols = [c for c in baseline_cols if c in panel.columns]
    baseline_df = panel.loc[panel["year"] == args.year, baseline_cols].copy()

    if not baseline_df.empty:
        baseline_df = baseline_df.rename(columns={
            "extraction_total_Tcc_bn": "extraction_total_Tcc",
            "extraction_total_Tii_bn": "extraction_total_Tii",
        })
        write_latex_table(
            baseline_df,
            TABLE_DIR / f"table_baseline_{args.year}.tex",
            f"Baseline IO structure and propagation metrics ({args.year}).",
            f"tab:baseline_{args.year}",
            float_fmt="%.3f"
        )

    # -------------------------
    # 2) Extraction Figures
    # -------------------------

    made_extraction_tcc = False
    made_extraction_tii = False

    if "extraction_total_Tcc_bn" in panel.columns:
        fig = plot_timeseries(
            panel,
            "year",
            "extraction_total_Tcc_bn",
            "Total extraction over time (Tcc)",
            "Extraction effect ($ billions)"
        )
        save_figure(fig, "fig_extraction_Tcc")
        made_extraction_tcc = True

    if "extraction_total_Tii_bn" in panel.columns:
        fig = plot_timeseries(
            panel,
            "year",
            "extraction_total_Tii_bn",
            "Total extraction over time (Tii)",
            "Extraction effect ($ billions)"
        )
        save_figure(fig, "fig_extraction_Tii")
        made_extraction_tii = True

    # -------------------------
    # 3) Summary table: Linkages + Extraction (1997–2024)
    # -------------------------

    link_extr_cols = [
        "backward_linkage_Tcc_colsum",
        "forward_linkage_Tcc_rowsum",
        "extraction_total_Tcc_bn",
        "extraction_total_Tii_bn",
    ]
    link_extr_labels = {
        "backward_linkage_Tcc_colsum": "Backward linkage (commodity system)",
        "forward_linkage_Tcc_rowsum": "Forward linkage (commodity system)",
        "extraction_total_Tcc_bn": "Extraction (commodity system, $bn)",
        "extraction_total_Tii_bn": "Extraction (industry system, $bn)",
    }
    link_extr_stats = summary_stats(panel, link_extr_cols, link_extr_labels)
    if not link_extr_stats.empty:
        write_latex_table(
            link_extr_stats,
            TABLE_DIR / "table_linkages_extraction_summary.tex",
            "Linkages and hypothetical extraction of the water sector (1997--2024).",
            "tab:linkages_extraction_summary",
            float_fmt="%.3f"
        )

    # -------------------------
    # 4) Summary table: Aggregate Influence (water-industry benchmark, 1997–2024)
    # -------------------------

    agg_inf_cols = [
        "influence_delta_total_commodity_output_waterind",
        "influence_delta_total_industry_output_waterind",
        "influence_pct_total_commodity_output_waterind",
        "influence_pct_total_industry_output_waterind",
    ]
    agg_inf_labels = {
        "influence_delta_total_commodity_output_waterind": "Water-industry shock: Δ commodity output ($bn)",
        "influence_delta_total_industry_output_waterind": "Water-industry shock: Δ industry output ($bn)",
        "influence_pct_total_commodity_output_waterind": "Water-industry shock: Δ commodity output (%)",
        "influence_pct_total_industry_output_waterind": "Water-industry shock: Δ industry output (%)",
    }
    agg_inf_stats = summary_stats(panel, agg_inf_cols, agg_inf_labels)
    if not agg_inf_stats.empty:
        write_latex_table(
            agg_inf_stats,
            TABLE_DIR / "table_influence_aggregate_summary.tex",
            "Aggregate propagation effects under a 10\\% water-intensity perturbation (1997--2024).",
            "tab:influence_aggregate_summary",
            float_fmt="%.3f"
        )

    # -------------------------
    # 5) Summary table: Sectoral Transmission (Crops + Semiconductors)
    # -------------------------

    sector_cols = [
        "influence_delta_total_commodity_output_crop",
        "influence_delta_total_industry_output_crop",
        "influence_pct_total_commodity_output_crop",
        "influence_pct_total_industry_output_crop",
        "influence_delta_total_commodity_output_semi",
        "influence_delta_total_industry_output_semi",
        "influence_pct_total_commodity_output_semi",
        "influence_pct_total_industry_output_semi",
    ]
    sector_labels = {
        "influence_delta_total_commodity_output_crop": "Crops: Δ commodity output ($bn)",
        "influence_delta_total_industry_output_crop": "Crops: Δ industry output ($bn)",
        "influence_pct_total_commodity_output_crop": "Crops: Δ commodity output (%)",
        "influence_pct_total_industry_output_crop": "Crops: Δ industry output (%)",
        "influence_delta_total_commodity_output_semi": "Semiconductors: Δ commodity output ($bn)",
        "influence_delta_total_industry_output_semi": "Semiconductors: Δ industry output ($bn)",
        "influence_pct_total_commodity_output_semi": "Semiconductors: Δ commodity output (%)",
        "influence_pct_total_industry_output_semi": "Semiconductors: Δ industry output (%)",
    }
    sector_stats = summary_stats(panel, sector_cols, sector_labels)
    if not sector_stats.empty:
        write_latex_table(
            sector_stats,
            TABLE_DIR / "table_influence_sectoral_summary.tex",
            "Sectoral transmission under a 10\\% water-intensity perturbation (1997--2024).",
            "tab:influence_sectoral_summary",
            float_fmt="%.3f"
        )

    # -------------------------
    # 6) Cross-sectional (single year) ranking table (Top-N)
    # -------------------------

    made_cross_table = False
    made_cross_fig = False

    lookup = None
    if args.lookup:
        lookup = pd.read_csv(args.lookup, dtype={"sector_id": str})
        if "sector_name" not in lookup.columns or "sector_id" not in lookup.columns:
            raise ValueError("--lookup CSV must have columns: sector_id, sector_name")
        lookup = lookup[["sector_id", "sector_name"]].drop_duplicates()

    if args.cross:
        cross = pd.read_csv(args.cross, dtype={"sector_id": str})

        if "influence_value" not in cross.columns:
            raise ValueError("Cross-sectional CSV must contain 'influence_value' column.")
        if "sector_id" not in cross.columns:
            raise ValueError("Cross-sectional CSV must contain 'sector_id' column.")

        cross = cross.copy()
        if "sector_name" not in cross.columns and lookup is not None:
            cross = cross.merge(lookup, on="sector_id", how="left")

        cross = cross.sort_values("influence_value", ascending=False).head(args.topn).copy()

        if "sector_name" in cross.columns:
            cross["sector_display"] = cross["sector_name"].fillna(cross["sector_id"]) + " (" + cross["sector_id"] + ")"
        else:
            cross["sector_display"] = cross["sector_id"]

        write_latex_table(
            cross[["sector_display", "influence_value"]],
            TABLE_DIR / f"table_influence_top{args.topn}_{args.year}.tex",
            f"Top {args.topn} sectors by output impact under water-intensity perturbation ({args.year}).",
            "tab:cross_section_topn",
            float_fmt="%.3f"
        )
        made_cross_table = True

        if not args.no_cross_fig:
            fig = plot_barh(
                cross.sort_values("influence_value"),
                "sector_display",
                "influence_value",
                f"Cross-sectional structure of influence ({args.year})",
                "Impact (influence value)"
            )
            save_figure(fig, "fig_cross_section_influence")
            made_cross_fig = True

    # -------------------------
    # 7) Master snippet file
    # -------------------------

    snippet_lines = [
        "% Auto-generated Results import file",
        "% Requires: booktabs, graphicx",
        "",
    ]

    # Baseline
    if (TABLE_DIR / f"table_baseline_{args.year}.tex").exists():
        snippet_lines += [rf"\input{{results/tables/table_baseline_{args.year}.tex}}", ""]

    # Linkages + extraction summary
    if (TABLE_DIR / "table_linkages_extraction_summary.tex").exists():
        snippet_lines += [r"\input{results/tables/table_linkages_extraction_summary.tex}", ""]

    # Extraction figures
    if made_extraction_tcc:
        snippet_lines += [
            r"\begin{figure}[!htbp]",
            r"\centering",
            r"\includegraphics[width=0.9\linewidth]{results/figures/fig_extraction_Tcc.pdf}",
            r"\caption{Hypothetical extraction of the water commodity from the commodity-by-commodity input--output system (Tcc), 1997--2024. Values report the total reduction in economy-wide output resulting from removing water as an intermediate commodity input.}",
            r"\label{fig:extraction_tcc}",
            r"\end{figure}",
            "",
        ]
    if made_extraction_tii:
        snippet_lines += [
            r"\begin{figure}[!htbp]",
            r"\centering",
            r"\includegraphics[width=0.9\linewidth]{results/figures/fig_extraction_Tii.pdf}",
            r"\caption{Hypothetical extraction of the water-producing industry from the industry-by-industry input--output system (Tii), 1997--2024. The smaller magnitude reflects the limited scale of the water-producing industry when treated as a single producing sector.}",
            r"\label{fig:extraction_tii}",
            r"\end{figure}",
            "",
        ]

    # Influence aggregate summary
    if (TABLE_DIR / "table_influence_aggregate_summary.tex").exists():
        snippet_lines += [r"\input{results/tables/table_influence_aggregate_summary.tex}", ""]

    # Sectoral transmission summary
    if (TABLE_DIR / "table_influence_sectoral_summary.tex").exists():
        snippet_lines += [r"\input{results/tables/table_influence_sectoral_summary.tex}", ""]

    # Cross-sectional ranking
    if made_cross_table:
        snippet_lines += [rf"\input{{results/tables/table_influence_top{args.topn}_{args.year}.tex}}", ""]
    if made_cross_fig:
        snippet_lines += [
            r"\begin{figure}[!htbp]",
            r"\centering",
            r"\includegraphics[width=0.9\linewidth]{results/figures/fig_cross_section_influence.pdf}",
            r"\caption{Cross-sectional concentration of output impacts under water-intensity perturbation.}",
            r"\label{fig:cross_section_influence}",
            r"\end{figure}",
            "",
        ]

    (RESULTS_DIR / "latex_snippets.tex").write_text("\n".join(snippet_lines))

    print("Done.")
    print(f"Tables written to: {TABLE_DIR}")
    print(f"Figures written to: {FIG_DIR}")
    print(f"LaTeX snippet: {RESULTS_DIR / 'latex_snippets.tex'}")


if __name__ == "__main__":
    main()
