"""Stockfish 9 with a strict 1 second budget per move (950 ms search so wall time incl. overhead stays under 1 s)."""

from src.heuristic.chess_stockfish_9.passthrough import policy as _stockfish_policy


def policy(pieces, to_play=None, memory=None, move_time_ms=950):
    return _stockfish_policy(pieces, to_play=to_play, move_time_ms=move_time_ms, memory=memory)
