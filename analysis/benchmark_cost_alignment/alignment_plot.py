"""Combine data/*.csv, canonicalise model names, compute leave-one-out alignment, plot cost vs alignment.

Alignment (BenchBench-style): for benchmark B, build a consensus from all OTHER benchmarks:
  each other benchmark's scores are converted to within-benchmark ranks scaled to [0,1];
  consensus(model) = mean over other benchmarks containing that model.
Then alignment(B) = Kendall tau between B's score and consensus on models shared by B and >=1 other benchmark,
requiring >= MIN_OVERLAP such models. Pearson on ranks (Spearman) is also reported.

Cost axis: Astra + Fable 5.1 cost at a matched effort (prefer PREFERRED_EFFORT, else max, else default),
converted to benchmark-pass API USD using additive counts or explicit component totals.
Medians and weighted means without component totals remain per-unit only.

Effort is chosen once per (benchmark, model) and used for BOTH the score that enters the ranking and
the cost on the x-axis, so the two axes describe the same run. The two cost models are additionally
pinned to a single shared effort per board; where a site publishes no effort in common for them the
board falls back to per-model picks and is flagged `mixed`.
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
from cost_utils import cost_values

# Match plot_median_elo in src/experimental/exp_plotting.py: plain seaborn whitegrid, no custom colours/weights.
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"pdf.fonttype": 42})

MIN_OVERLAP = 5
PREFERRED_EFFORT = ["high", "xhigh", "max", "default", "medium"]
N_BOOT, BOOT_SEED = 1000, 0   # bootstrap over the shared models for the tau CI (BAT variance is driven by the model sample)
import argparse
_ap = argparse.ArgumentParser(description="Cost vs alignment plot. Example: python alignment_plot.py --snapshot sep_13 --top-k 20")
_ap.add_argument("--data", default="data", help="directory of <benchmark>.csv files (default: data)")
_ap.add_argument("--out", default=".", help="output directory for plot/results")
_ap.add_argument("--snapshot", help="shorthand: --data snapshots/<name>/data --out snapshots/<name>")
_ap.add_argument("--top-k", type=int, default=None, help="restrict alignment to the top-k shared models by consensus")
_ap.add_argument("--exclude", default="", help="comma-separated benchmark slugs to drop")
_ap.add_argument("--only", default="", help="comma-separated benchmark slugs to keep (default: all)")
_ap.add_argument("--include-composites", action="store_true", help="keep composite/superseded boards (vals_index, epoch_eci, ...)")
_ap.add_argument("--show-ci", action="store_true", help="show bootstrap intervals in the figure (always retained in results CSVs)")
_a = _ap.parse_args()
if _a.snapshot: _a.data, _a.out = f"snapshots/{_a.snapshot}/data", f"snapshots/{_a.snapshot}"
DATA_DIR, OUT_DIR = Path(_a.data), Path(_a.out); OUT_DIR.mkdir(parents=True, exist_ok=True)
TOP_K = _a.top_k
# Composite indices and superseded boards are dropped from the consensus by default (pass --include-composites to keep them).
DEFAULT_EXCLUDE = {"vals_index", "epoch_eci", "epoch_frontiermath_v1_private", "epoch_frontiermath_tier_4_v1_private"}
_ap2 = _ap  # noqa
EXCLUDE = set(filter(None, _a.exclude.split(","))) | (set() if _a.include_composites else DEFAULT_EXCLUDE)
ONLY = set(filter(None, _a.only.split(",")))
SUFFIX = f"_top{TOP_K}" if TOP_K else ""

# ---------------- canonicalisation
ALIASES = {
    r"^fable-5\.1$": "claude-fable-5.1", r"^fable-5$": "claude-fable-5", r"^claude-fable$": "claude-fable-5",
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
df["cost_total_usd"] = pd.to_numeric(df.get("cost_total_usd", pd.Series(index=df.index, dtype=float)), errors="coerce")
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

COST_MODELS = ["gpt-6-astra", "claude-fable-5.1"]

def pair_effort(sub: pd.DataFrame):
    """The single effort both cost models are priced at on this board: the most preferred effort
    that BOTH publish a cost for. None when the site publishes no shared effort (then each model
    falls back to its own pick and the board is flagged `mixed`)."""
    av = {m: set(sub.loc[(sub["model"] == m) & sub["cost_usd"].notna(), "effort"]) for m in COST_MODELS}
    if not all(av.values()): return None
    for e in PREFERRED_EFFORT:
        if all(e in v for v in av.values()): return e
    shared = set.intersection(*av.values())
    return sorted(shared)[0] if shared else None

PAIR_EFFORT = {b: pair_effort(g) for b, g in df.groupby("benchmark")}

# Score and cost must describe the same run: every model enters the ranking at its preferred effort
# (the one it is priced at), not at whichever effort happened to score highest. The two cost models
# are pinned to their shared effort so the x-axis never sums two different compute budgets.
_er = df["effort"].map(lambda e: PREFERRED_EFFORT.index(e) if e in PREFERRED_EFFORT else len(PREFERRED_EFFORT))
_pinned = df["model"].isin(COST_MODELS) & (df["effort"] == df["benchmark"].map(PAIR_EFFORT))
df["effort_rank"] = np.where(_pinned, -1, _er)
best = df.sort_values(["effort_rank", "score"], ascending=[True, False]).drop_duplicates(["benchmark", "model"])
score = best.pivot(index="model", columns="benchmark", values="score")
benches = list(score.columns)

# within-benchmark rank scaled to [0,1] (higher better). Flip if meta says lower is better.
_cols = {}
for b in benches:
    col = score[b]
    if metas.get(b, {}).get("score_higher_better", True) is False: col = -col
    r = col.rank(method="average")
    _cols[b] = (r - 1) / max(col.notna().sum() - 1, 1)
rank01 = pd.DataFrame(_cols, index=score.index)

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
    # 95% CI on tau by resampling the shared models. A board measured on few models cannot
    # resolve small tau differences, so the plot draws these as error bars.
    tau_lo = tau_hi = np.nan
    if n >= MIN_OVERLAP:
        xv, yv, bs, rs = x.values, y.values, [], np.random.default_rng(BOOT_SEED)
        for _ in range(N_BOOT):
            i = rs.integers(0, n, n)
            if len(set(xv[i])) < 2 or len(set(yv[i])) < 2: continue
            t = kendalltau(xv[i], yv[i]).statistic
            if not np.isnan(t): bs.append(t)
        if len(bs) >= N_BOOT // 10: tau_lo, tau_hi = np.percentile(bs, [2.5, 97.5])
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
        pe = PAIR_EFFORT.get(b)
        at_pe = s[s["effort"] == pe] if pe is not None else s.iloc[0:0]
        r = at_pe.sort_values("score", ascending=False).iloc[0] if len(at_pe) else pick_effort(s)
        total, per_unit = cost_values(r["cost_usd"], r["cost_unit"], r["n_tasks"], r["cost_total_usd"])
        return dict(effort=r["effort"], unit=r["cost_unit"], per_unit=per_unit, total=total, n_tasks=r["n_tasks"])
    a, f = cost_for("gpt-6-astra"), cost_for("claude-fable-5.1")
    rows.append(dict(benchmark=b, n_models=int(score[b].notna().sum()), n_overlap=n, kendall_tau=tau, tau_lo=tau_lo, tau_hi=tau_hi, spearman=rho, pearson=pr,
                     mean_pairwise_tau=np.nanmean([v[1] for v in pw.values()]) if pw else np.nan, n_pairwise=len(pw),
                     astra_effort=a and a["effort"], astra_unit=a and a["unit"], astra_per_unit=a and a["per_unit"], astra_total=a and a["total"],
                     fable_effort=f and f["effort"], fable_unit=f and f["unit"], fable_per_unit=f and f["per_unit"], fable_total=f and f["total"],
                     pair_total=(a["total"] + f["total"]) if a and f else np.nan,
                     pair_per_unit=(a["per_unit"] + f["per_unit"]) if a and f else np.nan,
                     astra_n_tasks=a and a["n_tasks"], fable_n_tasks=f and f["n_tasks"],
                     cost_audit_status=metas.get(b, {}).get("cost_audit", {}).get("status", "not_audited"),
                     cost_audit_note=metas.get(b, {}).get("cost_audit", {}).get("evidence", ""),
                     pairwise=json.dumps({k: [v[0], round(v[1], 3)] for k, v in pw.items()})))
res = pd.DataFrame(rows).sort_values("kendall_tau", ascending=False)
# BenchBench best practice: interpret tau against the data-driven distribution of the other boards'
# agreement with the same reference, not a fixed threshold. Z > -1 sigma = "in agreement".
_t = res["kendall_tau"].dropna()
TAU_MU, TAU_SD = _t.mean(), _t.std()
res["tau_z"] = (res["kendall_tau"] - TAU_MU) / TAU_SD
res["in_agreement"] = res["tau_z"] > -1
print(f"tau distribution over {len(_t)} boards: mean={TAU_MU:.3f} sd={TAU_SD:.3f}; "
      f"{int((res['tau_z'] <= -1).sum())} boards fall below -1 sigma: {list(res.loc[res['tau_z'] <= -1, 'benchmark'])}")
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
ARENA_TYPE = {"game_arena", "agent_arena", "aa_briefcase", "aa_gdpval", "lmarena_text", "lmarena_webdev", "designarena_gamedev",
              "designarena_3d", "lech_debate", "snakebench", "chessbench", "threejs_eval", "duellab"}       # head-to-head / pairwise-judged (Elo, BT, TrueSkill)
TYPE_MARKER = {"arena": "^", "individual": "o"}
def btype(b): return "arena" if b in ARENA_TYPE else "individual"
def family(b): return "ours" if b == "game_arena" else ("aa" if b.startswith("aa_") else ("vals" if b.startswith("vals_") else "other"))
# Keep Strautomata orange; match the other points to the engine chess purple.
FCOL = {"ours": "#e66b00", "aa": "#6c4ca8", "vals": "#6c4ca8", "other": "#6c4ca8"}
DISPLAY = {"game_arena": "Strautomata", "threejs_eval": "Three.js Eval", "normal_cad_arena": "Normal CAD Arena", "duellab": "DuelLab", "pinnacle": "PINNACLE"}
def disp(b): return DISPLAY.get(b, b)

# Saturation: percent-scored boards where the top five models all score >90%.
NOT_PERCENT = {"game_arena", "agent_arena", "aicd", "aa_omniscience", "aa_gdpval", "aa_briefcase", "duellab", "pinnacle"}  # Elo / index / points
def saturated(b):
    if b in NOT_PERCENT or score[b].max() > 100: return False  # Elo / rating boards are never "saturated" by this rule
    top = score[b].dropna().sort_values(ascending=False).head(5)
    return len(top) == 5 and top.min() > 90
res["saturated"] = res["benchmark"].map(saturated)
print("saturated:", list(res.loc[res["saturated"], "benchmark"]))
for b in benches:
    top = score[b].dropna().sort_values(ascending=False).head(5)
    print(f"  {b:<22} top5 min={top.min():7.2f} max={top.max():7.2f} spread={top.max()-top.min():5.2f} {'SATURATED' if saturated(b) else ''}")
res.to_csv(OUT_DIR / f"alignment_results{SUFFIX}.csv", index=False)
n_all = int(res["kendall_tau"].notna().sum())
plot_all = res.dropna(subset=["kendall_tau"]).copy()
plot_all = plot_all[plot_all["pair_per_unit"].notna() | plot_all["pair_total"].notna()].copy()  # only boards with a cost point
# Stable IDs across full-model/top-20 views and subsequent alignment changes.
# Preserve existing assignments; append newly costed boards without renumbering.
id_path = DATA_DIR.parent / "benchmark_ids.json"
benchmark_ids = json.loads(id_path.read_text()) if id_path.exists() else {}
next_id = max(benchmark_ids.values(), default=0) + 1
for b in sorted(plot_all["benchmark"]):
    if b not in benchmark_ids:
        benchmark_ids[b] = next_id
        next_id += 1
if not id_path.exists() or json.loads(id_path.read_text()) != benchmark_ids:
    id_path.write_text(json.dumps(benchmark_ids, indent=2, sort_keys=True) + "\n")
plot_all["benchmark_id"] = plot_all["benchmark"].map(benchmark_ids)
plot_all.drop(columns=["pairwise"]).sort_values("benchmark_id").to_csv(
    OUT_DIR / f"benchmark_table{SUFFIX}.csv", index=False)
coverage = res[["benchmark", "kendall_tau", "pair_per_unit", "pair_total", "astra_n_tasks", "fable_n_tasks", "cost_audit_status", "cost_audit_note"]].copy()
coverage["per_unit_panel"] = coverage["kendall_tau"].notna() & coverage["pair_per_unit"].notna()
coverage["total_panel"] = coverage["kendall_tau"].notna() & coverage["pair_total"].notna()
coverage["omission_reason"] = np.where(coverage["kendall_tau"].isna(), "insufficient alignment overlap", np.where(coverage["total_panel"], "", np.where(coverage["pair_per_unit"].isna(), "missing cost for one or both target models", coverage["cost_audit_note"].replace("", "task count or additive cost basis unavailable"))))
coverage.to_csv(OUT_DIR / f"cost_coverage{SUFFIX}.csv", index=False)
def _place_labels(ax, fig, labels, frontier=()):
    """Greedy label placement: try upper-right, lower-right, upper-left, lower-left of the marker (in that order)
    and keep the first offset whose text box overlaps neither a placed label nor another marker."""
    fig.canvas.draw()  # freeze limits so data->pixel transforms are final
    dpi_pt = fig.dpi / 72.0
    pts = np.array([ax.transData.transform((x, y)) for x, y, *_ in labels]) if labels else np.zeros((0, 2))
    # the dotted frontier is an obstacle too: sample it every ~4 px
    fpx = [ax.transData.transform(p) for p in frontier]
    obstacles = []
    for (x0, y0), (x1, y1) in zip(fpx[:-1], fpx[1:]):
        n = max(2, int(np.hypot(x1 - x0, y1 - y0) / 4))
        obstacles += [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for t in np.linspace(0, 1, n)]
    placed = []  # (x0, y0, x1, y1) in pixels
    def box(px, py, dx, dy, ha, text, fs):
        w, h = 0.62 * fs * dpi_pt * len(text), 1.05 * fs * dpi_pt
        x0 = px + dx * dpi_pt - (w if ha == "right" else 0)
        y0 = py + dy * dpi_pt
        return (x0, y0, x0 + w, y0 + h)
    def clash(b, i):
        for q in placed:
            if b[0] < q[2] and q[0] < b[2] and b[1] < q[3] and q[1] < b[3]: return True
        for k, (mx, my) in enumerate(pts):
            if k != i and b[0] - 3 < mx < b[2] + 3 and b[1] - 3 < my < b[3] + 3: return True
        for mx, my in obstacles:
            if b[0] < mx < b[2] and b[1] < my < b[3]: return True
        return False
    # ours first so it always gets its preferred spot; then the rest in x order
    order = sorted(range(len(labels)), key=lambda i: (not labels[i][4], pts[i][0]))
    for i in order:
        x, y, text, fam, ours, sat = labels[i]
        fs = 8 if ours else 7
        px, py = pts[i]
        options = [((7, 4), "left"), ((7, -11), "left"), ((-7, 4), "right"), ((-7, -11), "right")]
        chosen = options[0]
        for (dx, dy), ha in options:
            if not clash(box(px, py, dx, dy, ha, text, fs), i):
                chosen = ((dx, dy), ha); break
        placed.append(box(px, py, *chosen[0], chosen[1], text, fs))
        ax.annotate(text, (x, y), xytext=chosen[0], ha=chosen[1], textcoords="offset points", fontsize=fs,
                    color=FCOL[fam], fontweight="bold" if ours else "normal",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.92) if ours else None,
                    alpha=0.65 if sat else 1, zorder=6)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))
panels = [("pair_per_unit", "GPT-6 Astra + Claude Fable 5.1 (USD per task/unit, log)", "Per Task/Unit Cost"),
          ("pair_total", "GPT-6 Astra + Claude Fable 5.1 (USD total cost, log)", "Total Cost")]
for ax, (col, xl, ttl) in zip(axes, panels):
    plot = plot_all.dropna(subset=[col])
    pending_labels, front = [], []
    for _, r in plot.iterrows():
        b = r["benchmark"]; fam = family(b); ours = fam == "ours"; mk = TYPE_MARKER[btype(b)]; sat = bool(r["saturated"])
        size = (100 if mk == "^" else 70) * (0.25 if sat else 1)
        if ours:
            size = 150
            # Soft halo plus a white rim keeps the orange triangle clear over the frontier.
            for halo_size, halo_alpha in [(340, 0.06)]:
                ax.scatter(r[col], r["kendall_tau"], s=halo_size, marker=mk, color=FCOL[fam],
                           edgecolor="none", alpha=halo_alpha, zorder=3)
            ax.scatter(r[col], r["kendall_tau"], s=size + 40, marker=mk,
                       color="white", edgecolor="none", zorder=4)
        if _a.show_ci and not np.isnan(r["tau_lo"]):
            ax.errorbar(r[col], r["kendall_tau"], yerr=[[r["kendall_tau"] - r["tau_lo"]], [r["tau_hi"] - r["kendall_tau"]]],
                        fmt="none", ecolor=FCOL[fam], elinewidth=1.0, capsize=2, alpha=0.15 if sat else 0.45, zorder=1)
        ax.scatter(r[col], r["kendall_tau"], s=size, marker=mk, color=FCOL[fam], alpha=0.3 if sat else (1 if ours else 0.95),
                   edgecolor="#713600" if ours else "#555555", linewidth=0.9 if ours else 0.5,
                   zorder=5 if ours else (2 if sat else 3))
        pending_labels.append((r[col], r["kendall_tau"], f'{r["benchmark_id"]} (Ours)' if ours else str(r["benchmark_id"]), fam, ours, sat))
    # Pareto frontier (cheaper and more aligned dominates); saturated boards excluded
    cand = plot[~plot["saturated"].astype(bool)].sort_values([col, "kendall_tau"], ascending=[True, False])
    front, best = [], -np.inf
    for _, r in cand.iterrows():
        if r["kendall_tau"] > best: front.append((r[col], r["kendall_tau"])); best = r["kendall_tau"]
    if len(front) > 1:
        fx, fy = zip(*front)
        ax.plot(fx, fy, ls=":", color="black", lw=1.6, alpha=0.95, zorder=2, label="Non-saturated Pareto frontier")
    # keep the y range set by the point estimates; a few tiny-n boards have CIs wide enough to
    # rescale the whole panel, so let those bars clip instead.
    ax.set_ylim(0.35, plot["kendall_tau"].max() + 0.05)
    ax.set_xscale("log"); ax.set_xlabel(xl)
    _place_labels(ax, fig, pending_labels, front)
    if col == "pair_total":  # the under-$200 box is drawn on every total-cost panel
        from matplotlib.patches import Rectangle
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        ax.add_patch(Rectangle((xmin, 0.6), 200 - xmin, ymax - 0.6,
                               facecolor=(76 / 255, 175 / 255, 80 / 255, 0.18),
                               edgecolor="none", zorder=0))
        ax.set_xlim(xmin, xmax)
        # top-10 view: centred in the box; all-models view: the frontier crosses the box, so tuck the text top-left
        tx, ty, tha = (np.sqrt(xmin * 200), 0.6 + 0.72 * (ymax - 0.6), "center") if TOP_K == 10 else (xmin * 1.25, ymax - 0.012, "left")
        ax.text(tx, ty, "high quality benchmark\nfor <$200", ha=tha, va="top" if TOP_K != 10 else "center",
                fontsize=12, fontweight="bold", fontfamily="DejaVu Sans",
                linespacing=1.0, color="#229b25", alpha=1.0, zorder=4)
    ax.grid(False, which="minor")
    ax.grid(axis="both", which="major", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", length=0)
    _ttl = "Benchmark Alignment vs Cost Per Task/Unit" if col == "pair_per_unit" else "Benchmark Alignment vs Frontier Cost"
    ax.set_title(_ttl + (f" (top {TOP_K})" if TOP_K else ""), pad=10)
for ax in axes:
    ax.set_ylabel("Alignment (Kendall τ)")
# marker legend
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker="^", ls="", ms=9, color=FCOL["other"], label="arena (pairwise)"),
           Line2D([], [], marker="o", ls="", ms=9, color=FCOL["other"], label="individual"),
           Line2D([], [], marker="o", ls="", ms=4, color=FCOL["other"], alpha=0.3, label="saturated"),
           Line2D([], [], ls=":", color="black", lw=1.5, label="Non-saturated Pareto frontier"),
           Line2D([], [], marker="^", ls="", ms=10, color=FCOL["ours"], markeredgecolor="#713600", markeredgewidth=0.9, label="Strautomata (ours)")]
if _a.show_ci:
    handles.insert(4, Line2D([], [], ls="-", color="gray", lw=1.0, label="95% CI on τ (bootstrap over shared models)"))
axes[0].legend(handles=handles, loc="lower left", fontsize=8.5, frameon=True, framealpha=0.9, edgecolor="none",
               labelspacing=0.45, handletextpad=0.65, borderaxespad=0.7)
fig.tight_layout(pad=1.0, h_pad=1.5)
if True:
    # Separate outline inset by two pixels at the PNG's 160 dpi export size.
    ax = axes[1]
    lower = ax.transAxes.inverted().transform(ax.transData.transform((ax.get_xlim()[0], 0.6)))
    upper = ax.transAxes.inverted().transform(ax.transData.transform((200, ax.get_ylim()[1])))
    inset_x = 2 / (ax.get_position().width * fig.get_figwidth() * 160)
    inset_y = 2 / (ax.get_position().height * fig.get_figheight() * 160)
    ax.add_patch(Rectangle((lower[0] + inset_x, lower[1] + inset_y),
                           upper[0] - lower[0] - 2 * inset_x,
                           upper[1] - lower[1] - 2 * inset_y,
                           transform=ax.transAxes, facecolor="none",
                           edgecolor=(76 / 255, 175 / 255, 80 / 255, 0.32),
                           linewidth=0.8, linestyle="-", zorder=1))
fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.png", dpi=160, bbox_inches="tight")
fig.savefig(OUT_DIR / f"cost_vs_alignment{SUFFIX}.pdf", bbox_inches="tight")
print("\nsaved", OUT_DIR / f"cost_vs_alignment{SUFFIX}.png")
