
import numpy as np
from functools import lru_cache

def policy(board: list[list[int]]) -> int:
    grid = np.array(board)
    
    # First, check if we can win in the next move
    for col in range(7):
        if is_legal_move(grid, col):
            temp_grid = make_move(grid, col, 1)
            if check_win(temp_grid, 1):
                return col
    
    # Then, check if opponent can win next move and block them
    for col in range(7):
        if is_legal_move(grid, col):
            temp_grid = make_move(grid, col, -1)
            if check_win(temp_grid, -1):
                return col
    
    # Use minimax with alpha-beta pruning to find best move
    best_score = -float('inf')
    best_col = 3  # Default to center column
    alpha = -float('inf')
    beta = float('inf')
    depth = 4  # Adjust depth based on performance
    
    # Consider columns ordered by center preference
    columns = [3, 2, 4, 1, 5, 0, 6]
    
    for col in columns:
        if is_legal_move(grid, col):
            temp_grid = make_move(grid, col, 1)
            score = minimax(temp_grid, depth-1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break
    
    return best_col

def is_legal_move(grid, col):
    return 0 in grid[:, col]

def make_move(grid, col, player):
    new_grid = grid.copy()
    row = get_next_open_row(new_grid, col)
    new_grid[row, col] = player
    return new_grid

def get_next_open_row(grid, col):
    for row in range(5, -1, -1):
        if grid[row, col] == 0:
            return row
    return -1

def check_win(grid, player):
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if (grid[row, col] == player and 
                grid[row, col+1] == player and 
                grid[row, col+2] == player and 
                grid[row, col+3] == player):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if (grid[row, col] == player and 
                grid[row+1, col] == player and 
                grid[row+2, col] == player and 
                grid[row+3, col] == player):
                return True
    
    # Check diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if (grid[row, col] == player and 
                grid[row+1, col+1] == player and 
                grid[row+2, col+2] == player and 
                grid[row+3, col+3] == player):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            if (grid[row, col] == player and 
                grid[row-1, col+1] == player and 
                grid[row-2, col+2] == player and 
                grid[row-3, col+3] == player):
                return True
    
    return False

def minimax(grid, depth, alpha, beta, maximizing_player):
    if check_win(grid, 1):
        return 1000 + depth  # Earlier win is better
    if check_win(grid, -1):
        return -1000 - depth  # Earlier loss is worse
    if depth == 0 or is_terminal_node(grid):
        return evaluate_position(grid)
    
    if maximizing_player:
        value = -float('inf')
        for col in range(7):
            if is_legal_move(grid, col):
                child = make_move(grid, col, 1)
                value = max(value, minimax(child, depth-1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        return value
    else:
        value = float('inf')
        for col in range(7):
            if is_legal_move(grid, col):
                child = make_move(grid, col, -1)
                value = min(value, minimax(child, depth-1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
        return value

def is_terminal_node(grid):
    return not (0 in grid) or check_win(grid, 1) or check_win(grid, -1)

def evaluate_position(grid):
    score = 0
    
    # Prefer center column
    center_array = [int(i) for i in list(grid[:, 3])]
    center_count = center_array.count(1)
    score += center_count * 3
    
    # Evaluate horizontal segments
    for row in range(6):
        row_array = [int(i) for i in list(grid[row, :])]
        for col in range(4):
            segment = row_array[col:col+4]
            score += evaluate_segment(segment)
    
    # Evaluate vertical segments
    for col in range(7):
        col_array = [int(i) for i in list(grid[:, col])]
        for row in range(3):
            segment = col_array[row:row+4]
            score += evaluate_segment(segment)
    
    # Evaluate positive diagonal segments
    for row in range(3):
        for col in range(4):
            segment = [grid[row+i, col+i] for i in range(4)]
            score += evaluate_segment(segment)
    
    # Evaluate negative diagonal segments
    for row in range(3):
        for col in range(4):
            segment = [grid[row+3-i, col+i] for i in range(4)]
            score += evaluate_segment(segment)
    
    return score

def evaluate_segment(segment):
    score = 0
    player_count = segment.count(1)
    opponent_count = segment.count(-1)
    
    if player_count == 4:
        score += 100
    elif player_count == 3 and opponent_count == 0:
        score += 5
    elif player_count == 2 and opponent_count == 0:
        score += 2
    elif player_count == 1 and opponent_count == 0:
        score += 1
    
    if opponent_count == 4:
        score -= 100
    elif opponent_count == 3 and player_count == 0:
        score -= 7  # More urgent to block opponent
    elif opponent_count == 2 and player_count == 0:
        score -= 3
    elif opponent_count == 1 and player_count == 0:
        score -= 1
    
    return score
