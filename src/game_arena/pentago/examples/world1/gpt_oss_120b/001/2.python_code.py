
#!/usr/bin/env python3
"""
A minimal Pentago move policy.

The policy always returns a legal move by:
1. Placing a marble on the first found empty cell (scanning rows then columns).
2. Rotating quadrant 0 clockwise (direction 'R').

The function signature matches the competition requirements.
"""

from typing import List, Sequence

def _first_empty(you: Sequence[Sequence[int]],
                 opponent: Sequence[Sequence[int]]) -> tuple[int, int]:
    """Return (row, col) of the first empty cell using 0‑based indices."""
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                return r, c
    # According to the problem statement this should never happen.
    raise ValueError("No empty cells available for a move.")


def policy(you: Sequence[Sequence[int]],
           opponent: Sequence[Sequence[int]]) -> str:
    """
    Return a legal Pentago move string: "row,col,quad,dir".

    Parameters
    ----------
    you : 6x6 array‑like of ints (0/1)
        Cells occupied by the current player.
    opponent : 6x6 array‑like of ints (0/1)
        Cells occupied by the opponent.

    Returns
    -------
    str
        A move in the required format, always legal.
    """
    r, c = _first_empty(you, opponent)

    # Choose a fixed quadrant and direction; they are always legal.
    quad = 0          # top‑left quadrant
    direction = 'R'   # clockwise

    # Convert to 1‑based row/col for the output format.
    return f"{r + 1},{c + 1},{quad},{direction}"
