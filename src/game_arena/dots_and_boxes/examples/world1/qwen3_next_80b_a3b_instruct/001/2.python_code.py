
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Get all possible moves (edges that are not drawn)
    possible_moves = []
    
    # Check horizontal edges (5 rows, 4 cols)
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                possible_moves.append((r, c, 'H'))
    
    # Check vertical edges (4 rows, 5 cols)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                possible_moves.append((r, c, 'V'))
    
    # First, check for any move that completes one or more boxes
    for r, c, direction in possible_moves:
        if direction == 'H':
            # This horizontal edge is at (r, c) — it's the top edge of box (r, c) and bottom edge of box (r-1, c)
            boxes_to_check = []
            # Top box: (r-1, c) if r > 0
            if r > 0:
                boxes_to_check.append((r-1, c))
            # Bottom box: (r, c) if r < 4
            if r < 4:
                boxes_to_check.append((r, c))
            
            # Count how many sides each box already has (including this move)
            completed = False
            for box_r, box_c in boxes_to_check:
                # Get the four sides of this box
                top = horizontal[box_r, box_c]
                bottom = horizontal[box_r+1, box_c]
                left = vertical[box_r, box_c]
                right = vertical[box_r, box_c+1]
                
                # Count existing edges (signed, but we only care if nonzero)
                sides_filled = sum(1 for x in [top, bottom, left, right] if x != 0)
                
                # If this move makes it 4, then we complete it
                if sides_filled == 3:
                    # This move completes a box!
                    return f"{r},{c},{direction}"
        
        else:  # direction == 'V'
            # This vertical edge is at (r, c) — it's the left edge of box (r, c) and right edge of box (r, c-1)
            boxes_to_check = []
            # Left box: (r, c-1) if c > 0
            if c > 0:
                boxes_to_check.append((r, c-1))
            # Right box: (r, c) if c < 4
            if c < 4:
                boxes_to_check.append((r, c))
            
            for box_r, box_c in boxes_to_check:
                # Get the four sides of this box
                top = horizontal[box_r, box_c]
                bottom = horizontal[box_r+1, box_c]
                left = vertical[box_r, box_c]
                right = vertical[box_r, box_c+1]
                
                sides_filled = sum(1 for x in [top, bottom, left, right] if x != 0)
                
                if sides_filled == 3:
                    return f"{r},{c},{direction}"
    
    # If we're here, no immediate capture moves exist.
    # Now check for moves that would create a 3-sided box for the opponent.
    # We must avoid those unless forced.
    safe_moves = []
    
    for r, c, direction in possible_moves:
        safe = True
        
        if direction == 'H':
            boxes_to_check = []
            if r > 0:
                boxes_to_check.append((r-1, c))
            if r < 4:
                boxes_to_check.append((r, c))
                
            for box_r, box_c in boxes_to_check:
                top = horizontal[box_r, box_c]
                bottom = horizontal[box_r+1, box_c]
                left = vertical[box_r, box_c]
                right = vertical[box_r, box_c+1]
                
                sides_filled = sum(1 for x in [top, bottom, left, right] if x != 0)
                
                # If adding this edge would make it 3, then it's dangerous
                # BUT: if the box is already captured, it doesn't matter
                if capture[box_r, box_c] == 0 and sides_filled == 2:
                    safe = False
                    break
                    
        else:  # direction == 'V'
            boxes_to_check = []
            if c > 0:
                boxes_to_check.append((r, c-1))
            if c < 4:
                boxes_to_check.append((r, c))
                
            for box_r, box_c in boxes_to_check:
                top = horizontal[box_r, box_c]
                bottom = horizontal[box_r+1, box_c]
                left = vertical[box_r, box_c]
                right = vertical[box_r, box_c+1]
                
                sides_filled = sum(1 for x in [top, bottom, left, right] if x != 0)
                
                if capture[box_r, box_c] == 0 and sides_filled == 2:
                    safe = False
                    break
        
        if safe:
            safe_moves.append((r, c, direction))
    
    # If there are safe moves, choose the lexicographically first
    if safe_moves:
        safe_moves.sort()  # sorts by r, then c, then dir (H before V)
        r, c, direction = safe_moves[0]
        return f"{r},{c},{direction}"
    
    # If no safe moves, we are forced to make a "dangerous" move.
    # We still want to minimize damage: pick the move that completes the least boxes
    # (though we know none complete immediately) and otherwise just pick the first.
    # In this case, any move will create a 3-sided box, so we pick the lexicographically first.
    possible_moves.sort()
    r, c, direction = possible_moves[0]
    return f"{r},{c},{direction}"
