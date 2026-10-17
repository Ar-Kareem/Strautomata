
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Selects the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-3, 0-3) indicating the row and column to choose.
    """

    # Convert the board to a NumPy array for easier manipulation
    board = np.array(board)

    # 1. Check for winning moves for yourself
    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                # Temporarily place your mark
                board[row, col] = 1
                # Check if this move wins the game
                if check_win(board, 1):
                    return (row, col)
                # Reset the move
                board[row, col] = 0

    # 2. Check for winning moves for the opponent and block them
    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                # Temporarily place the opponent's mark
                board[row, col] = -1
                # Check if this move wins the game for the opponent
                if check_win(board, -1):
                    return (row, col)
                # Reset the move
                board[row, col] = 0

    # 3. Choose the center if its free
    if board[1, 1] == 0:
        return (1, 1)
    if board[2, 2] == 0:
        return (2, 2)
    if board[1, 2] == 0:
        return (1, 2)
    if board[2, 1] == 0:
        return (2, 1)

    # 4. Choose the first available spot at random
    for row in range(4):
        for col in range(4):
            if board[row, col] == 0:
                return (row, col)
    # If no spots available. Shouldn't happen but return (0, 0) for safety
    return (0, 0)


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game.

    Args:
        board: The current state of the board.
        player: The player to check (1 or -1).

    Returns:
        True if the player has won, False otherwise.
    """

    # Check rows
    for row in range(4):
        if all(board[row, :] == player):
            return True

    # Check columns
    for col in range(4):
        if all(board[:, col] == player):
            return True

    # Check diagonals
    if all(np.diag(board) == player):
        return True
    if all(np.diag(np.fliplr(board)) == player):
        return True

    return False


if __name__ == '__main__':
    # Example usage
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    print(f"Move: {policy(board)}") # expects some tuple, e.g. (0, 0)
    board = [
        [1, -1, 1, 0],
        [-1, -1, 1, 0],
        [1, 0, -1, 0],
        [0, 0, 0, 0]
    ]
    print(f"Move: {policy(board)}") # returns tuple
