
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Get board size (5x5 for 4x4 boxes)
    rows, cols = horizontal.shape  # 5x5
    
    # Collect all legal moves (edge is 0)
    legal_moves = []
    
    # Scan horizontal edges
    for r in range(rows):
        for c in range(cols):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
    
    # Scan vertical edges
    for r in range(rows):
        for c in range(cols):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))
    
    # If no legal moves (shouldn't happen in proper game), return arbitrary
    if not legal_moves:
        return "0,0,H"  # Fallback (should never reach here)
    
    # Check for immediate capture moves
    immediate_capture_moves = []
    dangerous_moves = []   # Moves that complete 3rd side of any box
    safe_moves = []        # Moves that don't complete third side of any box
    
    for r, c, direction in legal_moves:
        completes_box = False
        third_side_count = 0
        
        if direction == 'H':
            # Horizontal edge at (r, c) affects boxes above and below
            # Box above: (r-1, c) if r > 0
            if r > 0:
                # Check the 4 edges of box (r-1, c)
                top = horizontal[r-1, c]
                bottom = horizontal[r, c]  # this is the move we are considering
                left = vertical[r-1, c]
                right = vertical[r-1, c+1]
                edges = [top, bottom, left, right]
                if sum(1 for e in edges if e != 0) == 3:
                    completes_box = True
                    third_side_count += 1
            
            # Box below: (r, c) if r < 4
            if r < 4:
                top = horizontal[r, c]  # this is the move
                bottom = horizontal[r+1, c]
                left = vertical[r, c]
                right = vertical[r, c+1]
                edges = [top, bottom, left, right]
                if sum(1 for e in edges if e != 0) == 3:
                    completes_box = True
                    third_side_count += 1
                
            if completes_box:
                immediate_capture_moves.append((r, c, direction))
            else:
                # Even if no immediate capture, if this edge is the 3rd for ANY box -> dangerous
                # We count third sides in all adjacent boxes
                third_sides = 0
                if r > 0:
                    edges = [horizontal[r-1, c], horizontal[r, c], vertical[r-1, c], vertical[r-1, c+1]]
                    if sum(1 for e in edges if e != 0) == 3:
                        third_sides += 1
                if r < 4:
                    edges = [horizontal[r, c], horizontal[r+1, c], vertical[r, c], vertical[r, c+1]]
                    if sum(1 for e in edges if e != 0) == 3:
                        third_sides += 1
                if third_sides > 0:
                    dangerous_moves.append((r, c, direction))
                else:
                    safe_moves.append((r, c, direction))
                    
        else:  # direction == 'V'
            # Vertical edge at (r, c) affects boxes on left and right
            # Box to the left: (r, c-1) if c > 0
            if c > 0:
                top = vertical[r, c-1]
                bottom = vertical[r, c]  # this is the move
                left = horizontal[r, c-1]
                right = horizontal[r+1, c-1]
                edges = [top, bottom, left, right]
                if sum(1 for e in edges if e != 0) == 3:
                    completes_box = True
                    third_side_count += 1
            
            # Box to the right: (r, c) if c < 4
            if c < 4:
                top = vertical[r, c]   # this is the move
                bottom = vertical[r, c+1]
                left = horizontal[r, c]
                right = horizontal[r+1, c]
                edges = [top, bottom, left, right]
                if sum(1 for e in edges if e != 0) == 3:
                    completes_box = True
                    third_side_count += 1
                
            if completes_box:
                immediate_capture_moves.append((r, c, direction))
            else:
                third_sides = 0
                if c > 0:
                    edges = [vertical[r, c-1], vertical[r, c], horizontal[r, c-1], horizontal[r+1, c-1]]
                    if sum(1 for e in edges if e != 0) == 3:
                        third_sides += 1
                if c < 4:
                    edges = [vertical[r, c], vertical[r, c+1], horizontal[r, c], horizontal[r+1, c]]
                    if sum(1 for e in edges if e != 0) == 3:
                        third_sides += 1
                if third_sides > 0:
                    dangerous_moves.append((r, c, direction))
                else:
                    safe_moves.append((r, c, direction))
    
    # Strategy hierarchy:
    # 1. If there are immediate capture moves, take one (prefer first for simplicity)
    if immediate_capture_moves:
        r, c, d = immediate_capture_moves[0]
        return f"{r},{c},{d}"
    
    # 2. If safe moves exist, prefer them
    if safe_moves:
        # Prioritize moves that are on the edge (less central) to reduce future threats
        # We prefer moves that are on the boundary of the board (outer edges)
        edge_moves = []
        for r, c, d in safe_moves:
            if r == 0 or r == 4 or c == 0 or c == 4:
                edge_moves.append((r, c, d))
        if edge_moves:
            return f"{edge_moves[0][0]},{edge_moves[0][1]},{edge_moves[0][2]}"
        else:
            return f"{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}"
    
    # 3. No safe moves: choose least dangerous among dangerous moves
    # Among dangerous moves, we pick one that completes the fewest number of potential double-box threats
    # Since all dangerous moves here complete exactly one third-side, we just pick the first
    if dangerous_moves:
        return f"{dangerous_moves[0][0]},{dangerous_moves[0][1]},{dangerous_moves[0][2]}"
    
    # Fallback: take any legal move (shouldn't reach here due to hierarchy)
    r, c, d = legal_moves[0]
    return f"{r},{c},{d}"
