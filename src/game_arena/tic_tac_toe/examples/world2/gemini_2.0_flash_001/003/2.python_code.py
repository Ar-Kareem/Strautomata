
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-3, 0-3) indicating the row and column you choose.
    """

    size = 4

    # Check for winning move
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    return (row, col)
                board[row][col] = 0  # Reset

    # Check for blocking move
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    return (row, col)
                board[row][col] = 0  # Reset

    # Prioritize center
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for row, col in center_moves:
        if board[row][col] == 0:
            return (row, col)

    # Prioritize corners
    corner_moves = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for row, col in corner_moves:
        if board[row][col] == 0:
            return (row, col)

    # Choose an edge
    edge_moves = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
    for row, col in edge_moves:
        if board[row][col] == 0:
            return (row, col)

    # Choose a random empty cell
    empty_cells = []
    for row in range(size):
        for col in range(size):
            if board[row][col] == 0:
                empty_cells.append((row, col))
    if empty_cells:
        return random.choice(empty_cells)

    # No move possible (should not happen in a valid game)
    return (0, 0)

def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the game."""
    size = 4

    # Check rows
    for row in range(size):
        if all(board[row][col] == player for col in range(size)):
            return True

    # Check columns
    for col in range(size):
        if all(board[row][col] == player for row in range(size)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(size)):
        return True
    if all(board[i][size - 1 - i] == player for i in range(size)):
        return True

    return False
