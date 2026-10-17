
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy for 4x4 grid.
    
    Strategy:
    1. Capture boxes greedily when possible
    2. Avoid creating 3-sided boxes (giving opponent easy captures)
    3. When forced to sacrifice, minimize the number of 3-sided boxes created
    4. Use positional heuristics for tiebreaking
    """
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        return "0,0,H"
    
    # Priority 1: Capture boxes if possible
    capturing_moves = []
    for move in legal_moves:
        boxes = count_boxes_captured(move, horizontal, vertical, capture)
        if boxes > 0:
            capturing_moves.append((move, boxes))
    
    if capturing_moves:
        # Take the move that captures the most boxes
        best_move = max(capturing_moves, key=lambda x: x[1])[0]
        return format_move(best_move)
    
    # Priority 2: Avoid creating 3-sided boxes
    safe_moves = [move for move in legal_moves 
                  if not creates_three_sided_box(move, horizontal, vertical, capture)]
    
    if safe_moves:
        return format_move(choose_best_safe_move(safe_moves))
    
    # Priority 3: Minimize damage when forced to sacrifice
    return format_move(choose_sacrifice_move(legal_moves, horizontal, vertical, capture))


def get_legal_moves(horizontal, vertical):
    """Return all legal moves as (row, col, is_horizontal) tuples."""
    moves = []
    # Horizontal edges: row in [0,4], col in [0,3]
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                moves.append((row, col, True))
    # Vertical edges: row in [0,3], col in [0,4]
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                moves.append((row, col, False))
    return moves


def format_move(move):
    """Format move as 'row,col,dir' string."""
    row, col, is_horizontal = move
    return f"{row},{col},{'H' if is_horizontal else 'V'}"


def count_filled_edges(box_row, box_col, horizontal, vertical):
    """Count how many edges of a box are filled."""
    count = 0
    if horizontal[box_row, box_col] != 0:
        count += 1
    if horizontal[box_row + 1, box_col] != 0:
        count += 1
    if vertical[box_row, box_col] != 0:
        count += 1
    if vertical[box_row, box_col + 1] != 0:
        count += 1
    return count


def count_boxes_captured(move, horizontal, vertical, capture):
    """Count how many boxes this move would complete."""
    row, col, is_horizontal = move
    count = 0
    
    if is_horizontal:
        # Check box below (this edge is its top)
        if row < 4 and capture[row, col] == 0:
            if count_filled_edges(row, col, horizontal, vertical) == 3:
                count += 1
        # Check box above (this edge is its bottom)
        if row > 0 and capture[row - 1, col] == 0:
            if count_filled_edges(row - 1, col, horizontal, vertical) == 3:
                count += 1
    else:  # vertical
        # Check box to right (this edge is its left)
        if col < 4 and capture[row, col] == 0:
            if count_filled_edges(row, col, horizontal, vertical) == 3:
                count += 1
        # Check box to left (this edge is its right)
        if col > 0 and capture[row, col - 1] == 0:
            if count_filled_edges(row, col - 1, horizontal, vertical) == 3:
                count += 1
    
    return count


def creates_three_sided_box(move, horizontal, vertical, capture):
    """Check if this move creates any 3-sided boxes."""
    row, col, is_horizontal = move
    
    # Simulate the move
    h_copy = horizontal.copy()
    v_copy = vertical.copy()
    if is_horizontal:
        h_copy[row, col] = 1
    else:
        v_copy[row, col] = 1
    
    # Check adjacent boxes
    boxes_to_check = []
    if is_horizontal:
        if row < 4:
            boxes_to_check.append((row, col))
        if row > 0:
            boxes_to_check.append((row - 1, col))
    else:
        if col < 4:
            boxes_to_check.append((row, col))
        if col > 0:
            boxes_to_check.append((row, col - 1))
    
    for box_row, box_col in boxes_to_check:
        if capture[box_row, box_col] != 0:
            continue
        if count_filled_edges(box_row, box_col, h_copy, v_copy) == 3:
            return True
    
    return False


def choose_best_safe_move(safe_moves):
    """Choose the best move among safe moves (prefer central positions)."""
    def score(move):
        row, col, is_h = move
        # Prefer positions closer to center
        if is_h:
            distance = abs(row - 2.5) + abs(col - 1.5)
        else:
            distance = abs(row - 1.5) + abs(col - 2.5)
        return -distance
    
    return max(safe_moves, key=score)


def choose_sacrifice_move(legal_moves, horizontal, vertical, capture):
    """Choose the least damaging move when all moves create 3-sided boxes."""
    def score(move):
        row, col, is_h = move
        h_copy = horizontal.copy()
        v_copy = vertical.copy()
        if is_h:
            h_copy[row, col] = 1
        else:
            v_copy[row, col] = 1
        
        # Count 3-sided boxes after this move
        three_sided_count = 0
        for br in range(4):
            for bc in range(4):
                if capture[br, bc] == 0:
                    if count_filled_edges(br, bc, h_copy, v_copy) == 3:
                        three_sided_count += 1
        
        # Tiebreaker: prefer central positions
        if is_h:
            distance = abs(row - 2.5) + abs(col - 1.5)
        else:
            distance = abs(row - 1.5) + abs(col - 2.5)
        
        return (three_sided_count, distance)
    
    return min(legal_moves, key=score)
