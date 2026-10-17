
from __future__ import annotations

from typing import List, Tuple, Set
import math

Square = Tuple[int, int]
Move = Tuple[Square, Square]


def policy(my_men, my_kings, opp_men, opp_kings, color) -> Move:
    my_men = set(map(tuple, my_men))
    my_kings = set(map(tuple, my_kings))
    opp_men = set(map(tuple, opp_men))
    opp_kings = set(map(tuple, opp_kings))

    legal = generate_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not legal:
        # Should not happen in valid arena states, but return something deterministic.
        # This branch avoids crashing; if no legal move exists, any move is technically impossible.
        all_my = list(my_men | my_kings)
        if all_my:
            s = all_my[0]
            return (s, s)
        return ((0, 0), (0, 0))

    # Iterative deepening style fixed depths for safety.
    best_move = legal[0]
    try:
        best_move = search_best_move(my_men, my_kings, opp_men, opp_kings, color, legal)
    except Exception:
        # Absolute safety fallback: always return a legal move.
        best_move = legal[0]
    return best_move


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def forward_dirs(color: str):
    # Black moves downward to lower row values, White upward to higher row values.
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def all_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7


def generate_legal_moves(my_men: Set[Square], my_kings: Set[Square],
                         opp_men: Set[Square], opp_kings: Set[Square],
                         color: str) -> List[Move]:
    captures = generate_captures(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        return captures
    return generate_quiet_moves(my_men, my_kings, opp_men, opp_kings, color)


def generate_captures(my_men: Set[Square], my_kings: Set[Square],
                      opp_men: Set[Square], opp_kings: Set[Square],
                      color: str) -> List[Move]:
    occupied = my_men | my_kings | opp_men | opp_kings
    opp = opp_men | opp_kings
    moves = []

    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    for r, c in my_kings:
        for dr, dc in all_dirs():
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    return moves


def generate_quiet_moves(my_men: Set[Square], my_kings: Set[Square],
                         opp_men: Set[Square], opp_kings: Set[Square],
                         color: str) -> List[Move]:
    occupied = my_men | my_kings | opp_men | opp_kings
    moves = []

    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                moves.append(((r, c), (nr, nc)))

    for r, c in my_kings:
        for dr, dc in all_dirs():
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                moves.append(((r, c), (nr, nc)))

    return moves


def apply_move(my_men: Set[Square], my_kings: Set[Square],
               opp_men: Set[Square], opp_kings: Set[Square],
               color: str, move: Move):
    (fr, fc), (tr, tc) = move

    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)

    was_king = (fr, fc) in my_kings
    if was_king:
        my_kings.remove((fr, fc))
    else:
        my_men.remove((fr, fc))

    # Capture
    if abs(tr - fr) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        if (mr, mc) in opp_men:
            opp_men.remove((mr, mc))
        elif (mr, mc) in opp_kings:
            opp_kings.remove((mr, mc))

    # Promotion
    if was_king:
        my_kings.add((tr, tc))
    else:
        if tr == promotion_row(color):
            my_kings.add((tr, tc))
        else:
            my_men.add((tr, tc))

    return my_men, my_kings, opp_men, opp_kings


def opponent_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def search_best_move(my_men: Set[Square], my_kings: Set[Square],
                     opp_men: Set[Square], opp_kings: Set[Square],
                     color: str, legal: List[Move]) -> Move:
    # Depth chosen to balance strength and safety.
    piece_count = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if piece_count <= 6:
        depth = 8
    elif piece_count <= 10:
        depth = 7
    elif piece_count <= 16:
        depth = 6
    else:
        depth = 5

    ordered = order_moves(legal, my_men, my_kings, opp_men, opp_kings, color)

    best_score = -math.inf
    best_move = ordered[0]
    alpha, beta = -math.inf, math.inf

    for mv in ordered:
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, color, mv
        )
        score = -negamax(
            n_opp_men, n_opp_kings, n_my_men, n_my_kings,
            opponent_color(color), depth - 1, -beta, -alpha
        )
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    return best_move


def order_moves(moves: List[Move], my_men: Set[Square], my_kings: Set[Square],
                opp_men: Set[Square], opp_kings: Set[Square], color: str) -> List[Move]:
    promo_row = promotion_row(color)

    def score(mv: Move):
        (fr, fc), (tr, tc) = mv
        capture = 1 if abs(tr - fr) == 2 else 0
        mover_king = 1 if (fr, fc) in my_kings else 0
        promote = 1 if ((fr, fc) in my_men and tr == promo_row) else 0
        center = 1 if (2 <= tr <= 5 and 2 <= tc <= 5) else 0
        advance = (tr - fr) if color == 'w' else (fr - tr)
        return (
            100 * capture + 40 * promote + 10 * mover_king + 3 * center + advance
        )

    return sorted(moves, key=score, reverse=True)


def negamax(my_men: Set[Square], my_kings: Set[Square],
            opp_men: Set[Square], opp_kings: Set[Square],
            color: str, depth: int, alpha: float, beta: float) -> float:
    legal = generate_legal_moves(my_men, my_kings, opp_men, opp_kings, color)

    if not legal:
        return -100000.0 - depth

    if depth <= 0:
        return evaluate(my_men, my_kings, opp_men, opp_kings, color, legal)

    ordered = order_moves(legal, my_men, my_kings, opp_men, opp_kings, color)

    best = -math.inf
    opp_color = opponent_color(color)

    for mv in ordered:
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, color, mv
        )
        val = -negamax(
            n_opp_men, n_opp_kings, n_my_men, n_my_kings,
            opp_color, depth - 1, -beta, -alpha
        )
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def evaluate(my_men: Set[Square], my_kings: Set[Square],
             opp_men: Set[Square], opp_kings: Set[Square],
             color: str, legal_moves: List[Move] | None = None) -> float:
    # Material
    score = 0.0
    score += 100.0 * len(my_men)
    score += 175.0 * len(my_kings)
    score -= 100.0 * len(opp_men)
    score -= 175.0 * len(opp_kings)

    # Mobility
    if legal_moves is None:
        legal_moves = generate_legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    opp_moves = generate_legal_moves(opp_men, opp_kings, my_men, my_kings, opponent_color(color))
    score += 4.0 * len(legal_moves)
    score -= 4.0 * len(opp_moves)

    # Men advancement / promotion pressure
    if color == 'w':
        score += sum(6.0 + 1.5 * r for (r, c) in my_men)
        score -= sum(6.0 + 1.5 * (7 - r) for (r, c) in opp_men)
    else:
        score += sum(6.0 + 1.5 * (7 - r) for (r, c) in my_men)
        score -= sum(6.0 + 1.5 * r for (r, c) in opp_men)

    # Center control
    score += sum(5.0 for (r, c) in my_men | my_kings if 2 <= r <= 5 and 2 <= c <= 5)
    score -= sum(5.0 for (r, c) in opp_men | opp_kings if 2 <= r <= 5 and 2 <= c <= 5)

    # Edge safety: slight bonus for edge occupancy, especially men.
    score += sum(2.0 for (r, c) in my_men if c in (0, 7))
    score -= sum(2.0 for (r, c) in opp_men if c in (0, 7))
    score += sum(1.0 for (r, c) in my_kings if c in (0, 7))
    score -= sum(1.0 for (r, c) in opp_kings if c in (0, 7))

    # Back-rank guard
    home_row = 0 if color == 'w' else 7
    opp_home_row = 0 if color == 'b' else 7
    score += sum(3.0 for (r, c) in my_men if r == home_row)
    score -= sum(3.0 for (r, c) in opp_men if r == opp_home_row)

    return score
