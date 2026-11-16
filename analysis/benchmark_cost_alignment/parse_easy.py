"""Parse WeirdML CSV, OpenRouter GPQA Diamond flight JSON, Terminal-Bench 4.0 flight JSON into data/*.csv per SCHEMA.md"""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from nextf import flight_text, find_objects

HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
EFFORTS = {"none","minimal","low","medium","high","xhigh","max","default","no_thinking","thinking"}

def canon(name: str) -> str:
    """Rough canonicalisation; effort must be stripped by caller."""
    s = name.lower().strip()
    s = re.sub(r"^(openai|anthropic|google|x-ai|xai|deepseek|moonshotai|moonshot|qwen|alibaba|z-ai|zhipu|meta-llama|meta|mistralai|mistral|minimax|tencent|nvidia|microsoft|amazon|cohere|ai21|baidu|bytedance|stepfun|inclusionai|arcee-ai|perplexity|nousresearch|liquid|ibm-granite|allenai|opengvlab|thudm|01-ai)[:/]\s*", "", s)
    s = s.replace("claude ", "claude-").replace(" ", "-").replace("_", "-")
    s = re.sub(r"[()]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def write(bench, rows, meta):
    p = Path("data") / f"{bench}.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in HDR})
    meta = dict(benchmark=bench, n_models=len({r["model_canonical"] for r in rows}), fetched="2026-09-13", **meta)
    for r in rows:
        if r["model_canonical"] == "gpt-6-astra": meta.setdefault("astra_cost", r["cost_usd"]); meta.setdefault("astra_effort", r["effort"])
        if r["model_canonical"] == "claude-fable-5.1": meta.setdefault("fable51_cost", r["cost_usd"]); meta.setdefault("fable51_effort", r["effort"])
    (Path("data") / f"{bench}.meta.json").write_text(json.dumps(meta, indent=1))
    print(bench, len(rows), "rows", meta.get("astra_cost"), meta.get("fable51_cost"))

# ---- WeirdML
rows, seen = [], set()
for r in csv.DictReader(open("raw/weirdml.csv")):
    key = r["internal_model_name"]
    if key in seen: continue
    seen.add(key)
    base, _, eff = key.partition(":")
    eff = eff or "default"
    if eff not in EFFORTS: eff_note, eff = f"raw effort={eff}", "default"
    else: eff_note = ""
    rows.append(dict(benchmark="weirdml", model_raw=r["display_name"], model_canonical=canon(base), effort=eff,
                     score=round(float(r["avg_acc"])*100, 3), cost_usd=r["cost_per_run_usd"], cost_unit="per_run",
                     n_tasks=17, source_url="https://htihle.github.io/data/weirdml_data.csv",
                     note=f"api={r['API source']}; se={r['avg_acc_standard_error']}; {eff_note}"))
write("weirdml", rows, dict(score_higher_better=True, cost_unit="per_run", how="public CSV; cost_per_run_usd is mean over the 17 tasks x 5 runs per task"))

# ---- OpenRouter GPQA Diamond
txt = flight_text(open("raw/or_gpqa.html", encoding="utf-8", errors="ignore").read())
objs = find_objects(txt, ["avgCostPerTask", "modelPermaslug"])
best = {}
for o in objs:
    # keep one row per model permaslug: prefer highest runCount, then auto-routing
    k = o["modelPermaslug"]
    cur = best.get(k)
    score = (o.get("runCount") or 0, o.get("providerName") == "auto-routing")
    if cur is None or score > cur[0]: best[k] = (score, o)
rows = []
for k, (_, o) in best.items():
    raw = o["modelName"]
    slug = o.get("modelSlug") or o["modelPermaslug"]
    eff = "default"
    m = re.search(r"\((?:reasoning[- ])?(\w+)\)$", raw.lower()) or re.search(r"[:/-](minimal|low|medium|high|xhigh|max)$", slug)
    if m and m.group(1) in EFFORTS: eff = m.group(1)
    c = canon(re.sub(r"\s*\(.*?\)\s*$", "", slug))
    c = re.sub(r"-(minimal|low|medium|high|xhigh|max)$", "", c)
    rows.append(dict(benchmark="or_gpqa_diamond", model_raw=raw, model_canonical=c, effort=eff,
                     score=round(o["accuracy"]*100, 3), cost_usd=o["avgCostPerTask"], cost_unit="per_task", n_tasks=198,
                     source_url="https://openrouter.ai/benchmarks/gpqa-diamond",
                     note=f"provider={o['providerName']}; runs={o['runCount']}; permaslug={k}"))
write("or_gpqa_diamond", rows, dict(score_higher_better=True, cost_unit="per_task", how="JSON in Next.js flight payload; one row per model permaslug, provider with most runs"))

# ---- Terminal-Bench 4.0
txt = flight_text(open("raw/tbench.html", encoding="utf-8", errors="ignore").read())
objs = find_objects(txt, ["metrics", "total_cost_usd", "model_display"])
rows = []
for o in objs:
    md, m = o["metadata"], o["metrics"]
    model = md["model_display"]["label"]; agent = md["agent_display"]["label"]
    rows.append(dict(benchmark="terminal_bench_4", model_raw=f"{model} ({agent})", model_canonical=canon(model), effort=md.get("reasoning_effort") or "default",
                     score=m["accuracy"], cost_usd=m["total_cost_usd"], cost_unit="total_run", n_tasks=m["n_trials"],
                     source_url="https://www.tbench.ai/leaderboard",
                     note=f"agent={agent}; ci95={m.get('accuracy_ci95_half_width')}; tokens={m.get('total_tokens')}; date={md.get('date')}"))
write("terminal_bench_4", rows, dict(score_higher_better=True, cost_unit="total_run", how="JSON in flight payload; official TB4.0 leaderboard, cost is total for n_trials trials"))
