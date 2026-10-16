
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    rows, cols = grid.shape
    
    # Helper function to check if a position is valid
    def is_valid(row, col):
        return 0 <= row < rows and 0 <= col < cols
    
    # Helper function to check if a position is empty
    def is_empty(row, col):
        return grid[row, col] == 0
    
    # Helper function to get the lowest empty row in a column
    def get_lowest_empty_row(col):
        for row in range(rows - 1, -1, -1):
            if grid[row, col] == 0:
                return row
        return -1  # Column is full
    
    # Score a position based on potential connections
    def score_position(row, col, player):
        score = 0
        directions = [
            (0, 1),   # Horizontal right
            (1, 0),   # Vertical down
            (1, 1),   # Diagonal down-right
            (1, -1)   # Diagonal down-left
        ]
        
        for dr, dc in directions:
            count = 1  # Count the current piece
            # Check in positive direction
            r, c = row + dr, col + dc
            while is_valid(r, c) and grid[r, c] == player:
                count += 1
                r += dr
                c += dc
            
            # Check in negative direction
            r, c = row - dr, col - dc
            while is_valid(r, c) and grid[r, c] == player:
                count += 1
                r -= dr
                c -= dc
            
            # Score based on how many connected pieces we have
            if count >= 4:
                score += 1000  # Win
            elif count == 3:
                score += 100   # Three in a row
            elif count == 2:
                score += 10    # Two in a row
            elif count == 1:
                score += 1     # One piece
        
        return score
    
    # Check if we can win in the next move
    for col in range(cols):
        row = get_lowest_empty_row(col)
        if row != -1:
            grid[row, col] = 1  # Try placing our disc
            if score_position(row, col, 1) >= 1000:
                grid[row, col] = 0  # Reset
                return col
            grid[row, col] = 0  # Reset
    
    # Check if opponent can win in the next move (block them)
    for col in range(cols):
        row = get_lowest_empty_row(col)
        if row != -1:
            grid[row, col] = -1  # Try placing opponent's disc
            if score_position(row, col, -1) >= 1000:
                grid[row, col] = 0  # Reset
                return col
            grid[row, col] = 0  # Reset
    
    # If no immediate win/block, use a heuristic to evaluate each column
    best_score = -1
    best_col = cols // 2  # Default to center
    
    # Evaluate columns from center to edges for better placement strategy
    center_cols = list(range(cols))
    center_cols.sort(key=lambda x: abs(x - cols // 2))
    
    for col in center_cols:
        row = get_lowest_empty_row(col)
        if row != -1:
            # Calculate score for placing our disc in this position
            score = score_position(row, col, 1)
            
            # Prefer center columns
            if col == cols // 2:
                score += 5
            
            # Prefer positions near the center of the board
            if abs(row - rows // 2) <= 1:
                score += 3
            
            if score > best_score:
                best_score = score
                best_col = col
    
    # If all columns are full, return center (should not happen in valid game state)
    return best_col
