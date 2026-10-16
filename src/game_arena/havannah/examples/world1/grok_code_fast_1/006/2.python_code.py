
import numpy as np
import random

def policy(me, opp, valid_mask):
    N = len(valid_mask)
    board = np.full((N, N), -1, dtype=int)  # -1: empty, 0: player 0 (me), 1: player 1 (opp)
    for r, c in me:
        board[r, c] = 0
    for r, c in opp:
        board[r, c] = 1
    player = 0  # I am player 0

    # Collect valid moves: positions where mask is True and board is empty
    valid_moves = []
    for i in range(N):
        for j in range(N):
            if valid_mask[i][j] and board[i, j] == -1:
                valid_moves.append((i, j))

    if not valid_moves:
        # Shouldn't happen, but fallback to first if list is empty
        return (0, 0)

    # Define neighbor deltas for hexagonal grid
    deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]

    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                neighbors.append((nr, nc))
        return neighbors

    # Calculate score for each move: number of friendly neighbors
    scores = []
    for r, c in valid_moves:
        score = 0
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == player:
                score += 1
        scores.append(score)

    # Find maximum score
    max_score = max(scores) if scores else 0
    candidates = [move for move, s in zip(valid_moves, scores) if s == max_score]

    # Return a random candidate to break ties
    return random.choice(candidates)
