
import copy
from itertools import product

# Pre‑computed list of all winning lines (49 of them)
WIN_LINES = []

# 1‑D lines (rows, columns, pillars)
for axis in range(3):
    # X‑axis lines (vary i, keep j,k fixed)
    for j in range(3):
        for k in range(3):
            WIN_LINES.append([(axis, j, k), (axis + 1, j, k), (axis + 2, j, k)])
    # Y‑axis lines (vary j, keep i,k fixed)
    for i in range(3):
        for k in range(3):
            WIN_LINES.append([(i, axis, k), (i, axis + 1, k), (i, axis + 2, k)])
    # Z‑axis lines (vary k, keep i,j fixed)
    for i in range(3):
        for j in range(3):
            WIN_LINES.append([(i, j, axis), (i, j, axis + 1), (i, j, axis + 2)])

# 2‑D plane diagonals (XY, XZ, YZ)
# XY‑plane diagonals (fixed Z)
for z in range(3):
    WIN_LINES.append([(0, 0, z), (1, 1, z), (2, 2, z)])          # main diagonal
    WIN_LINES.append([(0, 2, z), (1, 1, z), (2, 0, z)])          # anti diagonal
# XZ‑plane diagonals (fixed Y)
for y in range(3):
    WIN_LINES.append([(0, y, y), (1, y, y), (2, y, y)])          # main diagonal
    WIN_LINES.append([(0, y, 2), (1, y, 1), (2, y, 0)])          # anti diagonal
# YZ‑plane diagonals (fixed X)
for x in range(3):
    WIN_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])          # main diagonal
    WIN_LINES.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])          # anti diagonal

# 3‑D space diagonals
WIN_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
WIN_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
WIN_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
WIN_LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

def policy(board):
    """
    Choose the next move for a 3×3×3 Tic‑Tac‑Toe board.
    board[i][j][k] = 0 empty, 1 our mark, -1 opponent's mark.
    Returns a tuple (i,j,k) of an empty cell.
    """
    # Gather empty cells
    empty_cells = [(i, j, k) for i, j, k in product(range(3), repeat=3)
                  if board[i][j][k] == 0]
    if not empty_cells:
        # No legal move (should not happen in a valid game)
        return (0, 0, 0)

    # 1️⃣ Immediate win for us
    for i, j, k in empty_cells:
        # simulate the move
        sim_board = copy.deepcopy(board)
        sim_board[i][j][k] = 1
        if any(sum(sim_board[x][y][z] for x, y, z in line) == 2 for line in WIN_LINES):
            return (i, j, k)

    # 2️⃣ Block opponent's immediate win
    for line in WIN_LINES:
        values = [board[x][y][z] for x, y, z in line]
        if sum(values) == -2:          # two opponent marks, one empty
            # find the empty coordinate in this line
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)

    # 3️⃣ Fork creation (two or more winning lines after the move)
    for move in empty_cells:
        sim_board = copy.deepcopy(board)
        sim_board[move[0]][move[1]][move[2]] = 1
        win_cnt = sum(1 for line in WIN_LINES
                      if sum(sim_board[x][y][z] for x, y, z in line) == 2)
        if win_cnt >= 2:
            return move

    # 4️⃣ Prefer the centre (2,2,2)
    if (2, 2, 2) in empty_cells:
        return (2, 2, 2)

    # 5️⃣ Prefer corners (all cells where each coordinate is 0 or 2)
    corner_order = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
                    (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corner_order:
        if corner in empty_cells:
            return corner

    # 6️⃣ Fallback: any empty cell
    return empty_cells[0]
