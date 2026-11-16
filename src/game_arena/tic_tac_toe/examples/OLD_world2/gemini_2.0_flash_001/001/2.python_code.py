
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Selects the next move for a 4x4 Tic Tac Toe game.

    Args:
    board (list[list[int]]): A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
    tuple[int, int]: A tuple of two integers (0-3, 0-3) indicating the row and column you choose.
    """

    # Convert the board to a NumPy array for easier manipulation
    board = np.array(board)

    # 1. Check for winning moves
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                board[i, j] = 1  # Temporarily place our move
                if check_win(board, 1):
                    return (i, j)  # This move wins the game
                board[i, j] = 0  # Reset the board

    # 2. Check for blocking moves
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                board[i, j] = -1  # Temporarily place opponent's move
                if check_win(board, -1):
                    return (i, j)  # Block opponent's winning move
                board[i, j] = 0  # Reset the board

    # 3. Prioritize center positions
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for move in center_moves:
        if board[move[0], move[1]] == 0:
            return move

    # 4. Choose the first available move (fallback strategy)
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                return (i, j)

    # If no moves are available (board is full -- which is unexpected in a normal game), return (0, 0) as a safe default.
    return (0, 0)


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game.

    Args:
    board (np.ndarray): The game board.
    player (int): The player to check for (1 or -1).

    Returns:
    bool: True if the player has won, False otherwise.
    """

    # Check rows
    for i in range(4):
        if all(board[i, :] == player):
            return True

    # Check columns
    for j in range(4):
        if all(board[:, j] == player):
            return True

    # Check diagonals
    if all(np.diag(board) == player):
        return True
    if all(np.diag(np.fliplr(board)) == player):
        return True

    return False


if __name__ == '__main__':
    # Example usage:
    board_example = [
        [0, 0, 0, 0],
        [0, 1, -1, 0],
        [0, -1, 1, 0],
        [0, 0, 0, 0],
    ]
    next_move = policy(board_example)
    print(f"Next move: {next_move}")

    board_example2 = [
        [1, 1, 1, 0],
        [0, -1, 0, 0],
        [0, -1, 0, 0],
        [0, 0, 0, 0],
    ]
    next_move2 = policy(board_example2)
    print(f"Next move2: {next_move2}")

    board_example3 = [
        [1, -1, 1, 0],
        [0, -1, 0, 0],
        [0, -1, 0, 0],
        [0, 1, 0, 0],
    ]
    next_move3 = policy(board_example3)
    print(f"Next move3: {next_move3}")
