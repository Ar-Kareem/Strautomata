
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier handling (5x6)
    you = np.array(you).reshape(5, 6)
    opponent = np.array(opponent).reshape(5, 6)
    
    # Precompute opponent degree (number of adjacent opponent pieces) for all opponent positions
    opp_degree = np.zeros((5, 6), dtype=int)
    # Directions: up, right, down, left
    dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    # For each cell that is occupied by opponent, count adjacent opponent pieces
    for r in range(5):
        for c in range(6):
            if opponent[r, c] == 1:
                count = 0
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr, nc] == 1:
                        count += 1
                opp_degree[r, c] = count
    
    best_move = None
    best_degree = -1  # Will hold the max opponent degree we capture
    best_row, best_col = 10, 10  # Initialize to invalid, for tie-breaking
    
    # Iterate over your pieces in row-major order (0,0) to (4,5)
    for r in range(5):
        for c in range(6):
            if you[r, c] == 1:
                # Check all four directions for opponent pieces
                for idx, (dr, dc) in enumerate(dirs):
                    nr, nc = r + dr, c + dc
                    # Check bounds and opponent piece
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr, nc] == 1:
                        degree = opp_degree[nr, nc]
                        # Check if this move is better than the current best
                        # If degree is higher, it's better
                        # If equal, prefer smaller row then smaller col (row-major first)
                        if (degree > best_degree or 
                            (degree == best_degree and (r < best_row or (r == best_row and c < best_col)))):
                            best_degree = degree
                            best_row, best_col = r, c
                            # Map direction index to letter
                            direction_char = ['U', 'R', 'D', 'L'][idx]
                            best_move = f"{r},{c},{direction_char}"
    
    # Since we're guaranteed at least one legal move, best_move must be set
    return best_move
