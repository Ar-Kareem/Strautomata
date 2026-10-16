#!/usr/bin/env bash
set -euo pipefail


games=(
  amazons
  backgammon
  breakthrough
  chess
  clobber
  connect4
  dots_and_boxes
  go
  havannah
  hex
  lines_of_action
  mancala
  nim
  othello
  pentago
  tic_tac_toe
  tic_tac_toe_3d
)



# To regenrate json files
# python scripts/strategy_analysis.py --json-path analysis/strategy_runs.json

# quick box plot
python scripts/strategy_boxplots.py \
  --runs analysis/strategy_runs.json \
  --elo-csv src/frontend/arena_fe/public/elos_all_bots.csv \
  --out analysis/visuals/strategy_metric_r2_boxplot.png \
  --median-threshold 0.18 --corr-methods spearman --scatter_plot \

  # --all-games-y raw --all-games-x raw \
  # --elo-csv ./temp/temp_rating_all_bots_lm_arena.csv \
  # --median-threshold 0.18 --corr-methods pearson pearson_rank spearman spearman_rank kendall kendall_rank --scatter_plot


# To generate visuals (all games combined)
# python scripts/strategy_visuals.py
# To generate visuals (by game)
# python scripts/strategy_visuals.py --game connect4
# for game in "${games[@]}"; do
#   echo "Running visuals for game: ${game}"
#   python scripts/strategy_visuals.py --game "${game}"
# done



# for game in "${games[@]}"; do
#   echo "Running visuals for game: ${game}"
#   python scripts/strategy_visuals.py --elo-max-code-len 50000 --game "${game}"
#   if [[ -f analysis/visuals/code_length_vs_elo.png ]]; then
#     mv analysis/visuals/code_length_vs_elo.png "analysis/visuals/all/code_length_vs_elo_game_${game}.png"
#   fi
#   # read -r -p "Press Enter to continue to next game..."
# done
