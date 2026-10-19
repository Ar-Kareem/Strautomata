
import numpy as np
import random
import time

# Directions for queen-like movement: 8 directions
_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
               (-1, -1), (-1, 1), (1, -1), (1, 1)]

def _in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def _iter_move_targets(board, r, c):
    """Yield all empty target squares (row,col) reachable by queen move from (r,c)."""
    for dr, dc in _DIRECTIONS:
        nr, nc = r + dr, c + dc
        while _in_bounds(nr, nc) and board[nr, nc] == 0:
            yield (nr, nc)
            nr += dr
            nc += dc

def _iter_arrow_targets(board, from_r, from_c, to_r, to_c):
    """Given a board where 'from' is still occupied by original amazon,
    treat moving amazon from (from_r,from_c) to (to_r,to_c) by clearing from and occupying to,
    then yield arrow target squares reachable from to."""
    # We expect the caller to simulate move before calling this; but to keep API clear,
    # this function will assume the board passed is already with move applied.
    for dr, dc in _DIRECTIONS:
        nr, nc = to_r + dr, to_c + dc
        while _in_bounds(nr, nc) and board[nr, nc] == 0:
            yield (nr, nc)
            nr += dr
            nc += dc

def _get_amazons(board, player):
    return [(r, c) for r in range(6) for c in range(6) if board[r, c] == player]

def _count_move_arrow_sequences(board, player, cap=10000):
    """Count number of legal complete sequences (move then arrow) for player on board.
    Stop counting early if cap is reached (to save time)."""
    cnt = 0
    amazons = _get_amazons(board, player)
    for (r, c) in amazons:
        # for each possible move target
        for to_r, to_c in _iter_move_targets(board, r, c):
            # simulate move: clear from, occupy to
            board[r, c] = 0
            board[to_r, to_c] = player
            # count arrow targets
            for _ in _iter_arrow_targets(board, r, to_r, to_c):
                cnt += 1
                if cnt >= cap:
                    # restore and return early
                    board[r, c] = player
                    board[to_r, to_c] = 0
                    return cnt
            # restore board
            board[r, c] = player
            board[to_r, to_c] = 0
    return cnt

def _first_legal_move(board):
    """Return any legal move string found (used as fallback)."""
    my_ams = _get_amazons(board, 1)
    for (r, c) in my_ams:
        for to_r, to_c in _iter_move_targets(board, r, c):
            # simulate
            board[r, c] = 0
            board[to_r, to_c] = 1
            for ar, ac in _iter_arrow_targets(board, r, to_r, to_c):
                # restore before return
                board[r, c] = 1
                board[to_r, to_c] = 0
                return f"{r},{c}:{to_r},{to_c}:{ar},{ac}"
            board[r, c] = 1
            board[to_r, to_c] = 0
    # if no move found (should not be called in terminal), return a dummy valid-ish string if possible
    # Try to find any move where we at least move without arrow (rare); else return "0,0:0,0:0,0" though illegal.
    return "0,0:0,0:0,0"

def policy(board) -> str:
    """
    Choose a move string "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    Strategy: For each amazon and each reachable landing square, pick the arrow that
    minimizes opponent mobility (and maximizes our mobility) after the full move.
    """
    # Work on a copy to safely mutate when simulating
    board = board.copy()
    my_ams = _get_amazons(board, 1)
    if not my_ams:
        return _first_legal_move(board)  # fallback

    best_moves = []
    best_value = -10**9

    # To avoid pathological slowness, set caps for counting
    COUNT_CAP = 4000  # cap for counting move+arrow sequences
    # iterate over each amazon and possible landing squares
    for (r, c) in my_ams:
        for to_r, to_c in _iter_move_targets(board, r, c):
            # simulate move: clear from, occupy to
            board[r, c] = 0
            board[to_r, to_c] = 1

            # For this move-to, try all arrow shots and pick best arrow (local greedy)
            best_arrow_for_to = None
            best_value_for_to = -10**9

            # If there are no arrow targets, skip (shouldn't happen because at least something)
            found_arrow = False
            for ar, ac in _iter_arrow_targets(board, r, to_r, to_c):
                found_arrow = True
                # place arrow
                board[ar, ac] = -1

                # evaluate: count our and opponent move+arrow sequences
                # Give opponent counts a bit more weight (we want to minimize opponent)
                opp_count = _count_move_arrow_sequences(board, 2, cap=COUNT_CAP)
                my_count = _count_move_arrow_sequences(board, 1, cap=COUNT_CAP)

                val = my_count - opp_count  # heuristic: higher is better

                # undo arrow
                board[ar, ac] = 0

                if val > best_value_for_to:
                    best_value_for_to = val
                    best_arrow_for_to = (ar, ac)

            # restore move simulation
            board[r, c] = 1
            board[to_r, to_c] = 0

            if not found_arrow:
                # No arrow possible from this to (dead end) => treat as very bad
                continue

            # Record this candidate full move (from,to,best_arrow)
            if best_arrow_for_to is not None:
                # Compare to global best
                if best_value_for_to > best_value:
                    best_value = best_value_for_to
                    best_moves = [(r, c, to_r, to_c, best_arrow_for_to[0], best_arrow_for_to[1])]
                elif best_value_for_to == best_value:
                    best_moves.append((r, c, to_r, to_c, best_arrow_for_to[0], best_arrow_for_to[1]))

    if not best_moves:
        # No candidate moves found (shouldn't happen in normal scenarios) => fallback
        return _first_legal_move(board)

    # Random tie-break among best moves
    chosen = random.choice(best_moves)
    fr, fc, tr, tc, ar, ac = chosen
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
