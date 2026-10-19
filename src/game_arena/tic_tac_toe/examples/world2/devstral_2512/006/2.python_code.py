
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for immediate blocking move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Try to create a fork (two ways to win)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if count_potential_wins(board, 1) >= 2:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Try to block opponent's fork
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if count_potential_wins(board, -1) >= 2:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Prefer center positions
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for pos in center_positions:
        i, j = pos
        if board[i][j] == 0:
            return (i, j)

    # Prefer corner positions
    corner_positions = [(0,0), (0,3), (3,0), (3,3)]
    for pos in corner_positions:
        i, j = pos
        if board[i][j] == 0:
            return (i, j)

    # If no strategic move found, choose random available position
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    return random.choice(empty_cells)

def check_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True

    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3-i] == player for i in range(4)):
        return True

    return False

def count_potential_wins(board, player):
    count = 0
    # Check rows
    for i in range(4):
        if sum(1 for j in range(4) if board[i][j] == player) == 3 and sum(1 for j in range(4) if board[i][j] == 0) == 1:
            count += 1

    # Check columns
    for j in range(4):
        if sum(1 for i in range(4) if board[i][j] == player) == 3 and sum(1 for i in range(4) if board[i][j] == 0) == 1:
            count += 1

    # Check diagonals
    if sum(1 for i in range(4) if board[i][i] == player) == 3 and sum(1 for i in range(4) if board[i][i] == 0) == 1:
        count += 1
    if sum(1 for i in range(4) if board[i][3-i] == player) == 3 and sum(1 for i in range(4) if board[i][3-i] == 0) == 1:
        count += 1

    return count
