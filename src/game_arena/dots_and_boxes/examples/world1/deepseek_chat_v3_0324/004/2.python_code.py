
import numpy as np
from collections import defaultdict

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # First check for any immediate box completions
    for row in range(4):
        for col in range(4):
            # Check if we can complete this box
            if capture[row, col] != 0:
                continue
                
            # Count existing edges
            top = horizontal[row, col]
            bottom = horizontal[row+1, col]
            left = vertical[row, col]
            right = vertical[row, col+1]
            edges = [top, bottom, left, right]
            
            # If exactly 3 edges are filled, we can complete the box
            if sum(1 for e in edges if e != 0) == 3:
                # Find the missing edge
                if top == 0:
                    return f"{row},{col},H"
                if bottom == 0:
                    return f"{row+1},{col},H"
                if left == 0:
                    return f"{row},{col},V"
                if right == 0:
                    return f"{row},{col+1},V"
    
    # Find all potential moves that would create exactly 3-sided boxes
    dangerous_moves = set()
    safe_moves = []
    
    # Check horizontal edges
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                # Check if this would create any 3-sided boxes
                dangerous = False
                if row > 0:  # Check box above
                    top = horizontal[row-1, col] if row > 0 else 1
                    bottom = 1  # this edge
                    left = vertical[row-1, col] if row > 0 else 1
                    right = vertical[row-1, col+1] if row > 0 else 1
                    if sum(1 for e in [top, bottom, left, right] if e != 0) == 3:
                        dangerous = True
                
                if row < 4:  # Check box below
                    top = 1  # this edge
                    bottom = horizontal[row+1, col] if row < 4 else 1
                    left = vertical[row, col] if row < 4 else 1
                    right = vertical[row, col+1] if row < 4 else 1
                    if sum(1 for e in [top, bottom, left, right] if e != 0) == 3:
                        dangerous = True
                
                if dangerous:
                    dangerous_moves.add(f"{row},{col},H")
                else:
                    safe_moves.append(f"{row},{col},H")
    
    # Check vertical edges
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                # Check if this would create any 3-sided boxes
                dangerous = False
                if col > 0:  # Check box to the left
                    top = horizontal[row, col-1] if col > 0 else 1
                    bottom = horizontal[row+1, col-1] if col > 0 else 1
                    left = vertical[row, col-1] if col > 0 else 1
                    right = 1  # this edge
                    if sum(1 for e in [top, bottom, left, right] if e != 0) == 3:
                        dangerous = True
                
                if col < 4:  # Check box to the right
                    top = horizontal[row, col] if col < 4 else 1
                    bottom = horizontal[row+1, col] if col < 4 else 1
                    left = 1  # this edge
                    right = vertical[row, col+1] if col < 4 else 1
                    if sum(1 for e in [top, bottom, left, right] if e != 0) == 3:
                        dangerous = True
                
                if dangerous:
                    dangerous_moves.add(f"{row},{col},V")
                else:
                    safe_moves.append(f"{row},{col},V")
    
    # Prefer safe moves if available
    if safe_moves:
        # Among safe moves, prefer those that create two boxes at once
        for move in safe_moves:
            parts = move.split(',')
            row, col = int(parts[0]), int(parts[1])
            dir = parts[2]
            
            if dir == 'H':
                boxes_created = 0
                if 0 < row < 5:
                    # Check both boxes above and below
                    if row > 0 and capture[row-1, col] == 0:
                        boxes_created += 1
                    if row < 4 and capture[row, col] == 0:
                        boxes_created += 1
                if boxes_created == 2:
                    return move
        
        # Otherwise return a random safe move
        return safe_moves[np.random.randint(0, len(safe_moves))]
    
    # If we must make a dangerous move, try to minimize the damage
    if dangerous_moves:
        # Try to find a move that creates only one dangerous box
        best_move = None
        min_danger = float('inf')
        
        for move in dangerous_moves:
            parts = move.split(',')
            row, col = int(parts[0]), int(parts[1])
            dir = parts[2]
            
            danger_count = 0
            if dir == 'H':
                if row > 0 and capture[row-1, col] == 0:
                    danger_count += 1
                if row < 4 and capture[row, col] == 0:
                    danger_count += 1
            else:  # 'V'
                if col > 0 and capture[row, col-1] == 0:
                    danger_count += 1
                if col < 4 and capture[row, col] == 0:
                    danger_count += 1
            
            if danger_count < min_danger:
                min_danger = danger_count
                best_move = move
            elif danger_count == min_danger:
                # Prefer moves that might lead to double-cross opportunities
                if dir == 'H' and (row == 0 or row == 4):
                    best_move = move
                elif dir == 'V' and (col == 0 or col == 4):
                    best_move = move
        
        if best_move:
            return best_move
        
        # Fallback: return first dangerous move if all else fails
        return list(dangerous_moves)[0]
    
    # Fallback: return any legal move (shouldn't reach here in normal play)
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                return f"{row},{col},H"
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                return f"{row},{col},V"
    
    # Should never reach here if game isn't over
    return "0,0,H"
