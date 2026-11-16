
import itertools
from typing import List, Sequence

def policy(you: Sequence[Sequence[int]], opponent: Sequence[Sequence[int]]) -> str:
    """
    Return a legal Pentago move string.

    The move is constructed by selecting the first empty cell (row‑major order)
    and rotating quadrant 0 clockwise.

    Parameters
    ----------
    you : 6×6 array‑like of ints (0/1)
        Your stones.
    opponent : 6×6 array‑like of ints (0/1)
        Opponent's stones.

    Returns
    -------
    str
        Move formatted as "row,col,quad,dir" (1‑based row/col, quad 0‑3,
        dir = 'L' or 'R').
    """
    # Scan rows 0..5 and columns 0..5 for the first empty spot.
    for r, c in itertools.product(range(6), range(6)):
        if you[r][c] == 0 and opponent[r][c] == 0:
            # Convert to 1‑based coordinates for the output string.
            row_str = str(r + 1)
            col_str = str(c + 1)
            # Fixed rotation: quadrant 0, clockwise ('R').
            return f"{row_str},{col_str},0,R"
    # According to the problem statement this line should never be reached,
    # because the function is never called on a full board.
    raise RuntimeError("No empty cells found; cannot produce a legal move.")
