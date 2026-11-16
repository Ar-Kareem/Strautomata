
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    WINNING_LENGTH = 4
    
    def is_valid_move(col):
        return grid[0, col] == 0  # Top row empty
    
    def drop_disc(col, player):
        for r in range(ROWS-1, -1, -1):
            if grid[r, col] == 0:
                grid[r, col] = player
                return r
        return -1
    
    def undo_move(col):
        for r in range(ROWS):
            if grid[r, col] != 0:
                grid[r, col] = 0
                break
    
    def get_valid_moves():
        return [c for c in range(COLS) if is_valid_move(c)]
    
    def is_terminal():
        return winning_move(1) or winning_move(-1) or len(get_valid_moves()) == 0
    
    def winning_move(player):
        # Horizontal check
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(grid[r, c+i] == player for i in range(4)):
                    return True
        # Vertical check
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(grid[r+i, c] == player for i in range(4)):
                    return True
        # Diagonal (positive slope)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(grid[r+i, c+i] == player for i in range(4)):
                    return True
        # Diagonal (negative slope)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(grid[r-i, c+i] == player for i in range(4)):
                    return True
        return False
    
    def evaluate_window(window, player):
        score = 0
        opp_player = -player
        
        player_count = np.count_nonzero(window == player)
        opp_count = np.count_nonzero(window == opp_player)
        empty_count = np.count_nonzero(window == 0)
        
        if player_count == 4:
            score += 100000
        elif player_count == 3 and empty_count == 1:
            score += 100
        elif player_count == 2 and empty_count == 2:
            score += 10
        
        if opp_count == 3 and empty_count == 1:
            score -= 90  # Block opponent's threat
        
        return score
    
    def score_position():
        score = 0
        
        # Center column preference
        center_col = grid[:, 3]
        center_count = np.count_nonzero(center_col == 1)
        score += center_count * 6
        
        # Check all windows
        # Horizontal
        for r in range(ROWS):
            row_array = grid[r, :]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, 1)
        
        # Vertical
        for c in range(COLS):
            col_array = grid[:, c]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, 1)
        
        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i, c+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [grid[r-i, c+i] for i in range(4)]
                score += evaluate_window(window, 1)
                
        return score
    
    def minimax(depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[int, int]:
        valid_moves = get_valid_moves()
        
        if depth == 0 or is_terminal():
            if winning_move(1):
                return (None, 1000000)
            elif winning_move(-1):
                return (None, -1000000)
            else:
                return (None, score_position())
        
        if maximizing:
            value = float('-inf')
            column = valid_moves[0]
            
            # Move ordering: center columns first for better pruning
            ordered_moves = sorted(valid_moves, key=lambda x: -abs(x-3))
            
            for col in ordered_moves:
                row = drop_disc(col, 1)
                _, new_score = minimax(depth-1, alpha, beta, False)
                undo_move(col)
                
                if new_score > value:
                    value = new_score
                    column = col
                    
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            
            return column, value
        else:
            value = float('inf')
            column = valid_moves[0]
            
            ordered_moves = sorted(valid_moves, key=lambda x: -abs(x-3))
            
            for col in ordered_moves:
                row = drop_disc(col, -1)
                _, new_score = minimax(depth-1, alpha, beta, True)
                undo_move(col)
                
                if new_score < value:
                    value = new_score
                    column = col
                    
                beta = min(beta, value)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return column, value
    
    # Determine depth based on remaining space (shallow when crowded)
    valid_moves = get_valid_moves()
    if len(valid_moves) > 35:
        depth = 5
    elif len(valid_moves) > 30:
        depth = 6
    else:
        depth = 7
    
    # First check if we can win immediately
    for col in valid_moves:
        row = drop_disc(col, 1)
        if winning_move(1):
            undo_move(col)
            return col
        undo_move(col)
    
    # Check if opponent will win next move - block!
    for col in valid_moves:
        row = drop_disc(col, -1)
        if winning_move(-1):
            undo_move(col)
            return col
        undo_move(col)
    
    # Otherwise use minimax
    best_col, _ = minimax(depth, float('-inf'), float('inf'), True)
    
    # Fallback in case something went wrong
    if is_valid_move(best_col):
        return best_col
    else:
        return valid_moves[0]  # Guaranteed to return legal move
