
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for 4x4 grid.
    Strategy: 
    1. Avoid giving away boxes (safe moves) to build chains.
    2. Prioritize moves that maximize chain length (double edges).
    3. In the endgame (no safe moves), use parity counting to win chains.
    """
    
    # Dimensions: 5x5 dots, 4x4 boxes
    ROWS, COLS = 5, 5
    
    # Helper to count filled sides of a box
    def count_filled(r, c, h, v):
        if r < 0 or r >= 4 or c < 0 or c >= 4:
            return 0
        count = 0
        # Top edge
        if r > 0 and h[r, c] != 0: count += 1
        # Bottom edge
        if r < 4 and h[r+1, c] != 0: count += 1
        # Left edge
        if c > 0 and v[r, c] != 0: count += 1
        # Right edge
        if c < 4 and v[r, c+1] != 0: count += 1
        return count

    # Helper to simulate a move and count captured boxes
    def get_captures(r, c, is_horiz, h, v):
        caps = []
        if is_horiz:
            # Box above
            if r > 0 and count_filled(r-1, c, h, v) == 3: caps.append((r-1, c))
            # Box below
            if r < 4 and count_filled(r, c, h, v) == 3: caps.append((r, c))
        else:
            # Box left
            if c > 0 and count_filled(r, c-1, h, v) == 3: caps.append((r, c-1))
            # Box right
            if c < 4 and count_filled(r, c, h, v) == 3: caps.append((r, c))
        return caps

    # Helper to get degree (number of neighbors) for chain heuristic
    def get_degree(r, c, h, v):
        d = 0
        # Horizontal edges (rows)
        if r > 0 and h[r, c] == 0: d += 1
        if r < 4 and h[r+1, c] == 0: d += 1
        # Vertical edges (cols)
        if c > 0 and v[r, c] == 0: d += 1
        if c < 4 and v[r, c+1] == 0: d += 1
        return d

    # Collect all legal moves
    moves = []
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))

    if not moves:
        return "" # Should not happen in valid game state

    # --- 1. Look for Safe Moves (No immediate capture) ---
    safe_moves = []
    for r, c, d in moves:
        is_horiz = (d == 'H')
        
        # Simulate to check captures
        h_sim = horizontal.copy()
        v_sim = vertical.copy()
        if is_horiz:
            h_sim[r, c] = 1
        else:
            v_sim[r, c] = 1
            
        caps = get_captures(r, c, is_horiz, h_sim, v_sim)
        
        if not caps:
            # It's a safe move. Now, evaluate quality (Chain heuristic)
            # We want to maximize the creation of "double edges" (shared edges between 2 unclaimed boxes)
            # A simple heuristic: minimize the degree of the affected boxes to keep chains long.
            score = 0
            
            # Identify adjacent boxes
            adj_boxes = []
            if is_horiz:
                if r > 0: adj_boxes.append((r-1, c))
                if r < 4: adj_boxes.append((r, c))
            else:
                if c > 0: adj_boxes.append((r, c-1))
                if c < 4: adj_boxes.append((r, c))
                
            # Heuristic: We prefer edges that touch boxes with fewer existing sides.
            # And edges that connect two boxes (Double Edge) > 1 box > 0 box.
            for br, bc in adj_boxes:
                if capture[br, bc] == 0: # Only count unclaimed boxes
                    deg = count_filled(br, bc, h_sim, v_sim)
                    # Lower degree is generally better for building chains, but 1 is better than 0 for connectivity?
                    # Actually, strictly avoiding giving the opponent a "3" is priority.
                    # Here we just sum degrees. Lower sum is safer/more chain-like.
                    score -= deg
            
            # Bonus for double edges (touching 2 unclaimed boxes)
            if len(adj_boxes) == 2 and all(capture[br, bc] == 0 for br, bc in adj_boxes):
                score += 1 
            
            safe_moves.append((score, r, c, d))

    # If we have safe moves, pick the best one
    if safe_moves:
        # Sort by score descending (higher score is better)
        safe_moves.sort(key=lambda x: x[0], reverse=True)
        _, r, c, d = safe_moves[0]
        return f"{r},{c},{d}"

    # --- 2. Endgame: Forced Captures (No safe moves) ---
    # Calculate remaining unclaimed boxes
    unclaimed = 0
    for r in range(4):
        for c in range(4):
            if capture[r, c] == 0:
                unclaimed += 1

    # We want to control the parity.
    # If remaining boxes is ODD: We take 1, opponent takes 1... we take the last one. We win.
    # If remaining boxes is EVEN: We want to give the opponent the first one.
    
    sacrifices = [] # Moves that give away exactly 1 box
    
    for r, c, d in moves:
        is_horiz = (d == 'H')
        caps = get_captures(r, c, is_horiz, horizontal, vertical)
        
        num_caps = len(caps)
        
        if num_caps > 0:
            if unclaimed % 2 == 1:
                # Odd remaining: We must take the first box to maintain control
                # Taking 1 box (or any amount) is fine here, as long as we start the sequence.
                # Actually, taking exactly 1 is best to keep it simple.
                if num_caps == 1:
                    return f"{r},{c},{d}"
            else:
                # Even remaining: We want to force opponent to take the first box.
                # We need to make a move that gives away exactly 1 box.
                if num_caps == 1:
                    sacrifices.append((r, c, d))

    # If we are in the odd phase and didn't find a single capture, pick the move with minimum captures
    if unclaimed % 2 == 1:
        # Find move with fewest captures
        moves.sort(key=lambda m: len(get_captures(m[0], m[1], m[2]=='H', horizontal, vertical)))
        r, c, d = moves[0]
        return f"{r},{c},{d}"

    # If we are in the even phase and found a sacrifice
    if sacrifices:
        return f"{sacrifices[0][0]},{sacrifices[0][1]},{sacrifices[0][2]}"

    # Fallback (should rarely be reached in a solved 4x4 game)
    # Pick any move
    r, c, d = moves[0]
    return f"{r},{c},{d}"
