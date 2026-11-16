
import numpy as np
from collections import defaultdict

def policy(horizontal, vertical, capture):
    # First, check for any immediate box completions
    move = find_forced_move(horizontal, vertical)
    if move:
        return move
    
    # Then look for safe moves that don't create 3-sided boxes
    move = find_safe_move(horizontal, vertical)
    if move:
        return move
    
    # If no safe moves, find the move that creates the fewest 3-sided boxes
    move = find_least_dangerous_move(horizontal, vertical)
    if move:
        return move
    
    # As last resort, return any legal move (shouldn't happen in normal play)
    return find_any_legal_move(horizontal, vertical)

def find_forced_move(horizontal, vertical):
    # Check for any edges that would complete a box
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if row < 4 and horizontal[row, col] == 0:
                # Check boxes above and below
                boxes = []
                if row > 0:
                    boxes.append((row-1, col))
                if row < 4:
                    boxes.append((row, col))
                
                for (r, c) in boxes:
                    if is_box_completing_move(horizontal, vertical, r, c, row, col, 'H'):
                        return f"{row},{col},H"
            
            # Check vertical edges
            if col < 4 and vertical[row, col] == 0:
                # Check boxes to left and right
                boxes = []
                if col > 0:
                    boxes.append((row, col-1))
                if col < 4:
                    boxes.append((row, col))
                
                for (r, c) in boxes:
                    if is_box_completing_move(horizontal, vertical, r, c, row, col, 'V'):
                        return f"{row},{col},V"
    return None

def is_box_completing_move(horizontal, vertical, box_row, box_col, edge_row, edge_col, direction):
    # Count how many sides are already filled (excluding our potential move)
    sides = 0
    
    # Top edge
    if box_row > 0 and horizontal[box_row, box_col] != 0:
        sides += 1
    # Bottom edge
    if box_row < 4 and horizontal[box_row+1, box_col] != 0:
        sides += 1
    # Left edge
    if box_col > 0 and vertical[box_row, box_col] != 0:
        sides += 1
    # Right edge
    if box_col < 4 and vertical[box_row, box_col+1] != 0:
        sides += 1
    
    # Check if our move would be the 4th side
    if direction == 'H':
        if (edge_row == box_row and edge_col == box_col) or (edge_row == box_row+1 and edge_col == box_col):
            return sides == 3
    elif direction == 'V':
        if (edge_row == box_row and edge_col == box_col) or (edge_row == box_row and edge_col == box_col+1):
            return sides == 3
    
    return False

def find_safe_move(horizontal, vertical):
    # Find moves that don't create 3-sided boxes
    safe_moves = []
    
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if row < 4 and horizontal[row, col] == 0:
                if not creates_three_sided_box(horizontal, vertical, row, col, 'H'):
                    safe_moves.append(f"{row},{col},H")
            
            # Check vertical edges
            if col < 4 and vertical[row, col] == 0:
                if not creates_three_sided_box(horizontal, vertical, row, col, 'V'):
                    safe_moves.append(f"{row},{col},V")
    
    if safe_moves:
        # Prefer moves that are part of fewer potential boxes
        return min(safe_moves, key=lambda m: count_potential_boxes(m, horizontal, vertical))
    return None

def creates_three_sided_box(horizontal, vertical, row, col, direction):
    if direction == 'H':
        # Check box above
        if row > 0:
            top = horizontal[row-1, col] != 0
            left = vertical[row-1, col] != 0
            right = vertical[row-1, col+1] != 0
            if top + left + right == 2:
                return True
        
        # Check box below
        if row < 4:
            bottom = horizontal[row+1, col] != 0
            left = vertical[row, col] != 0
            right = vertical[row, col+1] != 0
            if bottom + left + right == 2:
                return True
    
    elif direction == 'V':
        # Check box to left
        if col > 0:
            left = vertical[row, col-1] != 0
            top = horizontal[row, col-1] != 0
            bottom = horizontal[row+1, col-1] != 0
            if left + top + bottom == 2:
                return True
        
        # Check box to right
        if col < 4:
            right = vertical[row, col+1] != 0
            top = horizontal[row, col] != 0
            bottom = horizontal[row+1, col] != 0
            if right + top + bottom == 2:
                return True
    
    return False

def count_potential_boxes(move, horizontal, vertical):
    # Count how many potential boxes this edge is part of
    parts = move.split(',')
    row, col = int(parts[0]), int(parts[1])
    direction = parts[2]
    
    count = 0
    if direction == 'H':
        if row > 0:
            count += 1
        if row < 4:
            count += 1
    else:  # 'V'
        if col > 0:
            count += 1
        if col < 4:
            count += 1
    return count

def find_least_dangerous_move(horizontal, vertical):
    # Find the move that creates the fewest 3-sided boxes
    moves = []
    
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if row < 4 and horizontal[row, col] == 0:
                danger = count_three_sided_boxes_created(horizontal, vertical, row, col, 'H')
                moves.append((danger, f"{row},{col},H"))
            
            # Check vertical edges
            if col < 4 and vertical[row, col] == 0:
                danger = count_three_sided_boxes_created(horizontal, vertical, row, col, 'V')
                moves.append((danger, f"{row},{col},V"))
    
    if moves:
        # Return the move with least danger
        moves.sort()
        return moves[0][1]
    return None

def count_three_sided_boxes_created(horizontal, vertical, row, col, direction):
    count = 0
    if direction == 'H':
        # Check box above
        if row > 0:
            top = horizontal[row-1, col] != 0
            left = vertical[row-1, col] != 0
            right = vertical[row-1, col+1] != 0
            if top + left + right == 2:
                count += 1
        
        # Check box below
        if row < 4:
            bottom = horizontal[row+1, col] != 0
            left = vertical[row, col] != 0
            right = vertical[row, col+1] != 0
            if bottom + left + right == 2:
                count += 1
    
    elif direction == 'V':
        # Check box to left
        if col > 0:
            left = vertical[row, col-1] != 0
            top = horizontal[row, col-1] != 0
            bottom = horizontal[row+1, col-1] != 0
            if left + top + bottom == 2:
                count += 1
        
        # Check box to right
        if col < 4:
            right = vertical[row, col+1] != 0
            top = horizontal[row, col] != 0
            bottom = horizontal[row+1, col] != 0
            if right + top + bottom == 2:
                count += 1
    
    return count

def find_any_legal_move(horizontal, vertical):
    # As a fallback, find any legal move (shouldn't be needed in normal play)
    for row in range(5):
        for col in range(5):
            if row < 4 and horizontal[row, col] == 0:
                return f"{row},{col},H"
            if col < 4 and vertical[row, col] == 0:
                return f"{row},{col},V"
    return "0,0,H"  # should never happen
