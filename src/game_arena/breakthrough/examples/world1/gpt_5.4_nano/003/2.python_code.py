
from __future__ import annotations

from typing import List, Tuple, Optional
import math
import random

Board = List[List[str]]  # 'b','w','.'


def _build_board(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> Board:
    b = [['.' for _ in range(8)] for _ in range(8)]
    for r, c in me:
        b[r][c] = color
    oc = 'w' if color == 'b' else 'b'
    for r, c in opp:
        b[r][c] = oc
    return b


def _other(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def _forward_dir(color: str) -> int:
    # black moves down (to lower row values)
    # white moves up (to higher row values)
    return -1 if color == 'b' else 1


def _home_row_for(color: str) -> int:
    # win immediately if any piece reaches opponent's home row
    # black's goal is row 0, white's goal is row 7
    return 0 if color == 'b' else 7


def _generate_moves(board: Board, color: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    dirr = _forward_dir(color)
    opp = _other(color)
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != color:
                continue
            fr = r + dirr
            if 0 <= fr < 8:
                # forward
                if board[fr][c] == '.':
                    moves.append(((r, c), (fr, c)))
                # diagonals
                for dc in (-1, 1):
                    fc = c + dc
                    if 0 <= fc < 8 and board[fr][fc] == opp:
                        moves.append(((r, c), (fr, fc)))
                    # Note: moving diagonally only allowed if empty for non-capture in rules
                    if 0 <= fc < 8 and board[fr][fc] == '.':
                        moves.append(((r, c), (fr, fc)))
    # Remove illegal "diagonal if empty" duplication? It's already allowed and distinct.
    return moves


def _apply_move(board: Board, move: tuple[tuple[int, int], tuple[int, int]], color: str) -> Board:
    (r1, c1), (r2, c2) = move
    nb = [row[:] for row in board]
    opp = _other(color)
    nb[r1][c1] = '.'
    # capture if landing on opponent
    if nb[r2][c2] == opp:
        nb[r2][c2] = '.'
    nb[r2][c2] = color
    return nb


def _count_pieces(board: Board, color: str) -> int:
    cnt = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == color:
                cnt += 1
    return cnt


def _has_won(board: Board, color: str) -> bool:
    goal = _home_row_for(color)
    for c in range(8):
        if board[goal][c] == color:
            return True
    # also win if opponent eliminated
    return _count_pieces(board, _other(color)) == 0


def _is_square_attacked(board: Board, target_r: int, target_c: int, by_color: str) -> bool:
    # by_color attacks diagonally forward relative to by_color movement.
    dirr = _forward_dir(by_color)
    # attacker must be one row behind in movement direction
    src_r = target_r - dirr
    if 0 <= src_r < 8:
        for dc in (-1, 1):
            src_c = target_c + dc
            if 0 <= src_c < 8 and board[src_r][src_c] == by_color:
                return True
    return False


def _immediate_capture_opportunity(board: Board, my_color: str) -> bool:
    # after my move, if opponent has a capture on one of my pieces immediately.
    opp = _other(my_color)
    for r in range(8):
        for c in range(8):
            if board[r][c] != my_color:
                continue
            # if opponent can capture this piece in one move: opponent piece one step behind and diagonally forward landing on (r,c).
            # That means (r,c) is attacked by opponent.
            if _is_square_attacked(board, r, c, opp):
                return True
    return False


def _evaluate(board: Board, my_color: str) -> float:
    opp = _other(my_color)
    # terminal
    if _has_won(board, my_color):
        return 1e9
    if _has_won(board, opp):
        return -1e9

    my_count = _count_pieces(board, my_color)
    opp_count = _count_pieces(board, opp)

    # If opponent has fewer pieces, good.
    material = (my_count - opp_count) * 500.0

    # Advancement: closer to goal is better.
    goal = _home_row_for(my_color)
    adv = 0.0
    for r in range(8):
        for c in range(8):
            if board[r][c] == my_color:
                # distance moved toward goal
                # for black goal=0, smaller r is closer; for white goal=7, larger r closer
                dist = abs(goal - r)
                # convert to progress score (larger is better)
                progress = (7 - dist)
                adv += progress * 18.0

    # Threat / safety: penalize pieces that are immediately capturable by opponent.
    safety_pen = 0.0
    for r in range(8):
        for c in range(8):
            if board[r][c] == my_color:
                if _is_square_attacked(board, r, c, opp):
                    safety_pen += 120.0

    # Prefer moves that keep forward lanes open (slight).
    lane = 0.0
    dirr = _forward_dir(my_color)
    for r in range(8):
        for c in range(8):
            if board[r][c] == my_color:
                fr = r + dirr
                if 0 <= fr < 8 and board[fr][c] == '.':
                    lane += 6.0

    return material + adv - safety_pen + lane


def _minimax_best_move(board: Board, my_color: str, depth: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], float]:
    moves = _generate_moves(board, my_color)
    if not moves:
        # no legal moves => bad (but should be rare in Breakthrough)
        return (moves[0], -1e9) if moves else (None, -1e9)

    # Pre-filter: avoid moves that hang a piece when alternatives exist.
    safe_moves = []
    for mv in moves:
        nb = _apply_move(board, mv, my_color)
        # If opponent can immediately capture some of my pieces, it's risky.
        # We'll still allow if it gives a win or capture advantage.
        if _has_won(nb, my_color):
            safe_moves.append(mv)
        else:
            if not _immediate_capture_opportunity(nb, my_color):
                safe_moves.append(mv)

    candidate_moves = safe_moves if safe_moves else moves

    opp = _other(my_color)

    def search(bd: Board, turn_color: str, d: int, alpha: float, beta: float) -> float:
        # terminal or depth
        if d == 0 or _has_won(bd, my_color) or _has_won(bd, opp):
            return _evaluate(bd, my_color)

        cur_moves = _generate_moves(bd, turn_color)
        if not cur_moves:
            # no moves => evaluate
            return _evaluate(bd, my_color)

        if turn_color == my_color:
            val = -math.inf
            # Move ordering: prefer moves with immediate win, then captures (roughly via evaluation).
            ordered = []
            for mv in cur_moves:
                nb = _apply_move(bd, mv, turn_color)
                score = 0.0
                if _has_won(nb, my_color):
                    score += 1e7
                # prefer landing on opponent square (capture)
                (r1, c1), (r2, c2) = mv
                score += 2000.0 if bd[r2][c2] == opp else 0.0
                score += _evaluate(nb, my_color) * 0.001
                ordered.append((score, mv, nb))
            ordered.sort(key=lambda x: x[0], reverse=True)
            for _, mv, nb in ordered:
                val = max(val, search(nb, _other(turn_color), d - 1, alpha, beta))
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = math.inf
            ordered = []
            for mv in cur_moves:
                nb = _apply_move(bd, mv, turn_color)
                score = 0.0
                if _has_won(nb, my_color):
                    score -= 1e7
                (r1, c1), (r2, c2) = mv
                score += 2000.0 if bd[r2][c2] == my_color else 0.0
                score -= _evaluate(nb, my_color) * 0.001
                ordered.append((score, mv, nb))
            ordered.sort(key=lambda x: x[0], reverse=True)
            for _, mv, nb in ordered:
                val = min(val, search(nb, _other(turn_color), d - 1, alpha, beta))
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val

    best_move = None
    best_val = -math.inf
    # order candidate moves
    scored = []
    for mv in candidate_moves:
        nb = _apply_move(board, mv, my_color)
        # quick heuristic to order
        score = 0.0
        if _has_won(nb, my_color):
            score += 1e10
        (r1, c1), (r2, c2) = mv
        opp = _other(my_color)
        score += 5000.0 if board[r2][c2] == opp else 0.0
        # advancement preference
        goal = _home_row_for(my_color)
        score += (6 - abs(goal - r2)) * 200.0
        score += _evaluate(nb, my_color) * 0.001
        scored.append((score, mv, nb))
    scored.sort(key=lambda x: x[0], reverse=True)

    for _, mv, nb in scored:
        val = search(nb, opp, depth - 1, -math.inf, math.inf)
        if val > best_val + 1e-9:
            best_val = val
            best_move = mv

    # Ensure legality/non-None
    if best_move is None:
        best_move = candidate_moves[0]
        best_val = _evaluate(_apply_move(board, best_move, my_color), my_color)
    return best_move, best_val


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    board = _build_board(me, opp, color)

    # Immediate win check: any move that reaches goal wins right away.
    goal = _home_row_for(color)
    moves = _generate_moves(board, color)
    legal = moves
    for mv in legal:
        (r1, c1), (r2, c2) = mv
        if r2 == goal:
            return mv

    # Search depth: 2 ply (my move + opponent response) is usually enough; keep fast.
    # If fewer pieces, we can go one ply deeper.
    piece_count = len(me) + len(opp)
    depth = 3 if piece_count <= 10 else 2

    best_move, _ = _minimax_best_move(board, color, depth=depth)
    if best_move is None:
        # Fallback: pick the first legal move (must be legal).
        best_move = legal[0]
    return best_move
