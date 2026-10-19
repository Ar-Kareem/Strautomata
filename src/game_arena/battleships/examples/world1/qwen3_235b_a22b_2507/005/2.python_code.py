
import random
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # First, collect all hit cells (value == 1) that have neighbors not yet fired at
    hit_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hit_cells.append((r, c))
    
    # Define possible directions
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # Try to extend from any hit cell
    for r, c in hit_cells:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                return (nr, nc)
    
    # If no hit has untargeted neighbors, perform sparse search using checkerboard pattern
    # But avoid already fired cells (-1 or 1)
    # Use step-2 pattern with offset based on total shots to sweep efficiently
    # We'll use a fixed order: prioritize cells on even-sum indices first (checkerboard), then odd
    # But skip any cell already fired at

    # First try even parity (r+c) % 2 == 0
    candidates = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if (r + c) % 2 == 0:
                    candidates.append((r, c))
    
    if candidates:
        # Randomly pick from even-parity unshot cells
        return random.choice(candidates)
    
    # If all even-parity are gone, pick from odd-parity
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if (r + c) % 2 == 1:
                    candidates.append((r, c))
    
    if candidates:
        return random.choice(candidates)
    
    # Fallback: should not happen unless board is full
    # But just in case, pick any unshot cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # If no cell is available (should not occur in valid game), return (0,0)
    return (0, 0)
