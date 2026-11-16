
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """Return a legal move 'row,col,dir' for Dots and Boxes on a 4x4 grid."""
    
    # ----- helpers -------------------------------------------------
    def box_filled(r: int, c: int, h: np.ndarray, v: np.ndarray) -> int:
        """Number of drawn edges around box (r,c)."""
        return (h[r, c] != 0) + (h[r + 1, c] != 0) + (v[r, c] != 0) + (v[r, c + 1] != 0)
    
    def count_two_sided(h: np.ndarray, v: np.ndarray, cap: np.ndarray) -> int:
        """Count uncaptured boxes with exactly two sides filled."""
        cnt = 0
        for r in range(4):
            for c in range(4):
                if cap[r, c] == 0 and box_filled(r, c, h, v) == 2:
                    cnt += 1
        return cnt
    
    def simulate_opponent(h: np.ndarray, v: np.ndarray, cap: np.ndarray) -> int:
        """
        Simulate the opponent greedily capturing all boxes that have three sides.
        Returns the number of boxes the opponent captures.
        Modifies h, v, cap in place (edges marked -1, boxes marked -1).
        """
        captured = 0
        while True:
            progressed = False
            for r in range(4):
                for c in range(4):
                    if cap[r, c] != 0:
                        continue
                    if box_filled(r, c, h, v) == 3:
                        # find the missing edge
                        if h[r, c] == 0:               # top
                            h[r, c] = -1
                            if r > 0 and cap[r - 1, c] == 0 and box_filled(r - 1, c, h, v) == 4:
                                cap[r - 1, c] = -1
                                captured += 1
                        elif h[r + 1, c] == 0:         # bottom
                            h[r + 1, c] = -1
                            if r < 3 and cap[r + 1, c] == 0 and box_filled(r + 1, c, h, v) == 4:
                                cap[r + 1, c] = -1
                                captured += 1
                        elif v[r, c] == 0:             # left
                            v[r, c] = -1
                            if c > 0 and cap[r, c - 1] == 0 and box_filled(r, c - 1, h, v) == 4:
                                cap[r, c - 1] = -1
                                captured += 1
                        else:                           # right (v[r, c+1] == 0)
                            v[r, c + 1] = -1
                            if c < 3 and cap[r, c + 1] == 0 and box_filled(r, c + 1, h, v) == 4:
                                cap[r, c + 1] = -1
                                captured += 1
                        # capture the box we just completed
                        cap[r, c] = -1
                        captured += 1
                        progressed = True
                        break
                if progressed:
                    break
            if not progressed:
                break
        return captured
    
    # ----- generate all legal moves --------------------------------
    moves = []
    # horizontal edges: rows 0..4, cols 0..3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    # vertical edges: rows 0..3, cols 0..4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
    
    best_move = None
    best_score = None   # tuple to be minimized
    
    for r, c, d in moves:
        h2 = horizontal.copy()
        v2 = vertical.copy()
        cap2 = capture.copy()
        
        # apply our move
        if d == 'H':
            h2[r, c] = 1
        else:
            v2[r, c] = 1
        
        # count boxes we capture with this move
        our_captures = 0
        if d == 'H':
            if r > 0 and cap2[r - 1, c] == 0 and box_filled(r - 1, c, h2, v2) == 4:
                our_captures += 1
                cap2[r - 1, c] = 1
            if r < 4 and cap2[r, c] == 0 and box_filled(r, c, h2, v2) == 4:
                our_captures += 1
                cap2[r, c] = 1
        else:  # V
            if c > 0 and cap2[r, c - 1] == 0 and box_filled(r, c - 1, h2, v2) == 4:
                our_captures += 1
                cap2[r, c - 1] = 1
            if c < 4 and cap2[r, c] == 0 and box_filled(r, c, h2, v2) == 4:
                our_captures += 1
                cap2[r, c] = 1
        
        if our_captures > 0:
            # capturing moves are best; prefer more captures
            score = (0, -our_captures, 0)
        else:
            # simulate opponent's greedy response
            opp_cost = simulate_opponent(h2, v2, cap2)
            danger = count_two_sided(h2, v2, cap2)
            # lower cost is better; if equal, lower danger is better
            score = (1, opp_cost, danger)
        
        if best_score is None or score < best_score:
            best_score = score
            best_move = (r, c, d)
    
    r, c, d = best_move
    return f"{r},{c},{d}"
