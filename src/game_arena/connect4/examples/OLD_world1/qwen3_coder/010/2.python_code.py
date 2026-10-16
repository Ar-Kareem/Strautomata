
import numpy as np
import random
from collections import deque

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    grid = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1
    WINNING_SCORE = 1000000
    DEPTH = 4  # Adjust based on performance needs
    
    # Check if a move leads to immediate win
    def check_win(grid, player, col):
        # Make a temporary move
        temp_grid = grid.copy()
        for row in range(ROWS-1, -1, -1):
            if temp_grid[row][col] == EMPTY:
                temp_grid[row][col] = player
                # Check for win
                if is_winning_move(temp_grid, player, row, col):
                    return True
                break
        return False
    
    # Check if placing a disc at (row, col) leads to a win
    def is_winning_move(grid, player, row, col):
        # Check horizontal
        count = 1
        # Check left
        c = col - 1
        while c >= 0 and grid[row][c] == player:
            count += 1
            c -= 1
        # Check right
        c = col + 1
        while c < COLS and grid[row][c] == player:
            count += 1
            c += 1
        if count >= 4:
            return True
        
        # Check vertical
        count = 1
        # Check down
        r = row + 1
        while r < ROWS and grid[r][col] == player:
            count += 1
            r += 1
        if count >= 4:
            return True
            
        # Check diagonal (top-left to bottom-right)
        count = 1
        # Check top-left
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and grid[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        # Check bottom-right
        r, c = row + 1, col + 1
        while r < ROWS and c < COLS and grid[r][c] == player:
            count += 1
            r += 1
            c += 1
        if count >= 4:
            return True
            
        # Check diagonal (top-right to bottom-left)
        count = 1
        # Check top-right
        r, c = row - 1, col + 1
        while r >= 0 and c < COLS and grid[r][c] == player:
            count += 1
            r -= 1
            c += 1
        # Check bottom-left
        r, c = row + 1, col - 1
        while r < ROWS and c >= 0 and grid[r][c] == player:
            count += 1
            r += 1
            c -= 1
        if count >= 4:
            return True
            
        return False
    
    # Evaluate position
    def evaluate_position(grid):
        score = 0
        
        # Score center column preference
        center_array = [int(i) for i in list(grid[:, COLS//2])]
        center_count = center_array.count(PLAYER)
        score += center_count * 3
        
        # Score horizontal
        for r in range(ROWS):
            row_array = [int(i) for i in list(grid[r,:])]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += evaluate_window(window)
        
        # Score vertical
        for c in range(COLS):
            col_array = [int(i) for i in list(grid[:,c])]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += evaluate_window(window)
        
        # Score positive diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [grid[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)
                
        # Score negative diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [grid[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window)
                
        return score
    
    def evaluate_window(window):
        score = 0
        player_count = window.count(PLAYER)
        opponent_count = window.count(OPPONENT)
        empty_count = window.count(EMPTY)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
            
        if opponent_count == 3 and empty_count == 1:
            score -= 80  # Blocking opponent is valuable
            
        return score
    
    # Check if column is valid (not full)
    def is_valid_location(grid, col):
        return grid[0][col] == EMPTY
    
    # Get next open row in column
    def get_next_open_row(grid, col):
        for r in range(ROWS-1, -1, -1):
            if grid[r][col] == EMPTY:
                return r
        return -1
    
    # Minimax with alpha-beta pruning
    def minimax(grid, depth, alpha, beta, maximizing_player):
        valid_locations = [c for c in range(COLS) if is_valid_location(grid, c)]
        is_terminal = len(valid_locations) == 0  # Board full
        # Also check for wins
        # We'll approximate terminal by depth or no moves left
        if depth == 0 or is_terminal:
            if depth == 0:
                return (None, evaluate_position(grid))
            else:  # Game over
                return (None, 0)
        
        if maximizing_player:
            value = -np.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                if row != -1:
                    temp_grid = grid.copy()
                    temp_grid[row][col] = PLAYER
                    new_score = minimax(temp_grid, depth-1, alpha, beta, False)[1]
                    if new_score > value:
                        value = new_score
                        column = col
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            return column, value
        else:  # Minimizing player
            value = np.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                if row != -1:
                    temp_grid = grid.copy()
                    temp_grid[row][col] = OPPONENT
                    new_score = minimax(temp_grid, depth-1, alpha, beta, True)[1]
                    if new_score < value:
                        value = new_score
                        column = col
                    beta = min(beta, value)
                    if alpha >= beta:
                        break
            return column, value
    
    # First check if we can win in one move
    valid_locations = [c for c in range(COLS) if is_valid_location(grid, c)]
    
    # Check for immediate win
    for col in valid_locations:
        if check_win(grid, PLAYER, col):
            return col
    
    # Check for opponent immediate win to block
    for col in valid_locations:
        if check_win(grid, OPPONENT, col):
            return col
    
    # Use minimax for more advanced strategy
    col, minimax_score = minimax(grid, DEPTH, -np.inf, np.inf, True)
    
    # If minimax didn't return a valid column, choose randomly from valid columns
    if col is None or not is_valid_location(grid, col):
        return random.choice(valid_locations)
    
    return col
