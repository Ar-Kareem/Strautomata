
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Look for boxes with exactly 3 edges filled and complete them
    for r in range(4):
        for c in range(4):
            if capture[r, c] == 0:
                edges = 0
                if horizontal[r, c] != 0:
                    edges += 1
                if horizontal[r + 1, c] != 0:
                    edges += 1
                if vertical[r, c] != 0:
                    edges += 1
                if vertical[r, c + 1] != 0:
                    edges += 1
                if edges == 3:
                    # Complete this box
                    if horizontal[r, c] == 0:
                        return f"{r},{c},H"
                    if horizontal[r + 1, c] == 0:
                        return f"{r+1},{c},H"
                    if vertical[r, c] == 0:
                        return f"{r},{c},V"
                    if vertical[r, c + 1] == 0:
                        return f"{r},{c+1},V"

    # Try to avoid moves that produce a box with 3 edges filled by the opponent
    safe_moves = []

    for r in range(5):
        for c in range(5):
            if r < 4 and horizontal[r, c] == 0:
                # Move H at (r, c)
                temp_capture = capture.copy()
                temp_edges = 0
                if r > 0:
                    if vertical[r - 1, c] != 0:
                        temp_edges += 1
                    if c < 4 and vertical[r - 1, c + 1] != 0:
                        temp_edges += 1
                else:
                    if c < 4 and vertical[r, c + 1] != 0:
                        temp_edges += 1
                if c > 0 and horizontal[r, c - 1] != 0:
                    temp_edges += 1
                if c < 4 and horizontal[r, c + 1] != 0:
                    temp_edges += 1
                # Check if placing this edge would create a danger for the opponent
                if temp_edges >= 2:
                    # Do not add to safe moves
                    pass
                else:
                    safe_moves.append((r, c, 'H'))
            if c < 4 and vertical[r, c] == 0:
                # Move V at (r, c)
                temp_edges = 0
                if c > 0:
                    if horizontal[r, c - 1] != 0:
                        temp_edges += 1
                    if r < 4 and horizontal[r + 1, c - 1] != 0:
                        temp_edges += 1
                else:
                    if r < 4 and horizontal[r + 1, c] != 0:
                        temp_edges += 1
                if r > 0 and vertical[r - 1, c] != 0:
                    temp_edges += 1
                if r < 4 and vertical[r + 1, c] != 0:
                    temp_edges += 1
                # Check if placing this edge would create a danger for the opponent
                if temp_edges >= 2:
                    # Do not add to safe moves
                    pass
                else:
                    safe_moves.append((r, c, 'V'))

    # If there are safe moves, choose one randomly
    if safe_moves:
        r, c, direction = safe_moves[0]
        return f"{r},{c},{direction}"

    # Fallback: make any legal move
    for r in range(5):
        for c in range(5):
            if r < 4 and horizontal[r, c] == 0:
                return f"{r},{c},H"
            if c < 4 and vertical[r, c] == 0:
                return f"{r},{c},V"

    # Should never reach here
    return "0,0,H"
