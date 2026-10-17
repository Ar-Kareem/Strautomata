
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists representing the Tic Tac Toe board.
               0 = empty, 1 = AI, -1 = opponent.

    Returns:
        A tuple (row, col) indicating the row and column of the chosen move.
    """

    # Check for winning move
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    board[row][col] = 0  # Reset board
                    return (row, col)
                board[row][col] = 0  # Reset board

    # Check for blocking move
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    board[row][col] = 0  # Reset board
                    return (row, col)
                board[row][col] = 0  # Reset board

    # Prefer center position if available
    if board[1][1] == 0:
        return (1, 1)

    # Prefer corner positions if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(r, c) for r, c in corners if board[r][c] == 0]
    if available_corners:
        return random.choice(available_corners)

    # Choose a random empty cell
    empty_cells = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                empty_cells.append((row, col))

    if empty_cells:
        return random.choice(empty_cells)
    else:
        return (0,0) #Should not happen in normal games as this would imply the board being full

def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the Tic Tac Toe game.

    Args:
        board: The Tic Tac Toe board.
        player: The player to check for (1 or -1).

    Returns:
        True if the player has won, False otherwise.
    """

    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True

    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True

    return False
