
import time

N = 6
SQ = 36

DIRS = (
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1)
)

ROW = [0] * SQ
COL = [0] * SQ
RAYS = [[] for _ in range(SQ)]
NEIGH = [[] for _ in range(SQ)]

for r in range(N):
    for c in range(N):
        i = r * N + c
        ROW[i] = r
        COL[i] = c

        for dr, dc in DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            RAYS[i].append(tuple(ray))

        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NEIGH[i] = tuple(ns)

CHEB = [[0] * SQ for _ in range(SQ)]
ALIGNED = [[False] * SQ for _ in range(SQ)]
CENTER = [0.0] * SQ

for i in range(SQ):
    CENTER[i] = 6.0 - (abs(ROW[i] - 2.5) + abs(COL[i] - 2.5))
    for j in range(SQ):
        dr = abs(ROW[i] - ROW[j])
        dc = abs(COL[i] - COL[j])
        CHEB[i][j] = max(dr, dc)
        ALIGNED[i][j] = (dr == 0 or dc == 0 or dr == dc)

WIN = 1000000.0
BIG = 1000000000.0
INF_D = 99

_NODES = 0
_KILLERS = [None] * 64


class _Timeout(Exception):
    pass


def policy(board) -> str:
    try:
        start = time.perf_counter()
        deadline = start + 0.90

        b = _to_flat(board)
        moves = _gen_moves(b, 1)

        if not moves:
            m = _first_legal_move(b, 1)
            return _format(m) if m is not None else "0,0:0,0:0,0"

        if len(moves) == 1:
            return _format(moves[0])

        # Exact immediate win check at root.
        for idx, m in enumerate(moves):
            if (idx & 31) == 0 and time.perf_counter() > deadline - 0.03:
                break
            _make(b, 1, m)
            wins_now = not _has_amazon_move(b, 2)
            _undo(b, 1, m)
            if wins_now:
                return _format(m)

        global _NODES, _KILLERS
        _NODES = 0
        _KILLERS = [None] * 64

        # Static ordering gives a safe initial legal move immediately.
        ordered = _sort_moves(b, 1, moves, depth=1, ply=0, limit=None)
        best = ordered[0]

        # One-ply heuristic ordering from the true side-to-move perspective.
        scored = []
        for idx, m in enumerate(ordered):
            if (idx & 7) == 0 and time.perf_counter() > deadline - 0.18:
                break
            _make(b, 1, m)
            val = -_evaluate(b, 2) + _tiny(m)
            _undo(b, 1, m)
            scored.append((val, m))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best = scored[0][1]
            done = set(m for _, m in scored)
            ordered = [m for _, m in scored] + [m for m in ordered if m not in done]

        empties = b.count(0)
        if empties <= 7:
            max_depth = empties + 1
        elif empties <= 11:
            max_depth = 6
        elif empties <= 17:
            max_depth = 5
        else:
            max_depth = 4
        max_depth = min(max_depth, empties + 1)

        for depth in range(2, max_depth + 1):
            if time.perf_counter() > deadline - 0.04:
                break
            try:
                val, mv = _search_root(b, ordered, depth, deadline)
                if mv is not None:
                    best = mv
                    if ordered and ordered[0] != best:
                        ordered = [best] + [m for m in ordered if m != best]
            except _Timeout:
                break

        return _format(best)

    except Exception:
        try:
            b = _to_flat(board)
            m = _first_legal_move(b, 1)
            return _format(m) if m is not None else "0,0:0,0:0,0"
        except Exception:
            return "0,0:0,0:0,0"


def _to_flat(board):
    try:
        flat = board.ravel()
        return [int(flat[i]) for i in range(SQ)]
    except Exception:
        return [int(board[r][c]) for r in range(N) for c in range(N)]


def _format(m):
    if m is None:
        return "0,0:0,0:0,0"
    f, t, a = m
    return f"{ROW[f]},{COL[f]}:{ROW[t]},{COL[t]}:{ROW[a]},{COL[a]}"


def _tiny(m):
    return ((m[0] * 131 + m[1] * 17 + m[2] * 7) & 255) * 0.00001


def _make(b, side, m):
    f, t, a = m
    b[f] = 0
    b[t] = side
    b[a] = -1


def _undo(b, side, m):
    f, t, a = m
    b[a] = 0
    b[t] = 0
    b[f] = side


def _has_amazon_move(b, side):
    for i, v in enumerate(b):
        if v == side:
            for ray in RAYS[i]:
                for j in ray:
                    if b[j] == 0:
                        return True
                    break
    return False


def _mobility_stats(b, side):
    total = 0
    stuck = 0
    for i, v in enumerate(b):
        if v == side:
            cnt = 0
            for ray in RAYS[i]:
                for j in ray:
                    if b[j] == 0:
                        cnt += 1
                    else:
                        break
            total += cnt
            if cnt == 0:
                stuck += 1
    return total, stuck


def _adjacent_liberties(b, side):
    s = 0
    for i, v in enumerate(b):
        if v == side:
            for j in NEIGH[i]:
                if b[j] == 0:
                    s += 1
    return s


def _arrow_count_from_to(b, f, t):
    cnt = 0
    for ray in RAYS[t]:
        for a in ray:
            if a == f or b[a] == 0:
                cnt += 1
            else:
                break
    return cnt


def _legal_move_count(b, side, cap=0):
    cnt = 0
    for f, v in enumerate(b):
        if v != side:
            continue
        for ray in RAYS[f]:
            for t in ray:
                if b[t] != 0:
                    break
                for aray in RAYS[t]:
                    for a in aray:
                        if a == f or b[a] == 0:
                            cnt += 1
                            if cap and cnt >= cap:
                                return cnt
                        else:
                            break
    return cnt


def _gen_moves(b, side):
    moves = []
    for f, v in enumerate(b):
        if v != side:
            continue
        for ray in RAYS[f]:
            for t in ray:
                if b[t] != 0:
                    break
                for aray in RAYS[t]:
                    for a in aray:
                        if a == f or b[a] == 0:
                            moves.append((f, t, a))
                        else:
                            break
    return moves


def _first_legal_move(b, side):
    for f, v in enumerate(b):
        if v != side:
            continue
        for ray in RAYS[f]:
            for t in ray:
                if b[t] != 0:
                    break
                for aray in RAYS[t]:
                    for a in aray:
                        if a == f or b[a] == 0:
                            return (f, t, a)
                        else:
                            break
    return None


def _queen_distances(b, side):
    dist = [INF_D] * SQ
    q = []
    for i, v in enumerate(b):
        if v == side:
            dist[i] = 0
            q.append(i)

    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1
        for ray in RAYS[p]:
            for j in ray:
                if b[j] != 0:
                    break
                if dist[j] == INF_D:
                    dist[j] = nd
                    q.append(j)
    return dist


def _territory_score(b, side):
    opp = 3 - side
    d_my = _queen_distances(b, side)
    d_op = _queen_distances(b, opp)

    owned = 0.0
    closeness = 0.0
    exclusive = 0.0

    for i, v in enumerate(b):
        if v != 0:
            continue
        dm = d_my[i]
        do = d_op[i]

        if dm < do:
            owned += 1.0
            closeness += 1.0 / (dm + 1.0)
            if do >= INF_D:
                exclusive += 1.0
        elif do < dm:
            owned -= 1.0
            closeness -= 1.0 / (do + 1.0)
            if dm >= INF_D:
                exclusive -= 1.0

    return 78.0 * owned + 22.0 * closeness + 28.0 * exclusive


def _component_score(b, side):
    opp = 3 - side
    seen = [False] * SQ
    score = 0.0

    for i in range(SQ):
        if seen[i] or b[i] == -1:
            continue

        stack = [i]
        seen[i] = True
        empty = 0
        own = 0
        enemy = 0

        while stack:
            p = stack.pop()
            v = b[p]
            if v == 0:
                empty += 1
            elif v == side:
                own += 1
            elif v == opp:
                enemy += 1

            for nb in NEIGH[p]:
                if not seen[nb] and b[nb] != -1:
                    seen[nb] = True
                    stack.append(nb)

        if own and not enemy:
            score += empty + 0.5 * own
        elif enemy and not own:
            score -= empty + 0.5 * enemy

    return score


def _evaluate(b, side):
    opp = 3 - side

    my_land, my_stuck = _mobility_stats(b, side)
    if my_land == 0:
        return -WIN

    op_land, op_stuck = _mobility_stats(b, opp)

    # If the opponent is already immobile and we can move, we can shoot back
    # to the vacated square and preserve the trap.
    if op_land == 0:
        return WIN * 0.45

    terr = _territory_score(b, side)
    comp = _component_score(b, side)
    adj = _adjacent_liberties(b, side) - _adjacent_liberties(b, opp)

    score = (
        terr
        + 36.0 * comp
        + 10.5 * (my_land - op_land)
        + 24.0 * (op_stuck - my_stuck)
        + 2.3 * adj
        + 1.5
    )

    empties = b.count(0)
    if empties <= 18:
        my_moves = _legal_move_count(b, side, cap=1200)
        op_moves = _legal_move_count(b, opp, cap=1200)
        score += 0.75 * (my_moves - op_moves)

    return score


def _sort_moves(b, side, moves, depth, ply, limit):
    if len(moves) <= 1:
        return moves[:]

    opp = 3 - side
    opp_positions = []
    own_positions = []
    for i, v in enumerate(b):
        if v == opp:
            opp_positions.append(i)
        elif v == side:
            own_positions.append(i)

    land_cache = {}
    killer = _KILLERS[ply] if ply < len(_KILLERS) else None

    def key(m):
        f, t, a = m
        ft = f * SQ + t
        lm = land_cache.get(ft)
        if lm is None:
            lm = _arrow_count_from_to(b, f, t)
            land_cache[ft] = lm

        s = 4.0 * lm + 0.7 * CENTER[t]

        pressure = 0.0
        for op in opp_positions:
            d = CHEB[a][op]
            if d == 1:
                pressure += 9.0
            elif d == 2:
                pressure += 4.0
            elif d == 3:
                pressure += 1.5
            if ALIGNED[a][op]:
                pressure += max(0.0, 5.0 - d)

        harm = 0.0
        for ow in own_positions:
            if ow == f:
                continue
            d = CHEB[a][ow]
            if d == 1:
                harm += 3.0
            elif d == 2:
                harm += 1.0
            if ALIGNED[a][ow]:
                harm += 0.5 * max(0.0, 3.0 - d)

        if a == f:
            s -= 2.0

        dt = CHEB[a][t]
        if dt == 1:
            s -= 0.4

        if killer is not None and m == killer:
            s += 100000.0

        return s + 2.8 * pressure - 1.2 * harm + _tiny(m)

    ordered = sorted(moves, key=key, reverse=True)
    if limit is not None and len(ordered) > limit:
        return ordered[:limit]
    return ordered


def _node_limit(depth, n, empties):
    if n <= 30:
        return n
    if empties <= 9 and n <= 180:
        return n
    if empties <= 12 and n <= 100:
        return n

    if depth <= 1:
        lim = 56
    elif depth == 2:
        lim = 36
    elif depth == 3:
        lim = 26
    else:
        lim = 18

    if empties <= 16:
        lim += 16
    if empties <= 12:
        lim += 24

    return min(n, lim)


def _ordered_candidates(b, side, depth, ply):
    moves = _gen_moves(b, side)
    n = len(moves)
    if n <= 1:
        return moves

    empties = b.count(0)

    # In small/late positions, never miss an immediate mate.
    if n <= 140 or empties <= 12:
        opp = 3 - side
        for m in moves:
            _make(b, side, m)
            wins = not _has_amazon_move(b, opp)
            _undo(b, side, m)
            if wins:
                return [m]

    limit = _node_limit(depth, n, empties)
    return _sort_moves(b, side, moves, depth, ply, limit)


def _root_limit(n, depth, empties):
    if n <= 1:
        return n
    if depth <= 1:
        return n
    if empties <= 8 and n <= 220:
        return n
    if depth == 2:
        return n if n <= 260 else 260
    if depth == 3:
        return min(n, 120 if empties <= 16 else 90)
    if depth == 4:
        return min(n, 80 if empties <= 14 else 55)
    return min(n, 45)


def _search_root(b, ordered, depth, deadline):
    alpha = -BIG
    beta = BIG
    best_val = -BIG
    best_move = None

    lim = _root_limit(len(ordered), depth, b.count(0))
    root_moves = ordered[:lim]

    for idx, m in enumerate(root_moves):
        if (idx & 7) == 0 and time.perf_counter() > deadline:
            raise _Timeout

        _make(b, 1, m)
        val = -_negamax(b, 2, depth - 1, -beta, -alpha, deadline, 1)
        _undo(b, 1, m)

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val

    return best_val, best_move


def _negamax(b, side, depth, alpha, beta, deadline, ply):
    global _NODES
    _NODES += 1
    if (_NODES & 63) == 0 and time.perf_counter() > deadline:
        raise _Timeout

    if depth <= 0:
        return _evaluate(b, side)

    if not _has_amazon_move(b, side):
        return -WIN + ply

    opp = 3 - side

    # If opponent currently has no mobility and we do, we can preserve the trap.
    if not _has_amazon_move(b, opp):
        return WIN - ply

    moves = _ordered_candidates(b, side, depth, ply)
    if not moves:
        return -WIN + ply

    best = -BIG

    for m in moves:
        _make(b, side, m)
        val = -_negamax(b, opp, depth - 1, -beta, -alpha, deadline, ply + 1)
        _undo(b, side, m)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            if ply < len(_KILLERS):
                _KILLERS[ply] = m
            break

    return best
