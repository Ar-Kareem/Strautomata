
import random
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    player = 1
    opponent = -1

    # Check for immediate win
    winning_move = find_winning_move(board_array, player)
    if winning_move is not None:
        return winning_move

    # Check for opponent's winning move to block
    blocking_move = find_winning_move(board_array, opponent)
    if blocking_move is not None:
        return blocking_move

    # Get all valid moves
    valid_moves = [col for col in range(7) if board_array[0][col] == 0]

    if not valid_moves:
        return random.choice(range(7))  # Shouldn't happen as game would be over

    # Evaluate all valid moves
    move_scores = []
    for col in valid_moves:
        # Create a temporary board with the move
        temp_board = board_array.copy()
        row = find_next_empty_row(temp_board, col)
        temp_board[row][col] = player

        # Calculate score for this move
        score = evaluate_board(temp_board, player)

        # Add some randomness to break ties
        score += random.random() * 0.01

        move_scores.append((score, col))

    # Sort moves by score (descending)
    move_scores.sort(reverse=True, key=lambda x: x[0])

    # Return the best move
    return move_scores[0][1]

def find_winning_move(board: np.ndarray, player: int) -> int:
    """Check if the player can win in the next move and return the winning column."""
    for col in range(7):
        if board[0][col] != 0:
            continue  # Column is full

        # Create a temporary board with the move
        temp_board = board.copy()
        row = find_next_empty_row(temp_board, col)
        temp_board[row][col] = player

        # Check if this move wins
        if check_win(temp_board, row, col, player):
            return col

    return None

def find_next_empty_row(board: np.ndarray, col: int) -> int:
    """Find the next empty row in the given column."""
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1  # Shouldn't happen as we check if column is full first

def check_win(board: np.ndarray, row: int, col: int, player: int) -> bool:
    """Check if the last move at (row, col) results in a win for the player."""
    # Check horizontal
    count = 0
    for c in range(max(0, col-3), min(7, col+4)):
        if board[row][c] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0

    # Check vertical
    count = 0
    for r in range(max(0, row-3), min(6, row+4)):
        if board[r][col] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0

    # Check diagonal (top-left to bottom-right)
    count = 0
    for i in range(-3, 4):
        r, c = row + i, col + i
        if 0 <= r < 6 and 0 <= c < 7:
            if board[r][c] == player:
                count += 1
                if count >= 4:
                    return True
            else:
                count = 0
        else:
            count = 0

    # Check diagonal (top-right to bottom-left)
    count = 0
    for i in range(-3, 4):
        r, c = row + i, col - i
        if 0 <= r < 6 and 0 <= c < 7:
            if board[r][c] == player:
                count += 1
                if count >= 4:
                    return True
            else:
                count = 0
        else:
            count = 0

    return False

def evaluate_board(board: np.ndarray, player: int) -> float:
    """Evaluate the board position for the given player."""
    opponent = -player
    score = 0.0

    # Center control
    center_count = np.sum(board[:, 3] == player) - np.sum(board[:, 3] == opponent)
    score += center_count * 0.5

    # Count potential threats
    player_threats = count_threats(board, player)
    opponent_threats = count_threats(board, opponent)
    score += (player_threats - opponent_threats) * 10.0

    # Disc height (lower discs are better)
    for col in range(7):
        for row in range(6):
            if board[row][col] == player:
                score += (5 - row) * 0.1
            elif board[row][col] == opponent:
                score -= (5 - row) * 0.1

    return score

def count_threats(board: np.ndarray, player: int) -> int:
    """Count the number of potential winning lines (threats) for the player."""
    threats = 0

    # Check horizontal threats
    for row in range(6):
        for col in range(4):
            window = board[row, col:col+4]
            if np.sum(window == player) == 3 and np.sum(window == 0) == 1:
                threats += 1

    # Check vertical threats
    for row in range(3):
        for col in range(7):
            window = board[row:row+4, col]
            if np.sum(window == player) == 3 and np.sum(window == 0) == 1:
                threats += 1

    # Check diagonal (top-left to bottom-right) threats
    for row in range(3):
        for col in range(4):
            window = [board[row+i][col+i] for i in range(4)]
            if window.count(player) == 3 and window.count(0) == 1:
                threats += 1

    # Check diagonal (top-right to bottom-left) threats
    for row in range(3):
        for col in range(3, 7):
            window = [board[row+i][col-i] for i in range(4)]
            if window.count(player) == 3 and window.count(0) == 1:
                threats += 1

    return threats
