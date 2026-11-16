from __future__ import annotations

import atexit
import os
import select
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Optional


class LegacyStockfishPolicy:
    DEFAULT_MOVE_TIME_MS = 2500
    DEFAULT_HASH_MB = 16
    DEFAULT_THREADS = 1
    PREWARM_WAIT_TIMEOUT_SECONDS = 30.0
    FILES = "abcdefgh"

    def __init__(
        self,
        *,
        this_dir: Path,
        version_label: str,
        env_var: str,
        prewarm_thread_name: str,
    ) -> None:
        self.this_dir = this_dir
        self.vendor_dir = this_dir / "vendor" / "stockfish"
        self.version_label = version_label
        self.env_var = env_var
        self.prewarm_thread_name = prewarm_thread_name

        self._direct_memory: dict[str, Any] = {}
        self._engine_lock = threading.Lock()
        self._engine: Optional[subprocess.Popen[bytes]] = None
        self._engine_buffer = b""
        self._engine_ready = False
        self._engine_broken = False
        self._prewarm_lock = threading.Lock()
        self._prewarm_started = False
        self._prewarm_finished = False
        self._prewarm_thread: Optional[threading.Thread] = None
        self.INITIAL_PIECES = self._initial_pieces()

        atexit.register(self._close_engine)

    def _initial_pieces(self) -> dict[str, str]:
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
        for file_char in self.FILES:
            pieces[f"{file_char}2"] = "wP"
            pieces[f"{file_char}7"] = "bP"
        return pieces

    def _discover_engine_path(self) -> Optional[Path]:
        override = os.environ.get(self.env_var)
        candidates = []
        if override:
            candidates.append(Path(override))
        candidates.extend(
            [
                self.vendor_dir / "src" / "stockfish",
                self.vendor_dir / "stockfish",
            ]
        )
        for candidate in candidates:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate
        return None

    def _close_engine(self) -> None:
        engine = self._engine
        self._engine = None
        self._engine_ready = False
        self._engine_buffer = b""
        if engine is None:
            return
        try:
            if engine.stdin is not None:
                engine.stdin.write(b"quit\n")
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

    def _engine_read_until(
        self,
        prefixes: Iterable[str],
        timeout_s: Optional[float] = None,
    ) -> Optional[str]:
        assert self._engine is not None and self._engine.stdout is not None
        stdout = self._engine.stdout
        fd = stdout.fileno()
        deadline = None if timeout_s is None else time.monotonic() + timeout_s
        while True:
            while b"\n" in self._engine_buffer:
                raw_line, self._engine_buffer = self._engine_buffer.split(b"\n", 1)
                stripped = raw_line.strip().decode("utf-8", errors="replace")
                for prefix in prefixes:
                    if stripped.startswith(prefix):
                        return stripped
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                readable, _, _ = select.select([fd], [], [], remaining)
                if not readable:
                    return None
            chunk = os.read(fd, 4096)
            if not chunk:
                if self._engine_buffer:
                    stripped = self._engine_buffer.strip().decode("utf-8", errors="replace")
                    self._engine_buffer = b""
                    for prefix in prefixes:
                        if stripped.startswith(prefix):
                            return stripped
                return None
            self._engine_buffer += chunk

    def _engine_write(self, command: str) -> None:
        assert self._engine is not None and self._engine.stdin is not None
        self._engine.stdin.write((command + "\n").encode("utf-8"))
        self._engine.stdin.flush()

    def _ensure_engine(self, timeout_s: Optional[float] = None) -> bool:
        if self._engine_broken:
            return False
        if self._engine is not None and self._engine_ready and self._engine.poll() is None:
            return True

        self._close_engine()
        engine_path = self._discover_engine_path()
        if engine_path is None:
            self._engine_broken = True
            return False

        try:
            self._engine = subprocess.Popen(
                [str(engine_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=False,
                bufsize=0,
            )
            self._engine_write("uci")
            if self._engine_read_until(("uciok",), timeout_s=timeout_s) != "uciok":
                raise RuntimeError(f"{self.version_label} did not answer uciok")
            self._engine_write(f"setoption name Threads value {self.DEFAULT_THREADS}")
            self._engine_write(f"setoption name Hash value {self.DEFAULT_HASH_MB}")
            self._engine_write("setoption name Ponder value false")
            self._engine_write("isready")
            if self._engine_read_until(("readyok",), timeout_s=timeout_s) != "readyok":
                raise RuntimeError(f"{self.version_label} did not answer readyok")
            self._engine_ready = True
            return True
        except Exception:
            self._engine_broken = True
            self._close_engine()
            return False

    def _run_dummy_search(self, timeout_s: float = PREWARM_WAIT_TIMEOUT_SECONDS) -> bool:
        with self._engine_lock:
            if not self._ensure_engine(timeout_s=timeout_s):
                return False
            assert self._engine is not None
            try:
                self._engine_write("ucinewgame")
                self._engine_write("position startpos")
                self._engine_write("go movetime 1")
                response = self._engine_read_until(("bestmove ",), timeout_s=timeout_s)
                return response is not None and response.startswith("bestmove ")
            except Exception:
                self._engine_broken = True
                self._close_engine()
                return False

    def prewarm_engine(self, wait: bool = False) -> bool:
        def _prewarm_target() -> None:
            if self._run_dummy_search():
                self._prewarm_finished = True

        with self._prewarm_lock:
            if not self._prewarm_started:
                self._prewarm_started = True
                self._prewarm_thread = threading.Thread(
                    target=_prewarm_target,
                    name=self.prewarm_thread_name,
                    daemon=True,
                )
                self._prewarm_thread.start()
            thread = self._prewarm_thread
        if wait and thread is not None:
            thread.join(timeout=self.PREWARM_WAIT_TIMEOUT_SECONDS)
        return (
            self._prewarm_finished
            and self._engine_ready
            and self._engine is not None
            and self._engine.poll() is None
        )

    def _piece_to_fen(self, code: str) -> str:
        if len(code) != 2:
            raise ValueError(f"Invalid piece code: {code!r}")
        color, piece = code[0], code[1]
        return piece.upper() if color == "w" else piece.lower()

    def _board_fen_from_pieces(self, pieces: dict[str, str]) -> str:
        rows = []
        for rank in range(8, 0, -1):
            empties = 0
            row_parts = []
            for file_char in self.FILES:
                square = f"{file_char}{rank}"
                code = pieces.get(square)
                if code is None:
                    empties += 1
                    continue
                if empties:
                    row_parts.append(str(empties))
                    empties = 0
                row_parts.append(self._piece_to_fen(code))
            if empties:
                row_parts.append(str(empties))
            rows.append("".join(row_parts))
        return "/".join(rows)

    def _reset_tracking(self, memory: dict[str, Any]) -> None:
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

    def _is_initial_position(self, pieces: dict[str, str], to_play: str) -> bool:
        return to_play == "white" and pieces == self.INITIAL_PIECES

    def _update_tracking(
        self,
        pieces: dict[str, str],
        to_play: str,
        memory: dict[str, Any],
    ) -> None:
        if not memory:
            self._reset_tracking(memory)
        tracked_side = memory.get("side")
        if tracked_side not in ("white", "black"):
            memory["side"] = to_play
        elif tracked_side != to_play:
            self._reset_tracking(memory)
            memory["side"] = to_play
        elif self._is_initial_position(pieces, to_play):
            self._reset_tracking(memory)
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

    def _tracked_castling_rights(self, pieces: dict[str, str], memory: dict[str, Any]) -> str:
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

    def _fen_from_state(self, pieces: dict[str, str], to_play: str, memory: dict[str, Any]) -> str:
        self._update_tracking(pieces, to_play, memory)
        board_fen = self._board_fen_from_pieces(pieces)
        turn = "w" if to_play == "white" else "b"
        castling = self._tracked_castling_rights(pieces, memory)
        fullmove_number = 1 + int(memory.get("turn_count", 0))
        return f"{board_fen} {turn} {castling} - 0 {fullmove_number}"

    def _query_stockfish(self, fen: str, move_time_ms: int) -> Optional[str]:
        with self._engine_lock:
            if not self._ensure_engine():
                return False
            assert self._engine is not None
            try:
                self._engine_write("ucinewgame")
                self._engine_write(f"position fen {fen}")
                self._engine_write(f"go movetime {move_time_ms}")
                response = self._engine_read_until(("bestmove ",))
                if response is None:
                    return None
                parts = response.split()
                if len(parts) < 2 or parts[1] == "(none)":
                    return None
                return parts[1]
            except Exception:
                self._engine_broken = True
                self._close_engine()
                return None

    def policy(
        self,
        pieces,
        to_play: Optional[str] = None,
        move_time_ms: int = DEFAULT_MOVE_TIME_MS,
        memory: Optional[dict[str, Any]] = None,
    ):
        using_wrapped_memory = memory is not None
        if memory is None:
            memory = self._direct_memory

        if to_play is None and isinstance(pieces, dict) and "pieces" in pieces:
            state = pieces
            pieces = state.get("pieces", {})
            to_play = state.get("to_play", "white")
        if to_play is None:
            to_play = "white"

        fen = self._fen_from_state(pieces, to_play, memory)
        bestmove = self._query_stockfish(fen, max(10, int(move_time_ms)))
        move = bestmove or ""
        if using_wrapped_memory:
            return move, memory
        return move
