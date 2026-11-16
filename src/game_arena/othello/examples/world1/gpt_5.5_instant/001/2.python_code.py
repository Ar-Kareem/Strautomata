
import numpy as np
import time

# 8 directions
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**9
COLS = "abcdefgh"

# Positional table: deliberately corner-heavy, with strong penalties around empty corners.
PST = np.array([
    [120, -25,  20,   8,   8,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  12,   4,   4,  12,  -5,  20],
    [  8,  -5,   4,   2,   2,   4,  -5,   8],
    [  8,  -5,   4,   2,   2,   4,  -5,   8],
    [ 20,  -5,  12,   4,   4,  12,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   8,   8,  20, -25, 120]
], dtype=np.int32)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
X_SQUARES = {(1, 1): (0, 0), (1, 6): (0, 7), (6, 1): (7, 0), (6, 6): (7, 7)}
C_SQUARES = {
    (0, 1): (0, 0), (1, 0): (0, 0),
    (0, 6): (0, 7), (1, 7): (0, 7),
    (6, 0): (7, 0), (7, 1): (7, 0),
    (6, 7): (7, 7), (7, 6): (7, 7)
}

# Move ordering preference: corners first, then safe-ish squares, bad corner-adjacent last.
ORDER_TABLE = np.array([
    [1000, -200, 80, 40, 40, 80, -200, 1000],
    [-200, -500,  0,  0,  0,  0, -500, -200],
    [  80,    0, 30, 10, 10, 30,    0,   80],
    [  40,    0, 10,  5,  5, 10,    0,   40],
    [  40,    0, 10,  5,  5, 10,    0,   40],
    [  80,    0, 30, 10, 10, 30,    0,   80],
    [-200, -500,  0,  0,  0,  0, -500, -200],
    [1000, -200, 80, 40, 40, 80, -200, 1000]
], dtype=np.int32)


def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _legal_moves(me, opp):
    occupied = me | opp
    moves = []
    for r in range(8):
        for c in range(8):
            if occupied[r, c]:
                continue
            legal = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                seen_opp = False
                while _inside(rr, cc) and opp[rr, cc]:
                    seen_opp = True
                    rr += dr
                    cc += dc
                if seen_opp and _inside(rr, cc) and me[rr, cc]:
                    legal = True
                    break
            if legal:
                moves.append((r, c))
    return moves


def _flips_for_move(me, opp, move):
    r, c = move
    flips = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while _inside(rr, cc) and opp[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _inside(rr, cc) and me[rr, cc]:
            flips.extend(line)
    return flips


def _apply_move(me, opp, move):
    # returns new_me, new_opp after current player moves
    nme = me.copy()
    nopp = opp.copy()
    flips = _flips_for_move(nme, nopp, move)
    r, c = move
    nme[r, c] = 1
    for rr, cc in flips:
        nme[rr, cc] = 1
        nopp[rr, cc] = 0
    return nme, nopp


def _frontier_count(discs, empty):
    cnt = 0
    positions = np.argwhere(discs)
    for r, c in positions:
        for dr, dc in DIRS:
            rr, cc = int(r) + dr, int(c) + dc
            if _inside(rr, cc) and empty[rr, cc]:
                cnt += 1
                break
    return cnt


def _stable_corner_lines(me, opp):
    # Approximate stable discs: contiguous owned discs from occupied corners along edges.
    score = 0
    for cr, cc in CORNERS:
        if me[cr, cc]:
            sign = 1
        elif opp[cr, cc]:
            sign = -1
        else:
            continue

        # directions along two edges from each corner
        edge_dirs = []
        if cr == 0:
            edge_dirs.append((1, 0))
        else:
            edge_dirs.append((-1, 0))
        if cc == 0:
            edge_dirs.append((0, 1))
        else:
            edge_dirs.append((0, -1))

        for dr, dc in edge_dirs:
            rr, cc2 = cr, cc
            while _inside(rr, cc2):
                if sign == 1 and me[rr, cc2]:
                    score += 1
                elif sign == -1 and opp[rr, cc2]:
                    score -= 1
                else:
                    break
                rr += dr
                cc2 += dc
    return score


def _evaluate(me, opp):
    my_count = int(me.sum())
    op_count = int(opp.sum())
    occupied_count = my_count + op_count
    empty = 1 - (me | opp)
    empties = 64 - occupied_count

    # Terminal check
    my_moves = _legal_moves(me, opp)
    op_moves = _legal_moves(opp, me)
    if not my_moves and not op_moves:
        diff = my_count - op_count
        if diff > 0:
            return 1000000 + diff
        if diff < 0:
            return -1000000 + diff
        return 0

    # Dynamic game phase
    if occupied_count < 22:
        phase = 0
    elif occupied_count < 46:
        phase = 1
    else:
        phase = 2

    # Mobility
    mobility = len(my_moves) - len(op_moves)
    potential_my = 0
    potential_op = 0
    for r, c in np.argwhere(empty):
        r = int(r); c = int(c)
        adj_my = False
        adj_op = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if _inside(rr, cc):
                if me[rr, cc]:
                    adj_my = True
                elif opp[rr, cc]:
                    adj_op = True
        if adj_op:
            potential_my += 1
        if adj_my:
            potential_op += 1
    potential_mobility = potential_my - potential_op

    # Corners
    corner_score = 0
    for r, c in CORNERS:
        if me[r, c]:
            corner_score += 1
        elif opp[r, c]:
            corner_score -= 1

    # Positional
    positional = int((PST * me).sum() - (PST * opp).sum())

    # Penalize X/C squares only if their corner is empty.
    danger = 0
    for (r, c), (cr, cc) in X_SQUARES.items():
        if not me[cr, cc] and not opp[cr, cc]:
            if me[r, c]:
                danger -= 1
            elif opp[r, c]:
                danger += 1
    for (r, c), (cr, cc) in C_SQUARES.items():
        if not me[cr, cc] and not opp[cr, cc]:
            if me[r, c]:
                danger -= 1
            elif opp[r, c]:
                danger += 1

    # Frontier discs: fewer is better.
    my_front = _frontier_count(me, empty)
    op_front = _frontier_count(opp, empty)
    frontier = op_front - my_front

    stable = _stable_corner_lines(me, opp)

    disc_diff = my_count - op_count

    if phase == 0:
        return (900 * corner_score +
                85 * mobility +
                25 * potential_mobility +
                8 * positional +
                75 * danger +
                18 * frontier +
                60 * stable -
                4 * disc_diff)
    elif phase == 1:
        return (1100 * corner_score +
                75 * mobility +
                12 * potential_mobility +
                8 * positional +
                80 * danger +
                22 * frontier +
                85 * stable +
                2 * disc_diff)
    else:
        # Endgame: disc count and exact search become more important.
        return (1400 * corner_score +
                45 * mobility +
                5 * potential_mobility +
                5 * positional +
                50 * danger +
                10 * frontier +
                100 * stable +
                18 * disc_diff +
                (64 - empties) * disc_diff)


def _move_order_key(move, me, opp):
    r, c = move
    score = int(ORDER_TABLE[r, c])

    # Adjust bad squares near empty corners.
    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not me[cr, cc] and not opp[cr, cc]:
            score -= 600
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not me[cr, cc] and not opp[cr, cc]:
            score -= 250

    # Prefer moves that reduce opponent mobility.
    nme, nopp = _apply_move(me, opp, move)
    opp_mob = len(_legal_moves(nopp, nme))
    score -= 15 * opp_mob

    # But corners are always excellent.
    if move in CORNERS:
        score += 5000
    return score


def _negamax(me, opp, depth, alpha, beta, deadline, passed=False):
    if time.perf_counter() >= deadline:
        raise TimeoutError

    moves = _legal_moves(me, opp)

    if depth == 0:
        return _evaluate(me, opp)

    if not moves:
        opp_moves = _legal_moves(opp, me)
        if not opp_moves:
            return _evaluate(me, opp)
        # Pass: opponent moves, perspective changes.
        return -_negamax(opp, me, depth, -beta, -alpha, deadline, passed=True)

    moves.sort(key=lambda m: _move_order_key(m, me, opp), reverse=True)

    best = -INF
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)
        val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, deadline, passed=False)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        if time.perf_counter() >= deadline:
            raise TimeoutError
    return best


def _exact_negamax(me, opp, alpha, beta, deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError

    moves = _legal_moves(me, opp)
    if not moves:
        opp_moves = _legal_moves(opp, me)
        if not opp_moves:
            return int(me.sum()) - int(opp.sum())
        return -_exact_negamax(opp, me, -beta, -alpha, deadline)

    moves.sort(key=lambda m: _move_order_key(m, me, opp), reverse=True)
    best = -INF
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)
        val = -_exact_negamax(nopp, nme, -beta, -alpha, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _choose_move(me, opp, moves, deadline):
    # Immediate corner if available is rarely wrong and saves time.
    for corner in CORNERS:
        if corner in moves:
            return corner

    moves.sort(key=lambda m: _move_order_key(m, me, opp), reverse=True)
    best_move = moves[0]
    best_score = -INF

    empties = 64 - int((me | opp).sum())

    # Exact endgame search when feasible.
    if empties <= 10:
        try:
            for mv in moves:
                nme, nopp = _apply_move(me, opp, mv)
                val = -_exact_negamax(nopp, nme, -INF, INF, deadline)
                if val > best_score:
                    best_score = val
                    best_move = mv
            return best_move
        except TimeoutError:
            pass

    # Iterative deepening. Depth tuned for Python under 1s.
    max_depth = 5
    if empties <= 18:
        max_depth = 7
    elif empties <= 28:
        max_depth = 6
    elif len(moves) <= 4:
        max_depth = 6

    completed_best = best_move
    completed_score = best_score

    for depth in range(1, max_depth + 1):
        try:
            local_best = best_move
            local_score = -INF
            alpha = -INF
            beta = INF

            ordered = list(moves)
            if completed_best in ordered:
                ordered.remove(completed_best)
                ordered.insert(0, completed_best)

            for mv in ordered:
                if time.perf_counter() >= deadline:
                    raise TimeoutError
                nme, nopp = _apply_move(me, opp, mv)
                val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, deadline)
                if val > local_score:
                    local_score = val
                    local_best = mv
                if val > alpha:
                    alpha = val

            completed_best = local_best
            completed_score = local_score
            best_move = completed_best
            best_score = completed_score
        except TimeoutError:
            break

    return best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move in algebraic notation, or "pass" if no legal moves exist.
    """
    # Ensure compact int arrays with 0/1 values.
    me = (you.astype(np.int8) != 0).astype(np.int8)
    opp = (opponent.astype(np.int8) != 0).astype(np.int8)

    moves = _legal_moves(me, opp)
    if not moves:
        return "pass"

    # Use a conservative time budget below the stated 1s.
    deadline = time.perf_counter() + 0.88

    try:
        move = _choose_move(me, opp, moves, deadline)
    except Exception:
        # Absolute fallback: choose best ordered legal move.
        moves.sort(key=lambda m: int(ORDER_TABLE[m[0], m[1]]), reverse=True)
        move = moves[0]

    # Final legality guard.
    if move not in moves:
        move = moves[0]

    r, c = move
    return COLS[c] + str(r + 1)
