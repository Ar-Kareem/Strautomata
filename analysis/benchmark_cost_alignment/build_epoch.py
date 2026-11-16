"""Epoch AI Benchmarking Hub -> data/epoch_<benchmark>.csv (+ data/epoch_eci.csv)
Sources (fetched 2026-09-13, saved under raw/):
  https://epoch.ai/data/benchmarks.csv        (raw/epoch_benchmarks.csv)  one row per Epoch-internal run, all benchmarks, incl. billable token columns
  https://epoch.ai/data/benchmark_data.zip    (raw/epoch_benchmark_data/) same runs split per benchmark + model_metadata.csv + benchmark_metadata.csv + ECI files
  https://epoch.ai/data/eci_scores.csv        (raw/epoch_eci_scores.csv)  Epoch Capabilities Index per model
Cost: Epoch publishes no cost column. Token columns (billable_input_tokens/billable_output_tokens/cache_*) are filled for only 12 runs
(all SimpleQA Verified, none for GPT-6 Astra / Claude Fable 5.1). The per-run Inspect .eval logs that would carry stats.model_usage
are not publicly fetchable today (S3 403, logs.epoch.ai 405) and the newest runs (Astra, Fable 5.1) have no log link at all.
Formula that would apply when tokens exist: cost_usd = (billable_input_tokens x in_price + billable_output_tokens x out_price) / 1e6,
with list prices GPT-6 Astra $10/$50 and Claude Fable 5.1 $10/$50 per 1M in/out. No such row exists, so cost_usd is blank everywhere."""
import csv, json, re
from pathlib import Path
import pandas as pd

HDR = "benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note".split(",")
RAW = Path("raw"); OUT = Path("data")
PRICES = {"gpt-6-astra": (10.0, 50.0), "claude-fable-5.1": (10.0, 50.0)}  # USD per 1M input/output tokens
EFF_ORDER = ["high", "xhigh", "max", "default", "medium", "low", "minimal", "none"]  # tie-break, mirrors alignment_plot.PREFERRED_EFFORT

# Epoch task name -> (slug, page url, n_tasks, note)
B = "https://epoch.ai/benchmarks/"
BENCH = {
 "GPQA diamond":                      ("epoch_gpqa_diamond", B+"gpqa-diamond", 198, "scorer=choice"),
 "FrontierMath-Tiers-1-3-v2-Private": ("epoch_frontiermath_tiers_1_3_v2", B+"frontiermath-tiers-1-3-v2", 285, "private set (295 minus 10 public); scorer=verification_code"),
 "FrontierMath-Tier-4-v2-Private":    ("epoch_frontiermath_tier_4_v2", B+"frontiermath-tier-4-v2", 41, "private set (43 minus 2 public); scorer=verification_code"),
 "FrontierMath-2025-02-28-Private":   ("epoch_frontiermath_v1_private", "https://epoch.ai/data/benchmarks.csv", 290, "v1 private tiers 1-3 (superseded by v2 2026-06-12, no live page); scorer=verification_code"),
 "FrontierMath-Tier-4-2025-07-01-Private": ("epoch_frontiermath_tier_4_v1_private", "https://epoch.ai/data/benchmarks.csv", 48, "v1 private tier 4 (superseded by v2 2026-06-12, no live page); scorer=verification_code"),
 "SWE-Bench verified":                ("epoch_swe_bench_verified", B+"swe-bench-verified", 500, "scorer=swe_bench_scorer; some older runs used 477/489-task subsets"),
 "OTIS Mock AIME 2024-2025":          ("epoch_otis_mock_aime", B+"otis-mock-aime-2024-2025", 45, "scorer=model_extracted_exact_match or model_graded"),
 "SimpleQA Verified":                 ("epoch_simpleqa_verified", B+"simple-qa-verified", 1000, "scorer=simpleqa_scorer"),
 "MATH level 5":                      ("epoch_math_level_5", B+"math-level-5", 1324, "best across scorers (normalized_string_match/sympy_equiv/model_graded_equiv)"),
 "Chess Puzzles":                     ("epoch_chess_puzzles", B+"chess-puzzles", 100, "scorer=model_extracted_exact_match"),
 "Mystery Game Puzzles":              ("epoch_mystery_game_puzzles", B+"mystery-game-puzzles", 100, "scorer=agent_submitted_next_move_scorer or exact_match_next_move_scorer"),
 "EBR-bench":                         ("epoch_ebr_bench", B+"ebr-bench", None, "Earthborne Rangers v2; scorer=ebr_scorer"),
 "MirrorCode":                        ("epoch_mirrorcode", B+"mirrorcode", 30, "scorer=solve_at_100"),
 "FrontierMath-Erdos":                ("epoch_frontiermath_erdos", B+"frontiermath-erdos", 68, "scorer=proof_scorer"),
}
# skipped (degenerate for a consensus): FrontierMath-*-Public (10 / 2 problems), OEIS Open / OEIS Open Lite (3 / 5 runs)

df = pd.read_csv(RAW / "epoch_benchmarks.csv", low_memory=False)
meta = pd.read_csv(RAW / "epoch_benchmark_data" / "model_metadata.csv").set_index("model_version")["display_name"].to_dict()

def split_effort(mid: str):
    m = re.match(r"^(.*)_(none|minimal|low|medium|high|xhigh|max)$", mid)
    return (m.group(1), m.group(2)) if m else (mid, "default")

def canon(base: str) -> str:
    s = re.sub(r"\([^)]*\)", "", base.lower()).strip().split("/")[-1]
    s = re.sub(r"_\d+k$", "", s)                         # thinking-budget variants (_16k/_32k...) -> note, not name
    s = re.sub(r"-(web-?app)$", "-web", s)
    s = re.sub(r"-\d{4}-\d{2}-\d{2}(?=-|$)", "", s)    # -2025-08-07 (anywhere)
    s = re.sub(r"-\d{8}$", "", s)                        # -20250929
    s = re.sub(r"-pre-release$", "", s)
    s = re.sub(r"^(claude-[a-z]+-\d+)-(\d+)(?=-|$)", r"\1.\2", s)  # claude-fable-5-1 -> claude-fable-5.1
    s = re.sub(r"^(gpt|gemini|grok|glm|kimi-k)-(\d+)-(\d+)(?=-|$)", r"\1-\2.\3", s)
    return re.sub(r"-+", "-", s).strip("-")

def cost_for(canon_name, row):
    ti, to = row["billable_input_tokens"], row["billable_output_tokens"]
    if pd.isna(ti) or pd.isna(to): return None, ""
    tok = f"tokens in={int(ti)} out={int(to)} cache_read={row['cache_read_tokens'] if pd.notna(row['cache_read_tokens']) else 'na'}"
    if canon_name in PRICES:
        pi, po = PRICES[canon_name]
        return (ti * pi + to * po) / 1e6, tok + f"; cost=in*{pi}+out*{po} per 1M"
    return None, tok + "; no list price on file, cost left blank"

summary = {}
for task, (slug, url, n_tasks, bnote) in BENCH.items():
    d = df[df.task == task].sort_values("started_at")
    d = d.drop_duplicates("model", keep="last")   # 1 row per model version; only SWE-bench has 2 repeated runs
    rows = []
    for _, r in d.iterrows():
        base, eff = split_effort(r["model"])
        disp = r["Display name"] if pd.notna(r["Display name"]) else None
        if disp is None:
            for k in (r["model"], base):
                v = meta.get(k)
                if isinstance(v, str) and v.strip(): disp = v; break
            if disp is None: disp = r["model"]
            elif eff != "default" and f"({eff})" not in disp: disp = f"{disp} ({eff})"
        c = canon(base)
        cost, tnote = cost_for(c, r)
        bm = re.search(r"_(\d+k)$", base, re.I)
        notes = [bnote, f"thinking budget {bm.group(1).lower()} (Epoch model_version suffix; not an effort level)" if bm else "", f"model_version={r['model']}", f"run={r['id_runs']}", f"started={str(r['started_at'])[:10]}", f"scores={r['Scores']}", tnote]
        rows.append({"benchmark": slug, "model_raw": disp, "model_canonical": c, "effort": eff,
                     "score": round(float(r["Best score (across scorers)"]) * 100, 4),
                     "cost_usd": "" if cost is None else round(cost, 6), "cost_unit": "total_run" if cost is not None else "",
                     "n_tasks": n_tasks if n_tasks else "", "source_url": url, "note": "; ".join(n for n in notes if n)})
    rows.sort(key=lambda x: -x["score"])
    with open(OUT / f"{slug}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HDR); w.writeheader(); w.writerows(rows)

    def pick(name):
        rs = [x for x in rows if x["model_canonical"] == name]
        if not rs: return None
        rs.sort(key=lambda x: (-x["score"], EFF_ORDER.index(x["effort"]) if x["effort"] in EFF_ORDER else 99))
        return rs[0]
    a, fb = pick("gpt-6-astra"), pick("claude-fable-5.1")
    m = {"benchmark": slug, "score_higher_better": True, "cost_unit": "total_run", "n_models": len({x["model_canonical"] for x in rows}),
         "n_rows": len(rows), "n_tasks": n_tasks, "astra_cost": a["cost_usd"] or None if a else None, "fable51_cost": fb["cost_usd"] or None if fb else None,
         "astra_effort": a["effort"] if a else None, "fable51_effort": fb["effort"] if fb else None,
         "astra_present": a is not None, "fable51_present": fb is not None, "fetched": "2026-09-13",
         "how": f"Epoch AI Benchmarking Hub run table https://epoch.ai/data/benchmarks.csv (task='{task}'), 'Best score (across scorers)' x100; page {url}; "
                "no cost: Epoch publishes token counts for only 12 SimpleQA runs (none for Astra/Fable 5.1) and the per-run .eval logs are not publicly fetchable"}
    json.dump(m, open(OUT / f"{slug}.meta.json", "w"), indent=1)
    summary[slug] = (len(rows), m["n_models"], a, fb, [x for x in rows if x["model_canonical"] in ("gpt-6-astra", "claude-fable-5.1")])

# ---- ECI (composite)
e = pd.read_csv(RAW / "epoch_eci_scores.csv")
rows = []
for _, r in e.iterrows():
    rows.append({"benchmark": "epoch_eci", "model_raw": r["Display name"], "model_canonical": canon(re.sub(r"[\s]+", "-", str(r["Model"]).strip().lower())),
                 "effort": "default", "score": r["eci"], "cost_usd": "", "cost_unit": "", "n_tasks": "", "source_url": "https://epoch.ai/data/eci_scores.csv",
                 "note": f"COMPOSITE: Epoch Capabilities Index (IRT over ~50 benchmarks, anchors Claude 3.5 Sonnet=130 / GPT-5=150); 90% CI {r['eci_ci_low']}-{r['eci_ci_high']}; date={r['date']}; org={r['Organization']}"})
rows.sort(key=lambda x: -x["score"])
with open(OUT / "epoch_eci.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HDR); w.writeheader(); w.writerows(rows)
a = next((x for x in rows if x["model_canonical"] == "gpt-6-astra"), None); fb = next((x for x in rows if x["model_canonical"] == "claude-fable-5.1"), None)
json.dump({"benchmark": "epoch_eci", "score_higher_better": True, "cost_unit": "", "n_models": len(rows), "n_rows": len(rows), "astra_cost": None, "fable51_cost": None,
           "astra_effort": "default" if a else None, "fable51_effort": "default" if fb else None, "astra_present": a is not None, "fable51_present": fb is not None,
           "fetched": "2026-09-13", "composite": True,
           "how": "https://epoch.ai/data/eci_scores.csv column eci (Epoch Capabilities Index, composite of ~50 benchmarks via IRT; docs https://epoch.ai/data/eci-documentation); no per-model effort or cost"},
          open(OUT / "epoch_eci.meta.json", "w"), indent=1)
summary["epoch_eci"] = (len(rows), len(rows), a, fb, [x for x in rows if x["model_canonical"] in ("gpt-6-astra", "claude-fable-5.1")])

for slug, (nr, nm, a, fb, tr) in summary.items():
    print(f"\n== {slug}: {nr} rows / {nm} models | Astra: {'YES' if a else 'no'} | Fable 5.1: {'YES' if fb else 'no'}")
    for x in tr: print("   ", {k: x[k] for k in ("model_raw", "model_canonical", "effort", "score", "cost_usd")})
