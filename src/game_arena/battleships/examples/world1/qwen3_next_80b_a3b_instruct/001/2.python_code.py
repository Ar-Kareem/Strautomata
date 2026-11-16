
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier indexing
    board = np.array(board)
    rows, cols = board.shape
    
    # Find all hit cells
    hits = np.argwhere(board == 1)
    
    # If there are hits, try to exploit them
    if len(hits) > 0:
        # For each hit, check its 4 neighbors for unknown cells
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        for hit_row, hit_col in hits:
            for dr, dc in directions:
                nr, nc = hit_row + dr, hit_col + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 0:
                    return (nr, nc)
        
        # If no adjacent unknown found, try to extend known lines
        # Look for potential lines (2+ hits in a row)
        for hit_row, hit_col in hits:
            # Check horizontal line
            left, right = hit_col, hit_col
            while left > 0 and board[hit_row][left - 1] == 1:
                left -= 1
            while right < cols - 1 and board[hit_row][right + 1] == 1:
                right += 1
            if left > 0 and board[hit_row][left - 1] == 0:
                return (hit_row, left - 1)
            if right < cols - 1 and board[hit_row][right + 1] == 0:
                return (hit_row, right + 1)
            
            # Check vertical line
            up, down = hit_row, hit_row
            while up > 0 and board[up - 1][hit_col] == 1:
                up -= 1
            while down < rows - 1 and board[down + 1][hit_col] == 1:
                down += 1
            if up > 0 and board[up - 1][hit_col] == 0:
                return (up - 1, hit_col)
            if down < rows - 1 and board[down + 1][hit_col] == 0:
                return (down + 1, hit_col)
    
    # No active hits to exploit, use parity-based scanning
    # Shoot on (row+col) % 2 == 0 to maximize coverage efficiency
    for row in range(rows):
        for col in range(cols):
            if board[row][col] == 0 and (row + col) % 2 == 0:
                return (row, col)
    
    # Fallback: if parity pattern exhausted (unlikely), try any unknown cell
    for row in range(rows):
        for col in range(cols):
            if board[row][col] == 0:
                return (row, col)
    
    # This should never happen if the game is valid
    return (0, 0)
