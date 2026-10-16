
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    rows, cols = horizontal.shape
    
    # Add all horizontal edges that are unclaimed
    for r in range(rows):
        for c in range(cols):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
    
    # Add all vertical edges that are unclaimed
    for r in range(rows):
        for c in range(cols):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))
    
    # Shuffle to randomize move selection among ties
    random.shuffle(legal_moves)
    
    capturing_moves = []
    for move in legal_moves:
        r, c, dir = move
        captures = 0
        if dir == 'H':
            # Box above (if exists)
            if r > 0 and capture[r-1, c] == 0:
                # Check other edges of box (top, left, right)
                if horizontal[r-1, c] != 0 and vertical[r-1, c] != 0 and vertical[r-1, c+1] != 0:
                    captures += 1
            # Box below (if exists)
            if r < 4 and capture[r, c] == 0:
                if horizontal[r+1, c] != 0 and vertical[r, c] != 0 and vertical[r, c+1] != 0:
                    captures += 1
        elif dir == 'V':
            # Box to the left (if exists)
            if c > 0 and capture[r, c-1] == 0:
                if horizontal[r, c-1] != 0 and horizontal[r+1, c-1] != 0 and vertical[r, c-1] != 0:
                    captures += 1
            # Box to the right (if exists)
            if c < 4 and capture[r, c] == 0:
                if horizontal[r, c] != 0 and horizontal[r+1, c] != 0 and vertical[r, c+1] != 0:
                    captures += 1
        if captures > 0:
            capturing_moves.append((move, captures))
    
    # If capturing moves available, pick the one with max captures
    if capturing_moves:
        capturing_moves.sort(key=lambda x: x[1], reverse=True)
        best_captures = capturing_moves[0][1]
        best_options = [m for m, cap in capturing_moves if cap == best_captures]
        move = random.choice(best_options)  # Randomize among ties
        return f"{move[0][0]},{move[0][1]},{move[0][2]}"
    
    # Evaluate danger for non-capturing moves (count boxes with 3 edges)
    danger_scores = []
    for move in legal_moves:
        r, c, dir = move
        danger = 0
        
        if dir == 'H':
            # Box above
            if r > 0 and capture[r-1, c] == 0:
                edges_filled = 1  # Current move
                if horizontal[r-1, c] != 0:
                    edges_filled += 1
                if vertical[r-1, c] != 0:
                    edges_filled += 1
                if vertical[r-1, c+1] != 0:
                    edges_filled += 1
                if edges_filled == 3:
                    danger += 1
            # Box below
            if r < 4 and capture[r, c] == 0:
                edges_filled = 1  # Current move
                if horizontal[r+1, c] != 0:
                    edges_filled += 1
                if vertical[r, c] != 0:
                    edges_filled += 1
                if vertical[r, c+1] != 0:
                    edges_filled += 1
                if edges_filled == 3:
                    danger += 1
        
        else:  # 'V' direction
            # Box to the left
            if c > 0 and capture[r, c-1] == 0:
                edges_filled = 1  # Current move
                if horizontal[r, c-1] != 0:
                    edges_filled += 1
                if horizontal[r+1, c-1] != 0:
                    edges_filled += 1
                if vertical[r, c-1] != 0:
                    edges_filled += 1
                if edges_filled == 3:
                    danger += 1
            # Box to the right
            if c < 4 and capture[r, c] == 0:
                edges_filled = 1  # Current move
                if horizontal[r, c] != 0:
                    edges_filled += 1
                if horizontal[r+1, c] != 0:
                    edges_filled += 1
                if vertical[r, c+1] != 0:
                    edges_filled += 1
                if edges_filled == 3:
                    danger += 1
        
        danger_scores.append((move, danger))
    
    # Select move with minimum danger
    min_danger = min(danger_scores, key=lambda x: x[1])[1]
    safe_moves = [m for m, d in danger_scores if d == min_danger]
    chosen_move = random.choice(safe_moves)[0]  # Randomize among safest
    return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"
