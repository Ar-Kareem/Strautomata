
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)

    # Check for immediate winning moves
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array, col, 1)
            if check_win(temp_board, 1):
                return col

    # Check for opponent's immediate winning moves to block
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array, col, -1)
            if check_win(temp_board, -1):
                return col

    # Evaluate all possible moves
    best_score = -float('inf')
    best_col = 3  # default to center

    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array, col, 1)
            score = evaluate_board(temp_board)
            if score > best_score:
                best_score = score
                best_col = col

    return best_col

def is_valid_move(board, col):
    """Check if a column has space for a move."""
    return board[0][col] == 0

def make_move(board, col, player):
    """Return a new board with the move applied."""
    new_board = board.copy()
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def check_win(board, player):
    """Check if the specified player has won."""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if (board[row][col] == player and
                board[row][col+1] == player and
                board[row][col+2] == player and
                board[row][col+3] == player):
                return True

    # Check vertical
    for row in range(3):
        for col in range(7):
            if (board[row][col] == player and
                board[row+1][col] == player and
                board[row+2][col] == player and
                board[row+3][col] == player):
                return True

    # Check diagonal (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            if (board[row][col] == player and
                board[row+1][col+1] == player and
                board[row+2][col+2] == player and
                board[row+3][col+3] == player):
                return True

    # Check diagonal (bottom-left to top-right)
    for row in range(3, 6):
        for col in range(4):
            if (board[row][col] == player and
                board[row-1][col+1] == player and
                board[row-2][col+2] == player and
                board[row-3][col+3] == player):
                return True

    return False

def evaluate_board(board):
    """Evaluate the board position with a heuristic score."""
    score = 0

    # Center control - prefer center columns
    center_count = np.sum(board[:, 3] == 1)
    score += center_count * 3

    # Count of my pieces
    my_pieces = np.sum(board == 1)
    opponent_pieces = np.sum(board == -1)
    score += (my_pieces - opponent_pieces) * 1

    # Evaluate potential threats
    score += evaluate_threats(board, 1) * 10
    score -= evaluate_threats(board, -1) * 10

    return score

def evaluate_threats(board, player):
    """Evaluate the number of potential threats for a player."""
    threat_score = 0

    # Check horizontal threats
    for row in range(6):
        for col in range(4):
            window = board[row][col:col+4]
            threat_score += evaluate_window(window, player)

    # Check vertical threats
    for row in range(3):
        for col in range(7):
            window = [board[row][col], board[row+1][col], board[row+2][col], board[row+3][col]]
            threat_score += evaluate_window(window, player)

    # Check diagonal threats (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            window = [board[row][col], board[row+1][col+1], board[row+2][col+2], board[row+3][col+3]]
            threat_score += evaluate_window(window, player)

    # Check diagonal threats (bottom-left to top-right)
    for row in range(3, 6):
        for col in range(4):
            window = [board[row][col], board[row-1][col+1], board[row-2][col+2], board[row-3][col+3]]
            threat_score += evaluate_window(window, player)

    return threat_score

def evaluate_window(window, player):
    """Evaluate a 4-cell window for threats."""
    opponent = -player
    score = 0

    # Count of player and opponent pieces in window
    player_count = sum(1 for cell in window if cell == player)
    opponent_count = sum(1 for cell in window if cell == opponent)
    empty_count = sum(1 for cell in window if cell == 0)

    # Three in a row with empty space
    if player_count == 3 and empty_count == 1:
        score += 5
    # Two in a row with two empty spaces
    elif player_count == 2 and empty_count == 2:
        score += 2
    # One in a row with three empty spaces
    elif player_count == 1 and empty_count == 3:
        score += 1

    # Block opponent's threats
    if opponent_count == 3 and empty_count == 1:
        score -= 4

    return score
