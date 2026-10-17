
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers (x, y, z) indicating the empty cell you choose (0-2).
    """
    board_np = np.array(board)
    empty_cells = np.where(board_np == 0)
    empty_cells = list(zip(empty_cells[0], empty_cells[1], empty_cells[2]))

    # Prioritize winning moves
    for x, y, z in empty_cells:
        board_np[x, y, z] = 1
        if check_win(board_np, 1):
            return (x, y, z)
        board_np[x, y, z] = 0  # Reset

    # Block opponent's winning moves
    for x, y, z in empty_cells:
        board_np[x, y, z] = -1
        if check_win(board_np, -1):
            return (x, y, z)
        board_np[x, y, z] = 0  # Reset

    # Choose a random empty cell if no winning or blocking moves are available
    if empty_cells:
        return empty_cells[0]
    else:
        return (0, 0, 0)  # Should not happen in a valid game


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    n = board.shape[0]

    # Check rows, columns, and depths
    for i in range(n):
        for j in range(n):
            if all(board[i, j, k] == player for k in range(n)):
                return True
            if all(board[i, k, j] == player for k in range(n)):
                return True
            if all(board[k, i, j] == player for k in range(n)):
                return True

    # Check diagonals on each face
    for i in range(n):
        if all(board[i, k, k] == player for k in range(n)):
            return True
        if all(board[i, k, n-1-k] == player for k in range(n)):
            return True
        if all(board[k, i, k] == player for k in range(n)):
            return True
        if all(board[k, i, n-1-k] == player for k in range(n)):
            return True
        if all(board[k, k, i] == player for k in range(n)):
            return True
        if all(board[k, n-1-k, i] == player for k in range(n)):
            return True

    # Check space diagonals
    if all(board[k, k, k] == player for k in range(n)):
        return True
    if all(board[k, k, n-1-k] == player for k in range(n)):
        return True
    if all(board[k, n-1-k, k] == player for k in range(n)):
        return True
    if all(board[k, n-1-k, n-1-k] == player for k in range(n)):
        return True

    return False


if __name__ == '__main__':
    # Example usage:
    board = [
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    ]
    next_move = policy(board)
    print(f"Next move: {next_move}")
