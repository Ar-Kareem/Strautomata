
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Collect all legal moves
    legal_moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    if not legal_moves:
        return None  # Should not happen as per problem statement
    
    capturing_moves = []
    non_capturing_moves = []
    
    for move in legal_moves:
        row, col, dir = move
        affected_boxes = []
        
        # Determine affected boxes for the current move
        if dir == 'H':
            if row > 0 and col < 4:
                affected_boxes.append((row-1, col))
            if row < 4 and col < 4:
                affected_boxes.append((row, col))
        else:
            if col > 0 and row < 4:
                affected_boxes.append((row, col-1))
            if col < 4 and row < 4:
                affected_boxes.append((row, col))
        
        num_captures = 0
        danger = 0
        for (i, j) in affected_boxes:
            if capture[i, j] != 0:
                continue  # Box already captured
            
            # Count currently filled edges for the box
            top = horizontal[i, j] != 0
            bottom = horizontal[i+1, j] != 0
            left = vertical[i, j] != 0
            right = vertical[i, j+1] != 0
            current = top + bottom + left + right
            
            # New edge adds to current count
            new_count = current + 1
            
            if new_count == 4:
                num_captures += 1
            elif new_count == 3:
                danger += 1
        
        if num_captures > 0:
            capturing_moves.append((move, num_captures))
        else:
            non_capturing_moves.append((move, danger))
    
    # Select best move
    if capturing_moves:
        # Choose move with maximum captures, break ties randomly
        max_captures = max(c for (_, c) in capturing_moves)
        best_moves = [m for m, c in capturing_moves if c == max_captures]
        chosen = random.choice(best_moves)
    else:
        # Choose move with minimum danger, break ties randomly
        if not non_capturing_moves:
            # Fallback, should not occur since legal_moves is non-empty
            chosen = legal_moves[0]
        else:
            min_danger = min(d for (_, d) in non_capturing_moves)
            best_moves = [m for m, d in non_capturing_moves if d == min_danger]
            chosen = random.choice(best_moves)
    
    row, col, dir = chosen
    return f"{row},{col},{dir}"
