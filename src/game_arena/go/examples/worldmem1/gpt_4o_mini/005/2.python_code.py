
import numpy as np

def is_legal_move(board, move):
    row, col = move
    return 1 <= row <= 19 and 1 <= col <= 19 and board[row, col] == 0

def get_neighbors(row, col):
    return [(row + dr, col + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr != 0 or dc != 0)]

def evaluate_move(board, move, me, opponent):
    row, col = move
    score = 0
    if not is_legal_move(board, move):
        return -float('inf')

    neighbors = get_neighbors(row, col)
    for n_row, n_col in neighbors:
        if 1 <= n_row <= 19 and 1 <= n_col <= 19:
            if board[n_row, n_col] == 1:  # friendly stone
                score += 1
            elif board[n_row, n_col] == -1:  # opponent's stone
                score -= 1  # risky move
    return score

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = np.zeros((20, 20), dtype=int)  # 19x19 board +1 for easier indexing
    for r, c in me:
        board[r, c] = 1  # My stones
    for r, c in opponent:
        board[r, c] = -1  # Opponent's stones

    best_move = (0, 0)
    best_score = -float('inf')

    for r in range(1, 20):
        for c in range(1, 20):
            move = (r, c)
            score = evaluate_move(board, move, me, opponent)
            if score > best_score:
                best_score = score
                best_move = move

    return best_move, memory
