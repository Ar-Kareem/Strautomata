
import numpy as np

def policy(horizontal, vertical, capture):
    # Find all legal moves
    legal_moves = []  # list of (dir, r, c)
    
    # Horizontal moves: dir='H', r from 0 to 4, c from 0 to 3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                legal_moves.append(('H', r, c))
    # Vertical moves: dir='V', r from 0 to 3, c from 0 to 4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                legal_moves.append(('V', r, c))
    
    if not legal_moves:
        # No legal moves, return a dummy move (should not happen in a valid game state)
        return '0,0,H'
    
    # For each move, compute completed_count and new_three_count
    moves_info = []  # list of (move, completed, new_three)
    for move in legal_moves:
        dir, r, c = move
        completed = 0
        new_three = 0
        
        # Find affected boxes
        affected_boxes = []
        if dir == 'H':
            # The edge can be the top edge of the box below it, if any
            if r < 4 and c < 4:
                affected_boxes.append((r, c))
            # The edge can be the bottom edge of the box above it, if any
            if r > 0 and c < 4:
                affected_boxes.append((r-1, c))
        else:  # dir == 'V'
            # The edge can be the left edge of the box to the right, if any
            if r < 4 and c < 4:
                affected_boxes.append((r, c))
            # The edge can be the right edge of the box to the left, if any
            if r < 4 and c > 0:
                affected_boxes.append((r, c-1))
        
        for (i, j) in affected_boxes:
            # Count the current number of drawn edges for box (i, j)
            count = 0
            # Top edge: horizontal[i, j]
            if horizontal[i, j] != 0:
                count += 1
            # Bottom edge: horizontal[i+1, j]
            if horizontal[i+1, j] != 0:
                count += 1
            # Left edge: vertical[i, j]
            if vertical[i, j] != 0:
                count += 1
            # Right edge: vertical[i, j+1]
            if vertical[i, j+1] != 0:
                count += 1
            
            # After the move, this box will have one more edge
            new_count = count + 1
            
            if new_count == 4:
                completed += 1
            elif new_count == 3 and count == 2:
                new_three += 1
        
        moves_info.append((move, completed, new_three))
    
    # Select the best move
    # First, consider moves that complete at least one box
    max_completed = max(info[1] for info in moves_info)
    if max_completed > 0:
        # Among moves that complete the most boxes, choose the one that creates the fewest three-edge boxes
        candidates = [info for info in moves_info if info[1] == max_completed]
        best_candidate = min(candidates, key=lambda x: x[2])
        best_move = best_candidate[0]
    else:
        # No move completes a box, look for moves that create no new three-edge boxes
        safe_moves = [info for info in moves_info if info[2] == 0]
        if safe_moves:
            # Choose the first safe move (or any)
            best_move = safe_moves[0][0]
        else:
            # All moves create new three-edge boxes, choose the one that creates the fewest
            best_candidate = min(moves_info, key=lambda x: x[2])
            best_move = best_candidate[0]
    
    # Format the move as string
    dir, r, c = best_move
    return f"{r},{c},{dir}"
