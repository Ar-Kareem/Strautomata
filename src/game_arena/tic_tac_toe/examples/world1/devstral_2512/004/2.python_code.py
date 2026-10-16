
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for immediate blocking move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Take center if available
    if board[1][1] == 0:
        return (1, 1)

    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for (i, j) in corners:
        if board[i][j] == 0:
            return (i, j)

    # Take an edge if available
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(edges)
    for (i, j) in edges:
        if board[i][j] == 0:
            return (i, j)

    # Fallback to any available move (shouldn't reach here if board isn't full)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

    # If no moves available (shouldn't happen in valid game)
    return (0, 0)

def check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for i in range(3):
        if all(cell == player for cell in board[i]):
            return True

    # Check columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True

    return False
