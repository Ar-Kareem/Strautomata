
import math

WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

POSITION_PREF = {
    (1, 1): 3,
    (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
    (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1,
}


def winner(b):
    for line in WIN_LINES:
        s = b[line[0][0]][line[0][1]] + b[line[1][0]][line[1][1]] + b[line[2][0]][line[2][1]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def empty_cells(b):
    return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]


def minimax(b, player, depth, alpha, beta, memo):
    key = (tuple(tuple(row) for row in b), player)
    if key in memo:
        return memo[key]
    w = winner(b)
    if w == 1:
        res = 10 - depth
        memo[key] = res
        return res
    if w == -1:
        res = depth - 10
        memo[key] = res
        return res
    cells = empty_cells(b)
    if not cells:
        memo[key] = 0
        return 0
    if player == 1:
        best = -math.inf
        for (r, c) in cells:
            b[r][c] = 1
            val = minimax(b, -1, depth + 1, alpha, beta, memo)
            b[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = math.inf
        for (r, c) in cells:
            b[r][c] = -1
            val = minimax(b, 1, depth + 1, alpha, beta, memo)
            b[r][c] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
    memo[key] = best
    return best


def trap_count(b, memo):
    # Number of opponent replies (from this position, opponent to move)
    # that lead to a forced win for us.
    count = 0
    for (r, c) in empty_cells(b):
        b[r][c] = -1
        val = minimax(b, 1, 1, -math.inf, math.inf, memo)
        b[r][c] = 0
        if val > 0:
            count += 1
    return count


def policy(board):
    try:
        b = [[int(board[r][c]) for c in range(3)] for r in range(3)]
        cells = empty_cells(b)
        if not cells:
            return (0, 0)
        if len(cells) == 9:
            return (1, 1)

        # Immediate win
        for (r, c) in cells:
            b[r][c] = 1
            if winner(b) == 1:
                b[r][c] = 0
                return (r, c)
            b[r][c] = 0

        memo = {}
        scored = []
        for (r, c) in cells:
            b[r][c] = 1
            val = minimax(b, -1, 1, -math.inf, math.inf, memo)
            b[r][c] = 0
            scored.append((val, (r, c)))

        best_val = max(v for v, _ in scored)
        candidates = [m for v, m in scored if v == best_val]
        if len(candidates) == 1:
            return candidates[0]

        best_move = None
        best_key = None
        for (r, c) in candidates:
            b[r][c] = 1
            traps = trap_count(b, memo)
            b[r][c] = 0
            key = (traps, POSITION_PREF.get((r, c), 0))
            if best_key is None or key > best_key:
                best_key = key
                best_move = (r, c)
        if best_move is not None and b[best_move[0]][best_move[1]] == 0:
            return best_move
        return candidates[0]
    except Exception:
        for r in range(3):
            for c in range(3):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
