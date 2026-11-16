"""Agentic / coding leaderboards -> data/<benchmark>.csv + .meta.json per SCHEMA.md.
Sources (all in raw/): SWE-bench (leaderboard-data JSON embedded in swebench.com), BFCL (data_overall.csv),
MCPMark (Next.js flight), LMArena text/webdev (flight leaderboard.entries), Scale SEAL (flight entries),
SimpleBench (leaderboard-data.js), SnakeBench (server-rendered table), HAL (server-rendered tables).
Run with ../../env3.12/bin/python from this directory."""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from nextf import flight_text

HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
EFF = ("minimal", "low", "medium", "high", "xhigh", "max", "none")
FETCHED = "2026-09-13"

def canon(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"^(openai|anthropic|google|google deepmind|x-ai|xai|deepseek|moonshotai|moonshot ai|moonshot|qwen|alibaba|z\.?ai|zhipu|meta-llama|meta|mistralai|mistral|minimax|tencent|nvidia|microsoft|amazon|cohere|ai21|baidu|bytedance|stepfun|inclusionai|arcee-ai|perplexity|nousresearch|liquid|ibm|ibm-granite|allenai|opengvlab|thudm|01-ai|xiaomi|reka|writer|sarvam|kimi)[:/]\s*", "", s)
    s = re.sub(r"\((?:fc|prompt|codex|thinking|preview|chat|responses|tool.?calling)\)", "", s)
    s = re.sub(r"\((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?) \d{4}\)", "", s)
    s = re.sub(r"\(?\b(20\d\d-?\d\d-?\d\d)\)?", "", s)  # date stamps
    s = re.sub(r"\b(minimal|low|medium|high|xhigh|x-high|max|none|default|thinking|reasoning|preview|codex)\b", "", s)
    s = re.sub(r"[()*†]", "", s)
    s = re.sub(r"[\s_/:]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    s = re.sub(r"^(?:claude-)?(\d[\d.]*)-(opus|sonnet|haiku)$", r"claude-\2-\1", s)
    s = re.sub(r"^(opus|sonnet|haiku)-(\d[\d.]*)$", r"claude-\1-\2", s)
    s = re.sub(r"^claude-(\d[\d.]*)-(opus|sonnet|haiku)$", r"claude-\2-\1", s)
    s = re.sub(r"^(gpt|gemini|grok|glm|kimi-k|claude-opus|claude-sonnet|claude-haiku|claude-fable|deepseek-v|qwen|llama)-?(\d)-(\d)(?=-|$)", r"\1-\2.\3", s)
    s = re.sub(r"^gpt-?(\d)", r"gpt-\1", s)
    s = re.sub(r"^fable-", "claude-fable-", s)
    s = re.sub(r"^(gpt-6-astra)-(pro)$", r"\1-\2", s)
    return s

def effort_of(name: str) -> str:
    s = name.lower()
    m = re.search(r"\b(minimal|low|medium|high|xhigh|x-high|max|none)\b", s)
    if m:
        e = m.group(1).replace("x-high", "xhigh")
        return e
    return "default"

def write(bench, rows, meta):
    p = Path("data") / f"{bench}.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in HDR})
    m = dict(benchmark=bench, score_higher_better=True, cost_unit=meta.get("cost_unit", ""),
             n_models=len({r["model_canonical"] for r in rows}), astra_cost=None, fable51_cost=None,
             astra_effort=None, fable51_effort=None, fetched=FETCHED, how=meta["how"])
    m.update({k: v for k, v in meta.items() if k not in ("how",)})
    def pick(cn):
        c = [r for r in rows if r["model_canonical"] == cn]
        if not c: return None, None
        # prefer high, then xhigh, max, default, medium
        order = ["high", "xhigh", "max", "default", "medium", "low"]
        c.sort(key=lambda r: order.index(r["effort"]) if r["effort"] in order else 99)
        return (c[0]["cost_usd"] if c[0]["cost_usd"] != "" else None), c[0]["effort"]
    m["astra_cost"], m["astra_effort"] = pick("gpt-6-astra")
    m["fable51_cost"], m["fable51_effort"] = pick("claude-fable-5.1")
    (Path("data") / f"{bench}.meta.json").write_text(json.dumps(m, indent=1))
    tgt = [r for r in rows if r["model_canonical"] in ("gpt-6-astra", "claude-fable-5.1")]
    print(f"{bench}: {len(rows)} rows, {m['n_models']} models, targets={[(r['model_raw'], r['effort'], r['score'], r['cost_usd']) for r in tgt]}")
    return m

def num(s):
    s = re.sub(r"[$,%\s]", "", str(s))
    try: return float(s)
    except ValueError: return ""

# ---------------- SWE-bench
sw = json.load(open("raw/swebench_leaderboard-data.json"))
for board, slug, n_tasks in [("Verified", "swebench_verified", 500), ("Multilingual", "swebench_multilingual", 300)]:
    res = next(b for b in sw if b["name"] == board)["results"]
    rows = []
    for r in res:
        eff = r.get("reasoning_effort") or effort_of(r.get("model_display") or r["name"])
        base = r.get("model_display") or r["name"]
        note = f"agent={r.get('agent')}; tags={'|'.join(r.get('tags') or [])}; date={r.get('date')}"
        if r.get("cost") is not None: note += "; cost is total USD for full run (bash-only/mini-swe-agent rows only)"
        rows.append(dict(benchmark=slug, model_raw=r["name"], model_canonical=canon(base), effort=eff, score=r["resolved"],
                         cost_usd=round(r["cost"], 4) if r.get("cost") is not None else "", cost_unit="total_run" if r.get("cost") is not None else "",
                         n_tasks=n_tasks, source_url="https://www.swebench.com/", note=note))
    write(slug, rows, dict(cost_unit="total_run", how=f"swebench.com <script id=leaderboard-data> JSON, board '{board}': results[].resolved (% resolved), results[].cost (total USD, only for bash-only mini-swe-agent submissions); newest models Claude 4.6 Opus / Gemini 3 Flash / GLM 5; no GPT-6 Astra or Fable 5.1"))

# ---------------- BFCL
rows = []
for r in csv.DictReader(open("raw/bfcl_data_overall.csv")):
    name = r["Model"]
    rows.append(dict(benchmark="bfcl", model_raw=name, model_canonical=canon(name), effort=effort_of(name), score=num(r["Overall Acc"]),
                     cost_usd=num(r["Total Cost ($)"]), cost_unit="total_run", n_tasks="", source_url="https://gorilla.cs.berkeley.edu/leaderboard.html",
                     note=f"rank={r['Rank']}; latency_mean_s={r['Latency Mean (s)']}; multi_turn={r['Multi Turn Acc']}; live={r['Live Acc']}; (FC)=native function calling, (Prompt)=prompting mode"))
write("bfcl", rows, dict(cost_unit="total_run", how="gorilla.cs.berkeley.edu/data_overall.csv (loaded by leaderboard.html index_main.js): Overall Acc, Total Cost ($) for the whole BFCL run; newest models Claude Opus 4.5 / GPT-5.x; no GPT-6 Astra or Fable 5.1"))

# ---------------- MCPMark
t = open("raw/mcpmark_leaderboard.flight.txt").read()
i = t.find('"columns":["filesystem"')
j = t.rfind("{", 0, i)
d, _ = json.JSONDecoder().raw_decode(t, j)
# total tasks: sum of per-service total_tasks for the first model
svc = []
for m in re.finditer(r'"total_tasks":', t):
    o, _ = json.JSONDecoder().raw_decode(t, t.rfind("{", 0, m.start()))
    svc.append(o)
tasks_by_model = {}
for o in svc:
    if "model" not in o or "total_tasks" not in o: continue
    tasks_by_model.setdefault(o["model"], 0); tasks_by_model[o["model"]] += o["total_tasks"]
rows = []
for r in d["data"]:
    name = r["name"]
    rows.append(dict(benchmark="mcpmark", model_raw=name, model_canonical=canon(r.get("actualModelName") or name), effort=effort_of(name),
                     score=round(r["passAtOne"]["avg"] * 100, 2), cost_usd=round(r["perRunCost"], 4), cost_unit="total_run",
                     n_tasks=tasks_by_model.get(name, ""), source_url="https://mcpmark.ai/leaderboard",
                     note=f"score=pass@1 avg over 4 runs (std {r['passAtOne']['std']}); pass@4={r.get('passAtFour')}; pass^4={r.get('passHatFour')}; actual_model={r.get('actualModelName')}; cost=USD per single full run; page titled 'Legacy Leaderboard', updated 12/15/2025"))
write("mcpmark", rows, dict(cost_unit="total_run", how="mcpmark.ai/leaderboard Next.js flight: 'Legacy Leaderboard' table data[] with passAtOne.avg and perRunCost (USD per full run over all services); n_tasks = sum of per-service total_tasks; newest model gpt-5.2-high (Dec 2025); no GPT-6 Astra or Fable 5.1"))

# ---------------- LMArena text / webdev
for fn, slug, url in [("raw/lmarena_text.flight.txt", "lmarena_text", "https://lmarena.ai/leaderboard/text"),
                      ("raw/lmarena_webdev.flight.txt", "lmarena_webdev", "https://lmarena.ai/leaderboard/code/webdev")]:
    t = open(fn).read()
    m = re.search(r'"leaderboard":\{"arenaSlug":"([^"]+)","leaderboardSlug":"([^"]+)","params":\{[^}]*\},"category":"[^"]*","id":"([^"]+)","entries":\[', t)
    arr, _ = json.JSONDecoder().raw_decode(t, m.end() - 1)
    rows = []
    for e in arr:
        name = e["modelDisplayName"]
        rows.append(dict(benchmark=slug, model_raw=name, model_canonical=canon(name), effort=effort_of(name), score=round(e["rating"], 2),
                         cost_usd="", cost_unit="", n_tasks="", source_url=url,
                         note=f"score is Arena Elo ({m.group(3).split('/')[3]}); rank={e['rank']} ({e['rankLower']}-{e['rankUpper']}); ci=[{e['ratingLower']:.1f},{e['ratingUpper']:.1f}]; votes={e['votes']}; org={e.get('modelOrganization')}; list price in/out per M = {e.get('inputPricePerMillion')}/{e.get('outputPricePerMillion')}"))
    write(slug, rows, dict(cost_unit="", how=f"{url} Next.js flight: leaderboard.entries[] (rating, votes, rank) for snapshot {m.group(3)}; no cost column (only list prices)"))

# ---------------- Scale SEAL (boards with both targets)
sc = json.load(open("raw/scale_entries.json"))
for fn, slug, title in [("scale_humanitys_last_exam.html", "scale_hle", "Humanity's Last Exam"),
                        ("scale_humanitys_last_exam_text_only.html", "scale_hle_text_only", "Humanity's Last Exam (Text Only)"),
                        ("scale_prbench-finance.html", "scale_prbench_finance", "Professional Reasoning Benchmark - Finance"),
                        ("scale_prbench-legal.html", "scale_prbench_legal", "Professional Reasoning Benchmark - Legal")]:
    rows = []
    for e in sc[fn]:
        name = e["model"].strip()
        rows.append(dict(benchmark=slug, model_raw=name, model_canonical=canon(name), effort=effort_of(name), score=e["score"], cost_usd="", cost_unit="",
                         n_tasks="", source_url=f"https://scale.com/leaderboard/{fn[6:-5]}",
                         note=f"rank={e['rank']}; ci=+/-{e.get('confidenceInterval_upper')}; company={e.get('company')}; created={e.get('createdAt')}; "
                              + (f"calibration_error={e['calibrationError']}; " if 'calibrationError' in e else "")
                              + (f"contamination_warning; " if e.get('contaminationMessage') else "")))
    write(slug, rows, dict(cost_unit="", how=f"labs.scale.com/leaderboard/{fn[6:-5]} Next.js flight: entries[] (model, score, rank, ci) for '{title}'; no cost column"))

# ---------------- SimpleBench
js = open("raw/simplebench_leaderboard-data.js").read()
lb = re.search(r"const leaderboardData = \[(.*?)\];", js, re.S).group(1)
mm = re.search(r"const modelMeta = \{(.*?)\n\};", js, re.S).group(1)
meta_by = {}
for m in re.finditer(r'"([^"]+)":\s*\{\s*input:\s*([\d.]+),\s*output:\s*([\d.]+),\s*released:\s*"([^"]*)",\s*est:\s*(true|false),\s*tout:\s*([\d.]+),\s*cpr:\s*([\d.]+)', mm):
    meta_by[m.group(1)] = dict(inp=m.group(2), out=m.group(3), released=m.group(4), est=m.group(5), tout=m.group(6), cpr=float(m.group(7)))
rows = []
for m in re.finditer(r'\{\s*rank:\s*"([^"]*)",\s*model:\s*"([^"]*)",\s*score:\s*"([^"]*)",\s*organization:\s*"([^"]*)",\s*dateAdded:\s*(null|"[^"]*")', lb):
    rank, name, score, org, added = m.groups()
    if not org: continue  # human baselines
    mt = meta_by.get(name, {})
    rows.append(dict(benchmark="simplebench", model_raw=name, model_canonical=canon(name), effort=effort_of(name), score=num(score),
                     cost_usd=mt.get("cpr", ""), cost_unit="total_run" if mt else "", n_tasks="", source_url="https://simple-bench.com/",
                     note=f"score=AVG@5 accuracy; rank={rank}; org={org}; added={added.strip(chr(34))}; cost=site's 'cpr' ($ per full benchmark run, computed by site from OpenRouter list prices in/out {mt.get('inp')}/{mt.get('out')} per M, tout={mt.get('tout')}, est={mt.get('est')})"))
write("simplebench", rows, dict(cost_unit="total_run", how="simple-bench.com/static/js/leaderboard-data.js: leaderboardData[] (score) joined with modelMeta[].cpr ($ per full benchmark run, site-computed from OpenRouter prices; chart axis label '$ per full benchmark run (log)')"))

# ---------------- SnakeBench
rows = []
for r in json.load(open("raw/snakebench_rows.json")):
    if r[0] == "#": continue
    rank, name = r[0], re.sub(r"^HREF=/models/", "", r[1])
    name = name[: len(name) // 2].strip() if name[: len(name) // 2].strip() == name[len(name) // 2 :].strip() else name.split("  ")[0].strip()
    name = re.sub(r"^(HREF=)?", "", name)
    w, l = r[4].split("/")
    games = int(w) + int(l)
    cost = num(r[8])
    rows.append(dict(benchmark="snakebench", model_raw=name, model_canonical=canon(name), effort=effort_of(name), score=num(r[2]),
                     cost_usd=cost, cost_unit="total_run", n_tasks=games, source_url="https://snakebench.com/",
                     note=f"score=TrueSkill exposed rating (sigma {r[3]}); rank={rank}; W/L={r[4]}; win%={r[5]}; apples={r[6]}; best={r[7]}; cost=total $ over all {games} games (n_tasks=games played, so cost/n_tasks = $ per game)"))
write("snakebench", rows, dict(cost_unit="total_run", how="snakebench.com server-rendered table (#, Model, Rating=TrueSkill exposed, sigma, W/L, Win%, Apples, Best, Cost=total $); newest models GPT-5.5 / Gemini 3.1 Pro / Claude Opus 4.5; no GPT-6 Astra or Fable 5.1"))

# ---------------- HAL
hal = json.load(open("raw/hal_tables.json"))
HAL_URL = {"hal_assistantbench.html": "assistantbench", "hal_corebench_hard.html": "corebench_hard", "hal_gaia.html": "gaia", "hal_online_mind2web.html": "online_mind2web",
           "hal_scicode.html": "scicode", "hal_scienceagentbench.html": "scienceagentbench", "hal_swebench.html": "swebench_verified_mini", "hal_taubench.html": "taubench_airline", "hal_usaco.html": "usaco"}
for fn, page in HAL_URL.items():
    tab = hal[fn]; hdr = [h.split(" ")[0] for h in tab[0]]
    ia = next(k for k, h in enumerate(tab[0]) if h.startswith("Accuracy")); ic = next(k for k, h in enumerate(tab[0]) if h.startswith("Cost"))
    im = 2; iruns = next(k for k, h in enumerate(tab[0]) if h.startswith("Runs"))
    rows = []
    for r in tab[1:]:
        model = r[im]; scaffold = re.sub(r"\s*(Pareto optimal|Submitted by.*|Download main\.py)", "", r[1]).strip()
        acc = re.match(r"[\d.]+%", r[ia]); cost = re.match(r"\$([\d,.]+)", r[ic])
        rows.append(dict(benchmark=f"hal_{page}", model_raw=model, model_canonical=canon(model), effort=effort_of(model), score=num(acc.group(0)) if acc else "",
                         cost_usd=num(cost.group(1)) if cost else "", cost_unit="total_run" if cost else "", n_tasks="", source_url=f"https://hal.cs.princeton.edu/{page}",
                         note=f"rank={r[0]}; scaffold={scaffold}; runs={r[iruns]}; raw_acc={r[ia]}; raw_cost={r[ic]}; cost is total API USD over all tasks; one row per (scaffold, model)"))
    write(f"hal_{page}", rows, dict(cost_unit="total_run", how=f"hal.cs.princeton.edu/{page} server-rendered leaderboard table: Accuracy %, Cost (USD) total over all tasks, per (scaffold, primary model); newest models Claude Opus 4.5 / Sonnet 4.5 / GPT-5; no GPT-6 Astra or Fable 5.1"))
