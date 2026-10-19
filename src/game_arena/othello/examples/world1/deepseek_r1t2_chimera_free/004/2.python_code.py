
import numpy as np

# Static evaluation matrix assigning weights to each board position
WEIGHTS = np.array([
    [100, -30, 10, 5, 5, 10, -30, 100],
    [-30, -50, -2, -1, -1, -2, -50, -30],
    [10, -2, 3, 2, 2, 3, -2, 10],
    [5, -1, 2, 1, 1, 2, -1, 5],
    [5, -1, 2, 1, 1, 2, -1, 5],
    [10, -2, 3, 2, 2, 3, -2, 10],
    [-30, -50, -2, -1, -1, -2, -50, -30],
    [100, -30, 10, 5, 5, 10, -30, 100]
])

# Directions to check for flipping opponent discs
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),          (0, 1),
              (1, -1),  (1, 0), (1, 1)]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = []
    
    # Iterate through all board positions
    for r in range(8):
        for c in range(8):
            if you[r, c] == 0 and opponent[r, c] == 0:
                flipped = []
                # Check all 8 directions for possible flips
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    temp_flip = []
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        if opponent[nr, nc] == 1:
                            temp_flip.append((nr, nc))
                        elif you[nr, nc] == 1:
                            if temp_flip:
                                flipped.extend(temp_flip)
                            break
                        else:
                            break  # Empty square terminates direction
                        nr += dr
                        nc += dc
                if flipped:
                    legal_moves.append((r, c, flipped))
    
    if not legal_moves:
        return "pass"
    
    # Evaluate each move by position + flipped disc weights
    best_score = -np.inf
    best_move = None
    for r, c, flips in legal_moves:
        score = WEIGHTS[r, c]
        for (fr, fc) in flips:
            score += WEIGHTS[fr, fc]
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # Convert coordinates to algebraic notation (e.g., "d3")
    col_char = chr(ord('a') + best_move[1])
    row_num = best_move[0] + 1
    return f"{col_char}{row_num}"
