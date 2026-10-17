
import random
from typing import List

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Select a legal Clobber move for the player to move.

    Parameters
    ----------
    you : List[List[int]]
        5x6 board where 1 indicates a piece belonging to the player.
    opponent : List[List[int]]
        5x6 board where 1 indicates a piece belonging to the opponent.

    Returns
    -------
    str
        A move in the format "row,col,dir" where dir is one of
        'U' (up), 'R' (right), 'D' (down), 'L' (left).
    """
    rows, cols = 5, 6
    # Directions: (label, dr, dc)
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]

    # Collect all possible captures – optional random choice for variety
    possible_moves = []

    for r in range(rows):
        for c in range(cols):
            if you[r][c] != 1:
                continue
            for d_label, dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and opponent[nr][nc] == 1:
                    possible_moves.append(f"{r},{c},{d_label}")

    if possible_moves:
        # Choose a random legal capture to avoid deterministic play
        return random.choice(possible_moves)

    # Fallback (should never be reached if the input guarantees a legal move)
    return "0,0,U"
