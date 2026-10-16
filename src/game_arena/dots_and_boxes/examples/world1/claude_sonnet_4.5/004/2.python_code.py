
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy using strategic principles.
    """
    
    def count_box_edges(row, col):
        """Count how many edges a box already has."""
        if row < 0 or row > 3 or col < 0 or col > 3:
            return 4  # Out of bounds
        count = 0
        if horizontal[row, col] != 0:
            count += 1
        if horizontal[row + 1, col] != 0:
            count += 1
        if vertical[row, col] != 0:
            count += 1
        if vertical[row, col + 1] != 0:
            count += 1
        return count
    
    def completes_box(row, col, is_horizontal):
        """Check if a move completes any boxes."""
        completed = []
        if is_horizontal:
            # Check box above
            if row > 0 and capture[row - 1, col] == 0:
                if count_box_edges(row - 1, col) == 3:
                    completed.append((row - 1, col))
            # Check box below
            if row < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 3:
                    completed.append((row, col))
        else:  # vertical
            # Check box to the left
            if col > 0 and capture[row, col - 1] == 0:
                if count_box_edges(row, col - 1) == 3:
                    completed.append((row, col - 1))
            # Check box to the right
            if col < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 3:
                    completed.append((row, col))
        return completed
    
    def creates_three_sided_box(row, col, is_horizontal):
        """Check if a move creates a 3-sided box (dangerous)."""
        count = 0
        if is_horizontal:
            # Check box above
            if row > 0 and capture[row - 1, col] == 0:
                if count_box_edges(row - 1, col) == 2:
                    count += 1
            # Check box below
            if row < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 2:
                    count += 1
        else:  # vertical
            # Check box to the left
            if col > 0 and capture[row, col - 1] == 0:
                if count_box_edges(row, col - 1) == 2:
                    count += 1
            # Check box to the right
            if col < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 2:
                    count += 1
        return count
    
    # Get all legal moves
    legal_moves = []
    
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    if not legal_moves:
        # Fallback (should never happen)
        return "0,0,H"
    
    # Categorize moves
    capturing_moves = []
    safe_moves = []
    dangerous_moves = []
    
    for row, col, direction in legal_moves:
        is_h = (direction == 'H')
        completed_boxes = completes_box(row, col, is_h)
        
        if completed_boxes:
            capturing_moves.append((row, col, direction, len(completed_boxes)))
        else:
            danger_count = creates_three_sided_box(row, col, is_h)
            if danger_count == 0:
                safe_moves.append((row, col, direction))
            else:
                dangerous_moves.append((row, col, direction, danger_count))
    
    # Priority 1: Capture boxes if available
    if capturing_moves:
        # Take the move that captures the most boxes
        capturing_moves.sort(key=lambda x: x[3], reverse=True)
        row, col, direction, _ = capturing_moves[0]
        return f"{row},{col},{direction}"
    
    # Priority 2: Play safe moves
    if safe_moves:
        row, col, direction = safe_moves[0]
        return f"{row},{col},{direction}"
    
    # Priority 3: No safe moves left - play least dangerous move
    if dangerous_moves:
        dangerous_moves.sort(key=lambda x: x[3])
        row, col, direction, _ = dangerous_moves[0]
        return f"{row},{col},{direction}"
    
    # Fallback: play first legal move
    row, col, direction = legal_moves[0]
    return f"{row},{col},{direction}"
