"""Stockfish 1.0-backed chess heuristic."""

from __future__ import annotations

from pathlib import Path

from src.heuristic._stockfish_legacy_common import LegacyStockfishPolicy


THIS_DIR = Path(__file__).resolve().parent
_IMPL = LegacyStockfishPolicy(
    this_dir=THIS_DIR,
    version_label="Stockfish 1.0",
    env_var="CHESS_STOCKFISH_1_0",
    prewarm_thread_name="stockfish-1.0-prewarm",
)

policy = _IMPL.policy
prewarm_engine = _IMPL.prewarm_engine
INITIAL_PIECES = _IMPL.INITIAL_PIECES

prewarm_engine(wait=True)
