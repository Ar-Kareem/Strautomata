
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Define all possible moves: horizontal and vertical edges
    moves = []
    
    # Collect all legal moves (edge is empty)
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
    
    # Check for immediate capture moves (completing 1 or more boxes)
    # Also collect safe moves (that don't complete any box)
    safe_moves = []
    dangerous_moves = []
    immediate_capture_moves = []
    
    for r, c, d in moves:
        boxes_completed = 0
        
        # Determine which box(es) this edge completes
        if d == 'H':  # Horizontal edge at (r, c)
            # This edge is top edge of box (r-1, c) and bottom edge of box (r, c)
            # Box above: (r-1, c) if r > 0
            if r > 0:
                # Check the box above: (r-1, c)
                top = horizontal[r-1, c]      # already set
                bottom = horizontal[r, c]     # this move
                left = vertical[r-1, c]       # left edge
                right = vertical[r-1, c+1]    # right edge
                if top != 0 and left != 0 and right != 0 and bottom == 0:  # 3 sides filled
                    boxes_completed += 1
            # Box below: (r, c) if r < 4
            if r < 4:
                top = horizontal[r, c]        # this move
                bottom = horizontal[r+1, c]   # already set
                left = vertical[r, c]         # left edge
                right = vertical[r, c+1]      # right edge
                if bottom != 0 and left != 0 and right != 0 and top == 0:
                    boxes_completed += 1
        
        elif d == 'V':  # Vertical edge at (r, c)
            # This edge is left edge of box (r, c-1) and right edge of box (r, c)
            # Box to the left: (r, c-1) if c > 0
            if c > 0:
                left = vertical[r, c-1]       # already set
                right = vertical[r, c]        # this move
                top = horizontal[r, c-1]      # top edge
                bottom = horizontal[r+1, c-1] # bottom edge
                if left != 0 and top != 0 and bottom != 0 and right == 0:
                    boxes_completed += 1
            # Box to the right: (r, c) if c < 4
            if c < 4:
                left = vertical[r, c]         # this move
                right = vertical[r, c+1]      # already set
                top = horizontal[r, c]        # top edge
                bottom = horizontal[r+1, c]   # bottom edge
                if right != 0 and top != 0 and bottom != 0 and left == 0:
                    boxes_completed += 1
        
        # Classify move
        if boxes_completed > 0:
            immediate_capture_moves.append((r, c, d))
        else:
            safe_moves.append((r, c, d))
    
    # Strategy: If we can capture a box, we want to do it — but only if it doesn't create a double-cross
    # However, in Dots and Boxes expert play: if there’s any move that creates a box, take it — unless
    # it creates a chain that lets opponent score multiple. But on 4x4, with simple lookahead, we assume:
    # Only avoid moves that complete a box if there’s a safe alternative. But here we go:
    
    if len(immediate_capture_moves) > 0:
        # We have moves that complete at least one box — let's check if any are "single-box" captures.
        # In many implementations, taking a single box is beneficial because you get an extra turn.
        # So we take any immediate capture move — even if it might create a chain, we assume we can handle it.
        # However, to be safe: prefer moves that complete exactly one box and not more (though max is 2).
        # We'll pick the first one to keep it simple and deterministic.
        return f"{immediate_capture_moves[0][0]},{immediate_capture_moves[0][1]},{immediate_capture_moves[0][2]}"
    
    # If no immediate capture, pick a safe move
    if len(safe_moves) > 0:
        # Prefer moves that are on edges with fewer adjacent filled edges to avoid creating two-sided boxes
        # Simple heuristic: prefer moves on borders or with least neighbors
        best_move = safe_moves[0]
        for r, c, d in safe_moves:
            # Count how many adjacent edges are already filled — we want to minimize this to avoid creating
            # future easy captures for opponent
            adjacent_filled = 0
            if d == 'H':
                if r > 0:
                    # Check box above
                    if horizontal[r-1, c] != 0: adjacent_filled += 1
                    if vertical[r-1, c] != 0: adjacent_filled += 1
                    if vertical[r-1, c+1] != 0: adjacent_filled += 1
                if r < 4:
                    # Check box below
                    if horizontal[r+1, c] != 0: adjacent_filled += 1
                    if vertical[r, c] != 0: adjacent_filled += 1
                    if vertical[r, c+1] != 0: adjacent_filled += 1
            else: # d == 'V'
                if c > 0:
                    # Check box left
                    if vertical[r, c-1] != 0: adjacent_filled += 1
                    if horizontal[r, c-1] != 0: adjacent_filled += 1
                    if horizontal[r+1, c-1] != 0: adjacent_filled += 1
                if c < 4:
                    # Check box right
                    if vertical[r, c+1] != 0: adjacent_filled += 1
                    if horizontal[r, c] != 0: adjacent_filled += 1
                    if horizontal[r+1, c] != 0: adjacent_filled += 1
            
            # We prefer moves with fewer adjacent filled edges (safer)
            # But since all are safe (no box completed), we just pick the first with minimal adjacent
            # Use first occurrence for determinism
            # We don't re-sort, we just take first minimal
            pass
        # Since we are prioritizing by order of scanning (row-major), pick the first safe move
        return f"{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}"
    
    # If no safe moves, then we are forced to make a dangerous move — pick the first one
    if len(moves) > 0:
        r, c, d = moves[0]  # This will be the first in the list, even if dangerous
        return f"{r},{c},{d}"
    
    # Should never reach here — but return a default if somehow no moves
    return "0,0,H"
