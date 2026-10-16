#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import html
import re
import pickle
import sys
import types
from pathlib import Path
from IPython.display import display as ipy_display

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from experimental.exp_plotting import save_csv_ratings

CORR_METHODS = ("pearson", "spearman", "kendall")
HOUSE_PURPLE = "#6c4ca8"
HOUSE_PURPLE_DARK = "#2f2149"
HOUSE_GRID = "#d7d0e6"
HOUSE_GUIDE = "#5a5369"
PLOT_RC = {
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.titlesize": 11.5,
    "axes.titleweight": "semibold",
    "axes.labelsize": 11,
    "axes.labelcolor": HOUSE_PURPLE_DARK,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "xtick.color": HOUSE_PURPLE_DARK,
    "ytick.color": HOUSE_PURPLE_DARK,
    "grid.color": HOUSE_GRID,
    "grid.linewidth": 0.8,
    "grid.alpha": 0.24,
    "axes.edgecolor": "#d8d2e7",
    "axes.linewidth": 0.8,
}

LMA_NAME_PAIRS = [
    ("claude-opus-4-6", "claude_opus_4.6"),
    ("claude-opus-4-5-20251101", "claude_opus_4.5"),
    ("glm-5", "glm_5"),
    ("gemini-3-pro", "gemini_3_pro_preview"),
    ("gemini-3-flash", "gemini_3_flash_preview"),
    ("glm-4.7", "glm_4.7"),
    ("kimi-k2.5-thinking", "kimi_k2.5"),
    ("minimax-m2.1-preview", "minimax_m2.1"),
    ("gpt-5.2", "gpt_5.2"),
    ("claude-sonnet-4-5-20250929", "claude_sonnet_4.5"),
    ("mimo-v2-flash (non-thinking)", "mimo_v2_flash"),
    ("gpt-5.2-codex", "gpt_5.2_codex"),
    ("kimi-k2-thinking-turbo", "kimi_k2_thinking"),
    ("minimax-m2", "minimax_m2"),
    ("deepseek-v3.2", "deepseek_v3.2"),
    ("qwen3-coder-480b-a35b-instruct", "qwen3_coder"),
    ("KAT-Coder-Pro-V1", "kat_coder_pro"),
    ("grok-code-fast-1", "grok_code_fast_1"),
    ("devstral-medium-2507", "devstral_2512"),
    ("gpt-5.5-high", "gpt_5.5_high"),
    ("gpt-5.5-high (codex-harness)", "gpt_5.5_high"),
    ("gpt-5.5-instant", "gpt_5.5_instant"),
    ("gpt-oss-120b", "gpt_oss_120b"),
    ("gpt-5.4-high", "gpt_5.4_high"),
    ("gpt-5.4-high (codex-harness)", "gpt_5.4_high"),
    ("gpt-5.4", "gpt_5.4_instant"),
    ("gpt-5.4-medium (codex-harness)", "gpt_5.4_medium"),
    ("qwen3-next-80b-a3b-instruct", "qwen3_next_80b_a3b_instruct"),
    ("qwen3-32b", "qwen3_32b"),
    ("qwen3-235b-a22b-instruct-2507", "qwen3_235b_a22b_2507"),
    ("gemini-2.0-flash-001", "gemini_2.0_flash_001"),
    ("deepseek-v3-0324", "deepseek_chat_v3_0324"),
    ("claude-opus-4-7-thinking", "claude_opus_4.7_high"),



    # Not in Strautomata
    ("claude-opus-4-6-thinking", None),
    ("gpt-5.2-high", None),
    ("claude-opus-4-5-20251101-thinking-32k", None),
    ("kimi-k2.5-instant", None),
    ("gemini-3-flash (thinking-minimal)", None),
    ("gpt-5-medium", None),
    ("claude-opus-4-1-20250805", None),
    ("gpt-5.1-medium", None),
    ("claude-sonnet-4-5-20250929-thinking-32k", None),
    ("deepseek-v3.2-thinking", None),
    ("glm-4.6", None),
    ("gpt-5.1", None),
    ("gpt-5.1-codex", None),
    ("claude-haiku-4-5-20251001", None),
    ("deepseek-v3.2-exp", None),
    ("gpt-5.1-codex-mini", None),
    ("grok-4-1-fast-reasoning", None),
    ("mistral-large-3", None),
    ("gemini-2.5-pro", None),
    ("grok-4.1-thinking", None),
    ("devstral-2", None),
    ("grok-4-fast-reasoning", None),

    # Not in LM Code Arena
    (None, "gpt_5.4_low"),
    (None, "gpt_5.4_nano"),
    (None, "gpt_5.5_low"),
    (None, "gpt_5.5_medium"),
    (None, "gpt_5.5_xhigh"),
    (None, "gpt_4o_mini"),
    (None, "gpt_5_mini"),
    (None, "deepseek_r1t2_chimera_free"),
    (None, "tng_r1t_chimera_free"),
    (None, "nemotron_nano_12b_v2_vl_free"),
    (None, "trinity_mini_free"),
    (None, "ministral_14b_2512"),
    (None, "solar_pro_3_free"),
    (None, "qwen3_coder_30b_a3b_instruct"),
    (None, "random"),
]


SWE_BASH_NAME_PAIRS = [
    ("Claude 4.5 Opus medium (20251101)", "claude_opus_4.5"),
    ("Gemini 3 Pro Preview (2025-11-18)", "gemini_3_pro_preview"),
    ("GPT-5.2 (2025-12-11) (high reasoning)", None),
    ("Claude 4.5 Sonnet (20250929)", "claude_sonnet_4.5"),
    ("Claude Opus 4.6", "claude_opus_4.6"),
    ("GPT-5.2 (2025-12-11)", "gpt_5.2"),
    ("GPT-5-2 Codex", "gpt_5.2_codex"),
    ("o4-mini (2025-04-16)", "gpt_4o_mini"),
    ("Claude 4 Opus (20250514)", None),
    ("GPT-5.1-codex (medium reasoning)", None),
    ("GPT-5.1 (2025-11-13) (medium reasoning)", None),
    ("GPT-5 (2025-08-07) (medium reasoning)", None),
    ("Claude 4 Sonnet (20250514)", None),
    ("Kimi K2 Thinking", "kimi_k2_thinking"),
    ("Minimax M2", "minimax_m2"),
    ("DeepSeek V3.2 Reasoner", "deepseek_v3.2"),
    ("GPT-5 mini (2025-08-07) (medium reasoning)", "gpt_5_mini"),
    ("o3 (2025-04-16)", None),
    ("Devstral small (2512)", None),
    ("Qwen3-Coder 480B/A35B Instruct", "qwen3_coder"),
    ("GLM-5 (high reasoning)", "glm_5"),
    ("GLM-4.6 (T=1)", None),
    ("GLM-4.5 (2025-08-22)", None),
    ("Devstral (2512)", "devstral_2512"),
    ("Gemini 2.5 Pro (2025-05-06)", None),
    ("Claude 3.7 Sonnet (20250219)", None),
    ("Kimi K2 Instruct", None),
    ("GPT-4.1 (2025-04-14)", None),
    ("GPT-5 nano (2025-08-07) (medium reasoning)", None),
    ("Gemini 2.5 Flash (2025-04-17)", None),
    ("gpt-oss-120b", "gpt_oss_120b"),
    ("GPT-4.1-mini (2025-04-14)", None),
    ("GPT-4o (2024-11-20)", None),
    ("Llama 4 Maverick Instruct", None),
    ("Gemini 2.0 flash", "gemini_2.0_flash_001"),
    ("Llama 4 Scout Instruct", None),
    ("Qwen2.5-Coder 32B Instruct", None),
]




def _resolve_source_name(
    name: str,
    *,
    available_source_names: list[str] | set[str],
    pair_table: list[tuple[str | None, str | None]],
    source_label: str,
) -> str:
    available = {str(source_name) for source_name in available_source_names}
    matches = sorted(
        {
            str(source_name)
            for source_name, real_name in pair_table
            if real_name == name and source_name is not None and str(source_name) in available
        }
    )
    if len(matches) == 0:
        return name
    if len(matches) != 1:
        print(f"expected 1 {source_label} match for {name}, got {matches}")
        return name
    return matches[0]


def name_to_lma_name(name: str, all_lma_names: list[str] | set[str]) -> str:
    return _resolve_source_name(
        name,
        available_source_names=all_lma_names,
        pair_table=LMA_NAME_PAIRS,
        source_label="LM Arena",
    )


def name_to_swe_bash_name(name: str, all_swe_names: list[str] | set[str]) -> str:
    return _resolve_source_name(
        name,
        available_source_names=all_swe_names,
        pair_table=SWE_BASH_NAME_PAIRS,
        source_label="SWE-bench Bash-Only",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LM Arena / SWE-bench comparison utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lma = subparsers.add_parser("lma", help="Run LM Arena vs Strautomata comparisons.")
    lma.add_argument("--pkl", type=Path, required=True, help="Path to Strautomata results pickle.")
    lma.add_argument("--out-dir", type=Path, required=True, help="Output directory for comparison plot.")
    lma.add_argument("--corr-type", choices=["kendall", "spearman", "pearson"], default="spearman", help="Correlation method shown in plot titles.")
    lma.add_argument("--show-lma-table", action="store_true", help="Print parsed LM Arena table to stdout before merging.")

    swe = subparsers.add_parser("swe", help="Parse SWE-bench leaderboard JSON from HTML.")
    swe.add_argument("--pkl", type=Path, required=True, help="Path to Strautomata results pickle.")
    swe.add_argument("--out-dir", type=Path, required=True, help="Output directory for SWE vs Strautomata outputs.")
    swe.add_argument("--html", type=Path, required=True, help="Path to SWE-bench HTML file.")
    swe.add_argument("--corr-type", choices=["kendall", "spearman", "pearson"], default="spearman", help="Correlation method shown in plot titles.")

    demo = subparsers.add_parser("demo-plot", help="Generate dummy comparison plots to preview the styling.")
    demo.add_argument(
        "--out-dir",
        type=Path,
        default=Path("experimental/lm_arena/demo_plot"),
        help="Output directory for dummy style preview plots.",
    )
    return parser.parse_args()


def _decode_json_string(value: str) -> str:
    # Decode escaped sequences that may appear in embedded JSON strings.
    return json.loads(f'"{value}"')


def extract_rows(html_text: str, keep_duplicates: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    escaped_entry_re = re.compile(
        r'\\"modelDisplayName\\":\\"(?P<model>(?:\\\\.|[^"\\])+)\\",'
        r'\\"rating\\":(?P<rating>-?\d+(?:\.\d+)?)'
    )
    for entry in escaped_entry_re.finditer(html_text):
        model = _decode_json_string(entry.group("model"))
        rating = float(entry.group("rating"))
        rows.append({"model": model, "elo": rating})

    # Rendered-table fallback seen in files like overall_sc.html.
    table_row_re = re.compile(
        r'title="(?P<model>[^"]+)".{0,2000}?'
        r'<span class="text-sm">(?P<rating>[\d,]+(?:\.\d+)?)</span>'
        r'<span class="text-tertiary text-xs">±',
        re.DOTALL,
    )
    if not rows:
        for entry in table_row_re.finditer(html_text):
            model = html.unescape(entry.group("model")).strip()
            rating_text = entry.group("rating").replace(",", "")
            rating = float(rating_text)
            rows.append({"model": model, "elo": rating})

    rows.sort(key=lambda row: row["elo"], reverse=True)
    if keep_duplicates:
        return rows

    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        deduped.setdefault(str(row["model"]), row)
    return list(deduped.values())


def write_rows(rows: list[dict[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = out_path.suffix.lower()
    if suffix == ".json":
        out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return
    if suffix == ".csv":
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["model", "elo"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return
    raise SystemExit("Unsupported --out suffix. Use .csv or .json.")


def load_strautomata_df(pkl_path: Path) -> pd.DataFrame:
    with pkl_path.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid pickle payload type: expected dict, got {type(payload).__name__}")
    results = payload.get("results_models")
    if not isinstance(results, dict) or not results:
        results = payload.get("results")
    if not isinstance(results, dict) or not results:
        raise ValueError(
            f"Input pickle missing usable results. Expected non-empty 'results_models' "
            f"(preferred) or legacy 'results'. Found keys: {sorted(payload.keys())}"
        )
    rating_df, _ = save_csv_ratings(results, None)
    rating_df['strautomata'] = rating_df.median(axis=1, skipna=True)
    rating_df = rating_df.sort_values(by='strautomata', ascending=False)
    rating_df = rating_df[['strautomata']].reset_index().rename(columns={'index': 'strautomata_name'})
    return rating_df

def load_lma_df(html_path: Path, show_table: bool = False) -> pd.DataFrame:
    rows = extract_rows(html_path.read_text(encoding="utf-8", errors="replace"), keep_duplicates=False)
    df = pd.DataFrame(rows).rename(columns={"elo": "lma"})
    df['lma_name'] = df['model']
    df = df.sort_values(by='lma', ascending=False).reset_index(drop=True)
    if show_table:
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
            ipy_display(df.sort_values(by="model", ascending=True))
    return df


def parse_swebench_leaderboard_data(html_path: Path) -> list[dict[str, object]]:
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r'<script[^>]*type="application/json"[^>]*id="leaderboard-data"[^>]*>(?P<json>.*?)</script>',
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise ValueError(f'Could not find <script id="leaderboard-data"> in {html_path}')
    payload = match.group("json").strip()
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("Expected leaderboard-data JSON to be a list.")
    return data


def load_swe_bash_df(html_path: Path, mean=450, scale=1800) -> pd.DataFrame:
    data = parse_swebench_leaderboard_data(html_path)
    bash_only = next((section for section in data if section.get("name") == "bash-only"), None)
    if bash_only is None:
        raise ValueError("Could not find bash-only section in SWE leaderboard-data.")
    results = bash_only.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Expected bash-only results to be a list.")
    rows = []
    for result in results:
        if not isinstance(result, dict):
            continue
        name = result.get("name")
        resolved = result.get("resolved")
        if name is None or resolved is None:
            continue
        rows.append({"model": str(name), "lma": float(resolved)})
    df = pd.DataFrame(rows)
    df["lma_name"] = df["model"]
    df["lma"] = ((df["lma"] / 100.0) * float(scale)) + float(mean)
    df = df.sort_values(by="lma", ascending=False).reset_index(drop=True)
    return df


def save_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    title: str,
    out_path: Path,
    rank_mode: bool = False,
) -> None:
    n = len(df)
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    plot_df = df.assign(_x=x, _y=y).dropna(subset=["_x", "_y"]).reset_index(drop=True)
    if plot_df.empty:
        print(f"Skipping empty plot: {out_path}")
        return

    x_vals = plot_df["_x"].to_numpy(dtype=float)
    y_vals = plot_df["_y"].to_numpy(dtype=float)
    min_xy = float(min(np.min(x_vals), np.min(y_vals)))
    max_xy = float(max(np.max(x_vals), np.max(y_vals)))

    with plt.style.context("seaborn-v0_8-whitegrid"), plt.rc_context(PLOT_RC):
        fig, ax = plt.subplots(figsize=(6.6, 5.0))
        annotation_texts = []
        ax.scatter(
            x_vals,
            y_vals,
            s=54 if not rank_mode else 50,
            alpha=0.88,
            color=HOUSE_PURPLE,
            edgecolors="white",
            linewidths=0.85,
            zorder=3,
        )

        for xi, yi, label in zip(x_vals, y_vals, plot_df["model"], strict=True):
            txt = ax.annotate(
                str(label),
                (xi, yi),
                textcoords="offset points",
                xytext=(4, 4),
                ha="left",
                va="bottom",
                fontsize=7.4,
                color=HOUSE_PURPLE_DARK,
                alpha=0.96,
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.86,
                },
                zorder=4,
            )
            annotation_texts.append(txt)

        ax.plot(
            [min_xy, max_xy],
            [min_xy, max_xy],
            color=HOUSE_GUIDE,
            linestyle="--",
            linewidth=1.25,
            alpha=0.8,
            zorder=2,
        )
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title, pad=7)
        ax.grid(axis="both", alpha=0.22, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            handles=[Line2D([], [], linestyle="none", label=f"n={n}")],
            loc="best",
            frameon=False,
            handlelength=0,
            handletextpad=0.2,
            borderpad=0.15,
            fontsize=8.5,
        )

        if rank_mode:
            max_rank = int(max_xy)
            current_xticks = [int(t) for t in ax.get_xticks() if 1 <= t <= max_rank]
            current_yticks = [int(t) for t in ax.get_yticks() if 1 <= t <= max_rank]
            ax.set_xticks(sorted(set(current_xticks + [1, max_rank])))
            ax.set_yticks(sorted(set(current_yticks + [1, max_rank])))
            ax.set_xlim(max_rank + 0.5, 0.5)
            ax.set_ylim(max_rank + 0.5, 0.5)
        else:
            x_span = float(np.ptp(x_vals)) if len(x_vals) > 1 else 0.0
            y_span = float(np.ptp(y_vals)) if len(y_vals) > 1 else 0.0
            x_pad = max(15.0, 0.05 * max(x_span, 1.0))
            y_pad = max(15.0, 0.05 * max(y_span, 1.0))
            ax.set_xlim(float(np.min(x_vals)) - x_pad, float(np.max(x_vals)) + x_pad)
            ax.set_ylim(float(np.min(y_vals)) - y_pad, float(np.max(y_vals)) + y_pad)

        fig.tight_layout()
        if annotation_texts:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            ax_bbox = ax.get_window_extent(renderer=renderer)
            overflow_left = max(
                max(ax_bbox.x0 - txt.get_window_extent(renderer=renderer).x0, 0.0)
                for txt in annotation_texts
            )
            overflow_right = max(
                max(txt.get_window_extent(renderer=renderer).x1 - ax_bbox.x1, 0.0)
                for txt in annotation_texts
            )
            overflow_px = max(overflow_left, overflow_right)
            if overflow_px > 0.5:
                y_center_px = 0.5 * (ax_bbox.y0 + ax_bbox.y1)
                data_left = ax.transData.inverted().transform((ax_bbox.x0, y_center_px))[0]
                data_outer = ax.transData.inverted().transform((ax_bbox.x0 - (overflow_px + 4.0), y_center_px))[0]
                x_pad_data = abs(float(data_outer - data_left))
                x0, x1 = ax.get_xlim()
                if x0 < x1:
                    ax.set_xlim(x0 - x_pad_data, x1 + x_pad_data)
                else:
                    ax.set_xlim(x0 + x_pad_data, x1 - x_pad_data)
                fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)


def _build_demo_df() -> pd.DataFrame:
    rows = [
        {"model": "Claude Opus 4.7", "lma": 1492.0, "strautomata": 1638.0},
        {"model": "GPT-5.5 High Extremely Long Extremely Long", "lma": 1518.0, "strautomata": 1669.0},
        {"model": "Gemini 3 Pro", "lma": 1460.0, "strautomata": 1608.0},
        {"model": "GLM-5", "lma": 1441.0, "strautomata": 1580.0},
        {"model": "Kimi K2.5", "lma": 1410.0, "strautomata": 1558.0},
        {"model": "Qwen3 Next 80B", "lma": 1388.0, "strautomata": 1525.0},
        {"model": "MiniMax M2.1", "lma": 1368.0, "strautomata": 1505.0},
        {"model": "Random", "lma": 1184.0, "strautomata": 1322.0},
    ]
    demo_df = pd.DataFrame(rows)
    demo_df["strautomata_rank"] = demo_df["strautomata"].rank(method="min", ascending=False).astype(int)
    demo_df["lma_rank"] = demo_df["lma"].rank(method="min", ascending=False).astype(int)
    return demo_df


def run_demo_plot(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    demo_df = _build_demo_df()
    save_plot(
        demo_df,
        x_col="lma",
        y_col="strautomata",
        x_label="Demo Source ELO",
        y_label="Demo Strautomata ELO",
        title="Demo Comparison ELO",
        out_path=args.out_dir / "demo_comparison_elo.pdf",
    )
    save_plot(
        demo_df,
        x_col="lma_rank",
        y_col="strautomata_rank",
        x_label="Demo Source Rank (1=best)",
        y_label="Demo Strautomata Rank (1=best)",
        title="Demo Comparison Rank",
        out_path=args.out_dir / "demo_comparison_rank.pdf",
        rank_mode=True,
    )
    print(f"saved_demo_elo={args.out_dir / 'demo_comparison_elo.pdf'}")
    print(f"saved_demo_rank={args.out_dir / 'demo_comparison_rank.pdf'}")


def _print_pairing_summary(full_df: pd.DataFrame, source_label: str) -> None:
    if full_df.empty:
        print(f"{source_label} pairings: none")
        return
    print(f"{source_label} pairings (HTML model -> Strautomata model):")
    pairing_df = full_df.copy()
    if "lma_name" in pairing_df.columns:
        html_col = "lma_name"
    elif "swe_name" in pairing_df.columns:
        html_col = "swe_name"
    else:
        html_col = "model"
    pairing_df = pairing_df.sort_values(by=html_col, ascending=True, na_position="last")
    for _, row in pairing_df.iterrows():
        html_name = row.get(html_col)
        if pd.isna(html_name):
            continue
        strautomata_name = row.get("strautomata_name")
        paired = str(strautomata_name) if pd.notna(strautomata_name) else "(no Strautomata match)"
        print(f"  {html_name} -> {paired}")


def _print_strautomata_models_missing_from_pairs(
    rating_df: pd.DataFrame,
    *,
    pair_table: list[tuple[str | None, str | None]],
    source_label: str,
) -> None:
    paired_real_names = {
        str(real_name)
        for _source_name, real_name in pair_table
        if real_name is not None
    }
    missing = sorted(
        {
            str(name)
            for name in rating_df["strautomata_name"].dropna().astype(str)
            if str(name) not in paired_real_names
        }
    )
    print(f"Strautomata models missing from {source_label} name pairs ({len(missing)}):")
    for name in missing:
        print(f"  {name}")


def merge_and_save(
    rating_df: pd.DataFrame,
    lma_df: pd.DataFrame,
    out_path: Path,
    model_name_mapper,
    source_label: str = "LM Code Arena",
    source_csv_prefix: str = "lma",
) -> pd.DataFrame:
    available_source_names = lma_df["model"].dropna().astype(str).tolist()
    rating_merge_df = rating_df.copy()
    rating_merge_df["source_model"] = rating_merge_df["strautomata_name"].astype(str).apply(
        lambda name: model_name_mapper(name, available_source_names)
    )
    full_df = pd.merge(
        rating_merge_df,
        lma_df,
        left_on="source_model",
        right_on="model",
        how="outer",
    )[['model', 'source_model', 'strautomata_name', 'lma_name', 'strautomata', 'lma']]
    full_df["model"] = full_df["model"].fillna(full_df["source_model"])
    full_df = full_df.drop(columns=["source_model"])
    assert isinstance(full_df, pd.DataFrame), "df is not a DataFrame"
    _print_pairing_summary(full_df, source_label)
    print("Missing from Strautomata", len(full_df[full_df['strautomata'].isna()]))
    print(f"Missing from {source_label}", len(full_df[full_df['lma'].isna()]))
    print("Shared", len(full_df[full_df['strautomata'].notna() & full_df['lma'].notna()]))

    shared_df = full_df.dropna(subset=['strautomata', 'lma']).reset_index(drop=True)
    shared_df['strautomata_rank'] = shared_df['strautomata'].rank(method='min', ascending=False).astype(int)
    shared_df['lma_rank'] = shared_df['lma'].rank(method='min', ascending=False).astype(int)

    rank_df = shared_df[['model', 'strautomata_rank', 'lma_rank']]
    full_df = full_df.merge(rank_df, on='model', how='left')
    full_df['strautomata_rank'] = full_df['strautomata_rank'].astype('Int64')
    full_df['lma_rank'] = full_df['lma_rank'].astype('Int64')
    save_df = full_df.rename(
        columns={
            "lma_name": f"{source_csv_prefix}_name",
            "lma": source_csv_prefix,
            "lma_rank": f"{source_csv_prefix}_rank",
        }
    )
    save_df.to_csv(out_path, index=False)
    return shared_df


def _corr_triplet(df: pd.DataFrame, x_col: str, y_col: str) -> dict[str, float]:
    return {method: df[x_col].corr(df[y_col], method=method) for method in CORR_METHODS}


def _print_all_corrs(df: pd.DataFrame, label: str) -> tuple[dict[str, float], dict[str, float]]:
    elo_corrs = _corr_triplet(df, "lma", "strautomata")
    rank_corrs = _corr_triplet(df, "lma_rank", "strautomata_rank")
    print(
        f"{label} | "
        f"ELO pearson={elo_corrs['pearson']:.2f} | "
        f"Rank pearson={rank_corrs['pearson']:.2f} | "
        f"spearman={elo_corrs['spearman']:.2f} | "
        f"kendall={elo_corrs['kendall']:.2f}"
    )
    return elo_corrs, rank_corrs


def run_lma(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rating_df = load_strautomata_df(args.pkl)
    _print_strautomata_models_missing_from_pairs(
        rating_df,
        pair_table=LMA_NAME_PAIRS,
        source_label="LM Arena",
    )
    corr_method = args.corr_type

    lma_df = load_lma_df(Path('experimental/lm_arena/html/code.html'), show_table=args.show_lma_table)
    df = merge_and_save(
        rating_df,
        lma_df,
        args.out_dir / 'lm_code_arena_vs_strautomata.csv',
        model_name_mapper=name_to_lma_name,
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "LM Code Arena (WebDev)")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    df_elo = df.copy()
    df_elo['lma'] += 200
    save_plot(df_elo, x_col='lma', y_col='strautomata', out_path=args.out_dir / 'lm_code_arena_vs_strautomata.pdf', x_label='LM Code Arena | WebDev ELO (+200)', y_label='Strautomata ELO', title=f'LM Code Arena (WebDev) vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})')
    save_plot(df, x_col='lma_rank', y_col='strautomata_rank', out_path=args.out_dir / 'lm_code_arena_vs_strautomata_rank.pdf', x_label='LM Code Arena Rank (1=best)', y_label='Strautomata Rank (1=best)', title=f'LM Code Arena (WebDev) vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})', rank_mode=True)

    lma_df = load_lma_df(Path('experimental/lm_arena/html/overall_sc.html'), show_table=args.show_lma_table)
    df = merge_and_save(
        rating_df,
        lma_df,
        args.out_dir / 'lm_arena_overall_sc_vs_strautomata.csv',
        model_name_mapper=name_to_lma_name,
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "LM Arena Overall SC")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    df_elo = df.copy()
    m = df_elo['lma'].mean()
    df_elo['lma'] = (df_elo['lma'] - m) * 2 + m + 300
    save_plot(df_elo, x_col='lma', y_col='strautomata', out_path=args.out_dir / 'lm_arena_overall_sc_vs_strautomata.pdf', x_label='LM Arena Overall SC ELO (scaled)', y_label='Strautomata ELO', title=f'LM Arena Overall SC vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})')
    save_plot(df, x_col='lma_rank', y_col='strautomata_rank', out_path=args.out_dir / 'lm_arena_overall_sc_vs_strautomata_rank.pdf', x_label='LM Arena Overall SC Rank (1=best)', y_label='Strautomata Rank (1=best)', title=f'LM Arena Overall SC vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})', rank_mode=True)

    lma_df = load_lma_df(Path('experimental/lm_arena/html/overall_no_sc.html'), show_table=args.show_lma_table)
    df = merge_and_save(
        rating_df,
        lma_df,
        args.out_dir / 'lm_arena_overall_no_sc_vs_strautomata.csv',
        model_name_mapper=name_to_lma_name,
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "LM Arena Overall No SC")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    df_elo = df.copy()
    df_elo['lma'] = (df_elo['lma'] - m) * 2 + m + 300
    save_plot(df_elo, x_col='lma', y_col='strautomata', out_path=args.out_dir / 'lm_arena_overall_no_sc_vs_strautomata.pdf', x_label='LM Arena Overall No SC ELO (scaled)', y_label='Strautomata ELO', title=f'LM Arena Overall No SC vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})')
    save_plot(df, x_col='lma_rank', y_col='strautomata_rank', out_path=args.out_dir / 'lm_arena_overall_no_sc_vs_strautomata_rank.pdf', x_label='LM Arena Overall No SC Rank (1=best)', y_label='Strautomata Rank (1=best)', title=f'LM Arena Overall No SC vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})', rank_mode=True)

    lma_df = load_lma_df(Path('experimental/lm_arena/html/text_coding_no_sc.html'), show_table=args.show_lma_table)
    df = merge_and_save(
        rating_df,
        lma_df,
        args.out_dir / 'lm_arena_text_coding_no_sc_vs_strautomata.csv',
        model_name_mapper=name_to_lma_name,
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "LM Arena Text Coding No SC")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    df_elo = df.copy()
    # df_elo['lma'] = (df_elo['lma'] - m) * 2 + m + 300
    save_plot(df_elo, x_col='lma', y_col='strautomata', out_path=args.out_dir / 'lm_arena_text_coding_no_sc_vs_strautomata.pdf', x_label='LM Arena Text Coding No SC ELO', y_label='Strautomata ELO', title=f'LM Arena Text Coding No SC vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})')
    save_plot(df, x_col='lma_rank', y_col='strautomata_rank', out_path=args.out_dir / 'lm_arena_text_coding_no_sc_vs_strautomata_rank.pdf', x_label='LM Arena Text Coding No SC Rank (1=best)', y_label='Strautomata Rank (1=best)', title=f'LM Arena Text Coding No SC vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})', rank_mode=True)

    lma_df = load_lma_df(Path('experimental/lm_arena/html/text_coding.html'), show_table=args.show_lma_table)
    df = merge_and_save(
        rating_df,
        lma_df,
        args.out_dir / 'lm_arena_text_coding_vs_strautomata.csv',
        model_name_mapper=name_to_lma_name,
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "LM Arena Text Coding")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    df_elo = df.copy()
    # df_elo['lma'] = (df_elo['lma'] - m) * 2 + m + 300
    save_plot(df_elo, x_col='lma', y_col='strautomata', out_path=args.out_dir / 'lm_arena_text_coding_vs_strautomata.pdf', x_label='LM Arena Text Coding ELO', y_label='Strautomata ELO', title=f'LM Arena Text Coding vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})')
    save_plot(df, x_col='lma_rank', y_col='strautomata_rank', out_path=args.out_dir / 'lm_arena_text_coding_vs_strautomata_rank.pdf', x_label='LM Arena Text Coding Rank (1=best)', y_label='Strautomata Rank (1=best)', title=f'LM Arena Text Coding vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})', rank_mode=True)


def run_swe(args: argparse.Namespace) -> None:
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rating_df = load_strautomata_df(args.pkl)
    _print_strautomata_models_missing_from_pairs(
        rating_df,
        pair_table=SWE_BASH_NAME_PAIRS,
        source_label="SWE-bench Bash-Only",
    )
    corr_method = args.corr_type

    swe_df = load_swe_bash_df(args.html)
    df = merge_and_save(
        rating_df,
        swe_df,
        args.out_dir / "swe_bash_vs_strautomata.csv",
        model_name_mapper=name_to_swe_bash_name,
        source_label="SWE-bench Bash-Only",
        source_csv_prefix="swe",
    )
    elo_corrs, rank_corrs = _print_all_corrs(df, "SWE-bench Bash-Only")
    elo_corr = elo_corrs[corr_method]
    rank_corr = rank_corrs[corr_method]
    save_plot(
        df,
        x_col="lma",
        y_col="strautomata",
        out_path=args.out_dir / "swe_bash_vs_strautomata.pdf",
        x_label="SWE-bench Bash-Only Resolved (Affine Transformed)",
        y_label="Strautomata ELO",
        title=f"SWE-bench Bash-Only vs Strautomata ELO ({corr_method} corr: {elo_corr:.2f})",
    )
    save_plot(
        df,
        x_col="lma_rank",
        y_col="strautomata_rank",
        out_path=args.out_dir / "swe_bash_vs_strautomata_rank.pdf",
        x_label="SWE-bench Bash-Only Rank (1=best)",
        y_label="Strautomata Rank (1=best)",
        title=f"SWE-bench Bash-Only vs Strautomata Rank ({corr_method} corr: {rank_corr:.2f})",
        rank_mode=True,
    )


def main() -> None:
    args = parse_args()
    if args.command == "lma":
        run_lma(args)
        return
    if args.command == "swe":
        run_swe(args)
        return
    if args.command == "demo-plot":
        run_demo_plot(args)
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
