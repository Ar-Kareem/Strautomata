
import time
from math import inf

# All 4-in-a-row winning lines on a 4x4 board.
LINES = (
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((1, 0), (1, 1), (1, 2), (1, 3)),
    ((2, 0), (2, 1), (2, 2), (2, 3)),
    ((3, 0), (3, 1), (3, 2), (3, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((0, 2), (1, 2), (2, 2), (3, 2)),
    ((0, 3), (1, 3), (2, 3), (3, 3)),
    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 3), (1, 2), (2, 1), (3, 0)),
)

# Prefer central squares, then corners/edges.
PREFERRED = (
    (1, 1), (1, 2), (2, 1), (2, 2),
    (0, 0), (0, 3), (3, 0), (3, 3),
    (0, 1), (0, 2), (1, 0), (2, 0),
    (1, 3), (2, 3), (3, 1), (3, 2),
)

TIME_LIMIT = 0.85


class SearchTimeout(Exception):
    pass


def _winner(flat):
    for line in LINES:
        s = 0
        for r, c in line:
            s += flat[r * 4 + c]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _legal_moves(flat):
    return [(i // 4, i % 4) for i, v in enumerate(flat) if v == 0]


def _would_win(flat, move, player):
    idx = move[0] * 4 + move[1]
    if flat[idx] != 0:
        return False
    b = list(flat)
    b[idx] = player
    return _winner(tuple(b)) == player


def _heuristic(flat):
    """
    Positive is good for player 1, negative is good for player -1.
    """
    score = 0

    # Center control is valuable on 4x4 because centers participate in diagonals
    # and keep many line options flexible.
    center_weights = (
        2, 3, 3, 2,
        3, 5, 5, 3,
        3, 5, 5, 3,
        2, 3, 3, 2,
    )
    for i, v in enumerate(flat):
        score += v * center_weights[i]

    # Open-line evaluation.
    # A line with only our marks and empties is good.
    # A line with only opponent marks and empties is bad.
    line_value = [0, 4, 35, 450, 100000]
    own_threes = 0
    opp_threes = 0
    own_twos = 0
    opp_twos = 0

    for line in LINES:
        vals = [flat[r * 4 + c] for r, c in line]
        ones = vals.count(1)
        negs = vals.count(-1)

        if ones and negs:
            continue

        if negs == 0:
            score += line_value[ones]
            if ones == 3:
                own_threes += 1
            elif ones == 2:
                own_twos += 1

        if ones == 0:
            score -= line_value[negs]
            if negs == 3:
                opp_threes += 1
            elif negs == 2:
                opp_twos += 1

    # Fork pressure: multiple simultaneous threats are often decisive.
    score += 250 * max(0, own_threes - 1)
    score -= 300 * max(0, opp_threes - 1)
    score += 20 * max(0, own_twos - 1)
    score -= 25 * max(0, opp_twos - 1)

    return score


def _move_order(flat, moves, player):
    """
    Order moves to improve alpha-beta pruning.
    """
    ordered = []

    for move in moves:
        r, c = move
        idx = r * 4 + c
        b = list(flat)
        b[idx] = player
        t = tuple(b)

        if _winner(t) == player:
            priority = 10_000_000
        elif _would_win(flat, move, -player):
            # Also prioritize occupying squares where opponent would win.
            priority = 8_000_000
        else:
            h = _heuristic(t)
            priority = h if player == 1 else -h

        # Small static tie-breaker favoring central preferred moves.
        try:
            priority += 20 - PREFERRED.index(move)
        except ValueError:
            pass

        ordered.append((priority, move))

    ordered.sort(reverse=True)
    return [m for _, m in ordered]


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = time.time()

    flat = tuple(board[r][c] for r in range(4) for c in range(4))
    moves = _legal_moves(flat)

    # Absolute safety fallback.
    if not moves:
        return (0, 0)

    # Always have a legal move ready.
    fallback = None
    for m in PREFERRED:
        if flat[m[0] * 4 + m[1]] == 0:
            fallback = m
            break
    if fallback is None:
        fallback = moves[0]

    # 1. Win immediately if possible.
    for m in _move_order(flat, moves, 1):
        if _would_win(flat, m, 1):
            return m

    # 2. Block opponent's immediate win.
    opponent_wins = [m for m in moves if _would_win(flat, m, -1)]
    if opponent_wins:
        # If multiple blocks exist, pick the most positionally useful one.
        ordered_blocks = _move_order(flat, opponent_wins, 1)
        return ordered_blocks[0]

    trans = {}

    def check_time():
        if time.time() - start > TIME_LIMIT:
            raise SearchTimeout()

    def minimax(position, player, depth, alpha, beta):
        check_time()

        w = _winner(position)
        if w == 1:
            # Faster wins are slightly better.
            return 1_000_000 + depth
        if w == -1:
            # Slower losses are slightly better.
            return -1_000_000 - depth

        empty_count = position.count(0)
        if empty_count == 0:
            return 0

        if depth == 0:
            return _heuristic(position)

        key = (position, player, depth)
        if key in trans:
            return trans[key]

        legal = _legal_moves(position)
        legal = _move_order(position, legal, player)

        if player == 1:
            value = -inf
            for move in legal:
                idx = move[0] * 4 + move[1]
                new_pos = list(position)
                new_pos[idx] = 1
                value = max(value, minimax(tuple(new_pos), -1, depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = inf
            for move in legal:
                idx = move[0] * 4 + move[1]
                new_pos = list(position)
                new_pos[idx] = -1
                value = min(value, minimax(tuple(new_pos), 1, depth - 1, alpha, beta))
                beta = min(beta, value)
                if alpha >= beta:
                    break

        trans[key] = value
        return value

    best_move = fallback
    best_score = -inf
    empties = len(moves)

    # Search deeper as the board fills. Iterative deepening gives a good answer
    # even if the time limit is approached.
    if empties >= 14:
        max_depth = 5
    elif empties >= 11:
        max_depth = 7
    elif empties >= 8:
        max_depth = 10
    else:
        max_depth = empties

    try:
        for depth in range(1, max_depth + 1):
            check_time()
            current_best = best_move
            current_score = -inf

            ordered = _move_order(flat, moves, 1)

            for move in ordered:
                check_time()
                idx = move[0] * 4 + move[1]
                new_pos = list(flat)
                new_pos[idx] = 1
                score = minimax(tuple(new_pos), -1, depth - 1, -inf, inf)

                if score > current_score:
                    current_score = score
                    current_best = move

            # Only commit after the full depth completed.
            best_move = current_best
            best_score = current_score

            # No need to keep searching if a forced win is found.
            if best_score > 900_000:
                break

    except SearchTimeout:
        pass

    # Final legality guard.
    if 0 <= best_move[0] < 4 and 0 <= best_move[1] < 4:
        if flat[best_move[0] * 4 + best_move[1]] == 0:
            return best_move

    return fallback
