cd ../..


# --game_worlds "stanford_gamemaster/w_albuquerque,stanford_gamemaster/w_alquerque,stanford_gamemaster/w_battleofnumbers,stanford_gamemaster/w_breakthrough,stanford_gamemaster/w_cbnk,stanford_gamemaster/w_chinook,stanford_gamemaster/w_connectfour,stanford_gamemaster/w_crusade,stanford_gamemaster/w_donttouch,stanford_gamemaster/w_hex7x7" \
python -m game_arena.prompter --n_bots 1 \
--game_worlds "stanford_gamemaster/w_albuquerque,stanford_gamemaster/w_alquerque,stanford_gamemaster/w_battleofnumbers,stanford_gamemaster/w_breakthrough,stanford_gamemaster/w_cbnk,stanford_gamemaster/w_chinook,stanford_gamemaster/w_connectfour,stanford_gamemaster/w_crusade,stanford_gamemaster/w_donttouch,stanford_gamemaster/w_hex7x7,stanford_gamemaster/w_knights,stanford_gamemaster/w_knightthrough,stanford_gamemaster/w_knightthroughsmall,stanford_gamemaster/w_kono,stanford_gamemaster/w_leafymcfallface,stanford_gamemaster/w_lines,stanford_gamemaster/w_majorities,stanford_gamemaster/w_minorities,stanford_gamemaster/w_multipleknightthrough,stanford_gamemaster/w_multiplesuicide,stanford_gamemaster/w_multipletictactoe,stanford_gamemaster/w_nineboardtictactoe,stanford_gamemaster/w_parallelbuttonsandlights,stanford_gamemaster/w_parallelhunter,stanford_gamemaster/w_parallelknightthrough,stanford_gamemaster/w_parallelkono,stanford_gamemaster/w_pentago,stanford_gamemaster/w_pentagosuicide,stanford_gamemaster/w_reversum,stanford_gamemaster/w_skirmish,stanford_gamemaster/w_suicide,stanford_gamemaster/w_tictactoe3,stanford_gamemaster/w_tictactoe5,stanford_gamemaster/w_tictactoe7,stanford_gamemaster/w_tictactoe,stanford_gamemaster/w_trifecta,stanford_gamemaster/w_ttcc4" \
--models "TINY|||openai/gpt-5.4-nano,google/gemini-3.1-flash-lite-preview,anthropic/claude-haiku-4.5,moonshotai/kimi-k2.5,z-ai/glm-5,minimax/minimax-m2.7" \
--filter_already_done \
--retry_count 12 \
--max_workers 32



# ---------------------- PLAY GAMES ----------------------
RUN_DIR="results_current/stanford"
# QUALS
QUALS_COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --conf 0.95 --match_limit_L 100 --allowed_bot_nums 1,2,3,4,5 --top_k_model_bots 5 --model_blacklist_file experimental/model_ignore.json --save_results_dir ${RUN_DIR}/quals"
# TEMP_ARGS='--n_games 4 --model_whitelist gpt_5.4 gpt_5.2 --save_results_dir results_temp'
# QUALS_COMMON_ARGS="$QUALS_COMMON_ARGS $TEMP_ARGS"
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_albuquerque" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_alquerque" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_battleofnumbers" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_breakthrough" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_cbnk" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_chinook" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_connectfour" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_crusade" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_donttouch" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_hex7x7" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_knights" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_knightthrough" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_knightthroughsmall" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_kono" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_leafymcfallface" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_lines" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_majorities" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_minorities" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_multipleknightthrough" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_multiplesuicide" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_multipletictactoe" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_nineboardtictactoe" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_parallelbuttonsandlights" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_parallelhunter" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_parallelknightthrough" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_parallelkono" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_pentago" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_pentagosuicide" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_reversum" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_skirmish" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_suicide" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_tictactoe3" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_tictactoe5" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_tictactoe7" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_tictactoe" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_trifecta" $QUALS_COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_quals --game stanford_gamemaster --world "w_ttcc4" $QUALS_COMMON_ARGS

# MAIN TOURNAMENT
COMMON_ARGS="--n_games 110 --timeout 1 --seed 0 --max_workers 50 --save_results_dir ${RUN_DIR}/tourney --top_k_model_bots 2 --model_blacklist_file experimental/model_ignore.json"
# TEMP_ARGS='--n_games 4 --model_whitelist gpt_5.4_high gpt_5.4_medium gpt_5.4 gpt_5.4_low gpt_5.2 --save_results_dir results_temp'
# COMMON_ARGS="$COMMON_ARGS $TEMP_ARGS"
COMMON_ARGS="$COMMON_ARGS --model_blacklist gpt_5.4_instant gpt_5.4_low gpt_5.4_medium gpt_5.4 gpt_5.4_high"
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_albuquerque" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_alquerque" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_battleofnumbers" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_breakthrough" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_cbnk" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_chinook" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_connectfour" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_crusade" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_donttouch" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_hex7x7" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_knights" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_knightthrough" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_knightthroughsmall" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_kono" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_leafymcfallface" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_lines" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_majorities" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_minorities" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_multipleknightthrough" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_multiplesuicide" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_multipletictactoe" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_nineboardtictactoe" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_parallelbuttonsandlights" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_parallelhunter" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_parallelknightthrough" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_parallelkono" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_pentago" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_pentagosuicide" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_reversum" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_skirmish" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_suicide" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_tictactoe3" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_tictactoe5" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_tictactoe7" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_tictactoe" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_trifecta" $COMMON_ARGS
PYTHONHASHSEED=0 python -m game_arena.run_leaderboard main --game stanford_gamemaster --world "w_ttcc4" $COMMON_ARGS




# ------- PROMPTS ---------
# python -m game_arena.stanford_gamemaster.game --world w_albuquerque
# python -m game_arena.stanford_gamemaster.game --world w_albuquerque
# python -m game_arena.stanford_gamemaster.game --world w_alquerque
# python -m game_arena.stanford_gamemaster.game --world w_battleofnumbers
# python -m game_arena.stanford_gamemaster.game --world w_breakthrough
# python -m game_arena.stanford_gamemaster.game --world w_cbnk
# python -m game_arena.stanford_gamemaster.game --world w_chinook
# python -m game_arena.stanford_gamemaster.game --world w_connectfour
# python -m game_arena.stanford_gamemaster.game --world w_crusade
# python -m game_arena.stanford_gamemaster.game --world w_donttouch
# python -m game_arena.stanford_gamemaster.game --world w_hex7x7
# python -m game_arena.stanford_gamemaster.game --world w_knights
# python -m game_arena.stanford_gamemaster.game --world w_knightthrough
# python -m game_arena.stanford_gamemaster.game --world w_knightthroughsmall
# python -m game_arena.stanford_gamemaster.game --world w_kono
# python -m game_arena.stanford_gamemaster.game --world w_leafymcfallface
# python -m game_arena.stanford_gamemaster.game --world w_lines
# python -m game_arena.stanford_gamemaster.game --world w_majorities
# python -m game_arena.stanford_gamemaster.game --world w_minorities
# python -m game_arena.stanford_gamemaster.game --world w_multipleknightthrough
# python -m game_arena.stanford_gamemaster.game --world w_multiplesuicide
# python -m game_arena.stanford_gamemaster.game --world w_multipletictactoe
# python -m game_arena.stanford_gamemaster.game --world w_nineboardtictactoe
# python -m game_arena.stanford_gamemaster.game --world w_parallelbuttonsandlights
# python -m game_arena.stanford_gamemaster.game --world w_parallelhunter
# python -m game_arena.stanford_gamemaster.game --world w_parallelknightthrough
# python -m game_arena.stanford_gamemaster.game --world w_parallelkono
# python -m game_arena.stanford_gamemaster.game --world w_pentago
# python -m game_arena.stanford_gamemaster.game --world w_pentagosuicide
# python -m game_arena.stanford_gamemaster.game --world w_reversum
# python -m game_arena.stanford_gamemaster.game --world w_skirmish
# python -m game_arena.stanford_gamemaster.game --world w_suicide
# python -m game_arena.stanford_gamemaster.game --world w_tictactoe3
# python -m game_arena.stanford_gamemaster.game --world w_tictactoe5
# python -m game_arena.stanford_gamemaster.game --world w_tictactoe7
# python -m game_arena.stanford_gamemaster.game --world w_tictactoe
# python -m game_arena.stanford_gamemaster.game --world w_trifecta
# python -m game_arena.stanford_gamemaster.game --world w_ttcc4