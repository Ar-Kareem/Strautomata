
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Create a flattened version of the board for easier access
    flattened = board_np.flatten()
    legal_moves_set = set(legal_moves)
    
    # Convert each legal move index to (row, col)
    possible_moves = [(move // 3, move % 3) for move in legal_moves if flattened[move] != 1]
    
    def evaluate_move(r, c):
        """Evaluate the strategic value of a move at (r,c)"""
        # Weight for position (center > corners > edges)
        position_weights = {
            (1,1): 4,  # center
            (0,0): 3, (0,2): 3, (2,0): 3, (2,2): 3,  # corners
            (0,1): 2, (1,0): 2, (1,2): 2, (2,1): 2   # edges
        }
        
        # Calculate strategic value
        value = position_weights[(r,c)]
        
        # Check if this move creates a potential win
        # Check row
        row = board_np[r,:]
        if (row == 1).sum() == 2 and row[c] != 1:
            value += 10
            
        # Check column
        col = board_np[:,c]
        if (col == 1).sum() == 2 and col[r] != 1:
            value += 10
            
        # Check diagonals if applicable
        if r == c:
            diag1 = board_np.diagonal()
            if (diag1 == 1).sum() == 2 and diag1[r] != 1:
                value += 10
        if r + c == 2:
            diag2 = np.fliplr(board_np).diagonal()
            if (diag2 == 1).sum() == 2 and diag2[r] != 1:
                value += 10
                
        # Check potential blocking moves
        # We'll consider positions where the opponent might have 2 in a line
        # and assign higher value to these (since even if we can't confirm,
        # it's good to block potential threats)
        total_row = len([x for x in row if x != -1])
        total_col = len([x for x in col if x != -1])
        if total_row == 2 and row[c] != 1:
            value += 5
        if total_col == 2 and col[r] != 1:
            value += 5
            
        return value
    
    if not possible_moves:
        # Shouldn't happen if API is correct, but fallback
        move = legal_moves[0]
        return (move // 3, move % 3)
    
    # Evaluate all possible moves
    evaluated_moves = [(r, c, evaluate_move(r, c)) for (r, c) in possible_moves]
    
    # Find the move with maximum value
    best_move = max(evaluated_moves, key=lambda x: x[2])
    return (best_move[0], best_move[1])
