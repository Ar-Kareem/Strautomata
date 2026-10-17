"""Artificial Analysis leaf evaluations -> data/aa_<eval>.csv
Scores: raw/aa_leaderboard_models.json (646 models, from /leaderboards/models flight payload) overlaid with
raw/aa_models_union.json (118 models from the /evaluations/* pages, which carry extra evals + canonicalEvalTokenCounts).
Cost: computed from canonicalEvalTokenCounts x list prices (USD per 1M): non-cached input at price1mInputTokens,
cache hits (cacheableInput*cacheHitRate) at cacheHitPrice, cache writes (rest of cacheableInput) at cacheWritePrice,
answer+reasoning at price1mOutputTokens. This mirrors AA's stated breakdown (input, cache hit, cache write, reasoning, answer)."""
import csv, json, re
from pathlib import Path
HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
lb = {o["slug"]: o for o in json.load(open("raw/aa_leaderboard_models.json"))}
un = {o["slug"]: o for o in json.load(open("raw/aa_models_union.json"))}
models = {}
for slug in set(lb) | set(un):
    m = dict(lb.get(slug, {})); m.update({k: v for k, v in un.get(slug, {}).items() if v is not None}); models[slug] = m

# eval key -> (benchmark slug, score field, token-count key, n_tasks, score kind, page slug)
EVALS = {
 "aa_gpqa_diamond":   ("gpqa", "gpqa", 198, "frac", "gpqa-diamond"),
 "aa_hle":            ("hle", "hle", None, "frac", "humanitys-last-exam"),
 "aa_lcr":            ("lcr", "lcr", 100, "frac", "artificial-analysis-long-context-reasoning"),
 "aa_critpt":         ("critpt", "critpt", None, "frac", "critpt"),
 "aa_scicode":        ("scicode", "scicode", 338, "frac", "scicode"),
 "aa_mmmu_pro":       ("mmmuPro", "mmmuPro", None, "frac", "mmmu-pro"),
 "aa_omniscience":    ("omniscience", "omniscience", 6000, "index", "omniscience"),
 "aa_gdpval":         ("gdpvalNormalized", "gdpval", 220, "normalized", "gdpval-aa"),
 "aa_tau3_banking":   ("tauBanking", "tauBanking", 97, "frac", "tau3-banking"),
 "aa_terminalbench_v21": ("terminalbenchV21", "terminalbenchV21", 89, "frac", "terminalbench-v2-1"),
 "aa_terminalbench_v40": ("terminalbenchV40", "terminalbenchV40", 66, "frac", "terminalbench-v4-0"),
 "aa_analyst_agent":  ("analystAgent", "analystAgent", 80, "frac", "aa-analyst-agent"),
 "aa_briefcase":      ("briefcaseElo", "briefcase", 91, "elo", "aa-briefcase"),
 "aa_mlcr":           ("mlcrOverall", "mlcr", None, "frac", "mlcr-aa"),
 "aa_automationbench":("automationBenchPartialScore", "automationBench", 657, "frac", "automationbench-aa"),
 "aa_gdp_pdf":        ("gdpPdfAllPass", "gdpPdf", 100, "frac", "gdp-pdf"),
 # score-only (no token counts published in payload)
 "aa_ifbench":        ("ifbench", None, None, "frac", "ifbench"),
 "aa_tau2":           ("tau2", None, None, "frac", "tau2-bench"),
 "aa_apex_agents":    ("apexAgents", None, 452, "frac", "apex-agents-aa"),
 "aa_itbench":        ("itbenchSre", None, None, "frac", "itbench-aa"),
 "aa_terminalbench_hard": ("terminalbenchHard", None, None, "frac", "terminalbench-hard"),
 "aa_aime25":         ("aime25", None, 30, "frac", "aime-2025"),
 "aa_livecodebench":  ("livecodebench", None, None, "frac", "livecodebench"),
 "aa_mmlu_pro":       ("mmluPro", None, None, "frac", "mmlu-pro"),
 "aa_math500":        ("math500", None, 500, "frac", "math-500"),
 "aa_harvey_lab":     ("harveyLab", None, None, "frac", "harvey-lab-aa"),
 "aa_enterprise_ops_gym": ("enterpriseOpsGym", None, None, "frac", "enterprise-ops-gym-aa"),
 "aa_global_mmlu_lite": ("globalMmluLiteScore", None, None, "frac", "global-mmlu-lite"),
}
EFF = {"low","medium","high","xhigh","max","minimal","none"}

def parse(name):
    """-> (base name, effort, note)"""
    m = re.search(r"\(([^)]*)\)\s*$", name)
    base, eff, note = name, "default", ""
    if m:
        inner = m.group(1); base = name[:m.start()].strip()
        toks = [t.strip().lower() for t in inner.split(",")]
        for t in toks:
            w = t.replace(" effort", "").replace("reasoning effort ", "").strip()
            if w in EFF: eff = w
            elif t in ("thinking", "reasoning"): eff = "thinking"
        note = inner
    return base, eff, note

def cost(m, key):
    tc = (m.get("canonicalEvalTokenCounts") or {}).get(key)
    if not tc or m.get("price1mInputTokens") is None: return None, ""
    pin, pout = m["price1mInputTokens"], m["price1mOutputTokens"]
    inp, ans, rea = tc["input"] or 0, tc["answer"] or 0, tc["reasoning"] or 0
    cache = tc.get("cacheableInput") or 0
    rate = m.get("cacheHitRate") or 0
    phit = m.get("cacheHitPrice"); pwrite = m.get("cacheWritePrice")
    phit = pin if phit is None else phit; pwrite = pin if pwrite is None else pwrite
    hits, writes = cache * rate, cache * (1 - rate)
    c = ((inp - cache) * pin + hits * phit + writes * pwrite + (ans + rea) * pout) / 1e6
    return c, f"tokens in={inp} cacheable={cache} hitrate={rate:.3f} ans={ans} reas={rea}; prices in={pin} out={pout} hit={phit} write={pwrite}"

summary = []
for bench, (sf, tk, n, kind, page) in EVALS.items():
    rows = []
    for slug, m in models.items():
        s = m.get(sf)
        if s is None: continue
        base, eff, pnote = parse(m["name"])
        score = s * 100 if kind == "frac" else s
        c, cnote = cost(m, tk) if tk else (None, "")
        per_task = c / n if (c is not None and n) else None
        rows.append(dict(benchmark=bench, model_raw=m["name"], model_canonical=base.lower().replace(" ", "-"), effort=eff,
                         score=round(score, 4), cost_usd=round(per_task, 6) if per_task is not None else (round(c, 4) if c is not None else ""),
                         cost_unit="per_task" if per_task is not None else ("total_run" if c is not None else ""), n_tasks=n or "",
                         source_url=f"https://artificialanalysis.ai/evaluations/{page}",
                         note=f"score kind={kind}; slug={slug}; {pnote}; {cnote}; deprecated={m.get('deprecated')}"))
    if len(rows) < 8: continue
    with open(f"data/{bench}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader(); w.writerows(rows)
    meta = dict(benchmark=bench, score_higher_better=True, cost_unit="per_task" if n else "total_run", n_models=len({r["model_canonical"] for r in rows}),
                n_rows=len(rows), fetched="2026-09-13", how=f"AA /leaderboards/models + /evaluations/{page} flight payloads; field {sf}; cost from canonicalEvalTokenCounts[{tk}] x list prices; n_tasks={n}")
    for r in rows:
        if r["model_canonical"] == "gpt-6-astra" and r["effort"] == "high": meta.update(astra_cost=r["cost_usd"], astra_effort="high")
        if r["model_canonical"] == "claude-fable-5.1" and r["effort"] == "high": meta.update(fable51_cost=r["cost_usd"], fable51_effort="high")
    Path(f"data/{bench}.meta.json").write_text(json.dumps(meta, indent=1))
    summary.append((bench, len(rows), meta.get("astra_cost"), meta.get("fable51_cost"), n))
for s in summary: print(*s)
