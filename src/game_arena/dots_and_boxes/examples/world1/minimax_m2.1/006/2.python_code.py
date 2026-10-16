
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart policy for Dots and Boxes on a 4x4 grid.
    
    Strategy priorities:
    1. Complete boxes if possible (immediate extra turn)
    2. Avoid creating 3-sided boxes (gives opponent points)
    3. Create threats when possible
    4. Minimize damage when forced to make a bad move
    """
    
    def get_empty_edges():
        """Get all legal moves (empty edges)"""
        moves = []
        
        # Horizontal edges: valid at rows 0-4, cols 0-3
        for row in range(5):
            for col in range(4):
                if horizontal[row, col] == 0:
                    moves.append((row, col, 'H'))
        
        # Vertical edges: valid at rows 0-3, cols 0-4
        for row in range(4):
            for col in range(5):
                if vertical[row, col] == 0:
                    moves.append((row, col, 'V'))
        
        return moves
    
    def count_box_sides(row, col):
        """Count how many sides are already drawn for a box at (row, col)"""
        sides = 0
        
        # Top edge (horizontal at row, col)
        if horizontal[row, col] != 0:
            sides += 1
        
        # Bottom edge (horizontal at row+1, col)
        if horizontal[row + 1, col] != 0:
            sides += 1
        
        # Left edge (vertical at row, col)
        if vertical[row, col] != 0:
            sides += 1
        
        # Right edge (vertical at row, col+1)
        if vertical[row, col + 1] != 0:
            sides += 1
        
        return sides
    
    def get_boxes_completed_by_move(move):
        """Return the number of boxes that would be completed by making this move"""
        row, col, direction = move
        count = 0
        
        if direction == 'H':
            # This edge could complete boxes above (row-1, col) and below (row, col)
            if row > 0 and capture[row - 1, col] == 0:
                # Check if this completes the box above
                sides = count_box_sides(row - 1, col)
                if sides == 3:  # After adding this edge, it will be complete
                    count += 1
            
            if row < 4 and capture[row, col] == 0:
                # Check if this completes the box below
                sides = count_box_sides(row, col)
                if sides == 3:
                    count += 1
                    
        else:  # 'V'
            # This edge could complete boxes to the left (row, col-1) and right (row, col)
            if col > 0 and capture[row, col - 1] == 0:
                sides = count_box_sides(row, col - 1)
                if sides == 3:
                    count += 1
            
            if col < 4 and capture[row, col] == 0:
                sides = count_box_sides(row, col)
                if sides == 3:
                    count += 1
        
        return count
    
    def creates_three_sided_box(move):
        """Check if this move would create a 3-sided box (dangerous)"""
        row, col, direction = move
        
        if direction == 'H':
            # Could create 3-sided box above or below
            if row > 0 and capture[row - 1, col] == 0:
                sides = count_box_sides(row - 1, col)
                if sides == 2:  # After adding, it becomes 3
                    return True
            
            if row < 4 and capture[row, col] == 0:
                sides = count_box_sides(row, col)
                if sides == 2:
                    return True
                    
        else:  # 'V'
            if col > 0 and capture[row, col - 1] == 0:
                sides = count_box_sides(row, col - 1)
                if sides == 2:
                    return True
            
            if col < 4 and capture[row, col] == 0:
                sides = count_box_sides(row, col)
                if sides == 2:
                    return True
        
        return False
    
    def evaluate_move(move):
        """Evaluate a move and return a score (higher is better)"""
        row, col, direction = move
        
        boxes_completed = get_boxes_completed_by_move(move)
        creates_three = creates_three_sided_box(move)
        
        # Base score: prioritize moves that complete boxes
        if boxes_completed >= 2:
            score = 1000 + boxes_completed * 100  # Double box completion is amazing
        elif boxes_completed == 1:
            score = 500  # Single box completion is very good
        else:
            # No box completion - consider other factors
            if creates_three:
                score = -1000  # Avoid creating 3-sided boxes at all costs
            else:
                # Look for moves that create threats (set up future captures)
                score = 100
                
                # Prefer edges that are part of multiple potential boxes
                if direction == 'H':
                    # Count how many boxes this edge borders
                    bordering_boxes = 0
                    if row > 0:
                        bordering_boxes += 1
                    if row < 4:
                        bordering_boxes += 1
                    score += bordering_boxes * 10
                else:
                    bordering_boxes = 0
                    if col > 0:
                        bordering_boxes += 1
                    if col < 4:
                        bordering_boxes += 1
                    score += bordering_boxes * 10
                
                # Prefer edges that are closer to center (more strategic)
                if direction == 'H':
                    center_dist = abs(row - 2) + abs(col - 1.5)
                else:
                    center_dist = abs(row - 1.5) + abs(col - 2)
                score -= center_dist * 2
        
        return score
    
    # Get all legal moves
    moves = get_empty_edges()
    
    if not moves:
        # No moves available - shouldn't happen, but handle gracefully
        return "0,0,H"
    
    # Find the best move
    best_move = None
    best_score = float('-inf')
    
    for move in moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        # Fallback to first legal move
        best_move = moves[0]
    
    row, col, direction = best_move
    return f"{row},{col},{direction}"
