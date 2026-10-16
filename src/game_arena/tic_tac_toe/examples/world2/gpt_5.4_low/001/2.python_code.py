
from functools import lru_cache
import math

N = 4
WIN_SCORE = 10**9

# All winning lines on a 4x4 board: 4 rows, 4 cols, 2 diagonals
LINES = []

for r in range(N):
    LINES.append(tuple((r, c) for c in range(N)))
for c in range(N):
    LINES.append(tuple((r, c) for r in range(N)))
LINES.append(tuple((i, i) for i in range(N)))
LINES.append(tuple((i, N - 1 - i) for i in range(N)))

# Mild positional preference: central squares are slightly better
POS_WEIGHTS = [
    [2, 3, 3, 2],
    [3, 4, 4, 3],
    [3, 4, 4, 3],
    [2, 3, 3, 2],
]

LINE_WEIGHTS = [0, 2, 12, 80, 0]  # index by count; 4 handled as terminal


def board_to_tuple(board):
    return tuple(tuple(row) for row in board)


def winner(board_t):
    # Returns 1 if we win, -1 if opponent wins, 0 otherwise
    for line in LINES:
        s = sum(board_t[r][c] for r, c in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def legal_moves(board_t):
    moves = []
    for r in range(N):
        for c in range(N):
            if board_t[r][c] == 0:
                moves.append((r, c))
    return moves


def apply_move(board_t, move, player):
    r, c = move
    b = [list(row) for row in board_t]
    b[r][c] = player
    return tuple(tuple(row) for row in b)


def count_empty(board_t):
    return sum(1 for r in range(N) for c in range(N) if board_t[r][c] == 0)


def heuristic(board_t):
    w = winner(board_t)
    if w == 1:
        return WIN_SCORE
    if w == -1:
        return -WIN_SCORE

    score = 0

    # Line-based evaluation
    for line in LINES:
        vals = [board_t[r][c] for r, c in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)

        if my_count and opp_count:
            continue
        if my_count:
            score += LINE_WEIGHTS[my_count]
        elif opp_count:
            score -= LINE_WEIGHTS[opp_count]

    # Positional preference
    for r in range(N):
        for c in range(N):
            if board_t[r][c] == 1:
                score += POS_WEIGHTS[r][c]
            elif board_t[r][c] == -1:
                score -= POS_WEIGHTS[r][c]

    return score


def move_priority(board_t, move, player):
    # Higher is better for ordering
    r, c = move
    priority = POS_WEIGHTS[r][c]

    # Prefer immediate wins
    nb = apply_move(board_t, move, player)
    if winner(nb) == player:
        priority += 1000000

    # Prefer blocks of opponent immediate wins
    nb2 = apply_move(board_t, move, -player)
    if winner(nb2) == -player:
        priority += 500000

    # Prefer contributing to open lines
    for line in LINES:
        if (r, c) in line:
            vals = [board_t[rr][cc] for rr, cc in line]
            my_count = vals.count(player)
            opp_count = vals.count(-player)
            if opp_count == 0:
                priority += 20 * my_count
            if my_count == 0:
                priority += 8 * opp_count
    return priority


TT = {}


def negamax(board_t, depth, alpha, beta, player):
    key = (board_t, depth, player)
    if key in TT:
        return TT[key]

    w = winner(board_t)
    if w != 0:
        val = WIN_SCORE if w == player else -WIN_SCORE
        TT[key] = val
        return val

    empties = count_empty(board_t)
    if empties == 0:
        TT[key] = 0
        return 0

    if depth == 0:
        val = heuristic(board_t) * player
        TT[key] = val
        return val

    moves = legal_moves(board_t)
    moves.sort(key=lambda m: move_priority(board_t, m, player), reverse=True)

    best = -math.inf
    for mv in moves:
        nb = apply_move(board_t, mv, player)
        val = -negamax(nb, depth - 1, -beta, -alpha, -player)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


def choose_depth(empty_cells):
    # Adaptive depth to stay safe under time limits
    if empty_cells >= 13:
        return 5
    if empty_cells >= 10:
        return 6
    if empty_cells >= 7:
        return 7
    return 16  # effectively search to end in late game


def immediate_winning_moves(board_t, player):
    wins = []
    for mv in legal_moves(board_t):
        if winner(apply_move(board_t, mv, player)) == player:
            wins.append(mv)
    return wins


def fallback_legal(board):
    # Guaranteed legal fallback
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        board_t = board_to_tuple(board)
        moves = legal_moves(board_t)
        if not moves:
            return (0, 0)

        # 1) Immediate win
        my_wins = immediate_winning_moves(board_t, 1)
        if my_wins:
            my_wins.sort(key=lambda m: move_priority(board_t, m, 1), reverse=True)
            return my_wins[0]

        # 2) Immediate block
        opp_wins = immediate_winning_moves(board_t, -1)
        if opp_wins:
            # If multiple threats exist, choose the block with best follow-up value
            best_block = None
            best_score = -math.inf
            for mv in opp_wins:
                nb = apply_move(board_t, mv, 1)
                score = heuristic(nb)
                if score > best_score:
                    best_score = score
                    best_block = mv
            if best_block is not None:
                return best_block

        # 3) Search
        empty_cells = count_empty(board_t)
        depth = choose_depth(empty_cells)

        ordered = legal_moves(board_t)
        ordered.sort(key=lambda m: move_priority(board_t, m, 1), reverse=True)

        best_move = ordered[0]
        best_val = -math.inf
        alpha = -math.inf
        beta = math.inf

        for mv in ordered:
            nb = apply_move(board_t, mv, 1)
            val = -negamax(nb, depth - 1, -beta, -alpha, -1)
            if val > best_val:
                best_val = val
                best_move = mv
            if val > alpha:
                alpha = val

        # Final legality check
        r, c = best_move
        if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
            return best_move
        return fallback_legal(board)

    except Exception:
        return fallback_legal(board)
