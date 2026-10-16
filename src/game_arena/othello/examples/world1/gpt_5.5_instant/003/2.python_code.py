
import numpy as np
import time

# 8 directions
_DIRS = [(-1, -1), (-1, 0), (-1, 1),
         (0, -1),           (0, 1),
         (1, -1),  (1, 0),  (1, 1)]

_COLS = "abcdefgh"

# Positional weights: corners huge, X-squares bad unless corner owned, edges useful.
_W = np.array([
    [120, -25,  20,   8,   8,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   8,   8,  20, -25, 120]
], dtype=np.int16)

_CORNER_ADJ = {
    (0, 0): [(0, 1), (1, 0), (1, 1)],
    (0, 7): [(0, 6), (1, 7), (1, 6)],
    (7, 0): [(6, 0), (7, 1), (6, 1)],
    (7, 7): [(6, 7), (7, 6), (6, 6)],
}

_INF = 10**9


def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _legal_moves(me, opp):
    occ = me | opp
    moves = []
    # Scanning empty squares is fast enough for 8x8 and simple/reliable.
    for r in range(8):
        for c in range(8):
            if occ[r, c]:
                continue
            legal = False
            for dr, dc in _DIRS:
                rr, cc = r + dr, c + dc
                if not _inside(rr, cc) or not opp[rr, cc]:
                    continue
                rr += dr
                cc += dc
                while _inside(rr, cc) and opp[rr, cc]:
                    rr += dr
                    cc += dc
                if _inside(rr, cc) and me[rr, cc]:
                    legal = True
                    break
            if legal:
                moves.append((r, c))
    return moves


def _apply_move(me, opp, move):
    r, c = move
    nme = me.copy()
    nopp = opp.copy()
    nme[r, c] = 1
    for dr, dc in _DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while _inside(rr, cc) and nopp[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _inside(rr, cc) and nme[rr, cc]:
            for fr, fc in line:
                nme[fr, fc] = 1
                nopp[fr, fc] = 0
    return nme, nopp


def _frontier_count(me, opp):
    occ = me | opp
    cnt = 0
    for r in range(8):
        for c in range(8):
            if not me[r, c]:
                continue
            for dr, dc in _DIRS:
                rr, cc = r + dr, c + dc
                if _inside(rr, cc) and not occ[rr, cc]:
                    cnt += 1
                    break
    return cnt


def _stable_corner_lines(me):
    # Lightweight stable-ish count from owned corners along edges.
    s = 0
    if me[0, 0]:
        for c in range(8):
            if me[0, c]: s += 1
            else: break
        for r in range(1, 8):
            if me[r, 0]: s += 1
            else: break
    if me[0, 7]:
        for c in range(7, -1, -1):
            if me[0, c]: s += 1
            else: break
        for r in range(1, 8):
            if me[r, 7]: s += 1
            else: break
    if me[7, 0]:
        for c in range(8):
            if me[7, c]: s += 1
            else: break
        for r in range(6, -1, -1):
            if me[r, 0]: s += 1
            else: break
    if me[7, 7]:
        for c in range(7, -1, -1):
            if me[7, c]: s += 1
            else: break
        for r in range(6, -1, -1):
            if me[r, 7]: s += 1
            else: break
    return s


def _evaluate(me, opp):
    empties = 64 - int(np.sum(me) + np.sum(opp))
    my_discs = int(np.sum(me))
    op_discs = int(np.sum(opp))

    # Endgame: disc differential dominates.
    if empties <= 8:
        return 10000 * (my_discs - op_discs)

    my_moves = len(_legal_moves(me, opp))
    op_moves = len(_legal_moves(opp, me))

    pos = int(np.sum(_W * me) - np.sum(_W * opp))

    my_corners = int(me[0,0] + me[0,7] + me[7,0] + me[7,7])
    op_corners = int(opp[0,0] + opp[0,7] + opp[7,0] + opp[7,7])
    corner_score = 900 * (my_corners - op_corners)

    # Penalize occupying squares adjacent to empty corners.
    danger = 0
    for corner, adj in _CORNER_ADJ.items():
        cr, cc = corner
        if not me[cr, cc] and not opp[cr, cc]:
            for ar, ac in adj:
                if me[ar, ac]:
                    danger -= 180
                elif opp[ar, ac]:
                    danger += 180

    mobility = 90 * (my_moves - op_moves)
    frontier = -22 * (_frontier_count(me, opp) - _frontier_count(opp, me))
    stable = 80 * (_stable_corner_lines(me) - _stable_corner_lines(opp))

    # Disc count is often bad early; useful later.
    disc_weight = -4 if empties > 28 else 18
    discs = disc_weight * (my_discs - op_discs)

    return pos + corner_score + danger + mobility + frontier + stable + discs


def _move_order_score(me, opp, mv):
    r, c = mv
    if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
        return 100000
    nme, nopp = _apply_move(me, opp, mv)
    score = _evaluate(nme, nopp)

    # Strong ordering penalty for playing next to empty corners.
    for corner, adj in _CORNER_ADJ.items():
        cr, cc = corner
        if not me[cr, cc] and not opp[cr, cc] and (r, c) in adj:
            score -= 50000
    return score


def _terminal_score(me, opp):
    diff = int(np.sum(me) - np.sum(opp))
    if diff > 0:
        return 10000000 + diff
    if diff < 0:
        return -10000000 + diff
    return 0


def _alphabeta(me, opp, depth, alpha, beta, start, limit):
    if time.perf_counter() - start > limit:
        raise TimeoutError

    moves = _legal_moves(me, opp)
    if not moves:
        opp_moves = _legal_moves(opp, me)
        if not opp_moves:
            return _terminal_score(me, opp)
        return -_alphabeta(opp, me, depth, -beta, -alpha, start, limit)

    if depth <= 0:
        return _evaluate(me, opp)

    moves.sort(key=lambda m: _move_order_score(me, opp, m), reverse=True)

    best = -_INF
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)
        val = -_alphabeta(nopp, nme, depth - 1, -beta, -alpha, start, limit)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _coord(mv):
    return _COLS[mv[1]] + str(mv[0] + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me = (you.astype(np.uint8) != 0)
    opp = (opponent.astype(np.uint8) != 0)

    moves = _legal_moves(me, opp)
    if not moves:
        return "pass"

    # Immediate corner if available is almost always best and avoids timeout.
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for c in corners:
        if c in moves:
            return _coord(c)

    start = time.perf_counter()
    limit = 0.92

    empties = 64 - int(np.sum(me) + np.sum(opp))

    # Baseline safe move from heuristic ordering.
    moves.sort(key=lambda m: _move_order_score(me, opp, m), reverse=True)
    best_move = moves[0]

    # Depth schedule; iterative deepening keeps move legal under time pressure.
    if empties <= 10:
        max_depth = empties
    elif empties <= 16:
        max_depth = 7
    elif empties <= 26:
        max_depth = 5
    else:
        max_depth = 4

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start > limit:
                break

            current_best = best_move
            current_score = -_INF

            ordered = sorted(moves, key=lambda m: (_move_order_score(me, opp, m), m == best_move), reverse=True)

            alpha = -_INF
            beta = _INF

            for mv in ordered:
                if time.perf_counter() - start > limit:
                    raise TimeoutError
                nme, nopp = _apply_move(me, opp, mv)
                val = -_alphabeta(nopp, nme, depth - 1, -beta, -alpha, start, limit)
                if val > current_score:
                    current_score = val
                    current_best = mv
                if val > alpha:
                    alpha = val

            best_move = current_best

    except TimeoutError:
        pass
    except Exception:
        # Final safety: never risk an illegal/invalid response due to unexpected issues.
        best_move = moves[0]

    return _coord(best_move)
