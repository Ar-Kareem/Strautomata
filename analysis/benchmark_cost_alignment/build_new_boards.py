"""Build data/<slug>.csv + .meta.json for boards discovered on 2026-09-13 (raw pages under raw/new/).

Boards: bughunt (Bug Hunt Bench), kilobench (Kilo Code KiloBench / TB2 via Kilo harness), lech_debate,
lech_nyt_connections (extended), lech_short_story, clockbench, designarena_* (only if Astra present).
"""
import csv, json, re, html, os

RAW = "raw/new"
OUT = "data"
FETCHED = "2026-09-13"
COLS = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "default"}


def canon(name):
    """Vendor-free lowercase canonical name; effort stripped."""
    s = name.lower()
    s = re.sub(r"\(.*?\)", " ", s)              # drop (high), (xhigh reasoning), ($$$$), (new) ...
    s = re.sub(r"\b(non-reasoning|no reasoning|reasoning|thinking)\b.*$", " ", s)
    if not s.startswith("qwen"):  # "Qwen 3.8 Max" is a model name, not an effort
        s = re.sub(r"\b(max|high|xhigh|medium|low|minimal)\s*(effort)?\s*$", " ", s)
    s = re.sub(r"[§†‡¶^*]", "", s)
    s = re.sub(r"^claude (\d[\d.]*) (haiku|sonnet|opus)", r"claude-\2-\1", s)
    s = s.replace("claude ", "").replace("openai ", "").replace("tencent ", "").replace("xiaomi ", "")
    s = s.replace("bytedance ", "").replace("baidu ", "").replace("alibaba ", "").replace("moonshotai ", "")
    s = re.sub(r"\b(with fallback|preview)\b", " ", s)  # date-stamped previews keep the date only if it disambiguates
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    # family normalisations
    s = s.replace("gpt 5.6", "gpt-5.6").replace("gpt-5.6-sol", "gpt-5.6-sol")
    s = s.replace("claude-fable", "fable").replace("fable 5.1", "fable-5.1").replace("fable 5", "fable-5")
    s = re.sub(r"^fable-", "claude-fable-", s)
    s = re.sub(r"^opus ", "claude-opus-", s)
    s = re.sub(r"^sonnet ", "claude-sonnet-", s)
    s = s.replace("gpt-6 astra", "gpt-6-astra")
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s


def effort_from(name, default="default"):
    n = name.lower()
    if re.search(r"non-reasoning|no reasoning|\(none\)", n):
        return "none"
    m = re.search(r"\((none|minimal|low|medium|high|xhigh|max)\b", n)
    if m:
        return m.group(1)
    if not n.startswith("qwen"):
        m = re.search(r"\b(max|high|xhigh|medium|low|minimal)\s*(effort)?\s*$", n)
        if m:
            return m.group(1)
    return default


def write(slug, rows, meta):
    rows = [dict(zip(COLS, r)) if isinstance(r, (list, tuple)) else r for r in rows]
    with open(f"{OUT}/{slug}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})
    astra = [r for r in rows if r["model_canonical"] == "gpt-6-astra"]
    fab = [r for r in rows if r["model_canonical"] == "claude-fable-5.1"]

    def best(rs):
        if not rs:
            return None, None
        r = max(rs, key=lambda x: float(x["score"]) if x["score"] != "" else -1e9)
        return (r["cost_usd"] if r["cost_usd"] != "" else None), r["effort"]

    ac, ae = best(astra)
    fc, fe = best(fab)
    m = {"benchmark": slug, "score_higher_better": True, "cost_unit": meta.get("cost_unit", ""),
         "n_models": len({r["model_canonical"] for r in rows}), "astra_cost": ac, "fable51_cost": fc,
         "astra_effort": ae, "fable51_effort": fe, "fetched": FETCHED, "how": meta["how"]}
    m.update({k: v for k, v in meta.items() if k not in m})
    with open(f"{OUT}/{slug}.meta.json", "w") as f:
        json.dump(m, f, indent=1)
    print(slug, len(rows), "rows;", m["n_models"], "models; astra", ac, ae, "; fable", fc, fe)


# ---------------------------------------------------------------- Bug Hunt Bench
def bughunt():
    d = json.load(open(f"{RAW}/bughunt_benchmark.json"))
    url = "https://github.com/phuryn/bug-hunt-bench"
    rows = []
    for r in d["runs"]:
        note = f"harness={r['harness']}; wall_min={r['wall_min']}; cost_kind={r.get('cost_kind')}; extras={r.get('extras')}; date={r.get('date')}"
        if r.get("superseded"):
            note += f"; superseded={r['superseded']}"
        if r.get("caveat"):
            note += f"; caveat={r['caveat']}"
        if r.get("note"):
            note += f"; note={r['note']}"
        eff = r.get("effort") or "default"
        if eff not in EFFORTS:
            note += f"; effort_raw={eff}"
            eff = "default"
        score = round(100.0 * r["fixed"] / 105, 2)
        rows.append([
            "bughunt", f"{r['model']} ({r.get('effort') or 'default'})", canon(r["model"]), eff, score,
            r["cost_usd"] if r.get("cost_usd") is not None else "", "total_run", 105, url,
            "score = fixed/105 as percent; cost is total for the full 105-bug run (list-price equivalent); " + note])
    write("bughunt", rows, {"cost_unit": "total_run", "n_tasks": 105,
          "how": "data/benchmark.json in github.com/phuryn/bug-hunt-bench (runs[]: model, harness, effort, fixed/105, cost_usd, wall_min). 105 real bugs across two repos; model runs inside its own CLI, graded blind. Score converted to percent of 105; cost = total run cost (list-price equivalent)."})


# ---------------------------------------------------------------- KiloBench
def kilobench():
    h = open(f"{RAW}/kilobench.html").read()
    tx = html.unescape(re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)))
    i = tx.find("1 GPT-6 Astra")
    seg = tx[i:tx.find("Results at a glance")]
    found = re.findall(r"(\d+) (.+?) (\d+\.\d)% \$(\d+\.\d+)", seg)
    url = "https://kilo.ai/kilobench"
    rows = []
    seen = set()
    for rank, name, comp, cost in found:
        if len(name) > 60 or name in seen:  # page repeats the table (chart list + official table); skip prose captures
            continue
        seen.add(name)
        clean = re.sub(r"\s*\((\$+|new|50% off|free|retires [^)]*)\)", "", name).strip()
        rows.append(["kilobench", name, canon(clean), "default", float(comp), float(cost), "total_run", 89, url,
                     "Terminal Bench 2.0 tasks run through Kilo Code's own agent harness; cost = real bill per full attempt (89 tasks, incl. reasoning tokens and context re-sends); effort not stated"])
    write("kilobench", rows, {"cost_unit": "total_run", "n_tasks": 89,
          "how": "HTML table on https://kilo.ai/kilobench (also https://kilo.ai/leaderboard/llm.txt top-10): Rank / Model / Completion % / Cost per attempt. Eval suite = Terminal Bench 2.0 (89 tasks) run end-to-end in Kilo's harness; cost per attempt is the real bill for one full pass."})


# ---------------------------------------------------------------- Lech Mazur: Debate
DEBATE_COST_FROM_CHART = {  # read off images/debate_price_vs_performance png (log x-axis), USD per completed debate, approx
    "Claude Fable 5.1 (high)": 0.31, "Claude Fable 5 (high)": 0.32, "Claude Opus 5 (high)": 0.18, "Kimi K3": 0.25,
    "GPT-5.6 Sol (high)": 0.10, "GPT-6 Astra (high)": 0.19, "GLM-5.3 (high)": 0.023, "GLM-5.2 (max)": 0.052,
    "Muse Spark 1.1 (high)": 0.055, "Muse Spark 1.3 (high)": 0.06, "Grok 4.6 (high)": 0.15, "Claude Sonnet 5 (high)": 0.10,
    "Tencent Hy4 Preview (high)": 0.15, "DeepSeek V4 Pro 0813 (high)": 0.07, "Qwen 3.8 Max": 0.15, "Gemini 3.8 Flash (high)": 0.08,
    "Gemini 3.1 Pro Preview": 0.19, "Grok 4.5 (high)": 0.08, "Gemini 3.7 Flash (high)": 0.065, "Qwen 3.7 Max": 0.10,
    "Gemini 3.5 Flash": 0.11, "Xiaomi MiMo V2.5 Pro": 0.009, "MiniMax-M3": 0.015, "DeepSeek V4 Pro Preview": 0.017,
    "ByteDance Seed2.0 Pro": 0.018, "Baidu Ernie 5.1": 0.035, "Step 3.7 Flash (high)": 0.021, "Tencent Hy3 Preview (high)": 0.0045,
    "Gemini 3.1 Flash-Lite Preview": 0.005, "GPT-OSS-120B": 0.004, "Mistral Large 3": 0.01, "Mistral Medium 3.5 (high)": 0.27,
}


def lech_debate():
    md = open(f"{RAW}/lech_debate_leaderboard.md").read()
    url = "https://github.com/lechmazur/debate"
    rows = []
    for line in md.splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", line)
        if not m:
            continue
        rank, name, bt, gl, rd, avail, adj, pg, topics, opp = m.groups()
        cost = DEBATE_COST_FROM_CHART.get(name, "")
        note = f"score is Bradley-Terry rating; glicko2={gl}; RD={rd}; avail={avail}; adjBT={adj}; matchups={pg}; topics={topics}"
        if cost != "":
            note += "; cost read off the price-vs-performance chart (log axis), approx +-10%, avg debater-side USD per completed debate"
        rows.append(["lech_debate", name, canon(name), effort_from(name), float(bt), cost, "per_debate", "", url, note])
    write("lech_debate", rows, {"cost_unit": "per_debate", "score_is": "Bradley-Terry rating",
          "how": "reports/debate_leaderboard__judge_judge_blend_glm53_coverage_20260904a__debate_all_templates.md in github.com/lechmazur/debate (BT ratings, 52 models). Cost is NOT published as a table: only in images/debate_price_vs_performance__*.png (32 costed models, x = avg debater-side USD per completed debate, log axis); values here were read off that chart by eye."})


# ---------------------------------------------------------------- Lech Mazur: NYT Connections extended
def lech_nyt():
    md = open(f"{RAW}/lech_nyt.md").read()
    url = "https://github.com/lechmazur/nyt-connections"
    sec = md[md.find("### Leaderboard: Extended Version"):md.find("### Leaderboard: Newest 100")]
    rows = []
    for line in sec.splitlines():
        m = re.match(r"\|(\d+)\|(.+?)\|([\d.]+)\|(\d+)\|", line)
        if not m:
            continue
        rank, name, score, n = m.groups()
        rows.append(["lech_nyt_connections", name, canon(name), effort_from(name), float(score), "", "", int(n), url,
                     "Extended NYT Connections (940 puzzles, harder prompt); no cost published"])
    write("lech_nyt_connections", rows, {"cost_unit": "", "n_tasks": 940,
          "how": "README.md 'Leaderboard: Extended Version' table (models that completed all 940 puzzles) in github.com/lechmazur/nyt-connections. No cost/token data."})


# ---------------------------------------------------------------- Lech Mazur: short story
def lech_story():
    md = open(f"{RAW}/lech_story.html").read()  # raw README markdown despite the extension
    url = "https://github.com/lechmazur/writing"
    rows = []
    for line in md.splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(-?[\d.]+)\s*\|\s*(\d+)%\s*\|\s*(.+?)\s*\|", line)
        if not m:
            continue
        rank, name, score, win, ci = m.groups()
        clean = re.sub(r"[§†‡¶^]+$", "", name).strip()
        rows.append(["lech_short_story", name, canon(clean), effort_from(clean), float(score), "", "", 400, url,
                     f"score is Thurstone comparison score (win chance vs pool {win}%; CI {ci}); 400 stories; no cost published"])
    write("lech_short_story", rows, {"cost_unit": "", "n_tasks": 400,
          "how": "README.md ranking table in github.com/lechmazur/writing (Short-Story Creative Writing Benchmark v4; Thurstone comparison score, 400 prompts, LLM-judged pairwise). data/leaderboard.csv is an older snapshot without Fable 5.1/Astra. No cost data."})


# ---------------------------------------------------------------- ClockBench
def clockbench():
    js = open(f"{RAW}/clockbench_page.js").read()
    m = re.search(r'r=\[\{name:"Human Baseline".*?\}\]', js)
    arr = m.group(0)[2:]
    items = re.findall(r'\{name:"([^"]+)",lab:"([^"]*)",url:"[^"]*",validAccuracy:([\d.]+)(?:,isHuman:!0)?\}', arr)
    url = "https://clockbench.ai/"
    rows = []
    for name, lab, acc in items:
        if name == "Human Baseline":
            continue
        rows.append(["clockbench", name, canon(name), effort_from(name), float(acc), "", "", "", url,
                     f"lab={lab}; score = valid-clock accuracy %; human baseline 90.7; no cost published"])
    write("clockbench", rows, {"cost_unit": "",
          "how": "Model array embedded in /_next/static/chunks/app/page-*.js on https://clockbench.ai (name, lab, validAccuracy). Analog-clock reading benchmark; effort is the suffix in the name (Max/High). No cost data."})


# ---------------------------------------------------------------- Design Arena (Elo, no cost)
def designarena(cat):
    d = json.load(open(f"{RAW}/da_lb_{cat}.json"))
    names = json.load(open(f"{RAW}/da_model_names.json"))
    url = f"https://www.designarena.ai/leaderboard?category={cat}"
    slug = f"designarena_{cat}"
    rows = []
    for r in d["data"]:
        mid = r["modelId"]
        raw = names.get(mid, mid)
        eff = "default"
        if (mid.endswith(("-xhigh", "-max", "-high", "-medium", "-low", "-none")) and not mid.startswith("qwen")) or "(xhigh)" in raw or "(max)" in raw:
            eff = effort_from(raw) if "(" in raw else mid.rsplit("-", 1)[1]
        base = mid if mid.startswith("qwen") else re.sub(r"-(xhigh|max|high|medium|low|none)$", "", mid)
        base = re.sub(r"-thinking$", "", base)
        canon_id = base.replace("claude-fable-5-1", "claude-fable-5.1").replace("claude-opus-4-", "claude-opus-4.").replace("claude-sonnet-4-", "claude-sonnet-4.")
        canon_id = canon_id.replace("deepseek-v4-1-flash", "deepseek-v4.1-flash").replace("gpt-5-6", "gpt-5.6")
        note = f"score is Bradley-Terry 'Elo'; wins={r['wins']}; losses={r['losses']}; battles={r['battles']}; winRate={r['winRate']}; btStdErr={r['btStdErr']}; no cost published"
        if mid == raw and not any(ch.isdigit() for ch in mid):
            note += "; anonymous codename model"
        rows.append([slug, raw, canon_id, eff, r["elo"], "", "", "", url, note])
    write(slug, rows, {"cost_unit": "", "score_is": "Bradley-Terry Elo",
          "how": f"POST https://www.designarena.ai/api/leaderboard with {{arenaType:'models', category:'{cat}'}} (found in the site's JS chunks); JSON data[] of modelId/wins/losses/battles/winRate/elo/btStdErr. Crowd-voted head-to-head design tournaments. Model names are the API modelIds (some are anonymous codenames); effort is a suffix in the id where present (e.g. gpt-5.6-sol-xhigh); the Astra entry is labelled 'GPT-6 Astra (xhigh)' on its model page. lastUpdateTime={d['metadata'].get('lastUpdateTime')}."})


if __name__ == "__main__":
    bughunt()
    kilobench()
    lech_debate()
    lech_nyt()
    lech_story()
    clockbench()
    designarena("gamedev")
    designarena("3d")
