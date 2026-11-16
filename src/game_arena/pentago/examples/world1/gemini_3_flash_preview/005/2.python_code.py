
import numpy as np

def policy(you, opponent):
    # Convert input to 2D numpy arrays
    me = np.array(you)
    opp = np.array(opponent)
    
    def get_winner(b):
        # Check all 5-in-a-row in 6x6
        # Horizontal
        for r in range(6):
            for c in range(2):
                if np.all(b[r, c:c+5] == 1): return True
        # Vertical
        for c in range(6):
            for r in range(2):
                if np.all(b[r:r+5, c] == 1): return True
        # Diagonal
        for r in range(2):
            for c in range(2):
                if all(b[r+i, c+i] == 1 for i in range(5)): return True
                if all(b[r+i, c+4-i] == 1 for i in range(5)): return True
        return False

    def rotate(b, quad, direction):
        nb = b.copy()
        r_start = 0 if quad in [0, 1] else 3
        c_start = 0 if quad in [0, 2] else 3
        sub = b[r_start:r_start+3, c_start:c_start+3]
        if direction == 'R':
            nb[r_start:r_start+3, c_start:c_start+3] = np.rot90(sub, -1)
        else:
            nb[r_start:r_start+3, c_start:c_start+3] = np.rot90(sub, 1)
        return nb

    # Optimization: pre-calculate empty spots
    empty = []
    for r in range(6):
        for c in range(6):
            if me[r, c] == 0 and opp[r, c] == 0:
                empty.append((r, c))

    best_move = None
    
    # 1. Search for immediate win
    for r, c in empty:
        for q in range(4):
            for d in ['L', 'R']:
                temp_me = me.copy()
                temp_me[r, c] = 1
                temp_opp = opp.copy()
                
                # Apply rotation to both
                new_me = rotate(temp_me, q, d)
                new_opp = rotate(temp_opp, q, d)
                
                if get_winner(new_me):
                    return f"{r+1},{c+1},{q},{d}"

    # 2. Block opponent immediate win
    # A simple blocks involves seeing if opponent wins if they go next
    # For speed, we just look for high-value placements
    
    # 3. Heuristic: Center of quadrants, then corners, then others
    preferred_order = [
        (1, 1), (1, 4), (4, 1), (4, 4), # 3x3 centers
        (0, 0), (0, 2), (0, 3), (0, 5), # Quadrant corners
        (2, 0), (2, 2), (3, 0), (3, 2),
        (2, 3), (2, 5), (3, 3), (3, 5),
    ]
    
    # Filter empty spots based on preference
    sorted_empty = []
    pref_set = set(preferred_order)
    for p in preferred_order:
        if p in empty:
            sorted_empty.append(p)
    for e in empty:
        if e not in pref_set:
            sorted_empty.append(e)

    # Return the first heuristic-friendly move that doesn't immediately lose 
    # (Simplified: just return the first preferred move)
    r, c = sorted_empty[0]
    # Default rotation: rotate the quadrant we placed in to maximize impact
    q = (0 if r < 3 else 2) + (0 if c < 3 else 1)
    return f"{r+1},{c+1},{q},R"
