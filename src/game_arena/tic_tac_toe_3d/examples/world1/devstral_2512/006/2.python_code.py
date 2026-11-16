
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # All possible winning lines in 3D tic-tac-toe
    lines = [
        # Rows in each layer
        [(0, 0, 0), (0, 0, 1), (0, 0, 2)],
        [(0, 1, 0), (0, 1, 1), (0, 1, 2)],
        [(0, 2, 0), (0, 2, 1), (0, 2, 2)],
        [(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        [(1, 1, 0), (1, 1, 1), (1, 1, 2)],
        [(1, 2, 0), (1, 2, 1), (1, 2, 2)],
        [(2, 0, 0), (2, 0, 1), (2, 0, 2)],
        [(2, 1, 0), (2, 1, 1), (2, 1, 2)],
        [(2, 2, 0), (2, 2, 1), (2, 2, 2)],

        # Columns in each layer
        [(0, 0, 0), (0, 1, 0), (0, 2, 0)],
        [(0, 0, 1), (0, 1, 1), (0, 2, 1)],
        [(0, 0, 2), (0, 1, 2), (0, 2, 2)],
        [(1, 0, 0), (1, 1, 0), (1, 2, 0)],
        [(1, 0, 1), (1, 1, 1), (1, 2, 1)],
        [(1, 0, 2), (1, 1, 2), (1, 2, 2)],
        [(2, 0, 0), (2, 1, 0), (2, 2, 0)],
        [(2, 0, 1), (2, 1, 1), (2, 2, 1)],
        [(2, 0, 2), (2, 1, 2), (2, 2, 2)],

        # Pillars through layers
        [(0, 0, 0), (1, 0, 0), (2, 0, 0)],
        [(0, 0, 1), (1, 0, 1), (2, 0, 1)],
        [(0, 0, 2), (1, 0, 2), (2, 0, 2)],
        [(0, 1, 0), (1, 1, 0), (2, 1, 0)],
        [(0, 1, 1), (1, 1, 1), (2, 1, 1)],
        [(0, 1, 2), (1, 1, 2), (2, 1, 2)],
        [(0, 2, 0), (1, 2, 0), (2, 2, 0)],
        [(0, 2, 1), (1, 2, 1), (2, 2, 1)],
        [(0, 2, 2), (1, 2, 2), (2, 2, 2)],

        # Space diagonals
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
    ]

    # Check for winning move
    for line in lines:
        counts = [0, 0, 0]  # empty, me, opponent
        empty_pos = None
        for pos in line:
            i, j, k = pos
            val = board[i][j][k]
            if val == 0:
                counts[0] += 1
                empty_pos = pos
            elif val == 1:
                counts[1] += 1
            else:
                counts[2] += 1

        # If two of mine and one empty, take the empty
        if counts[1] == 2 and counts[0] == 1:
            return empty_pos

    # Check for blocking opponent's winning move
    for line in lines:
        counts = [0, 0, 0]  # empty, me, opponent
        empty_pos = None
        for pos in line:
            i, j, k = pos
            val = board[i][j][k]
            if val == 0:
                counts[0] += 1
                empty_pos = pos
            elif val == 1:
                counts[1] += 1
            else:
                counts[2] += 1

        # If two of opponent's and one empty, take the empty
        if counts[2] == 2 and counts[0] == 1:
            return empty_pos

    # Center control
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Corner control
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    random.shuffle(corners)
    for pos in corners:
        i, j, k = pos
        if board[i][j][k] == 0:
            return pos

    # Edge control
    edges = [
        (0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),
        (1, 0, 0), (1, 0, 2), (1, 1, 0), (1, 1, 2),
        (1, 2, 0), (1, 2, 2), (2, 0, 1), (2, 1, 0),
        (2, 1, 2), (2, 2, 1)
    ]
    random.shuffle(edges)
    for pos in edges:
        i, j, k = pos
        if board[i][j][k] == 0:
            return pos

    # Fallback: any available move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    # Should never reach here if board has empty cells
    return (0, 0, 0)
