
import numpy as np

def policy(board):
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    rows, cols = 6, 7
    
    # Check for immediate winning move
    for col in range(cols):
        if is_valid_move(grid, col):
            row = get_next_open_row(grid, col)
            if check_win(grid, row, col, 1):  # Check if this move wins
                return col
    
    # Check if opponent has immediate winning move
    for col in range(cols):
        if is_valid_move(grid, col):
            row = get_next_open_row(grid, col)
            if check_win(grid, row, col, -1):  # Check if this would let opponent win
                return col
    
    # Create forks (positions with multiple winning opportunities)
    best_col = -1
    best_score = -1
    center_cols = [3, 2, 4, 1, 5, 0, 6]  # Prefer center columns first
    
    for col in center_cols:
        if is_valid_move(grid, col):
            row = get_next_open_row(grid, col)
            temp_grid = grid.copy()
            temp_grid[row, col] = 1
            score = evaluate_position(temp_grid, row, col)
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col if best_col != -1 else get_first_valid_move(grid)

# Helper functions
def is_valid_move(grid, col):
    return grid[0, col] == 0

def get_next_open_row(grid, col):
    for row in range(5, -1, -1):
        if grid[row, col] == 0:
            return row
    return -1

def check_win(grid, row, col, player):
    # Check horizontal, vertical, and both diagonals
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        # Check one direction
        for i in range(1, 4):
            r, c = row + i*dr, col + i*dc
            if 0 <= r < 6 and 0 <= c < 7 and grid[r, c] == player:
                count += 1
            else:
                break
        # Check opposite direction
        for i in range(1, 4):
            r, c = row - i*dr, col - i*dc
            if 0 <= r < 6 and 0 <= c < 7 and grid[r, c] == player:
                count += 1
            else:
                break
        if count >= 4:
            return True
    return False

def evaluate_position(grid, row, col):
    score = 0
    # Count potential winning lines
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        empty = 0
        our = 1  # We just placed one
        for i in range(1, 4):
            r, c = row + i*dr, col + i*dc
            if 0 <= r < 6 and 0 <= c < 7:
                if grid[r, c] == 1:
                    our += 1
                elif grid[r, c] == 0:
                    empty += 1
                else:
                    break
            else:
                break
        for i in range(1, 4):
            r, c = row - i*dr, col - i*dc
            if 0 <= r < 6 and 0 <= c < 7:
                if grid[r, c] == 1:
                    our += 1
                elif grid[r, c] == 0:
                    empty += 1
                else:
                    break
            else:
                break
        if our + empty >= 4:
            score += our*our  # More weight to near-complete lines
    
    # Bonus for center and middle columns
    if col in [2, 3, 4]:
        score += 2
    elif col in [1, 5]:
        score += 1
    
    return score

def get_first_valid_move(grid):
    for col in range(7):
        if is_valid_move(grid, col):
            return col
    return 0  # Fallback (shouldn't happen)
