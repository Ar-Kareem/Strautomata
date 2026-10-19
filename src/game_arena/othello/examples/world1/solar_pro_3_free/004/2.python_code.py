
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the next Othello move (or 'pass') given the current board."""
    # Directions: eight possible lines of play
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (1, 1), (-1, 1), (1, -1)]
    rows, cols = you.shape
    
    # Helper: check a single direction
    def count_flips(r, c, dir_r, dir_c):
        flips = 0
        nr, nc = r + dir_r, c + dir_c
        while 0 <= nr < rows and 0 <= nc < cols:
            if you[nr, nc] == 1:          # your disc blocks the line
                return flips
            elif opponent[nr, nc] == 1:   # opponent disc can be captured
                flips += 1
                nr += dir_r
                nc += dir_c
            else:                        # empty cell stops the line
                break
        return flips
    
    # 1️⃣ Legal moves with flip count
    legal_moves = []   # each entry: (r, c, flips)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    
    # Check every empty square
    for r in range(rows):
        for c in range(cols):
            if you[r, c] == 1 or opponent[r, c] == 1:
                continue  # occupied
            legal = False
            total_flips = 0
            for dr, dc in dirs:
                if count_flips(r, c, dr, dc) > 0:
                    legal = True
                    total_flips += count_flips(r, c, dr, dc)
                    # early exit: if already a corner, we don't need more counts
                    break
            if legal:
                legal_moves.append((r, c, total_flips))
    
    # If no legal move → pass
    if not legal_moves:
        return "pass"
    
    # 2️⃣ Pick a corner move if any exists
    corner_candidates = [mv for mv in legal_moves if mv[:2] in corners]
    if corner_candidates:
        # Choose corner with highest flip count, breaking ties with board score
        best_corner = max(corner_candidates,
                          key=lambda mv: (mv[2],
                                         -(you.sum() - opponent.sum())))  # tie‑breaker
        r, c = best_corner[:2]
        file = chr(ord('a') + c)
        rank = str(r + 1)   # rows are 0‑based, ranks are 1‑based
        return f"{file}{rank}"
    
    # 3️⃣ Otherwise evaluate all moves
    best_move = max(legal_moves,
                    key=lambda mv: (mv[2],
                                   -(you.sum() - opponent.sum())))
    r, c = best_move[:2]
    file = chr(ord('a') + c)
    rank = str(r + 1)
    return f"{file}{rank}"
