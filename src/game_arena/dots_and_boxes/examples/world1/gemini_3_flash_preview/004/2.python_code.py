
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Helper to count sides for a box at (r, c)
    def count_sides(r, c):
        sides = 0
        if horizontal[r, c] != 0: sides += 1
        if horizontal[r + 1, c] != 0: sides += 1
        if vertical[r, c] != 0: sides += 1
        if vertical[r, c + 1] != 0: sides += 1
        return sides

    # 1. Look for winning moves (completes a box)
    for r in range(4):
        for c in range(4):
            sides = count_sides(r, c)
            if sides == 3:
                # Find the missing side
                if horizontal[r, c] == 0: return f"{r},{c},H"
                if horizontal[r + 1, c] == 0: return f"{r+1},{c},H"
                if vertical[r, c] == 0: return f"{r},{c},V"
                if vertical[r, c + 1] == 0: return f"{r},{c+1},V"

    # 2. Look for safe moves (does not create a box with 3 sides)
    safe_moves = []
    
    # Check all horizontal edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                is_safe = True
                # Check box above
                if r > 0 and count_sides(r - 1, c) == 2: is_safe = False
                # Check box below
                if r < 4 and count_sides(r, c) == 2: is_safe = False
                if is_safe: safe_moves.append(f"{r},{c},H")
                
    # Check all vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                is_safe = True
                # Check box left
                if c > 0 and count_sides(r, c - 1) == 2: is_safe = False
                # Check box right
                if c < 4 and count_sides(r, c) == 2: is_safe = False
                if is_safe: safe_moves.append(f"{r},{c},V")

    if safe_moves:
        # Pick the first safe move found
        return safe_moves[0]

    # 3. If no safe moves, pick any legal move (fallback)
    # Check horizontal
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    # Check vertical
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H" # Should not be reached
