
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 3D Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers 0-2 indicating the empty cell you choose.
    """
    board = np.array(board)
    # Prioritize winning moves
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z, y, x] == 0:
                    temp_board = board.copy()
                    temp_board[z, y, x] = 1
                    if check_win(temp_board, 1):
                        return (z, y, x)
    # Block opponent winning moves
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z, y, x] == 0:
                    temp_board = board.copy()
                    temp_board[z, y, x] = -1
                    if check_win(temp_board, -1):
                        return (z, y, x)

    # Choose center if available
    if board[1, 1, 1] == 0:
        return (1, 1, 1)

    # Choose corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
               (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1),
               (1, 1, 0), (1, 1, 2)]

    for corner in corners:
        if board[corner[0], corner[1], corner[2]] == 0:
            return corner

    # Choose any available cell
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z, y, x] == 0:
                    return (z, y, x)

    # No available moves
    return (0, 0, 0)


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the 3D Tic Tac Toe game.

    Args:
        board: A 3x3x3 numpy array representing the game board.
        player: The player to check for a win (1 or -1).

    Returns:
        True if the player has won, False otherwise.
    """
    # Check rows, columns, and depths
    for i in range(3):
        for j in range(3):
            if all(board[i, j, :] == player) or all(board[i, :, j] == player) or all(board[:, i, j] == player):
                return True
    # Check diagonals
    for i in range(3):
        if all(board[i, range(3), range(3)] == player) or all(board[i, range(3), range(2, -1, -1)] == player) \
           or all(board[range(3), i, range(3)] == player) or all(board[range(3), i, range(2, -1, -1)] == player) \
           or all(board[range(3), range(3), i] == player) or all(board[range(3), range(2, -1, -1), i] == player):
            return True

    # Check main diagonals through the cube
    if all(board[range(3), range(3), range(3)] == player) or all(board[range(3), range(3), range(2, -1, -1)] == player) \
        or all(board[range(3), range(2, -1, -1), range(3)] == player) or all(board[range(3), range(2, -1, -1), range(2, -1, -1)] == player):
        return True
    return False

if __name__ == '__main__':
    # Example usage
    board = [
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    ]

    move = policy(board)
    print(f"Next move: {move}")
