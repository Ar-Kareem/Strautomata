
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Greedy strategy for Dots and Boxes:
    1. Take any available capture (prefer double captures).
    2. Play safe moves that don't create 3-sided boxes.
       Prefer moves that create fewer 2-sided boxes.
    3. If forced, play moves that create the fewest 3-sided boxes.
    """
    
    def box_edge_count(i, j):
        """Count filled edges around box (i,j). Returns 4 if already captured."""
        if capture[i, j] != 0:
            return 4
        top = horizontal[i, j] != 0
        bottom = horizontal[i+1, j] != 0
        left = vertical[i, j] != 0
        right = vertical[i, j+1] != 0
        return int(top) + int(bottom) + int(left) + int(right)
    
    moves = []  # (captures, dangers, twos, r, c, dir)
    
    # Horizontal edges: rows 0-4, cols 0-3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                caps = 0
                dangs = 0
                twos = 0
                # Affected boxes
                boxes = []
                if r > 0:
                    boxes.append((r-1, c))
                if r < 4:
                    boxes.append((r, c))
                
                for (bi, bj) in boxes:
                    if capture[bi, bj] != 0:
                        continue
                    cnt = box_edge_count(bi, bj)
                    if cnt == 3:
                        caps += 1
                    elif cnt == 2:
                        dangs += 1
                    elif cnt == 1:
                        twos += 1
                    # cnt == 0: becomes 1, ignore
                
                moves.append((caps, dangs, twos, r, c, 'H'))
    
    # Vertical edges: rows 0-3, cols 0-4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                caps = 0
                dangs = 0
                twos = 0
                boxes = []
                if c > 0:
                    boxes.append((r, c-1))
                if c < 4:
                    boxes.append((r, c))
                
                for (bi, bj) in boxes:
                    if capture[bi, bj] != 0:
                        continue
                    cnt = box_edge_count(bi, bj)
                    if cnt == 3:
                        caps += 1
                    elif cnt == 2:
                        dangs += 1
                    elif cnt == 1:
                        twos += 1
                
                moves.append((caps, dangs, twos, r, c, 'V'))
    
    if not moves:
        # Should not happen in a valid game
        return "0,0,H"
    
    # Separate by category
    capturing = [m for m in moves if m[0] > 0]
    safe = [m for m in moves if m[0] == 0 and m[1] == 0]
    risky = [m for m in moves if m[0] == 0 and m[1] > 0]
    
    # 1. Capturing: maximize captures, then minimize dangers
    if capturing:
        best = max(capturing, key=lambda x: (x[0], -x[1]))
        return f"{best[3]},{best[4]},{best[5]}"
    
    # 2. Safe: minimize twos (boxes that become 2-sided)
    if safe:
        best = min(safe, key=lambda x: x[2])
        return f"{best[3]},{best[4]},{best[5]}"
    
    # 3. Risky: minimize dangers
    if risky:
        best = min(risky, key=lambda x: x[1])
        return f"{best[3]},{best[4]},{best[5]}"
    
    # Fallback
    m = moves[0]
    return f"{m[3]},{m[4]},{m[5]}"
