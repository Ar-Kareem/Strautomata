"""Recheck build (2026-09-13): DeepSWE, Vending-Bench 2, ChessBench, OpenRouter (tau2/browsecomp/hle/deepsearchqa/widesearch),
Kagi, Aider polyglot, SWE-rebench, LiveBench -> data/<slug>.csv + .meta.json per SCHEMA.md"""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from nextf import flight_text, find_objects


HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
EFFORTS = {"none","minimal","low","medium","high","xhigh","max","default"}
FETCHED = "2026-09-13"
R = Path("raw")

def canon(name):
    s = name.lower().strip()
    s = re.sub(r"^(openai|anthropic|google|x-ai|xai|deepseek|moonshotai|moonshot|qwen|alibaba|z-ai|zhipu|meta-llama|meta|mistralai|mistral|minimax|tencent|nvidia|microsoft|amazon|cohere|ai21|baidu|bytedance|stepfun|inclusionai|arcee-ai|perplexity|nousresearch|liquid|ibm-granite|allenai|opengvlab|thudm|01-ai|xiaomi|thinkingmachines|sao10k)[:/]\s*", "", s)
    s = s.replace("claude ", "claude-").replace(" ", "-").replace("_", "-")
    s = re.sub(r"[()\[\]]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def dotver(s):
    """gpt-5-6-sol -> gpt-5.6-sol ; claude-opus-4-8 -> claude-opus-4.8 (join single-digit-single-digit pairs)."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"(?<![\d.])(\d)-(\d{1,2})(?=-|$)", r"\1.\2", s)
    return s

def write(bench, rows, meta):
    p = Path("data") / f"{bench}.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in HDR})
    m = dict(benchmark=bench, n_models=len({r["model_canonical"] for r in rows}), fetched=FETCHED, **meta)
    for key in ("astra_cost","fable51_cost","astra_effort","fable51_effort"): m.setdefault(key, None)
    for r in rows:
        if r["model_canonical"] == "gpt-6-astra" and m["astra_cost"] is None:
            m["astra_cost"] = r["cost_usd"] if r["cost_usd"] != "" else None; m["astra_effort"] = r["effort"]
        if r["model_canonical"] == "claude-fable-5.1" and m["fable51_cost"] is None:
            m["fable51_cost"] = r["cost_usd"] if r["cost_usd"] != "" else None; m["fable51_effort"] = r["effort"]
    (Path("data") / f"{bench}.meta.json").write_text(json.dumps(m, indent=1))
    a = [r for r in rows if r["model_canonical"]=="gpt-6-astra"]; b = [r for r in rows if r["model_canonical"]=="claude-fable-5.1"]
    print(f"\n### {bench}: {len(rows)} rows, {m['n_models']} models; astra={len(a)} fable51={len(b)}")
    for r in a+b: print("   ", ",".join(str(r.get(k,"")) for k in HDR))
    print("    canon:", sorted({r["model_canonical"] for r in rows}))

def num(x):
    try: return float(x)
    except: return ""

# ---------------- 1. DeepSWE (TanStack serialized objects in HTML)
t = (R/"deepswe.html").read_text(encoding="utf-8", errors="ignore")
rows = []
for m in re.finditer(r'\{model:"([^"]*)",harness:"([^"]*)",(?:provider:"[^"]*",)?reasoning_effort:"([^"]*)",config:"([^"]*)",source:"deep-swe"', t):
    nx = t.find('{model:"', m.start()+10); body = t[m.start(): nx if nx > 0 else m.start()+8000]
    g = lambda k: (re.search(k + r":([-\d.e]+|null)", body) or [None, ""])[1]
    model, harness, eff, cfg = m.groups()
    rows.append(dict(benchmark="deepswe", model_raw=f"{model} [{eff}]", model_canonical=dotver(canon(model)), effort=eff if eff in EFFORTS else "default",
                     score=round(float(g("pass_rate"))*100, 2), cost_usd=num(g("mean_cost_usd")), cost_unit="per_task", n_tasks=113,
                     source_url="https://deepswe.datacurve.ai/",
                     note=f"harness={harness}; config={cfg}; pass@1 mean over n_runs={g('n_runs')}; ci_half={g('ci_half')}; median_cost={g('median_cost_usd')}; mean_output_tokens={g('mean_output_tokens')}; mean_agent_steps={g('mean_agent_steps')}"))
write("deepswe", rows, dict(score_higher_better=True, cost_unit="per_task",
      how="Objects {model,harness,reasoning_effort,pass_rate,mean_cost_usd,...} serialized in the SSR HTML (TanStack $R[...] payload) of https://deepswe.datacurve.ai/ (v1.1, 113 tasks, updated Sep 3 2026). score=pass_rate*100 (Pass@1 mean over runs), cost=mean_cost_usd per task."))

# ---------------- 2. Vending-Bench 2 (SvelteKit chunk with per-model final_value)
t = (R/"vending_chunks/DAnYm5vA.js").read_text(encoding="utf-8", errors="ignore")
rows, seen = [], set()
for m in re.finditer(r'"([^"]+)":\{num_epochs:(\d+),num_final_values:(\d+),', t):
    name = m.group(1)
    if name in seen: break            # second object in the chunk (arena / other views) repeats names
    seen.add(name)
    body = t[m.start(): t.find("}", t.find("final_value:", m.start()))]
    g = lambda k: (re.search(k + r":([-\d.e]+)", body) or [None, ""])[1]
    eff, base, note = "default", name, ""
    mm = re.match(r"^(.*?)\s*[-(]\s*(High|Low|Max|Medium|None|Max reasoning)\)?$", name)
    if mm: base, eff = mm.group(1), mm.group(2).split()[0].lower()
    mm = re.match(r"^(.*?)\s*\((Fireworks|Moonshot)\)$", base)
    if mm: base, note = mm.group(1), f"provider={mm.group(2)}; "
    c = canon(base.replace("Custom Tools", "").strip())
    c = re.sub(r"^(gpt|glm|minimax|deepseek)-?", r"\1-", c)
    if "custom tools" in name.lower(): note += "custom tools variant; "
    rows.append(dict(benchmark="vending_bench_2", model_raw=name, model_canonical=c, effort=eff, score=round(float(g("final_value")), 2), cost_usd="", cost_unit="", n_tasks="",
                     source_url="https://andonlabs.com/evals/vending-bench-2",
                     note=note + f"score is mean final money balance USD over {m.group(3)} runs; sem={g('final_value_sem')}; geomean={g('final_value_geomean')}; no cost published"))
write("vending_bench_2", rows, dict(score_higher_better=True, cost_unit="",
      how="Per-model {final_value, final_value_sem, ...} in SvelteKit chunk /_app/immutable/chunks/DAnYm5vA.js (first object = main leaderboard, 63 entries; only 10 rows are server-rendered). score = mean final money balance ($) over 5 runs. No cost column on the site."))

# ---------------- 3. ChessBench (inline JSON array)
t = (R/"chessbench.html").read_text(encoding="utf-8", errors="ignore")
objs = find_objects(t, ["benchmarkElo", "costPerTask"])
rows, seen = [], set()
for o in objs:
    if not isinstance(o, dict) or o.get("model") in seen: continue
    seen.add(o["model"]); name = o["model"]; eff, note = "default", ""
    mm = re.search(r"\((?:reasoning[- ])?(max|high|xhigh|medium|low|minimal)\)|\s(xhigh|high)$", name, re.I)
    if mm: eff = (mm.group(1) or mm.group(2)).lower()
    if re.search(r"no thinking", name, re.I): eff = "none"
    if "Adaptive" in name: note = "adaptive thinking; "
    if "1M" in name: note += "1M context; "
    base = re.sub(r"\s*\((?:reasoning[- ])?[^)]*\)|\s(xhigh|high)$|\s1M$", "", name, flags=re.I).strip()
    c = canon(base); c = c.replace("chatgpt-", "gpt-"); c = re.sub(r"^qwen-", "qwen-", c)
    rows.append(dict(benchmark="chessbench", model_raw=name, model_canonical=c, effort=eff, score=o["benchmarkElo"], cost_usd=o["costPerTask"] if o["costPerTask"] is not None else "",
                     cost_unit="per_task" if o["costPerTask"] is not None else "", n_tasks="", source_url="https://chessbench-ai.github.io/",
                     note=note + f"score is benchmark Elo (field-relative); rank={o['rank']}; provider={o['provider']}; acpl={o['acpl']}" + ("; cost not reported (dash)" if o["costPerTask"] is None else "")))
write("chessbench", rows, dict(score_higher_better=True, cost_unit="per_task",
      how="Inline JSON array [{rank,model,provider,benchmarkElo,acpl,costPerTask}] in https://chessbench-ai.github.io/ (32 models). score=benchmarkElo; cost=costPerTask USD (null -> blank; only some models have cost)."))

# ---------------- 4. OpenRouter: tau2-bench-airline (same shape as gpqa) + 4 search suites (lanes)
def or_effort_from(raw, slug):
    m = re.search(r"\((?:reasoning[- ])?(\w+)\)$", raw.lower()) or re.search(r"[:/-](minimal|low|medium|high|xhigh|max)$", slug)
    return m.group(1) if m and m.group(1) in EFFORTS else "default"

txt = flight_text((R/"or_tau2-bench-airline.html").read_text(encoding="utf-8", errors="ignore"))
best = {}
for o in find_objects(txt, ["avgCostPerTask", "modelPermaslug"]):
    k = o["modelPermaslug"]; sc = (o.get("runCount") or 0, o.get("providerName") == "auto-routing")
    if k not in best or sc > best[k][0]: best[k] = (sc, o)
rows = []
for k, (_, o) in best.items():
    raw = o["modelName"]; slug = o.get("modelSlug") or k; eff = or_effort_from(raw, slug)
    c = re.sub(r"-(minimal|low|medium|high|xhigh|max)$", "", canon(re.sub(r"\s*\(.*?\)\s*$", "", slug)))
    rows.append(dict(benchmark="or_tau2_bench_airline", model_raw=raw, model_canonical=c, effort=eff, score=round(o["accuracy"]*100, 3), cost_usd=o["avgCostPerTask"],
                     cost_unit="per_task", n_tasks=o.get("totalTasks"), source_url="https://openrouter.ai/benchmarks/tau2-bench-airline",
                     note=f"provider={o['providerName']}; runs={o['runCount']}; permaslug={k}"))
write("or_tau2_bench_airline", rows, dict(score_higher_better=True, cost_unit="per_task", how="JSON in Next.js flight payload (objects with modelPermaslug/accuracy/avgCostPerTask/totalTasks); one row per model permaslug, provider with most runs"))

for slug, suite in [("browsecomp","search_browsecomp"),("hle","search_hle"),("deepsearchqa","search_dsqa"),("widesearch","search_widesearch")]:
    txt = flight_text((R/f"or_{slug}.html").read_text(encoding="utf-8", errors="ignore"))
    lanes = [o for o in find_objects(txt, ["model_permaslug", "cost_per_task"]) if isinstance(o, dict) and o.get("suite") == suite]
    best = {}
    for o in lanes:
        k = o["model_permaslug"]; sc = (o.get("runs") or 0, o.get("total_samples") or 0)
        if k not in best or sc > best[k][0]: best[k] = (sc, o)
    rows = []
    for k, (_, o) in best.items():
        eff = o.get("reasoning_effort") or "default"; eff = eff if eff in EFFORTS else "default"
        c = re.sub(r"-\d{8}$", "", canon(k)); c = re.sub(r"-(minimal|low|medium|high|xhigh|max)$", "", c)
        ntask = round(o["total_samples"]/o["runs"]) if o.get("runs") else ""
        rows.append(dict(benchmark=f"or_{slug}", model_raw=k, model_canonical=c, effort=eff, score=round(o["score"]*100, 3), cost_usd=o["cost_per_task"], cost_unit="per_task", n_tasks=ntask,
                         source_url=f"https://openrouter.ai/benchmarks/{slug}",
                         note=f"search_engine={o.get('search_engine')}; surface={o.get('surface')}; max_agent_turns={o.get('max_agent_turns')}; runs={o.get('runs')}; total_samples={o.get('total_samples')}; raw_effort={o.get('reasoning_effort')}; last_run={o.get('last_run_at')}"))
    if len(rows) < 8:
        print(f"\n### or_{slug}: SKIPPED, only {len(rows)} models ({sorted({r['model_canonical'] for r in rows})})"); continue
    write(f"or_{slug}", rows, dict(score_higher_better=True, cost_unit="per_task", how=f"'lanes' JSON in Next.js flight payload of https://openrouter.ai/benchmarks/{slug} (suite={suite}; keys model_permaslug/score/cost_per_task/runs/total_samples/search_engine); one row per model permaslug = lane with most runs. n_tasks = total_samples/runs."))

# ---------------- 5. Kagi LLM benchmark (VitePress markdown chunk)
t = (R/"kagi_chunk.js").read_text(encoding="utf-8", errors="ignore")
tbl = re.search(r"<table.*?</table>", t, re.S).group(0)
rows = []
for tr in re.findall(r"<tr>(.*?)</tr>", tbl, re.S)[1:]:
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
    if len(cells) < 7: continue
    name, acc, cost, tpt, toks, tps, prov = cells[:7]
    base = re.sub(r"\s*\(.*?\)\s*$", "", name); eff, note = "default", ""
    if base.endswith("-thinking"): base = base[:-9]; note = "thinking variant; "
    elif re.search(r"claude|gemini-2-5|gpt-5|grok-4", base): pass
    c = canon(base)
    mm = re.match(r"^claude-(\d)(?:-(\d))?-(opus|sonnet|haiku|fable)$", c)
    if mm: c = f"claude-{mm.group(3)}-{mm.group(1)}" + (f".{mm.group(2)}" if mm.group(2) else "")
    c = dotver(c)
    if "points to gpt 5.3" in name: c = "gpt-5.3-chat"; note += "chatgpt-4o alias -> gpt 5.3; "
    rows.append(dict(benchmark="kagi_llm", model_raw=name, model_canonical=c, effort=eff, score=num(acc), cost_usd=num(cost), cost_unit="total_run", n_tasks=116,
                     source_url="https://help.kagi.com/kagi/ai/llm-benchmark.html",
                     note=note + f"Cost($) column = total for the 116-task offline benchmark; time/task={tpt}s; tokens={toks}; TPS={tps}; provider={prov}"))
thinkers = {r["model_canonical"] for r in rows if "thinking variant" in r["note"]}
for r in rows:
    if r["model_canonical"] in thinkers and "thinking variant" not in r["note"] and r["effort"] == "default": r["effort"] = "none"; r["note"] = "non-thinking variant; " + r["note"]
write("kagi_llm", rows, dict(score_higher_better=True, cost_unit="total_run",
      how="Single <table> (model / %accuracy / Cost($) / time/task / tokens / TPS / provider) inside VitePress chunk /assets/kagi_ai_llm-benchmark.md.*.js (Kagi Offline Benchmark, 116 tasks, task list rev Feb 13 2026). score=%accuracy; cost=Cost($) total."))

# ---------------- 6. Aider polyglot (upstream YAML; page table is the same data)
import yaml  # type: ignore
items = yaml.safe_load((R/"aider_polyglot_leaderboard.yml").read_text())
rows = []
for it in items:
    name = it["model"]; eff = str(it.get("reasoning_effort") or "").lower(); note = f"edit_format={it.get('edit_format')}; date={it.get('date')}; pass_rate_1={it.get('pass_rate_1')}; well_formed={it.get('percent_cases_well_formed')}"
    if eff not in EFFORTS:
        mm = re.search(r"\((high|medium|low|xhigh|max|minimal)\)", name)
        eff = mm.group(1) if mm else ("none" if re.search(r"no ?think", name, re.I) else "default")
    base = re.sub(r"\s*\(.*?\)", "", name); base = re.sub(r"\s*\+.*$", "", base); base = re.sub(r",.*$", "", base)
    base = re.sub(r"-\d{8}$", "", base.strip())
    rows.append(dict(benchmark="aider_polyglot", model_raw=name, model_canonical=dotver(canon(base)), effort=eff, score=num(it.get("pass_rate_2")), cost_usd=num(it.get("total_cost")) if it.get("total_cost") not in (None, 0, 0.0) else "",
                     cost_unit="total_run", n_tasks=it.get("test_cases", 225), source_url="https://aider.chat/docs/leaderboards/", note=note + ("; cost not listed" if it.get("total_cost") in (None,0,0.0) else "")))
write("aider_polyglot", rows, dict(score_higher_better=True, cost_unit="total_run",
      how="polyglot_leaderboard.yml (aider/website/_data, same data as the HTML table on https://aider.chat/docs/leaderboards/). score=pass_rate_2 (%), cost=total_cost USD for the 225-case run. Board is stale: newest entries Aug-Sep 2025 (gpt-5, DeepSeek-V3.2-Exp)."))

# ---------------- 7. SWE-rebench (flight payload items with rangeStats keyed 'from:to')
txt = (R/"swe_rebench.flight.txt").read_text()
i = txt.find('"items":[{"modelId"'); j = txt.find(']', i)  # naive; use decoder
dec = json.JSONDecoder(); items, _ = dec.raw_decode(txt, txt.find('[', i))
rows = []
for it in items:
    fr, to = it["taskRangeTimestamp"]["from"], it["taskRangeTimestamp"]["to"]
    st = it["rangeStats"]["all"].get(f"{fr}:{to}") or {}
    name = it["modelName"]; eff = "default"
    mm = re.search(r"\[(\w+)\]", name)
    if mm and mm.group(1) in EFFORTS: eff = mm.group(1)
    base = re.sub(r"\s*\[.*?\]", "", name); base = re.sub(r"-20\d{2}-\d{2}-\d{2}", "", base)
    mm2 = re.search(r"[- ](minimal|low|medium|high|xhigh|max)$", base)
    if mm2 and eff == "default" and not base.lower().endswith("codex-max"): eff = mm2.group(1); base = base[:mm2.start()]
    if re.search(r"no-thinking", base): eff = "none"
    base = re.sub(r"\s*(no-thinking|thinking)$", "", base)
    c = dotver(canon(base)); c = re.sub(r"^(fable|opus|sonnet|haiku)-", r"claude-\1-", c)
    agent_note = "AGENT/external system row (instance_type=agent); " if it["meta"].get("instance_type") == "agent" else ""
    from datetime import datetime, timezone
    d = lambda ms: datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    rows.append(dict(benchmark="swe_rebench", model_raw=name, model_canonical=c, effort=eff, score=round(st.get("resolvedRate", ""), 2) if st else "", cost_usd=st.get("instanceCosts", "") if st and st.get("instanceCosts") else "",
                     cost_unit="per_task" if st and st.get("instanceCosts") else "", n_tasks="", source_url="https://swe-rebench.com/",
                     note=agent_note + f"agentVersion={it.get('agentVersion')}; developer={it['meta'].get('developer')}; window={d(fr)}..{d(to)} (model's full task window); sem={st.get('sem')}; pass@N={st.get('passN')}; release={it['release'].get('date')}; cost 0/absent -> blank"))
write("swe_rebench", rows, dict(score_higher_better=True, cost_unit="per_task",
      how="items[] in Next.js flight payload of https://swe-rebench.com/ (modelName, taskRangeTimestamp, rangeStats.all['from:to'] -> resolvedRate, instanceCosts). score=resolvedRate over the model's full task window; cost=instanceCosts (avg USD per instance). Site default window not recovered; per-model full window used."))

# ---------------- 8. LiveBench (table_/cost_ CSVs + categories JSON)
cats = json.loads((R/"livebench_categories_2026_06_25.json").read_text())
cost = {r["model"]: r for r in csv.DictReader(open(R/"livebench_cost_2026_06_25.csv"))}
rows = []
for r in csv.DictReader(open(R/"livebench_table_2026_06_25.csv")):
    name = r["model"]
    catavg = []
    for cat, tasks in cats.items():
        vals = [float(r[t]) for t in tasks if r.get(t) not in (None, "", "nan")]
        if vals: catavg.append(sum(vals)/len(vals))
    score = round(sum(catavg)/len(catavg), 3)
    cr = cost.get(name, {}); cpq = num(cr.get("cost_per_question", ""))
    nq = sum(int(float(cr[k])) for k in cr if k.startswith("nq_") and cr[k]) if cr else ""
    s = name.lower(); eff = "default"
    mm = re.search(r"-(xhigh|high|medium|low|minimal|max)(?:-effort)?$", s)
    if mm: eff = mm.group(1); s = s[:mm.start()]
    if re.search(r"-(no-?thinking|nothinking)$", s): eff = "none"
    note = ""
    if "thinking" in s: note = "thinking variant; "
    s = re.sub(r"-thinking(-auto|-\d+k)?$|-thinking(-auto|-\d+k)?-", "-", s).strip("-")
    s = re.sub(r"-20\d{6}$|-20\d{2}-\d{2}-\d{2}", "", s); s = re.sub(r"-\d+k$", "", s)
    c = dotver(canon(s))
    rows.append(dict(benchmark="livebench", model_raw=name, model_canonical=c, effort=eff, score=score, cost_usd=cpq, cost_unit="per_task" if cpq != "" else "", n_tasks=nq,
                     source_url="https://livebench.ai/", note=note + f"score = mean of 7 category means (2026-06-25 release); cost_per_question from cost_2026_06_25.csv; in=${cr.get('input_price_per_million','')}/M out=${cr.get('output_price_per_million','')}/M; cost_per_successful_task={cr.get('cost_per_successful_task','')}"))
write("livebench", rows, dict(score_higher_better=True, cost_unit="per_task",
      how="https://livebench.ai/table_2026_06_25.csv (per-task scores) + cost_2026_06_25.csv (cost_per_question, computed from token usage x list price) + categories_2026_06_25.json. score = mean over 7 category means (each = mean of its tasks), which is how the site computes Global Average."))
