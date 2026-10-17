
#!/usr/bin/env python3
"""
Phantom Tic Tac Toe policy.

Implements:
    def policy(board: list[list[int]], legal_moves: list[int]) -> (int, int)

Strategy:
- If a legal move would immediately complete a 3-in-a-row for us, play it.
- Otherwise score legal candidate cells by how many 2-in-a-row threats they create,
  plus positional preference (center > corners > edges). Avoid cells already marked '1'
  whenever possible.
- Return a tuple (row, col) for the chosen move.
"""

from typing import List, Tuple

# Precompute all winning lines as index triples (0-8)
_LINES = [
    (0, 1, 2),  # rows
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),  # cols
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),  # diagonals
    (2, 4, 6),
]

_CENTER = 4
_CORNERS = {0, 2, 6, 8}

def _idx_to_rc(idx: int) -> Tuple[int, int]:
    return divmod(idx, 3)

def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    """
    Choose a move for Phantom Tic Tac Toe.

    board: 3x3 list of ints, 1 means confirmed our mark, 0 means unknown (may be empty/opponent).
    legal_moves: list of integers 0-8 of allowed actions.

    Returns: (row, col) tuple with ints in 0..2
    """
    # Flatten board for easier indexing
    flat = [board[r][c] for r in range(3) for c in range(3)]

    # Helper: whether an index is already confirmed ours
    def is_our(idx: int) -> bool:
        return flat[idx] == 1

    # Filter legal moves to prefer those not already marked as ours
    # but if none available, we must pick something from legal_moves anyway
    nonconfirmed_moves = [m for m in legal_moves if 0 <= m <= 8 and not is_our(m)]
    candidates = nonconfirmed_moves if nonconfirmed_moves else [m for m in legal_moves if 0 <= m <= 8]

    # If somehow empty, pick (0,0) as fallback
    if not candidates:
        return (0, 0)

    # 1) Immediate win: if placing on a candidate completes any line of ours -> play it
    for m in candidates:
        won = False
        for a, b, c in _LINES:
            if m in (a, b, c):
                # count existing our marks in other two cells
                cnt = (1 if (a != m and is_our(a)) else 0) + (1 if (b != m and is_our(b)) else 0) + (1 if (c != m and is_our(c)) else 0)
                # If the other two are ours, placing on m completes 3-in-a-row
                if cnt == 2:
                    won = True
                    break
        if won:
            return _idx_to_rc(m)

    # 2) Heuristic scoring for candidates
    best_move = None
    best_score = None

    for m in candidates:
        score = 0.0

        # Positional bonus: center > corner > edge
        if m == _CENTER:
            score += 3.0
        elif m in _CORNERS:
            score += 2.0
        else:
            score += 1.0

        # Evaluate lines containing m
        two_in_row_creations = 0
        lines_involved = 0
        for a, b, c in _LINES:
            if m not in (a, b, c):
                continue
            lines_involved += 1
            # Count how many confirmed our marks in the other two cells
            other_idxs = [x for x in (a, b, c) if x != m]
            others_our = sum(1 for x in other_idxs if is_our(x))
            others_unknown = sum(1 for x in other_idxs if not is_our(x))
            # If placing here would make two of ours in that line -> threat creation
            if others_our == 1:
                two_in_row_creations += 1
            # If both other cells are not ours, small potential
            if others_our == 0 and others_unknown == 2:
                score += 0.3

        # Reward creating multiple two-in-a-row threats (forks)
        score += two_in_row_creations * 4.0

        # Slightly prefer moves that are part of more lines (center is 4, corners 3, edges 2)
        score += 0.2 * lines_involved

        # As a tie-breaker, use move index (deterministic)
        if best_score is None or score > best_score or (score == best_score and m < best_move):
            best_move = m
            best_score = score

    # Return chosen move as (row, col)
    return _idx_to_rc(best_move)
