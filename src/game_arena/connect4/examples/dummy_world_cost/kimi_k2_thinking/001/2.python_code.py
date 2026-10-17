
import numpy as np
import time

def policy(board):
    """
    Connect 4 AI policy with minimax search and alpha-beta pruning.
    Returns best column to play (0-6).
    """
    start_time = time.time()
    board = np.array(board, dtype=np.int8)
    
    # Check for immediate win
    for col in get_valid_moves(board):
        if check_immediate_win(board, col, 1):
            return col
    
    # Check for immediate block
    for col in get_valid_moves(board):
        if check_immediate_win(board, col, -1):
            return col
    
    # Use minimax with iterative deepening
    best_move = 3  # Default to center
    valid_moves = get_valid_moves(board)
    
    # Prioritize center moves for better search
    valid_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
    
    max_depth = 7
    
    best_score = -np.inf
    for col in valid_moves:
        row = get_next_open_row(board, col)
        if row is None:
            continue
        
        temp_board = board.copy()
        temp_board[row, col] = 1
        
        # If this move wins, take it immediately
        if check_win(temp_board, 1):
            return col
        
        score = minimax(temp_board, max_depth - 1, -np.inf, np.inf, False)
        
        if score > best_score:
            best_score = score
            best_move = col
    
    return best_move

def get_valid_moves(board):
    """Return list of columns that are not full."""
    valid = []
    for col in range(7):
        if board[0, col] == 0:
            valid.append(col)
    return valid

def get_next_open_row(board, col):
    """Get the next open row in given column (0 is top, 5 is bottom)."""
    for row in range(5, -1, -1):
        if board[row, col] == 0:
            return row
    return None

def check_immediate_win(board, col, player):
    """Check if playing in col gives immediate win for player."""
    row = get_next_open_row(board, col)
    if row is None:
        return False
    
    # Simulate move
    test_board = board.copy()
    test_board[row, col] = player
    
    return check_win(test_board, player)

def check_win(board, player):
    """Check if player has won."""
    # Horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row, col:col+4] == player):
                return True
    
    # Vertical
    for col in range(7):
        for row in range(3):
            if all(board[row:row+4, col] == player):
                return True
    
    # Diagonal (down-right)
    for row in range(3):
        for col in range(4):
            if all(board[row + i, col + i] == player for i in range(4)):
                return True
    
    # Diagonal (up-right)
    for row in range(3, 6):
        for col in range(4):
            if all(board[row - i, col + i] == player for i in range(4)):
                return True
    
    return False

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax with alpha-beta pruning."""
    valid_moves = get_valid_moves(board)
    
    if depth == 0 or not valid_moves:
        return evaluate_position(board)
    
    if maximizing_player:
        max_eval = -np.inf
        # Order moves: center first, then evaluate
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        for col in ordered_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            
            temp_board = board.copy()
            temp_board[row, col] = 1
            
            if check_win(temp_board, 1):
                return 1000000 + depth  # Win sooner is better
            
            eval_score = minimax(temp_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break
        
        return max_eval
    else:
        min_eval = np.inf
        ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
        
        for col in ordered_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            
            temp_board = board.copy()
            temp_board[row, col] = -1
            
            if check_win(temp_board, -1):
                return -1000000 - depth  # Opp win sooner is worse
            
            eval_score = minimax(temp_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break
        
        return min_eval

def evaluate_position(board):
    """Heuristic evaluation of board position."""
    score = 0
    
    # Center column control (very important)
    center_array = board[:, 3]
    center_count = np.sum(center_array == 1) - np.sum(center_array == -1)
    score += center_count * 3
    
    # Evaluate all possible 4-length windows
    windows = get_all_windows(board)
    
    for window in windows:
        score += evaluate_window(window)
    
    return score

def get_all_windows(board):
    """Extract all possible 4-length windows from board."""
    windows = []
    
    # Horizontal
    for row in range(6):
        for col in range(4):
            windows.append(board[row, col:col+4])
    
    # Vertical
    for col in range(7):
        for row in range(3):
            windows.append(board[row:row+4, col])
    
    # Diagonal down-right
    for row in range(3):
        for col in range(4):
            windows.append(np.array([board[row+i, col+i] for i in range(4)]))
    
    # Diagonal up-right
    for row in range(3, 6):
        for col in range(4):
            windows.append(np.array([board[row-i, col+i] for i in range(4)]))
    
    return windows

def evaluate_window(window):
    """Score a 4-cell window."""
    score = 0
    player_sum = np.sum(window)
    opp_sum = np.sum(window == -1)
    player_count = np.sum(window == 1)
    opp_count = np.sum(window == -1)
    empty_count = np.sum(window == 0)
    
    # Winning window
    if player_count == 4:
        score += 100000
    if opp_count == 4:
        score -= 100000
    
    # Three in a row (with one empty) is strong
    if player_count == 3 and empty_count == 1:
        score += 50
    if opp_count == 3 and empty_count == 1:
        score -= 50
    
    # Two in a row is good
    if player_count == 2 and empty_count == 2:
        score += 10
    if opp_count == 2 and empty_count == 2:
        score -= 10
    
    return score
