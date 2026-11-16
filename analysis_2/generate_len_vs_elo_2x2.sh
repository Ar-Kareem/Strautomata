#!/usr/bin/env bash
set -euo pipefail

# # python analysis_2/viz_len_vs_elo.py --game ALL --world ignore --remove-comments --extension pdf --elos-csv analysis_2/elos_all_bots.csv

# # chess
# python analysis_2/viz_len_vs_elo.py --game chess --world worlduci1 --remove-comments --extension pdf --elos-csv analysis_2/elos_all_bots.csv
# mv analysis_2/code_length_vs_elo_chess_worlduci1.pdf "figures/code_len_chess.pdf"
# rm analysis_2/code_length_vs_elo_chess_worlduci1.pkl

# # 2x2 and 1x2
# python analysis_2/viz_len_vs_elo.py --game battleships --world world1 --remove-comments --elos-csv analysis_2/elos_all_bots.csv
# python analysis_2/viz_len_vs_elo.py --game go --world world1 --remove-comments --elos-csv analysis_2/elos_all_bots.csv
# python analysis_2/viz_len_vs_elo.py --game backgammon --world world1 --remove-comments --elos-csv analysis_2/elos_all_bots.csv
# python analysis_2/viz_len_vs_elo.py --game breakthrough --world world1 --remove-comments --elos-csv analysis_2/elos_all_bots.csv
# python analysis_2/viz_len_vs_elo.py --game nim --world world1 --remove-comments --ignore-corr --elos-csv analysis_2/elos_all_bots.csv
# python analysis_2/viz_len_vs_elo.py --game tic_tac_toe --world world1 --remove-comments --ignore-corr --elos-csv analysis_2/elos_all_bots.csv

# collect_dir="analysis_2/collect_2x2"
# collect_dir2="analysis_2/collect_1x2"
# mkdir -p "${collect_dir}"
# mkdir -p "${collect_dir2}"

# mv analysis_2/code_length_vs_elo_battleships_world1.png "${collect_dir}/battleships.png"
# mv analysis_2/code_length_vs_elo_battleships_world1.pkl "${collect_dir}/battleships.pkl"
# mv analysis_2/code_length_vs_elo_go_world1.png "${collect_dir}/go.png"
# mv analysis_2/code_length_vs_elo_go_world1.pkl "${collect_dir}/go.pkl"
# mv analysis_2/code_length_vs_elo_backgammon_world1.png "${collect_dir}/backgammon.png"
# mv analysis_2/code_length_vs_elo_backgammon_world1.pkl "${collect_dir}/backgammon.pkl"
# mv analysis_2/code_length_vs_elo_breakthrough_world1.png "${collect_dir}/breakthrough.png"
# mv analysis_2/code_length_vs_elo_breakthrough_world1.pkl "${collect_dir}/breakthrough.pkl"

# mv analysis_2/code_length_vs_elo_nim_world1.png "${collect_dir2}/nim.png"
# mv analysis_2/code_length_vs_elo_nim_world1.pkl "${collect_dir2}/nim.pkl"
# mv analysis_2/code_length_vs_elo_tic_tac_toe_world1.png "${collect_dir2}/tic_tac_toe.png"
# mv analysis_2/code_length_vs_elo_tic_tac_toe_world1.pkl "${collect_dir2}/tic_tac_toe.pkl"

# python analysis_2/collect_png_grid.py --in-dir "${collect_dir}" --out figures/code_len_combined_2x2.pdf --cols 2 --glob "*.pkl"
# python analysis_2/collect_png_grid.py --in-dir "${collect_dir2}" --out figures/code_len_combined_1x2.pdf --cols 2 --glob "*.pkl"

# rm -rf "${collect_dir}"
# rm -rf "${collect_dir2}"


# TO RUN ALL: python analysis_2/viz_len_vs_elo.py --game ALL --world ignore --remove-comments --out-dir analysis_2/all
# TO RUN ALL THINKING: python analysis_2/viz_len_vs_elo.py --game ALL --world ignore --remove-comments --out-dir analysis_2/all_thinking --x-axis thinking


# COST VS ELO
python analysis_2/viz_cost_vs_elo.py --elos-csv analysis_2/elos_all_bots.csv --ranking-csv analysis_2/ranking_all_bots.csv
cp analysis_2/cost/elos_all_bots_cost_vs_elo_only_real.pdf figures/cost_vs_elo.pdf
cp analysis_2/cost/elos_all_bots_cost_vs_elo_chess_uci_only.pdf figures/cost_vs_elo_chess_uci.pdf
