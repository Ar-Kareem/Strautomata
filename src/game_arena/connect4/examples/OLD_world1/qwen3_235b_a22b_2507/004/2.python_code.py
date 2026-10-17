
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 AI policy using minimax with alpha-beta pruning and heuristic evaluation.
    Prioritizes winning moves, blocks opponent wins, and evaluates board positions.
    """
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    rows, cols = grid.shape
    
    def is_valid_move(col):
        return grid[0][col] == 0
    
    def get_next_row(col):
        for row in range(rows-1, -1, -1):
            if grid[row][col] == 0:
                return row
        return -1
    
    def is_winning_move(row, col, player):
        # Check horizontal
        count = 0
        for c in range(max(0, col-3), min(cols, col+4)):
            if grid[row][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check vertical
        count = 0
        for r in range(max(0, row-3), min(rows, row+4)):
            if grid[r][col] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check diagonal (top-left to bottom-right)
        count = 0
        for diff in range(-3, 4):
            r, c = row + diff, col + diff
            if 0 <= r < rows and 0 <= c < cols:
                if grid[r][c] == player:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        
        # Check diagonal (bottom-left to top-right)
        count = 0
        for diff in range(-3, 4):
            r, c = row - diff, col + diff
            if 0 <= r < rows and 0 <= c < cols:
                if grid[r][c] == player:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        
        return False
    
    def evaluate_window(window, player):
        """Evaluate a window of 4 consecutive positions"""
        opponent = -player
        player_count = np.sum(window == player)
        opponent_count = np.sum(window == opponent)
        empty_count = np.sum(window == 0)
        
        score = 0
        if player_count == 4:
            score += 100000
        elif player_count == 3 and empty_count == 1:
            score += 100
        elif player_count == 2 and empty_count == 2:
            score += 10
        
        if opponent_count == 3 and empty_count == 1:
            score -= 90  # Strongly block opponent's winning move
        
        return score
    
    def score_position():
        """Evaluate the entire board position"""
        score = 0
        center_col = 3
        
        # Score center column
        center_array = grid[:, center_col]
        center_count = np.sum(center_array == 1)
        score += center_count * 6
        
        # Score horizontal
        for r in range(rows):
            for c in range(cols - 3):
                window = grid[r, c:c+4]
                score += evaluate_window(window, 1)
        
        # Score vertical
        for c in range(cols):
            for r in range(rows - 3):
                window = grid[r:r+4, c]
                score += evaluate_window(window, 1)
        
        # Score diagonal (top-left to bottom-right)
        for r in range(rows - 3):
            for c in range(cols - 3):
                window = np.array([grid[r+i][c+i] for i in range(4)])
                score += evaluate_window(window, 1)
        
        # Score diagonal (bottom-left to top-right)
        for r in range(3, rows):
            for c in range(cols - 3):
                window = np.array([grid[r-i][c+i] for i in range(4)])
                score += evaluate_window(window, 1)
        
        return score
    
    def minimax(board_copy, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning"""
        # Check for terminal conditions or depth limit
        if depth == 0:
            return None, score_position()
        
        valid_cols = [c for c in range(cols) if is_valid_move(c)]
        if not valid_cols:
            return None, 0
        
        # Check if current player can win
        for col in valid_cols:
            row = get_next_row(col)
            if is_winning_move(row, col, 1 if maximizing_player else -1):
                if maximizing_player:
                    return col, 1000000 - depth  # Prefer quicker wins
                else:
                    return col, -1000000 + depth  # Prefer delaying opponent's win
        
        if maximizing_player:
            value = float('-inf')
            column = valid_cols[0]
            
            # Prioritize center columns
            valid_cols.sort(key=lambda x: abs(x - 3))
            
            for col in valid_cols:
                row = get_next_row(col)
                board_copy[row][col] = 1
                
                _, new_score = minimax(board_copy, depth - 1, alpha, beta, False)
                board_copy[row][col] = 0
                
                if new_score > value:
                    value = new_score
                    column = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Alpha-beta pruning
            
            return column, value
        else:
            value = float('inf')
            column = valid_cols[0]
            
            # Prioritize center columns
            valid_cols.sort(key=lambda x: abs(x - 3))
            
            for col in valid_cols:
                row = get_next_row(col)
                board_copy[row][col] = -1
                
                _, new_score = minimax(board_copy, depth - 1, alpha, beta, True)
                board_copy[row][col] = 0
                
                if new_score < value:
                    value = new_score
                    column = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Alpha-beta pruning
            
            return column, value
    
    # First, check if we can win immediately
    valid_moves = [c for c in range(cols) if is_valid_move(c)]
    for col in valid_moves:
        row = get_next_row(col)
        if is_winning_move(row, col, 1):
            return col
    
    # Then, check if we need to block opponent's winning move
    for col in valid_moves:
        row = get_next_row(col)
        if is_winning_move(row, col, -1):
            return col
    
    # Use minimax with reduced depth based on available time
    # For balance between strength and speed, use depth 5
    try:
        best_col, _ = minimax(grid.copy(), 5, float('-inf'), float('inf'), True)
        if best_col is not None and is_valid_move(best_col):
            return best_col
    except:
        pass
    
    # Fallback strategies if minimax fails
    # Prefer center columns
    preferred_cols = [3, 2, 4, 1, 5, 0, 6]
    for col in preferred_cols:
        if is_valid_move(col):
            return col
    
    # Last resort: return first valid column
    return valid_moves[0]
