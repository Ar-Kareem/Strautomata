
import numpy as np
from typing import List, Tuple

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning and heuristics.
    Prioritizes winning moves, blocks opponent wins, and uses a position-based scoring system.
    """
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    rows, cols = grid.shape
    
    def is_valid_move(col):
        return grid[0][col] == 0
    
    def drop_piece(col, player):
        for row in range(rows - 1, -1, -1):
            if grid[row][col] == 0:
                grid[row][col] = player
                return row, col
        return None, None
    
    def undo_move(row, col):
        grid[row][col] = 0
    
    def check_winner(player):
        # Check horizontal
        for row in range(rows):
            for col in range(cols - 3):
                if all(grid[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(rows - 3):
            for col in range(cols):
                if all(grid[row + i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(rows - 3):
            for col in range(cols - 3):
                if all(grid[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(3, rows):
            for col in range(cols - 3):
                if all(grid[row - i][col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def get_valid_moves():
        return [col for col in range(cols) if is_valid_move(col)]
    
    def evaluate_position():
        """
        Heuristic evaluation function
        """
        score = 0
        
        # Center column preference
        center_array = list(grid[:, cols // 2])
        center_count = center_array.count(1)
        score += center_count * 3
        
        # Check for potential connections
        score += evaluate_direction(1, 0)  # horizontal
        score += evaluate_direction(0, 1)  # vertical
        score += evaluate_direction(1, 1)  # diagonal down-right
        score += evaluate_direction(1, -1) # diagonal down-left
        
        return score
    
    def evaluate_direction(delta_row, delta_col):
        score = 0
        for row in range(rows):
            for col in range(cols):
                end_row = row + delta_row * 3
                end_col = col + delta_col * 3
                
                if (end_row >= 0 and end_row < rows and 
                    end_col >= 0 and end_col < cols):
                    
                    # Count pieces in this window
                    player_count = 0
                    opponent_count = 0
                    empty_count = 0
                    
                    for i in range(4):
                        current_row = row + delta_row * i
                        current_col = col + delta_col * i
                        if grid[current_row][current_col] == 1:
                            player_count += 1
                        elif grid[current_row][current_col] == -1:
                            opponent_count += 1
                        else:
                            empty_count += 1
                    
                    # Score this window
                    if player_count == 3 and empty_count == 1:
                        score += 100  # Potential win
                    elif player_count == 2 and empty_count == 2:
                        score += 10
                    elif player_count == 1 and empty_count == 3:
                        score += 1
                        
                    if opponent_count == 3 and empty_count == 1:
                        score -= 90  # Block opponent win
                    elif opponent_count == 2 and empty_count == 2:
                        score -= 8
                    
        return score
    
    def minimax(depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_position()
        
        valid_moves = get_valid_moves()
        
        if not valid_moves:
            return 0  # Draw
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                row, _ = drop_piece(col, 1)
                if row is not None:
                    if check_winner(1):
                        undo_move(row, col)
                        return 100000 + depth  # Prefer immediate wins
                    
                    eval_score = minimax(depth - 1, alpha, beta, False)
                    undo_move(row, col)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                row, _ = drop_piece(col, -1)
                if row is not None:
                    if check_winner(-1):
                        undo_move(row, col)
                        return -100000 - depth  # Avoid moves where opponent wins
                    
                    eval_score = minimax(depth - 1, alpha, beta, True)
                    undo_move(row, col)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            return min_eval
    
    # First, check if we can win immediately
    valid_moves = get_valid_moves()
    for col in valid_moves:
        row, _ = drop_piece(col, 1)
        if row is not None:
            if check_winner(1):
                undo_move(row, col)
                return col
            undo_move(row, col)
    
    # Check if opponent can win and block
    for col in valid_moves:
        row, _ = drop_piece(col, -1)
        if row is not None:
            if check_winner(-1):
                undo_move(row, col)
                return col
            undo_move(row, col)
    
    # Use minimax with depth limit based on game stage
    best_score = float('-inf')
    best_col = valid_moves[0]  # Default to first valid move
    
    # Adjust search depth based on how full the board is
    empty_cells = np.sum(grid == 0)
    depth = 5 if empty_cells > 20 else 6 if empty_cells > 10 else 7
    
    for col in valid_moves:
        row, _ = drop_piece(col, 1)
        if row is not None:
            score = minimax(depth - 1, float('-inf'), float('inf'), False)
            undo_move(row, col)
            
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col
