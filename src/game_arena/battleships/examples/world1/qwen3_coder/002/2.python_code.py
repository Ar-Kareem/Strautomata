
import random
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Look for hits that haven't been sunk yet
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:  # Hit ship
                hits.append((r, c))
    
    # If we have hits, focus on sinking those ships
    if hits:
        # For each hit, try adjacent cells
        candidates = set()
        for r, c in hits:
            # Check if this hit is part of a horizontal or vertical line
            horizontal_line = False
            vertical_line = False
            
            # Check left/right neighbors for horizontal continuation
            left_hit = (r, c-1) in hits if c > 0 else False
            right_hit = (r, c+1) in hits if c < 9 else False
            if left_hit or right_hit:
                horizontal_line = True
                
            # Check up/down neighbors for vertical continuation  
            up_hit = (r-1, c) in hits if r > 0 else False
            down_hit = (r+1, c) in hits if r < 9 else False
            if up_hit or down_hit:
                vertical_line = True
            
            # Continue in the direction of the line first
            if horizontal_line:
                # Check left and right
                if c > 0 and board[r][c-1] == 0:
                    candidates.add((r, c-1))
                if c < 9 and board[r][c+1] == 0:
                    candidates.add((r, c+1))
            elif vertical_line:
                # Check up and down
                if r > 0 and board[r-1][c] == 0:
                    candidates.add((r-1, c))
                if r < 9 and board[r+1][c] == 0:
                    candidates.add((r+1, c))
            else:
                # No clear direction, check all 4 directions
                if r > 0 and board[r-1][c] == 0:
                    candidates.add((r-1, c))  # Up
                if r < 9 and board[r+1][c] == 0:
                    candidates.add((r+1, c))  # Down
                if c > 0 and board[r][c-1] == 0:
                    candidates.add((r, c-1))  # Left
                if c < 9 and board[r][c+1] == 0:
                    candidates.add((r, c+1))  # Right
        
        # Return first candidate if found
        if candidates:
            # Prefer candidates that continue a clear line if possible
            return list(candidates)[0]
    
    # Hunting phase - no hits yet or no good adjacent cells
    # Use parity strategy to maximize search efficiency
    # Ships of length 2+ mean we can skip every other cell initially
    
    # Try checkerboard pattern with offset consideration
    # We'll use a pattern that hits cells where (row + col) % 2 == 0
    # But we want to be more systematic
    
    # Scan the board systematically but with a smarater pattern
    valid_moves = []
    
    # Do a smarter sweep - spiral or priority-based
    # Try to maximize potential hits by avoiding obvious misses where possible
    
    for parity in [0, 1]:  # Try both checkerboard patterns
        for r in range(10):
            for c in range(10):
                if (r + c) % 2 == parity and board[r][c] == 0:
                    # Additional heuristic: prefer center area for opening moves
                    valid_moves.append((r, c))
    
    if valid_moves:
        # Sort by "preference" - center positions more likely to have ships
        def center_preference(pos):
            r, c = pos
            center_distance = abs(r - 4.5) + abs(c - 4.5)  # Distance from center
            return center_distance
        
        valid_moves.sort(key=center_preference)
        return valid_moves[0]
    
    # Fallback: random selection among unknown cells
    unknown_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                unknown_cells.append((r, c))
    
    if unknown_cells:
        return random.choice(unknown_cells)
    
    # Should never get here since the game would be over
    return (0, 0)
