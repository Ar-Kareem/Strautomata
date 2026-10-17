
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Check row
                row = board[i]
                if sum(1 for x in row if x == 1) == 3 and row[j] == 0:
                    return (i, j)
                # Check column
                col = [board[x][j] for x in range(4)]
                if sum(1 for x in col if x == 1) == 3 and col[i] == 0:
                    return (i, j)
                # Check diagonals if on diagonal
                if i == j:
                    diag = [board[x][x] for x in range(4)]
                    if sum(1 for x in diag if x == 1) == 3 and diag[i] == 0:
                        return (i, j)
                if i + j == 3:
                    anti_diag = [board[x][3-x] for x in range(4)]
                    if sum(1 for x in anti_diag if x == 1) == 3 and anti_diag[i] == 0:
                        return (i, j)

    # Check for opponent's immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Check row
                row = board[i]
                if sum(1 for x in row if x == -1) == 3 and row[j] == 0:
                    return (i, j)
                # Check column
                col = [board[x][j] for x in range(4)]
                if sum(1 for x in col if x == -1) == 3 and col[i] == 0:
                    return (i, j)
                # Check diagonals if on diagonal
                if i == j:
                    diag = [board[x][x] for x in range(4)]
                    if sum(1 for x in diag if x == -1) == 3 and diag[i] == 0:
                        return (i, j)
                if i + j == 3:
                    anti_diag = [board[x][3-x] for x in range(4)]
                    if sum(1 for x in anti_diag if x == -1) == 3 and anti_diag[i] == 0:
                        return (i, j)

    # Prioritize center squares
    center_squares = [(1,1), (1,2), (2,1), (2,2)]
    random.shuffle(center_squares)
    for i, j in center_squares:
        if board[i][j] == 0:
            return (i, j)

    # Then prioritize corners
    corners = [(0,0), (0,3), (3,0), (3,3)]
    random.shuffle(corners)
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Finally, make any valid move
    valid_moves = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    return random.choice(valid_moves)
