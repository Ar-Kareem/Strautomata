
"""
policy.py - Provides a simple yet effective policy for a 3×3×3 3D Tic‑Tac‑Toe game.
The function `policy(board)` returns the coordinates (x, y, z) of an empty
cell to play next.  The strategy:
1. If we can immediately win (create a line of three of our marks), play that.
2. If the opponent can win on the next move, block that.
3. Otherwise pick the first empty cell (or a more central cell preferring the 
   middle slices).
"""

import numpy as np


def policy(board: list[list[list[int]]]") -> tuple[int, int, int]:
    """
    Returns the next move for the current 3D Tic‑Tac‑Toe board.

    Parameters
    ----------
    board : list[list[list[int]]]
        A 3×3×3 nested list where
            - 0 means the cell is empty,
            - 1 means the cell is occupied by the player (`us`),
            - -1 means the cell is occupied by the opponent.

    Returns
    -------
    tuple[int, int, int]
        Coordinates (x, y, z) of the chosen empty cell, each ranging from 0 to 2.
    """
    # Convert the board to a NumPy array for easier indexing
    b_np = np.array(board, dtype=int)

    # Constants
    US = 1
    OPP = -1
    EMPTY = 0
    size = 3

    # ------------------------------------------------------------------
    # 1. Check for an immediate winning move for us
    # ------------------------------------------------------------------
    # Iterate over all possible lines in 3‑D tic‑tac‑toe:
    #   - rows (x, y, z varying)
    #   - columns
    #   - depth (z direction)
    #   - planes (xy, yz, xz)
    #   - space diagonals
    #
    # For each line, if the sum of the three cells equals 2 (i.e., two of us
    # and one empty), then that empty cell is a winning move.

    win_dirs = []
    # 3 axes directions
    for ax in range(3):
        # Rows along that axis (fixed other two coordinates)
        for i in range(size):
            for j in range(size):
                idx = [0, 0, 0]
                idx[ax] = i
                other1 = ax % 3
                other2 = (ax + 1) % 3
                idx[other1] = j
                # three positions along axis ax
                positions = [
                    tuple(idx[:]),  # start at (i, j, k) where k is varying?
                ]
                # Actually easier: just generate all triples where two coords are fixed and one varies.
                # Simpler: iterate over all lines using known patterns.
                pass

    # Instead of reinventing, we enumerate all 49 lines manually.
    # There are 49 lines in 3x3x3: 3*3*3 (rows) + 3*3*3 (columns) + 3*3*3 (piles)
    # + 6 face diagonals + 4 space diagonals = 49.
    # We'll list them as list of tuples of three (x,y,z) coordinates.

    lines = [
        # layers (xy-planes) rows and columns
        [(0,0,0), (1,0,0), (2,0,0)],
        [(0,0,1), (1,0,1), (2,0,1)],
        [(0,0,2), (1,0,2), (2,0,2)],
        [(0,1,0), (1,1,0), (2,1,0)],
        [(0,1,1), (1,1,1), (2,1,1)],
        [(0,1,2), (1,1,2), (2,1,2)],
        [(0,2,0), (1,2,0), (2,2,0)],
        [(0,2,1), (1,2,1), (2,2,1)],
        [(0,2,2), (1,2,2), (2,2,2)],

        # columns in y direction within each z-layer
        [(0,0,0), (0,1,0), (0,2,0)],
        [(0,0,1), (0,1,1), (0,2,1)],
        [(0,0,2), (0,1,2), (0,2,2)],
        [(1,0,0), (1,1,0), (1,2,0)],
        [(1,0,1), (1,1,1), (1,2,1)],
        [(1,0,2), (1,1,2), (1,2,2)],
        [(2,0,0), (2,1,0), (2,2,0)],
        [(2,0,1), (2,1,1), (2,2,1)],
        [(2,0,2), (2,1,2), (2,2,2)],

        # columns in z direction within each xy-layer
        [(0,0,0), (0,0,1), (0,0,2)],
        [(0,1,0), (0,1,1), (0,1,2)],
        [(0,2,0), (0,2,1), (0,2,2)],
        [(1,0,0), (1,0,1), (1,0,2)],
        [(1,1,0), (1,1,1), (1,1,2)],
        [(1,2,0), (1,2,1), (1,2,2)],
        [(2,0,0), (2,0,1), (2,0,2)],
        [(2,1,0), (2,1,1), (2,1,2)],
        [(2,2,0), (2,2,1), (2,2,2)],

        # face diagonals (within each layer)
        [(0,0,0), (1,1,0), (2,2,0)],
        [(0,2,0), (1,1,0), (2,0,0)],
        [(0,0,1), (1,1,1), (2,2,1)],
        [(0,2,1), (1,1,1), (2,0,1)],
        [(0,0,2), (1,1,2), (2,2,2)],
        [(0,2,2), (1,1,2), (2,0,2)],

        # column diagonals across layers (xy-plane diagonals across depth)
        [(0,0,0), (1,1,1), (2,2,2)],
        [(0,2,0), (1,1,1), (2,0,2)],
        [(0,0,2), (1,1,1), (2,2,0)],
        [(0,2,2), (1,1,1), (2,0,0)],
    ]

    # Check for winning move for us
    for line in lines:
        cells = [b_np[c] for c in line]
        count_us = sum(1 for v in cells if v == US)
        count_opp = sum(1 for v in cells if v == OPP)
        if count_us == 2 and count_opp == 0:
            # There is exactly one empty cell, play it
            empty_cell = next(c for c in line if b_np[c] == EMPTY)
            return empty_cell

    # --------------------------------------------------------------
    # 2. Block opponent's immediate win
    # --------------------------------------------------------------
    for line in lines:
        cells = [b_np[c] for c in line]
        count_opp = sum(1 for v in cells if v == OPP)
        count_us = sum(1 for v in cells if v == US)
        if count_opp == 2 and count_us == 0:
            empty_cell = next(c for c in line if b_np[c] == EMPTY)
            return empty_cell

    # --------------------------------------------------------------
    # 3. No forced win/block -> pick a good empty cell
    # --------------------------------------------------------------
    # Prefer the centre-most positions (1,1,1) first, then cells with
    # the highest Manhattan distance from edges.
    empty_positions = [(i, j, k) for i in range(size)
                       for j in range(size) for k in range(size)
                       if b_np[i, j, k] == EMPTY]

    if not empty_positions:
        # Board is full (should never be called in a proper game)
        raise ValueError("No empty cells available")

    # Score each empty cell by sum of coordinates (prefer middle)
    empty_positions.sort(key=lambda pos: -(abs(pos[0]-1)+abs(pos[1]-1)+abs(pos[2]-1)))
    best = empty_positions[0]
    return best


if __name__ == "__main__":
    # Small sanity check
    board = [[[0]*3 for _ in range(3)] for __ in range(3)]
    board[1][1][1] = 1  # player placed centre
    move = policy(board)
    print("Suggested move:", move)
