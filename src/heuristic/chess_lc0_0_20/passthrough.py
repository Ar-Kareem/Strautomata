"""Leela Chess Zero v0.20-backed chess heuristic.

This wrapper uses a locally built lc0 v0.20.2 UCI engine and a pinned legacy
network bundled in this directory. The arena passes `pieces` and `to_play`,
 and the wrapper rebuilds a best-effort FEN directly from that
state.
"""

from __future__ import annotations

import atexit
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Optional


THIS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = THIS_DIR / "vendor" / "lc0"
DEFAULT_MOVE_TIME_MS = 2500
DEFAULT_THREADS = 1
DEFAULT_MINIBATCH_SIZE = 1
FILES = "abcdefgh"
_DIRECT_MEMORY: dict[str, Any] = {}

_ENGINE_LOCK = threading.Lock()
_ENGINE: Optional[subprocess.Popen[str]] = None
_ENGINE_READY = False
_ENGINE_BROKEN = False
_PREWARM_LOCK = threading.Lock()
_PREWARM_STARTED = False
_PREWARM_FINISHED = False
_PREWARM_THREAD: Optional[threading.Thread] = None


def _add_timing(timings: Optional[list[tuple[str, float]]], label: str, started_at: float) -> None:
    if timings is not None:
        timings.append((label, time.perf_counter() - started_at))


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
    override = os.environ.get("CHESS_LC0_0_20")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.extend(
        [
            VENDOR_DIR / "lc0",
            THIS_DIR / ".runtime" / "lc0-v0.20.2" / "build" / "release" / "lc0",
        ]
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _discover_weights_path() -> Optional[Path]:
    override = os.environ.get("CHESS_LC0_0_20_WEIGHTS")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.extend(
        [
            VENDOR_DIR / "networks" / "weights.pb.gz",
            THIS_DIR / ".runtime" / "weights.pb.gz",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _discover_library_dirs() -> list[Path]:
    candidates = [
        VENDOR_DIR / "lib",
        THIS_DIR / ".runtime" / "lc0-v0.20.2" / "build" / "release" / "subprojects" / "protobuf-3.5.1",
        THIS_DIR / ".runtime" / "lc0-v0.20.2" / "build" / "release" / "subprojects" / "protobuf-3.6.0",
    ]
    return [path for path in candidates if path.is_dir()]


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


def _ensure_engine(timings: Optional[list[tuple[str, float]]] = None) -> bool:
    global _ENGINE, _ENGINE_READY, _ENGINE_BROKEN
    total_started_at = time.perf_counter()
    if _ENGINE_BROKEN:
        _add_timing(timings, "ensure_engine.broken_flag", total_started_at)
        return False
    if _ENGINE is not None and _ENGINE_READY and _ENGINE.poll() is None:
        _add_timing(timings, "ensure_engine.fast_path", total_started_at)
        return True

    _close_engine()
    started_at = time.perf_counter()
    engine_path = _discover_engine_path()
    weights_path = _discover_weights_path()
    _add_timing(timings, "ensure_engine.discover_paths", started_at)
    if engine_path is None or weights_path is None:
        _ENGINE_BROKEN = True
        _add_timing(timings, "ensure_engine.total", total_started_at)
        return False

    try:
        started_at = time.perf_counter()
        env = os.environ.copy()
        library_dirs = _discover_library_dirs()
        if library_dirs:
            existing_ld_path = env.get("LD_LIBRARY_PATH", "")
            extra_ld_path = ":".join(str(path) for path in library_dirs)
            env["LD_LIBRARY_PATH"] = (
                f"{extra_ld_path}:{existing_ld_path}" if existing_ld_path else extra_ld_path
            )
        _add_timing(timings, "ensure_engine.prepare_env", started_at)
        started_at = time.perf_counter()
        _ENGINE = subprocess.Popen(
            [
                str(engine_path),
                f"--weights={weights_path}",
                "--backend=blas",
                f"--threads={DEFAULT_THREADS}",
                "--move-overhead=5",
                f"--minibatch-size={DEFAULT_MINIBATCH_SIZE}",
                "--temperature=0",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
        )
        _add_timing(timings, "ensure_engine.spawn", started_at)
        started_at = time.perf_counter()
        _engine_write("uci")
        _add_timing(timings, "ensure_engine.write_uci", started_at)
        started_at = time.perf_counter()
        if _engine_read_until(("uciok",)) != "uciok":
            raise RuntimeError("lc0 did not answer uciok")
        _add_timing(timings, "ensure_engine.wait_uciok", started_at)
        started_at = time.perf_counter()
        _engine_write("isready")
        _add_timing(timings, "ensure_engine.write_isready", started_at)
        started_at = time.perf_counter()
        if _engine_read_until(("readyok",)) != "readyok":
            raise RuntimeError("lc0 did not answer readyok")
        _add_timing(timings, "ensure_engine.wait_readyok", started_at)
        _ENGINE_READY = True
        _add_timing(timings, "ensure_engine.total", total_started_at)
        return True
    except Exception:
        _ENGINE_BROKEN = True
        _close_engine()
        _add_timing(timings, "ensure_engine.total", total_started_at)
        return False


def _run_dummy_search() -> bool:
    with _ENGINE_LOCK:
        if not _ensure_engine():
            return False
        assert _ENGINE is not None
        try:
            _engine_write("ucinewgame")
            _engine_write("position startpos")
            _engine_write("go movetime 1")
            response = _engine_read_until(("bestmove ",))
            return response is not None and response.startswith("bestmove ")
        except Exception:
            global _ENGINE_BROKEN
            _ENGINE_BROKEN = True
            _close_engine()
            return False


def prewarm_engine(wait: bool = False) -> bool:
    global _PREWARM_STARTED, _PREWARM_FINISHED, _PREWARM_THREAD

    def _prewarm_target() -> None:
        global _PREWARM_FINISHED
        if _run_dummy_search():
            _PREWARM_FINISHED = True

    with _PREWARM_LOCK:
        if not _PREWARM_STARTED:
            _PREWARM_STARTED = True
            _PREWARM_THREAD = threading.Thread(
                target=_prewarm_target,
                name="lc0-prewarm",
                daemon=True,
            )
            _PREWARM_THREAD.start()
        thread = _PREWARM_THREAD
    if wait and thread is not None:
        thread.join()
    return (
        _PREWARM_FINISHED
        and _ENGINE_READY
        and _ENGINE is not None
        and _ENGINE.poll() is None
    )


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
            "engine_needs_ucinewgame": True,
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
    timings: Optional[list[tuple[str, float]]] = None,
) -> None:
    started_at = time.perf_counter()
    if not memory:
        _reset_tracking(memory)
    _add_timing(timings, "state.ensure_memory", started_at)
    started_at = time.perf_counter()
    tracked_side = memory.get("side")
    if tracked_side not in ("white", "black"):
        memory["side"] = to_play
    elif tracked_side != to_play:
        _reset_tracking(memory)
        memory["side"] = to_play
    elif _is_initial_position(pieces, to_play):
        _reset_tracking(memory)
        memory["side"] = to_play
    _add_timing(timings, "state.boundary_check", started_at)

    started_at = time.perf_counter()
    previous_pieces = memory.get("last_pieces")
    if previous_pieces is not None and previous_pieces != pieces:
        memory["turn_count"] = int(memory.get("turn_count", 0)) + 1
    _add_timing(timings, "state.turn_count", started_at)
    started_at = time.perf_counter()
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
    _add_timing(timings, "state.scan_home_squares", started_at)


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


def _fen_from_state(
    pieces: dict[str, str],
    to_play: str,
    memory: dict[str, Any],
    timings: Optional[list[tuple[str, float]]] = None,
) -> str:
    started_at = time.perf_counter()
    _update_tracking(pieces, to_play, memory, timings=timings)
    _add_timing(timings, "fen.update_tracking", started_at)
    started_at = time.perf_counter()
    board_fen = _board_fen_from_pieces(pieces)
    _add_timing(timings, "fen.board_from_pieces", started_at)
    turn = "w" if to_play == "white" else "b"
    started_at = time.perf_counter()
    castling = _tracked_castling_rights(pieces, memory)
    _add_timing(timings, "fen.castling_rights", started_at)
    # This observation interface does not expose enough information to recover
    # en passant targets exactly on every turn, so leave it unset.
    started_at = time.perf_counter()
    fullmove_number = 1 + int(memory.get("turn_count", 0))
    fen = f"{board_fen} {turn} {castling} - 0 {fullmove_number}"
    _add_timing(timings, "fen.compose", started_at)
    return fen


def _query_lc0(
    fen: str,
    move_time_ms: int,
    new_game: bool = False,
    timings: Optional[list[tuple[str, float]]] = None,
) -> Optional[str]:
    lock_started_at = time.perf_counter()
    with _ENGINE_LOCK:
        _add_timing(timings, "query.lock_wait", lock_started_at)
        started_at = time.perf_counter()
        if not _ensure_engine(timings=timings):
            _add_timing(timings, "query.ensure_engine_total", started_at)
            return None
        _add_timing(timings, "query.ensure_engine_total", started_at)
        assert _ENGINE is not None
        try:
            total_started_at = time.perf_counter()
            if new_game:
                started_at = time.perf_counter()
                _engine_write("ucinewgame")
                _add_timing(timings, "query.write_ucinewgame", started_at)
            started_at = time.perf_counter()
            _engine_write(f"position fen {fen}")
            _add_timing(timings, "query.write_position", started_at)
            started_at = time.perf_counter()
            _engine_write(f"go movetime {move_time_ms}")
            _add_timing(timings, "query.write_go", started_at)
            started_at = time.perf_counter()
            response = _engine_read_until(("bestmove ",))
            _add_timing(timings, "query.wait_bestmove", started_at)
            if response is None:
                _add_timing(timings, "query.total", total_started_at)
                return None
            started_at = time.perf_counter()
            parts = response.split()
            _add_timing(timings, "query.parse_bestmove", started_at)
            if len(parts) < 2 or parts[1] == "(none)":
                _add_timing(timings, "query.total", total_started_at)
                return None
            _add_timing(timings, "query.total", total_started_at)
            return parts[1]
        except Exception:
            global _ENGINE_BROKEN
            _ENGINE_BROKEN = True
            _close_engine()
            return None


def choose_move(
    pieces,
    to_play: Optional[str] = None,
    move_time_ms: int = DEFAULT_MOVE_TIME_MS,
    memory: Optional[dict[str, Any]] = None,
    debug: bool = False,
) -> tuple[str, dict[str, Any], Optional[dict[str, Any]]]:
    timings: Optional[list[tuple[str, float]]] = [] if debug else None
    total_started_at = time.perf_counter()
    if memory is None:
        memory = _DIRECT_MEMORY

    started_at = time.perf_counter()
    if to_play is None and isinstance(pieces, dict) and "pieces" in pieces:
        state = pieces
        pieces = state.get("pieces", {})
        to_play = state.get("to_play", "white")
    if to_play is None:
        to_play = "white"
    _add_timing(timings, "policy.normalize_input", started_at)

    started_at = time.perf_counter()
    fen = _fen_from_state(pieces, to_play, memory, timings=timings)
    _add_timing(timings, "policy.build_fen_total", started_at)
    new_game = bool(memory.get("engine_needs_ucinewgame", False))
    started_at = time.perf_counter()
    bestmove = _query_lc0(
        fen,
        max(10, int(move_time_ms)),
        new_game=new_game,
        timings=timings,
    )
    _add_timing(timings, "policy.query_engine_total", started_at)
    move = bestmove or ""
    if bestmove is not None and new_game:
        memory["engine_needs_ucinewgame"] = False

    info: Optional[dict[str, Any]] = None
    if timings is not None:
        _add_timing(timings, "policy.total", total_started_at)
        info = {
            "fen": fen,
            "timings": timings,
            "move_time_ms": max(10, int(move_time_ms)),
            "move": move,
        }
    return move, memory, info


def policy(
    pieces,
    to_play: Optional[str] = None,
    move_time_ms: int = DEFAULT_MOVE_TIME_MS,
    memory: Optional[dict[str, Any]] = None,
):
    using_wrapped_memory = memory is not None
    move, memory, _ = choose_move(
        pieces,
        to_play=to_play,
        move_time_ms=move_time_ms,
        memory=memory,
        debug=False,
    )
    if using_wrapped_memory:
        return move, memory
    return move


prewarm_engine(wait=True)
