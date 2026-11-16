
import random
from typing import List, Tuple, Set

Move = Tuple[Tuple[int, int], Tuple[int, int]]

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Move:
    """
    Return a legal move for Breakthrough.
    - `me`  : list of (row, col) for our pieces
    - `opp` : list of (row, col) for opponent pieces
    - `color`: 'b' (black, moves toward decreasing rows) or
               'w' (white, moves toward increasing rows)
    """
    # ------------------------------------------------------------------
    # Helper data
    # ------------------------------------------------------------------
    board_set: Set[Tuple[int, int]] = set(me) | set(opp)
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)

    # direction of movement: +1 for white (up), -1 for black (down)
    dir_step = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0  # row we want to reach

    # ------------------------------------------------------------------
    # Compute all squares the opponent could capture on its next turn.
    # This is used for a simple safety penalty.
    # ------------------------------------------------------------------
    opp_dir = -dir_step           # opponent moves opposite direction
    opp_capture_squares: Set[Tuple[int, int]] = set()
    for (r, c) in opp:
        for dc in (-1, 1):
            nr, nc = r + opp_dir, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) in me_set:
                opp_capture_squares.add((nr, nc))

    # ------------------------------------------------------------------
    # Generate all legal moves for us
    # ------------------------------------------------------------------
    legal_moves: List[Move] = []
    for (r, c) in me:
        # straight forward
        nf_r, nf_c = r + dir_step, c
        if 0 <= nf_r <= 7 and (nf_r, nf_c) not in board_set:
            legal_moves.append(((r, c), (nf_r, nf_c)))

        # diagonal forward (capture or simple move)
        for dc in (-1, 1):
            nd_r, nd_c = r + dir_step, c + dc
            if 0 <= nd_r <= 7 and 0 <= nd_c <= 7:
                if (nd_r, nd_c) in opp_set:
                    # capture
                    legal_moves.append(((r, c), (nd_r, nd_c)))
                elif (nd_r, nd_c) not in board_set:
                    # simple diagonal advance
                    legal_moves.append(((r, c), (nd_r, nd_c)))

    # ------------------------------------------------------------------
    # Score each move
    # ------------------------------------------------------------------
    best_score = -10**9
    best_move: Move = legal_moves[0]  # there is always at least one move

    for move in legal_moves:
        (fr, fc), (tr, tc) = move
        score = 0

        # 1) Immediate win?
        if tr == goal_row:
            # winning move – make it overwhelmingly attractive
            best_move = move
            best_score = 10**9
            break

        # 2) Capture reward
        if (tr, tc) in opp_set:
            score += 120          # capture value

        # 3) Advancement reward (how much closer to goal)
        if color == 'w':
            old_dist = 7 - fr
            new_dist = 7 - tr
        else:
            old_dist = fr
            new_dist = tr
        advance = old_dist - new_dist   # positive if we move forward
        score += advance * 15

        # 4) Safety penalty
        # after a capture the square is empty for the opponent,
        # but they could still capture the moved piece with another piece.
        if (tr, tc) in opp_capture_squares:
            score -= 80

        # Keep best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
