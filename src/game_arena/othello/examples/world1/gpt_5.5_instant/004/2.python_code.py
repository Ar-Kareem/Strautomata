
import numpy as np
import time

# 8 directions
DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
COLS = "abcdefgh"

# Positional table: corners and good edges high, X-squares bad.
PST = np.array([
    [120, -35,  20,   5,   5,  20, -35, 120],
    [-35, -60, -10, -10, -10, -10, -60, -35],
    [ 20, -10,  15,   3,   3,  15, -10,  20],
    [  5, -10,   3,   3,   3,   3, -10,   5],
    [  5, -10,   3,   3,   3,   3, -10,   5],
    [ 20, -10,  15,   3,   3,  15, -10,  20],
    [-35, -60, -10, -10, -10, -10, -60, -35],
    [120, -35,  20,   5,   5,  20, -35, 120]
], dtype=np.int16)

CORNERS = ((0,0),(0,7),(7,0),(7,7))
X_SQUARES = {(1,1):(0,0), (1,6):(0,7), (6,1):(7,0), (6,6):(7,7)}
C_SQUARES = {
    (0,1):(0,0), (1,0):(0,0),
    (0,6):(0,7), (1,7):(0,7),
    (6,0):(7,0), (7,1):(7,0),
    (6,7):(7,7), (7,6):(7,7),
}


def _to_bitboard(arr):
    b = 0
    # numpy iteration overhead is okay for 64 squares
    for r in range(8):
        row = arr[r]
        for c in range(8):
            if row[c]:
                b |= 1 << (r * 8 + c)
    return b


def _popcount(x):
    return int(x.bit_count())


def _bit_to_move(idx):
    return COLS[idx & 7] + str((idx >> 3) + 1)


def _legal_moves_bits(me, opp):
    occupied = me | opp
    empty = (~occupied) & ((1 << 64) - 1)
    moves = []
    # Simple robust generator; fast enough with alpha-beta and caching.
    for idx in range(64):
        bit = 1 << idx
        if not (empty & bit):
            continue
        r, c = divmod(idx, 8)
        legal = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            seen_opp = False
            while 0 <= rr < 8 and 0 <= cc < 8:
                b = 1 << (rr * 8 + cc)
                if opp & b:
                    seen_opp = True
                elif me & b:
                    if seen_opp:
                        legal = True
                    break
                else:
                    break
                rr += dr
                cc += dc
            if legal:
                moves.append(idx)
                break
    return moves


def _apply_move(me, opp, idx):
    r, c = divmod(idx, 8)
    move_bit = 1 << idx
    flips = 0
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = 0
        while 0 <= rr < 8 and 0 <= cc < 8:
            b = 1 << (rr * 8 + cc)
            if opp & b:
                line |= b
            elif me & b:
                flips |= line
                break
            else:
                break
            rr += dr
            cc += dc
    me2 = me | move_bit | flips
    opp2 = opp & ~flips
    return me2, opp2


def _frontier_count(me, opp):
    occupied = me | opp
    empty = (~occupied) & ((1 << 64) - 1)
    fm = fo = 0
    for idx in range(64):
        bit = 1 << idx
        if not (occupied & bit):
            continue
        r, c = divmod(idx, 8)
        is_frontier = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and (empty & (1 << (rr * 8 + cc))):
                is_frontier = True
                break
        if is_frontier:
            if me & bit:
                fm += 1
            else:
                fo += 1
    return fm, fo


def _corner_adj_penalty(me, opp):
    score = 0
    for sq, corner in X_SQUARES.items():
        sidx = sq[0] * 8 + sq[1]
        cidx = corner[0] * 8 + corner[1]
        if not ((me | opp) & (1 << cidx)):
            if me & (1 << sidx):
                score -= 45
            elif opp & (1 << sidx):
                score += 45
    for sq, corner in C_SQUARES.items():
        sidx = sq[0] * 8 + sq[1]
        cidx = corner[0] * 8 + corner[1]
        if not ((me | opp) & (1 << cidx)):
            if me & (1 << sidx):
                score -= 22
            elif opp & (1 << sidx):
                score += 22
    return score


def _edge_stability_rough(me, opp):
    # Reward discs connected from owned corners along edges.
    score = 0
    for cr, cc in CORNERS:
        cbit = 1 << (cr * 8 + cc)
        if me & cbit:
            owner = 1
        elif opp & cbit:
            owner = -1
        else:
            continue

        # horizontal from corner
        step_c = 1 if cc == 0 else -1
        c = cc
        while 0 <= c < 8:
            b = 1 << (cr * 8 + c)
            if owner == 1 and (me & b):
                score += 12
            elif owner == -1 and (opp & b):
                score -= 12
            else:
                break
            c += step_c

        # vertical from corner
        step_r = 1 if cr == 0 else -1
        r = cr
        while 0 <= r < 8:
            b = 1 << (r * 8 + cc)
            if owner == 1 and (me & b):
                score += 12
            elif owner == -1 and (opp & b):
                score -= 12
            else:
                break
            r += step_r
    return score


def _evaluate(me, opp):
    occupied = me | opp
    discs = _popcount(occupied)
    my_discs = _popcount(me)
    op_discs = _popcount(opp)

    my_moves = len(_legal_moves_bits(me, opp))
    op_moves = len(_legal_moves_bits(opp, me))

    if my_moves == 0 and op_moves == 0:
        diff = my_discs - op_discs
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    # Phase weights
    if discs < 22:
        w_mob, w_pst, w_disc, w_front, w_corner = 90, 10, -8, 35, 900
    elif discs < 48:
        w_mob, w_pst, w_disc, w_front, w_corner = 75, 8, 2, 28, 900
    else:
        w_mob, w_pst, w_disc, w_front, w_corner = 45, 4, 18, 12, 1000

    score = 0

    # Mobility
    score += w_mob * (my_moves - op_moves)

    # Disc differential: negative early to avoid overflipping
    score += w_disc * (my_discs - op_discs)

    # Positional table
    pst_score = 0
    for idx in range(64):
        b = 1 << idx
        if me & b:
            pst_score += int(PST[idx >> 3, idx & 7])
        elif opp & b:
            pst_score -= int(PST[idx >> 3, idx & 7])
    score += w_pst * pst_score

    # Corners
    my_corners = 0
    op_corners = 0
    for r, c in CORNERS:
        b = 1 << (r * 8 + c)
        if me & b:
            my_corners += 1
        elif opp & b:
            op_corners += 1
    score += w_corner * (my_corners - op_corners)

    # Frontier discs: fewer is better
    fm, fo = _frontier_count(me, opp)
    score += w_front * (fo - fm)

    # Corner-adjacent danger and rough stable edges
    score += 15 * _corner_adj_penalty(me, opp)
    score += 18 * _edge_stability_rough(me, opp)

    # Parity in late endgame
    empties = 64 - discs
    if empties <= 14:
        score += 12 * ((empties % 2) * 2 - 1) * (my_moves - op_moves)
        score += 35 * (my_discs - op_discs)

    return int(score)


def _move_order_score(me, opp, idx):
    r, c = divmod(idx, 8)
    score = int(PST[r, c]) * 10

    if (r, c) in CORNERS:
        score += 100000

    # Avoid X/C squares if adjacent corner is empty
    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not ((me | opp) & (1 << (cr * 8 + cc))):
            score -= 25000
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not ((me | opp) & (1 << (cr * 8 + cc))):
            score -= 9000

    me2, opp2 = _apply_move(me, opp, idx)
    opp_reply = len(_legal_moves_bits(opp2, me2))
    score -= 120 * opp_reply

    # Prefer moves that give opponent no move
    if opp_reply == 0:
        score += 5000

    # Small flip-count heuristic: avoid excessive early flips
    flips = _popcount(me2) - _popcount(me) - 1
    discs = _popcount(me | opp)
    if discs < 28:
        score -= 20 * flips
    else:
        score += 8 * flips

    return score


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start = time.perf_counter()
    deadline = start + 0.92

    me = _to_bitboard(you)
    opp = _to_bitboard(opponent)

    legal = _legal_moves_bits(me, opp)
    if not legal:
        return "pass"

    # Immediate corner if available is almost always best and saves time.
    for idx in legal:
        if divmod(idx, 8) in CORNERS:
            return _bit_to_move(idx)

    ordered = sorted(legal, key=lambda m: _move_order_score(me, opp, m), reverse=True)
    best_move = ordered[0]
    best_score = -10**18
    tt = {}

    def negamax(a_me, a_opp, depth, alpha, beta, passed):
        if time.perf_counter() > deadline:
            raise TimeoutError

        key = (a_me, a_opp, depth, passed)
        cached = tt.get(key)
        if cached is not None:
            return cached

        moves = _legal_moves_bits(a_me, a_opp)
        if depth == 0:
            val = _evaluate(a_me, a_opp)
            tt[key] = val
            return val

        if not moves:
            opp_moves = _legal_moves_bits(a_opp, a_me)
            if not opp_moves:
                diff = _popcount(a_me) - _popcount(a_opp)
                if diff > 0:
                    return 1000000 + diff
                if diff < 0:
                    return -1000000 + diff
                return 0
            val = -negamax(a_opp, a_me, depth - 1, -beta, -alpha, True)
            tt[key] = val
            return val

        moves.sort(key=lambda m: _move_order_score(a_me, a_opp, m), reverse=True)

        value = -10**18
        for m in moves:
            nme, nopp = _apply_move(a_me, a_opp, m)
            score = -negamax(nopp, nme, depth - 1, -beta, -alpha, False)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        tt[key] = value
        return value

    empties = 64 - _popcount(me | opp)

    # Depth schedule: deeper near endgame.
    if empties <= 8:
        max_depth = empties + 2
    elif empties <= 14:
        max_depth = 8
    elif empties <= 24:
        max_depth = 6
    else:
        max_depth = 5

    # If branching is high, be conservative.
    if len(legal) >= 10 and max_depth > 5:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break
            current_best = best_move
            current_score = -10**18

            # Principal variation first
            root_moves = ordered[:]
            if best_move in root_moves:
                root_moves.remove(best_move)
                root_moves.insert(0, best_move)

            alpha = -10**18
            beta = 10**18

            for m in root_moves:
                if time.perf_counter() > deadline:
                    raise TimeoutError
                nme, nopp = _apply_move(me, opp, m)
                score = -negamax(nopp, nme, depth - 1, -beta, -alpha, False)
                if score > current_score:
                    current_score = score
                    current_best = m
                if score > alpha:
                    alpha = score

            best_move = current_best
            best_score = current_score

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety fallback.
        best_move = ordered[0]

    # Final legality safety check
    if best_move not in legal:
        best_move = ordered[0]

    return _bit_to_move(best_move)
