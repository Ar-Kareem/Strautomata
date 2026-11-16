
import time

N = 6
NSQ = 36
ALL_MASK = (1 << NSQ) - 1

WIN_SCORE = 1_000_000
INF_SCORE = 1_000_000_000
INF_DIST = 99
EXACT_EMPTIES = 7

_DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

_BITS = [1 << i for i in range(NSQ)]
_RAYS = []
_KING_NB = []
_CENTER = []

for r in range(N):
    for c in range(N):
        rays = []
        for dr, dc in _DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            rays.append(tuple(ray))
        _RAYS.append(tuple(rays))

        nb = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    nb |= 1 << (rr * N + cc)
        _KING_NB.append(nb)

        # 48 near center, 0 at corners.
        _CENTER.append(50 - ((2 * r - 5) * (2 * r - 5) + (2 * c - 5) * (2 * c - 5)))


class _Timeout(Exception):
    pass


def _masks_from_board(board):
    my = opp = occ = 0
    try:
        flat = board.ravel()
        for i in range(NSQ):
            v = int(flat[i])
            b = _BITS[i]
            if v == 1:
                my |= b
                occ |= b
            elif v == 2:
                opp |= b
                occ |= b
            elif v == -1:
                occ |= b
        return my, opp, occ
    except Exception:
        my = opp = occ = 0
        for r in range(N):
            for c in range(N):
                v = int(board[r][c])
                i = r * N + c
                b = _BITS[i]
                if v == 1:
                    my |= b
                    occ |= b
                elif v == 2:
                    opp |= b
                    occ |= b
                elif v == -1:
                    occ |= b
        return my, opp, occ


def _reachable_mask(square, occ):
    res = 0
    bits = _BITS
    for ray in _RAYS[square]:
        for j in ray:
            b = bits[j]
            if occ & b:
                break
            res |= b
    return res


def _has_move(side_mask, occ):
    pieces = side_mask
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        if _reachable_mask(sq, occ):
            return True
    return False


def _first_legal(side_mask, occ):
    pieces = side_mask
    while pieces:
        fb = pieces & -pieces
        f = fb.bit_length() - 1
        pieces ^= fb

        tm = _reachable_mask(f, occ)
        occ_without_f = occ ^ fb
        while tm:
            tb = tm & -tm
            t = tb.bit_length() - 1
            tm ^= tb

            occ2 = occ_without_f | tb
            am = _reachable_mask(t, occ2)
            if am:
                ab = am & -am
                a = ab.bit_length() - 1
                return (f, t, a)
    return None


def _generate_moves(side_mask, occ):
    moves = []
    pieces = side_mask
    while pieces:
        fb = pieces & -pieces
        f = fb.bit_length() - 1
        pieces ^= fb

        tm = _reachable_mask(f, occ)
        occ_without_f = occ ^ fb
        while tm:
            tb = tm & -tm
            t = tb.bit_length() - 1
            tm ^= tb

            occ2 = occ_without_f | tb
            am = _reachable_mask(t, occ2)
            while am:
                ab = am & -am
                a = ab.bit_length() - 1
                am ^= ab
                moves.append((f, t, a))
    return moves


def _apply_move(my, opp, occ, move, side):
    f, t, a = move
    fb = _BITS[f]
    tb = _BITS[t]
    ab = _BITS[a]
    nocc = (occ ^ fb) | tb | ab
    if side == 1:
        return (my ^ fb) | tb, opp, nocc
    return my, (opp ^ fb) | tb, nocc


def _move_to_str(move):
    f, t, a = move
    return "%d,%d:%d,%d:%d,%d" % (
        f // N, f % N,
        t // N, t % N,
        a // N, a % N
    )


def _mobility(side_mask, occ):
    total = 0
    union = 0
    pieces = side_mask
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        r = _reachable_mask(sq, occ)
        total += r.bit_count()
        union |= r
    return total, union.bit_count()


def _adjacent_count(side_mask, occ):
    empty = ALL_MASK & ~occ
    total = 0
    pieces = side_mask
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        total += (_KING_NB[sq] & empty).bit_count()
    return total


def _center_diff(my, opp):
    score = 0
    pieces = my
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        score += _CENTER[sq]

    pieces = opp
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        score -= _CENTER[sq]
    return score


def _action_count(side_mask, occ, limit=1200):
    total = 0
    pieces = side_mask
    while pieces:
        fb = pieces & -pieces
        f = fb.bit_length() - 1
        pieces ^= fb

        tm = _reachable_mask(f, occ)
        occ_without_f = occ ^ fb
        while tm:
            tb = tm & -tm
            t = tb.bit_length() - 1
            tm ^= tb
            occ2 = occ_without_f | tb
            total += _reachable_mask(t, occ2).bit_count()
            if total >= limit:
                return limit
    return total


def _queen_distances(starts, occ):
    dist = [INF_DIST] * NSQ
    q = []

    pieces = starts
    while pieces:
        b = pieces & -pieces
        sq = b.bit_length() - 1
        pieces ^= b
        dist[sq] = 0
        q.append(sq)

    head = 0
    bits = _BITS
    while head < len(q):
        sq = q[head]
        head += 1
        nd = dist[sq] + 1
        for ray in _RAYS[sq]:
            for j in ray:
                b = bits[j]
                if occ & b:
                    break
                if dist[j] == INF_DIST:
                    dist[j] = nd
                    q.append(j)
    return dist


def _territory_eval(my, opp, occ):
    d1 = _queen_distances(my, occ)
    d2 = _queen_distances(opp, occ)
    empty = ALL_MASK & ~occ
    score = 0

    for i, b in enumerate(_BITS):
        if not (empty & b):
            continue

        a = d1[i]
        o = d2[i]

        if a < o:
            score += 100
            if o >= INF_DIST:
                score += 45
            else:
                bonus = 8 * (o - a)
                score += bonus if bonus < 48 else 48
        elif o < a:
            score -= 100
            if a >= INF_DIST:
                score -= 45
            else:
                bonus = 8 * (a - o)
                score -= bonus if bonus < 48 else 48

        if 0 < a < INF_DIST:
            score += 24 // a
        if 0 < o < INF_DIST:
            score -= 24 // o

    return score


def _component_eval(my, opp, occ):
    # Components separated by arrows only: if a chamber has amazons of one side,
    # its empty squares are effectively secured.
    arrows = occ & ~(my | opp)
    free = ALL_MASK & ~arrows
    rem = free
    score = 0

    while rem:
        start = rem & -rem
        rem ^= start
        stack = start
        has_my = False
        has_opp = False
        empty_count = 0

        while stack:
            b = stack & -stack
            stack ^= b
            sq = b.bit_length() - 1

            if my & b:
                has_my = True
            elif opp & b:
                has_opp = True
            else:
                empty_count += 1

            nb = _KING_NB[sq] & rem
            if nb:
                rem ^= nb
                stack |= nb

        if has_my and not has_opp:
            score += empty_count
        elif has_opp and not has_my:
            score -= empty_count

    return score


def _light_eval(my, opp, occ):
    mt, mu = _mobility(my, occ)
    ot, ou = _mobility(opp, occ)

    if mt == 0:
        return -WIN_SCORE
    if ot == 0:
        return WIN_SCORE

    return (
        45 * (mu - ou)
        + 13 * (mt - ot)
        + 20 * (_adjacent_count(my, occ) - _adjacent_count(opp, occ))
        + 3 * _center_diff(my, opp)
    )


def _static_eval(my, opp, occ):
    mt, mu = _mobility(my, occ)
    ot, ou = _mobility(opp, occ)
    empties = NSQ - occ.bit_count()

    if mt == 0:
        return -WIN_SCORE + empties
    if ot == 0:
        return WIN_SCORE - empties

    score = _territory_eval(my, opp, occ)
    score += 75 * _component_eval(my, opp, occ)
    score += 30 * (mu - ou)
    score += 10 * (mt - ot)
    score += 18 * (_adjacent_count(my, occ) - _adjacent_count(opp, occ))

    cd = _center_diff(my, opp)
    score += 3 * cd if empties > 18 else cd

    if empties <= 16:
        ac1 = _action_count(my, occ)
        ac2 = _action_count(opp, occ)
        score += (4 if empties <= 9 else 2) * (ac1 - ac2)

    return score


def _node_limit(depth, empties):
    if empties <= 12:
        if depth <= 1:
            return 34
        if depth == 2:
            return 20
        if depth == 3:
            return 12
        return 8

    if depth <= 1:
        return 22
    if depth == 2:
        return 13
    if depth == 3:
        return 9
    return 6


def _root_limit(depth, total, empties):
    if total <= 0:
        return 0
    if empties <= EXACT_EMPTIES + 1 or total <= 36:
        return total
    if depth == 1:
        return min(total, 56)
    if depth == 2:
        return min(total, 30)
    if depth == 3:
        return min(total, 16)
    if depth == 4:
        return min(total, 10)
    return min(total, 8)


def _ordered_moves(my, opp, occ, side, limit, deadline):
    side_mask = my if side == 1 else opp
    scored = []
    made = 0

    pieces = side_mask
    while pieces:
        fb = pieces & -pieces
        f = fb.bit_length() - 1
        pieces ^= fb

        tm = _reachable_mask(f, occ)
        occ_without_f = occ ^ fb

        while tm:
            tb = tm & -tm
            t = tb.bit_length() - 1
            tm ^= tb

            occ2 = occ_without_f | tb
            am = _reachable_mask(t, occ2)

            if side == 1:
                base_my = (my ^ fb) | tb
                base_opp = opp
            else:
                base_my = my
                base_opp = (opp ^ fb) | tb

            while am:
                ab = am & -am
                a = ab.bit_length() - 1
                am ^= ab

                nocc = occ2 | ab
                score = _light_eval(base_my, base_opp, nocc)
                scored.append((score, (f, t, a)))

                made += 1
                if (made & 127) == 0 and time.perf_counter() > deadline:
                    raise _Timeout()

    scored.sort(key=lambda x: x[0], reverse=(side == 1))
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [m for _, m in scored]


def _alphabeta(my, opp, occ, side, depth, alpha, beta, deadline, tt, ply):
    if time.perf_counter() > deadline:
        raise _Timeout()

    side_mask = my if side == 1 else opp
    if not _has_move(side_mask, occ):
        return (-WIN_SCORE + ply) if side == 1 else (WIN_SCORE - ply)

    empties = NSQ - occ.bit_count()
    if empties <= EXACT_EMPTIES and depth < empties:
        depth = empties

    if depth <= 0:
        return _static_eval(my, opp, occ)

    key = (my, opp, occ, side, depth)
    hit = tt.get(key)
    if hit is not None:
        return hit

    limit = None if empties <= 9 else _node_limit(depth, empties)
    moves = _ordered_moves(my, opp, occ, side, limit, deadline)

    if not moves:
        return (-WIN_SCORE + ply) if side == 1 else (WIN_SCORE - ply)

    cutoff = False

    if side == 1:
        best = -INF_SCORE
        for mv in moves:
            nmy, nopp, nocc = _apply_move(my, opp, occ, mv, 1)
            val = _alphabeta(nmy, nopp, nocc, 2, depth - 1, alpha, beta, deadline, tt, ply + 1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                cutoff = True
                break
    else:
        best = INF_SCORE
        for mv in moves:
            nmy, nopp, nocc = _apply_move(my, opp, occ, mv, 2)
            val = _alphabeta(nmy, nopp, nocc, 1, depth - 1, alpha, beta, deadline, tt, ply + 1)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                cutoff = True
                break

    if not cutoff and len(tt) < 40000:
        tt[key] = best

    return best


def _safe_fallback(board):
    try:
        my, opp, occ = _masks_from_board(board)
        mv = _first_legal(my, occ)
        if mv is not None:
            return _move_to_str(mv)
    except Exception:
        pass
    return "0,0:0,0:0,0"


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90
    best_move = None

    try:
        my, opp, occ = _masks_from_board(board)

        best_move = _first_legal(my, occ)
        if best_move is None:
            return "0,0:0,0:0,0"

        root_moves = _generate_moves(my, occ)
        if not root_moves:
            return _move_to_str(best_move)

        scored = []
        for i, mv in enumerate(root_moves):
            nmy, nopp, nocc = _apply_move(my, opp, occ, mv, 1)

            # If opponent cannot move, this is immediately winning.
            if not _has_move(nopp, nocc):
                return _move_to_str(mv)

            scored.append((_light_eval(nmy, nopp, nocc), mv))

            if (i & 63) == 0 and time.perf_counter() > deadline:
                raise _Timeout()

        scored.sort(key=lambda x: x[0], reverse=True)
        best_move = scored[0][1]

        # More expensive static ordering for the most plausible root moves.
        static_stop = min(deadline, start + 0.26)
        total = len(scored)
        if total <= 140:
            full_limit = total
        elif total <= 320:
            full_limit = 170
        else:
            full_limit = 130

        full_scored = []
        for rank, (_, mv) in enumerate(scored):
            if rank >= full_limit or time.perf_counter() > static_stop:
                break
            nmy, nopp, nocc = _apply_move(my, opp, occ, mv, 1)
            full_scored.append((_static_eval(nmy, nopp, nocc), mv))

        if full_scored:
            full_scored.sort(key=lambda x: x[0], reverse=True)
            best_move = full_scored[0][1]
            used = set(mv for _, mv in full_scored)
            root_order = [mv for _, mv in full_scored] + [mv for _, mv in scored if mv not in used]
        else:
            root_order = [mv for _, mv in scored]

        empties = NSQ - occ.bit_count()
        if empties <= EXACT_EMPTIES + 1:
            max_depth = max(1, empties)
        elif empties <= 12:
            max_depth = 6
        elif empties <= 20:
            max_depth = 5
        else:
            max_depth = 4

        tt = {}

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            count = _root_limit(depth, len(root_order), empties)
            if count <= 0:
                break

            current = list(root_order[:count])
            if best_move in current:
                current.remove(best_move)
            elif len(current) >= count and current:
                current.pop()
            current.insert(0, best_move)

            cur_scores = []
            alpha = -INF_SCORE

            for mv in current:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                nmy, nopp, nocc = _apply_move(my, opp, occ, mv, 1)
                val = _alphabeta(nmy, nopp, nocc, 2, depth, alpha, INF_SCORE, deadline, tt, 1)
                cur_scores.append((val, mv))
                if val > alpha:
                    alpha = val

            cur_scores.sort(key=lambda x: x[0], reverse=True)
            best_move = cur_scores[0][1]

            searched = set(mv for _, mv in cur_scores)
            root_order = [mv for _, mv in cur_scores] + [mv for mv in root_order if mv not in searched]

            if cur_scores[0][0] > WIN_SCORE // 2:
                break

        return _move_to_str(best_move)

    except _Timeout:
        if best_move is not None:
            return _move_to_str(best_move)
        return _safe_fallback(board)
    except Exception:
        return _safe_fallback(board)
