
import numpy as np
from itertools import product

def policy(board) -> str:
    # Find all our amazons
    amazons = np.argwhere(board == 1)
    
    best_move = None
    best_score = -float('inf')
    
    for amazon in amazons:
        from_row, from_col = amazon
        # Get all possible moves for this amazon
        moves = get_queen_moves(board, from_row, from_col)
        
        for to_row, to_col in moves:
            # Temporarily move the amazon
            board[from_row, from_col] = 0
            board[to_row, to_col] = 1
            
            # Get all possible arrow shots from new position
            arrows = get_queen_moves(board, to_row, to_col)
            
            for arrow_row, arrow_col in arrows:
                # Calculate score for this complete move
                score = evaluate_move(board, from_row, from_col, 
                                    to_row, to_col, arrow_row, arrow_col)
                
                if score > best_score:
                    best_score = score
                    best_move = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
            
            # Revert the temporary move
            board[to_row, to_col] = 0
            board[from_row, from_col] = 1
    
    return best_move

def get_queen_moves(board, row, col):
    """Get all possible queen moves from (row,col) on empty board"""
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),          (0,1),
                  (1,-1),  (1,0),  (1,1)]
    moves = []
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r, c] != 0:
                break
            moves.append((r, c))
            r += dr
            c += dc
    
    return moves

def evaluate_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col):
    """Evaluate the quality of a potential move"""
    # Mobility score: how many moves does our amazon have after moving
    mobility = len(get_queen_moves(board, to_row, to_col))
    
    # Arrow impact: how many squares does this arrow block
    board[arrow_row, arrow_col] = -1
    arrow_blocking = 0
    for dr, dc in [(-1,-1), (-1,0), (-1,1),
                   (0,-1),          (0,1),
                   (1,-1), (1,0), (1,1)]:
        r, c = arrow_row + dr, arrow_col + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r, c] != 0:
                break
            arrow_blocking += 1
            r += dr
            c += dc
    board[arrow_row, arrow_col] = 0
    
    # Distance to opponent amazons (avoid being too close)
    opponent_amazons = np.argwhere(board == 2)
    min_dist = float('inf')
    for opp_row, opp_col in opponent_amazons:
        dist = max(abs(to_row - opp_row), abs(to_col - opp_col))
        min_dist = min(min_dist, dist)
    
    safety = min_dist if min_dist != float('inf') else 0
    
    # Combine factors with weights
    score = mobility * 2 + arrow_blocking + safety * 3
    return score
