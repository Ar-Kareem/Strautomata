
import numpy as np
import copy
import math

def policy(board):
    """
    Returns the best column to drop disc for current player (player 1).
    Uses minimax with alpha-beta pruning and evaluation heuristic.
    """
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Check for immediate win
    for col in range(7):
        if is_valid_move(board_np, col):
            new_board = make_move(board_np, col, 1)
            if is_win(new_board, 1):
                return col
    
    # Check for immediate blocking (opponent would win next)
    for col in range(7):
        if is_valid_move(board_np, col):
            new_board = make_move(board_np, col, -1)
            if is_win(new_board, -1):
                return col
    
    # Use minimax with alpha-beta pruning
    depth = 5  # Adjust based on performance
    best_col = 3  # Default center column
    best_value = -math.inf
    
    # Try each valid move
    valid_cols = [col for col in range(7) if is_valid_move(board_np, col)]
    
    # Order moves by center preference for better pruning
    valid_cols.sort(key=lambda x: abs(x - 3))
    
    for col in valid_cols:
        new_board = make_move(board_np, col, 1)
        value = minimax(new_board, depth - 1, -math.inf, math.inf, False)
        if value > best_value:
            best_value = value
            best_col = col
    
    return best_col

def is_valid_move(board, col):
    """Check if column has empty cell."""
    return board[0, col] == 0

def make_move(board, col, player):
    """Return new board after dropping player's disc in column."""
    new_board = board.copy()
    for row in range(5, -1, -1):  # from bottom to top
        if new_board[row, col] == 0:
            new_board[row, col] = player
            break
    return new_board

def is_win(board, player):
    """Check if player has four in a row."""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row, col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if all(board[row + i, col] == player for i in range(4)):
                return True
    
    # Check diagonal (down-right)
    for row in range(3):
        for col in range(4):
            if all(board[row + i, col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (down-left)
    for row in range(3):
        for col in range(3, 7):
            if all(board[row + i, col - i] == player for i in range(4)):
                return True
    
    return False

def is_terminal(board):
    """Check if game is over (win or board full)."""
    if is_win(board, 1) or is_win(board, -1):
        return True
    
    # Check if board is full
    if np.all(board != 0):
        return True
    
    return False

def evaluate(board):
    """
    Evaluate board position from perspective of player 1.
    Positive is good for player 1.
    """
    score = 0
    
    # Center column preference
    center_array = board[:, 3]
    center_count = np.sum(center_array == 1) - np.sum(center_array == -1)
    score += center_count * 3
    
    # Score horizontal lines
    for row in range(6):
        for col in range(4):
            window = board[row, col:col+4]
            score += evaluate_window(window)
    
    # Score vertical lines
    for row in range(3):
        for col in range(7):
            window = board[row:row+4, col]
            score += evaluate_window(window)
    
    # Score diagonal (down-right)
    for row in range(3):
        for col in range(4):
            window = [board[row+i, col+i] for i in range(4)]
            score += evaluate_window(window)
    
    # Score diagonal (down-left)
    for row in range(3):
        for col in range(3, 7):
            window = [board[row+i, col-i] for i in range(4)]
            score += evaluate_window(window)
    
    return score

def evaluate_window(window):
    """Evaluate a window of 4 cells."""
    score = 0
    
    # Count pieces
    count_1 = np.sum(window == 1)
    count_m1 = np.sum(window == -1)
    empty = np.sum(window == 0)
    
    # If both players have pieces in window, it's blocked (no advantage)
    if count_1 > 0 and count_m1 > 0:
        return 0
    
    # Player 1 advantage
    if count_1 > 0:
        if count_1 == 4:
            score += 100000
        elif count_1 == 3 and empty == 1:
            score += 100
        elif count_1 == 2 and empty == 2:
            score += 10
        elif count_1 == 1 and empty == 3:
            score += 1
    
    # Player -1 advantage
    elif count_m1 > 0:
        if count_m1 == 4:
            score -= 100000
        elif count_m1 == 3 and empty == 1:
            score -= 100
        elif count_m1 == 2 and empty == 2:
            score -= 10
        elif count_m1 == 1 and empty == 3:
            score -= 1
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax with alpha-beta pruning.
    maximizing_player: True if it's player 1's turn, False for opponent.
    """
    # Terminal state or depth limit reached
    if depth == 0 or is_terminal(board):
        return evaluate(board)
    
    valid_cols = [col for col in range(7) if is_valid_move(board, col)]
    
    # If no valid moves, return evaluation
    if not valid_cols:
        return evaluate(board)
    
    if maximizing_player:  # Player 1's turn
        value = -math.inf
        for col in valid_cols:
            new_board = make_move(board, col, 1)
            value = max(value, minimax(new_board, depth - 1, alpha, beta, False))
            alpha = max(alpha, value)
            if value >= beta:
                break  # Beta cutoff
        return value
    else:  # Opponent's turn
        value = math.inf
        for col in valid_cols:
            new_board = make_move(board, col, -1)
            value = min(value, minimax(new_board, depth - 1, alpha, beta, True))
            beta = min(beta, value)
            if value <= alpha:
                break  # Alpha cutoff
        return value
