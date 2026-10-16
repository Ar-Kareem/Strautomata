
import time
import heapq
import numpy as np

N = 6
WIN = 10_000_000
INF = 1_000_000_000

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

RAYS = []
ADJ = []
for i in range(36):
    r, c = divmod(i, 6)
    sq_rays = []
    for dr, dc in DIRS:
        ray = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6:
            ray.append(nr * 6 + nc)
            nr += dr
            nc += dc
        sq_rays.append(ray)
    RAYS.append(sq_rays)
    ADJ.append([ray[0] for ray in sq_rays if ray])

CENTER = [
    10 - (abs(2 * (i // 6) - 5) + abs(2 * (i % 6) - 5))
    for i in range(36)
]
CHEB = [
    [max(abs(i // 6 - j // 6), abs(i % 6 - j % 6)) for j in range(36)]
    for i in range(36)
]


class SearchTimeout(Exception):
    pass


def _move_to_str(m):
    fr, to, ar = m
    return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"


def _do_move(b, m, side):
    fr, to, ar = m
    b[fr] = 0
    b[to] = side
    b[ar] = -1


def _undo_move(b, m, side):
    fr, to, ar = m
    b[ar] = 0
    b[to] = 0
    b[fr] = side


def _has_move(b, side):
    for fr, v in enumerate(b):
        if v == side:
            for ray in RAYS[fr]:
                if ray and b[ray[0]] == 0:
                    return True
    return False


def _gen_moves(b, side):
    moves = []
    rays = RAYS
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in rays[fr]:
            for to in ray:
                if b[to] != 0:
                    break

                # Arrow is shot after fr is vacated, so fr is treated as empty.
                for aray in rays[to]:
                    for ar in aray:
                        if b[ar] != 0 and ar != fr:
                            break
                        moves.append((fr, to, ar))
    return moves


def _mobility_count(b, side):
    cnt = 0
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in RAYS[fr]:
            for q in ray:
                if b[q] != 0:
                    break
                cnt += 1
    return cnt


def _adjacent_count(b, side):
    cnt = 0
    for p, v in enumerate(b):
        if v == side:
            for q in ADJ[p]:
                if b[q] == 0:
                    cnt += 1
    return cnt


def _full_move_count(b, side, cap=2000):
    cnt = 0
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in RAYS[fr]:
            for to in ray:
                if b[to] != 0:
                    break
                for aray in RAYS[to]:
                    for ar in aray:
                        if b[ar] != 0 and ar != fr:
                            break
                        cnt += 1
                        if cnt >= cap:
                            return cnt
    return cnt


def _ray_count_after_vacating(b, pos, vacated):
    cnt = 0
    for ray in RAYS[pos]:
        for q in ray:
            if b[q] != 0 and q != vacated:
                break
            cnt += 1
    return cnt


def _center_diff(b, side):
    other = 3 - side
    s = 0
    for i, v in enumerate(b):
        if v == side:
            s += CENTER[i]
        elif v == other:
            s -= CENTER[i]
    return s


def _quick_evaluate(b, side):
    other = 3 - side
    ms = _mobility_count(b, side)
    mo = _mobility_count(b, other)

    if ms == 0:
        return -WIN // 2
    if mo == 0:
        return WIN // 2

    loc = _adjacent_count(b, side) - _adjacent_count(b, other)
    cd = _center_diff(b, side)
    empties = b.count(0)

    center_weight = 2 if empties > 18 else 1
    return 75 * (ms - mo) + 18 * loc + center_weight * cd


def _queen_distances(b, side):
    dist = [99] * 36
    queue = []

    for i, v in enumerate(b):
        if v == side:
            dist[i] = 0
            queue.append(i)

    head = 0
    while head < len(queue):
        p = queue[head]
        head += 1
        nd = dist[p] + 1

        for ray in RAYS[p]:
            for q in ray:
                if b[q] != 0:
                    break
                if dist[q] == 99:
                    dist[q] = nd
                    queue.append(q)
                # Continue through already-seen empty squares.
    return dist


def _evaluate(b, side):
    other = 3 - side

    ms = _mobility_count(b, side)
    mo = _mobility_count(b, other)

    if ms == 0:
        return -WIN // 2
    if mo == 0:
        return WIN // 2

    ds = _queen_distances(b, side)
    do = _queen_distances(b, other)

    territory = 0
    reach_diff = 0

    for i, v in enumerate(b):
        if v != 0:
            continue

        a = ds[i]
        o = do[i]

        if a < 99:
            reach_diff += 1
        if o < 99:
            reach_diff -= 1

        if a < o:
            if o >= 99:
                territory += 6
            else:
                territory += 3 + min(4, o - a)
        elif o < a:
            if a >= 99:
                territory -= 6
            else:
                territory -= 3 + min(4, a - o)
        elif a < 99:
            # Equal-distance squares are slightly better for the player to move.
            territory += 1

    loc = _adjacent_count(b, side) - _adjacent_count(b, other)
    cd = _center_diff(b, side)
    empties = b.count(0)

    val = (
        70 * (ms - mo)
        + 35 * territory
        + 8 * reach_diff
        + 14 * loc
        + (2 if empties > 18 else 1) * cd
    )

    if empties <= 18:
        val += 30 * (ms - mo)

    if empties <= 14:
        f_side = _full_move_count(b, side, 1600)
        f_opp = _full_move_count(b, other, 1600)
        val += (5 if empties > 8 else 9) * (f_side - f_opp)

    return int(val)


def _light_move_score(b, m, side):
    fr, to, ar = m
    other = 3 - side

    # Prefer mobile landing squares and arrows that attack opponent space.
    score = 5 * _ray_count_after_vacating(b, to, fr) + 2 * CENTER[to]

    for i, v in enumerate(b):
        if v == other:
            d = CHEB[ar][i]
            if d < 5:
                score += 7 * (5 - d)
        elif v == side and i != fr:
            d = CHEB[ar][i]
            if d < 4:
                score -= 3 * (4 - d)

    # Avoid shooting too close to the landing amazon unless tactically useful.
    d_to = CHEB[ar][to]
    if d_to < 4:
        score -= 2 * (4 - d_to)

    return score


def _candidate_limit(depth, n, empties):
    if n <= 0:
        return 0

    if empties <= 10:
        if n <= 260:
            return n
        if depth <= 1:
            return min(n, 180)
        if depth == 2:
            return min(n, 90)
        return min(n, 55)

    if empties <= 16:
        if depth <= 1:
            return min(n, 160)
        if depth == 2:
            return min(n, 70)
        if depth == 3:
            return min(n, 40)
        return min(n, 26)

    if depth <= 1:
        return min(n, 115)
    if depth == 2:
        return min(n, 48)
    if depth == 3:
        return min(n, 28)
    return min(n, 18)


def _ordered_limited_moves(b, side, depth, deadline):
    if time.perf_counter() > deadline:
        raise SearchTimeout()

    moves = _gen_moves(b, side)
    if not moves:
        return []

    empties = b.count(0)
    limit = _candidate_limit(depth, len(moves), empties)

    if len(moves) > limit:
        mult = 4 if depth <= 1 else 3
        prelimit = min(len(moves), max(limit * mult, limit + 20))
        light = heapq.nlargest(
            prelimit,
            ((_light_move_score(b, m, side), m) for m in moves),
            key=lambda x: x[0],
        )
        candidates = [m for _, m in light]
    else:
        candidates = moves

    other = 3 - side
    scored = []

    for k, m in enumerate(candidates):
        if (k & 31) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout()

        _do_move(b, m, side)
        try:
            if not _has_move(b, other):
                s = WIN
            else:
                s = -_quick_evaluate(b, other)
        finally:
            _undo_move(b, m, side)

        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]


def _negamax(b, side, depth, alpha, beta, deadline, ply):
    if time.perf_counter() > deadline:
        raise SearchTimeout()

    if not _has_move(b, side):
        return -WIN + ply

    if depth <= 0:
        return _evaluate(b, side)

    moves = _ordered_limited_moves(b, side, depth, deadline)
    if not moves:
        return -WIN + ply

    other = 3 - side
    best = -INF

    for k, m in enumerate(moves):
        if (k & 15) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout()

        _do_move(b, m, side)
        try:
            if not _has_move(b, other):
                val = WIN - ply - 1
            else:
                val = -_negamax(b, other, depth - 1, -beta, -alpha, deadline, ply + 1)
        finally:
            _undo_move(b, m, side)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def _root_limit(total_depth, n, empties):
    if empties <= 12:
        table = {2: 150, 3: 70, 4: 36, 5: 22}
        return min(n, table.get(total_depth, 14))
    if empties <= 20:
        table = {2: 120, 3: 50, 4: 24, 5: 14}
        return min(n, table.get(total_depth, 10))
    table = {2: 90, 3: 34, 4: 16}
    return min(n, table.get(total_depth, 10))


def _policy_impl(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.88

    flat = np.asarray(board).reshape(36)
    b = [int(flat[i]) for i in range(36)]

    root_moves = _gen_moves(b, 1)
    if not root_moves:
        return "0,0:0,0:0,0"

    best_move = root_moves[0]
    if len(root_moves) == 1:
        return _move_to_str(best_move)

    # First pass: cheap tactical/static ordering over all legal moves.
    scored = []
    for m in root_moves:
        _do_move(b, m, 1)
        try:
            win_now = not _has_move(b, 2)
            if win_now:
                s = WIN
            else:
                s = -_quick_evaluate(b, 2)
        finally:
            _undo_move(b, m, 1)

        if win_now:
            return _move_to_str(m)

        s += _light_move_score(b, m, 1) // 4
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_move = scored[0][1]

    empties = b.count(0)

    # Stronger static evaluation for the best-looking root moves.
    full_scored = []
    full_n = min(len(scored), 180 if empties > 18 else 260)
    full_stop = start + (0.30 if empties > 18 else 0.34)

    for old_s, m in scored[:full_n]:
        if time.perf_counter() > full_stop or time.perf_counter() > deadline - 0.12:
            break

        _do_move(b, m, 1)
        try:
            if not _has_move(b, 2):
                s = WIN
            else:
                s = -_evaluate(b, 2)
        finally:
            _undo_move(b, m, 1)

        full_scored.append((s, m))

    if full_scored:
        full_scored.sort(key=lambda x: x[0], reverse=True)
        seen = set()
        root_order = []
        for _, m in full_scored:
            if m not in seen:
                seen.add(m)
                root_order.append(m)
        for _, m in scored:
            if m not in seen:
                seen.add(m)
                root_order.append(m)
        best_move = root_order[0]
    else:
        root_order = [m for _, m in scored]

    if time.perf_counter() > deadline - 0.08:
        return _move_to_str(best_move)

    if empties <= 8:
        depth_plan = (2, 3, 4, 5, 6, 7)
    elif empties <= 14:
        depth_plan = (2, 3, 4, 5)
    else:
        depth_plan = (2, 3, 4)

    # Iterative selective alpha-beta search.
    for total_depth in depth_plan:
        if time.perf_counter() > deadline - 0.06:
            break

        rlim = _root_limit(total_depth, len(root_order), empties)
        current = []

        try:
            for m in root_order[:rlim]:
                if time.perf_counter() > deadline:
                    raise SearchTimeout()

                _do_move(b, m, 1)
                try:
                    if not _has_move(b, 2):
                        val = WIN - 1
                    else:
                        val = -_negamax(b, 2, total_depth - 1, -INF, INF, deadline, 1)
                finally:
                    _undo_move(b, m, 1)

                current.append((val, m))

            if current:
                current.sort(key=lambda x: x[0], reverse=True)
                best_move = current[0][1]

                # Use this depth's result as move ordering for the next depth.
                seen = set()
                new_order = []
                for _, m in current:
                    if m not in seen:
                        seen.add(m)
                        new_order.append(m)
                for m in root_order:
                    if m not in seen:
                        new_order.append(m)
                root_order = new_order

        except SearchTimeout:
            break

    return _move_to_str(best_move)


def policy(board) -> str:
    try:
        return _policy_impl(board)
    except Exception:
        # Robust fallback: regenerate and return the first legal move.
        try:
            flat = np.asarray(board).reshape(36)
            b = [int(flat[i]) for i in range(36)]
            moves = _gen_moves(b, 1)
            if moves:
                return _move_to_str(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
