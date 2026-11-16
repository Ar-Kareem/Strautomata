
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 3x3 Tic Tac Toe game.

    Args:
      board: A 3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
      A tuple of two integers (0-2, 0-2) indicating the row and column you choose.
    """

    # 1. Check for winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    board[row][col] = 0  # Reset board
                    return (row, col)
                board[row][col] = 0  # Reset board

    # 2. Block opponent's winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    board[row][col] = 0  # Reset board
                    return (row, col)
                board[row][col] = 0  # Reset board

    # 3. Try to take the center if available
    if board[1][1] == 0:
        return (1, 1)

    # 4. Try to take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(r, c) for r, c in corners if board[r][c] == 0]
    if available_corners:
        return random.choice(available_corners)

    # 5. Take any available space
    available_moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                available_moves.append((row, col))

    if available_moves:
        return random.choice(available_moves)

    # If no moves are available (shouldn't happen in a valid game), return a random move
    return (0, 0)


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the board.

    Args:
      board: The Tic Tac Toe board.
      player: The player to check for a win (1 or -1).

    Returns:
      True if the player has won, False otherwise.
    """
    # Check rows
    for row in range(3):
        if all(board[row][col] == player for col in range(3)):
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
    # Example usage
    board = [
        [1, 0, -1],
        [0, -1, 1],
        [0, 1, 0]
    ]
    row, col = policy(board)
    print(f"Next move: ({row}, {col})")
