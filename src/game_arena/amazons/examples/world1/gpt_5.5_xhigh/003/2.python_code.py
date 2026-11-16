
import time

N = 6
NSQ = 36
MOVE_F = NSQ * NSQ   # 1296
MOVE_T = NSQ         # 36

WIN = 1_000_000_000
POS_INF = 2 * WIN
NEG_INF = -2 * WIN
INF = 99
TIME_LIMIT = 0.90

BITS = tuple(1 << i for i in range(NSQ))
ALL_MASK = (1 << NSQ) - 1
COORD = tuple(f"{i // N},{i % N}" for i in range(NSQ))

DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

RAYS = []
NEIGH = []
NEIGH_MASK = []
CELL_WEIGHT = []

for r in range(N):
    for c in range(N):
        rays_for_sq = []
        for dr, dc in DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            rays_for_sq.append(tuple(ray))
        RAYS.append(tuple(rays_for_sq))

        neigh = []
        nmask = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    sq = rr * N + cc
                    neigh.append(sq)
                    nmask |= BITS[sq]
        NEIGH.append(tuple(neigh))
        NEIGH_MASK.append(nmask)

        CELL_WEIGHT.append(int(8 - (abs(r - 2.5) + abs(c - 2.5))))

RAYS = tuple(RAYS)
NEIGH = tuple(NEIGH)
NEIGH_MASK = tuple(NEIGH_MASK)
CELL_WEIGHT = tuple(CELL_WEIGHT)

BETWEEN_MASK = [[-1] * NSQ for _ in range(NSQ)]
for i in range(NSQ):
    r1, c1 = divmod(i, N)
    for j in range(NSQ):
        if i == j:
            continue
        r2, c2 = divmod(j, N)
        dr, dc = r2 - r1, c2 - c1
        if dr == 0:
            sr, sc = 0, 1 if dc > 0 else -1
        elif dc == 0:
            sr, sc = 1 if dr > 0 else -1, 0
        elif abs(dr) == abs(dc):
            sr, sc = 1 if dr > 0 else -1, 1 if dc > 0 else -1
        else:
            continue

        mask = 0
        rr, cc = r1 + sr, c1 + sc
        while rr != r2 or cc != c2:
            mask |= BITS[rr * N + cc]
            rr += sr
            cc += sc
        BETWEEN_MASK[i][j] = mask
BETWEEN_MASK = tuple(tuple(row) for row in BETWEEN_MASK)

NEAR_SCORE = []
for a in range(NSQ):
    ar, ac = divmod(a, N)
    row = []
    for b in range(NSQ):
        br, bc = divmod(b, N)
        d = max(abs(ar - br), abs(ac - bc))
        row.append(max(0, 5 - d))
    NEAR_SCORE.append(tuple(row))
NEAR_SCORE = tuple(NEAR_SCORE)

_EVAL_CACHE = {}
_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _board_to_masks(board):
    my = opp = block = 0
    idx = 0
    bits = BITS
    for r in range(N):
        row = board[r]
        for c in range(N):
            v = int(row[c])
            if v == 1:
                my |= bits[idx]
            elif v == 2:
                opp |= bits[idx]
            elif v == -1:
                block |= bits[idx]
            idx += 1
    return my, opp, block


def _move_to_string(m):
    f = m // MOVE_F
    rem = m - f * MOVE_F
    t = rem // MOVE_T
    a = rem - t * MOVE_T
    return COORD[f] + ":" + COORD[t] + ":" + COORD[a]


def _apply_move(my, opp, block, m):
    f = m // MOVE_F
    rem = m - f * MOVE_F
    t = rem // MOVE_T
    a = rem - t * MOVE_T

    new_current = (my ^ BITS[f]) | BITS[t]
    new_block = block | BITS[a]

    # Swap perspective: opponent becomes side to move.
    return opp, new_current, new_block


def _reach_count_from(sq, occ):
    total = 0
    bits = BITS
    for ray in RAYS[sq]:
        for d in ray:
            if occ & bits[d]:
                break
            total += 1
    return total


def _queen_mobility(mask, occ):
    total = 0
    bits = BITS
    rays = RAYS
    m = mask
    while m:
        lb = m & -m
        sq = lb.bit_length() - 1
        m ^= lb
        for ray in rays[sq]:
            for d in ray:
                if occ & bits[d]:
                    break
                total += 1
    return total


def _generate_moves(my, opp, block):
    occ = my | opp | block
    moves = []
    append = moves.append
    bits = BITS
    rays = RAYS

    m = my
    while m:
        fb = m & -m
        f = fb.bit_length() - 1
        m ^= fb

        base_f = f * MOVE_F
        occ_without_from = occ ^ fb

        for ray in rays[f]:
            for t in ray:
                tb = bits[t]
                if occ & tb:
                    break

                occ_after_move = occ_without_from | tb
                base = base_f + t * MOVE_T

                for aray in rays[t]:
                    for a in aray:
                        if occ_after_move & bits[a]:
                            break
                        append(base + a)

    return moves


def _queen_dist(starts, occ):
    dist = [INF] * NSQ
    q = []
    m = starts
    while m:
        lb = m & -m
        sq = lb.bit_length() - 1
        m ^= lb
        dist[sq] = 0
        q.append(sq)

    bits = BITS
    rays = RAYS
    head = 0
    while head < len(q):
        sq = q[head]
        head += 1
        nd = dist[sq] + 1
        for ray in rays[sq]:
            for d in ray:
                if occ & bits[d]:
                    break
                if dist[d] == INF:
                    dist[d] = nd
                    q.append(d)
    return dist


def _king_dist(starts, occ):
    dist = [INF] * NSQ
    q = []
    m = starts
    while m:
        lb = m & -m
        sq = lb.bit_length() - 1
        m ^= lb
        dist[sq] = 0
        q.append(sq)

    bits = BITS
    head = 0
    while head < len(q):
        sq = q[head]
        head += 1
        nd = dist[sq] + 1
        for d in NEIGH[sq]:
            if occ & bits[d]:
                continue
            if dist[d] == INF:
                dist[d] = nd
                q.append(d)
    return dist


def _neighbor_liberties(mask, empty):
    cover = 0
    m = mask
    while m:
        lb = m & -m
        sq = lb.bit_length() - 1
        m ^= lb
        cover |= NEIGH_MASK[sq]
    return (cover & empty).bit_count()


def _amazon_position(mask):
    total = 0
    m = mask
    weights = CELL_WEIGHT
    while m:
        lb = m & -m
        sq = lb.bit_length() - 1
        m ^= lb
        total += weights[sq]
    return total


def _full_move_count(my, opp, block, cap=4000):
    occ = my | opp | block
    total = 0
    bits = BITS
    rays = RAYS

    m = my
    while m:
        fb = m & -m
        f = fb.bit_length() - 1
        m ^= fb

        occ_without_from = occ ^ fb
        for ray in rays[f]:
            for t in ray:
                tb = bits[t]
                if occ & tb:
                    break
                occ_after_move = occ_without_from | tb
                total += _reach_count_from(t, occ_after_move)
                if total >= cap:
                    return cap
    return total


def _evaluate(my, opp, block):
    key = (my, opp, block)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    occ = my | opp | block
    my_mob = _queen_mobility(my, occ)
    opp_mob = _queen_mobility(opp, occ)

    if my_mob == 0:
        score = -WIN
    elif opp_mob == 0:
        score = WIN
    else:
        empty = ALL_MASK & ~occ
        empties = empty.bit_count()

        md = _queen_dist(my, occ)
        od = _queen_dist(opp, occ)

        qterr = 0
        reach_adv = 0
        ties = 0

        e = empty
        while e:
            lb = e & -e
            sq = lb.bit_length() - 1
            e ^= lb

            mds = md[sq]
            ods = od[sq]
            w = 10 + CELL_WEIGHT[sq]

            if mds < ods:
                qterr += w
                reach_adv += 6 if ods >= INF else min(6, ods - mds)
            elif ods < mds:
                qterr -= w
                reach_adv -= 6 if mds >= INF else min(6, mds - ods)
            elif mds < INF:
                ties |= lb

        kterr = 0
        if ties:
            mk = _king_dist(my, occ)
            ok = _king_dist(opp, occ)
            e = ties
            while e:
                lb = e & -e
                sq = lb.bit_length() - 1
                e ^= lb
                w = 4 + CELL_WEIGHT[sq] // 2
                if mk[sq] < ok[sq]:
                    kterr += w
                elif ok[sq] < mk[sq]:
                    kterr -= w

        lib = _neighbor_liberties(my, empty) - _neighbor_liberties(opp, empty)
        pos = _amazon_position(my) - _amazon_position(opp)

        terr_weight = 5 if empties <= 14 else 4
        mob_weight = 9 if empties >= 16 else 6

        score = (
            terr_weight * qterr
            + 2 * kterr
            + 3 * reach_adv
            + mob_weight * (my_mob - opp_mob)
            + 4 * lib
            + 2 * pos
            + 1
        )

        if empties <= 12:
            full_diff = _full_move_count(my, opp, block) - _full_move_count(opp, my, block)
            score += full_diff

    if len(_EVAL_CACHE) < 70000:
        _EVAL_CACHE[key] = score
    return score


def _fast_order_score(my, opp, block, m):
    f = m // MOVE_F
    rem = m - f * MOVE_F
    t = rem // MOVE_T
    a = rem - t * MOVE_T

    bits = BITS
    fb = bits[f]
    tb = bits[t]
    ab = bits[a]

    occ0 = my | opp | block
    pre_arrow_occ = (occ0 ^ fb) | tb
    occ_after = pre_arrow_occ | ab
    cur = (my ^ fb) | tb

    land = _reach_count_from(t, occ_after)

    near_row = NEAR_SCORE[a]
    near_opp = 0
    impact = 0
    oo = opp
    between = BETWEEN_MASK
    while oo:
        lb = oo & -oo
        osq = lb.bit_length() - 1
        oo ^= lb
        near_opp += near_row[osq]
        bm = between[osq][a]
        if bm >= 0 and (pre_arrow_occ & bm) == 0:
            impact += 1

    near_my = 0
    cm = cur
    while cm:
        lb = cm & -cm
        csq = lb.bit_length() - 1
        cm ^= lb
        near_my += near_row[csq]

    return (
        10 * land
        + 16 * impact
        + 5 * near_opp
        - 3 * near_my
        + 2 * CELL_WEIGHT[t]
        + CELL_WEIGHT[a]
    )


def _medium_order_score(my, opp, block, m):
    base = _fast_order_score(my, opp, block, m)

    f = m // MOVE_F
    rem = m - f * MOVE_F
    t = rem // MOVE_T
    a = rem - t * MOVE_T

    cur = (my ^ BITS[f]) | BITS[t]
    nb = block | BITS[a]
    occ = cur | opp | nb

    opp_mob = _queen_mobility(opp, occ)
    if opp_mob == 0:
        return WIN + base

    my_mob = _queen_mobility(cur, occ)
    return base + 6 * (my_mob - opp_mob)


def _child_limit(depth, n_moves, empties):
    if n_moves <= 24 or empties <= 6:
        return n_moves
    if empties <= 9:
        base = 70
    elif depth >= 5:
        base = 14
    elif depth == 4:
        base = 20
    elif depth == 3:
        base = 28
    elif depth == 2:
        base = 38
    else:
        base = 50
    return n_moves if n_moves < base else base


def _ordered_limited_moves(my, opp, block, depth):
    moves = _generate_moves(my, opp, block)
    n = len(moves)
    if n <= 1:
        return moves

    empties = (ALL_MASK & ~(my | opp | block)).bit_count()
    limit = _child_limit(depth, n, empties)

    if limit < n:
        scored = []
        for i, m in enumerate(moves):
            if (i & 127) == 0 and time.perf_counter() > _DEADLINE:
                raise _SearchTimeout
            scored.append((_fast_order_score(my, opp, block, m), m))
        scored.sort(reverse=True)
        moves = [m for _, m in scored[:limit]]

    scored = []
    for i, m in enumerate(moves):
        if (i & 31) == 0 and time.perf_counter() > _DEADLINE:
            raise _SearchTimeout
        scored.append((_medium_order_score(my, opp, block, m), m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(my, opp, block, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout

    if depth <= 0:
        return _evaluate(my, opp, block)

    key = (my, opp, block)
    entry = _TT.get(key)
    if entry is not None and entry[0] >= depth:
        val, flag = entry[1], entry[2]
        if flag == 0:
            return val
        if flag == 1:
            alpha = max(alpha, val)
        else:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    occ = my | opp | block
    my_mob = _queen_mobility(my, occ)
    if my_mob == 0:
        return -WIN

    opp_mob = _queen_mobility(opp, occ)
    if opp_mob == 0:
        return WIN

    alpha_orig = alpha
    beta_orig = beta

    best = NEG_INF
    moves = _ordered_limited_moves(my, opp, block, depth)

    if not moves:
        return -WIN

    for m in moves:
        nmy, nopp, nb = _apply_move(my, opp, block, m)
        val = -_negamax(nmy, nopp, nb, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = 2  # upper bound
    elif best >= beta_orig:
        flag = 1  # lower bound
    else:
        flag = 0  # exact inside this selective search

    if len(_TT) < 120000:
        _TT[key] = (depth, best, flag)

    return best


def _root_limit(depth, n_moves, empties):
    if n_moves <= 50 or empties <= 7:
        return n_moves
    if depth == 2:
        if n_moves > 700:
            return 70
        if n_moves > 300:
            return 100
        return min(n_moves, 130)
    if depth == 3:
        if n_moves > 700:
            return 35
        if n_moves > 300:
            return 55
        return min(n_moves, 80)
    if depth == 4:
        return min(n_moves, 45 if n_moves > 300 else 60)
    return min(n_moves, 28)


def _max_depth(n_moves, empties):
    if empties <= 6:
        return empties + 1
    if n_moves <= 10:
        return 10
    if n_moves <= 25:
        return 8
    if n_moves <= 60:
        return 6
    if n_moves <= 180:
        return 5
    if n_moves <= 500:
        return 4
    return 3


def policy(board) -> str:
    global _DEADLINE, _NODES

    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODES = 0
    _TT.clear()

    if len(_EVAL_CACHE) > 70000:
        _EVAL_CACHE.clear()

    my, opp, block = _board_to_masks(board)
    moves = _generate_moves(my, opp, block)

    # The environment should not call us here, but return a syntactically valid
    # string if the position is terminal.
    if not moves:
        return "0,0:0,0:0,0"

    if len(moves) == 1:
        return _move_to_string(moves[0])

    # Cheap ordering gives a decent legal fallback immediately.
    try:
        moves.sort(key=lambda mv: _fast_order_score(my, opp, block, mv), reverse=True)
    except Exception:
        pass

    best_move = moves[0]
    best_score = NEG_INF

    try:
        if time.perf_counter() > _DEADLINE:
            return _move_to_string(best_move)

        # Static root evaluation of every move, while time allows.
        scored = []
        for i, m in enumerate(moves):
            if (i & 7) == 0 and time.perf_counter() > _DEADLINE:
                raise _SearchTimeout

            nmy, nopp, nb = _apply_move(my, opp, block, m)
            s = -_evaluate(nmy, nopp, nb)
            scored.append((s, m))

            if s > best_score:
                best_score = s
                best_move = m

            # Immediate terminal win.
            if s > WIN // 2:
                return _move_to_string(m)

        scored.sort(reverse=True)
        root_order = [m for _, m in scored]
        root_scores = {m: s for s, m in scored}

        if root_order:
            best_move = root_order[0]
            best_score = scored[0][0]

        empties = (ALL_MASK & ~(my | opp | block)).bit_count()
        max_depth = _max_depth(len(root_order), empties)

        # Iterative-deepening alpha-beta. If interrupted, the previous completed
        # root decision is retained.
        for depth in range(2, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                raise _SearchTimeout

            limit = _root_limit(depth, len(root_order), empties)
            considered = root_order[:limit]
            if not considered:
                break

            alpha = NEG_INF
            beta = POS_INF
            layer = []

            for i, m in enumerate(considered):
                if (i & 3) == 0 and time.perf_counter() > _DEADLINE:
                    raise _SearchTimeout

                nmy, nopp, nb = _apply_move(my, opp, block, m)
                val = -_negamax(nmy, nopp, nb, depth - 1, -beta, -alpha)
                layer.append((val, m))

                if val > alpha:
                    alpha = val

            if not layer:
                continue

            layer.sort(reverse=True)
            for val, m in layer:
                root_scores[m] = val

            layer_moves = [m for _, m in layer]
            rest = root_order[limit:]
            rest.sort(key=lambda mv: root_scores.get(mv, NEG_INF), reverse=True)

            # If every searched candidate is a proven disaster, try the best
            # still-unsearched static move instead of resigning into it.
            if layer[0][0] < -WIN // 2 and rest:
                root_order = rest + layer_moves
                best_move = rest[0]
                best_score = root_scores.get(best_move, best_score)
            else:
                root_order = layer_moves + rest
                best_move = layer[0][1]
                best_score = layer[0][0]

    except _SearchTimeout:
        pass
    except Exception:
        # Last-resort robustness: best_move is always from generated legal moves.
        pass

    return _move_to_string(best_move)
