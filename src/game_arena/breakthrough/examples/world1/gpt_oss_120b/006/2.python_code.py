
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Return the next move for Breakthrough.

    Parameters
    ----------
    me : list[tuple[int, int]]
        Positions of our pieces.
    opp : list[tuple[int, int]]
        Positions of opponent pieces.
    color : str
        'w' for white (moves to higher row numbers) or 'b' for black (moves to lower row numbers).

    Returns
    -------
    tuple[tuple[int, int], tuple[int, int]]
        ((from_row, from_col), (to_row, to_col))
    """

    # ----- board representation -------------------------------------------------
    board = [[None for _ in range(8)] for _ in range(8)]
    for r, c in me:
        board[r][c] = 'me'
    for r, c in opp:
        board[r][c] = 'opp'

    # ----- movement direction ---------------------------------------------------
    dir_forward = 1 if color == 'w' else -1          # white goes up, black goes down
    goal_row = 7 if color == 'w' else 0             # row we want to reach

    # ----- opponent attack squares (where they could capture next turn) ---------
    opp_dir = -dir_forward
    opp_attack_squares = set()
    for r, c in opp:
        for dc in (-1, 1):
            nr = r + opp_dir
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                opp_attack_squares.add((nr, nc))

    # ----- evaluation helper ----------------------------------------------------
    def evaluate(to_square: Tuple[int, int], capture: bool) -> float:
        """Return a numeric score for moving to `to_square`."""
        # distance to goal (the smaller, the better)
        distance = abs(goal_row - to_square[0])
        score = -distance * 1.0                     # progress reward

        # winning move
        if to_square[0] == goal_row:
            score += 1000.0                         # immediate win

        # capture bonus
        if capture:
            score += 5.0

        # safety penalty
        if to_square in opp_attack_squares:
            score -= 10.0

        return score

    # ----- generate all legal moves and evaluate them ---------------------------
    best_score = -float('inf')
    best_moves = []

    for r, c in me:
        # straight forward
        fr = r + dir_forward
        fc = c
        if 0 <= fr < 8 and board[fr][fc] is None:
            sc = evaluate((fr, fc), capture=False)
            if sc > best_score:
                best_score, best_moves = sc, [((r, c), (fr, fc))]
            elif sc == best_score:
                best_moves.append(((r, c), (fr, fc)))

        # diagonal moves (capture or normal)
        for dc in (-1, 1):
            tr = r + dir_forward
            tc = c + dc
            if 0 <= tr < 8 and 0 <= tc < 8:
                target = board[tr][tc]
                if target is None:                     # normal diagonal move
                    sc = evaluate((tr, tc), capture=False)
                    if sc > best_score:
                        best_score, best_moves = sc, [((r, c), (tr, tc))]
                    elif sc == best_score:
                        best_moves.append(((r, c), (tr, tc)))
                elif target == 'opp':                  # capture
                    sc = evaluate((tr, tc), capture=True)
                    if sc > best_score:
                        best_score, best_moves = sc, [((r, c), (tr, tc))]
                    elif sc == best_score:
                        best_moves.append(((r, c), (tr, tc)))

    # Fallback – should never happen, but keep code safe
    if not best_moves:
        # pick any legal forward move (there is always at least one)
        for r, c in me:
            fr = r + dir_forward
            if 0 <= fr < 8 and board[fr][c] is None:
                return ((r, c), (fr, c))
        # as a last resort, pick any diagonal capture
        for r, c in me:
            for dc in (-1, 1):
                tr = r + dir_forward
                tc = c + dc
                if 0 <= tr < 8 and 0 <= tc < 8 and board[tr][tc] == 'opp':
                    return ((r, c), (tr, tc))
        # If still nothing, raise (should not be reachable)
        raise RuntimeError("No legal moves found")

    # Randomly choose among equally good moves
    return random.choice(best_moves)
