"""Stockfish 9-backed chess heuristic.

This wrapper uses a locally compiled Stockfish 9 UCI engine bundled in this
directory. The arena passes `pieces` and `to_play`, and the wrapper rebuilds a
best-effort FEN directly from that state.
"""

from __future__ import annotations

import atexit
import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Iterable, Optional


THIS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = THIS_DIR / "vendor" / "stockfish"
DEFAULT_MOVE_TIME_MS = 2500
DEFAULT_HASH_MB = 16
DEFAULT_THREADS = 1
FILES = "abcdefgh"
_DIRECT_MEMORY: dict[str, Any] = {}

_ENGINE_LOCK = threading.Lock()
_ENGINE: Optional[subprocess.Popen[str]] = None
_ENGINE_READY = False
_ENGINE_BROKEN = False


def _initial_pieces() -> dict[str, str]:
    pieces = {
        "a1": "wR",
        "b1": "wN",
        "c1": "wB",
        "d1": "wQ",
        "e1": "wK",
        "f1": "wB",
        "g1": "wN",
        "h1": "wR",
        "a8": "bR",
        "b8": "bN",
        "c8": "bB",
        "d8": "bQ",
        "e8": "bK",
        "f8": "bB",
        "g8": "bN",
        "h8": "bR",
    }
    for file_char in FILES:
        pieces[f"{file_char}2"] = "wP"
        pieces[f"{file_char}7"] = "bP"
    return pieces


INITIAL_PIECES = _initial_pieces()


def _discover_engine_path() -> Optional[Path]:
    override = os.environ.get("CHESS_STOCKFISH_9")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.extend(
        [
            VENDOR_DIR / "src" / "stockfish",
            VENDOR_DIR / "stockfish",
        ]
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _close_engine() -> None:
    global _ENGINE, _ENGINE_READY
    engine = _ENGINE
    _ENGINE = None
    _ENGINE_READY = False
    if engine is None:
        return
    try:
        if engine.stdin is not None:
            engine.stdin.write("quit\n")
            engine.stdin.flush()
    except Exception:
        pass
    try:
        engine.terminate()
        engine.wait(timeout=1.0)
    except Exception:
        try:
            engine.kill()
        except Exception:
            pass


atexit.register(_close_engine)


def _engine_read_until(prefixes: Iterable[str]) -> Optional[str]:
    assert _ENGINE is not None and _ENGINE.stdout is not None
    for line in _ENGINE.stdout:
        stripped = line.strip()
        for prefix in prefixes:
            if stripped.startswith(prefix):
                return stripped
    return None


def _engine_write(command: str) -> None:
    assert _ENGINE is not None and _ENGINE.stdin is not None
    _ENGINE.stdin.write(command + "\n")
    _ENGINE.stdin.flush()


def _ensure_engine() -> bool:
    global _ENGINE, _ENGINE_READY, _ENGINE_BROKEN
    if _ENGINE_BROKEN:
        return False
    if _ENGINE is not None and _ENGINE_READY and _ENGINE.poll() is None:
        return True

    _close_engine()
    engine_path = _discover_engine_path()
    if engine_path is None:
        _ENGINE_BROKEN = True
        return False

    try:
        _ENGINE = subprocess.Popen(
            [str(engine_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        _engine_write("uci")
        if _engine_read_until(("uciok",)) != "uciok":
            raise RuntimeError("Stockfish did not answer uciok")
        _engine_write(f"setoption name Threads value {DEFAULT_THREADS}")
        _engine_write(f"setoption name Hash value {DEFAULT_HASH_MB}")
        _engine_write("setoption name Ponder value false")
        _engine_write("isready")
        if _engine_read_until(("readyok",)) != "readyok":
            raise RuntimeError("Stockfish did not answer readyok")
        _ENGINE_READY = True
        return True
    except Exception:
        _ENGINE_BROKEN = True
        _close_engine()
        return False


def _piece_to_fen(code: str) -> str:
    if len(code) != 2:
        raise ValueError(f"Invalid piece code: {code!r}")
    color, piece = code[0], code[1]
    return piece.upper() if color == "w" else piece.lower()


def _board_fen_from_pieces(pieces: dict[str, str]) -> str:
    rows = []
    for rank in range(8, 0, -1):
        empties = 0
        row_parts = []
        for file_char in FILES:
            square = f"{file_char}{rank}"
            code = pieces.get(square)
            if code is None:
                empties += 1
                continue
            if empties:
                row_parts.append(str(empties))
                empties = 0
            row_parts.append(_piece_to_fen(code))
        if empties:
            row_parts.append(str(empties))
        rows.append("".join(row_parts))
    return "/".join(rows)


def _reset_tracking(memory: dict[str, Any]) -> None:
    memory.clear()
    memory.update(
        {
            "side": None,
            "white_king_moved": False,
            "white_queenside_rook_moved": False,
            "white_kingside_rook_moved": False,
            "black_king_moved": False,
            "black_queenside_rook_moved": False,
            "black_kingside_rook_moved": False,
            "turn_count": 0,
            "last_pieces": None,
        }
    )


def _is_initial_position(pieces: dict[str, str], to_play: str) -> bool:
    return to_play == "white" and pieces == INITIAL_PIECES


def _update_tracking(
    pieces: dict[str, str],
    to_play: str,
    memory: dict[str, Any],
) -> None:
    if not memory:
        _reset_tracking(memory)
    tracked_side = memory.get("side")
    if tracked_side not in ("white", "black"):
        memory["side"] = to_play
    elif tracked_side != to_play:
        _reset_tracking(memory)
        memory["side"] = to_play
    elif _is_initial_position(pieces, to_play):
        _reset_tracking(memory)
        memory["side"] = to_play

    previous_pieces = memory.get("last_pieces")
    if previous_pieces is not None and previous_pieces != pieces:
        memory["turn_count"] = int(memory.get("turn_count", 0)) + 1

    if previous_pieces != pieces:
        if pieces.get("e1") != "wK":
            memory["white_king_moved"] = True
        if pieces.get("a1") != "wR":
            memory["white_queenside_rook_moved"] = True
        if pieces.get("h1") != "wR":
            memory["white_kingside_rook_moved"] = True
        if pieces.get("e8") != "bK":
            memory["black_king_moved"] = True
        if pieces.get("a8") != "bR":
            memory["black_queenside_rook_moved"] = True
        if pieces.get("h8") != "bR":
            memory["black_kingside_rook_moved"] = True
        memory["last_pieces"] = dict(pieces)


def _tracked_castling_rights(pieces: dict[str, str], memory: dict[str, Any]) -> str:
    rights = []
    if pieces.get("e1") == "wK" and not memory.get("white_king_moved", False):
        if pieces.get("h1") == "wR" and not memory.get("white_kingside_rook_moved", False):
            rights.append("K")
        if pieces.get("a1") == "wR" and not memory.get("white_queenside_rook_moved", False):
            rights.append("Q")
    if pieces.get("e8") == "bK" and not memory.get("black_king_moved", False):
        if pieces.get("h8") == "bR" and not memory.get("black_kingside_rook_moved", False):
            rights.append("k")
        if pieces.get("a8") == "bR" and not memory.get("black_queenside_rook_moved", False):
            rights.append("q")
    return "".join(rights) or "-"


def _fen_from_state(pieces: dict[str, str], to_play: str, memory: dict[str, Any]) -> str:
    _update_tracking(pieces, to_play, memory)
    board_fen = _board_fen_from_pieces(pieces)
    turn = "w" if to_play == "white" else "b"
    castling = _tracked_castling_rights(pieces, memory)
    fullmove_number = 1 + int(memory.get("turn_count", 0))
    return f"{board_fen} {turn} {castling} - 0 {fullmove_number}"


def _query_stockfish(fen: str, move_time_ms: int) -> Optional[str]:
    with _ENGINE_LOCK:
        if not _ensure_engine():
            return None
        assert _ENGINE is not None
        try:
            _engine_write("ucinewgame")
            _engine_write("isready")
            if _engine_read_until(("readyok",)) != "readyok":
                return None
            _engine_write(f"position fen {fen}")
            _engine_write(f"go movetime {move_time_ms}")
            response = _engine_read_until(("bestmove ",))
            if response is None:
                return None
            parts = response.split()
            if len(parts) < 2 or parts[1] == "(none)":
                return None
            return parts[1]
        except Exception:
            global _ENGINE_BROKEN
            _ENGINE_BROKEN = True
            _close_engine()
            return None


def policy(
    pieces,
    to_play: Optional[str] = None,
    move_time_ms: int = DEFAULT_MOVE_TIME_MS,
    memory: Optional[dict[str, Any]] = None,
):
    using_wrapped_memory = memory is not None
    if memory is None:
        memory = _DIRECT_MEMORY

    if to_play is None and isinstance(pieces, dict) and "pieces" in pieces:
        state = pieces
        pieces = state.get("pieces", {})
        to_play = state.get("to_play", "white")

    if to_play is None:
        to_play = "white"

    fen = _fen_from_state(pieces, to_play, memory)
    bestmove = _query_stockfish(fen, max(10, int(move_time_ms)))
    move = bestmove or ""
    if using_wrapped_memory:
        return move, memory
    return move
