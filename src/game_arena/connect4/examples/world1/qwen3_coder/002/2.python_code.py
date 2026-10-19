
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Check for immediate win
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_open_row(np_board, col)
            drop_piece(np_board, row, col, 1)
            if winning_move(np_board, 1):
                return col
            # Undo the move
            np_board[row][col] = 0
    
    # Check for opponent's immediate win to block
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_open_row(np_board, col)
            drop_piece(np_board, row, col, -1)
            if winning_move(np_board, -1):
                return col
            # Undo the move
            np_board[row][col] = 0
    
    # Use minimax to find the best move
    best_score = -float('inf')
    best_col = 3  # Default to center
    
    # Try columns in order of preference (center first)
    column_order = [3, 2, 4, 1, 5, 0, 6]
    
    for col in column_order:
        if is_valid_move(np_board, col):
            row = get_next_open_row(np_board, col)
            drop_piece(np_board, row, col, 1)
            score = minimax(np_board, 5, -float('inf'), float('inf'), False)
            np_board[row][col] = 0  # Undo move
            
            if score > best_score:
                best_score = score
                best_col = col
                
    return best_col

def is_valid_move(board, col):
    return board[0][col] == 0

def get_next_open_row(board, col):
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return -1

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def winning_move(board, piece):
    # Check horizontal locations
    for c in range(4):
        for r in range(6):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Check vertical locations
    for c in range(7):
        for r in range(3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Check positively sloped diagonals
    for c in range(4):
        for r in range(3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Check negatively sloped diagonals
    for c in range(4):
        for r in range(3, 6):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False

def evaluate_window(window, piece):
    score = 0
    opp_piece = -1 if piece == 1 else 1

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 10
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 80

    return score

def score_position(board, piece):
    score = 0

    # Score center column
    center_array = [int(i) for i in list(board[:, 3])]
    center_count = center_array.count(piece)
    score += center_count * 3

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
    for r in range(3, 6):
        for c in range(4):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    return winning_move(board, 1) or winning_move(board, -1) or len([c for c in range(7) if is_valid_move(board, c)]) == 0

def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = [c for c in range(7) if is_valid_move(board, c)]
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, 1):
                return 10000000000000
            elif winning_move(board, -1):
                return -10000000000000
            else:  # Game is over, no more valid moves
                return 0
        else:  # Depth is zero
            return score_position(board, 1)
    
    if maximizingPlayer:
        value = -float('inf')
        for col in valid_locations:
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, 1)
            new_score = minimax(board, depth-1, alpha, beta, False)
            board[row][col] = 0
            value = max(value, new_score)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    else:  # Minimizing player
        value = float('inf')
        for col in valid_locations:
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, -1)
            new_score = minimax(board, depth-1, alpha, beta, True)
            board[row][col] = 0
            value = min(value, new_score)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
