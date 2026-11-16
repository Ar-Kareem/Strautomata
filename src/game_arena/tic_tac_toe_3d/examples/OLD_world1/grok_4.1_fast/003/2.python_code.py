
import itertools

def flat_index(x, y, z):
    return x * 9 + y * 3 + z

def get_winning_lines(n=3):
    lines = set()
    for dx, dy, dz in itertools.product([-1, 0, 1], repeat=3):
        if dx == 0 and dy == 0 and dz == 0:
            continue
        for sx, sy, sz in itertools.product(range(n), repeat=3):
            positions = []
            valid = True
            seen = set()
            for step in range(n):
                x = sx + step * dx
                y = sy + step * dy
                z = sz + step * dz
                if not (0 <= x < n and 0 <= y < n and 0 <= z < n):
                    valid = False
                    break
                pos = (x, y, z)
                if pos in seen:
                    valid = False
                    break
                seen.add(pos)
            if valid and len(seen) == n:
                lines.add(tuple(sorted(seen)))
    return [list(pos) for pos in lines]

winning_lines = get_winning_lines()
line_indices = [[flat_index(x, y, z) for x, y, z in line] for line in winning_lines]

memo = {}

def flatten(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

def winner(flat):
    for idxs in line_indices:
        v1 = flat[idxs[0]]
        v2 = flat[idxs[1]]
        v3 = flat[idxs[2]]
        if v1 != 0 and v1 == v2 == v3:
            return v1
    return 0

def get_player(flat):
    num1 = flat.count(1)
    numm1 = flat.count(-1)
    if num1 == numm1:
        return 1
    elif num1 == numm1 + 1:
        return -1
    return 0

def minimax(board, depth, alpha, beta):
    flat = flatten(board)
    if flat in memo:
        return memo[flat]
    player = get_player(flat)
    w = winner(flat)
    if w != 0:
        score = (30 - depth) if w == 1 else (depth - 30)
        memo[flat] = score
        return score
    if 0 not in flat:
        memo[flat] = 0
        return 0
    if player == 1:
        best = -10000
        for i, j, k in itertools.product(range(3), repeat=3):
            if board[i][j][k] == 0:
                board[i][j][k] = 1
                score = minimax(board, depth + 1, alpha, beta)
                board[i][j][k] = 0
                best = max(best, score)
                alpha = max(alpha, best)
                if alpha >= beta:
                    memo[flat] = best
                    return best
        memo[flat] = best
        return best
    else:
        best = 10000
        for i, j, k in itertools.product(range(3), repeat=3):
            if board[i][j][k] == 0:
                board[i][j][k] = -1
                score = minimax(board, depth + 1, alpha, beta)
                board[i][j][k] = 0
                best = min(best, score)
                beta = min(beta, best)
                if alpha >= beta:
                    memo[flat] = best
                    return best
        memo[flat] = best
        return best

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global memo
    memo.clear()
    best_score = -10001
    best_move = None
    for i, j, k in itertools.product(range(3), repeat=3):
        if board[i][j][k] != 0:
            continue
        board[i][j][k] = 1
        flat = flatten(board)
        if winner(flat) == 1:
            board[i][j][k] = 0
            return (i, j, k)
        val = minimax(board, 1, -10001, 10001)
        board[i][j][k] = 0
        if val > best_score:
            best_score = val
            best_move = (i, j, k)
    return best_move
