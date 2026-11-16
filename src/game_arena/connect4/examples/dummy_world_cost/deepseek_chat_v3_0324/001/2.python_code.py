
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> int:
    # Constants
    ROWS = 6
    COLS = 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1
    WIN_SCORE = 1000000
    
    def is_valid_location(board, col):
        return board[0][col] == EMPTY
    
    def get_next_open_row(board, col):
        for r in range(ROWS-1, -1, -1):
            if board[r][col] == EMPTY:
                return r
        return -1
    
    def winning_move(board, piece):
        # Horizontal check
        for c in range(COLS-3):
            for r in range(ROWS):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True

        # Vertical check
        for c in range(COLS):
            for r in range(ROWS-3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True

        # Positive diagonal check
        for c in range(COLS-3):
            for r in range(ROWS-3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True

        # Negative diagonal check
        for c in range(COLS-3):
            for r in range(3, ROWS):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False
    
    def evaluate_window(window, piece):
        score = 0
        opp_piece = PLAYER if piece == OPPONENT else OPPONENT
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 2
        
        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 4
            
        return score
    
    def score_position(board, piece):
        score = 0
        
        # Prefer center column
        center_array = [board[r][COLS//2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 6
        
        # Horizontal windows
        for r in range(ROWS):
            row_array = board[r]
            for c in range(COLS-3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
                
        # Vertical windows
        for c in range(COLS):
            col_array = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS-3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
                
        # Positive diagonal windows
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        # Negative diagonal windows
        for r in range(ROWS-3):
            for c in range(COLS-3):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_locations = [c for c in range(COLS) if is_valid_location(board, c)]
        
        if depth == 0 or len(valid_locations) == 0:
            return (None, score_position(board, PLAYER)) if len(valid_locations) > 0 else (None, 0)
        
        if maximizing_player:
            value = -float('inf')
            column = np.random.choice(valid_locations)
            
            for col in valid_locations:
                row = get_next_open_row(board, col)
                temp_board = [row[:] for row in board]
                temp_board[row][col] = PLAYER
                
                if winning_move(temp_board, PLAYER):
                    return (col, WIN_SCORE)
                    
                new_score = minimax(temp_board, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = np.random.choice(valid_locations)
            
            for col in valid_locations:
                row = get_next_open_row(board, col)
                temp_board = [row[:] for row in board]
                temp_board[row][col] = OPPONENT
                
                if winning_move(temp_board, OPPONENT):
                    return (col, -WIN_SCORE)
                    
                new_score = minimax(temp_board, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
    
    # Check if we can win in the next move
    for col in range(COLS):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            temp_board = [row[:] for row in board]
            temp_board[row][col] = PLAYER
            if winning_move(temp_board, PLAYER):
                return col
    
    # Check if we need to block opponent from winning
    for col in range(COLS):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            temp_board = [row[:] for row in board]
            temp_board[row][col] = OPPONENT
            if winning_move(temp_board, OPPONENT):
                return col
    
    # Use minimax with alpha-beta pruning to determine best move
    best_col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    
    # Fallback to center or random valid move
    if best_col is None or not is_valid_location(board, best_col):
        if is_valid_location(board, COLS//2):
            return COLS//2
        else:
            valid_cols = [c for c in range(COLS) if is_valid_location(board, c)]
            return np.random.choice(valid_cols)
    
    return best_col
