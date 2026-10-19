
import numpy as np

# Static weight matrix for positional evaluation
# Corners have high weight (100), c-squares have negative weight (-20), x-squares have very negative weight (-50)
WEIGHT_MATRIX = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10,  -2,  1,  2,  2,  1,  -2,  10],
    [5,   -2,  2,  0,  0,  2,  -2,   5],
    [5,   -2,  2,  0,  0,  2,  -2,   5],
    [10,  -2,  1,  2,  2,  1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
])

def get_flips(board, r, c, player=1):
    """Calculate the list of discs that would be flipped if a move is made at (r, c) by player."""
    flips = []
    directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
    for dr, dc in directions:
        i, j = r+dr, c+dc
        temp_flips = []
        while 0 <= i < 8 and 0 <= j < 8:
            if board[i][j] == -player:  # opponent disc
                temp_flips.append((i, j))
                i += dr
                j += dc
            elif board[i][j] == 0:  # empty cell, stop without flipping
                break
            else:  # our own disc
                if temp_flips:
                    flips.extend(temp_flips)
                break
    return flips

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the next move in algebraic notation (e.g., 'd3') or 'pass' if no moves are available."""
    # Combine the boards into a single array where 1 represents our disc, -1 for opponent, 0 for empty
    board = np.zeros((8, 8), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = -1
    
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 0:  # empty cell
                flips = get_flips(board, r, c, player=1)
                if flips:  # if there are flips, the move is legal
                    # Calculate score as the weight of the new disc plus the weights of flipped discs
                    score = WEIGHT_MATRIX[r][c] + sum(WEIGHT_MATRIX[i][j] for i, j in flips)
                    legal_moves.append((r, c, score))
    
    if not legal_moves:
        return "pass"
    
    # Find the move with the highest score
    best_move = max(legal_moves, key=lambda x: x[2])
    r, c, _ = best_move
    # Convert to algebraic notation: column 0->a, row 0->1
    file = chr(ord('a') + c)
    rank = str(r + 1)
    return file + rank
