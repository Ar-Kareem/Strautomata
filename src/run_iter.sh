# nvidia/nemotron-3-super-120b-a12b:free $0
# openai/gpt-5.4-nano $1.25
# google/gemini-3.1-flash-lite-preview $1.5
# minimax/minimax-m2.7 $1.2
# xiaomi/mimo-v2-omni $2


    # --model qwen/qwen3-235b-a22b-2507 \
    # --model qwen/qwen3.5-flash-02-23 \
    # --model qwen/qwen3-30b-a3b-instruct-2507 \
python -m game_arena.z_arc.run_experiment \
    --experiment hex_code_002 \
    --game hex \
    --world world1 \
    --model openai/gpt-5.4-nano \
    --model google/gemini-3.1-flash-lite-preview \
    --comparison_model claude_opus_4.6 \
    --comparison_model gpt_5.2 \
    --timeout 1 \
    --n_bots 4 \
    --n_games 1 \
    --n_generations 5 \
    --retry_count 3 \
    --max_workers 32 \
    --filter_already_done \
    --feedback_mode peer_code \
    --state_history_stride 1

python -m game_arena.z_arc.all_generations \
    --experiment hex_code_002 \
    --n_games 1 \
    --timeout 1 \
    --max_workers 32

# just plot
python -m game_arena.z_arc.all_generations --experiment hex_code_002 --plot_only