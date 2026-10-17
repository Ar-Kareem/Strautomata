
import numpy as np
from typing import List
import random

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    you_arr = np.array(you, dtype=int)
    opponent_arr = np.array(opponent, dtype=int)
    rows, cols = you_arr.shape
    legal_moves = []
    
    # Directions: U, R, D, L
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    for row in range(rows):
        for col in range(cols):
            if you_arr[row, col] == 1:
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < rows and 0 <= new_col < cols:
                        if opponent_arr[new_row, new_col] == 1:
                            legal_moves.append((row, col, dir))
    
    # If no legal moves (shouldn't happen per rules), but handle just in case
    if not legal_moves:
        return "0,0,U"  # fallback (should never be reached)
    
    # Evaluate each move by opponent's mobility after the move
    best_move = None
    best_opponent_mobility = float('inf')
    
    for move in legal_moves:
        row, col, dir = move
        new_row, new_col = row, col
        if dir == 'U':
            new_row -= 1
        elif dir == 'D':
            new_row += 1
        elif dir == 'L':
            new_col -= 1
        elif dir == 'R':
            new_col += 1
        
        # Simulate the move
        new_you = you_arr.copy()
        new_opponent = opponent_arr.copy()
        new_you[row, col] = 0
        new_you[new_row, new_col] = 1
        new_opponent[new_row, new_col] = 0
        
        # Calculate opponent's mobility after this move
        opponent_mobility = 0
        for opp_row in range(rows):
            for opp_col in range(cols):
                if new_opponent[opp_row, opp_col] == 1:
                    for dr, dc, _ in directions:
                        nr, nc = opp_row + dr, opp_col + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if new_you[nr, nc] == 1:
                                opponent_mobility += 1
        
        if opponent_mobility < best_opponent_mobility:
            best_opponent_mobility = opponent_mobility
            best_move = move
    
    # If multiple moves have the same opponent mobility, pick randomly
    best_moves = [m for m in legal_moves if 
                  np.all([m[0] == best_move[0], m[1] == best_move[1], m[2] == best_move[2]]) or 
                  (best_opponent_mobility == float('inf'))]
    
    if not best_moves:
        best_moves = legal_moves
    
    # Randomly select among best moves (or all if no best)
    selected_move = random.choice(best_moves)
    return f"{selected_move[0]},{selected_move[1]},{selected_move[2]}"
