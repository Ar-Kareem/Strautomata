
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Directions for 3D Tic Tac Toe: rows, columns, pillars, and space diagonals
    directions = [
        # Rows (fixed i, j varies, k varies)
        [(0, j, k) for j in range(3) for k in range(3)],
        [(1, j, k) for j in range(3) for k in range(3)],
        [(2, j, k) for j in range(3) for k in range(3)],
        # Columns (fixed i, j fixed, k varies)
        [(i, 0, k) for i in range(3) for k in range(3)],
        [(i, 1, k) for i in range(3) for k in range(3)],
        [(i, 2, k) for i in range(3) for k in range(3)],
        # Pillars (fixed j, i varies, k varies)
        [(i, 0, k) for i in range(3) for k in range(3)],
        [(i, 1, k) for i in range(3) for k in range(3)],
        [(i, 2, k) for i in range(3) for k in range(3)],
        # Space diagonals (all three coordinates vary)
        [(i, i, i) for i in range(3)],
        [(i, i, 2 - i) for i in range(3)],
        [(i, 2 - i, i) for i in range(3)],
        [(i, 2 - i, 2 - i) for i in range(3)],
        # Face diagonals (two coordinates vary, one fixed)
        [(i, j, j) for i in range(3) for j in range(3)],
        [(i, j, 2 - j) for i in range(3) for j in range(3)],
        [(i, i, k) for i in range(3) for k in range(3)],
        [(i, 2 - i, k) for i in range(3) for k in range(3)],
        [(j, i, k) for i in range(3) for j in range(3) for k in range(3) if i == j or i == 2 - j],
    ]

    # Flatten the board for easier checking
    def is_win(player: int, move: tuple[int, int, int]) -> bool:
        i, j, k = move
        # Check row (fixed i, j varies, k varies)
        if all(board[i][j][k] == player for k in range(3)):
            return True
        if all(board[i][k][j] == player for k in range(3)):
            return True
        # Check column (fixed i, j fixed, k varies)
        if all(board[i][j][k] == player for k in range(3)):
            return True
        # Check pillar (fixed j, i varies, k varies)
        if all(board[i][j][k] == player for i in range(3)):
            return True
        # Check space diagonals
        if i == j == k:
            if all(board[i][i][i] == player for i in range(3)):
                return True
        if i == j and k == 2 - i:
            if all(board[i][i][2 - i] == player for i in range(3)):
                return True
        if i == k and j == 2 - i:
            if all(board[i][2 - i][i] == player for i in range(3)):
                return True
        if j == k and i == 2 - j:
            if all(board[2 - j][j][j] == player for j in range(3)):
                return True
        # Check face diagonals (e.g., fixed i, j varies, k = j)
        if k == j:
            if all(board[i][j][j] == player for j in range(3)):
                return True
        if k == 2 - j:
            if all(board[i][j][2 - j] == player for j in range(3)):
                return True
        # Check other face diagonals (e.g., fixed j, i varies, k = i)
        if k == i:
            if all(board[i][j][i] == player for i in range(3)):
                return True
        if k == 2 - i:
            if all(board[i][j][2 - i] == player for i in range(3)):
                return True
        return False

    # Check for winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1
                    if is_win(1, (i, j, k)):
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0

    # Block opponent's winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = -1
                    if is_win(-1, (i, j, k)):
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0

    # Prioritize center
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Prioritize corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board[corner[0]][corner[1]][corner[2]] == 0:
            return corner

    # Prioritize edges
    edges = [(0, 1, 0), (0, 1, 1), (0, 1, 2),
             (1, 0, 0), (1, 0, 1), (1, 0, 2),
             (1, 2, 0), (1, 2, 1), (1, 2, 2),
             (2, 1, 0), (2, 1, 1), (2, 1, 2),
             (0, 0, 1), (0, 2, 1), (2, 0, 1), (2, 2, 1),
             (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2)]
    for edge in edges:
        if board[edge[0]][edge[1]][edge[2]] == 0:
            return edge

    # Fallback: random empty cell
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    return random.choice(empty_cells)
