
import random

LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def winner(board):
    for line in LINES:
        s = board[line[0][0]][line[0][1]] + board[line[1][0]][line[1][1]] + board[line[2][0]][line[2][1]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def empty_cells(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]


def minimax(board, player, alpha, beta, depth):
    w = winner(board)
    if w == 1:
        return 10 - depth
    if w == -1:
        return depth - 10
    cells = empty_cells(board)
    if not cells:
        return 0
    if player == 1:
        best = -100
        for (r, c) in cells:
            board[r][c] = 1
            val = minimax(board, -1, alpha, beta, depth + 1)
            board[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 100
        for (r, c) in cells:
            board[r][c] = -1
            val = minimax(board, 1, alpha, beta, depth + 1)
            board[r][c] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def opponent_blunder_potential(board, move):
    """Heuristic: after our move, count how many opponent replies lead to a forced loss for them."""
    r, c = move
    board[r][c] = 1
    count = 0
    cells = empty_cells(board)
    for (rr, cc) in cells:
        board[rr][cc] = -1
        val = minimax(board, 1, -100, 100, 0)
        board[rr][cc] = 0
        if val > 0:
            count += 1
    board[r][c] = 0
    return count


def positional_bonus(move):
    if move == (1, 1):
        return 2
    if move in [(0, 0), (0, 2), (2, 0), (2, 2)]:
        return 1
    return 0


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

        # Immediate block
        threats = []
        for (r, c) in cells:
            b[r][c] = -1
            if winner(b) == -1:
                threats.append((r, c))
            b[r][c] = 0
        if len(threats) == 1:
            return threats[0]

        # Full minimax evaluation of each move
        scored = []
        for (r, c) in cells:
            b[r][c] = 1
            val = minimax(b, -1, -100, 100, 1)
            b[r][c] = 0
            scored.append((val, (r, c)))
        best_val = max(v for v, _ in scored)
        candidates = [m for v, m in scored if v == best_val]

        if len(candidates) == 1:
            return candidates[0]

        # Tie-break: maximize opponent blunder chances, then positional preference
        best_move = None
        best_key = None
        for m in candidates:
            key = (opponent_blunder_potential(b, m), positional_bonus(m), random.random())
            if best_key is None or key > best_key:
                best_key = key
                best_move = m
        return best_move
    except Exception:
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
