#!/usr/bin/env bash
set -euo pipefail

# Assert that this script is run from src/game_arena/stanford_gamemaster.
[ "$(basename "$PWD")" = "stanford_gamemaster" ] || {
  echo "ERROR: run this script from src/game_arena/stanford_gamemaster"
  exit 1
}
[ -d examples ] || { echo "ERROR: examples does not exist"; exit 1; }
[ -d offline_mirror ] || { echo "ERROR: offline_mirror does not exist"; exit 1; }

PYTHON_BIN=../../../env3.12/bin/python
[ -x "$PYTHON_BIN" ] || { echo "ERROR: $PYTHON_BIN does not exist"; exit 1; }

mkdir -p offline_mirror/examples offline_mirror/game_stats/ offline_mirror/prompts/
cp -r examples/. offline_mirror/examples/
cp prompts/* offline_mirror/prompts/
cp ../../../analysis/results_tmp/plots_stanford/bots/rating_df.csv offline_mirror/elos_all_bots.csv
cp ../../../analysis/results_tmp/plots_stanford/bots/heatmaps/model_stats_* offline_mirror/game_stats/

"$PYTHON_BIN" stanford_gamemaster_fetch.py --sync-local-only --output offline_mirror
"$PYTHON_BIN" -m http.server -d offline_mirror 6700
