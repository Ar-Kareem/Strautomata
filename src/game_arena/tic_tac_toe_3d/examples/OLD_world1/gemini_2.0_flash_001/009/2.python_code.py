
import numpy as np

def check_win(board: list[list[list[int]]], player: int) -> bool:
    """Checks if the given player has won the 3D Tic Tac Toe game.
    """
    n = len(board)

    # Check rows, columns, and depth
    for i in range(n):
        for j in range(n):
            # Rows
            if all(board[i][j][k] == player for k in range(n)):
                return True
            # Columns
            if all(board[i][k][j] == player for k in range(n)):
                return True
            # Depth
            if all(board[k][i][j] == player for k in range(n)):
                return True

    # Check diagonals
    for i in range(n):
        # Main diagonals
        if all(board[i][k][k] == player for k in range(n)):
            return True
        if all(board[i][k][n - 1 - k] == player for k in range(n)):
            return True
        if all(board[k][i][k] == player for k in range(n)):
            return True
        if all(board[k][i][n - 1 - k] == player for k in range(n)):
            return True
        if all(board[k][k][i] == player for k in range(n)):
            return True
        if all(board[k][n-1-k][i] == player for k in range(n)):
            return True

    # Check space diagonals
    if all(board[k][k][k] == player for k in range(n)):
        return True
    if all(board[k][k][n - 1 - k] == player for k in range(n)):
        return True
    if all(board[k][n - 1 - k][k] == player for k in range(n)):
        return True
    if all(board[k][n - 1 - k][n - 1 - k] == player for k in range(n)):
        return True

    return False


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Makes a move for the 3D Tic Tac Toe game.
    """
    n = len(board)

    # 1. Check for a winning move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1  # Try the move
                    if check_win(board, 1):
                        return (i, j, k)  # Winning move found
                    board[i][j][k] = 0  # Undo the move

    # 2. Block opponent's winning move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    board[i][j][k] = -1  # Try the move for opponent
                    if check_win(board, -1):
                        return (i, j, k)  # Block the opponent
                    board[i][j][k] = 0  # Undo the move

    # 3. Make a random move
    available_moves = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    available_moves.append((i, j, k))

    if available_moves:
        return available_moves[0]  # Choose the first available move
    else:
        return (0, 0, 0) #Should Never Happen - Board Full.
