
import numpy as np
from collections import defaultdict

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

def _inb(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def _queen_reach(board, start_r, start_c):
    """Return list of empty landing squares reachable by queen lines."""
    res = []
    for dr, dc in DIRS:
        r, c = start_r + dr, start_c + dc
        while _inb(r, c) and board[r, c] == 0:
            res.append((r, c))
            r += dr
            c += dc
    return res

def _line_clear(board, r1, c1, r2, c2):
    """Check if straight/diagonal path from (r1,c1) to (r2,c2) is unobstructed excluding destination,
    assuming destination is empty (or vacated context provided by caller)."""
    dr = r2 - r1
    dc = c2 - c1
    if dr == 0:
        step_r, step_c = 0, 1 if dc > 0 else -1
    elif dc == 0:
        step_r, step_c = 1 if dr > 0 else -1, 0
    elif abs(dr) == abs(dc):
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1
    else:
        return False

    r, c = r1 + step_r, c1 + step_c
    while (r, c) != (r2, c2):
        if board[r, c] != 0:
            return False
        r += step_r
        c += step_c
    return True

def _apply_move(board, fr, fc, tr, tc, ar, ac):
    """Return new board after moving amazon and shooting arrow."""
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = 1
    b[ar, ac] = -1
    return b

def _legal_moves(board, player_val=1):
    """Generate legal move tuples (fr,fc,tr,tc,ar,ac)."""
    opp_val = 2 if player_val == 1 else 1
    my_positions = np.argwhere(board == player_val)
    if my_positions.size == 0:
        return []

    moves = []
    for fr, fc in my_positions:
        # Possible landing squares
        for tr, tc in _queen_reach(board, fr, fc):
            # Temporarily vacate from for arrow-path legality
            # Treat landing square as occupied by amazon for arrow shot blocking rules only at endpoints.
            # For arrow shot, only the path and arrow destination must be empty in the original after the move.
            # Passing through vacated (fr,fc) is allowed since it becomes empty.
            # We'll use a board view for arrow legality: mark fr,fc empty, tr,tc occupied, then arrow must land on 0.
            temp = board  # we'll compute legality without building full temp board each arrow by careful checks
            # Arrow destination must be empty in original position AFTER move:
            # i.e., in original board, arrow square must be 0, and cannot be (tr,tc) or blocked squares.
            for ar, ac in _queen_reach(board if True else temp, tr, tc):
                # _queen_reach assumes tr,tc is empty; it's occupied in actual move.
                # So we can't use it directly. We'll instead enumerate arrow squares by scanning directions
                # with blocking treated as if tr,tc has player's amazon (still blocks beyond it),
                # but since start square is occupied by amazon, that does not prevent sliding outward.
                pass
            # We'll implement arrow generation properly:
            for dr, dc in DIRS:
                r, c = tr + dr, tc + dc
                while _inb(r, c):
                    # For arrow, destination must be empty AFTER move:
                    # - squares with 0 remain empty
                    # - the vacated from (fr,fc) becomes empty (it was 1 originally so not empty in board)
                    # - any other amazon/arrow squares block and cannot be arrow landing squares.
                    cell = board[r, c]
                    if (r, c) == (fr, fc):
                        # vacated square is empty now
                        pass
                    elif cell != 0:
                        break
                    # destination is along a clear path, so if it is empty after move, it's a valid arrow landing
                    # Note: r,c != tr,tc always since starting beyond.
                    moves.append((fr, fc, tr, tc, r, c))
                    r += dr
                    c += dc
                    continue
                # end while
            # The above appends arrows to every reachable square regardless of whether squares block after vacated logic.
            # We already break on non-empty unless it's the vacated square; and we allow passing through vacated square
            # because it is empty after move. Good.

            # However, we also need to ensure arrow destination is not landing on opponent or own amazon or arrow.
            # The logic above ensures destination cell must be 0 or (fr,fc). For (fr,fc) it's now empty.
            # Great.

    # But our arrow generator above may include arrows shooting through tr,tc start, which is fine, and along lines
    # it stops on the first blocked square. It also allows a ray to include the vacated square then continue
    # (because after it, the subsequent squares are checked). Our loop currently "continue" even after appending.
    # It will continue scanning beyond vacated square, but we must ensure the path is unobstructed:
    # vacated square is empty now; thus scanning beyond is allowed. That's what happens because we didn't break.
    # So correctness holds.
    # Now we must remove duplicates caused by earlier unused temp loops.
    # There should be none, but we'll keep it safe.
    # Additionally, we might have included arrows that land on squares which were non-empty but == -1 etc:
    # we break before appending in those cases, so ok.
    return moves

def _count_legal_from(board, player_val=1):
    """Count total legal moves for player, using legal move generator (fast enough on 6x6)."""
    return len(_legal_moves(board, player_val))

def _move_to_str(fr, fc, tr, tc, ar, ac):
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def policy(board) -> str:
    board = np.array(board, copy=False)
    my_val = 1
    opp_val = 2

    moves = _legal_moves(board, my_val)
    if not moves:
        # Robust fallback (shouldn't happen in arena).
        # Find any single legal-like move; otherwise return a dummy that is always legal is impossible.
        return "0,0:0,0:0,0"

    # Heuristic weights
    W_mobility = 1.0
    W_opp_mobility_reduction = 2.0
    W_immediate_block = 0.35  # small reward for reducing squares the opponent can target

    # Precompute current opponent mobility
    opp_mob_before = _count_legal_from(board, opp_val)

    best_score = -1e18
    best_move = moves[0]

    for fr, fc, tr, tc, ar, ac in moves:
        newb = _apply_move(board, fr, fc, tr, tc, ar, ac)
        my_mob = _count_legal_from(newb, my_val)
        opp_mob = _count_legal_from(newb, opp_val)

        # Basic mobility-difference
        score = W_mobility * my_mob + W_opp_mobility_reduction * (opp_mob_before - opp_mob)

        # Extra: slight preference for moves that reduce opponent's immediate ability
        # by counting how many arrow cells they can shoot next is expensive; use mobility only.

        # Safety: avoid moves that give opponent very high mobility (blunder)
        if opp_mob > opp_mob_before:
            score -= 0.75 * (opp_mob - opp_mob_before)

        # Terminal-ish: if opponent has no moves, win immediately; boost heavily.
        if opp_mob == 0:
            score = 1e15

        if score > best_score:
            best_score = score
            best_move = (fr, fc, tr, tc, ar, ac)

    fr, fc, tr, tc, ar, ac = best_move
    return _move_to_str(fr, fc, tr, tc, ar, ac)
