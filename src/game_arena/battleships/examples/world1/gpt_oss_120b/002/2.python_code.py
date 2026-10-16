
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next firing coordinate on a 10x10 Battleship board.

    board: 10x10 matrix where
        0  = unknown (not fired yet)
       -1  = miss
        1  = hit
    Returns (row, col) of an unknown cell.
    """
    SIZE = 10
    SHIP_LENGTHS = [5, 4, 3, 3, 2]

    # Weight matrix for each cell
    weight = [[0 for _ in range(SIZE)] for _ in range(SIZE)]

    # Helper: check if a placement of given length and orientation is compatible
    def placement_ok(start_r: int, start_c: int, length: int, dr: int, dc: int) -> bool:
        """Return True if a ship of given length placed starting at (start_r,start_c)
        moving by (dr,dc) each step does not conflict with known misses."""
        for k in range(length):
            r = start_r + dr * k
            c = start_c + dc * k
            cell = board[r][c]
            if cell == -1:          # miss – cannot occupy this cell
                return False
        return True

    # Iterate over all ships, orientations and start positions
    for length in SHIP_LENGTHS:
        # Horizontal (dr=0, dc=1)
        for r in range(SIZE):
            for c in range(SIZE - length + 1):
                if placement_ok(r, c, length, 0, 1):
                    # Add weight to every unknown cell this ship would cover
                    for k in range(length):
                        rr = r
                        cc = c + k
                        if board[rr][cc] == 0:   # only count unknown cells
                            weight[rr][cc] += 1
        # Vertical (dr=1, dc=0)
        for r in range(SIZE - length + 1):
            for c in range(SIZE):
                if placement_ok(r, c, length, 1, 0):
                    for k in range(length):
                        rr = r + k
                        cc = c
                        if board[rr][cc] == 0:
                            weight[rr][cc] += 1

    # Find the unknown cell(s) with maximal weight
    max_weight = -1
    candidates = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:          # only consider cells we haven't fired at
                w = weight[r][c]
                if w > max_weight:
                    max_weight = w
                    candidates = [(r, c)]
                elif w == max_weight:
                    candidates.append((r, c))

    # If for some reason no candidates were found (shouldn't happen), pick any unknown cell
    if not candidates:
        unknown_cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
        return random.choice(unknown_cells)

    # Choose randomly among the best cells to avoid deterministic play
    return random.choice(candidates)
