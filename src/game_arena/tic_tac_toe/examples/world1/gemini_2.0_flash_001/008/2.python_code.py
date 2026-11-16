
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 3x3 Tic Tac Toe game.
    """

    # 1. Check for winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    board[row][col] = 0  # Reset the board
                    return row, col
                board[row][col] = 0  # Reset the board

    # 2. Check for blocking moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    board[row][col] = 0  # Reset the board
                    return row, col
                board[row][col] = 0  # Reset the board

    # 3. Take the center
    if board[1][1] == 0:
        return 1, 1

    # 4. Take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for row, col in corners:
        if board[row][col] == 0:
            return row, col

    # 5. Take an edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for row, col in edges:
        if board[row][col] == 0:
            return row, col

    # 6. If all else fails, return a random move
    available_moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                available_moves.append((row, col))

    if available_moves:  # Should always be true in a valid game state
        return random.choice(available_moves)
    else:
        return 0, 0  # Should not happen in normal game flow


def check_win(board: list[list[int]], player: int) -> bool:
    """
    Checks if the given player has won the game.
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
