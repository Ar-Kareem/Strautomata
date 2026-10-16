
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board = np.array(board, dtype=int)
    rows, cols = board.shape

    # Check for immediate winning moves
    winning_move = find_winning_move(board, 1)
    if winning_move is not None:
        return winning_move

    # Block opponent's immediate winning moves
    opponent_winning_move = find_winning_move(board, -1)
    if opponent_winning_move is not None:
        return opponent_winning_move

    # Evaluate all possible moves using a heuristic
    best_score = -float('inf')
    best_col = None

    for col in range(cols):
        if board[0][col] != 0:  # Skip full columns
            continue

        # Create a copy of the board and make the move
        temp_board = board.copy()
        row = get_next_open_row(temp_board, col)
        temp_board[row][col] = 1

        # Evaluate the position
        score = evaluate_position(temp_board, 1)

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_col = col

    return best_col

def find_winning_move(board: np.ndarray, player: int) -> int:
    """Check if the player has a winning move in any column."""
    for col in range(board.shape[1]):
        if board[0][col] != 0:  # Skip full columns
            continue

        # Make the move
        row = get_next_open_row(board, col)
        temp_board = board.copy()
        temp_board[row][col] = player

        # Check if this move wins
        if check_win(temp_board, player):
            return col
    return None

def get_next_open_row(board: np.ndarray, col: int) -> int:
    """Find the next open row in a column."""
    for row in range(board.shape[0]):
        if board[row][col] == 0:
            return row
    return -1  # Column is full

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the player has won on the board."""
    # Check horizontal locations
    for c in range(board.shape[1] - 3):
        for r in range(board.shape[0]):
            if (board[r][c] == player and board[r][c+1] == player and
                board[r][c+2] == player and board[r][c+3] == player):
                return True

    # Check vertical locations
    for c in range(board.shape[1]):
        for r in range(board.shape[0] - 3):
            if (board[r][c] == player and board[r+1][c] == player and
                board[r+2][c] == player and board[r+3][c] == player):
                return True

    # Check positively sloped diagonals
    for c in range(board.shape[1] - 3):
        for r in range(board.shape[0] - 3):
            if (board[r][c] == player and board[r+1][c+1] == player and
                board[r+2][c+2] == player and board[r+3][c+3] == player):
                return True

    # Check negatively sloped diagonals
    for c in range(board.shape[1] - 3):
        for r in range(3, board.shape[0]):
            if (board[r][c] == player and board[r-1][c+1] == player and
                board[r-2][c+2] == player and board[r-3][c+3] == player):
                return True

    return False

def evaluate_position(board: np.ndarray, player: int) -> int:
    """Evaluate the board position from the player's perspective."""
    score = 0

    # Center control
    center_array = [int(i) for i in list(board[:, board.shape[1]//2])]
    center_count = center_array.count(player)
    score += center_count * 3

    # Horizontal evaluation
    for r in range(board.shape[0]):
        row_array = [int(i) for i in list(board[r, :])]
        for c in range(board.shape[1] - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)

    # Vertical evaluation
    for c in range(board.shape[1]):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(board.shape[0] - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)

    # Positive diagonal evaluation
    for r in range(board.shape[0] - 3):
        for c in range(board.shape[1] - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    # Negative diagonal evaluation
    for r in range(3, board.shape[0]):
        for c in range(board.shape[1] - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, player)

    return score

def evaluate_window(window: list, player: int) -> int:
    """Evaluate a window of 4 cells."""
    score = 0
    opponent = -player

    if window.count(player) == 4:
        score += 100
    elif window.count(player) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(player) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opponent) == 3 and window.count(0) == 1:
        score -= 4

    return score
