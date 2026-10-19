
import random

def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the Tic Tac Toe board."""
    size = len(board)

    # Check rows and columns
    for i in range(size):
        if all(board[i][j] == player for j in range(size)):
            return True
        if all(board[j][i] == player for j in range(size)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(size)):
        return True
    if all(board[i][size - 1 - i] == player for i in range(size)):
        return True

    return False

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game.
    """
    size = len(board)

    # 1. Check for winning move
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    return (row, col)
                board[row][col] = 0  # Reset

    # 2. Check for blocking move
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    return (row, col)
                board[row][col] = 0  # Reset

    # 3. Center preference
    centers = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for row, col in centers:
        if board[row][col] == 0:
            return (row, col)

    # 4. Corner preference
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)

    # 5. Random move
    empty_cells = []
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                empty_cells.append((row, col))

    if empty_cells:
        return random.choice(empty_cells)

    # If no moves are available (board full - unlikely in a competition, but robust.)
    return (0, 0)
