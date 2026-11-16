# Benchmark cost vs alignment (demo, fetched 2026-09-13–14)

Plot: `cost_vs_alignment.png` / `.pdf`. Results table: `alignment_results.csv`. Pairwise agreement: `pairwise_tau.csv`, overlap counts: `overlap_matrix.csv`.

Figures show point estimates by default, without CI bars or interval labels.
Bootstrap intervals remain in the results CSVs. Pass `--show-ci` to include
them in a figure, optionally with `--out` to keep a separate uncertainty view.

Percentage-scored benchmarks are marked saturated when their top five selected
models all score strictly above 90%; no score-spread condition applies.
Saturated boards remain plotted as small faint markers and enter the consensus,
but are excluded from the plotted Pareto frontier.

Small numbers beside points refer to stable IDs in `benchmark_ids.json`.
The same IDs appear in both panels and the top-20 figure. New costed boards
receive new IDs without renumbering existing boards. `benchmark_table.csv`
and `benchmark_table_top20.csv` export IDs, benchmark names, alignment and cost
values for a later LaTeX table; no table is drawn inside the figure.

## Additional benchmarks (2026-09-14)

`build_september_additions.py` rebuilds Three.js Eval and Normal CAD Arena from
archived sources in `raw/september_additions/`. Metadata records source hashes.
Run it before `alignment_plot.py` to reproduce these additions offline.

- Three.js Eval uses blind pairwise ratings and is classified `arena (pairwise)`.
  The September 14 API snapshot contains 20 model/effort entries; the usual
  effort selection applies. Astra's effort is unspecified and Fable's is high,
  so the pair is flagged mixed. The combined mean generation cost is $5.3421545
  per evaluation. The count of priced generations is unverified, so it appears
  only in the per-unit panel; vote counts are not generation counts.
- Normal CAD Arena is classified `individual`: geometry and editability are
  verified independently. Both target models use max effort and completed
  90 trials (18 parts across five CAD platforms). Their combined cost is
  $24.83/trial, or approximately $2,234.70 for the pass. Means are source-rounded.
  Native harnesses differ. Its experimental DeepSeek V4 Flash Vision entry is
  kept distinct from text-only DeepSeek variants, avoiding an unsupported match.

Both boards enter the leave-one-out consensus, so other alignments are also
recomputed. DuelLab was added; see the cost
follow-up below. Original September 13 snapshots stay frozen.

## Cost denominator correction (2026-09-14)

See [COST_AUDIT.md](COST_AUDIT.md) for sourced counts, calculations, exclusions,
and scope limitations. The denominator audit restored 14 previously missing
benchmarks (27 → 41 points). After the additions and cost follow-up below, the panels contain
47 per-unit points and 43 total-cost points; eight per-unit points lack a
defensible total, and four boards have only total costs. Missing points are marked explicitly, and
`cost_coverage.csv` / `cost_coverage_top20.csv` explain coverage for every board.

After running any source parsers, apply the reviewed enrichment before plotting:

```bash
cd analysis/benchmark_cost_alignment
../../env3.12/bin/python enrich_cost_data.py
../../env3.12/bin/python alignment_plot.py
../../env3.12/bin/python alignment_plot.py --top-k 20
../../env3.12/bin/python -m unittest test_cost_accounting.py
```

The enrichment checks cached-source hashes against `cost_count_sources.json`.
If a source changes, review its split and cost unit before updating the manifest.
It changes current `data/` only; historical snapshots retain their original data.
The total axis now says **estimated benchmark-pass API cost**: it does not
promise full infrastructure/judging cost or the cost of reproducing every
score-estimation repetition. Finance Agent v2, for example, averages three runs,
while its plotted cost estimates one pass over 450 held-out questions.

## Pipeline
1. `raw/` holds the downloaded pages/JSON. Re-fetch with the curl lines in the session log or the per-source scripts.
2. Parsers write `data/<benchmark>.csv` + `.meta.json` in the schema of `SCHEMA.md`:
   - `parse_easy.py` -> weirdml (public CSV), or_gpqa_diamond (OpenRouter flight JSON), terminal_bench_4 (tbench flight JSON)
   - `build_arc.py` -> arc_agi_1/2/3 from https://arcprize.org/media/data/leaderboard/v{1,2,3}.json
   - `matharena_build.py` -> matharena (IRT capability + expected cost from the index page's `releasePoints`), plus 41 per-competition files
   - `build_arena.py` -> game_arena (ours): Median ELO from analysis/results_tmp/plots_somerset_sept_5/models/rating_df.csv, cost = mean OpenRouter usage.cost per generated bot (100 bots per model)
   - agent_arena, frontiercode (from /data/frontiercode-leaderboard/data.json), aicd, vals_index (home page Astro props + per-model pages), real_swe: written by one-off extraction; see meta.json `how`
3. `enrich_cost_data.py` applies sourced cost denominators and component totals; run it after source parsers.
4. `alignment_plot.py` (run with `../../env3.12/bin/python`): canonicalises model names, selects preferred effort (breaking ties by score),
   converts to within-benchmark scaled ranks, builds a leave-one-out consensus (mean scaled rank over the other benchmarks), and reports
   Kendall tau / Spearman / Pearson of each benchmark against the consensus on shared models (min 5). Cost = Astra + Fable 5.1 at matched
   effort (prefers high, then xhigh, max, default, medium), per task and, where a task count is published, total run.

## Original collection notes (historical; current coverage is above)
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

## Snapshots
`snapshots/<name>/data/` is a frozen copy of `data/` at that date, with the plot and results regenerated from it.
Re-plot any snapshot with the current script: `python alignment_plot.py --snapshot sep_13 [--top-k 20] [--exclude a,b] [--only a,b]`.
`alignment_plot_frozen.py` in the snapshot folder is the script as it was on that date, in case the live script changes semantics.
- `sep_13`: 40 benchmarks (12 hand-pulled + Strautomata + 27 Artificial Analysis leaf evals), the first full demo plot.
New benchmark data goes into `data/` as before; the live plot picks up everything there except `matharena_*` sub-tables.

## Sources added after sep_13 (2026-09-13, later the same day)
- `build_vals.py` -> 34 `vals_<bench>.csv` leaf boards from the Vals benchmark pages (Astro island props); cost per test on nearly all rows. `vals_index` is now excluded from the consensus by default (composite of 7 of these).
- `build_epoch.py` -> 15 `epoch_*.csv` from https://epoch.ai/data/benchmarks.csv and benchmark_data.zip. Score only: Epoch publishes no cost and its token columns are empty for the new models. `epoch_eci` and the superseded FrontierMath v1 boards are excluded by default.
- `build_recheck.py` -> deepswe, vending_bench_2, chessbench, or_tau2_bench_airline, kagi_llm, aider_polyglot, swe_rebench, livebench. Only livebench has both target models and cost.
- `build_agentic.py` -> hal_* (9), swebench_verified, swebench_multilingual, bfcl, mcpmark, snakebench, lmarena_text, lmarena_webdev, scale_* (4), simplebench. None of the cost-tracking agent boards list the new models; LMArena/Scale/SimpleBench do (SimpleBench cost is the site's list-price estimate).
- `build_new_boards.py` -> bughunt, kilobench, lech_debate (cost read off a chart, +-10%), lech_nyt_connections, lech_short_story, clockbench, designarena_gamedev, designarena_3d.
Composite/superseded boards are dropped via DEFAULT_EXCLUDE in alignment_plot.py; `--include-composites` keeps them.

## Cost follow-up (2026-09-14)

`build_cost_followup.py` rebuilds DuelLab and PINNACLE from archived sources in
`raw/cost_followup/`; source hashes and assumptions are recorded in their metadata.
Run it before the alignment script, alongside `build_september_additions.py`.

- DuelLab GameBench 2: ranked entries from the mixed full-freedom track in release
  `gb2-20260910-43fc3ba818c2`; 146 reasoning variants, with provisional entries excluded.
  Pairwise rating, not percentage accuracy. XHigh Astra + Fable costs $6.3245167
  per equally weighted game/setting cell and $59.1665579 across recorded priced
  generation runs. The total is published separately: multiplying the mean by
  run count is invalid because repetitions have unequal weights. These are list-price
  estimates including repairs and excluding infrastructure failures. Historical
  effort provenance does not establish identical provider settings across models.
- PINNACLE: Model Score across KAMI and RIKER; their component boards are not separately
  included in our consensus. Published input-equivalent and output token usage,
  multiplied by the source's September 13 API rate card, gives $1.51172 for Astra max
  and $2.46331 for Fable thinking: $3.97503 combined **per correct task**. This differs
  from cost per attempted task. Fable's input usage is explicitly source-estimated;
  its detailed provenance is not embedded in the public page. Cache discounts are
  already incorporated into input-equivalent tokens; cache-write premiums are omitted.
  No defensible additive total is available. Openweight rental costs are not
  treated as API costs. The target effort pair is mixed.

`cost_followup_availability.json` records the remaining-source investigation:
Epoch's current export has 24 target-model rows and no measured token fields or
linked logs; Scale HLE describes token budgets without measured usage; LMArena
and DesignArena expose prices without target evaluation usage. AA Harvey LAB
has Fable token counts but no Astra score/counts in the captured payload; MMMU Pro
has Astra counts but no Fable counts. Vals Index has both costs but remains excluded
because its components already enter the consensus. Absence here means not recovered
from the checked public sources, not proof that the benchmark owners lack the data.
