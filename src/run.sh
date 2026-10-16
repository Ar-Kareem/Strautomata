{

# EXIT IF ERROR OCCURS
set -e

# gemini_2.5_pro, glm_4.6 are too expensive
#  removed openai/gpt-5.2-pro because extremely expensive
#  removed allenai/olmo-3-32b-think:free because its not available
#  removed x-ai/grok-4.1-fast because "Content violates usage guidelines"
#  removed google/gemini-2.5-flash-lite because it keeps getting the instructions wrong
#  removed deepseek/deepseek-v3.2-speciale because it keeps getting the instructions wrong

# expensive: (old list)
# google/gemini-3-pro-preview $10
# anthropic/claude-opus-4.5 $5
# anthropic/claude-sonnet-4.5 $2
# anthropic/claude-sonnet-4 $1.6
# google/gemini-2.5-flash $1.4
# rest is <$1
# no longer free:
# xiaomi/mimo-v2-flash:free
# tngtech/deepseek-r1t2-chimera:free

# no longer exists: tngtech/tng-r1t-chimera:free

# maybe add:


# ---------------------- CREATE BOTS ----------------------

    # IGNORE
    # poker/world1,phantom_ttt/world1,phantom_ttt/world2

# ALL GAMES
ALL_GW="tic_tac_toe_3d/world1,tic_tac_toe/world1,tic_tac_toe/world2,battleships/world1,connect4/world1,mancala/world1,othello/world1,lines_of_action/world1,pentago/world1,clobber/world1,amazons/world1,backgammon/world1,nim/world1,dots_and_boxes/world1,chess/worlduci1,go/world1,checkers/world1,havannah/world1,hex/world1,breakthrough/world1"
# --game_worlds "tic_tac_toe_3d/world1,tic_tac_toe/world1,tic_tac_toe/world2,battleships/world1,connect4/world1,mancala/world1,othello/world1,lines_of_action/world1,pentago/world1,clobber/world1,amazons/world1,backgammon/world1,nim/world1,dots_and_boxes/world1,chess/worlduci1,go/world1,go/worldmem1,checkers/world1,havannah/world1,hex/world1,breakthrough/world1" \
# GAMES WITH MEMORY
# --game_worlds "go/worldmem1" \
# --game_worlds "chess/worlducimem1" \

# MODEL GROUPS:
# --models "MAX|||anthropic/claude-opus-4.6-max,anthropic/claude-opus-4.5-max,anthropic/claude-sonnet-4.5-max" \
# --models "EXPENSIVE|||openai/gpt-5.4,openai/gpt-5.2,z-ai/glm-4.7,z-ai/glm-5,anthropic/claude-opus-4.6,anthropic/claude-opus-4.5,google/gemini-3-pro-preview,anthropic/claude-sonnet-4.5,openai/gpt-5.2-codex,moonshotai/kimi-k2-thinking,moonshotai/kimi-k2.5" \
# --models "openai/gpt-5.5-high,anthropic/claude-opus-4.7-high,openai/gpt-5.5-xhigh" \
# --models "GPT_THINKING|||openai/gpt-5.4-instant,openai/gpt-5.4-low,openai/gpt-5.4-medium,openai/gpt-5.5-instant,openai/gpt-5.5-low,openai/gpt-5.5-medium" \
# --models "CLAUDE_THINKING|||anthropic/claude-opus-4.5-max,anthropic/claude-sonnet-4.5-max" \
# --models "PAID|||minimax/minimax-m2.1,x-ai/grok-code-fast-1,deepseek/deepseek-v3.2,google/gemini-3-flash-preview,minimax/minimax-m2,google/gemini-2.0-flash-001,deepseek/deepseek-chat-v3-0324,openai/gpt-5-mini,qwen/qwen3-coder-30b-a3b-instruct,qwen/qwen3-32b,qwen/qwen3-235b-a22b-2507,qwen/qwen3-coder,kwaipilot/kat-coder-pro,openai/gpt-oss-120b,openai/gpt-4o-mini,qwen/qwen3-next-80b-a3b-instruct" \
# --models "FREE|||mistralai/ministral-14b-2512,arcee-ai/trinity-mini:free,nvidia/nemotron-nano-12b-v2-vl:free,upstage/solar-pro-3:free" \
# --models "FREE_THEN_NO|||xiaomi/mimo-v2-flash,mistralai/devstral-2512,tngtech/deepseek-r1t2-chimera:free" \
# --models "SEPT_2|||deepseek/deepseek-v4-pro,meta/muse-spark-1.3,google/gemini-3.8-flash,z-ai/glm-5.3" \

# --models "CLAUDE_THINKING|||anthropic/claude-opus-4.5-max,anthropic/claude-sonnet-4.5-max" \

# python -m game_arena.prompter --n_bots 5 \
#     --game_worlds "$ALL_GW" \
#     --models "moonshotai/kimi-k3" \
#     --filter_already_done \
#     --max_workers 16


# BATCHED PROMPTING
# python -m game_arena.prompter_batch place --n_bots 5 --game_worlds "$ALL_GW" --models "anthropic/claude-fable-5.1-high,openai/gpt-5.6-sol-high,openai/gpt-6-astra-high"
# python -m game_arena.prompter_batch status
# python -m game_arena.prompter_batch collect


# all games / all models
    # --models "openai/gpt-5.5-high,anthropic/claude-opus-4.7-high" \
    # --models "EXPENSIVE|||openai/gpt-5.2,z-ai/glm-4.7,z-ai/glm-5,anthropic/claude-opus-4.6,anthropic/claude-opus-4.5,google/gemini-3-pro-preview,anthropic/claude-sonnet-4.5,openai/gpt-5.2-codex,moonshotai/kimi-k2-thinking,moonshotai/kimi-k2.5" \
    # --models "PAID|||minimax/minimax-m2.1,x-ai/grok-code-fast-1,deepseek/deepseek-v3.2,google/gemini-3-flash-preview,minimax/minimax-m2,google/gemini-2.0-flash-001,deepseek/deepseek-chat-v3-0324,openai/gpt-5-mini,qwen/qwen3-coder-30b-a3b-instruct,qwen/qwen3-32b,qwen/qwen3-235b-a22b-2507,qwen/qwen3-coder,kwaipilot/kat-coder-pro,openai/gpt-oss-120b,openai/gpt-4o-mini,qwen/qwen3-next-80b-a3b-instruct" \
    # --models "FREE|||mistralai/ministral-14b-2512,arcee-ai/trinity-mini:free,nvidia/nemotron-nano-12b-v2-vl:free,upstage/solar-pro-3:free" \
    # --models "FREE_THEN_NO|||xiaomi/mimo-v2-flash,mistralai/devstral-2512,tngtech/deepseek-r1t2-chimera:free" \
# while true; do
#   if python -m game_arena.prompter --n_bots 5 \
#     --game_worlds "tic_tac_toe_3d/world1,tic_tac_toe/world1,tic_tac_toe/world2,battleships/world1,connect4/world1,mancala/world1,othello/world1,lines_of_action/world1,pentago/world1,clobber/world1,amazons/world1,backgammon/world1,nim/world1,dots_and_boxes/world1,chess/worlduci1,go/world1,checkers/world1,havannah/world1,hex/world1,breakthrough/world1" \
#     --models "deepseek/deepseek-v4-pro,meta/muse-spark-1.3,google/gemini-3.8-flash" \
#     --filter_already_done \
#     --max_workers 24
#   then
#     echo "All prompting successful. Exiting."
#     break
#   else
#     status=$?
#     echo "Some prompting failed (exit $status). Retrying in 5s..."
#     sleep 5
#   fi
# done


# ---------------------- PLAY GAMES ----------------------
RUN_DIR="results_current/results_somerset_sept_5"
# RUN_DIR="results_side_experiments/full_nsquared_may_4_neurips"
# QUALS
QUALS_COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --conf 0.95 --match_limit_L 100 --allowed_bot_nums 1,2,3,4,5 --top_k_model_bots 2 --model_blacklist_file experimental/model_ignore.json --save_results_dir ${RUN_DIR}/quals"
# TEMP_ARGS='--n_games 4 --model_whitelist gpt_5.5_xhigh gpt_5.5_high gpt_5.5_medium gpt_5.5_instant gpt_5.5_low gpt_5.2 random --save_results_dir results_temp'
# QUALS_COMMON_ARGS="$QUALS_COMMON_ARGS $TEMP_ARGS"
PYTHONHASHSEED=0 python -m game_arena.run_quals --game mancala --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game othello --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game lines_of_action --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game pentago --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game clobber --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game amazons --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game nim --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game dots_and_boxes --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game chess --world "worlduci1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game go --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game havannah --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game hex --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game breakthrough --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game battleships --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game connect4 --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game tic_tac_toe --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game tic_tac_toe --world "world2" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game checkers --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game tic_tac_toe_3d --world "world1" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game backgammon --world "world1" $QUALS_COMMON_ARGS


# MAIN TOURNAMENT
COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --quals_dir ${RUN_DIR}/quals --save_results_dir ${RUN_DIR}/tourney --top_k_model_bots 2 --model_blacklist_file experimental/model_ignore.json"
# COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --save_results_dir results_temp --top_k_model_bots 2 --model_blacklist_file experimental/model_ignore.json"
# FULL N-SQUARED
# COMMON_ARGS="--n_games 1 --timeout 1 --seed 0 --max_workers 50 --quals_dir ${RUN_DIR}/quals --save_results_dir ${RUN_DIR}/tourney --top_k_model_bots 5 --model_blacklist_file experimental/model_ignore.json"
# TEMP_ARGS='--n_games 4 --model_whitelist gpt_5.5_xhigh gpt_5.5_high random --save_results_dir results_temp'
# NO QUALS
# COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --model_blacklist_file experimental/model_ignore.json"

# TEMP_ARGS='--n_games 4 --allowed_bot_nums 1,2 --model_whitelist claude_fable_5.1_high gpt_6_astra_high gpt_5.6_sol_high kimi_k3 deepseek_v4_pro muse_spark_1.3 gemini_3.8_flash gpt_5.5_high random --save_results_dir smoke_sep_9'
# COMMON_ARGS="$COMMON_ARGS $TEMP_ARGS"
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game mancala --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game othello --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game lines_of_action --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game pentago --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game clobber --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game amazons --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game nim --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game dots_and_boxes --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game chess --world "worlduci1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game go --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game havannah --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game hex --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game breakthrough --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game battleships --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game connect4 --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game tic_tac_toe --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game tic_tac_toe --world "world2" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game checkers --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game tic_tac_toe_3d --world "world1" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game backgammon --world "world1" $COMMON_ARGS


# dead games
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game poker --world "world1" --n_games 50 --timeout 10 --max_workers 32 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game phantom_ttt --world "world1" --n_games 5 --timeout 20 --max_workers 32 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game phantom_ttt --world "world2" --n_games 20 --timeout 20 --max_workers 32 --pre_elimination_games 0
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game blackjack --world "world1" $COMMON_ARGS

# with memory
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game go --world "worldmem1" $COMMON_ARGS --timeout 60
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game chess --world "worldmem1" --n_games 1 --timeout 20 --max_workers 32 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game chess --world "worlducimem1" --n_games 5 --timeout 20 --max_workers 32 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2

# REPETITION EXPERIMENTS
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game checkers --world "world1" --n_games 10 --timeout 10 --max_workers 128 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2 --save_results_dir "results_variance_checkers"
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game dots_and_boxes --world "world1" --n_games 10 --timeout 10 --max_workers 128 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2 --save_results_dir "results_variance_checkers"
# PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game pentago --world "world1" --n_games 10 --timeout 10 --max_workers 128 --pre_elimination_games 0 --allowed_bot_nums 0,1,2,3,4 --top_k_model_bots 2 --save_results_dir "results_variance_checkers"


# PROMPTS
# python -m game_arena.amazons.game
# python -m game_arena.backgammon.game
# python -m game_arena.battleships.game
# python -m game_arena.blackjack.game
# python -m game_arena.breakthrough.game
# python -m game_arena.checkers.game
# python -m game_arena.chess.game
# python -m game_arena.clobber.game
# python -m game_arena.connect4.game
# python -m game_arena.dots_and_boxes.game
# python -m game_arena.go.game
# python -m game_arena.havannah.game
# python -m game_arena.hex.game
# python -m game_arena.lines_of_action.game
# python -m game_arena.mancala.game
# python -m game_arena.othello.game
# python -m game_arena.nim.game
# python -m game_arena.pentago.game
# python -m game_arena.tic_tac_toe.tic_tac_toe
# python -m game_arena.tic_tac_toe_3d.game
# python -m game_arena.phantom_ttt.game
# python -m game_arena.poker.game


# ---------------------- LIVE PLAY ---------------------
# python -m game_arena.live_play --game_worlds "dots_and_boxes/world1" --model google/gemini-3-flash-preview --vs_model_parent ALL --num_games 1
# python -m game_arena.live_play --game_worlds "hex/world1" --model google/gemini-3-flash-preview --vs_model_parent ALL --num_games 1
# python -m game_arena.live_play --game_worlds "clobber/world1" --model google/gemini-3-flash-preview --vs_model_parent ALL --num_games 1
# python -m game_arena.live_play --game_worlds "connect4/world1" --model google/gemini-3-flash-preview --vs_model_parent ALL --num_games 1
# python -m game_arena.live_play --game_worlds "breakthrough/world1" --model google/gemini-3-flash-preview --vs_model_parent ALL --num_games 1

# python -m game_arena.live_play --game_worlds "hex/world1" --model mistralai/ministral-14b-2512 --vs_model_parent ALL --num_games 3
# python -m game_arena.live_play --game_worlds "hex/world1" --model arcee-ai/trinity-mini:free --vs_model_parent ALL --num_games 3
# python -m game_arena.live_play --game_worlds "hex/world1" --model mistralai/devstral-2512:free --vs_model_parent ALL --num_games 3  # WARNING NO LONGER FREE!!!
# python -m game_arena.live_play --game_worlds "hex/world1" --model nvidia/nemotron-nano-12b-v2-vl:free --vs_model_parent ALL --num_games 3


# Live competitors: gemini_3_pro_preview,gpt_5.2,deepseek_v3.2,gpt_5.2_codex,claude_opus_4.5,claude_sonnet_4.5,minimax_m2.1,gemini_3_flash_preview,qwen3_235b_a22b_2507,kat_coder_pro,gpt_5_mini,qwen3_coder,grok_code_fast_1,gpt_4o_mini,gpt_oss_120b
# python -m game_arena.live_play --game_worlds "clobber/world1" --model mistralai/ministral-14b-2512 --vs_model_parent ALL --num_games 1 --show_legal_moves --history_len 5
# python -m game_arena.live_play --game_worlds "clobber/world1" --model openai/gpt-5-mini --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "gemini_3_pro_preview,gpt_5.2,deepseek_v3.2,gpt_5.2_codex,claude_opus_4.5,claude_sonnet_4.5,minimax_m2.1,gemini_3_flash_preview,qwen3_235b_a22b_2507,kat_coder_pro,gpt_5_mini,qwen3_coder,grok_code_fast_1,gpt_4o_mini,gpt_oss_120b"
# python -m game_arena.live_play --game_worlds "chess/worlduci1" --model mistralai/ministral-14b-2512 --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "gemini_3_pro_preview,gpt_5.2,deepseek_v3.2,gpt_5.2_codex,claude_opus_4.5,claude_sonnet_4.5,minimax_m2.1,gemini_3_flash_preview,qwen3_235b_a22b_2507,kat_coder_pro,gpt_5_mini,qwen3_coder,grok_code_fast_1,gpt_4o_mini,gpt_oss_120b"

# python -m game_arena.live_play --game_worlds "chess/worlduci1,breakthrough/world1,clobber/world1,connect4/world1,dots_and_boxes/world1,hex/world1" --model mistralai/devstral-2512:free --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "gpt_oss_120b"  # WARNING NO LONGER FREE!!!
# python -m game_arena.live_play --game_worlds "chess/worlduci1,breakthrough/world1,clobber/world1,connect4/world1,dots_and_boxes/world1,hex/world1" --model mistralai/devstral-2512:free --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "gpt_oss_120b"  # WARNING NO LONGER FREE!!!
# python -m game_arena.live_play --game_worlds "chess/worlduci1,breakthrough/world1,clobber/world1,connect4/world1,dots_and_boxes/world1,hex/world1" --model mistralai/devstral-2512:free --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "gpt_oss_120b"  # WARNING NO LONGER FREE!!!
# python -m game_arena.live_play --game_worlds "chess/worlduci1,breakthrough/world1,clobber/world1,connect4/world1,dots_and_boxes/world1,hex/world1" --model mistralai/devstral-2512:free --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "deepseek_v3.2,gpt_5.2_codex,claude_opus_4.5,minimax_m2.1,gemini_3_flash_preview,qwen3_235b_a22b_2507,kat_coder_pro,gpt_5_mini,qwen3_coder,grok_code_fast_1,gpt_4o_mini,gpt_oss_120b"

# python -m game_arena.live_play --game_worlds "chess/worlduci1" --model openai/gpt-5-mini --num_games 1 --show_legal_moves --history_len 2 --vs_model_parent "deepseek_v3.2,gpt_5.2_codex,claude_opus_4.5,minimax_m2.1,gemini_3_flash_preview,qwen3_235b_a22b_2507,kat_coder_pro,gpt_5_mini,qwen3_coder,grok_code_fast_1,gpt_4o_mini,gpt_oss_120b"

# live play double for loop
    #   --game_worlds "chess/worlduci1" \
    #   --game_worlds "connect4/world1" \
    #   --game_worlds "dots_and_boxes/world1" \


# MODELS=("google/gemini-3-flash-preview")
# MODELS=("moonshotai/kimi-k2-thinking")
# MODELS=("mistralai/ministral-14b-2512" "arcee-ai/trinity-mini:free" "nvidia/nemotron-nano-12b-v2-vl:free")
# MODELS=("moonshotai/kimi-k2-thinking")
# MODELS=("google/gemini-3-flash-preview")
# CONNECT4
# MODELS=("x-ai/grok-code-fast-1" "deepseek/deepseek-v3.2" "google/gemini-3-flash-preview" "minimax/minimax-m2" "google/gemini-2.0-flash-001" "deepseek/deepseek-chat-v3-0324" "openai/gpt-5-mini" "qwen/qwen3-coder-30b-a3b-instruct" "qwen/qwen3-32b" "qwen/qwen3-235b-a22b-2507" "qwen/qwen3-coder" "kwaipilot/kat-coder-pro" "openai/gpt-oss-120b" "openai/gpt-4o-mini" "qwen/qwen3-next-80b-a3b-instruct")
# MODELS=("google/gemini-2.0-flash-001" "deepseek/deepseek-chat-v3-0324" "openai/gpt-5-mini" "qwen/qwen3-coder-30b-a3b-instruct" "qwen/qwen3-32b" "qwen/qwen3-235b-a22b-2507" "qwen/qwen3-coder" "kwaipilot/kat-coder-pro" "openai/gpt-oss-120b" "openai/gpt-4o-mini" "qwen/qwen3-next-80b-a3b-instruct")

# VS_MODELS=("deepseek_v3.2" "gpt_5.2_codex" "claude_opus_4.5" "minimax_m2.1" "gemini_3_flash_preview" "qwen3_235b_a22b_2507" "kat_coder_pro" "gpt_5_mini" "qwen3_coder" "grok_code_fast_1" "gpt_4o_mini" "gpt_oss_120b" "kimi_k2_thinking")
# ALL MODELS
# VS_MODELS=("gpt_5.2" "gemini_3_pro_preview" "gpt_5.2_codex" "gpt_5_mini" "claude_opus_4.5" "kimi_k2_thinking" "glm_4.7" "gemini_3_flash_preview" "deepseek_v3.2" "deepseek_r1t2_chimera_free" "gpt_oss_120b" "claude_sonnet_4.5" "minimax_m2.1" "mimo_v2_flash_free" "minimax_m2" "qwen3_235b_a22b_2507" "grok_code_fast_1" "deepseek_chat_v3_0324" "tng_r1t_chimera_free" "qwen3_coder" "qwen3_32b" "qwen3_next_80b_a3b_instruct" "kat_coder_pro" "gemini_2.0_flash_001" "devstral_2512_free" "gpt_4o_mini" "nemotron_nano_12b_v2_vl_free" "qwen3_coder_30b_a3b_instruct" "trinity_mini_free" "ministral_14b_2512" )
# VS_MODELS=("gpt_5.2" "gemini_3_pro_preview" "gpt_5.2_codex" "claude_opus_4.5" "kimi_k2_thinking" "deepseek_v3.2" "deepseek_r1t2_chimera_free" "minimax_m2.1" "qwen3_235b_a22b_2507" "grok_code_fast_1" "qwen3_coder" "qwen3_32b" "devstral_2512_free" )
# VS_MODELS=("gemini_3_flash_preview" "minimax_m2" "kat_coder_pro" "devstral_2512_free" "gpt_4o_mini")
# MAX_JOBS=12
# for model in "${MODELS[@]}"; do
#   for vs in "${VS_MODELS[@]}"; do
#     # echo "$model vs $vs"
#     python -m game_arena.live_play \
#       --game_worlds "dots_and_boxes/world1" \
#       --model "$model" \
#       --num_games 1 \
#       --show_legal_moves \
#       --history_len 2 \
#       --vs_model_parent "$vs" &
#     while (( $(jobs -pr | wc -l) >= MAX_JOBS )); do
#       wait -n
#     done
#   done
# done
# wait




exit
}
