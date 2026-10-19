
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Given a 3x3x3 Tic Tac Toe board, return the next move (x, y, z) as a tuple of integers.

    The strategy is to:
    1. Prioritize winning moves.
    2. Prioritize blocking opponent's winning moves.
    3. If no winning or blocking moves are available, make a random valid move.

    Args:
        board (list[list[list[int]]]): A 3x3x3 Tic Tac Toe board represented as a list of lists of lists.
                                         0 represents an empty cell, 1 represents the AI's move, and -1 represents the opponent's move.

    Returns:
        tuple[int, int, int]: A tuple representing the (x, y, z) coordinates of the AI's next move.
    """

    board_np = np.array(board)
    n = board_np.shape[0]

    # Check for winning moves
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    board_np[x, y, z] = 1
                    if check_win(board_np, 1):
                        return (x, y, z)
                    board_np[x, y, z] = 0

    # Check for blocking moves
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    board_np[x, y, z] = -1
                    if check_win(board_np, -1):
                        return (x, y, z)
                    board_np[x, y, z] = 0

    # Make a random valid move
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board_np[x, y, z] == 0:
                    return (x, y, z)

    return (-1, -1, -1)  # Should not happen, but return a safe value if the board is full


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the Tic Tac Toe game.

    This function checks all possible winning combinations (rows, columns, diagonals)
    to determine if the given player has achieved a win condition.

    Args:
        board (np.ndarray): The Tic Tac Toe board represented as a numpy array.
        player (int): The player to check for a win (1 or -1).

    Returns:
        bool: True if the player has won, False otherwise.
    """
    n = board.shape[0]

    # Check rows
    for i in range(n):
        for j in range(n):
            if all(board[i, j, k] == player for k in range(n)):
                return True
            if all(board[i, k, j] == player for k in range(n)):
                return True
            if all(board[k, i, j] == player for k in range(n)):
                return True

    # Check diagonals
    for i in range(n):
        if all(board[i, k, k] == player for k in range(n)):
            return True
        if all(board[i, k, n - 1 - k] == player for k in range(n)):
            return True
        if all(board[k, i, k] == player for k in range(n)):
            return True
        if all(board[k, i, n - 1 - k] == player for k in range(n)):
            return True
        if all(board[k, k, i] == player for k in range(n)):
            return True
        if all(board[k, n - 1 - k, i] == player for k in range(n)):
            return True

    # Check main diagonals
    if all(board[k, k, k] == player for k in range(n)):
        return True
    if all(board[k, k, n - 1 - k] == player for k in range(n)):
        return True
    if all(board[k, n - 1 - k, k] == player for k in range(n)):
        return True
    if all(board[k, n - 1 - k, n - 1 - k] == player for k in range(n)):
        return True
    
    return False
