
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Game constants
    ROWS, COLS = 4, 4

    def get_box_edges_count(r, c):
        count = 0
        if horizontal[r, c] != 0: count += 1
        if horizontal[r + 1, c] != 0: count += 1
        if vertical[r, c] != 0: count += 1
        if vertical[r, c + 1] != 0: count += 1
        return count

    # 1. Look for capturing moves (boxes with 3 sides already filled)
    for r in range(ROWS):
        for c in range(COLS):
            cnt = get_box_edges_count(r, c)
            if cnt == 3:
                # Find the missing edge
                if horizontal[r, c] == 0: return f"{r},{c},H"
                if horizontal[r + 1, c] == 0: return f"{r+1},{c},H"
                if vertical[r, c] == 0: return f"{r},{c},V"
                if vertical[r, c + 1] == 0: return f"{r},{c+1},V"

    # Helper to check if a specific move is safe (doesn't create a "3-side" box)
    def is_safe(r, c, btype):
        if btype == 'H':
            # Check box above and box below
            if r > 0:
                if get_box_edges_count(r - 1, c) == 2: return False
            if r < ROWS:
                if get_box_edges_count(r, c) == 2: return False
        else: # Vertical
            # Check box left and box right
            if c > 0:
                if get_box_edges_count(r, c - 1) == 2: return False
            if c < COLS:
                if get_box_edges_count(r, c) == 2: return False
        return True

    # Collect all legal moves
    legal_h = []
    for r in range(ROWS + 1):
        for c in range(COLS):
            if horizontal[r, c] == 0:
                legal_h.append((r, c, 'H'))
    
    legal_v = []
    for r in range(ROWS):
        for c in range(COLS + 1):
            if vertical[r, c] == 0:
                legal_v.append((r, c, 'V'))

    all_legal = legal_h + legal_v

    # 2. Filter for safe moves
    safe_moves = [m for m in all_legal if is_safe(m[0], m[1], m[2])]

    if safe_moves:
        # Prefer edges that are not part of any box yet or have only 0-1 neighbors
        # Sort or pick first available safe move
        import random
        move = random.choice(safe_moves)
        return f"{move[0]},{move[1]},{move[2]}"

    # 3. If no safe moves, we are forced to give a box away.
    # We choose a move that completes a box for the opponent but try to minimize damage.
    # For simplicity, returning the first available legal move.
    if all_legal:
        # In a real competitive scenario, one would calculate chain lengths here.
        move = all_legal[0]
        return f"{move[0]},{move[1]},{move[2]}"

    return "0,0,H" # Fallback (should not be reached)
