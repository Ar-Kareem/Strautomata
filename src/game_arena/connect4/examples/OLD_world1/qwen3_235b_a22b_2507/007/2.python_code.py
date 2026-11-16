
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 targeting policy using minimax with alpha-beta pruning.
    Prioritizes winning moves, blocks opponent wins, and evaluates board positions.
    """
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    ROWS, COLS = 6, 7
    
    def is_valid_move(col):
        return grid[0][col] == 0
    
    def drop_disc(col, player):
        for row in range(ROWS-1, -1, -1):
            if grid[row][col] == 0:
                grid[row][col] = player
                return row, col
        return None, None
    
    def remove_disc(row, col):
        grid[row][col] = 0
    
    def check_winner(player):
        # Check horizontal
        for row in range(ROWS):
            for col in range(COLS-3):
                if all(grid[row][col+i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(ROWS-3):
            for col in range(COLS):
                if all(grid[row+i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(3, ROWS):
            for col in range(COLS-3):
                if all(grid[row-i][col+i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(ROWS-3):
            for col in range(COLS-3):
                if all(grid[row+i][col+i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, player):
        score = 0
        opponent = -player
        
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 10000
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 8
        
        return score
    
    def score_position():
        score = 0
        
        # Center column preference
        center_col = [grid[row][3] for row in range(ROWS)]
        center_count = center_col.count(1)
        score += center_count * 6
        
        # Check all windows
        # Horizontal
        for row in range(ROWS):
            for col in range(COLS-3):
                window = [grid[row][col+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Vertical
        for row in range(ROWS-3):
            for col in range(COLS):
                window = [grid[row+i][col] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Positive diagonal
        for row in range(ROWS-3):
            for col in range(COLS-3):
                window = [grid[row+i][col+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        # Negative diagonal
        for row in range(3, ROWS):
            for col in range(COLS-3):
                window = [grid[row-i][col+i] for i in range(4)]
                score += evaluate_window(window, 1)
        
        return score
    
    def minimax(depth, alpha, beta, maximizing_player):
        # Terminal conditions
        if check_winner(1):  # AI wins
            return (None, 1000000000)
        if check_winner(-1):  # Opponent wins
            return (None, -1000000000)
        if depth == 0:  # Depth limit reached
            return (None, score_position())
        
        valid_moves = [col for col in range(COLS) if is_valid_move(col)]
        if not valid_moves:  # Board full
            return (None, 0)
        
        if maximizing_player:
            value = float('-inf')
            column = valid_moves[0]
            for col in valid_moves:
                row, col_idx = drop_disc(col, 1)
                new_score = minimax(depth-1, alpha, beta, False)[1]
                remove_disc(row, col_idx)
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = valid_moves[0]
            for col in valid_moves:
                row, col_idx = drop_disc(col, -1)
                new_score = minimax(depth-1, alpha, beta, True)[1]
                remove_disc(row, col_idx)
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
    
    # First, check if we can win in one move
    for col in range(COLS):
        if is_valid_move(col):
            row, col_idx = drop_disc(col, 1)
            if check_winner(1):
                remove_disc(row, col_idx)
                return col
            remove_disc(row, col_idx)
    
    # Then check if opponent can win in one move, and block
    for col in range(COLS):
        if is_valid_move(col):
            row, col_idx = drop_disc(col, -1)
            if check_winner(-1):
                remove_disc(row, col_idx)
                return col
            remove_disc(row, col_idx)
    
    # If no immediate threat, use minimax search
    best_col, _ = minimax(5, float('-inf'), float('inf'), True)
    return best_col
