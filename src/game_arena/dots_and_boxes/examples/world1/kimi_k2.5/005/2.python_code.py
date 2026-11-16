
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h = horizontal
    v = vertical
    
    def count_box_edges(br, bc):
        """Count filled edges for box at (br, bc)"""
        count = 0
        if h[br, bc] != 0: count += 1      # top
        if h[br+1, bc] != 0: count += 1    # bottom
        if v[br, bc] != 0: count += 1      # left
        if v[br, bc+1] != 0: count += 1    # right
        return count
    
    def simulate_opponent_captures(r, c, is_horizontal):
        """Simulate opponent capturing all boxes after we make this move"""
        h_temp = h.copy()
        v_temp = v.copy()
        
        # Make our move
        if is_horizontal:
            h_temp[r, c] = 1
        else:
            v_temp[r, c] = 1
        
        # Simulate opponent taking all available boxes (chain reaction)
        total = 0
        while True:
            found = False
            for br in range(4):
                for bc in range(4):
                    # Find empty edges of box (br, bc)
                    empty = []
                    if h_temp[br, bc] == 0: empty.append(('H', br, bc))
                    if h_temp[br+1, bc] == 0: empty.append(('H', br+1, bc))
                    if v_temp[br, bc] == 0: empty.append(('V', br, bc))
                    if v_temp[br, bc+1] == 0: empty.append(('V', br, bc+1))
                    
                    if len(empty) == 1:
                        # Opponent captures this box
                        total += 1
                        d, er, ec = empty[0]
                        if d == 'H':
                            h_temp[er, ec] = -1
                        else:
                            v_temp[er, ec] = -1
                        found = True
                        break
                if found:
                    break
            if not found:
                break
        return total
    
    moves = []  # (row, col, dir, our_captures, opponent_captures)
    
    # Check all horizontal edges
    for r in range(5):
        for c in range(5):
            if h[r, c] == 0:
                our_caps = 0
                # Box above: (r-1, c) - this edge is the bottom
                if r > 0 and count_box_edges(r-1, c) == 3:
                    our_caps += 1
                # Box below: (r, c) - this edge is the top
                if r < 4 and count_box_edges(r, c) == 3:
                    our_caps += 1
                
                opp_caps = simulate_opponent_captures(r, c, True)
                moves.append((r, c, 'H', our_caps, opp_caps))
    
    # Check all vertical edges
    for r in range(5):
        for c in range(5):
            if v[r, c] == 0:
                our_caps = 0
                # Box left: (r, c-1) - this edge is the right side
                if c > 0 and count_box_edges(r, c-1) == 3:
                    our_caps += 1
                # Box right: (r, c) - this edge is the left side
                if c < 4 and count_box_edges(r, c) == 3:
                    our_caps += 1
                
                opp_caps = simulate_opponent_captures(r, c, False)
                moves.append((r, c, 'V', our_caps, opp_caps))
    
    # Priority 1: Take any capturing move (prefer those that capture more)
    capturing = [m for m in moves if m[3] > 0]
    if capturing:
        capturing.sort(key=lambda x: -x[3])
        r, c, d, _, _ = capturing[0]
        return f"{r},{c},{d}"
    
    # Priority 2: Safe moves that don't give opponent any boxes
    safe = [m for m in moves if m[4] == 0]
    if safe:
        r, c, d, _, _ = safe[0]
        return f"{r},{c},{d}"
    
    # Priority 3: Minimize opponent's gain
    moves.sort(key=lambda x: x[4])
    r, c, d, _, _ = moves[0]
    return f"{r},{c},{d}"
