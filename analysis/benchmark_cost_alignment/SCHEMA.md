# Output schema for data/<benchmark>.csv

One row per (model, effort) entry on the leaderboard. Columns (exact header, in order):

benchmark,model_raw,model_canonical,effort,score,cost_usd,cost_unit,n_tasks,source_url,note

- benchmark: short slug, e.g. arc_agi_1, arc_agi_2, matharena, agent_arena, frontiercode, aicd, vals_index, real_swe
- model_raw: the name exactly as shown on the site
- model_canonical: lowercase, vendor-free, `<family>-<version>[-<variant>]`. Examples:
  gpt-6-astra, gpt-6-astra-pro, gpt-5.5, gpt-5.4-mini, claude-fable-5.1, claude-fable-5, claude-opus-5,
  claude-opus-4.7, claude-sonnet-4.6, gemini-3.1-pro, gemini-3-flash, grok-5, deepseek-v4, qwen-3.5-397b, kimi-k3, glm-5.
  Do NOT put effort/thinking level into model_canonical. Date-stamped previews: drop the date unless it disambiguates two live versions.
- effort: one of none|minimal|low|medium|high|xhigh|max|default. Use `default` when the site does not say.
- score: the primary leaderboard number (percent 0-100 for accuracies; Elo/score as-is otherwise). Empty if unknown.
- cost_usd: dollar cost as a float. Empty if not published for that row.
- cost_unit: what cost_usd is per, e.g. per_task, per_problem, per_rollout, per_test, per_prompt, total_run, median_per_task
- n_tasks: count of cost-bearing executions in one pass of the evaluated split, or model-specific observed debate count. Multiply only additive mean costs by this count. Do not use grading substeps, public+test size, or a median as if it were a mean.
- source_url: page the row came from
- note: anything odd (e.g. "cost is total for run", "score is Elo", "provider adapter")

Also write data/<benchmark>.meta.json: {"benchmark":..., "score_higher_better": true/false, "cost_unit":..., "n_models":..., "astra_cost": ..., "fable51_cost": ..., "astra_effort":..., "fable51_effort":..., "fetched": "2026-09-13", "how": "<one line on where the numbers live>"}

After source parsing, run `enrich_cost_data.py`. Reviewed rows gain an optional
`cost_total_usd` column (blank unless a separately computed total is needed).
This total takes precedence over multiplication. `weighted_per_test` preserves
a source's weighted per-unit cost but cannot be multiplied by `n_tasks`;
Code Migration instead sums its CLI and COBOL component costs.
`median_per_task` is also nonadditive. Unknown units do not get implicit totals.

The enrichment records `cost_audit` in each reviewed metadata file, with source
URL, cached evidence SHA-256, split/count rationale, and remaining caveats.
See `cost_count_sources.json` and `COST_AUDIT.md`. One-pass estimates do not
include extra score-estimation repetitions, unreported judges or infrastructure.
