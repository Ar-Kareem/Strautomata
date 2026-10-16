
import numpy as np
import random

# 8 queen directions
DIRS = [(-1,-1), (-1,0), (-1,1),
        (0,-1),         (0,1),
        (1,-1),  (1,0), (1,1)]

def _in_bounds(r, c, n=6):
    return 0 <= r < n and 0 <= c < n

def _ray_squares(board, start_r, start_c, dr, dc):
    """Yield consecutive empty squares along (dr,dc) until blocked (including target squares)."""
    r, c = start_r + dr, start_c + dc
    n = board.shape[0]
    while _in_bounds(r, c, n):
        yield r, c
        if board[r, c] != 0:
            break
        r, c = r + dr, c + dc

def _clear_path(board, r1, c1, r2, c2):
    """Assumes r1,c1 != r2,c2 and is in queen line; returns True if all intermediate squares empty."""
    dr = r2 - r1
    dc = c2 - c1
    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
    r, c = r1 + step_r, c1 + step_c
    while (r, c) != (r2, c2):
        if board[r, c] != 0:
            return False
        r, c = r + step_r, c + step_c
    return True

def _queen_destinations(board, r, c):
    """All squares we can move to from (r,c) with queen rules, requiring destination empty."""
    n = board.shape[0]
    res = []
    if board[r, c] != 1:
        return res
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        while _in_bounds(rr, cc, n):
            if board[rr, cc] != 0:
                break
            res.append((rr, cc))
            rr += dr
            cc += dc
    return res

def _queen_arrows(board_after_move, r, c):
    """All arrow targets from (r,c) with queen rules, requiring destination empty."""
    n = board_after_move.shape[0]
    res = []
    if board_after_move[r, c] != 1:
        # In our simulated boards, amazon is still marked 1; but be robust:
        pass
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        while _in_bounds(rr, cc, n):
            if board_after_move[rr, cc] != 0:
                break
            res.append((rr, cc))
            rr += dr
            cc += dc
    return res

def _count_opponent_mobility(board):
    """Count all legal moves for opponent (board==2) including their arrows."""
    n = board.shape[0]
    opp_positions = np.argwhere(board == 2)
    if len(opp_positions) == 0:
        return 0

    total = 0
    # For each opponent amazon, enumerate move-to and arrow squares.
    for r, c in opp_positions:
        for tr, tc in _queen_destinations(board, r, c):
            # simulate move: place opponent at to
            b2 = board.copy()
            b2[r, c] = 0
            b2[tr, tc] = 2
            # arrow targets from (tr,tc)
            arrows = _queen_arrows(b2, tr, tc)
            total += len(arrows)
    return total

def _count_our_mobility(board):
    """Count all legal moves for us (board==1), including arrow shots."""
    n = board.shape[0]
    positions = np.argwhere(board == 1)
    total = 0
    for r, c in positions:
        for tr, tc in _queen_destinations(board, r, c):
            b2 = board.copy()
            b2[r, c] = 0
            b2[tr, tc] = 1
            total += len(_queen_arrows(b2, tr, tc))
    return total

def _generate_legal_moves(board):
    """Generate all legal moves as (from_r,from_c,to_r,to_c,arr_r,arr_c)."""
    positions = np.argwhere(board == 1)
    moves = []
    for fr, fc in positions:
        for tr, tc in _queen_destinations(board, fr, fc):
            # simulate amazon move
            b2 = board.copy()
            b2[fr, fc] = 0
            b2[tr, tc] = 1
            # arrow shot from landing square
            for ar, ac in _queen_arrows(b2, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def _center_score(r, c):
    # Higher near center (2.5,2.5) on 6x6
    return -((r - 2.5)**2 + (c - 2.5)**2)

def policy(board) -> str:
    board = np.asarray(board)
    n = board.shape[0]
    assert n == 6

    legal_moves = _generate_legal_moves(board)
    if not legal_moves:
        # Robust fallback: should not happen per environment guarantees.
        # Return a syntactically valid but likely illegal move; better to pick any queen step
        # from the first amazon if possible.
        pos = np.argwhere(board == 1)
        if len(pos) == 0:
            return "0,0:0,0:0,0"
        fr, fc = pos[0]
        dests = _queen_destinations(board, fr, fc)
        if not dests:
            return f"{fr},{fc}:{fr},{fc}:{fr},{fc}"
        tr, tc = dests[0]
        b2 = board.copy()
        b2[fr, fc] = 0
        b2[tr, tc] = 1
        arrows = _queen_arrows(b2, tr, tc)
        ar, ac = arrows[0] if arrows else (tr, tc)
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # Heuristic scoring
    our_mobility_before = _count_our_mobility(board)
    opp_mobility_before = _count_opponent_mobility(board)

    best = None
    best_score = -10**18

    # Precompute slight randomness for tie-breaking
    rng = random.Random(42 + int(np.sum(board)))

    for fr, fc, tr, tc, ar, ac in legal_moves:
        b2 = board.copy()
        b2[fr, fc] = 0
        b2[tr, tc] = 1
        b2[ar, ac] = -1

        our_mob = _count_our_mobility(b2)
        opp_mob = _count_opponent_mobility(b2)

        # Mobility differential
        score = 0.0
        score += 3.0 * (our_mob - our_mobility_before)
        score += -3.5 * (opp_mob - opp_mobility_before)

        # Encourage arrow placement that blocks lines: central / higher value for corner penalty less.
        score += 0.6 * _center_score(ar, ac)

        # Encourage landing near center too (but less than arrow)
        score += 0.2 * _center_score(tr, tc)

        # If move significantly reduces opponent mobility, boost
        if opp_mob < opp_mobility_before:
            score += 1.0 * (opp_mobility_before - opp_mob)

        # If move gives immediate advantage in total mobility, boost
        if our_mob > our_mobility_before:
            score += 0.5 * (our_mob - our_mobility_before)

        # Tie-break noise (tiny)
        score += rng.uniform(-0.05, 0.05)

        if score > best_score:
            best_score = score
            best = (fr, fc, tr, tc, ar, ac)

    fr, fc, tr, tc, ar, ac = best
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
