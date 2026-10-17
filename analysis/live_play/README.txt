Live-play comparisons
=====================
Run from the repository root:
  MPLCONFIGDIR=/tmp/mpl-live-numbered OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=src env3.12/bin/python analysis/live_play/generate.py --bot-errors include

Output layout:
  iter/clean/  Notebook iterative Elo; completed live games only.
  iter/all/    Notebook iterative Elo; completed games plus attributable forfeits.
  bt/clean/    Paper simple_example BT pipeline; completed live games only.
  bt/all/      Paper simple_example BT pipeline; completed games plus attributable forfeits.

Each directory contains numbers.png/pdf and hand.png/pdf.
CSV exports are optional: pass --export-data. Model numbers are shared. Hand-picked
labels are Gemini 3 Flash Preview, Ministral 14B, GPT-5 Mini, Qwen3 235B,
DeepSeek V3.2, and GPT-4o Mini. Gemini's legal-moves-shown/hidden populations stay separate.

Population:
Both results_live_legacy_pre_2026_oct and results_live are read. Trash and
results_live_unsaved are excluded. Exact duplicate records are removed.
Clean/all changes the live-game population; the tournament baseline retains
its normal scoring in both variants.

'all' includes terminal illegal moves/retry exhaustion and bot-code crashes,
with the offending player losing. It does not retroactively forfeit a finished
game over an illegal retry that the original harness allowed the model to fix.
Legacy generic retry failures require traceback evidence of illegal-move
exhaustion. API/network failures, I/O errors and unattributed failures are
excluded. A final API failure is not scored based on an earlier illegal retry.
With --export-data, every classification is written to game_audit.csv.
No source game JSON is modified.

Methods:
iter reproduces notebook top-1 selection, parent-name collapse, and final
iterative Elo fit with 20 passes and learning_rate=2. It may not converge.
bt calls simple_example.main_results(rating_system='bt', only_model=False),
with 100 bootstrap samples and seed 42. Actual bot identities remain distinct.
The automaton point is the joint-fit rating of the model's best bot selected
by BT on the tournament alone. BT's standard qualifier filtering is retained.
Live populations with only wins or only losses have no finite maximum-
likelihood rating and are omitted from BT figures (but retained and flagged
in optional plot_points.csv exports). Numerical solver outputs for such rows are not ratings.

Tests:
  MPLCONFIGDIR=/tmp/mpl-live-numbered PYTHONPATH=src env3.12/bin/python analysis/live_play/test_classification.py
