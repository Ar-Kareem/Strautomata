
import random
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    player = 1  # Current player is always 1
    opponent = -1

    # Check for immediate winning move
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array.copy(), col, player)
            if check_win(temp_board, player):
                return col

    # Check for opponent's winning move to block
    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array.copy(), col, opponent)
            if check_win(temp_board, opponent):
                return col

    # Evaluate all possible moves with scoring
    best_score = -float('inf')
    best_moves = []

    for col in range(7):
        if is_valid_move(board_array, col):
            temp_board = make_move(board_array.copy(), col, player)
            score = evaluate_position(temp_board, player)

            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)

    # If multiple moves have same best score, choose randomly among them
    if best_moves:
        return random.choice(best_moves)

    # Fallback: choose random valid move
    valid_moves = [col for col in range(7) if is_valid_move(board_array, col)]
    return random.choice(valid_moves)

def is_valid_move(board, col):
    return board[0][col] == 0

def make_move(board, col, player):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return board
    return board  # Shouldn't happen if is_valid_move was checked

def check_win(board, player):
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

def evaluate_position(board, player):
    opponent = -player
    score = 0

    # Center control
    center_count = np.sum(board[:, 3] == player)
    score += center_count * 3

    # Count potential threats
    score += count_potential_threats(board, player) * 10
    score -= count_potential_threats(board, opponent) * 8

    # Count pieces
    player_pieces = np.sum(board == player)
    opponent_pieces = np.sum(board == opponent)
    score += (player_pieces - opponent_pieces)

    return score

def count_potential_threats(board, player):
    count = 0

    # Check horizontal
    for row in range(6):
        for col in range(4):
            window = board[row, col:col+4]
            if np.sum(window == player) == 3 and np.sum(window == 0) == 1:
                count += 1

    # Check vertical
    for row in range(3):
        for col in range(7):
            window = board[row:row+4, col]
            if np.sum(window == player) == 3 and np.sum(window == 0) == 1:
                count += 1

    # Check diagonal (top-left to bottom-right)
    for row in range(3):
        for col in range(4):
            window = [board[row+i][col+i] for i in range(4)]
            if window.count(player) == 3 and window.count(0) == 1:
                count += 1

    # Check diagonal (bottom-left to top-right)
    for row in range(3, 6):
        for col in range(4):
            window = [board[row-i][col+i] for i in range(4)]
            if window.count(player) == 3 and window.count(0) == 1:
                count += 1

    return count
