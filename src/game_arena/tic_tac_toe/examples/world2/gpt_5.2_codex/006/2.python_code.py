
import time
from functools import lru_cache

# Precompute all 4-length winning lines on 4x4 board
LINES = []
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

# Heuristic weights
WEIGHTS = {0: 0, 1: 1, 2: 10, 3: 50, 4: 10000}

def check_winner(board):
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def heuristic(board):
    winner = check_winner(board)
    if winner == 1:
        return 100000
    if winner == -1:
        return -100000
    score = 0
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        if 1 in vals and -1 in vals:
            continue
        cnt1 = vals.count(1)
        cnt2 = vals.count(-1)
        if cnt1 > 0:
            score += WEIGHTS[cnt1]
        elif cnt2 > 0:
            score -= WEIGHTS[cnt2]
    return score

def board_to_tuple(board):
    return tuple(tuple(row) for row in board)

def policy(board):
    start_time = time.perf_counter()
    time_limit = 0.9  # seconds

    empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if not empty_cells:
        return (0, 0)  # should not happen

    # default move
    best_move = empty_cells[0]

    # Determine maximum depth based on empties
    max_depth = len(empty_cells)
    if max_depth > 8:
        max_depth = 6  # avoid explosion early game

    @lru_cache(maxsize=None)
    def minimax(board_t, player, depth, alpha, beta):
        # convert tuple to list for evaluation
        b = [list(row) for row in board_t]
        winner = check_winner(b)
        if winner == 1:
            return 100000
        if winner == -1:
            return -100000
        if depth == 0:
            return heuristic(b)

        moves = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
        if not moves:
            return heuristic(b)

        if player == 1:
            value = -float('inf')
            for r, c in moves:
                b[r][c] = 1
                val = minimax(board_to_tuple(b), -1, depth - 1, alpha, beta)
                b[r][c] = 0
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for r, c in moves:
                b[r][c] = -1
                val = minimax(board_to_tuple(b), 1, depth - 1, alpha, beta)
                b[r][c] = 0
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.perf_counter() - start_time > time_limit:
            break
        best_score = -float('inf')
        # move ordering: try winning or blocking lines first
        moves = empty_cells[:]
        # simple ordering by heuristic after move
        scored_moves = []
        for r, c in moves:
            board[r][c] = 1
            scored_moves.append((heuristic(board), (r, c)))
            board[r][c] = 0
        scored_moves.sort(reverse=True, key=lambda x: x[0])

        for _, (r, c) in scored_moves:
            if time.perf_counter() - start_time > time_limit:
                break
            board[r][c] = 1
            val = minimax(board_to_tuple(board), -1, depth - 1, -float('inf'), float('inf'))
            board[r][c] = 0
            if val > best_score:
                best_score = val
                best_move = (r, c)

    return best_move
