
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Flatten the board for easier processing
    flat_board = [cell for row in board for cell in row]

    # Directions for checking lines (rows, columns, diagonals)
    directions = [
        [(0, 1), (0, 2)],  # row
        [(1, 0), (2, 0)],  # column
        [(1, 1), (2, 2)],  # diagonal
        [(1, -1), (2, -2)] # anti-diagonal
    ]

    # Check all possible lines for winning or blocking moves
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:  # Only consider empty or uncertain cells
                # Check all lines passing through (i,j)
                for di, dj in directions:
                    # Check if (i,j) is part of a potential winning line
                    line = []
                    for k in range(3):
                        ni, nj = i + k * di[0], j + k * di[1]
                        if 0 <= ni < 3 and 0 <= nj < 3:
                            line.append((ni, nj))

                    # Count confirmed 1s in the line
                    confirmed_ones = sum(1 for (ni, nj) in line if board[ni][nj] == 1)

                    # If we have 2 confirmed 1s, placing here would win
                    if confirmed_ones == 2 and (i,j) in line:
                        return (i, j)

    # Check for opponent's potential winning moves (assuming they have 2 in a row)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                for di, dj in directions:
                    line = []
                    for k in range(3):
                        ni, nj = i + k * di[0], j + k * di[1]
                        if 0 <= ni < 3 and 0 <= nj < 3:
                            line.append((ni, nj))

                    # Count confirmed 1s in the line
                    confirmed_ones = sum(1 for (ni, nj) in line if board[ni][nj] == 1)

                    # If opponent could win next turn (assuming they have 2 in a row)
                    if confirmed_ones == 2 and (i,j) in line:
                        return (i, j)

    # Prefer center if available
    if board[1][1] == 0:
        return (1, 1)

    # Prefer corners
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for corner in corners:
        if board[corner[0]][corner[1]] == 0:
            return corner

    # Prefer edges
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for edge in edges:
        if board[edge[0]][edge[1]] == 0:
            return edge

    # Fallback: choose any available cell randomly
    available = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    return random.choice(available)
