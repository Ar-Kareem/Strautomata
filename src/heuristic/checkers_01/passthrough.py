from pathlib import Path
import sys
import time
from typing import Iterable, Optional

import numpy as np


DRAUGHTS_ROOT = Path(__file__).resolve().parent / "py-draughts"
sys.path.append(str(DRAUGHTS_ROOT))

from draughts.boards.american import Board as AmericanBoard  # noqa: E402
from draughts.engines.alpha_beta import (  # noqa: E402
    AlphaBetaEngine,
    CHECKMATE,
    IID_DEPTH,
    INF,
    QS_MAX_DEPTH,
    TT_MAX_SIZE,
)
from draughts.models import Color  # noqa: E402
from draughts.move import Move as DraughtsMove  # noqa: E402


SQUARE_NAME_TO_INDEX = {name: idx for idx, name in enumerate(AmericanBoard.SQUARE_NAMES)}
INDEX_TO_SQUARE_NAME = AmericanBoard.SQUARE_NAMES
PENDING_CONTINUATION_SRC_IDX: Optional[int] = None
PENDING_CONTINUATION_BOARD_KEY: Optional[tuple[int, ...]] = None
PENDING_CONTINUATION_PLAN: Optional[list[int]] = None  # remaining square path of a multi-jump chosen by the search
MOVE_TIME_LIMIT_SECONDS = 0.8
ENGINE_DEPTH_LIMIT = 64
TIME_CHECK_INTERVAL_NODES = 128


class _HardTimedAlphaBetaEngine(AlphaBetaEngine):
    def __init__(self, depth_limit: int = ENGINE_DEPTH_LIMIT, time_limit: float | None = MOVE_TIME_LIMIT_SECONDS):
        super().__init__(depth_limit=depth_limit, time_limit=time_limit)
        self._deadline: float = 0.0
        self.fallback_move = None

    def _check_deadline(self, force: bool = False) -> None:
        if self._deadline and (force or self.nodes % TIME_CHECK_INTERVAL_NODES == 0):
            if time.perf_counter() >= self._deadline:
                raise TimeoutError

    def get_best_move(self, board, with_evaluation: bool = False):
        self.start_time = time.perf_counter()
        self._deadline = self.start_time + (self.time_limit or MOVE_TIME_LIMIT_SECONDS)
        self.nodes = 0
        self.stop_search = False

        num_squares = len(board._pos)
        self._current_zobrist = self._get_zobrist_table(num_squares)
        rows = 10 if num_squares == 50 else (8 if num_squares == 32 else int(np.sqrt(num_squares * 2)))
        self._current_pst = self._get_pst_tables(num_squares, rows)

        for key in self.history:
            self.history[key] //= 2

        current_hash = self._compute_hash_fast(board)
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available")

        best_move = self.fallback_move
        best_score = -INF
        max_depth = self.depth_limit or 6

        for depth in range(1, max_depth + 1):
            try:
                self._check_deadline(force=True)
                score = self.negamax(board, depth, -INF, INF, current_hash)
                entry = self.tt.get(current_hash)
                if entry and entry[3] is not None:
                    best_move = entry[3]
                    best_score = score
            except TimeoutError:
                break

        if len(self.tt) > TT_MAX_SIZE:
            keys_to_remove = list(self.tt.keys())[:len(self.tt) - TT_MAX_SIZE // 2]
            for key in keys_to_remove:
                del self.tt[key]

        if best_move is None:
            best_move = legal_moves[0]
            best_score = -INF

        if with_evaluation:
            return best_move, float(best_score)
        return best_move

    def negamax(self, board, depth: int, alpha: float, beta: float, h: int) -> float:
        self.nodes += 1
        self._check_deadline()

        tt_entry = self.tt.get(h)
        if tt_entry:
            tt_depth, tt_flag, tt_score, _tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                if tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        if depth <= 0:
            return self.quiescence_search(board, alpha, beta, h)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return -CHECKMATE + ((self.depth_limit or 6) - depth)

        if board.is_draw:
            return 0.0

        if depth >= IID_DEPTH and (not tt_entry or tt_entry[3] is None):
            self.negamax(board, depth - 2, alpha, beta, h)

        legal_moves = self._order_moves(legal_moves, board, h, depth)

        best_value = -INF
        best_move = None
        tt_flag = 1

        for i, move in enumerate(legal_moves):
            self._check_deadline()
            new_hash = self._update_hash(h, board, move)
            board.push(move)

            if i == 0:
                val = -self.negamax(board, depth - 1, -beta, -alpha, new_hash)
            else:
                reduction = 0
                if depth >= 3 and i >= 3 and not move.captured_list:
                    reduction = 1
                val = -self.negamax(board, depth - 1 - reduction, -alpha - 1, -alpha, new_hash)
                if val > alpha and (reduction > 0 or val < beta):
                    val = -self.negamax(board, depth - 1, -beta, -alpha, new_hash)

            board.pop()

            if val > best_value:
                best_value = val
                best_move = move

            alpha = max(alpha, val)
            if alpha >= beta:
                tt_flag = 2
                if not move.captured_list:
                    self._update_killers(move, depth)
                self._update_history(move, depth)
                break

        self.tt[h] = (depth, tt_flag, best_value, best_move)
        return best_value

    def quiescence_search(self, board, alpha: float, beta: float, h: int, qs_depth: int = 0) -> float:
        self.nodes += 1
        self._check_deadline()

        stand_pat = self.evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        if qs_depth >= QS_MAX_DEPTH:
            return stand_pat

        captures = [move for move in board.legal_moves if move.captured_list]
        if not captures:
            return stand_pat

        captures = self._order_captures(captures, board)
        for move in captures:
            self._check_deadline()
            new_hash = self._update_hash(h, board, move)
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha, new_hash, qs_depth + 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

def _coord_to_name(row: int, col: int) -> str:
    return f"{chr(ord('a') + col)}{row + 1}"


def _name_to_coord(name: str) -> tuple[int, int]:
    col = ord(name[0]) - ord('a')
    row = int(name[1:]) - 1
    return row, col


def _coords_to_index(row: int, col: int) -> int:
    name = _coord_to_name(row, col)
    if name not in SQUARE_NAME_TO_INDEX:
        raise ValueError(f"Invalid dark-square coordinate: {(row, col)} -> {name}. SQUARE_NAME_TO_INDEX={SQUARE_NAME_TO_INDEX}")
    return SQUARE_NAME_TO_INDEX[name]


def _move_to_action(move) -> tuple[tuple[tuple[int, int], tuple[int, int]], str]:
    if len(move.square_list) < 2:
        raise ValueError(f"Unexpected move.square_list: {move.square_list}")
    src_name = INDEX_TO_SQUARE_NAME[move.square_list[0]]
    dst_name = INDEX_TO_SQUARE_NAME[move.square_list[1]]
    src_coord = _name_to_coord(src_name)
    dst_coord = _name_to_coord(dst_name)
    action_str = f"{src_name}{dst_name}"
    return (src_coord, dst_coord), action_str


def _build_position(
    my_men: Iterable[tuple[int, int]],
    my_kings: Iterable[tuple[int, int]],
    opp_men: Iterable[tuple[int, int]],
    opp_kings: Iterable[tuple[int, int]],
    color: str,
) -> AmericanBoard:
    arr = np.zeros(32, dtype=np.int8)

    if color == "w":
        my_man_val, my_king_val = -1, -2
        opp_man_val, opp_king_val = 1, 2
        turn = Color.WHITE
    else:
        my_man_val, my_king_val = 1, 2
        opp_man_val, opp_king_val = -1, -2
        turn = Color.BLACK

    for row, col in my_men:
        arr[_coords_to_index(row, col)] = my_man_val
    for row, col in my_kings:
        arr[_coords_to_index(row, col)] = my_king_val
    for row, col in opp_men:
        arr[_coords_to_index(row, col)] = opp_man_val
    for row, col in opp_kings:
        arr[_coords_to_index(row, col)] = opp_king_val

    return AmericanBoard(starting_position=arr, turn=turn)


def _prime_engine_for_board(engine: AlphaBetaEngine, board: AmericanBoard) -> None:
    num_squares = len(board._pos)
    engine._current_zobrist = engine._get_zobrist_table(num_squares)
    rows = 10 if num_squares == 50 else (8 if num_squares == 32 else int(np.sqrt(num_squares * 2)))
    engine._current_pst = engine._get_pst_tables(num_squares, rows)


def _select_best_static_move(
    board: AmericanBoard,
    engine: AlphaBetaEngine,
    candidates: Optional[list[object]] = None,
) -> object:
    legal_moves = candidates if candidates is not None else list(board.legal_moves)
    if not legal_moves:
        raise RuntimeError("Draughts engine returned no legal moves.")

    _prime_engine_for_board(engine, board)
    best_move = legal_moves[0]
    best_score = None
    for move in legal_moves:
        board.push(move)
        score = engine.evaluate(board)
        board.pop()
        score = -score
        if best_score is None or score > best_score:
            best_score = score
            best_move = move
    return best_move


def _select_best_move(board: AmericanBoard, engine: AlphaBetaEngine) -> object:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        raise RuntimeError("Draughts engine returned no move.")
    if len(legal_moves) == 1:
        return legal_moves[0]

    fallback_move = _select_best_static_move(board, engine, legal_moves)
    if isinstance(engine, _HardTimedAlphaBetaEngine):
        engine.fallback_move = fallback_move

    # Search on a copy: a hard timeout aborts negamax mid-push, which would leave moves applied to `board`.
    search_board = AmericanBoard(starting_position=board._pos.copy(), turn=board.turn)
    move = engine.get_best_move(search_board)
    if move is None:
        return fallback_move
    return move


def _select_best_capture_or_move(
    board: AmericanBoard,
    engine: AlphaBetaEngine,
    forced_src_idx: Optional[int] = None,
) -> object:
    legal_moves = list(board.legal_moves)
    if len(legal_moves) == 1:
        return legal_moves[0]
    if forced_src_idx is not None:
        forced_moves = [m for m in legal_moves if m.square_list and m.square_list[0] == forced_src_idx]
        if forced_moves:
            legal_moves = forced_moves

    if forced_src_idx is None:
        # board.legal_moves already enforces mandatory captures (and lists multi-jumps as full paths),
        # so capture choices go through the same search as quiet moves.
        return _select_best_move(board, engine)
    if not legal_moves:
        raise RuntimeError("Draughts engine returned no legal moves.")

    # Mid multi-jump: keep following the path the search planned on the first hop.
    if PENDING_CONTINUATION_PLAN:
        planned = [m for m in legal_moves if list(m.square_list) == PENDING_CONTINUATION_PLAN]
        if planned:
            return planned[0]

    captures = [m for m in legal_moves if m.captured_list]
    candidates = captures if captures else legal_moves
    return _select_best_static_move(board, engine, candidates)


def _select_best_legal_move(
    board: AmericanBoard,
    engine: AlphaBetaEngine,
    legal_action_set: set[str],
) -> object:
    _prime_engine_for_board(engine, board)

    candidates = []
    american_legal_moves = []
    for move in board.legal_moves:
        _, action_str = _move_to_action(move)
        american_legal_moves.append(action_str)
        if action_str in legal_action_set:
            candidates.append(move)

    if not candidates:
        raise RuntimeError("No intersection between engine moves and legal moves. board.legal_moves=" + str(american_legal_moves) + " legal_action_set=" + str(legal_action_set))

    captures = [m for m in candidates if m.captured_list]
    if captures:
        candidates = captures

    move_scores = []
    best_move = candidates[0]
    best_score = None
    for move in candidates:
        board.push(move)
        score = engine.evaluate(board)
        board.pop()
        score = -score
        move_scores.append((_move_to_action(move)[1], score.round(3).item()))
        if best_score is None or score > best_score:
            best_score = score
            best_move = move
    print('evaluation scores', sorted(move_scores, key=lambda x: x[1], reverse=True))
    return best_move


def _board_key(board: AmericanBoard) -> tuple[int, ...]:
    return tuple(int(v) for v in board._pos)


def _to_first_hop_move(board: AmericanBoard, move: object) -> DraughtsMove:
    src_idx = move.square_list[0]
    dst_idx = move.square_list[1]
    src_row, src_col = _name_to_coord(INDEX_TO_SQUARE_NAME[src_idx])
    dst_row, dst_col = _name_to_coord(INDEX_TO_SQUARE_NAME[dst_idx])
    if abs(src_row - dst_row) != 2:
        return DraughtsMove([src_idx, dst_idx])
    mid_row = (src_row + dst_row) // 2
    mid_col = (src_col + dst_col) // 2
    mid_idx = _coords_to_index(mid_row, mid_col)
    captured_piece = int(board._get(mid_idx))
    if captured_piece == 0:
        return DraughtsMove([src_idx, dst_idx])
    return DraughtsMove([src_idx, dst_idx], [mid_idx], [captured_piece])


def _set_pending_continuation(src_idx: Optional[int], board_key: Optional[tuple[int, ...]], plan: Optional[list[int]] = None) -> None:
    global PENDING_CONTINUATION_SRC_IDX
    global PENDING_CONTINUATION_BOARD_KEY
    global PENDING_CONTINUATION_PLAN
    PENDING_CONTINUATION_SRC_IDX = src_idx
    PENDING_CONTINUATION_BOARD_KEY = board_key
    PENDING_CONTINUATION_PLAN = plan


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global PENDING_CONTINUATION_SRC_IDX
    global PENDING_CONTINUATION_BOARD_KEY

    board = _build_position(my_men, my_kings, opp_men, opp_kings, color)
    current_key = _board_key(board)
    engine = _HardTimedAlphaBetaEngine(depth_limit=ENGINE_DEPTH_LIMIT, time_limit=MOVE_TIME_LIMIT_SECONDS)
    forced_src_idx = None
    if PENDING_CONTINUATION_SRC_IDX is not None and PENDING_CONTINUATION_BOARD_KEY == current_key:
        forced_src_idx = PENDING_CONTINUATION_SRC_IDX
    else:
        _set_pending_continuation(None, None)

    move = _select_best_capture_or_move(board, engine, forced_src_idx=forced_src_idx)
    first_hop_move = _to_first_hop_move(board, move)

    # Save forced continuation only when this capture creates another capture from the same piece.
    if first_hop_move.captured_list:
        mover_turn = board.turn
        dst_idx = first_hop_move.square_list[-1]
        board.push(first_hop_move)
        saved_turn = board.turn
        board.turn = mover_turn
        has_continuation = any(
            m.captured_list and m.square_list and m.square_list[0] == dst_idx
            for m in board.legal_moves
        )
        board.turn = saved_turn
        if has_continuation:
            plan = list(move.square_list[1:]) if len(move.square_list) > 2 else None
            _set_pending_continuation(dst_idx, _board_key(board), plan)
        else:
            _set_pending_continuation(None, None)
        board.pop()
    else:
        _set_pending_continuation(None, None)

    move_tuple, _ = _move_to_action(first_hop_move)
    return move_tuple
