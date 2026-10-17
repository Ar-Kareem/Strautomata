
import numpy as np
from collections import deque

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Find all positions where we have pieces
    your_pieces = np.argwhere(you == 1)
    
    # Find all legal moves
    legal_moves = []
    
    # For each of our pieces, check all four directions
    for row, col in your_pieces:
        # Check up
        if row > 0 and opponent[row-1, col] == 1:
            legal_moves.append((row, col, 'U'))
        # Check right
        if col < 5 and opponent[row, col+1] == 1:
            legal_moves.append((row, col, 'R'))
        # Check down
        if row < 4 and opponent[row+1, col] == 1:
            legal_moves.append((row, col, 'D'))
        # Check left
        if col > 0 and opponent[row, col-1] == 1:
            legal_moves.append((row, col, 'L'))
    
    # Score moves based on simple heuristic
    best_move = None
    best_score = -1
    
    for start_row, start_col, direction in legal_moves:
        # Basic scoring - prioritize capturing opponent pieces
        # We can improve this by looking at future mobility
        
        # For now, simple approach: pick first valid move
        # But we should check if this might lead to disadvantageous situations
        
        # A more sophisticated approach would be:
        # 1. Capture closest opponent pieces
        # 2. Prefer moves that give us mobility
        # 3. Avoid moves that leave us isolated
        
        # Let's try a simple heuristic:
        # - Prefer moves that don't leave our pieces isolated
        # - Prefer moves towards center if possible
        
        # Simplest valid implementation for now:
        if best_move is None:
            best_move = (start_row, start_col, direction)
    
    # If we have no moves available (shouldn't happen per problem statement)
    if best_move is None:
        # Fallback
        start_row, start_col, direction = legal_moves[0]
        return f"{start_row},{start_col},{direction}"
    
    start_row, start_col, direction = best_move
    return f"{start_row},{start_col},{direction}"
