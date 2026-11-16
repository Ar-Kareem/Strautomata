
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Smart 4x4 Tic Tac Toe policy.
    
    Args:
        board: 4x4 list of lists where 0=empty, 1=our move, -1=opponent move
        
    Returns:
        Tuple of (row, col) for next move
    """
    # Convert to numpy for easier manipulation
    b = np.array(board)
    
    # Get all empty positions
    empty_positions = []
    for i in range(4):
        for j in range(4):
            if b[i, j] == 0:
                empty_positions.append((i, j))
    
    # Helper to check if a player can win in one move
    def can_win(player):
        # Check rows
        for i in range(4):
            row = b[i, :]
            if np.sum(row == player) == 3 and np.sum(row == 0) == 1:
                return (i, np.where(row == 0)[0][0])
        
        # Check columns
        for j in range(4):
            col = b[:, j]
            if np.sum(col == player) == 3 and np.sum(col == 0) == 1:
                return (np.where(col == 0)[0][0], j)
        
        # Check diagonals
        diag1 = np.diag(b)
        if np.sum(diag1 == player) == 3 and np.sum(diag1 == 0) == 1:
            idx = np.where(diag1 == 0)[0][0]
            return (idx, idx)
            
        diag2 = np.diag(np.fliplr(b))
        if np.sum(diag2 == player) == 3 and np.sum(diag2 == 0) == 1:
            idx = np.where(diag2 == 0)[0][0]
            return (idx, 3-idx)
        
        return None
    
    # 1. Check if we can win
    win_move = can_win(1)
    if win_move:
        return win_move
    
    # 2. Check if opponent can win and block
    block_move = can_win(-1)
    if block_move:
        return block_move
    
    # 3. Score each empty position
    def score_position(r, c):
        score = 0
        
        # Check row
        row = b[r, :]
        if np.sum(row == 1) > 0 and np.sum(row == -1) == 0:
            score += np.sum(row == 1)
        elif np.sum(row == -1) > 0 and np.sum(row == 1) == 0:
            score += np.sum(row == -1) * 0.5
        
        # Check column
        col = b[:, c]
        if np.sum(col == 1) > 0 and np.sum(col == -1) == 0:
            score += np.sum(col == 1)
        elif np.sum(col == -1) > 0 and np.sum(col == 1) == 0:
            score += np.sum(col == -1) * 0.5
        
        # Check main diagonal (if on it)
        if r == c:
            diag = np.diag(b)
            if np.sum(diag == 1) > 0 and np.sum(diag == -1) == 0:
                score += np.sum(diag == 1)
            elif np.sum(diag == -1) > 0 and np.sum(diag == 1) == 0:
                score += np.sum(diag == -1) * 0.5
        
        # Check anti-diagonal (if on it)
        if r + c == 3:
            diag = np.diag(np.fliplr(b))
            if np.sum(diag == 1) > 0 and np.sum(diag == -1) == 0:
                score += np.sum(diag == 1)
            elif np.sum(diag == -1) > 0 and np.sum(diag == 1) == 0:
                score += np.sum(diag == -1) * 0.5
        
        # Position preference: center > corners > edges
        if (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]:  # Center
            score += 2
        elif (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]:  # Corners
            score += 1.5
        else:  # Edges
            score += 1
            
        return score
    
    # Calculate scores for all empty positions
    scores = [(score_position(r, c), r, c) for r, c in empty_positions]
    
    # Sort by score (descending)
    scores.sort(reverse=True)
    
    # Return the best move
    return (scores[0][1], scores[0][2])
