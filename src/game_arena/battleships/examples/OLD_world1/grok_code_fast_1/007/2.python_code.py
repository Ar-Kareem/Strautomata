
import numpy as np

def policy(board):
    """
    A Battleship targeting policy.
    - Prioritize shooting adjacent to hits (target mode).
    - Fall back to checkerboard pattern for hunting.
    """
    b = np.array(board)
    rows, cols = b.shape
    
    # Target mode: collect cells adjacent to hits that are unknown (0)
    candidates = []
    for i in range(rows):
        for j in range(cols):
            if b[i, j] == 0:
                # Check orthogonal neighbors for hits
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols and b[ni, nj] == 1:
                        candidates.append((i, j))
                        break  # Only add once per cell
    
    if candidates:
        # Return the first candidate (top-leftmost)
        return candidates[0]
    
    # Hunt mode: checkerboard pattern (shoot where (i + j) % 2 == 0)
    for i in range(rows):
        for j in range(cols):
            if b[i, j] == 0 and (i + j) % 2 == 0:
                return (i, j)
    
    # Fallback: shoot any remaining unknown cell
    for i in range(rows):
        for j in range(cols):
            if b[i, j] == 0:
                return (i, j)
    
    # Should not reach here if grid is properly sized
    raise ValueError("No available shots.")
