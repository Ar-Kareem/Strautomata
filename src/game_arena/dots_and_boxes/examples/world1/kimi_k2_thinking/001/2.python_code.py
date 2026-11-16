
import numpy as np

def policy(horizontal, vertical, capture):
    """
    Advanced Dots and Boxes policy for 4x4 grid.
    
    Strategy:
    1. Greedy Capture: Always take any available boxes, preferring moves that
       capture multiple boxes (double-crosses, etc.)
    2. Safe Play: Avoid moves that complete the third side of any box,
       which would give opponent a scoring opportunity
    3. Minimal Sacrifice: When forced, sacrifice the fewest boxes to opponent
    4. Board Control: Among safe moves, prefer edges in open areas with
       fewer adjacent edges to maintain flexibility
    
    Returns: move string in format 'row,col,dir'
    """
    # Get all legal moves
    moves = get_legal_moves(horizontal, vertical)
    
    if not moves:
        # Emergency fallback - game should be over, but return valid format
        return "0,0,H"
    
    # Priority 1: Capture boxes
    capture_moves = [(move, len(boxes_captured_by_move(move, horizontal, vertical))) 
                     for move in moves]
    capture_moves = [(m, c) for m, c in capture_moves if c > 0]
    
    if capture_moves:
        # Choose move capturing most boxes
        capture_moves.sort(key=lambda x: x[1], reverse=True)
        move = capture_moves[0][0]
        return format_move(move)
    
    # Priority 2: Safe moves (don't give boxes)
    safe_moves = [m for m in moves if not gives_boxes_to_opponent(m, horizontal, vertical)]
    
    if safe_moves:
        # Choose safest move (fewest adjacent edges)
        move = min(safe_moves, key=lambda m: adjacent_edge_count(m, horizontal, vertical))
        return format_move(move)
    
    # Priority 3: Minimize sacrifice
    sacrifice_scores = [(move, count_boxes_given(move, horizontal, vertical)) 
                        for move in moves]
    sacrifice_scores.sort(key=lambda x: x[1])  # Fewer boxes = better
    move = sacrifice_scores[0][0]
    return format_move(move)

def get_legal_moves(horizontal, vertical):
    """Return list of all legal (row, col, dir) moves."""
    moves = []
    
    # Horizontal edges: 5 rows, 4 columns (valid)
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    
    # Vertical edges: 4 rows, 5 columns (valid)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
    
    return moves

def format_move(move):
    """Convert move tuple to string format."""
    return f"{move[0]},{move[1]},{move[2]}"

def boxes_captured_by_move(move, horizontal, vertical):
    """Return list of boxes captured by this move."""
    r, c, dir = move
    captured = []
    
    if dir == 'H':
        # Box above: (r-1, c), exists if r > 0
        if r > 0:
            if (horizontal[r-1, c] != 0 and vertical[r-1, c] != 0 and vertical[r-1, c+1] != 0):
                captured.append((r-1, c))
        
        # Box below: (r, c), exists if r < 4
        if r < 4:
            if (horizontal[r+1, c] != 0 and vertical[r, c] != 0 and vertical[r, c+1] != 0):
                captured.append((r, c))
    
    else:  # 'V'
        # Box left: (r, c-1), exists if c > 0
        if c > 0:
            if (vertical[r, c-1] != 0 and horizontal[r, c-1] != 0 and horizontal[r+1, c-1] != 0):
                captured.append((r, c-1))
        
        # Box right: (r, c), exists if c < 4
        if c < 4:
            if (vertical[r, c+1] != 0 and horizontal[r, c] != 0 and horizontal[r+1, c] != 0):
                captured.append((r, c))
    
    return captured

def gives_boxes_to_opponent(move, horizontal, vertical):
    """
    Check if move completes the 3rd side of any box.
    Returns True if opponent could capture next turn.
    """
    r, c, dir = move
    
    if dir == 'H':
        # Box above: (r-1, c), our move is bottom edge
        if r > 0:
            sides = 0
            if horizontal[r-1, c] != 0: sides += 1
            if vertical[r-1, c] != 0: sides += 1
            if vertical[r-1, c+1] != 0: sides += 1
            if sides == 2:  # 2 other sides drawn → our move is 3rd
                return True
        
        # Box below: (r, c), our move is top edge
        if r < 4:
            sides = 0
            if horizontal[r+1, c] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1
            if vertical[r, c+1] != 0: sides += 1
            if sides == 2:
                return True
    
    else:  # 'V'
        # Box left: (r, c-1), our move is right edge
        if c > 0:
            sides = 0
            if vertical[r, c-1] != 0: sides += 1
            if horizontal[r, c-1] != 0: sides += 1
            if horizontal[r+1, c-1] != 0: sides += 1
            if sides == 2:
                return True
        
        # Box right: (r, c), our move is left edge
        if c < 4:
            sides = 0
            if vertical[r, c+1] != 0: sides += 1
            if horizontal[r, c] != 0: sides += 1
            if horizontal[r+1, c] != 0: sides += 1
            if sides == 2:
                return True
    
    return False

def count_boxes_given(move, horizontal, vertical):
    """Count boxes this move would give to opponent (completes 3rd side)."""
    r, c, dir = move
    count = 0
    
    if dir == 'H':
        if r > 0:
            sides = 0
            if horizontal[r-1, c] != 0: sides += 1
            if vertical[r-1, c] != 0: sides += 1
            if vertical[r-1, c+1] != 0: sides += 1
            if sides == 2:
                count += 1
        
        if r < 4:
            sides = 0
            if horizontal[r+1, c] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1
            if vertical[r, c+1] != 0: sides += 1
            if sides == 2:
                count += 1
    
    else:  # 'V'
        if c > 0:
            sides = 0
            if vertical[r, c-1] != 0: sides += 1
            if horizontal[r, c-1] != 0: sides += 1
            if horizontal[r+1, c-1] != 0: sides += 1
            if sides == 2:
                count += 1
        
        if c < 4:
            sides = 0
            if vertical[r, c+1] != 0: sides += 1
            if horizontal[r, c] != 0: sides += 1
            if horizontal[r+1, c] != 0: sides += 1
            if sides == 2:
                count += 1
    
    return count

def adjacent_edge_count(move, horizontal, vertical):
    """Count adjacent edges to prioritize moves in open areas."""
    r, c, dir = move
    count = 0
    
    if dir == 'H':
        if r > 0 and vertical[r-1, c] != 0:
            count += 1
        if r < 4 and vertical[r, c] != 0:
            count += 1
        if c > 0 and horizontal[r, c-1] != 0:
            count += 1
        if c < 3 and horizontal[r, c+1] != 0:
            count += 1
    else:  # 'V'
        if c > 0 and horizontal[r, c-1] != 0:
            count += 1
        if c < 4 and horizontal[r, c] != 0:
            count += 1
        if r > 0 and vertical[r-1, c] != 0:
            count += 1
        if r < 3 and vertical[r+1, c] != 0:
            count += 1
    
    return count
