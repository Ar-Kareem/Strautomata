
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Check for immediate win
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_open_row(np_board, col)
            np_board[row][col] = 1
            if winning_move(np_board, 1):
                np_board[row][col] = 0  # Reset
                return col
            np_board[row][col] = 0  # Reset
    
    # Check for opponent immediate win to block
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_open_row(np_board, col)
            np_board[row][col] = -1
            if winning_move(np_board, -1):
                np_board[row][col] = 0  # Reset
                return col
            np_board[row][col] = 0  # Reset
    
    # Use minimax with iterative deepening
    best_col = 3  # Default to center
    try:
        import time
        start_time = time.time()
        
        # Iterative deepening - try increasing depths until time runs out
        for depth in range(1, 8):  # Cap at depth 7
            if time.time() - start_time > 0.9:  # Leave buffer time
                break
                
            col, _ = minimax(np_board, depth, -np.inf, np.inf, True)
            if col is not None:
                best_col = col
                
    except:
        # Fallback if something goes wrong
        pass
        
    # Make sure we return a valid column
    if is_valid_move(np_board, best_col):
        return best_col
    
    # If somehow best_col is invalid, find first valid column
    for col in range(7):
        if is_valid_move(np_board, col):
            return col
    
    # Should never reach here in a valid game
    return 0

def is_valid_move(board, col):
    return board[0][col] == 0

def get_next_open_row(board, col):
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def winning_move(board, piece):
    # Check horizontal locations
    for c in range(4):
        for r in range(6):
            if (board[r][c] == piece and board[r][c+1] == piece and 
                board[r][c+2] == piece and board[r][c+3] == piece):
                return True

    # Check vertical locations
    for c in range(7):
        for r in range(3):
            if (board[r][c] == piece and board[r+1][c] == piece and 
                board[r+2][c] == piece and board[r+3][c] == piece):
                return True

    # Check positively sloped diagonals
    for c in range(4):
        for r in range(3):
            if (board[r][c] == piece and board[r+1][c+1] == piece and 
                board[r+2][c+2] == piece and board[r+3][c+3] == piece):
                return True

    # Check negatively sloped diagonals
    for c in range(4):
        for r in range(3, 6):
            if (board[r][c] == piece and board[r-1][c+1] == piece and 
                board[r-2][c+2] == piece and board[r-3][c+3] == piece):
                return True

    return False

def evaluate_window(window, piece):
    score = 0
    opponent_piece = -1 if piece == 1 else 1

    if window.count(piece) == 4:
        score += 1000
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 100
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 10

    if window.count(opponent_piece) == 3 and window.count(0) == 1:
        score -= 200
        
    return score

def score_position(board, piece):
    score = 0

    # Score center column
    center_array = [int(i) for i in list(board[:, 3])]
    center_count = center_array.count(piece)
    score += center_count * 6

    # Score Horizontal
    for r in range(6):
        row_array = [int(i) for i in list(board[r,:])]
        for c in range(4):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)

    # Score Vertical
    for c in range(7):
        col_array = [int(i) for i in list(board[:,c])]
        for r in range(3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)

    # Score positive diagonal
    for r in range(3):
        for c in range(4):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    # Score negative diagonal
    for r in range(3):
        for c in range(4):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    return winning_move(board, 1) or winning_move(board, -1) or len([c for c in range(7) if is_valid_move(board, c)]) == 0

def minimax(board, depth, alpha, beta, maximizing_player):
    valid_locations = [c for c in range(7) if is_valid_move(board, c)]
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, 1):
                return (None, 10000000000000)
            elif winning_move(board, -1):
                return (None, -10000000000000)
            else: # Game is over, no more valid moves
                return (None, 0)
        else: # Depth is zero
            return (None, score_position(board, 1))
    
    if maximizing_player:
        value = -np.inf
        column = np.random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = 1
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else: # Minimizing player
        value = np.inf
        column = np.random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = -1
            new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value
