
import random
from typing import List

# Winning line definitions – each line is a tuple of the three cell indices.
WIN_LINES = [
    (0, 1, 2),  # rows
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),  # columns
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),  # diagonals
    (2, 4, 6),
]

def _cell(board: List[List[int]], idx: int) -> int:
    """Return the board value at linear index idx."""
    r, c = divmod(idx, 3)
    return board[r][c]

def policy(board: List[List[int]], legal_moves: List[int]) -> int:
    """
    Choose the next move for Phantom Tic‑Tac‑Toe.

    Parameters
    ----------
    board : 3×3 list of ints
        1 = confirmed own mark, 0 = unknown (empty or opponent).
    legal_moves : list[int]
        Indices (0‑8) that the engine currently allows.

    Returns
    -------
    int
        The chosen cell index (0‑8).  Always a legal move and never a
        cell already confirmed as ours.
    """
    # Remove moves that are already our confirmed marks (should not be legal,
    # but guard against malformed input).
    legal = [m for m in legal_moves if _cell(board, m) != 1]
    if not legal:
        # Fallback – pick any legal move to stay compliant.
        return random.choice(legal_moves)

    best_score = -1
    best_move = legal[0]

    for move in legal:
        score = 0
        for line in WIN_LINES:
            if move not in line:
                continue

            # Count our confirmed marks in the line (excluding the candidate cell).
            our_marks = sum(1 for idx in line if idx != move and _cell(board, idx) == 1)

            # Count unknown cells (could be empty or opponent) excluding the candidate.
            unknown = sum(1 for idx in line if idx != move and _cell(board, idx) == 0)

            # Immediate winning opportunity.
            if our_marks == 2:
                score += 1000
                # No need to evaluate further lines – this is already a win.
                continue

            # Strengthen our own line.
            if our_marks == 1:
                score += 10
            else:
                score += 1  # just a possible line

            # Potential opponent threat: line currently has no our marks and
            # already two unknown cells (the opponent could be about to win).
            if our_marks == 0 and unknown == 2:
                score += 5  # modest block incentive

        # Tie‑breaker: prefer lower index (deterministic) but add tiny random jitter
        # to avoid predictable behavior when scores are exactly equal.
        jitter = random.random() * 1e-6
        total = score + jitter
        if total > best_score:
            best_score = total
            best_move = move

    return best_move
