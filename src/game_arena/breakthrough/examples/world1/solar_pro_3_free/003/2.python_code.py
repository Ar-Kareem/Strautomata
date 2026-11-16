
from typing import List, Tuple

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Choose the next move for Breakthrough.
    
    Parameters
    ----------
    me : list of (row, col) tuples
        Your pieces.
    opp : list of (row, col) tuples
        Opponent pieces.
    color : str
        'b' for black (moves downwards toward row 0) or 'w' for white (moves upwards toward row 7).

    Returns
    -------
    ((from_row, from_col), (to_row, to_col)) : tuple
        The selected move.
    """
    # Helper to compute distance of a piece to its own home row.
    def distance(r: int, c: int) -> int:
        if color == 'b':
            return r                     # home row is 0
        else:
            return 7 - r                 # home row is 7

    # Board directions
    dr = -1 if color == 'b' else +1          # our forward direction
    opp_dr = -dr                             # opponent's forward direction

    # Fast set of opponent positions for membership checks
    opp_set = set(opp)

    # -------------------------------------------------
    # Gather all legal candidate moves
    # -------------------------------------------------
    candidates: List[Tuple[Tuple[int, int],
                           Tuple[int, int],
                           int,  # is_capture (0/1)
                           Tuple[int, int] | None]] = []  # (from, to, capture, captured_piece)

    for fr, fc in me:
        # Straight forward move
        tr = fr + dr
        if 0 <= tr < 8 and (tr, fc) not in opp_set:
            candidates.append(((fr, fc), (tr, fc), 0, None))

        # Diagonal captures
        for dc in (-1, 1):
            tr = fr + dr
            tc = fc + dc
            if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) in opp_set:
                candidates.append(((fr, fc), (tr, tc), 1, (tr, tc)))

    # In a correct Breakthrough position there is always at least one move.
    if not candidates:
        # Should never happen – caller would have provided an illegal board state.
        raise RuntimeError("No legal moves available")

    # -------------------------------------------------
    # Score each move
    # -------------------------------------------------
    # Parameters for scoring
    BASE_SCORE_PER_DST = -1          # moving closer to home (negative distance)
    CAPTURE_BASE = 20                # basic credit for removing an opponent
    PROMOTION_BONUS = 1000           # huge boost for winning moves
    DANGER_PENALTY = -5000          # heavy penalty for exposing yourself to capture

    # Helper: does the opponent have a forward diagonal that lands on (tr, tc)?
    def will_be_captured(tr: int, tc: int) -> bool:
        for op_r, op_c in opp:
            if opp_dr == -1:   # opponent is white, moves upward
                diagonals = [(op_r - 1, op_c - 1), (op_r - 1, op_c + 1)]
            else:               # opponent is black, moves downward
                diagonals = [(op_r + 1, op_c - 1), (op_r + 1, op_c + 1)]
            if (tr, tc) in diagonals:
                return True
        return False

    best_move: Tuple[Tuple[int, int], Tuple[int, int]] = None
    best_score: int = -float('inf')

    for (fr, fc), (tr, tc), is_capture, captured_piece in candidates:
        # Distance after the move (how many forward squares left)
        new_dist = distance(tr, tc)

        # Base score: we like pieces that are nearer the home row.
        score = BASE_SCORE_PER_DST * new_dist  # negative distance → higher score

        # Capture bonus
        if is_capture:
            # Distance of the captured opponent piece to its own home row
            if color == 'b':      # capturing a white piece
                opp_dist_to_home = 7 - tr  # white's home is row 7
            else:                 # capturing a black piece
                opp_dist_to_home = tr     # black's home is row 0
            bonus = CAPTURE_BASE
            if opp_dist_to_home == 1:
                bonus += 100                 # extra credit for removing a piece one step from promotion
            score += bonus

            # Promotion win check
            if new_dist == 0:
                score += PROMOTION_BONUS

        # Danger penalty
        if will_be_captured(tr, tc) and new_dist != 0:
            score += DANGER_PENALTY

        # Tie‑breaker: capture moves beat straight moves if scores are equal
        if score > best_score or (score == best_score and is_capture):
            best_score = score
            best_move = ((fr, fc), (tr, tc))

    return best_move
