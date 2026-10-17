
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy for 4x4 grid.
    
    Strategy:
    1. Complete boxes when possible (immediate points + extra turn)
    2. Avoid creating 3-sided boxes for opponent
    3. When forced to sacrifice, choose the least damaging move
    
    Returns:
        str: Move in format 'row,col,dir' (e.g., '0,0,H' or '1,2,V')
    """
    
    # Find all available moves (empty edges)
    available_moves = []
    
    # Check horizontal edges (5x5 array, edges between columns)
    for row in range(5):
        for col in range(4):  # horizontal edges: 0-3 in columns
            if horizontal[row, col] == 0:
                available_moves.append((row, col, 'H'))
    
    # Check vertical edges (5x5 array, edges between rows)
    for row in range(4):  # vertical edges: 0-3 in rows
        for col in range(5):
            if vertical[row, col] == 0:
                available_moves.append((row, col, 'V'))
    
    # Helper function to check if a box is completed by a move
    def check_box_completion(move_row, move_col, move_dir):
        """Count how many boxes this move would complete"""
        completed_boxes = 0
        
        if move_dir == 'H':
            # Horizontal edge affects boxes above and below
            # Box above: (move_row-1, move_col)
            if move_row > 0:
                # Check if this horizontal edge completes the bottom of box above
                if horizontal[move_row-1, move_col] != 0 and vertical[move_row-1, move_col] != 0 and vertical[move_row-1, move_col+1] != 0:
                    if capture[move_row-1, move_col] == 0:
                        completed_boxes += 1
            
            # Box below: (move_row, move_col)
            if move_row < 4:
                # Check if this horizontal edge completes the top of box below
                if horizontal[move_row+1, move_col] != 0 and vertical[move_row, move_col] != 0 and vertical[move_row, move_col+1] != 0:
                    if capture[move_row, move_col] == 0:
                        completed_boxes += 1
                        
        else:  # move_dir == 'V'
            # Vertical edge affects boxes to the left and right
            # Box to the left: (move_row, move_col-1)
            if move_col > 0:
                # Check if this vertical edge completes the right side of box to left
                if vertical[move_row, move_col-1] != 0 and horizontal[move_row, move_col-1] != 0 and horizontal[move_row+1, move_col-1] != 0:
                    if capture[move_row, move_col-1] == 0:
                        completed_boxes += 1
            
            # Box to the right: (move_row, move_col)
            if move_col < 4:
                # Check if this vertical edge completes the left side of box to right
                if vertical[move_row, move_col+1] != 0 and horizontal[move_row, move_col] != 0 and horizontal[move_row+1, move_col] != 0:
                    if capture[move_row, move_col] == 0:
                        completed_boxes += 1
        
        return completed_boxes
    
    # Helper function to check if a move creates a 3-sided box for opponent
    def creates_threat(move_row, move_col, move_dir):
        """Check if this move creates a 3-sided box (threat for opponent)"""
        boxes_to_check = []
        
        if move_dir == 'H':
            # Check box above
            if move_row > 0:
                boxes_to_check.append((move_row-1, move_col))
            # Check box below
            if move_row < 4:
                boxes_to_check.append((move_row, move_col))
        else:  # move_dir == 'V'
            # Check box to the left
            if move_col > 0:
                boxes_to_check.append((move_row, move_col-1))
            # Check box to the right
            if move_col < 4:
                boxes_to_check.append((move_row, move_col))
        
        # Count how many boxes would have exactly 3 sides after this move
        threats_created = 0
        
        for box_row, box_col in boxes_to_check:
            if capture[box_row, box_col] != 0:  # Already captured
                continue
                
            # Count sides that will be filled after this move
            sides_filled = 0
            
            # Top edge (horizontal)
            if horizontal[box_row, box_col] != 0:
                sides_filled += 1
            if move_dir == 'H' and box_row == move_row - 1 and move_col == box_col:
                sides_filled += 1
            
            # Bottom edge (horizontal)
            if horizontal[box_row + 1, box_col] != 0:
                sides_filled += 1
            if move_dir == 'H' and box_row == move_row and move_col == box_col:
                sides_filled += 1
            
            # Left edge (vertical)
            if vertical[box_row, box_col] != 0:
                sides_filled += 1
            if move_dir == 'V' and box_row == box_row and box_col == move_col - 1:
                sides_filled += 1
            
            # Right edge (vertical)
            if vertical[box_row, box_col + 1] != 0:
                sides_filled += 1
            if move_dir == 'V' and box_row == box_row and box_col == move_col:
                sides_filled += 1
            
            if sides_filled == 3:  # Creates a 3-sided box
                threats_created += 1
        
        return threats_created
    
    # Step 1: Prioritize moves that complete boxes (immediate points + extra turn)
    completing_moves = []
    for move_row, move_col, move_dir in available_moves:
        if check_box_completion(move_row, move_col, move_dir) > 0:
            completing_moves.append((move_row, move_col, move_dir))
    
    if completing_moves:
        # Return the first completing move (any is good)
        return f"{completing_moves[0][0]},{completing_moves[0][1]},{completing_moves[0][2]}"
    
    # Step 2: Avoid creating 3-sided boxes when possible
    safe_moves = []
    threatening_moves = []
    
    for move_row, move_col, move_dir in available_moves:
        if creates_threat(move_row, move_col, move_dir) == 0:
            safe_moves.append((move_row, move_col, move_dir))
        else:
            threatening_moves.append((move_row, move_col, move_dir))
    
    if safe_moves:
        # Among safe moves, prefer those that don't create future threats
        # Simple approach: return first safe move
        return f"{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}"
    
    # Step 3: Forced to make a threatening move - choose least damaging
    # Evaluate all moves and pick the one that minimizes opponent gains
    best_move = None
    min_threats = float('inf')
    
    for move_row, move_col, move_dir in threatening_moves:
        threats = creates_threat(move_row, move_col, move_dir)
        if threats < min_threats:
            min_threats = threats
            best_move = (move_row, move_col, move_dir)
    
    if best_move:
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    # Fallback: should never reach here if moves are available
    return f"{available_moves[0][0]},{available_moves[0][1]},{available_moves[0][2]}"
