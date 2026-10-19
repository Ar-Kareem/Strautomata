
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 3x3 Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists representing the board.
            0: empty, 1: AI, -1: opponent.

    Returns:
        A tuple (row, col) indicating the row and column to play (0-2).
    """
    # 1. Check for a winning move.
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    board[row][col] = 0  # Reset the board
                    return (row, col)
                board[row][col] = 0  # Reset the board

    # 2. Block opponent's winning move.
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    board[row][col] = 0  # Reset the board
                    return (row, col)
                board[row][col] = 0  # Reset the board

    # 3. Choose the center if available.
    if board[1][1] == 0:
        return (1, 1)

    # 4. Choose a corner if available.
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(row, col) for row, col in corners if board[row][col] == 0]
    if available_corners:
        return random.choice(available_corners)

    # 5. Choose any available move.
    available_moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                available_moves.append((row, col))

    if available_moves:
        return random.choice(available_moves)
    else:
        # No moves available (board full). Should not happen in a valid game.
        return (0, 0)


def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the Tic Tac Toe game."""
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


if __name__ == '__main__':
    # Example usage:
    board = [
        [1, -1, 0],
        [-1, 1, 0],
        [0, 0, -1]
    ]
    row, col = policy(board)
    print(f"Next move: ({row}, {col})")
