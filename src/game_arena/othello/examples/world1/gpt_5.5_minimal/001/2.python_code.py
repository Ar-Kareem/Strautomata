
import numpy as np
import time

# 8 directions for Othello flips
_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

# Positional weights: corners are extremely valuable, squares adjacent to
# empty corners are dangerous, edges are generally good.
_WEIGHTS = np.array([
    [120, -25,  20,   8,   8,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [  8,  -5,   3,   3,   3,   3,  -5,   8],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   8,   8,  20, -25, 120],
], dtype=np.int16)

_CORNERS = ((0, 0), (0, 7), (7, 0), (7, 7))

# Squares adjacent to each corner, used to penalize giving access near empty corners.
_CORNER_ADJ = {
    (0, 0): ((0, 1), (1, 0), (1, 1)),
    (0, 7): ((0, 6), (1, 7), (1, 6)),
    (7, 0): ((7, 1), (6, 0), (6, 1)),
    (7, 7): ((7, 6), (6, 7), (6, 6)),
}


def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _legal_moves(me, opp):
    """Return list of legal moves as (r, c)."""
    occupied = me | opp
    moves = []

    for r in range(8):
        for c in range(8):
            if occupied[r, c]:
                continue

            legal = False
            for dr, dc in _DIRS:
                rr, cc = r + dr, c + dc
                if not _in_bounds(rr, cc) or not opp[rr, cc]:
                    continue

                rr += dr
                cc += dc
                while _in_bounds(rr, cc) and opp[rr, cc]:
                    rr += dr
                    cc += dc

                if _in_bounds(rr, cc) and me[rr, cc]:
                    legal = True
                    break

            if legal:
                moves.append((r, c))

    return moves


def _flip_count_for_move(me, opp, move):
    """Count how many discs would be flipped by move."""
    r, c = move
    total = 0

    for dr, dc in _DIRS:
        rr, cc = r + dr, c + dc
        cnt = 0

        while _in_bounds(rr, cc) and opp[rr, cc]:
            cnt += 1
            rr += dr
            cc += dc

        if cnt and _in_bounds(rr, cc) and me[rr, cc]:
            total += cnt

    return total


def _apply_move(me, opp, move):
    """Apply move and return new_me, new_opp from same side perspective."""
    r, c = move
    new_me = me.copy()
    new_opp = opp.copy()

    new_me[r, c] = 1

    for dr, dc in _DIRS:
        rr, cc = r + dr, c + dc
        captured = []

        while _in_bounds(rr, cc) and new_opp[rr, cc]:
            captured.append((rr, cc))
            rr += dr
            cc += dc

        if captured and _in_bounds(rr, cc) and new_me[rr, cc]:
            for fr, fc in captured:
                new_me[fr, fc] = 1
                new_opp[fr, fc] = 0

    return new_me, new_opp


def _move_to_str(move):
    r, c = move
    return chr(ord("a") + c) + str(r + 1)


def _danger_near_empty_corners(me, opp):
    """Penalty if my discs occupy squares next to empty corners."""
    occupied = me | opp
    score = 0

    for corner, adj in _CORNER_ADJ.items():
        cr, cc = corner
        if occupied[cr, cc]:
            continue
        for ar, ac in adj:
            if me[ar, ac]:
                score -= 35
            elif opp[ar, ac]:
                score += 35

    return score


def _stable_corner_edge_bonus(me, opp):
    """
    Approximate stable-disc bonus from corners along edges.
    True stability is expensive; this captures most important edge stability.
    """
    score = 0

    # For each owned corner, reward contiguous owned discs along the two edges.
    for cr, cc in _CORNERS:
        if me[cr, cc]:
            score += 80
            # horizontal edge
            step_c = 1 if cc == 0 else -1
            c = cc + step_c
            while 0 <= c < 8 and me[cr, c]:
                score += 12
                c += step_c
            # vertical edge
            step_r = 1 if cr == 0 else -1
            r = cr + step_r
            while 0 <= r < 8 and me[r, cc]:
                score += 12
                r += step_r

        elif opp[cr, cc]:
            score -= 80
            step_c = 1 if cc == 0 else -1
            c = cc + step_c
            while 0 <= c < 8 and opp[cr, c]:
                score -= 12
                c += step_c
            step_r = 1 if cr == 0 else -1
            r = cr + step_r
            while 0 <= r < 8 and opp[r, cc]:
                score -= 12
                r += step_r

    return score


def _evaluate(me, opp):
    """Heuristic evaluation from current player's perspective."""
    my_count = int(me.sum())
    op_count = int(opp.sum())
    occupied_count = my_count + op_count
    empties = 64 - occupied_count

    my_moves = len(_legal_moves(me, opp))
    op_moves = len(_legal_moves(opp, me))

    # Terminal position or double pass
    if my_moves == 0 and op_moves == 0:
        diff = my_count - op_count
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    positional = int((me * _WEIGHTS).sum() - (opp * _WEIGHTS).sum())

    corner_score = 0
    for r, c in _CORNERS:
        if me[r, c]:
            corner_score += 1
        elif opp[r, c]:
            corner_score -= 1

    mobility = my_moves - op_moves

    # Potential mobility: empty squares adjacent to opponent discs are possible future options.
    empty = 1 - (me | opp)
    my_potential = 0
    op_potential = 0
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            adj_opp = False
            adj_me = False
            for dr, dc in _DIRS:
                rr, cc = r + dr, c + dc
                if _in_bounds(rr, cc):
                    if opp[rr, cc]:
                        adj_opp = True
                    elif me[rr, cc]:
                        adj_me = True
            if adj_opp:
                my_potential += 1
            if adj_me:
                op_potential += 1

    potential_mobility = my_potential - op_potential

    danger = _danger_near_empty_corners(me, opp)
    stableish = _stable_corner_edge_bonus(me, opp)

    # Disc parity matters mostly late. In the opening, having fewer discs can be better.
    disc_diff = my_count - op_count

    if empties > 40:
        return (
            8 * positional +
            900 * corner_score +
            90 * mobility +
            25 * potential_mobility +
            15 * danger +
            8 * stableish -
            4 * disc_diff
        )
    elif empties > 16:
        return (
            6 * positional +
            1100 * corner_score +
            120 * mobility +
            20 * potential_mobility +
            15 * danger +
            10 * stableish +
            3 * disc_diff
        )
    else:
        return (
            3 * positional +
            1400 * corner_score +
            80 * mobility +
            10 * potential_mobility +
            10 * danger +
            12 * stableish +
            25 * disc_diff
        )


def _ordered_moves(me, opp, moves):
    """Order moves to improve alpha-beta pruning."""
    scored = []
    occupied = me | opp

    for mv in moves:
        r, c = mv
        s = int(_WEIGHTS[r, c]) * 10

        if mv in _CORNERS:
            s += 100000

        # Discourage moves adjacent to an empty corner.
        for corner, adj in _CORNER_ADJ.items():
            cr, cc = corner
            if not occupied[cr, cc] and mv in adj:
                s -= 50000

        # Prefer moves that reduce opponent mobility.
        nme, nopp = _apply_move(me, opp, mv)
        opp_mob = len(_legal_moves(nopp, nme))
        s -= 200 * opp_mob

        # Flipping too many discs early is not always good, but it helps move ordering.
        s += 5 * _flip_count_for_move(me, opp, mv)

        scored.append((s, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def _negamax(me, opp, depth, alpha, beta, end_time):
    if time.perf_counter() > end_time:
        raise TimeoutError

    moves = _legal_moves(me, opp)
    opp_moves_exist = None

    if depth <= 0:
        return _evaluate(me, opp)

    if not moves:
        opp_moves = _legal_moves(opp, me)
        opp_moves_exist = bool(opp_moves)
        if not opp_moves_exist:
            diff = int(me.sum()) - int(opp.sum())
            if diff > 0:
                return 100000 + diff
            if diff < 0:
                return -100000 + diff
            return 0
        # Pass turn: perspective swaps, so negate.
        return -_negamax(opp, me, depth - 1, -beta, -alpha, end_time)

    best = -10**12
    for mv in _ordered_moves(me, opp, moves):
        nme, nopp = _apply_move(me, opp, mv)
        val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, end_time)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _choose_depth(empties, move_count):
    """Conservative depth selection for a 1 second budget."""
    if empties <= 8:
        return empties + 1
    if empties <= 12:
        return 9
    if empties <= 16:
        return 7
    if empties <= 28:
        return 5
    if move_count <= 5:
        return 5
    return 4


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move in algebraic notation, or 'pass' if no legal move exists.
    """
    # Convert to compact integer arrays in case inputs have a wider dtype.
    me = (you.astype(np.uint8) != 0).astype(np.uint8)
    opp = (opponent.astype(np.uint8) != 0).astype(np.uint8)

    moves = _legal_moves(me, opp)
    if not moves:
        return "pass"

    # Immediate corner rule: corners are almost always best and avoids search timeout.
    for corner in _CORNERS:
        if corner in moves:
            return _move_to_str(corner)

    # Safe fallback: best positional legal move.
    ordered_initial = _ordered_moves(me, opp, moves)
    best_move = ordered_initial[0]

    empties = 64 - int(me.sum()) - int(opp.sum())
    target_depth = _choose_depth(empties, len(moves))

    # Keep margin below 1 second.
    end_time = time.perf_counter() + 0.88

    # Iterative deepening gives us a valid best move even if deeper search times out.
    try:
        for depth in range(1, target_depth + 1):
            if time.perf_counter() > end_time:
                break

            alpha = -10**12
            beta = 10**12
            current_best = best_move
            current_best_val = -10**12

            for mv in ordered_initial:
                if time.perf_counter() > end_time:
                    raise TimeoutError

                nme, nopp = _apply_move(me, opp, mv)
                val = -_negamax(nopp, nme, depth - 1, -beta, -alpha, end_time)

                if val > current_best_val:
                    current_best_val = val
                    current_best = mv

                if val > alpha:
                    alpha = val

            best_move = current_best

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        best_move = ordered_initial[0]

    return _move_to_str(best_move)
