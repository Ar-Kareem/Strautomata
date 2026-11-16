# Benchmark cost vs alignment (demo, fetched 2026-09-13)

Plot: `cost_vs_alignment.png` / `.pdf`. Results table: `alignment_results.csv`. Pairwise agreement: `pairwise_tau.csv`, overlap counts: `overlap_matrix.csv`.

## Pipeline
1. `raw/` holds the downloaded pages/JSON. Re-fetch with the curl lines in the session log or the per-source scripts.
2. Parsers write `data/<benchmark>.csv` + `.meta.json` in the schema of `SCHEMA.md`:
   - `parse_easy.py` -> weirdml (public CSV), or_gpqa_diamond (OpenRouter flight JSON), terminal_bench_4 (tbench flight JSON)
   - `build_arc.py` -> arc_agi_1/2/3 from https://arcprize.org/media/data/leaderboard/v{1,2,3}.json
   - `matharena_build.py` -> matharena (IRT capability + expected cost from the index page's `releasePoints`), plus 41 per-competition files
   - `build_arena.py` -> game_arena (ours): Median ELO from analysis/results_tmp/plots_somerset_sept_5/models/rating_df.csv, cost = mean OpenRouter usage.cost per generated bot (100 bots per model)
   - agent_arena, frontiercode (from /data/frontiercode-leaderboard/data.json), aicd, vals_index (home page Astro props + per-model pages), real_swe: written by one-off extraction; see meta.json `how`
3. `alignment_plot.py` (run with `../../env3.12/bin/python`): canonicalises model names, keeps each model's best score per benchmark,
   converts to within-benchmark scaled ranks, builds a leave-one-out consensus (mean scaled rank over the other benchmarks), and reports
   Kendall tau / Spearman / Pearson of each benchmark against the consensus on shared models (min 5). Cost = Astra + Fable 5.1 at matched
   effort (prefers high, then xhigh, max, default, medium), per task and, where a task count is published, total run.

## Caveats
- ARC-AGI-1 and ARC-AGI-2 share 83 models and agree at tau 0.88, so they pull the consensus toward each other.
- Only 11 leaf-ish benchmarks in the consensus; vals_index is itself a composite of 27 Vals evals.
- Effort differs across sites (see marker shape). Terminal-Bench has Fable 5.1 only at max.
- "Per task" means different things per site (a GPQA question vs a Terminal-Bench trial vs an Arena session).
- Model-name canonicalisation is regex based (`canon()` in alignment_plot.py); check `combined.csv` column `model` for merges/misses.
- Artificial Analysis (10-16 more leaf evals) is not included: cost only in rendered charts, needs a browser scrape.

## Artificial Analysis (added later)
`build_aa.py` -> `data/aa_<eval>.csv` for 27 leaf evaluations (composite indices excluded). No browser scrape was needed:
- Scores for all ~646 models are embedded in the flight payload of https://artificialanalysis.ai/leaderboards/models (`raw/aa_leaderboard_models.json`).
- Each /evaluations/<slug> page embeds ~30 "chart default" model objects with `canonicalEvalTokenCounts` per eval and list prices
  (`raw/aa_models_union.json`, 118 models incl. Astra and Fable 5.1 at every effort).
- Cost is computed, not read: non-cached input x input price + cache hits x cache-hit price + cache writes x cache-write price
  + (answer + reasoning) x output price, following AA's stated cost breakdown. Treat as an estimate of AA's own numbers.
- n_tasks comes from each eval page's description (GPQA 198, SciCode 338, LCR 100, tau3-Banking 97, TB2.1 89, TB4.0 66, GDPval 220, ...).
  HLE, CritPt, MMMU-Pro and MLCR have no stated count, so only total-run cost is available for them.
- 11 AA evals have scores but no token counts in the payload (IFBench, tau2, AIME25, LiveCodeBench, MMLU-Pro, ...); they enter the consensus but have no cost point.
- Caveat: AA now supplies 27 of 40 benchmarks, so the consensus leans toward AA's model set and methodology. Duplicates across sources
  (or_gpqa_diamond vs aa_gpqa_diamond, terminal_bench_4 vs aa_terminalbench_v40) also inflate each other slightly.
