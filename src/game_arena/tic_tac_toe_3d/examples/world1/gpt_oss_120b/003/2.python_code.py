
#!/usr/bin/env python3
"""
policy.py

Provides a simple but effective policy for 3x3x3 Tic‑Tac‑Toe.

The function `policy(board)` receives a 3‑dimensional list:
    board[z][y][x]  where 0 = empty, 1 = us, -1 = opponent

It returns a tuple (z, y, x) with coordinates of the selected move.
"""

from __future__ import annotations
import random
from typing import List, Tuple

# ----------------------------------------------------------------------
# Pre‑compute all possible winning lines (there are 49 of them)
# ----------------------------------------------------------------------
def _generate_lines() -> List[List[Tuple[int, int, int]]]:
    lines: List[List[Tuple[int, int, int]]] = []

    # rows along x  (z, y fixed)
    for z in range(3):
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])

    # columns along y  (z, x fixed)
    for z in range(3):
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])

    # pillars along z  (x, y fixed)
    for y in range(3):
        for x in range(3):
            lines.append([(z, y, x) for z in range(3)])

    # face diagonals on xy‑planes (z fixed)
    for z in range(3):
        lines.append([(z, i, i) for i in range(3)])          # main diagonal
        lines.append([(z, i, 2 - i) for i in range(3)])      # anti‑diagonal

    # face diagonals on xz‑planes (y fixed)
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])
        lines.append([(i, y, 2 - i) for i in range(3)])

    # face diagonals on yz‑planes (x fixed)
    for x in range(3):
        lines.append([(i, i, x) for i in range(3)])
        lines.append([(i, 2 - i, x) for i in range(3)])

    # the four space diagonals
    lines.append([(i, i, i) for i in range(3)])                # (0,0,0) → (2,2,2)
    lines.append([(i, i, 2 - i) for i in range(3)])            # (0,0,2) → (2,2,0)
    lines.append([(i, 2 - i, i) for i in range(3)])            # (0,2,0) → (2,0,2)
    lines.append([(2 - i, i, i) for i in range(3)])            # (2,0,0) → (0,2,2)

    return lines


# Store the lines once so policy() can reuse them quickly.
_LINES = _generate_lines()


def _find_move(board: List[List[List[int]]], target: int, needed: int) -> None:
    """
    Search for a line that contains `needed` pieces of `target`
    (target = 1 for us, -1 for opponent) and exactly one empty cell.
    Return the coordinate of that empty cell, or None if not found.
    """
    for line in _LINES:
        values = [board[z][y][x] for (z, y, x) in line]
        if values.count(target) == needed and values.count(0) == 1:
            empty_index = values.index(0)
            return line[empty_index]
    return None


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Choose the next move for the player represented by `1` on a 3×3×3 board.

    Strategy (in order):
        1. Win if possible.
        2. Block opponent's immediate win.
        3. Take centre if free.
        4. Take any free corner.
        5. Pick a random empty cell.
    """

    # 1. Win if we have two in a line.
    win_move = _find_move(board, target=1, needed=2)
    if win_move is not None:
        return win_move

    # 2. Block opponent's winning line.
    block_move = _find_move(board, target=-1, needed=2)
    if block_move is not None:
        return block_move

    # 3. Take centre cell if empty.
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Prefer corners.
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for cz, cy, cx in corners:
        if board[cz][cy][cx] == 0:
            return (cz, cy, cx)

    # 5. Fallback: any empty cell (random choice for variability).
    empties = [(z, y, x)
               for z in range(3)
               for y in range(3)
               for x in range(3)
               if board[z][y][x] == 0]

    if empties:
        return random.choice(empties)

    # No empty cells – return a default (should never be used in a proper game).
    return (0, 0, 0)


# ----------------------------------------------------------------------
# When run as a script, demonstrate a simple usage example.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Example empty board
    empty_board = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    move = policy(empty_board)
    print("Chosen move:", move)
