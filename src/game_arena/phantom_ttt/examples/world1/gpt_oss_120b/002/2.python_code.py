
from typing import List

# ----- Helper structures ----------------------------------------------------
# All winning lines expressed as a list of 3 cell indices (0‑8)
_LINES = [
    [0, 1, 2],  # rows
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],  # columns
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],  # diagonals
    [2, 4, 6],
]

# Positional weights: center > corners > edges
_POSITION_WEIGHT = {
    4: 3,               # center
    0: 2, 2: 2, 6: 2, 8: 2,   # corners
    1: 1, 3: 1, 5: 1, 7: 1    # edges
}


def _index_to_rc(idx: int) -> (int, int):
    """Convert a flat index (0‑8) to (row, col)."""
    return idx // 3, idx % 3


def policy(board: List[List[int]], legal_moves: List[int]) -> int:
    """
    Choose the next cell to attempt to claim in Phantom Tic‑Tac‑Toe.

    Parameters
    ----------
    board : List[List[int]]
        3×3 board where 1 marks cells confirmed to belong to us.
    legal_moves : List[int]
        Flat indices (0‑8) that the engine currently allows.

    Returns
    -------
    int
        Flat index (0‑8) of the selected move.
    """
    # Flatten the board for easier indexing
    flat_board = [board[r][c] for r in range(3) for c in range(3)]

    # Pre‑compute for each cell the set of lines it belongs to
    cell_to_lines = {i: [] for i in range(9)}
    for line in _LINES:
        for cell in line:
            cell_to_lines[cell].append(line)

    best_move = None
    best_score = -1e9

    # Evaluate each legal move independently
    for move in legal_moves:
        # Skip cells we already own (should never be in legal_moves, but be safe)
        if flat_board[move] == 1:
            continue

        # Base positional score
        score = _POSITION_WEIGHT.get(move, 0)

        # Analyse all lines that contain this cell
        for line in cell_to_lines[move]:
            my_marks = sum(1 for c in line if flat_board[c] == 1)
            unknown = sum(1 for c in line if flat_board[c] == 0)

            # Immediate win possibility
            if my_marks == 2 and move in line:
                score += 100  # decisive
                continue  # no need to add other bonuses for this line

            # Building our own line
            if my_marks == 1:
                # Prefer completing a line we already own
                score += 10 + unknown

            # Potential opponent threat
            elif my_marks == 0:
                # The more unknown cells, the higher the chance opponent already has 2 in this line
                # Give a modest incentive to block
                score += unknown

        # Keep the highest‑scoring legal move
        if score > best_score or (score == best_score and (best_move is None or move < best_move)):
            best_score = score
            best_move = move

    # As a safety net, if something went wrong, just pick the first legal move
    if best_move is None:
        best_move = legal_moves[0]

    return best_move
