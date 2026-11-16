
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)

    # Check for immediate winning move
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = board_array.copy()
            row = get_next_open_row(temp_board, col)
            temp_board[row][col] = 1
            if check_win(temp_board, 1):
                return col

    # Check for opponent's winning move to block
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = board_array.copy()
            row = get_next_open_row(temp_board, col)
            temp_board[row][col] = -1
            if check_win(temp_board, -1):
                return col

    # Evaluate all possible moves and choose the best one
    best_score = -np.inf
    best_col = 3  # default to center if all else fails

    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = board_array.copy()
            row = get_next_open_row(temp_board, col)
            temp_board[row][col] = 1
            score = evaluate_position(temp_board, 1)
            if score > best_score:
                best_score = score
                best_col = col

    return best_col

def is_valid_move(board, col):
    return board[0][col] == 0

def get_next_open_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1  # should not happen if is_valid_move is checked first

def check_win(board, player):
    # Check horizontal locations
    for row in range(6):
        for col in range(4):
            if board[row][col] == player and board[row][col+1] == player and board[row][col+2] == player and board[row][col+3] == player:
                return True

    # Check vertical locations
    for row in range(3):
        for col in range(7):
            if board[row][col] == player and board[row+1][col] == player and board[row+2][col] == player and board[row+3][col] == player:
                return True

    # Check positively sloped diagonals
    for row in range(3):
        for col in range(4):
            if board[row][col] == player and board[row+1][col+1] == player and board[row+2][col+2] == player and board[row+3][col+3] == player:
                return True

    # Check negatively sloped diagonals
    for row in range(3, 6):
        for col in range(4):
            if board[row][col] == player and board[row-1][col+1] == player and board[row-2][col+2] == player and board[row-3][col+3] == player:
                return True

    return False

def evaluate_position(board, player):
    score = 0

    # Center control
    center_array = [3, 4, 2, 5, 1, 6, 0]
    for col in range(7):
        for row in range(6):
            if board[row][col] == player:
                score += center_array[col]
            elif board[row][col] == -player:
                score -= center_array[col]

    # Evaluate horizontal
    for row in range(6):
        for col in range(4):
            window = board[row][col:col+4]
            score += evaluate_window(window, player)

    # Evaluate vertical
    for row in range(3):
        for col in range(7):
            window = [board[row][col], board[row+1][col], board[row+2][col], board[row+3][col]]
            score += evaluate_window(window, player)

    # Evaluate positive diagonal
    for row in range(3):
        for col in range(4):
            window = [board[row][col], board[row+1][col+1], board[row+2][col+2], board[row+3][col+3]]
            score += evaluate_window(window, player)

    # Evaluate negative diagonal
    for row in range(3, 6):
        for col in range(4):
            window = [board[row][col], board[row-1][col+1], board[row-2][col+2], board[row-3][col+3]]
            score += evaluate_window(window, player)

    return score

def evaluate_window(window, player):
    score = 0
    opponent = -player

    # Count player and opponent pieces in the window
    player_count = np.count_nonzero(window == player)
    opponent_count = np.count_nonzero(window == opponent)
    empty_count = np.count_nonzero(window == 0)

    # Player's potential threats
    if player_count == 3 and empty_count == 1:
        score += 5
    elif player_count == 2 and empty_count == 2:
        score += 2
    elif player_count == 1 and empty_count == 3:
        score += 1

    # Opponent's potential threats (we want to block these)
    if opponent_count == 3 and empty_count == 1:
        score -= 4
    elif opponent_count == 2 and empty_count == 2:
        score -= 2
    elif opponent_count == 1 and empty_count == 3:
        score -= 1

    return score
