{

# TO DEBUG: -m debugpy --listen 5678 --wait-for-client

# EXIT IF ERROR OCCURS
set -e

############ PIPELINE (1-json_dataset, 2-ASK LLM, 3-plot)
RUN_DIR="results_side_experiments/results_guessing/may_4_top10_gpt_5.4_nano"
MODEL="openai/gpt-5.4-nano"
# RUN_DIR="results_side_experiments/results_guessing/may_4_top10_kimi_k2.5"
# MODEL="moonshotai/kimi-k2.5"
SUB_RUN="20games"

# #### MAKE BOT LIST FROM PKL
# python -m guessing.build_dataset top_bots_from_pkl --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --out-json $RUN_DIR/top_bots.json


    # --game_worlds "othello/world1,connect4/world1,mancala/world1" \
# ### MAKE DATASET FROM BOT LIST
# python -m guessing.build_dataset build_dataset \
#     --game_worlds "tic_tac_toe_3d/world1,tic_tac_toe/world1,tic_tac_toe/world2,battleships/world1,connect4/world1,mancala/world1,othello/world1,lines_of_action/world1,pentago/world1,clobber/world1,amazons/world1,backgammon/world1,nim/world1,dots_and_boxes/world1,chess/worlduci1,go/world1,checkers/world1,havannah/world1,hex/world1,breakthrough/world1" \
#     --top-k 10 \
#     --in-json $RUN_DIR/top_bots.json \
#     --out-json "$RUN_DIR/guessing_${SUB_RUN}.json"

# #### ASK LLM
# python -m guessing.start_predict \
#     --in-json "$RUN_DIR/guessing_${SUB_RUN}.json" \
#     --model $MODEL \
#     --out-dir "$RUN_DIR/$SUB_RUN"

##### COMPARE PREDICTIONS
python -m guessing.compare_predictions \
    --pred-dir $RUN_DIR/$SUB_RUN \
    --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl \
    --out-dir $RUN_DIR/${SUB_RUN}_compare
# python -m guessing.compare_predictions --pred-dir $RUN_DIR/chess --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --out-dir $RUN_DIR/chess_compare
# python -m guessing.compare_predictions --pred-dir $RUN_DIR/checkers --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --out-dir $RUN_DIR/checkers_compare
# python -m guessing.compare_predictions --pred-dir $RUN_DIR/go --in-pkl analysis/results_tmp/exp_results_somerset_may_1.pkl --out-dir $RUN_DIR/go_compare





# FIGURES
cp ../results_side_experiments/results_guessing/may_4_top10_kimi_k2.5/20games_compare/rank_scatter_bt_subset_predicted_vs_empirical.pdf ../figures/llm_guess_kimi_k2.5.pdf
cp ../results_side_experiments/results_guessing/may_4_top10_gpt_5.4_nano/20games_compare/rank_scatter_bt_subset_predicted_vs_empirical.pdf ../figures/llm_guess_gpt_5.4_nano.pdf






exit
}
