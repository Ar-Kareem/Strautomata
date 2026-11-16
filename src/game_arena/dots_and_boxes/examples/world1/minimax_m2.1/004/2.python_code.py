
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy for 4x4 grid.
    Prioritizes: 1) Box completion, 2) Avoiding 3-sided boxes, 3) Strategic edge control
    """
    # Get all legal moves
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        # No legal moves (shouldn't happen unless game over)
        return "0,0,H"
    
    # Priority 1: Check for moves that complete boxes (immediate wins)
    winning_moves = get_winning_moves(horizontal, vertical, capture, legal_moves)
    if winning_moves:
        # Choose the winning move that creates the most boxes or has best chain potential
        return select_best_winning_move(winning_moves, horizontal, vertical, capture)
    
    # Priority 2: Avoid creating 3-sided boxes (which give opponent free points)
    safe_moves = get_safe_moves(horizontal, vertical, capture, legal_moves)
    if safe_moves:
        # Among safe moves, prefer those that might lead to future opportunities
        return select_best_safe_move(safe_moves, horizontal, vertical, capture, capture)
    
    # Priority 3: If no safe moves, minimize damage
    return select_min_damage_move(legal_moves, horizontal, vertical, capture)

def get_legal_moves(horizontal, vertical):
    """Get all legal moves (empty edges)"""
    moves = []
    # Horizontal edges: rows 0-4, cols 0-4
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                moves.append((row, col, 'H'))
    # Vertical edges: rows 0-4, cols 0-4
    for row in range(5):
        for col in range(5):
            if vertical[row, col] == 0:
                moves.append((row, col, 'V'))
    return moves

def count_box_sides(row, col, horizontal, vertical):
    """Count how many sides of box (row, col) are already drawn"""
    if row < 0 or row > 3 or col < 0 or col > 3:
        return -1
    
    sides_drawn = 0
    # Top edge (horizontal[row, col])
    if horizontal[row, col] != 0:
        sides_drawn += 1
    # Bottom edge (horizontal[row+1, col])
    if horizontal[row+1, col] != 0:
        sides_drawn += 1
    # Left edge (vertical[row, col])
    if vertical[row, col] != 0:
        sides_drawn += 1
    # Right edge (vertical[row, col+1])
    if vertical[row, col+1] != 0:
        sides_drawn += 1
    
    return sides_drawn

def get_empty_sides(row, col, horizontal, vertical):
    """Get list of empty side indices for box (row, col)"""
    if row < 0 or row > 3 or col < 0 or col > 3:
        return []
    
    empty_sides = []
    # Top edge (horizontal[row, col]) -> side 0
    if horizontal[row, col] == 0:
        empty_sides.append(0)
    # Bottom edge (horizontal[row+1, col]) -> side 1
    if horizontal[row+1, col] == 0:
        empty_sides.append(1)
    # Left edge (vertical[row, col]) -> side 2
    if vertical[row, col] == 0:
        empty_sides.append(2)
    # Right edge (vertical[row, col+1]) -> side 3
    if vertical[row, col+1] == 0:
        empty_sides.append(3)
    
    return empty_sides

def simulate_move(row, col, direction, horizontal, vertical, capture):
    """Simulate a move and return resulting state"""
    # Make copies
    h_copy = horizontal.copy()
    v_copy = vertical.copy()
    c_copy = capture.copy()
    
    # Place the edge
    if direction == 'H':
        h_copy[row, col] = 1
    else:
        v_copy[row, col] = 1
    
    # Check for completed boxes
    boxes_completed = []
    for box_row in range(4):
        for box_col in range(4):
            # Check if this box is now complete
            sides = count_box_sides(box_row, box_col, h_copy, v_copy)
            if sides == 4 and c_copy[box_row, box_col] == 0:
                c_copy[box_row, box_col] = 1
                boxes_completed.append((box_row, box_col))
    
    return h_copy, v_copy, c_copy, boxes_completed

def get_winning_moves(horizontal, vertical, capture, legal_moves):
    """Get moves that complete at least one box"""
    winning = []
    for row, col, direction in legal_moves:
        _, _, _, boxes = simulate_move(row, col, direction, horizontal, vertical, capture)
        if boxes:  # Move completes at least one box
            winning.append((row, col, direction, len(boxes), boxes))
    
    return winning

def select_best_winning_moves(winning_moves, horizontal, vertical, capture):
    """Select the best winning move, prioritizing more boxes and chain potential"""
    # Sort by: 1) number of boxes completed, 2) chain potential (boxes that would have 1 side left)
    winning_moves.sort(key=lambda x: (-x[3], -count_chain_potential(x[4], horizontal, vertical, capture)))
    return f"{winning_moves[0][0]},{winning_moves[0][1]},{winning_moves[0][2]}"

def count_chain_potential(just_completed, horizontal, vertical, capture):
    """Count how many boxes would have exactly 1 side left after completing these boxes"""
    potential = 0
    for box_row, box_col in just_completed:
        # Check adjacent boxes that might now have 1 empty side
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            adj_row, adj_col = box_row + dr, box_col + dc
            if 0 <= adj_row < 4 and 0 <= adj_col < 4:
                if capture[adj_row, adj_col] == 0:  # Not already captured
                    empty = get_empty_sides(adj_row, adj_col, horizontal, vertical)
                    # After completing 'just_completed', check if adj would have 1 empty side
                    # This is complex, so we'll use a simpler heuristic
                    pass
    
    # Simple heuristic: just return number of boxes completed
    return len(just_completed)

def get_safe_moves(horizontal, vertical, capture, legal_moves):
    """Get moves that don't create 3-sided boxes for opponent"""
    safe = []
    for row, col, direction in legal_moves:
        creates_three_sided = False
        h_new, v_new, c_new, boxes = simulate_move(row, col, direction, horizontal, vertical, capture)
        
        # Check if this move creates any 3-sided boxes for opponent
        for box_row in range(4):
            for box_col in range(4):
                if c_new[box_row, box_col] == 0:  # Box not captured
                    sides = count_box_sides(box_row, box_col, h_new, v_new)
                    if sides == 3:
                        creates_three_sided = True
                        break
            if creates_three_sided:
                break
        
        if not creates_three_sided:
            safe.append((row, col, direction, len(boxes)))
    
    return safe

def select_best_safe_move(safe_moves, horizontal, vertical, capture):
    """Select best safe move using heuristic evaluation"""
    # Score each move: prefer moves that might complete boxes or lead to good positions
    scored = []
    for row, col, direction, boxes_completed in safe_moves:
        score = boxes_completed * 100  # Completed boxes are very valuable
        
        # Bonus for being near unclaimed territory
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = row + dr, col + dc
                if 0 <= nr < 4 and 0 <= nc < 4 and capture[nr, nc] == 0:
                    score += 5  # Near unclaimed boxes
        
        # Bonus for edge control (center edges are more valuable)
        center_bonus = 0
        if direction == 'H':
            center_bonus = min(row, 4-row) + min(col, 4-col)
        else:
            center_bonus = min(row, 4-row) + min(col, 4-col)
        score += center_bonus
        
        scored.append((score, row, col, direction))
    
    scored.sort(reverse=True)
    return f"{scored[0][1]},{scored[0][2]},{scored[0][3]}"

def select_min_damage_move(legal_moves, horizontal, vertical, capture):
    """When no safe moves, choose move that gives opponent least opportunity"""
    best_move = None
    best_score = float('-inf')
    
    for row, col, direction in legal_moves:
        h_new, v_new, c_new, boxes = simulate_move(row, col, direction, horizontal, vertical, capture)
        
        # Score: negative of boxes opponent could get from our mistake
        opponent_boxes = 0
        three_sided_count = 0
        
        for box_row in range(4):
            for box_col in range(4):
                if c_new[box_row, box_col] == 0:
                    sides = count_box_sides(box_row, box_col, h_new, v_new)
                    if sides == 3:
                        three_sided_count += 1
                        opponent_boxes += 1  # Opponent can take this
        
        # Lower is better for opponent_boxes and three_sided_count
        # So we negate them for scoring
        score = -opponent_boxes * 100 - three_sided_count * 50
        
        # Add small positive for any boxes we completed
        score += len(boxes) * 100
        
        # Prefer moves that keep options open
        score += len(get_legal_moves(h_new, v_new)) * 0.1
        
        if score > best_score:
            best_score = score
            best_move = (row, col, direction)
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def select_best_winning_move(winning_moves, horizontal, vertical, capture):
    """Select the best winning move"""
    # Prioritize moves that complete more boxes
    winning_moves.sort(key=lambda x: -x[3])
    return f"{winning_moves[0][0]},{winning_moves[0][1]},{winning_moves[0][2]}"

def select_best_safe_move(safe_moves, horizontal, vertical, capture):
    """Select the best safe move"""
    if not safe_moves:
        return None
    
    # Score safe moves
    best_idx = 0
    best_score = float('-inf')
    
    for idx, (row, col, direction, boxes) in enumerate(safe_moves):
        score = boxes * 100  # Completed boxes are most important
        
        # Prefer center positions for control
        center_dist = abs(row - 2) + abs(col - 2)
        score -= center_dist * 2
        
        # Prefer moves that are part of longer potential chains
        chain_score = 0
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = row + dr, col + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    if capture[nr, nc] == 0:
                        empty_sides = get_empty_sides(nr, nc, horizontal, vertical)
                        if len(empty_sides) <= 2:  # Near-completion boxes
                            chain_score += (3 - len(empty_sides)) * 10
        
        score += chain_score
        
        if score > best_score:
            best_score = score
            best_idx = idx
    
    row, col, direction, boxes = safe_moves[best_idx]
    return f"{row},{col},{direction}"
