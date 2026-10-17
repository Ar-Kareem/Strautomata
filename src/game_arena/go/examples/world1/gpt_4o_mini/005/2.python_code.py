
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board_size = 19
    board = np.zeros((board_size + 1, board_size + 1), dtype=int)  # Using 1-indexing
    
    # Marking my stones
    for r, c in me:
        board[r][c] = 1
    
    # Marking opponent's stones
    for r, c in opponent:
        board[r][c] = 2

    # Directions for adjacent checking (8 directions)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def is_within_bounds(r, c):
        return 1 <= r <= 19 and 1 <= c <= 19

    # Scoring moves
    best_score = -1
    best_move = (0, 0)

    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if board[row][col] == 0:  # Only consider empty spots
                score = 0
                for dr, dc in directions:
                    adj_row, adj_col = row + dr, col + dc
                    if is_within_bounds(adj_row, adj_col):
                        if board[adj_row][adj_col] == 1:
                            score += 1   # Friendly stones increase score
                        elif board[adj_row][adj_col] == 2:
                            # Potential capture opportunity
                            if is_within_bounds(adj_row + dr, adj_col + dc) and board[adj_row + dr][adj_col + dc] == 1:
                                score += 2  # Increase score for capturing a stone
                # Considering random boosts for future potential plays (could be refined)
                if score > best_score:
                    best_score = score
                    best_move = (row, col)

    return best_move
