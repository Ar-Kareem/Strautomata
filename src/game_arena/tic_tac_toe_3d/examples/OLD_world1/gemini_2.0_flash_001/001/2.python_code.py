
import numpy as np

def check_win(board: list[list[list[int]]], player: int) -> bool:
    """Checks if the given player has won the Tic Tac Toe game."""
    n = len(board)

    # Check rows
    for i in range(n):
        for j in range(n):
            if all(board[i][j][k] == player for k in range(n)):
                return True
            if all(board[i][k][j] == player for k in range(n)):
                return True
            if all(board[k][i][j] == player for k in range(n)):
                return True

    # Check diagonals
    for i in range(n):
        if all(board[i][k][k] == player for k in range(n)):
            return True
        if all(board[i][k][n-1-k] == player for k in range(n)):
            return True
        if all(board[k][i][k] == player for k in range(n)):
            return True
        if all(board[k][i][n-1-k] == player for k in range(n)):
            return True
        if all(board[k][k][i] == player for k in range(n)):
            return True
        if all(board[k][n-1-k][i] == player for k in range(n)):
            return True

    if all(board[k][k][k] == player for k in range(n)):
        return True
    if all(board[k][k][n-1-k] == player for k in range(n)):
        return True
    if all(board[k][n-1-k][k] == player for k in range(n)):
        return True
    if all(board[k][n-1-k][n-1-k] == player for k in range(n)):
        return True

    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for the 3x3x3 Tic Tac Toe game.
    Prioritizes winning moves, then blocking opponent's winning moves,
    then choosing the center, then choosing a random empty cell.
    """
    n = len(board)
    my_player = 1
    opponent_player = -1

    # 1. Check for winning move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    board[i][j][k] = my_player
                    if check_win(board, my_player):
                        return (i, j, k)
                    board[i][j][k] = 0  # Reset the board

    # 2. Check for blocking opponent's winning move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    board[i][j][k] = opponent_player
                    if check_win(board, opponent_player):
                        board[i][j][k] = 0  # Reset the board
                        return (i, j, k)
                    board[i][j][k] = 0  # Reset the board

    # 3. Choose the center if available
    if board[n//2][n//2][n//2] == 0:
        return (n//2, n//2, n//2)

    # 4. Choose a random empty cell
    empty_cells = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))

    if empty_cells:
        return empty_cells[0]  # Just pick the first available

    # If no moves are available, return a dummy move (shouldn't happen)
    return (0, 0, 0)
