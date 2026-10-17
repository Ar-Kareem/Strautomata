
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Find all legal moves
    legal_moves = []
    
    # Check all horizontal edges
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    
    # Check all vertical edges
    for row in range(5):
        for col in range(5):
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    # If no legal moves (shouldn't happen in a valid game), return any (but shouldn't occur)
    if not legal_moves:
        return "0,0,H"  # fallback (should not reach here)
    
    # For each legal move, check what happens if we play it
    winning_moves = []      # completes at least one box
    dangerous_moves = []    # completes exactly 3 sides of at least one box (but not more, which could be good)
    safe_moves = []         # completes 0 boxes (no side becomes the 3rd of any box)
    
    for r, c, d in legal_moves:
        completes_boxes = 0
        is_dangerous = False
        
        if d == 'H':  # horizontal edge at (r,c)
            # This edge is the top of box (r-1, c) and bottom of box (r, c)
            # Check box above: (r-1, c) if r > 0
            if r > 0:
                # Check the 4 sides of box (r-1, c): top=horizontal[r-1,c], bottom=horizontal[r,c], left=vertical[r-1,c], right=vertical[r-1,c+1]
                top = horizontal[r-1, c]
                bottom = horizontal[r, c]  # this is the move
                left = vertical[r-1, c]
                right = vertical[r-1, c+1]
                sides = [top, bottom, left, right]
                if sum(1 for s in sides if s != 0) == 3:  # exactly 3 sides filled
                    is_dangerous = True
                if sum(1 for s in sides if s != 0) == 4:  # box is completed
                    completes_boxes += 1
            
            # Check box below: (r, c) if r < 4
            if r < 4:
                top = horizontal[r, c]  # this is the move
                bottom = horizontal[r+1, c]
                left = vertical[r, c]
                right = vertical[r, c+1]
                sides = [top, bottom, left, right]
                if sum(1 for s in sides if s != 0) == 3:
                    is_dangerous = True
                if sum(1 for s in sides if s != 0) == 4:
                    completes_boxes += 1
            
        else:  # d == 'V', vertical edge at (r,c)
            # This edge is the left of box (r, c-1) and right of box (r, c)
            # Check box to left: (r, c-1) if c > 0
            if c > 0:
                left = vertical[r, c-1]
                right = vertical[r, c]  # this is the move
                top = horizontal[r, c-1]
                bottom = horizontal[r+1, c-1]
                sides = [top, bottom, left, right]
                if sum(1 for s in sides if s != 0) == 3:
                    is_dangerous = True
                if sum(1 for s in sides if s != 0) == 4:
                    completes_boxes += 1
            
            # Check box to right: (r, c) if c < 4
            if c < 4:
                left = vertical[r, c]  # this is the move
                right = vertical[r, c+1]
                top = horizontal[r, c]
                bottom = horizontal[r+1, c]
                sides = [top, bottom, left, right]
                if sum(1 for s in sides if s != 0) == 3:
                    is_dangerous = True
                if sum(1 for s in sides if s != 0) == 4:
                    completes_boxes += 1
        
        if completes_boxes > 0:
            winning_moves.append((r, c, d))
        elif is_dangerous:
            dangerous_moves.append((r, c, d))
        else:
            safe_moves.append((r, c, d))
    
    # Strategy: prioritize winning moves, then safe moves, then avoid dangerous if possible
    if winning_moves:
        # Return the first winning move (deterministic ordering)
        move = winning_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    if safe_moves:
        # Return the first safe move
        move = safe_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # If no safe or winning moves, must choose a dangerous move (only one left)
    # We choose the dangerous move that completes the fewest boxes (should be 1)
    # and prefer lower indices for determinism
    dangerous_moves.sort(key=lambda x: (x[0], x[1]))  # sort by row, then col
    move = dangerous_moves[0]
    return f"{move[0]},{move[1]},{move[2]}"
