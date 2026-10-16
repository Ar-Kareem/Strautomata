
import numpy as np
import time

DIRS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
COLS = "abcdefgh"

# Strong but phase-adjusted square values. X-squares and C-squares are dangerous
# unless their corner is owned, handled further in evaluation.
PST = np.array([
    [120, -25,  20,   8,   8,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   8,   8,  20, -25, 120]
], dtype=np.int16)

CORNERS = ((0,0), (0,7), (7,0), (7,7))
X_SQUARES = {
    (1,1):(0,0), (1,6):(0,7), (6,1):(7,0), (6,6):(7,7)
}
C_SQUARES = {
    (0,1):(0,0), (1,0):(0,0),
    (0,6):(0,7), (1,7):(0,7),
    (6,0):(7,0), (7,1):(7,0),
    (6,7):(7,7), (7,6):(7,7)
}

def _on(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _legal_moves(me, opp):
    occ = me | opp
    moves = []
    for r in range(8):
        for c in range(8):
            if occ[r, c]:
                continue
            legal = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if not _on(rr, cc) or not opp[rr, cc]:
                    continue
                rr += dr
                cc += dc
                while _on(rr, cc) and opp[rr, cc]:
                    rr += dr
                    cc += dc
                if _on(rr, cc) and me[rr, cc]:
                    legal = True
                    break
            if legal:
                moves.append((r, c))
    return moves

def _apply_move(me, opp, mv):
    if mv is None:
        return opp.copy(), me.copy()
    r, c = mv
    nme = me.copy()
    nopp = opp.copy()
    nme[r, c] = 1
    for dr, dc in DIRS:
        line = []
        rr, cc = r + dr, c + dc
        while _on(rr, cc) and nopp[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _on(rr, cc) and nme[rr, cc]:
            for fr, fc in line:
                nme[fr, fc] = 1
                nopp[fr, fc] = 0
    return nopp, nme  # perspective switches: next player is opponent

def _disc_diff(me, opp):
    return int(me.sum()) - int(opp.sum())

def _frontier_count(me, occ):
    cnt = 0
    empt = 1 - occ
    for r in range(8):
        for c in range(8):
            if me[r, c]:
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    if _on(rr, cc) and empt[rr, cc]:
                        cnt += 1
                        break
    return cnt

def _stable_edge_count(me):
    # Conservative stable estimate from occupied corners along edges.
    s = 0
    if me[0,0]:
        for c in range(8):
            if me[0,c]: s += 1
            else: break
        for r in range(1,8):
            if me[r,0]: s += 1
            else: break
    if me[0,7]:
        for c in range(7,-1,-1):
            if me[0,c]: s += 1
            else: break
        for r in range(1,8):
            if me[r,7]: s += 1
            else: break
    if me[7,0]:
        for c in range(8):
            if me[7,c]: s += 1
            else: break
        for r in range(6,-1,-1):
            if me[r,0]: s += 1
            else: break
    if me[7,7]:
        for c in range(7,-1,-1):
            if me[7,c]: s += 1
            else: break
        for r in range(6,-1,-1):
            if me[r,7]: s += 1
            else: break
    return s

def _evaluate(me, opp):
    empties = 64 - int((me | opp).sum())
    if empties == 0:
        d = _disc_diff(me, opp)
        return 1000000 if d > 0 else (-1000000 if d < 0 else 0)

    my_moves = len(_legal_moves(me, opp))
    op_moves = len(_legal_moves(opp, me))
    if my_moves == 0 and op_moves == 0:
        d = _disc_diff(me, opp)
        return d * 100000

    occ = me | opp
    my_discs = int(me.sum())
    op_discs = int(opp.sum())

    # Positional score with dynamic penalties around empty corners.
    pos = int((PST * me).sum() - (PST * opp).sum())
    for sq, corner in X_SQUARES.items():
        r, c = sq
        cr, cc = corner
        if not occ[cr, cc]:
            if me[r, c]: pos -= 80
            if opp[r, c]: pos += 80
    for sq, corner in C_SQUARES.items():
        r, c = sq
        cr, cc = corner
        if not occ[cr, cc]:
            if me[r, c]: pos -= 45
            if opp[r, c]: pos += 45

    my_corners = sum(1 for r, c in CORNERS if me[r, c])
    op_corners = sum(1 for r, c in CORNERS if opp[r, c])
    corner_score = 350 * (my_corners - op_corners)

    mobility = 0
    if my_moves + op_moves:
        mobility = 100 * (my_moves - op_moves) // (my_moves + op_moves)

    my_front = _frontier_count(me, occ)
    op_front = _frontier_count(opp, occ)
    frontier = 0
    if my_front + op_front:
        frontier = -70 * (my_front - op_front) // (my_front + op_front)

    stable = 25 * (_stable_edge_count(me) - _stable_edge_count(opp))

    disc = 0
    if my_discs + op_discs:
        disc = 100 * (my_discs - op_discs) // (my_discs + op_discs)

    parity = 18 if (empties % 2 == 1) else -18

    # Phase weighting: avoid greed early, care about material late.
    if empties > 40:
        return 6*pos + 9*mobility + corner_score + 5*frontier + stable - 2*disc
    elif empties > 16:
        return 5*pos + 8*mobility + corner_score + 4*frontier + 2*stable + disc
    else:
        return 3*pos + 4*mobility + corner_score + 2*frontier + 2*stable + 8*disc + parity

def _move_order_score(me, opp, mv):
    r, c = mv
    if (r, c) in CORNERS:
        return 100000
    score = int(PST[r, c]) * 10
    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not (me[cr, cc] or opp[cr, cc]):
            score -= 5000
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not (me[cr, cc] or opp[cr, cc]):
            score -= 2500
    nme, nopp = _apply_move(me, opp, mv)
    # _apply_move returns next-perspective arrays, so current resulting board is nopp vs nme.
    after_me, after_opp = nopp, nme
    score -= 35 * len(_legal_moves(after_opp, after_me))
    score += 10 * (int(after_me.sum()) - int(me.sum()))
    return score

def _terminal_value(me, opp):
    d = _disc_diff(me, opp)
    if d > 0:
        return 1000000 + d
    if d < 0:
        return -1000000 + d
    return 0

def _alphabeta(me, opp, depth, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise TimeoutError

    moves = _legal_moves(me, opp)
    op_moves_exist = None

    if depth <= 0:
        return _evaluate(me, opp)

    if not moves:
        op_moves = _legal_moves(opp, me)
        op_moves_exist = bool(op_moves)
        if not op_moves_exist:
            return _terminal_value(me, opp)
        val = -_alphabeta(opp, me, depth - 1, -beta, -alpha, deadline)
        return val

    # Endgame: search all remaining moves when feasible.
    moves.sort(key=lambda m: _move_order_score(me, opp, m), reverse=True)

    best = -10**9
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)
        val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _choose_fallback(me, opp, moves):
    # Safe deterministic fallback, heavily preferring corners and avoiding poison squares.
    best_mv = moves[0]
    best_sc = -10**18
    for mv in moves:
        sc = _move_order_score(me, opp, mv)
        nme, nopp = _apply_move(me, opp, mv)
        sc += _evaluate(nopp, nme) // 20
        if sc > best_sc:
            best_sc = sc
            best_mv = mv
    return best_mv

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me = np.array(you, dtype=np.int8, copy=True)
    opp = np.array(opponent, dtype=np.int8, copy=True)

    moves = _legal_moves(me, opp)
    if not moves:
        return "pass"

    # Immediate corner rule is almost always correct and saves time.
    for mv in moves:
        if mv in CORNERS:
            return COLS[mv[1]] + str(mv[0] + 1)

    start = time.perf_counter()
    deadline = start + 0.92

    empties = 64 - int((me | opp).sum())
    if empties <= 10:
        max_depth = empties + 2
    elif empties <= 16:
        max_depth = 8
    elif empties <= 28:
        max_depth = 6
    else:
        max_depth = 5

    ordered = sorted(moves, key=lambda m: _move_order_score(me, opp, m), reverse=True)
    best_move = _choose_fallback(me, opp, ordered)

    # Iterative deepening; if time expires, keep the last completed result.
    depth = 1
    while depth <= max_depth:
        try:
            alpha = -10**9
            beta = 10**9
            local_best = best_move
            local_score = -10**9

            # Reorder using previous best first.
            search_moves = ordered[:]
            if best_move in search_moves:
                search_moves.remove(best_move)
                search_moves.insert(0, best_move)

            for mv in search_moves:
                if time.perf_counter() > deadline:
                    raise TimeoutError
                nme, nopp = _apply_move(me, opp, mv)
                val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha, deadline)
                if val > local_score:
                    local_score = val
                    local_best = mv
                if val > alpha:
                    alpha = val

            best_move = local_best
            depth += 1
        except TimeoutError:
            break

    return COLS[best_move[1]] + str(best_move[0] + 1)
