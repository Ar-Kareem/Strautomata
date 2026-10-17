
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Helper to count sides of a box at (r, c)
    def count_sides(r, c):
        count = 0
        if horizontal[r, c] != 0: count += 1
        if horizontal[r + 1, c] != 0: count += 1
        if vertical[r, c] != 0: count += 1
        if vertical[r, c + 1] != 0: count += 1
        return count

    # Helper to find which edge is missing in a box with 3 sides
    def get_missing_edge(r, c):
        if horizontal[r, c] == 0: return f"{r},{c},H"
        if horizontal[r + 1, c] == 0: return f"{r+1},{c},H"
        if vertical[r, c] == 0: return f"{r},{c},V"
        if vertical[r, c + 1] == 0: return f"{r},{c+1},V"
        return None

    # 1. Capture moves (priority 1)
    for r in range(4):
        for c in range(4):
            if count_sides(r, c) == 3:
                return get_missing_edge(r, c)

    # 2. Collect all legal moves
    legal_h = []
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                legal_h.append((r, c, 'H'))
    
    legal_v = []
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                legal_v.append((r, c, 'V'))

    all_moves = legal_h + legal_v

    # 3. Filter "Safe" moves (moves that don't create a box with 3 sides)
    safe_moves = []
    for r, c, d in all_moves:
        is_safe = True
        if d == 'H':
            # Check box above
            if r > 0 and count_sides(r - 1, c) == 2:
                is_safe = False
            # Check box below
            if r < 4 and count_sides(r, c) == 2:
                is_safe = False
        else: # d == 'V'
            # Check box left
            if c > 0 and count_sides(r, c - 1) == 2:
                is_safe = False
            # Check box right
            if c < 4 and count_sides(r, c) == 2:
                is_safe = False
        
        if is_safe:
            safe_moves.append(f"{r},{c},{d}")

    if safe_moves:
        # Prefer edges on the perimeter for safety
        for move in safe_moves:
            r, c, d = move.split(',')
            r, c = int(r), int(c)
            if d == 'H' and (r == 0 or r == 4): return move
            if d == 'V' and (c == 0 or c == 4): return move
        return safe_moves[0]

    # 4. If no safe moves, pick a move that creates the smallest impact (heuristic)
    # For simplicity, we return the first available legal move
    if all_moves:
        r, c, d = all_moves[0]
        return f"{r},{c},{d}"

    return "0,0,H" # Should never reach here in a legal game state
