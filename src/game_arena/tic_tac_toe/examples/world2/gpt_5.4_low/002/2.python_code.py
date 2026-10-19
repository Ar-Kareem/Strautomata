
from typing import List, Tuple
import math

# Precomputed winning lines for 4x4 Tic Tac Toe
LINES = []

# Rows
for r in range(4):
    LINES.append([(r, c) for c in range(4)])

# Columns
for c in range(4):
    LINES.append([(r, c) for r in range(4)])

# Diagonals
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

# Positional preference: central-ish squares are slightly better
POS_WEIGHTS = [
    [3, 4, 4, 3],
    [4, 5, 5, 4],
    [4, 5, 5, 4],
    [3, 4, 4, 3],
]

INF = 10**9


def _winner(board: List[List[int]]) -> int:
    for line in LINES:
        s = 0
        vals = []
        for r, c in line:
            v = board[r][c]
            vals.append(v)
            s += v
        if s == 4 and all(v == 1 for v in vals):
            return 1
        if s == -4 and all(v == -1 for v in vals):
            return -1
    return 0


def _legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]


def _heuristic(board: List[List[int]]) -> int:
    w = _winner(board)
    if w == 1:
        return 1000000
    if w == -1:
        return -1000000

    score = 0

    # Line-based scoring
    # Only uncontested lines matter.
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        cnt_me = vals.count(1)
        cnt_opp = vals.count(-1)
        cnt_empty = vals.count(0)

        if cnt_me > 0 and cnt_opp > 0:
            continue

        if cnt_opp == 0 and cnt_me > 0:
            if cnt_me == 1:
                score += 8
            elif cnt_me == 2:
                score += 40
            elif cnt_me == 3:
                score += 300
        elif cnt_me == 0 and cnt_opp > 0:
            if cnt_opp == 1:
                score -= 8
            elif cnt_opp == 2:
                score -= 45
            elif cnt_opp == 3:
                score -= 350

        # Slight preference for more empties in promising lines
        if cnt_opp == 0 and cnt_me > 0:
            score += cnt_empty
        elif cnt_me == 0 and cnt_opp > 0:
            score -= cnt_empty

    # Positional weights
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1:
                score += POS_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= POS_WEIGHTS[r][c]

    return score


def _ordered_moves(board: List[List[int]], player: int) -> List[Tuple[int, int]]:
    moves = _legal_moves(board)

    scored = []
    for r, c in moves:
        board[r][c] = player

        # Tactical priority
        if _winner(board) == player:
            priority = 10**8
        else:
            # Also prioritize blocks / strong heuristic moves
            priority = 0
            # Count how many lines involving this square are promising
            for line in LINES:
                if (r, c) in line:
                    vals = [board[rr][cc] for rr, cc in line]
                    cnt_p = vals.count(player)
                    cnt_o = vals.count(-player)
                    if cnt_o == 0:
                        priority += [0, 2, 10, 50, 0][cnt_p]
                    if cnt_p == 0:
                        priority += [0, 1, 3, 8, 0][cnt_o]
            priority += POS_WEIGHTS[r][c]

        board[r][c] = 0
        scored.append((priority, (r, c)))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _board_key(board: List[List[int]], player: int) -> Tuple[int, ...]:
    flat = []
    for row in board:
        flat.extend(row)
    flat.append(player)
    return tuple(flat)


def _negamax(board: List[List[int]], depth: int, alpha: int, beta: int, player: int, memo) -> int:
    key = (_board_key(board, player), depth, alpha, beta)
    if key in memo:
        return memo[key]

    w = _winner(board)
    if w != 0:
        val = w * player * 1000000
        memo[key] = val
        return val

    moves = _legal_moves(board)
    if not moves:
        memo[key] = 0
        return 0

    if depth == 0:
        val = _heuristic(board) * player
        memo[key] = val
        return val

    best = -INF
    for r, c in _ordered_moves(board, player):
        board[r][c] = player
        val = -_negamax(board, depth - 1, -beta, -alpha, -player, memo)
        board[r][c] = 0

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    memo[key] = best
    return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    moves = _legal_moves(board)
    if not moves:
        return (0, 0)  # Should not happen in a valid game, but keeps API total.

    # 1. Immediate winning move
    for r, c in moves:
        board[r][c] = 1
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2. Immediate block of opponent winning move
    opp_wins = []
    for r, c in moves:
        board[r][c] = -1
        if _winner(board) == -1:
            opp_wins.append((r, c))
        board[r][c] = 0
    if opp_wins:
        # If multiple blocks exist, choose the best-looking one
        opp_wins.sort(key=lambda mv: POS_WEIGHTS[mv[0]][mv[1]], reverse=True)
        return opp_wins[0]

    empties = len(moves)

    # Adaptive depth
    if empties <= 6:
        depth = empties  # full solve
    elif empties <= 8:
        depth = 7
    elif empties <= 10:
        depth = 6
    else:
        depth = 4

    best_move = None
    best_score = -INF
    alpha = -INF
    beta = INF
    memo = {}

    for r, c in _ordered_moves(board, 1):
        board[r][c] = 1
        score = -_negamax(board, depth - 1, -beta, -alpha, -1, memo)
        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = (r, c)
        if score > alpha:
            alpha = score

    if best_move is not None and board[best_move[0]][best_move[1]] == 0:
        return best_move

    # Final safety fallback: always return a legal move
    ordered = _ordered_moves(board, 1)
    for mv in ordered:
        if board[mv[0]][mv[1]] == 0:
            return mv

    return moves[0]
