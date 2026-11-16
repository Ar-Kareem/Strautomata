"""Stockfish 1.0 with a 1 second search per move (matches the 1s budget given to model programs)."""

from src.heuristic.chess_stockfish_1.passthrough import policy as _stockfish_1_policy


def policy(pieces, to_play=None, memory=None, move_time_ms=1000):
    return _stockfish_1_policy(pieces, to_play=to_play, move_time_ms=move_time_ms, memory=memory)
