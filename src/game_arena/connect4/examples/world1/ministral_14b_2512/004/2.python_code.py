
import numpy as np

def is_win(board, row, col, player):
    """Check if placing a disc at (row, col) for player results in a win."""
    directions = [
        (0, 1),   # horizontal
        (1, 0),    # vertical
        (1, 1),    # diagonal down-right
        (1, -1)    # diagonal down-left
    ]

    for dr, dc in directions:
        count = 1  # the current disc
        # Check in the positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        # Check in the negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False

def simulate_drop(board, col, player):
    """Simulate dropping a disc in the specified column for the given player."""
    new_board = [row.copy() for row in board]
    for row in range(5, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            return new_board
    return None  # column is full

def evaluate_column(board, col, player):
    """Evaluate how good a move in 'col' is for 'player'."""
    # Simulate the drop
    new_board = simulate_drop(board, col, player)
    if new_board is None:
        return -float('inf')  # column is full

    # Check if this move wins
    for row in range(6):
        if new_board[row][col] == player and is_win(new_board, row, col, player):
            return 100  # immediate win

    # Evaluate potential threats and opportunities
    score = 0

    # Check for potential two-in-a-row or three-in-a-row
    for row in range(6):
        if new_board[row][col] == player:
            # Check horizontal
            for dc in [-1, 1]:
                if 0 <= col + dc < 7 and new_board[row][col + dc] == player:
                    # Check if there's an empty space adjacent
                    if 0 <= col + 2 * dc < 7 and new_board[row][col + 2 * dc] == 0:
                        score += 5
                    if 0 <= col - dc < 7 and new_board[row][col - dc] == 0:
                        score += 5
            # Check vertical
            for dr in [-1, 1]:
                if 0 <= row + dr < 6 and new_board[row + dr][col] == player:
                    if 0 <= row + 2 * dr < 6 and new_board[row + 2 * dr][col] == 0:
                        score += 5
                    if 0 <= row - dr < 6 and new_board[row - dr][col] == 0:
                        score += 5
            # Check diagonals
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                if 0 <= row + dr < 6 and 0 <= col + dc < 7 and new_board[row + dr][col + dc] == player:
                    if 0 <= row + 2 * dr < 6 and 0 <= col + 2 * dc < 7 and new_board[row + 2 * dr][col + 2 * dc] == 0:
                        score += 5
                    if 0 <= row - dr < 6 and 0 <= col - dc < 7 and new_board[row - dr][col - dc] == 0:
                        score += 5

    # Prefer center columns
    center_pref = [0, 1, 2, 3, 2, 1, 0]
    score += center_pref[col]

    return score

def policy(board):
    """Choose the best column to drop a disc."""
    # First, check for immediate win
    for col in range(7):
        new_board = simulate_drop(board, col, 1)
        if new_board is not None:
            for row in range(6):
                if new_board[row][col] == 1 and is_win(new_board, row, col, 1):
                    return col

    # Then, check for opponent's immediate win and block
    for col in range(7):
        new_board = simulate_drop(board, col, -1)
        if new_board is not None:
            for row in range(6):
                if new_board[row][col] == -1 and is_win(new_board, row, col, -1):
                    return col

    # If no immediate win or block, evaluate all columns and choose the best
    best_col = -1
    best_score = -float('inf')

    for col in range(7):
        # Skip full columns
        if board[0][col] != 0:
            continue
        score = evaluate_column(board, col, 1)
        if score > best_score:
            best_score = score
            best_col = col

    # If no valid column found (shouldn't happen for empty board), return center
    if best_col == -1:
        return 3  # center column

    return best_col
