
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Check for winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    # Check if this move would win
                    board[i][j][k] = 1
                    if check_win(board, 1):
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0

    # Check for opponent winning move to block
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    # Check if opponent would win here
                    board[i][j][k] = -1
                    if check_win(board, -1):
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0

    # Try to take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Try to take corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    random.shuffle(corners)
    for corner in corners:
        i, j, k = corner
        if board[i][j][k] == 0:
            return corner

    # Make any legal move
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    return random.choice(empty_cells)

def check_win(board: list[list[list[int]]], player: int) -> bool:
    # Check all lines in 3D space
    # Check rows in each layer
    for i in range(3):
        for j in range(3):
            if all(board[i][j][k] == player for k in range(3)):
                return True

    # Check columns in each layer
    for i in range(3):
        for k in range(3):
            if all(board[i][j][k] == player for j in range(3)):
                return True

    # Check depth in each row-column
    for j in range(3):
        for k in range(3):
            if all(board[i][j][k] == player for i in range(3)):
                return True

    # Check diagonals in each layer
    for i in range(3):
        if board[i][0][0] == board[i][1][1] == board[i][2][2] == player:
            return True
        if board[i][0][2] == board[i][1][1] == board[i][2][0] == player:
            return True

    # Check vertical diagonals
    for j in range(3):
        if board[0][j][0] == board[1][j][1] == board[2][j][2] == player:
            return True
        if board[0][j][2] == board[1][j][1] == board[2][j][0] == player:
            return True

    # Check depth diagonals
    for k in range(3):
        if board[0][0][k] == board[1][1][k] == board[2][2][k] == player:
            return True
        if board[0][2][k] == board[1][1][k] == board[2][0][k] == player:
            return True

    # Check space diagonals
    if board[0][0][0] == board[1][1][1] == board[2][2][2] == player:
        return True
    if board[0][0][2] == board[1][1][1] == board[2][2][0] == player:
        return True
    if board[0][2][0] == board[1][1][1] == board[2][0][2] == player:
        return True
    if board[0][2][2] == board[1][1][1] == board[2][0][0] == player:
        return True

    return False
