
import numpy as np
from typing import List, Tuple

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

# positional weights (corner > edge > interior)
POS_WEIGHT = np.ones((8, 8), dtype=int)
for r, c in [(0, 0), (0, 7), (7, 0), (7, 7)]:
    POS_WEIGHT[r, c] = 100
for i in range(1, 7):
    POS_WEIGHT[0, i] = POS_WEIGHT[7, i] = 10
    POS_WEIGHT[i, 0] = POS_WEIGHT[i, 7] = 10


def _legal_moves(you: np.ndarray, opp: np.ndarray) -> List[Tuple[int, int, List[Tuple[int, int]]]]:
    """Return a list of (row, col, flips) for every legal move."""
    empty = (you == 0) & (opp == 0)
    moves = []
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            total_flips = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                line = []
                while 0 <= rr < 8 and 0 <= cc < 8:
                    if opp[rr, cc]:
                        line.append((rr, cc))
                    elif you[rr, cc]:
                        if line:
                            total_flips.extend(line)
                        break
                    else:          # empty square – stop scanning this direction
                        break
                    rr += dr
                    cc += dc
            if total_flips:
                moves.append((r, c, total_flips))
    return moves


def _apply_move(you: np.ndarray, opp: np.ndarray,
                r: int, c: int, flips: List[Tuple[int, int]]) -> Tuple[np.ndarray, np.ndarray]:
    """Return new (you, opp) boards after playing (r,c) and flipping."""
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    for rr, cc in flips:
        new_you[rr, cc] = 1
        new_opp[rr, cc] = 0
    return new_you, new_opp


def _evaluate(you: np.ndarray, opp: np.ndarray, flip_cnt: int) -> int:
    """
    Simple static evaluation:
        weighted disc difference
        - 3 * opponent mobility
        + flips taken this turn
    """
    disc_score = int(np.sum(POS_WEIGHT * you) - np.sum(POS_WEIGHT * opp))
    # mobility of opponent after the move
    opp_moves = len(_legal_moves(opp, you))
    mobility_penalty = 3 * opp_moves
    return disc_score - mobility_penalty + flip_cnt


def _to_notation(r: int, c: int) -> str:
    """Convert (row, col) to Othello algebraic notation."""
    return f"{chr(ord('a') + c)}{r + 1}"


# ------------------------------------------------------------
# Main policy function
# ------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the best legal move according to the simple heuristic.
    If no move exists, return "pass".
    """
    moves = _legal_moves(you, opponent)

    if not moves:                     # no legal move -> pass
        return "pass"

    best_score = -10**9
    best_move = None

    for r, c, flips in moves:
        new_you, new_opp = _apply_move(you, opponent, r, c, flips)
        score = _evaluate(new_you, new_opp, len(flips))

        # tie‑break: prefer corners, then edges
        if score > best_score:
            best_score = score
            best_move = (r, c)
        elif score == best_score:
            # corner preference
            if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
                best_move = (r, c)
            elif best_move and best_move not in [(0, 0), (0, 7), (7, 0), (7, 7)]:
                # edge over interior
                if (r in (0, 7) or c in (0, 7)):
                    best_move = (r, c)

    r, c = best_move
    return _to_notation(r, c)
