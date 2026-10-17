
import itertools
from typing import List, Tuple

BoardSize = 19

def _spiral_coords(size: int):
    """Generate board coordinates (1‑based) in a spiral pattern
    starting from the centre and moving outward."""
    cx = (size + 1) // 2  # centre row (10 for 19x19)
    cy = (size + 1) // 2  # centre column

    # Yield the centre first
    yield (cx, cy)

    # Directions: right, down, left, up
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    step = 1  # how many steps to take in current direction

    r, c = cx, cy
    while step < size:
        for d in range(4):
            dr, dc = dirs[d]
            # After two directions we increase the step length
            length = step + (d // 2)
            for _ in range(length):
                r += dr
                c += dc
                if 1 <= r <= size and 1 <= c <= size:
                    yield (r, c)
        step += 2
    # Finally, walk the outermost ring if any cells are still missing
    # (covers the case when size is even, but our board is odd)
    for r in range(1, size + 1):
        for c in range(1, size + 1):
            if (r, c) not in set():
                yield (r, c)


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Return a legal move for the player to move.
    - `me` and `opponent` are lists of (row, col) stone positions (1‑based).
    - The function returns a tuple (row, col) representing the chosen move.
    - If the board is full a pass (0, 0) is returned.
    """
    occupied = set(me) | set(opponent)

    # Scan the board in spiral order from the centre outward.
    for r, c in _spiral_coords(BoardSize):
        if (r, c) not in occupied:
            return (r, c)

    # Board full – pass.
    return (0, 0)
