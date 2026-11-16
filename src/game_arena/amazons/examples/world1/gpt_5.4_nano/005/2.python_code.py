
import numpy as np
import random

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

def _inb(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def _queen_ray_free(board, start, step, target):
    """Check whether all squares from start+step up to target are empty in the given board."""
    r, c = start
    tr, tc = target
    dr, dc = step
    r += dr
    c += dc
    while (r, c) != (tr, tc):
        if not _inb(r, c):
            return False
        if board[r, c] != 0:
            return False
        r += dr
        c += dc
    # landing square must be empty
    return board[tr, tc] == 0

def _lines_from(board, pos, empty_mask=None):
    """Yield reachable empty squares from pos (queen moves) on current board."""
    r0, c0 = pos
    for dr, dc in DIRS:
        r, c = r0 + dr, c0 + dc
        while _inb(r, c) and board[r, c] == 0:
            yield (r, c)
            r += dr
            c += dc

def _arrow_targets(board_after_move, from_pos, to_pos, amazon_val_to_place=1):
    """
    From landing square to_pos, shoot arrow to any reachable empty cell on board_after_move.
    board_after_move must already reflect: from vacated, amazon placed at to, other pieces unchanged.
    """
    return list(_lines_from(board_after_move, to_pos))

def _apply_move(board, frm, to, arr):
    """Return new board after applying a legal move."""
    nb = board.copy()
    nb[frm] = 0
    nb[to] = 1  # our amazon
    nb[arr] = -1
    return nb

def _legal_moves(board):
    moves = []
    my_positions = np.argwhere(board == 1)
    for frm in my_positions:
        fr, fc = int(frm[0]), int(frm[1])
        # possible destinations for amazon move
        for to in _lines_from(board, (fr, fc)):
            tr, tc = to
            # create board with amazon moved (without arrow yet)
            nb = board.copy()
            nb[fr, fc] = 0
            nb[tr, tc] = 1
            # possible arrow shots from landing square
            for arr in _lines_from(nb, (tr, tc)):
                ar, ac = arr
                # arrow square must be empty already guaranteed by _lines_from
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def _count_reachable(board, pos):
    return sum(1 for _ in _lines_from(board, pos))

def _opponent_positions(board):
    return np.argwhere(board == 2)

def _best_move(board):
    legal = _legal_moves(board)
    if not legal:
        # Shouldn't happen if environment checks legality before calling,
        # but return a syntactically valid "impossible" move as fallback.
        return "0,0:0,0:0,0"

    best = None
    best_score = -10**18

    # Heuristic weights (tuned for general strength)
    W_mobility = 3.0
    W_center = 0.4
    W_elim = 1.5
    W_arrow_far = 0.15
    W_trap_penalty = 2.0
    W_opp_mobility = -2.8

    my_positions = np.argwhere(board == 1)
    opp_positions = np.argwhere(board == 2)

    # precompute current counts for opponent mobility
    cur_opp_mob = 0
    for p in opp_positions:
        cur_opp_mob += _count_reachable(board, (int(p[0]), int(p[1])))

    # deterministic tiny noise to break ties among equal scores
    rng = random.Random(42)

    for (fr, fc, tr, tc, ar, ac) in legal:
        nb = _apply_move(board, (fr, fc), (tr, tc), (ar, ac))

        # mobility after move for all our amazons
        my_mob = 0
        for p in np.argwhere(nb == 1):
            my_mob += _count_reachable(nb, (int(p[0]), int(p[1])))

        # opponent mobility after move
        opp_mob = 0
        for p in np.argwhere(nb == 2):
            opp_mob += _count_reachable(nb, (int(p[0]), int(p[1])))

        # center preference
        # (closer to center (2.5,2.5) on 6x6 is better)
        center_dist = abs(tr - 2.5) + abs(tc - 2.5)

        # elimination / blocking: arrow placement that reduces opponent mobility
        # Approximate via delta in opponent mobility.
        opp_mob_delta = opp_mob - cur_opp_mob  # negative is good

        # arrow far-ish: encourages sending arrows to far squares (more partitioning)
        arrow_dist = abs(tr - ar) + abs(tc - ac)

        # trap penalty: if our landing square ends up with very low immediate mobility,
        # penalize (helps avoid self-blocking).
        landing_mob = _count_reachable(nb, (tr, tc))
        trap_penalty = 0.0
        if landing_mob <= 2:
            trap_penalty = W_trap_penalty * (3 - landing_mob)

        score = 0.0
        score += W_mobility * my_mob
        score += W_opp_mobility * opp_mob
        score += W_center * (-center_dist)
        score += W_elim * (-opp_mob_delta)  # if opp_mob decreases, -delta positive
        score += W_arrow_far * arrow_dist
        score -= trap_penalty

        # tie break noise
        score += rng.random() * 1e-6

        if score > best_score:
            best_score = score
            best = (fr, fc, tr, tc, ar, ac)

    fr, fc, tr, tc, ar, ac = best
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def policy(board) -> str:
    board = np.asarray(board)
    # Ensure expected shape
    if board.shape != (6, 6):
        # fallback: try to avoid crash; pick first "valid-looking" move if board is malformed
        return "0,0:0,0:0,0"

    # If player already has no legal move, environment may not call us, but be robust.
    move = _best_move(board)
    # As a final safety check, ensure the string formatting is correct.
    # (If something went wrong, return a syntactically valid move.)
    if not isinstance(move, str) or move.count(":") != 2 or move.count(",") < 6:
        return "0,0:0,0:0,0"
    return move
