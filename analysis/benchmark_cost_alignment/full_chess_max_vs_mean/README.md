# Full chess round robin: top-1 bot vs mean-of-bots as the model score

Source: `analysis/results_tmp/plots_full_nsquared_sept_25/bots/rating_df.csv` (260 bots, 52 models, all 5 automata per model, 67,860 games).
Each variant is scored against the leave-one-out consensus of the external boards in `../data/` (game_arena removed, so both face the same consensus). Same code path as `../alignment_plot.py`.

Agreement between the two model rankings themselves: Kendall tau = 0.763, Spearman = 0.910 over 52 models.

## Alignment with the benchmark consensus

| variant                                    | top_k   |   n_overlap |   kendall_tau |   tau_lo |   tau_hi |   spearman |   tau_z |   rank_among_boards |   n_boards |
|:-------------------------------------------|:--------|------------:|--------------:|---------:|---------:|-----------:|--------:|--------------------:|-----------:|
| chess_max                                  | all     |          43 |         0.654 |    0.483 |    0.799 |      0.806 |    0.43 |                  47 |        125 |
| chess_max                                  | 10      |          10 |         0.494 |    0.028 |    0.85  |      0.663 |    0.62 |                  38 |        125 |
| chess_top2mean                             | all     |          43 |         0.669 |    0.514 |    0.805 |      0.83  |    0.55 |                  38 |        125 |
| chess_top2mean                             | 10      |          10 |         0.467 |   -0.1   |    0.897 |      0.612 |    0.51 |                  43 |        125 |
| chess_top3mean                             | all     |          43 |         0.641 |    0.487 |    0.772 |      0.818 |    0.33 |                  54 |        125 |
| chess_top3mean                             | 10      |          10 |         0.467 |   -0.1   |    0.897 |      0.612 |    0.51 |                  44 |        125 |
| chess_top3median                           | all     |          43 |         0.614 |    0.451 |    0.75  |      0.798 |    0.12 |                  65 |        125 |
| chess_top3median                           | 10      |          10 |         0.422 |   -0.2   |    0.85  |      0.6   |    0.34 |                  52 |        125 |
| chess_top4mean                             | all     |          43 |         0.645 |    0.5   |    0.768 |      0.821 |    0.36 |                  50 |        125 |
| chess_top4mean                             | 10      |          10 |         0.467 |   -0.1   |    0.897 |      0.612 |    0.51 |                  44 |        125 |
| chess_top4median                           | all     |          43 |         0.619 |    0.467 |    0.753 |      0.798 |    0.16 |                  64 |        125 |
| chess_top4median                           | 10      |          10 |         0.467 |   -0.1   |    0.897 |      0.612 |    0.52 |                  43 |        125 |
| chess_mean                                 | all     |          43 |         0.648 |    0.5   |    0.772 |      0.825 |    0.38 |                  49 |        125 |
| chess_mean                                 | 10      |          10 |         0.467 |   -0.1   |    0.897 |      0.612 |    0.52 |                  43 |        125 |
| chess_median                               | all     |          43 |         0.63  |    0.466 |    0.761 |      0.793 |    0.24 |                  59 |        125 |
| chess_median                               | 10      |          10 |         0.422 |   -0.151 |    0.851 |      0.576 |    0.35 |                  51 |        125 |
| game_arena (20-game median, main analysis) | all     |          43 |         0.748 |    0.641 |    0.835 |      0.907 |    1.16 |                     |            |
| game_arena (20-game median, main analysis) | 10      |          10 |         0.689 |    0.35  |    0.954 |      0.842 |    1.33 |                     |            |


Agreement of top2mean ranking with max: tau = 0.861; with mean: tau = 0.867.

## Largest rank shifts (positive = mean ranks the model lower than max does)

| model_raw                  |    max |   mean |   std |   rank_max |   rank_mean |   rank_shift(mean-max) |
|:---------------------------|-------:|-------:|------:|-----------:|------------:|-----------------------:|
| kat_coder_pro              | 1627.6 | 1413.9 | 394.5 |         42 |          24 |                    -18 |
| gpt_5.4_instant            | 2038.1 | 1182.7 | 656.7 |         19 |          36 |                     17 |
| minimax_m2.1               | 1874   |  948.8 | 517.2 |         28 |          44 |                     16 |
| deepseek_v4_pro            | 2040   | 1272.5 | 587.1 |         18 |          31 |                     13 |
| gpt_oss_120b               | 1807.5 |  940.2 | 484.9 |         35 |          45 |                     10 |
| deepseek_r1t2_chimera_free | 1845.7 | 1443.3 | 467.9 |         32 |          23 |                     -9 |
| gpt_5.4_high               | 2513.1 | 1906.7 | 426.5 |          5 |          14 |                      9 |
| qwen3_32b                  | 1770.5 |  927.3 | 471.4 |         37 |          46 |                      9 |
| gpt_5.4_nano               | 1869   | 1480   | 526.7 |         30 |          22 |                     -8 |
| gpt_5_mini                 | 1880.6 | 1634.7 | 206.3 |         27 |          20 |                     -7 |


Files: `summary.csv`, `model_scores.csv` (per-model max/mean/median/min/std and ranks), `rank_shift.csv`, `tmp/out_*` (full alignment outputs per variant).
Regenerate: `cd analysis/benchmark_cost_alignment && ../../env3.12/bin/python full_chess_max_vs_mean/compare.py`
