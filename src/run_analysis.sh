{

# TO DEBUG: -m debugpy --listen 5678 --wait-for-client

# EXIT IF ERROR OCCURS
set -e
# assert that ../analysis exists
[ -d ../analysis ] || { echo "ERROR: ../analysis does not exist"; exit 1; }


# ---------------------- GENERATE PKL ----------------------
# rm -rf ../analysis/results_tmp
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_akimiski_feb_19/tourney --out-pkl analysis/results_tmp/exp_results_akimiski_feb_19.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_akimiski_feb_20/tourney --out-pkl analysis/results_tmp/exp_results_akimiski_feb_20.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_feb_20/tourney --out-pkl analysis/results_tmp/exp_results_somerset_feb_20.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_feb_21/tourney --out-pkl analysis/results_tmp/exp_results_somerset_feb_21.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_feb_20_updated/tourney --out-pkl analysis/results_tmp/exp_results_somerset_feb_20_updated.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_feb_20_updated/tourney --out-pkl analysis/results_tmp/exp_results_somerset_feb_20_updated.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_may_1/tourney --out-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_may_1_thinking/tourney --out-pkl analysis/results_tmp/exp_results_somerset_may_1_thinking.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_may_5/tourney --out-pkl analysis/results_tmp/exp_results_somerset_may_5.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_sept_5/tourney --out-pkl analysis/results_tmp/exp_results_somerset_sept_5.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_somerset_sept_5/tourney --model-repr top2mean --out-pkl analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_side_experiments/full_nsquared_may_4_neurips/tourney --out-pkl analysis/results_tmp/exp_results_full_nsquared.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/stanford/tourney --out-pkl analysis/results_tmp/exp_results_stanford.pkl --game-names albuquerque alquerque battleofnumbers breakthrough cbnk chinook connectfour crusade donttouch hex7x7 knights knightthrough knightthroughsmall kono leafymcfallface lines majorities minorities multipleknightthrough multiplesuicide multipletictactoe nineboardtictactoe parallelbuttonsandlights parallelhunter parallelknightthrough parallelkono pentago pentagosuicide reversum skirmish suicide tictactoe3 tictactoe5 tictactoe7 tictactoe trifecta ttcc4
# python -m experimental.exp_plotting gen_pkl --results-dir results_temp --out-pkl analysis/results_tmp/temp.pkl


# DEBUG CODE
# python -m experimental.exp_plotting gen_pkl --results-dir results_old/results_feb_15 --games go chess checkers connect4 --out-pkl analysis/results_tmp/exp_results_tmp.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_old/results_feb_15 --out-pkl analysis/results_tmp/exp_results.pkl


# ENGINE
# python -m experimental.exp_plotting gen_pkl --results-dir results_side_experiments/results_heuristic/a --out-pkl analysis/results_tmp/exp_results_heuristic_chess.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_side_experiments/results_heuristic/b/ --out-pkl analysis/results_tmp/exp_results_heuristic_checkers.pkl

# LIMITED AUTOMATA EXPERIMENTS
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_1/tourney --out-pkl analysis/results_tmp/exp_results_rep_1.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_2/tourney --out-pkl analysis/results_tmp/exp_results_rep_2.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_3/tourney --out-pkl analysis/results_tmp/exp_results_rep_3.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_4/tourney --out-pkl analysis/results_tmp/exp_results_rep_4.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_6/tourney --out-pkl analysis/results_tmp/exp_results_rep_6.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_A3_A4/tourney --out-pkl analysis/results_tmp/exp_results_rep_A3_A4.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_A4_A5/tourney --out-pkl analysis/results_tmp/exp_results_rep_A4_A5.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_A5/tourney --out-pkl analysis/results_tmp/exp_results_rep_A5.pkl
# python -m experimental.exp_plotting gen_pkl --results-dir results_current/results_rep_A6/tourney --out-pkl analysis/results_tmp/exp_results_rep_A6.pkl


# ---------------------- PLOT PKL ----------------------

# # main plots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_feb_20/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_feb_20/models

# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_akimiski_feb_19.pkl --mode models --out-dir analysis/results_tmp/plots_akimiski_feb_19/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_akimiski_feb_19.pkl --mode bots --out-dir analysis/results_tmp/plots_akimiski_feb_19/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_akimiski_feb_20.pkl --mode models --out-dir analysis/results_tmp/plots_akimiski_feb_20/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_akimiski_feb_20.pkl --mode bots --out-dir analysis/results_tmp/plots_akimiski_feb_20/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_21.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_feb_21/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_21.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_feb_21/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_feb_20/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_feb_20/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20_updated.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_feb_20_updated/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_feb_20_updated.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_feb_20_updated/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_may_1/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_may_1/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_1_thinking.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_may_1_thinking/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_1_thinking.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_may_1_thinking/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_5.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_may_5/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_5.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_may_5/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_sept_5.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_sept_5/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_sept_5.pkl --mode bots --out-dir analysis/results_tmp/plots_somerset_sept_5/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_sept_5_top2/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_5.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_may_5/models_sample \
#     --ignore gpt_5.5_high gpt_5.5_medium gpt_5.5_low gpt_5.5_instant gpt_5.4_medium gpt_5.4_low gpt_5.4_instant gpt_5.2 devstral_2512 nemotron_nano_12b_v2_vl_free trinity_mini_free qwen3_coder_30b_a3b_instruct gpt_4o_mini solar_pro_3_free ministral_14b_2512
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_sept_5.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_sept_5/models_sample \
#     --ignore gpt_5.5_high gpt_5.5_medium gpt_5.5_low gpt_5.5_instant gpt_5.4_medium gpt_5.4_low gpt_5.4_instant gpt_5.2 devstral_2512 nemotron_nano_12b_v2_vl_free trinity_mini_free qwen3_coder_30b_a3b_instruct gpt_4o_mini solar_pro_3_free ministral_14b_2512

# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_full_nsquared.pkl --mode bots --out-dir analysis/results_tmp/plots_full_nsquared/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_stanford.pkl --mode bots --out-dir analysis/results_tmp/plots_stanford/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_stanford.pkl --mode models --out-dir analysis/results_tmp/plots_stanford/models

# # For frontend
# cp ../analysis/results_tmp/plots_somerset_may_5/models/rating_df.csv frontend/arena_fe/public/elos_combined_bots.csv
# cp ../analysis/results_tmp/plots_somerset_may_5/bots/rating_df.csv frontend/arena_fe/public/elos_all_bots.csv
# cp ../analysis/results_tmp/plots_somerset_may_5/models/rankings_df.csv frontend/arena_fe/public/ranking_combined_bots.csv
# cp ../analysis/results_tmp/plots_somerset_may_5/bots/rankings_df.csv frontend/arena_fe/public/ranking_all_bots.csv
# cp ../analysis/results_tmp/plots_somerset_may_5/bots/rating_df.csv ../analysis_2/elos_all_bots.csv
# cp ../analysis/results_tmp/plots_somerset_may_5/bots/rankings_df.csv ../analysis_2/ranking_all_bots.csv


# Plot thinking levels
# python -m experimental.exp_plotting thinking_plot --in-pkl analysis/results_tmp/exp_results_somerset_may_5.pkl --out-dir analysis/results_tmp/plots_somerset_may_5/models_thinking
# cp ../analysis/results_tmp/plots_somerset_may_5/models_thinking/thinking_plot.pdf ../figures/thinking_plot.pdf


# quals consistency
# python -m experimental.exp_plotting quals-plot --in-pkl analysis/results_tmp/exp_results.pkl --quals-dir results_quals --out-dir analysis/results_tmp/plots_quals --hide-yellow

# Compare different runs      (plots_compare_pkl_pkl)
OUT_DIR="../analysis/results_tmp"
# #    FULL vs #
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_rep_1.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "1 Automata #1" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_1.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_rep_2.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "2 Automata #1,#2" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_2.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_rep_3.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "3 Automata #1,#2,#3" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_3.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_rep_4.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "4 Automata #1,#2,#3,#4" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_4.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_rep_6.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "6 Automata #1,#2,#3,#4,#5,#6" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_6.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_rep_3.pkl --pkl-b ${OUT_DIR}/exp_results_rep_A4_A5.pkl --x-axis "3 Automata #1,#2,#3" --y-axis "2 Automata #4,#5" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_A123_A45.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_rep_A4_A5.pkl --pkl-b ${OUT_DIR}/exp_results_rep_A6.pkl --x-axis "2 Automata #4,#5" --y-axis "1 Automata #6" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_A45_A6.png
# #   FULL vs FULL different dates
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_akimiski_feb_19.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 19)" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_a20_a19.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_somerset_feb_20.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "5 Automata #1,#2,#3,#4,#5 (somerset feb 20)" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_a20_s20.png
# python -m experimental.exp_plot_pkl_pkl --pkl-a ${OUT_DIR}/exp_results_akimiski_feb_20.pkl --pkl-b ${OUT_DIR}/exp_results_somerset_feb_21.pkl --x-axis "5 Automata #1,#2,#3,#4,#5 (akimiski feb 20)" --y-axis "5 Automata #1,#2,#3,#4,#5 (somerset feb 21)" --mode models --out-dir ${OUT_DIR}/plots_compare_pkl_pkl
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_compare_scatter.png ${OUT_DIR}/plots_compare_pkl_pkl/compare_scatter_vs_a20_s21.png

# python -m experimental.exp_plot_pkl_pkl --mode corr-heatmap --corr-granularity models --corr-method spearman --corr-metric mean_rank --out-dir ${OUT_DIR}/plots_compare_pkl_pkl \
#     --pkls ${OUT_DIR}/exp_results_rep_A6.pkl ${OUT_DIR}/exp_results_rep_A4_A5.pkl ${OUT_DIR}/exp_results_rep_3.pkl ${OUT_DIR}/exp_results_rep_4.pkl ${OUT_DIR}/exp_results_somerset_feb_21.pkl ${OUT_DIR}/exp_results_rep_6.pkl \
#     --names "1 bot (#6)" "2 bots (#4 #5)" "3 bots (#1 #2 #3)" "4 bots (#1 #2 #3 #4)" "5 bots (#1 #2 #3 #4 #5)" "6 bots (#1 #2 #3 #4 #5 #6)"
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_corr_heatmap.pdf ../figures/corr_heatmap_all_iters.pdf
# python -m experimental.exp_plot_pkl_pkl --mode corr-heatmap --corr-granularity models --corr-method spearman --corr-metric median_elo --out-dir ${OUT_DIR}/plots_compare_pkl_pkl \
#     --pkls ${OUT_DIR}/exp_results_rep_1.pkl ${OUT_DIR}/exp_results_rep_2.pkl ${OUT_DIR}/exp_results_rep_3.pkl ${OUT_DIR}/exp_results_rep_4.pkl ${OUT_DIR}/exp_results_somerset_feb_21.pkl ${OUT_DIR}/exp_results_rep_6.pkl \
#     --names "1 automata (#1)" "2 automata (#2 #3)" "3 automata (#1 #2 #3)" "4 automata (#1 #2 #3 #4)" "5 automata (#1 #2 #3 #4 #5)" "6 automata (#1 #2 #3 #4 #5 #6)"
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_corr_heatmap.pdf ../figures/corr_heatmap_all_iters_2.pdf
# python -m experimental.exp_plot_pkl_pkl --mode corr-heatmap --corr-granularity models --corr-method spearman --corr-metric mean_rank --out-dir ${OUT_DIR}/plots_compare_pkl_pkl \
#     --pkls ${OUT_DIR}/exp_results_akimiski_feb_20.pkl ${OUT_DIR}/exp_results_akimiski_feb_19.pkl ${OUT_DIR}/exp_results_somerset_feb_20.pkl ${OUT_DIR}/exp_results_somerset_feb_21.pkl \
#     --names "R1 (5 automata)" "R2 (5 automata)" "R3 (5 automata)" "R4 (5 automata)"
# cp ${OUT_DIR}/plots_compare_pkl_pkl/pkl_corr_heatmap.pdf ../figures/corr_heatmap_duplicate.pdf
    # --corr-metric median_elo \



# DEBUG CODE (focusing on specific models)
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_tmp.pkl --mode bots --out-dir analysis/results_tmp/plots_bots_tmp --focus-on gemini_3_flash tng
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_tmp.pkl --mode models --out-dir analysis/results_tmp/plots_models_tmp --focus-on gemini_3_flash tng


# CHESS ENGINE
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_heuristic_chess.pkl --mode bots --out-dir analysis/results_tmp/plots_models_heuristic_chess
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_heuristic_checkers.pkl --mode bots --out-dir analysis/results_tmp/plots_models_heuristic_checkers

# LIMITED AUTOMATA EXPERIMENTS
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_1.pkl --mode models --out-dir analysis/results_tmp/plots_rep_1/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_1.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_1/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_2.pkl --mode models --out-dir analysis/results_tmp/plots_rep_2/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_2.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_2/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_3.pkl --mode models --out-dir analysis/results_tmp/plots_rep_3/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_3.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_3/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_4.pkl --mode models --out-dir analysis/results_tmp/plots_rep_4/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_4.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_4/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_6.pkl --mode models --out-dir analysis/results_tmp/plots_rep_6/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_6.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_6/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A3_A4.pkl --mode models --out-dir analysis/results_tmp/plots_rep_A3_A4/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A3_A4.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_A3_A4/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A4_A5.pkl --mode models --out-dir analysis/results_tmp/plots_rep_A4_A5/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A4_A5.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_A4_A5/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A5.pkl --mode models --out-dir analysis/results_tmp/plots_rep_A5/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A5.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_A5/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A6.pkl --mode models --out-dir analysis/results_tmp/plots_rep_A6/models
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_rep_A6.pkl --mode bots --out-dir analysis/results_tmp/plots_rep_A6/bots
# python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl --mode models --out-dir analysis/results_tmp/plots_somerset_sept_5_top2/models_sample_top20 --ignore gpt_5.5_high gpt_5.4_medium gpt_5.5_medium gpt_5.2 gpt_5.5_instant gpt_5.5_low gpt_5.4_low gpt_5.4_instant gpt_5.2_codex claude_sonnet_4.5 minimax_m2 minimax_m2.1 gpt_5.4_nano deepseek_r1t2_chimera_free tng_r1t_chimera_free deepseek_v3.2 grok_code_fast_1 mimo_v2_flash qwen3_235b_a22b_2507 qwen3_coder qwen3_32b deepseek_chat_v3_0324 gemini_2.0_flash_001 qwen3_next_80b_a3b_instruct devstral_2512 kat_coder_pro trinity_mini_free nemotron_nano_12b_v2_vl_free random qwen3_coder_30b_a3b_instruct gpt_4o_mini solar_pro_3_free ministral_14b_2512

# ----------------------- LM ARENA COMPARISON -----------------------
# download the lmarena html files
# curl -o experimental/lm_arena/html/overall_no_sc.html https://arena.ai/leaderboard/text/overall-no-style-control
# curl -o experimental/lm_arena/html/text_coding_no_sc.html https://arena.ai/leaderboard/text/coding-no-style-control
# curl -o experimental/lm_arena/html/text_coding.html https://arena.ai/leaderboard/text/coding
# curl -o experimental/lm_arena/html/code.html https://arena.ai/leaderboard/code/webdev
# python -m experimental.lm_arena.my_comparison lma \
#     --pkl ../analysis/results_tmp/exp_results_somerset_may_5.pkl \
#     --out-dir ../analysis/lm_arena_comparison/ \
#     --corr-type spearman
# cp ../analysis/lm_arena_comparison/lm_code_arena_vs_strautomata.pdf ../figures/
# cp ../analysis/lm_arena_comparison/lm_code_arena_vs_strautomata_rank.pdf ../figures/

# ----------------------- SWE BENCH COMPARISON -----------------------
# download the swebench html files
# curl -o experimental/lm_arena/html/swebench.html https://www.swebench.com/index.html
# python -m experimental.lm_arena.my_comparison swe \
#     --html experimental/lm_arena/html/swebench.html \
#     --pkl ../analysis/results_tmp/exp_results_somerset_may_5.pkl \
#     --out-dir ../analysis/lm_arena_comparison/ \
#     --corr-type spearman
# cp ../analysis/lm_arena_comparison/swe_bash_vs_strautomata.pdf ../figures/
# cp ../analysis/lm_arena_comparison/swe_bash_vs_strautomata_rank.pdf ../figures/


# ----------------------- AUTOMATA RANDOMNESS ASSESSMENT -----------------------
# # will take ~hours to finish if fresh directory
# python -m experimental.exp_randomness main \
#     --game ALL \
#     --n_seeds 16 \
#     --repeats 3 \
#     --timeout 1 \
#     --continue-from ../results_side_experiments/results_randomness_assessment/seeded \
#     --seed_world \
#     --limit_model_bots 6 \
#     --model_blacklist_file ./experimental/model_ignore.json \
#     --max_workers 50
# # will take ~hours
# python -m experimental.exp_randomness main \
#     --game ALL \
#     --n_seeds 16 \
#     --repeats 3 \
#     --timeout 1 \
#     --continue-from ../results_side_experiments/results_randomness_assessment/unseeded \
#     --limit_model_bots 6 \
#     --model_blacklist_file ./experimental/model_ignore.json \
#     --max_workers 50



# python -m experimental.exp_randomness latex --continue-from ../results_side_experiments/results_randomness_assessment/seeded
# python -m experimental.exp_randomness barplot --continue-from ../results_side_experiments/results_randomness_assessment/seeded --output-dir ../figures/ --pkl ../analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl
# python -m experimental.exp_randomness barplot --continue-from ../results_side_experiments/results_randomness_assessment/unseeded --output-dir ../figures/ --pkl ../analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl
# python -m experimental.exp_randomness barplot_combined --from-unseeded ../results_side_experiments/results_randomness_assessment/unseeded --from-seeded ../results_side_experiments/results_randomness_assessment/seeded --output-dir ../figures/ --pkl ../analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl
# python -m experimental.exp_randomness scatter --from-unseeded ../results_side_experiments/results_randomness_assessment/unseeded --from-seeded ../results_side_experiments/results_randomness_assessment/seeded --output-dir ../figures/ --pkl ../analysis/results_tmp/exp_results_somerset_sept_5_top2.pkl


# ----------------------- DVs CLUSTERING -----------------------z
# python -m experimental.exp_cluster_code \
#     --in-pkl ../analysis/results_tmp/exp_results_somerset_may_1.pkl \
#     --result-key 'Chess UCI' \
#     --mode bots \
#     --n-clusters 4
    # --estimate-only


# ----------------------- OPENROUTER -----------------------
# python -m experimental.exp_openrouter --in-dir ../openrouter_csv --out-csv ../openrouter_csv/openrouter_model_summary.csv \
#     --ignore-human-names "Claude Haiku 4.5" "DeepSeek TNG R1T" "GPT-5.4 Instant"


# ----------------------- QUAL TOURNEY MATCH COUNTS -----------------------
# python -m experimental.exp_count_stage_games --results-dir results_current/results_somerset_sept_5 > ../figures/match_counts.tex

exit 
}
