"""Does ranking models by their BEST chess automaton or by the MEAN of their five automata align better with the benchmark consensus?

Input: per-bot chess Elo from the full all-bots round robin
  analysis/results_tmp/plots_full_nsquared_sept_25/bots/rating_df.csv  (261 bots, 53 models incl. random)
For each model we build scores: max over its bots, mean of its top-2 bots, mean and median of its top-3 and top-4 bots, mean over all 5, and median (reference).
Each score is dropped into the alignment pipeline (../alignment_plot.py) as its own board, one at a time, with
game_arena (the 20-game median board) removed so both variants face the *same* consensus of external benchmarks.

Run:  cd analysis/benchmark_cost_alignment && ../../env3.12/bin/python full_chess_max_vs_mean/compare.py
Outputs (this directory): summary.csv, model_scores.csv, rank_shift.csv, README.md, tmp/ (per-variant alignment outputs)
"""
import re, shutil, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

HERE = Path(__file__).resolve().parent
BCA = HERE.parent                      # analysis/benchmark_cost_alignment
ROOT = BCA.parents[1]
RATING = ROOT / "analysis/results_tmp/plots_full_nsquared_sept_25/bots/rating_df.csv"
PY = sys.executable
EFF = {"low", "medium", "high", "xhigh", "max", "instant"}
VARIANTS = {"chess_max": "max", "chess_top2mean": "top2mean", "chess_top3mean": "top3mean", "chess_top3median": "top3median", "chess_top4mean": "top4mean", "chess_top4median": "top4median", "chess_mean": "mean", "chess_median": "median"}
TOPK = [None, 10]

def canon_model(name):
    """Same mapping as build_arena.py so models merge with the other boards."""
    parts = name.split("_")
    eff = parts[-1] if parts[-1] in EFF else "default"
    base = "_".join(parts[:-1]) if eff != "default" else name
    base = re.sub(r"_free$", "", base)
    c = base.replace("_", "-")
    if eff == "instant": eff, c = "none", c + "-instant"
    return c, eff

# ---- per-model scores
bots = pd.read_csv(RATING, index_col=0)["Chess UCI"].dropna()
bots = bots[~bots.index.str.startswith("random")]
per = bots.groupby(bots.index.str.split("/").str[0]).agg(["max", "mean", "median", "min", "std", "count"]).round(1)
per["top2mean"] = bots.groupby(bots.index.str.split("/").str[0]).agg(lambda s: s.nlargest(2).mean()).round(1)
per["top3mean"] = bots.groupby(bots.index.str.split("/").str[0]).agg(lambda s: s.nlargest(3).mean()).round(1)
per["top3median"] = bots.groupby(bots.index.str.split("/").str[0]).agg(lambda s: s.nlargest(3).median()).round(1)
per["top4mean"] = bots.groupby(bots.index.str.split("/").str[0]).agg(lambda s: s.nlargest(4).mean()).round(1)
per["top4median"] = bots.groupby(bots.index.str.split("/").str[0]).agg(lambda s: s.nlargest(4).median()).round(1)
per.index.name = "model_raw"
per["rank_max"] = per["max"].rank(ascending=False).astype(int)
per["rank_mean"] = per["mean"].rank(ascending=False).astype(int)
per["rank_shift(mean-max)"] = per["rank_mean"] - per["rank_max"]
per["rank_top2mean"] = per["top2mean"].rank(ascending=False).astype(int)
per.sort_values("max", ascending=False).to_csv(HERE / "model_scores.csv")
shift = per.reindex(per["rank_shift(mean-max)"].abs().sort_values(ascending=False).index)
shift[["max", "mean", "std", "rank_max", "rank_mean", "rank_shift(mean-max)"]].head(12).to_csv(HERE / "rank_shift.csv")

# ---- build a data dir: all external boards + the chess variants (game_arena removed)
TMP = HERE / "tmp"; shutil.rmtree(TMP, ignore_errors=True)
DATA = TMP / "data"; DATA.mkdir(parents=True)
for p in BCA.glob("data/*"):
    if p.stem.split(".")[0] != "game_arena": shutil.copy(p, DATA / p.name)
HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
for b, stat in VARIANTS.items():
    rows = []
    for m, r in per.iterrows():
        c, e = canon_model(m)
        rows.append(dict(benchmark=b, model_raw=m, model_canonical=c, effort=e, score=r[stat], cost_usd="", cost_unit="", n_tasks="",
                         source_url=str(RATING.relative_to(ROOT)), note=f"{stat} chess Elo over the model's automata (full round robin)"))
    pd.DataFrame(rows, columns=HDR).to_csv(DATA / f"{b}.csv", index=False)
    (DATA / f"{b}.meta.json").write_text('{"benchmark": "%s", "score_higher_better": true}' % b)

# ---- run the alignment once per variant (other variants excluded so they never enter the consensus)
def run(b, k):
    out = TMP / f"out_{b}{'_top%d' % k if k else ''}"
    cmd = [PY, str(BCA / "alignment_plot.py"), "--data", str(DATA), "--out", str(out),
           "--exclude", ",".join(v for v in VARIANTS if v != b)] + (["--top-k", str(k)] if k else [])
    subprocess.run(cmd, cwd=BCA, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    res = pd.read_csv(out / f"alignment_results{'_top%d' % k if k else ''}.csv").set_index("benchmark")
    r = res.loc[b]
    return dict(variant=b, top_k=k or "all", n_overlap=int(r["n_overlap"]), kendall_tau=round(r["kendall_tau"], 3),
                tau_lo=round(r["tau_lo"], 3), tau_hi=round(r["tau_hi"], 3), spearman=round(r["spearman"], 3),
                tau_z=round(r["tau_z"], 2), rank_among_boards=int((res["kendall_tau"] > r["kendall_tau"]).sum() + 1), n_boards=int(res["kendall_tau"].notna().sum()))
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex: rows = list(ex.map(lambda bk: run(*bk), [(b, k) for b in VARIANTS for k in TOPK]))
# reference: the existing 20-game Median ELO board from the main analysis
for k, f in [(None, "alignment_results.csv"), (10, "alignment_results_top10.csv")]:
    r = pd.read_csv(BCA / f).set_index("benchmark").loc["game_arena"]
    rows.append(dict(variant="game_arena (20-game median, main analysis)", top_k=k or "all", n_overlap=int(r["n_overlap"]), kendall_tau=round(r["kendall_tau"], 3),
                     tau_lo=round(r["tau_lo"], 3), tau_hi=round(r["tau_hi"], 3), spearman=round(r["spearman"], 3), tau_z=round(r["tau_z"], 2), rank_among_boards="", n_boards=""))
summ = pd.DataFrame(rows); summ.to_csv(HERE / "summary.csv", index=False)

tau_mm = kendalltau(per["max"], per["mean"]).statistic; rho_mm = spearmanr(per["max"], per["mean"]).statistic
print(f"max vs mean ranking agreement over {len(per)} models: Kendall tau={tau_mm:.3f}, Spearman={rho_mm:.3f}")
print(summ.to_string(index=False))
print("\nlargest rank shifts (mean rank - max rank):\n", shift[["max", "mean", "std", "rank_max", "rank_mean", "rank_shift(mean-max)"]].head(10).to_string())

# ---- README
md = [f"# Full chess round robin: top-1 bot vs mean-of-bots as the model score\n",
      f"Source: `{RATING.relative_to(ROOT)}` ({len(bots)} bots, {len(per)} models, all 5 automata per model, 67,860 games).",
      "Each variant is scored against the leave-one-out consensus of the external boards in `../data/` (game_arena removed, so both face the same consensus). Same code path as `../alignment_plot.py`.\n",
      f"Agreement between the two model rankings themselves: Kendall tau = {tau_mm:.3f}, Spearman = {rho_mm:.3f} over {len(per)} models.\n",
      "## Alignment with the benchmark consensus\n", summ.to_markdown(index=False), "\n",
      "Agreement of top2mean ranking with max: tau = %.3f; with mean: tau = %.3f.\n" % (kendalltau(per["top2mean"], per["max"]).statistic, kendalltau(per["top2mean"], per["mean"]).statistic),
      "## Largest rank shifts (positive = mean ranks the model lower than max does)\n",
      shift[["max", "mean", "std", "rank_max", "rank_mean", "rank_shift(mean-max)"]].head(10).to_markdown(), "\n",
      "Files: `summary.csv`, `model_scores.csv` (per-model max/mean/median/min/std and ranks), `rank_shift.csv`, `tmp/out_*` (full alignment outputs per variant).",
      "Regenerate: `cd analysis/benchmark_cost_alignment && ../../env3.12/bin/python full_chess_max_vs_mean/compare.py`"]
(HERE / "README.md").write_text("\n".join(md) + "\n")
