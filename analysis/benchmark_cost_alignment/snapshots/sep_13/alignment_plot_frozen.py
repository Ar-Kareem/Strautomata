"""Combine data/*.csv, canonicalise model names, compute leave-one-out alignment, plot cost vs alignment.

Alignment (BenchBench-style): for benchmark B, build a consensus from all OTHER benchmarks:
  each other benchmark's scores are converted to within-benchmark ranks scaled to [0,1];
  consensus(model) = mean over other benchmarks containing that model.
Then alignment(B) = Kendall tau between B's score and consensus on models shared by B and >=1 other benchmark,
requiring >= MIN_OVERLAP such models. Pearson on ranks (Spearman) is also reported.

Cost axis: Astra + Fable 5.1 cost at a matched effort (prefer PREFERRED_EFFORT, else max, else default),
converted to total-run USD where n_tasks is known; otherwise per-unit cost (flagged).
"""
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr, pearsonr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MIN_OVERLAP = 5
PREFERRED_EFFORT = ["high", "xhigh", "max", "default", "medium"]
import argparse
_ap = argparse.ArgumentParser(description="Cost vs alignment plot. Example: python alignment_plot.py --snapshot sep_13 --top-k 20")
_ap.add_argument("--data", default="data", help="directory of <benchmark>.csv files (default: data)")
_ap.add_argument("--out", default=".", help="output directory for plot/results")
_ap.add_argument("--snapshot", help="shorthand: --data snapshots/<name>/data --out snapshots/<name>")
_ap.add_argument("--top-k", type=int, default=None, help="restrict alignment to the top-k shared models by consensus")
_ap.add_argument("--exclude", default="", help="comma-separated benchmark slugs to drop")
_ap.add_argument("--only", default="", help="comma-separated benchmark slugs to keep (default: all)")
_a = _ap.parse_args()
if _a.snapshot: _a.data, _a.out = f"snapshots/{_a.snapshot}/data", f"snapshots/{_a.snapshot}"
DATA_DIR, OUT_DIR = Path(_a.data), Path(_a.out); OUT_DIR.mkdir(parents=True, exist_ok=True)
TOP_K = _a.top_k
EXCLUDE = set(filter(None, _a.exclude.split(","))); ONLY = set(filter(None, _a.only.split(",")))
SUFFIX = f"_top{TOP_K}" if TOP_K else ""

# ---------------- canonicalisation
ALIASES = {
    r"^fable-5\.1$": "claude-fable-5.1", r"^fable-5$": "claude-fable-5",
    r"^(claude-)?opus-(\d[\d.]*)$": r"claude-opus-\2", r"^(claude-)?sonnet-(\d[\d.]*)$": r"claude-sonnet-\2", r"^(claude-)?haiku-(\d[\d.]*)$": r"claude-haiku-\2",
    r"^gemini-(\d[\d.]*)-pro-preview.*$": r"gemini-\1-pro", r"^gemini-(\d[\d.]*)-flash-preview.*$": r"gemini-\1-flash",
    r"^gemini-(\d[\d.]*)-flash-lite-preview.*$": r"gemini-\1-flash-lite",
    r"^gpt-6-astra-pro.*$": "gpt-6-astra-pro", r"^gpt-6-astra.*$": "gpt-6-astra",
    r"^deepseek-chat-v(\d[\d.]*)(-\d+)?$": r"deepseek-v\1", r"^deepseek-chat$": "deepseek-v3",
    r"^grok-(\d[\d.]*)(-\d{4})?$": r"grok-\1",
    r"^kimi-k(\d[\d.]*)(-thinking|-instruct)?$": r"kimi-k\1",
    r"^(o\d)(-\d{4}-\d\d-\d\d)?$": r"\1",
}
STRIP = [r"-\d{8}$", r"-\d{4}-\d\d-\d\d$", r":free$", r"-exp$", r"-thinking$", r"-reasoning$", r"-instruct$", r"-chat$",
         r"-\d{4}$",  # 4-digit mm-dd
         r"-(minimal|low|medium|high|xhigh|max|none|default)$", r"\((minimal|low|medium|high|xhigh|max|none)\)$",
         r"^openai-", r"^anthropic-", r"^google-", r"^x-ai-", r"^xai-", r"^deepseek-ai-", r"^moonshot(ai)?-", r"^z-ai-", r"^zhipu-", r"^alibaba-", r"^qwen-qwen", r"^meta-llama-", r"^mistralai-", r"^minimax(ai)?-"]

def canon(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[()]", "", s)
    s = re.sub(r"[\s_/:]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    for _ in range(3):
        for p in STRIP: s = re.sub(p, "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    s = re.sub(r"^(?:xiaomi-|thinkingmachines-|meta-|nvidia-)", "", s)
    s = re.sub(r"^claude-(\d[\d.]*)-(opus|sonnet|haiku)$", r"claude-\2-\1", s)
    s = re.sub(r"^(opus|sonnet|haiku)-(\d)-(\d)$", r"claude-\1-\2.\3", s)
    s = re.sub(r"^(gpt|gemini|grok|glm|kimi-k|claude-opus|claude-sonnet|claude-haiku)-(\d)-(\d)(?=-|$)", r"\1-\2.\3", s)
    s = re.sub(r"^qwen-?(\d)", r"qwen-\1", s)
    s = re.sub(r"-\d\d-\d\d$", "", s)  # mm-dd
    for pat, rep in ALIASES.items():
        if re.match(pat, s): s = re.sub(pat, rep, s); break
    return s

# ---------------- load
frames = []
metas = {}
PRIMARY = ["game_arena", "arc_agi_1", "arc_agi_2", "arc_agi_3", "or_gpqa_diamond", "matharena", "weirdml", "agent_arena", "frontiercode",
           "vals_index", "aicd", "terminal_bench_4", "real_swe"]
for p in sorted(DATA_DIR.glob("*.csv")):
    if p.stem.startswith("matharena_"): continue  # per-competition sub-tables, not leaf boards
    if p.stem in EXCLUDE or (ONLY and p.stem not in ONLY): continue
    df = pd.read_csv(p, dtype=str).fillna("")
    if df.empty: continue
    b = df["benchmark"].iloc[0] or p.stem
    df["benchmark"] = b
    mp = p.with_suffix(".meta.json")
    metas[b] = json.loads(mp.read_text()) if mp.exists() else {}
    frames.append(df)
df = pd.concat(frames, ignore_index=True)
df["model"] = df["model_canonical"].map(canon)
df["effort"] = df["effort"].replace("", "default")
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce")
df["n_tasks"] = pd.to_numeric(df["n_tasks"], errors="coerce")
df = df.dropna(subset=["score"])
df.to_csv(OUT_DIR / "combined.csv", index=False)

def pick_effort(sub: pd.DataFrame) -> pd.Series:
    """One row per model per benchmark: prefer effort order, then best score."""
    for e in PREFERRED_EFFORT:
        s = sub[sub["effort"] == e]
        if len(s): return s.sort_values("score", ascending=False).iloc[0]
    return sub.sort_values("score", ascending=False).iloc[0]

def best_effort(sub: pd.DataFrame) -> pd.Series:
    return sub.sort_values("score", ascending=False).iloc[0]

# For alignment, use each model's BEST score on each benchmark (the leaderboard's own ordering of models).
best = df.groupby(["benchmark", "model"], as_index=False).apply(best_effort, include_groups=False).reset_index(drop=True) if False else \
       df.sort_values("score", ascending=False).drop_duplicates(["benchmark", "model"])
score = best.pivot(index="model", columns="benchmark", values="score")
benches = list(score.columns)

# within-benchmark rank scaled to [0,1] (higher better). Flip if meta says lower is better.
rank01 = pd.DataFrame(index=score.index)
for b in benches:
    col = score[b]
    if metas.get(b, {}).get("score_higher_better", True) is False: col = -col
    r = col.rank(method="average")
    rank01[b] = (r - 1) / (col.notna().sum() - 1)

rows = []
for b in benches:
    others = [o for o in benches if o != b]
    cons = rank01[others].mean(axis=1, skipna=True)
    n_other = rank01[others].notna().sum(axis=1)
    mask = rank01[b].notna() & (n_other >= 1)
    x, y = rank01.loc[mask, b], cons[mask]
    if TOP_K:
        top = y.sort_values(ascending=False).index[:TOP_K]; x, y = x[top], y[top]
    n = len(x)
    tau = kendalltau(x, y).statistic if n >= MIN_OVERLAP else np.nan
    rho = spearmanr(x, y).statistic if n >= MIN_OVERLAP else np.nan
    pr = pearsonr(score.loc[y.index, b], y).statistic if n >= MIN_OVERLAP else np.nan
    # pairwise taus with each other benchmark (for a z-score later)
    pw = {}
    for o in others:
        m2 = rank01[b].notna() & rank01[o].notna()
        if m2.sum() >= MIN_OVERLAP: pw[o] = (int(m2.sum()), kendalltau(rank01.loc[m2, b], rank01.loc[m2, o]).statistic)
    # cost
    sub = df[df["benchmark"] == b]
    def cost_for(model):
        s = sub[(sub["model"] == model) & sub["cost_usd"].notna()]
        if s.empty: return None
        r = pick_effort(s)
        has_n = not np.isnan(r["n_tasks"])
        if r["cost_unit"] == "total_run":
            total, per_unit = r["cost_usd"], (r["cost_usd"] / r["n_tasks"] if has_n else np.nan)
        else:
            total, per_unit = (r["cost_usd"] * r["n_tasks"] if has_n else np.nan), r["cost_usd"]
        return dict(effort=r["effort"], unit=r["cost_unit"], per_unit=per_unit, total=total, n_tasks=r["n_tasks"])
    a, f = cost_for("gpt-6-astra"), cost_for("claude-fable-5.1")
    rows.append(dict(benchmark=b, n_models=int(score[b].notna().sum()), n_overlap=n, kendall_tau=tau, spearman=rho, pearson=pr,
                     mean_pairwise_tau=np.nanmean([v[1] for v in pw.values()]) if pw else np.nan, n_pairwise=len(pw),
                     astra_effort=a and a["effort"], astra_unit=a and a["unit"], astra_per_unit=a and a["per_unit"], astra_total=a and a["total"],
                     fable_effort=f and f["effort"], fable_unit=f and f["unit"], fable_per_unit=f and f["per_unit"], fable_total=f and f["total"],
                     pair_total=(a["total"] + f["total"]) if a and f else np.nan,
                     pair_per_unit=(a["per_unit"] + f["per_unit"]) if a and f else np.nan,
                     pairwise=json.dumps({k: [v[0], round(v[1], 3)] for k, v in pw.items()})))
res = pd.DataFrame(rows).sort_values("kendall_tau", ascending=False)
res.to_csv(OUT_DIR / f"alignment_results{SUFFIX}.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(res.drop(columns=["pairwise"]).round(3).to_string(index=False))

# overlap matrix
ov = pd.DataFrame({b: {o: int((rank01[b].notna() & rank01[o].notna()).sum()) for o in benches} for b in benches})
print("\nmodel overlap matrix:\n", ov.to_string())
ov.to_csv(OUT_DIR / "overlap_matrix.csv")
pt = pd.DataFrame({b: {o: (kendalltau(rank01.loc[m, b], rank01.loc[m, o]).statistic if (m := rank01[b].notna() & rank01[o].notna()).sum() >= MIN_OVERLAP else np.nan) for o in benches} for b in benches})
print("\npairwise Kendall tau:\n", pt.round(2).to_string())
pt.to_csv(OUT_DIR / "pairwise_tau.csv")

# ---------------- plot
# Benchmark type -> marker. Edit these sets to reclassify.
ARENA_TYPE = {"game_arena", "agent_arena", "aa_briefcase", "aa_gdpval"}          # head-to-head / pairwise-judged (Elo or BT)
OTHER_TYPE = {"aicd", "vals_index", "aa_harvey_lab"}                              # human/LLM rubric or composite index
TYPE_MARKER = {"arena": "*", "grader": "o", "other": "^"}
def btype(b): return "arena" if b in ARENA_TYPE else ("other" if b in OTHER_TYPE else "grader")
def family(b): return "ours" if b == "game_arena" else ("aa" if b.startswith("aa_") else "other")
FCOL = {"ours": "#d95f02", "aa": "#1b9e77", "other": "#6c4ca8"}
DISPLAY = {"game_arena": "Strautomata"}
def disp(b): return DISPLAY.get(b, b)

# Saturation: percent-scored boards where the top-5 models all score >90 and span <2 points.
NOT_PERCENT = {"game_arena", "agent_arena", "aicd", "aa_omniscience", "aa_gdpval", "aa_briefcase"}  # Elo / index / points
def saturated(b):
    if b in NOT_PERCENT: return False
    top = score[b].dropna().sort_values(ascending=False).head(5)
    return len(top) == 5 and top.min() > 90 and (top.max() - top.min()) < 5
res["saturated"] = res["benchmark"].map(saturated)
print("saturated:", list(res.loc[res["saturated"], "benchmark"]))
for b in benches:
    top = score[b].dropna().sort_values(ascending=False).head(5)
    print(f"  {b:<22} top5 min={top.min():7.2f} max={top.max():7.2f} spread={top.max()-top.min():5.2f} {'SATURATED' if saturated(b) else ''}")
res.to_csv(OUT_DIR / f"alignment_results{SUFFIX}.csv", index=False)
plot_all = res.dropna(subset=["kendall_tau"]).copy()
plot_all["idx"] = range(1, len(plot_all) + 1)  # numbered by alignment rank
fig, axes = plt.subplots(1, 2, figsize=(18, 8))
panels = [("pair_per_unit", "Cost per task, GPT-6 Astra + Claude Fable 5.1 (USD, log)", "per task"),
          ("pair_total", "Total cost to run benchmark, Astra + Fable 5.1 (USD, log; where task count known)", "total run")]
for ax, (col, xl, ttl) in zip(axes, panels):
    plot = plot_all.dropna(subset=[col])
    for _, r in plot.iterrows():
        b = r["benchmark"]; fam = family(b); ours = fam == "ours"; mk = TYPE_MARKER[btype(b)]; sat = bool(r["saturated"])
        size = (260 if mk == "*" else 120) * (0.25 if sat else 1)
        ax.scatter(r[col], r["kendall_tau"], s=size, marker=mk, color=FCOL[fam], alpha=0.3 if sat else 0.9,
                   edgecolor="black" if ours else "white", linewidth=1.2 if ours else 0.8, zorder=4 if ours else (2 if sat else 3))
        ax.annotate(str(r["idx"]), (r[col], r["kendall_tau"]), xytext=(6, 3), textcoords="offset points", fontsize=6 if sat else 8,
                    fontweight="bold" if ours else "normal", color=FCOL[fam], alpha=0.45 if sat else 1)
    # Pareto frontier (cheaper and more aligned dominates); saturated boards excluded
    cand = plot[~plot["saturated"].astype(bool)].sort_values([col, "kendall_tau"], ascending=[True, False])
    front, best = [], -np.inf
    for _, r in cand.iterrows():
        if r["kendall_tau"] > best: front.append((r[col], r["kendall_tau"])); best = r["kendall_tau"]
    if len(front) > 1:
        fx, fy = zip(*front)
        ax.plot(fx, fy, ls=":", color="black", lw=1.5, zorder=2, label="Pareto line")
        ax.scatter(fx, fy, s=230, facecolor="none", edgecolor="black", lw=0.8, zorder=2, alpha=0.5)
    ax.set_xscale("log"); ax.set_xlabel(xl, fontsize=9); ax.grid(True, which="both", alpha=0.25)
    ax.set_title(f"Alignment vs {ttl} cost", fontsize=11)
axes[0].set_ylabel("Alignment: Kendall τ vs leave-one-out consensus of other benchmarks")
# marker legend
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker="*", ls="", ms=13, color="gray", label="arena: outputs face off head to head"),
           Line2D([], [], marker="o", ls="", ms=9, color="gray", label="fixed grader: output must pass a checker"),
           Line2D([], [], marker="^", ls="", ms=9, color="gray", label="other: rubric-judged or composite"),
           Line2D([], [], ls=":", color="black", lw=1.5, label="Pareto line (cheaper and more aligned)"),
           Line2D([], [], marker="s", ls="", ms=9, color=FCOL["ours"], label="Strautomata (ours)"),
           Line2D([], [], marker="s", ls="", ms=9, color=FCOL["aa"], label="Artificial Analysis"),
           Line2D([], [], marker="s", ls="", ms=9, color=FCOL["other"], label="other public boards")]
axes[0].legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.9)
# numbered list
lines = []
for _, r in plot_all.iterrows():
    e = r["astra_effort"] if r["astra_effort"] == r["fable_effort"] else "mixed"
    c = "" if np.isnan(r["pair_per_unit"]) else f"${r['pair_per_unit']:.2f}/task"
    lines.append(f"{r['idx']:>2}. {disp(r['benchmark']):<22} τ={r['kendall_tau']:.2f} n={r['n_overlap']:<3} {e:<7} {c:<12}{' SAT' if r['saturated'] else ''}")
fig.text(0.775, 0.5, "\n".join(lines), fontsize=6.4, family="monospace", va="center", ha="left", bbox=dict(boxstyle="round", fc="white", ec="lightgray"))
fig.suptitle("Benchmark cost vs agreement with other benchmarks (demo, data fetched 2026-09-13)" + (f"  |  alignment on top-{TOP_K} shared models by consensus" if TOP_K else ""), fontsize=12)
fig.text(0.01, 0.005, "n = models shared with the consensus; effort column = reasoning effort used for the cost of Astra / Fable 5.1.  consensus = mean scaled rank over the other benchmarks, min 5 shared models.  "
         "Unnumbered benchmarks in the list have no cost for both models.\nSAT / tiny dim marker = saturated: top-5 models all >90% and within 5 points.", fontsize=7.5, color="gray")
fig.tight_layout(rect=(0, 0.03, 0.77, 0.97))
fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.png", dpi=160); fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.pdf")
print("\nsaved", OUT_DIR / f"cost_vs_alignment{SUFFIX}.png")
