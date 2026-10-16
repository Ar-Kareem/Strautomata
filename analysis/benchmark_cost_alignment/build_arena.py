"""Our game arena (strautomata) as a benchmark: Median ELO per model from rating_df.csv, cost = summed OpenRouter usage.cost over all bots."""
import csv, glob, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RATING = ROOT / "analysis/results_tmp/plots_somerset_sept_5/models/rating_df.csv"
HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
EFF = {"low","medium","high","xhigh","max","instant"}

def cost_for(model):
    files = glob.glob(str(ROOT / f"src/game_arena/*/examples/*/{model}/*/0.info.json"))
    tot, n = 0.0, 0
    for f in files:
        c = (json.load(open(f)).get("usage") or {}).get("cost")
        if c is not None: tot += float(c); n += 1
    return tot, n, len(files)

rows = []
for r in csv.DictReader(open(RATING)):
    name = r[""]
    if name == "random": continue
    parts = name.split("_")
    eff = parts[-1] if parts[-1] in EFF else "default"
    base = "_".join(parts[:-1]) if eff != "default" else name
    base = re.sub(r"_free$", "", base)
    canon = base.replace("_", "-")
    canon = re.sub(r"^gpt-(\d)-astra", r"gpt-\1-astra", canon)
    if eff == "instant": eff, canon = "none", canon + "-instant"
    tot, n, nb = cost_for(name)
    rows.append(dict(benchmark="game_arena", model_raw=name, model_canonical=canon, effort=eff, score=r["Median ELO"],
                     cost_usd=round(tot / n, 4) if n else "", cost_unit="per_bot", n_tasks=nb or "",
                     source_url=str(RATING.relative_to(ROOT)),
                     note=f"score=Median ELO over 20 games; cost=mean OpenRouter usage.cost per generated bot ({n}/{nb} bots with cost); total=${tot:.2f}"))
out = ROOT / "analysis/benchmark_cost_alignment/data/game_arena.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HDR); w.writeheader(); w.writerows(rows)
meta = dict(benchmark="game_arena", score_higher_better=True, cost_unit="per_bot", n_models=len(rows), fetched="2026-09-13",
            how="rating_df.csv Median ELO; cost summed from src/game_arena/*/examples/*/<model>/*/0.info.json usage.cost")
for r in rows:
    if r["model_canonical"] == "gpt-6-astra": meta.update(astra_cost=r["cost_usd"], astra_effort=r["effort"])
    if r["model_canonical"] == "claude-fable-5.1": meta.update(fable51_cost=r["cost_usd"], fable51_effort=r["effort"])
out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=1))
for r in rows[:6]: print(r["model_raw"], r["model_canonical"], r["effort"], r["score"], r["cost_usd"], r["n_tasks"])
