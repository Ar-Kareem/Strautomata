
#!/usr/bin/env python3
"""
Simple Pentago move policy.

The function `policy(you, opponent)` returns a legal move string
"row,col,quad,dir" for the current player. It chooses the first
empty cell (row‑major order) and rotates quadrant 0 clockwise.
"""

from typing import List, Sequence

def policy(you: Sequence[Sequence[int]], opponent: Sequence[Sequence[int]]) -> str:
    """
    Return a legal Pentago move.

    Parameters
    ----------
    you : 6×6 array‑like of ints (0/1)
        Positions of the current player's marbles.
    opponent : 6×6 array‑like of ints (0/1)
        Positions of the opponent's marbles.

    Returns
    -------
    str
        A move string formatted as "row,col,quad,dir".
        Rows and columns are 1‑based.
    """
    # Scan the board row‑major for the first empty cell.
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                # Choose quadrant 0 (top‑left) and rotate clockwise (R).
                return f"{r+1},{c+1},0,R"

    # According to the problem statement this line should never be reached,
    # because a move is always possible when the function is called.
    # Return a fallback move to avoid runtime errors.
    return "1,1,0,R"


# If this file is executed directly, run a tiny sanity test.
if __name__ == "__main__":
    empty_board = [[0]*6 for _ in range(6)]
    print(policy(empty_board, empty_board))  # Expected: "1,1,0,R"
