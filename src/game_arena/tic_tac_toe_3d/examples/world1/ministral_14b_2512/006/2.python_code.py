
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Check all possible moves for a winning move (1)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    # Check if placing here wins
                    if check_win(board, i, j, k, 1):
                        return (i, j, k)

    # Check all possible moves for blocking opponent's winning move (-1)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    # Check if opponent can win next turn
                    if check_win(board, i, j, k, -1):
                        return (i, j, k)

    # Prioritize center if empty
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Prioritize corners (randomly if multiple are available)
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    available_corners = [c for c in corners if board[c[0]][c[1]][c[2]] == 0]
    if available_corners:
        return random.choice(available_corners)

    # Fallback: choose any empty cell (edges or random)
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    return random.choice(empty_cells)

def check_win(board: list[list[list[int]]], i: int, j: int, k: int, player: int) -> bool:
    # Create a copy of the board with the move
    temp_board = [row[:] for row in board]
    temp_board[i][j][k] = player

    # Check rows in each layer (fixed i)
    for j in range(3):
        for k in range(3):
            if all(temp_board[i][j][k] == player for k in range(3)):
                return True

    # Check columns in each layer (fixed i)
    for j in range(3):
        for k in range(3):
            if all(temp_board[i][j][k] == player for j in range(3)):
                return True

    # Check diagonals in each layer (fixed i)
    if (temp_board[i][0][0] == player and temp_board[i][1][1] == player and temp_board[i][2][2] == player) or \
       (temp_board[i][0][2] == player and temp_board[i][1][1] == player and temp_board[i][2][0] == player):
        return True

    # Check lines along the third dimension (fixed j and k)
    for i in range(3):
        if all(temp_board[i][j][k] == player for i in range(3)):
            return True

    # Check planes (fixed k)
    for k in range(3):
        # Check rows in the plane
        for i in range(3):
            if all(temp_board[i][j][k] == player for j in range(3)):
                return True
        # Check columns in the plane
        for j in range(3):
            if all(temp_board[i][j][k] == player for i in range(3)):
                return True
        # Check diagonals in the plane
        if (temp_board[0][0][k] == player and temp_board[1][1][k] == player and temp_board[2][2][k] == player) or \
           (temp_board[0][2][k] == player and temp_board[1][1][k] == player and temp_board[2][0][k] == player):
            return True

    # Check 3D diagonals
    if (temp_board[0][0][0] == player and temp_board[1][1][1] == player and temp_board[2][2][2] == player) or \
       (temp_board[0][2][2] == player and temp_board[1][1][1] == player and temp_board[2][0][0] == player):
        return True

    return False
