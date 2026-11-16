# Strautomata

LLMs are prompted to write game-playing programs ("automata") for 20 two-player games. The automata then compete in qualifiers and a tournament, and the results are turned into ELO ratings per model and per automaton.

All automata are committed to the repository. For game "$GAME" the automata are in the directory `src/game_arena/$GAME/examples/$WORLD` where $WORLD is almost always "world1" (simply used when a game has multiple configurations like 3x3 and 4x4 tic-tac-toe).

This repo includes all code needed to reproduce all results in the paper from scratch.

## Games and Automata

- `src/game_arena/` contains 1 folder per game. Includes implementation, all automata, prompter, qualifiers (`run_quals.py`) and tournament (`run_leaderboard.py`)

The games are: amazons, backgammon, battleships, breakthrough, checkers, chess, clobber, connect4, dots_and_boxes, go, havannah, hex, lines_of_action, mancala, nim, othello, pentago, tic_tac_toe (3x3 and 4x4), tic_tac_toe_3d.


## Install

```bash
# Create a local env (python 3.12.12 for exact version)
conda create -y -p ./env python=3.12
conda activate ./env

# Pip / install requirements
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

All commands below are run from the `src/` directory.

Prompting automata requires an OpenRouter API key in a `.env` file at the repository root:

Running the qualifiers and tournament does not need an API key since all automata are already committed.


# Prompt automata:


A simple bash loop can be used to prompt $N$ automata for each model and each game in the project. For example the following prompts 5 automata for each of the 3 models and each of the 20 games in the project. The file `prompter_overrides.json` specifies how the string `openai/gpt-5.5-instant` is mapped to the openrouter model `openai/gpt-5.5` with specific special parameters. If your model is default openrouter model then no entry is needed in the `prompter_overrides.json` file.


```bash
while true; do
  if python -m game_arena.prompter --n_bots 5 \
    --game_worlds "tic_tac_toe_3d/world1,tic_tac_toe/world1,tic_tac_toe/world2,battleships/world1,connect4/world1,mancala/world1,othello/world1,lines_of_action/world1,pentago/world1,clobber/world1,amazons/world1,backgammon/world1,nim/world1,dots_and_boxes/world1,chess/worlduci1,go/world1,checkers/world1,havannah/world1,hex/world1,breakthrough/world1" \
    --models "openai/gpt-5.5-instant,openai/gpt-5.5-low,openai/gpt-5.5-medium" \
    --filter_already_done \
    --max_workers 24
  then
    echo "All prompting successful. Exiting."
    break
  else
    status=$?
    echo "Some prompting failed (exit $status). Retrying in 5s..."
    sleep 5
  fi
done
```


# Run Qualifiers:


The qualifiers for all games can be simply run with


```bash
RUN_DIR="results_experiments/name_of_experiment_here"
QUALS_COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --conf 0.95 --match_limit_L 100 --allowed_bot_nums 1,2,3,4,5 --top_k_model_bots 5 --model_blacklist_file experimental/model_ignore.json --save_results_dir ${RUN_DIR}/quals"
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
```


# Run Tournament:


The tournament is very similar to the qualifiers:


```bash
COMMON_ARGS="--n_games 10 --timeout 1 --seed 0 --max_workers 50 --quals_dir ${RUN_DIR}/quals --save_results_dir ${RUN_DIR}/tourney --top_k_model_bots 2 --model_blacklist_file experimental/model_ignore.json"
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
```


# Plotting and Analysis:


Once all qualifiers and tournament are run, the resulting json files can be grouped into a `.pkl` and plotted using the following commands:


```bash
python -m experimental.exp_plotting gen_pkl --results-dir results_experiments/name_of_experiment_here/tourney --out-pkl analysis/results_tmp/exp_results_name_of_experiment_here.pkl
python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_name_of_experiment_here.pkl --mode models --out-dir analysis/results_tmp/plots_name_of_experiment_here/models
python -m experimental.exp_plotting plot_pkl --in-pkl analysis/results_tmp/exp_results_name_of_experiment_here.pkl --mode bots --out-dir analysis/results_tmp/plots_name_of_experiment_here/bots
```


## Extra analysis:


There are multiple extra analysis scripts that can be run to get more insights into the data. These are included in `run_analysis.sh`. Additionally there are scripts:

- `python -m experimental.exp_plotting plot_pkl` - Main plotting script that can be used to plot the results of a `.pkl` file.
- `python -m experimental.exp_plot_pkl_pkl` - Compares two `.pkl` files and exports a scatter plot of the ELOs.
- `scripts/analyze_current_bots.py` - Analyzes the current automata in the repository and exports a CSV file with the number of automata for each model and game.
- `python -m experimental.exp_count_stage_games` - Counts the number of qualifiers and tournament matches for each game and exports a LaTeX table.
- `python -m experimental.exp_openrouter`- Aggregates the OpenRouter CSV files and exports a LaTeX table of the model metadata.
- `python -m experimental.exp_randomness main` - Look in `run_analysis.sh` for exact commands to run this analyzes the randomness of the automata.
- `python -m experimental.exp_randomness latex/barplot/scatter` - This outputs the visualizations from the above randomness analysis.
- `python -m experimental.lm_arena.my_comparison` - Compares the Strautomata ELOs with the LM Arena ELOs and SWE-bench ELOs.


# New Environments:


Adding new environments to the project is simple, add it in the `game_arena` folder and make it match the structure of existing environments. Add it in `utils.py` and `exp_utils.py`.
