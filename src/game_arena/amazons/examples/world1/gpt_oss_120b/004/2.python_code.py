
import numpy as np
import random

# 8 queen directions
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

def _in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def _reachable(board, start):
    """Yield all empty squares reachable from start using queen moves."""
    sr, sc = start
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while _in_bounds(r, c) and board[r, c] == 0:
            yield (r, c)
            r += dr
            c += dc

def _all_moves(board, player):
    """
    Generate all legal moves for `player` (1 for us, 2 for opponent).
    Returns a list of tuples:
        (from_r, from_c, to_r, to_c, arrow_r, arrow_c)
    """
    moves = []
    my_positions = np.argwhere(board == player)
    for fr, fc in my_positions:
        # possible destinations for the amazon
        for tr, tc in _reachable(board, (fr, fc)):
            # simulate moving the amazon
            temp = board.copy()
            temp[fr, fc] = 0
            temp[tr, tc] = player
            # now generate arrow shots from the new location
            for ar, ac in _reachable(temp, (tr, tc)):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def _mobility(board, player):
    """Return the total number of squares the player's amazons can move to."""
    count = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        count += sum(1 for _ in _reachable(board, (r, c)))
    return count

def policy(board) -> str:
    """
    Choose a move for the player whose amazons are marked with 1.
    Returns a string "fr,fc:tr,tc:ar,ac".
    """
    # generate every legal move for us
    possible_moves = _all_moves(board, 1)

    if not possible_moves:
        # No legal move – should not happen, but we return an empty string safely.
        return ""

    best_score = -10**9
    best_move = None

    for fr, fc, tr, tc, ar, ac in possible_moves:
        # simulate the whole turn (amazon move + arrow)
        new_board = board.copy()
        new_board[fr, fc] = 0          # vacate original square
        new_board[tr, tc] = 1          # place amazon on destination
        new_board[ar, ac] = -1         # place the arrow

        my_mob = _mobility(new_board, 1)
        opp_mob = _mobility(new_board, 2)
        score = my_mob - opp_mob

        if score > best_score:
            best_score = score
            best_move = (fr, fc, tr, tc, ar, ac)
            # early exit if we find a clearly dominating move
            # (optional, but keeps us fast)
            if best_score >= 0:
                # we cannot do better than a non‑negative advantage,
                # but still continue to ensure the absolute best is found.
                pass

    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
