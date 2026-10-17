
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists representing the Tic Tac Toe board.
               0: empty, 1: player (AI), -1: opponent.

    Returns:
        A tuple of two integers (row, col) indicating the chosen move.
    """

    # Check for immediate win M=1 moves
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1  # Try placing our piece
                if check_win(board, 1):
                    return (r, c)
                board[r][c] = 0  # Undo
    
    # Check for opponent's immediate win (block) M=2 moves
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1  # Try placing opponent's piece
                if check_win(board, -1):
                    return (r, c)
                board[r][c] = 0  # Undo

    # Try to take the center
    if board[1][1] == 0:
        return (1, 1)

    # Try to take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)  # Randomize corner choice
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(sides)  # Randomize side choice
    for r, c in sides:
        if board[r][c] == 0:
            return (r, c)

    # If no strategic move, pick the first available empty spot (should not happen)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)

    # Should not reach here in a valid Tic Tac Toe game condition
    return (-1, -1)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for r in range(3):
        if all(board[r][c] == player for c in range(3)):
            return True
    # Check columns
    for c in range(3):
        if all(board[r][c] == player for r in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

