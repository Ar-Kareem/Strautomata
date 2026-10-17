
import time
from typing import List, Tuple

# Precompute all winning lines for 4x4 tic tac toe
LINES = []
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

TIME_LIMIT = 0.90  # seconds


def check_winner(board: List[List[int]]) -> int:
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def evaluate(board: List[List[int]]) -> int:
    w = check_winner(board)
    if w == 1:
        return 100000
    if w == -1:
        return -100000
    score = 0
    # Heuristic: open lines with counts
    for line in LINES:
        cnt1 = cnt2 = 0
        for r, c in line:
            if board[r][c] == 1:
                cnt1 += 1
            elif board[r][c] == -1:
                cnt2 += 1
        if cnt1 and cnt2:
            continue  # blocked line
        if cnt1:
            # stronger weight for more in line
            score += cnt1 * cnt1 * 10
        elif cnt2:
            score -= cnt2 * cnt2 * 10
    return score


def policy(board: List[List[int]]) -> Tuple[int, int]:
    start = time.time()
    empties = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    # If no moves, return arbitrary (shouldn't happen)
    if not empties:
        return (0, 0)

    # Immediate win
    for r, c in empties:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Immediate block
    for r, c in empties:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Transposition table
    cache = {}

    def flatten(b):
        return tuple(b[r][c] for r in range(4) for c in range(4))

    def negamax(depth, alpha, beta, player):
        # time check
        if time.time() - start > TIME_LIMIT:
            return evaluate(board)

        key = (flatten(board), player, depth)
        if key in cache:
            return cache[key]

        winner = check_winner(board)
        if winner != 0:
            val = winner * 100000
            cache[key] = val * player
            return cache[key]

        if depth == 0:
            val = evaluate(board) * player
            cache[key] = val
            return val

        best = -10**9
        # Move ordering: heuristic of resulting position
        moves = []
        for r, c in empties_list():
            board[r][c] = player
            h = evaluate(board) * player
            board[r][c] = 0
            moves.append(((r, c), h))
        moves.sort(key=lambda x: x[1], reverse=True)

        for (r, c), _ in moves:
            board[r][c] = player
            score = -negamax(depth - 1, -beta, -alpha, -player)
            board[r][c] = 0
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        cache[key] = best
        return best

    def empties_list():
        return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    best_move = empties[0]
    max_depth = len(empties)

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.time() - start > TIME_LIMIT:
            break
        best_score = -10**9
        moves = empties_list()
        # simple ordering: center first
        moves.sort(key=lambda x: (abs(x[0] - 1.5) + abs(x[1] - 1.5)))
        for r, c in moves:
            if time.time() - start > TIME_LIMIT:
                break
            board[r][c] = 1
            score = -negamax(depth - 1, -10**9, 10**9, -1)
            board[r][c] = 0
            if score > best_score:
                best_score = score
                best_move = (r, c)

    # Ensure legal
    if board[best_move[0]][best_move[1]] == 0:
        return best_move
    # Fallback
    return empties[0]
