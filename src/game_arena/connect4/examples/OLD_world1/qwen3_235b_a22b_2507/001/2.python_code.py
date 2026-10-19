
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 policy that uses minimax with alpha-beta pruning and heuristic evaluation.
    """
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    ROWS, COLS = 6, 7
    
    def is_valid_move(col):
        return grid[0, col] == 0
    
    def get_valid_moves():
        return [col for col in range(COLS) if is_valid_move(col)]
    
    def make_move(grid, col, player):
        # Create a copy and make move
        new_grid = grid.copy()
        for row in range(ROWS-1, -1, -1):
            if new_grid[row, col] == 0:
                new_grid[row, col] = player
                break
        return new_grid
    
    def is_winning_move(grid, col, player):
        # Check if placing a disc in col results in a win
        # Find the row where the disc would land
        row = None
        for r in range(ROWS-1, -1, -1):
            if grid[r, col] == 0:
                row = r
                break
        if row is None:
            return False
        
        # Check horizontal
        count = 1
        # Left
        c = col - 1
        while c >= 0 and grid[row, c] == player:
            count += 1
            c -= 1
        # Right
        c = col + 1
        while c < COLS and grid[row, c] == player:
            count += 1
            c += 1
        if count >= 4:
            return True
        
        # Check vertical
        count = 1
        # Up (not possible since we're dropping)
        # Down
        r = row + 1
        while r < ROWS and grid[r, col] == player:
            count += 1
            r += 1
        if count >= 4:
            return True
        
        # Check diagonal /
        count = 1
        # Up-right
        r, c = row - 1, col + 1
        while r >= 0 and c < COLS and grid[r, c] == player:
            count += 1
            r -= 1
            c += 1
        # Down-left
        r, c = row + 1, col - 1
        while r < ROWS and c >= 0 and grid[r, c] == player:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True
        
        # Check diagonal \
        count = 1
        # Up-left
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and grid[r, c] == player:
            count += 1
            r -= 1
            c -= 1
        # Down-right
        r, c = row + 1, col + 1
        while r < ROWS and c < COLS and grid[r, c] == player:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True
        
        return False
    
    def evaluate_position(grid):
        """Heuristic evaluation of the board position"""
        score = 0
        
        # Check center column preference
        center_col = grid[:, 3]
        center_count = np.sum(center_col == 1)
        score += center_count * 3
        
        # Check for potential wins and blocking
        for row in range(ROWS):
            for col in range(COLS):
                if grid[row, col] == 0:
                    # Check if this empty position can lead to a win for me
                    if is_winning_move(grid, col, 1):
                        score += 1000
                    
                    # Check if opponent could win here
                    if is_winning_move(grid, col, -1):
                        score += 500  # Strong incentive to block
        
        # Count potential 3-in-a-row for both players
        for row in range(ROWS):
            for col in range(COLS):
                if grid[row, col] == 1:
                    # Look for patterns with this piece
                    # This is a simplified pattern evaluation
                    pass
        
        return score
    
    def minimax(grid, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        
        # Terminal conditions
        if depth == 0 or len(valid_moves) == 0:
            return evaluate_position(grid)
        
        # Check for immediate win
        for col in valid_moves:
            if is_winning_move(grid, col, 1 if maximizing_player else -1):
                if maximizing_player:
                    return 10000 - depth  # Prefer shallower wins
                else:
                    return -10000 + depth  # Prefer shallower losses
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                if not is_valid_move(col):
                    continue
                new_grid = make_move(grid, col, 1)
                eval_score = minimax(new_grid, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                if not is_valid_move(col):
                    continue
                new_grid = make_move(grid, col, -1)
                eval_score = minimax(new_grid, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # First, check if we can win immediately
    valid_moves = get_valid_moves()
    for col in valid_moves:
        if is_winning_move(grid, col, 1):
            return col
    
    # Then check if we need to block opponent's win
    for col in valid_moves:
        if is_winning_move(grid, col, -1):
            return col
    
    # If no immediate threats, use minimax with limited depth
    best_col = valid_moves[0]  # default
    best_value = float('-inf')
    
    # Use depth 5 for decent look-ahead within time limits
    depth = 5
    
    for col in valid_moves:
        new_grid = make_move(grid, col, 1)
        value = minimax(new_grid, depth - 1, float('-inf'), float('inf'), False)
        if value > best_value:
            best_value = value
            best_col = col
    
    return best_col
