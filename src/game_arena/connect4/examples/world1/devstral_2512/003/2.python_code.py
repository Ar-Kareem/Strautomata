
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert the board to a numpy array for easier manipulation
    board_array = np.array(board)

    # Check for immediate win
    for col in range(7):
        if board_array[0][col] != 0:
            continue  # Column is full
        # Simulate placing my disc in this column
        temp_board = board_array.copy()
        for row in range(5, -1, -1):
            if temp_board[row][col] == 0:
                temp_board[row][col] = 1
                break
        if check_win(temp_board, 1):
            return col

    # Check for opponent's win and block it
    for col in range(7):
        if board_array[0][col] != 0:
            continue  # Column is full
        # Simulate placing opponent's disc in this column
        temp_board = board_array.copy()
        for row in range(5, -1, -1):
            if temp_board[row][col] == 0:
                temp_board[row][col] = -1
                break
        if check_win(temp_board, -1):
            return col

    # Evaluate strategic moves using a heuristic
    best_col = -1
    best_score = -np.inf
    for col in range(7):
        if board_array[0][col] != 0:
            continue  # Column is full
        # Simulate placing my disc in this column
        temp_board = board_array.copy()
        for row in range(5, -1, -1):
            if temp_board[row][col] == 0:
                temp_board[row][col] = 1
                break
        # Evaluate the board state
        score = evaluate_board(temp_board)
        if score > best_score:
            best_score = score
            best_col = col

    # If no strategic move is found, default to the center column
    if best_col == -1:
        for col in [3, 2, 4, 1, 5, 0, 6]:
            if board_array[0][col] == 0:
                return col

    return best_col

def check_win(board: np.ndarray, player: int) -> bool:
    # Check horizontal, vertical, and diagonal lines for a win
    for row in range(6):
        for col in range(7):
            if board[row][col] != player:
                continue
            # Check horizontal
            if col + 3 < 7 and all(board[row][col + i] == player for i in range(4)):
                return True
            # Check vertical
            if row + 3 < 6 and all(board[row + i][col] == player for i in range(4)):
                return True
            # Check diagonal (down-right)
            if row + 3 < 6 and col + 3 < 7 and all(board[row + i][col + i] == player for i in range(4)):
                return True
            # Check diagonal (up-right)
            if row - 3 >= 0 and col + 3 < 7 and all(board[row - i][col + i] == player for i in range(4)):
                return True
    return False

def evaluate_board(board: np.ndarray) -> float:
    # Evaluate the board state using a heuristic
    score = 0.0

    # Center control
    center_column = 3
    for row in range(6):
        if board[row][center_column] == 1:
            score += 0.5
        elif board[row][center_column] == -1:
            score -= 0.5

    # Count potential threats for both players
    for player in [1, -1]:
        for row in range(6):
            for col in range(7):
                if board[row][col] != player:
                    continue
                # Check horizontal threats
                if col + 3 < 7:
                    line = board[row][col:col+4]
                    if np.sum(line == player) == 3 and np.sum(line == 0) == 1:
                        score += 0.2 * player
                # Check vertical threats
                if row + 3 < 6:
                    line = board[row:row+4, col]
                    if np.sum(line == player) == 3 and np.sum(line == 0) == 1:
                        score += 0.2 * player
                # Check diagonal (down-right) threats
                if row + 3 < 6 and col + 3 < 7:
                    line = [board[row + i][col + i] for i in range(4)]
                    if np.sum(np.array(line) == player) == 3 and np.sum(np.array(line) == 0) == 1:
                        score += 0.2 * player
                # Check diagonal (up-right) threats
                if row - 3 >= 0 and col + 3 < 7:
                    line = [board[row - i][col + i] for i in range(4)]
                    if np.sum(np.array(line) == player) == 3 and np.sum(np.array(line) == 0) == 1:
                        score += 0.2 * player

    return score
