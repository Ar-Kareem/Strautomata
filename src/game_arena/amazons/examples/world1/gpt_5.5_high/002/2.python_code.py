
import time

N = 6
DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)
INF = 99
WIN = 1000000


class SearchTimeout(Exception):
    pass


def policy(board) -> str:
    """
    Return a legal Amazons move on a 6x6 board.

    The input board marks our amazons as 1, opponent amazons as 2,
    arrows as -1, and empty squares as 0.
    """
    b = [[int(board[r][c]) for c in range(N)] for r in range(N)]
    deadline = time.perf_counter() + 0.90

    moves = _generate_moves(b)
    if not moves:
        # The environment should not call us in terminal states.
        return "0,0:0,0:0,0"

    best = moves[0]

    try:
        ordered = _order_moves(
            b,
            moves,
            limit=None,
            strong=(len(moves) <= 220),
            deadline=deadline,
        )
        if ordered:
            best = ordered[0]

        if len(ordered) == 1:
            return _move_to_str(best)

        # Iterative deepening. Early depths use more root moves; deeper searches
        # become selective so the policy stays inside the time limit.
        for depth in range(1, 11):
            _check_time(deadline)

            root_cap = _root_cap(depth, len(ordered))
            root_moves = ordered[:root_cap]

            # Keep the previous principal variation first.
            if best in root_moves:
                root_moves.remove(best)
                root_moves.insert(0, best)
            else:
                root_moves = [best] + root_moves[:-1]

            alpha = -2 * WIN
            beta = 2 * WIN
            local_best = best
            local_score = -2 * WIN
            scored = []

            for mv in root_moves:
                _check_time(deadline)
                child = _apply_move_swap(b, mv)
                val = -_negamax(child, depth - 1, -beta, -alpha, deadline, 1)
                scored.append((val, mv))

                if val > local_score:
                    local_score = val
                    local_best = mv
                if val > alpha:
                    alpha = val

                # A forced immediate/near-immediate win is enough.
                if val > WIN // 2:
                    return _move_to_str(mv)

            best = local_best

            # Use the completed iteration to improve ordering next iteration.
            scored.sort(key=lambda x: x[0], reverse=True)
            searched = [m for _, m in scored]
            used = set(searched)
            ordered = searched + [m for m in ordered if m not in used]

    except SearchTimeout:
        pass
    except Exception:
        # Safety: always return the best legal move found so far.
        pass

    return _move_to_str(best)


def _check_time(deadline):
    if time.perf_counter() >= deadline:
        raise SearchTimeout()


def _move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def _root_cap(depth, n):
    if depth <= 1:
        return min(n, 220)
    if depth == 2:
        return min(n, 70)
    if depth == 3:
        return min(n, 38)
    if depth == 4:
        return min(n, 24)
    return min(n, 16)


def _node_cap(depth, n):
    if n <= 35:
        return n
    if depth <= 1:
        return min(n, 42)
    if depth == 2:
        return min(n, 30)
    if depth == 3:
        return min(n, 22)
    return min(n, 16)


def _negamax(b, depth, alpha, beta, deadline, ply):
    _check_time(deadline)

    my_mob = _total_mobility(b, 1)
    if my_mob == 0:
        return -WIN + ply

    if depth <= 0:
        return _evaluate(b, my_mob)

    moves = _generate_moves(b)
    if not moves:
        return -WIN + ply

    cap = _node_cap(depth, len(moves))
    ordered = _order_moves(b, moves, limit=cap, strong=False, deadline=deadline)

    best = -2 * WIN
    for mv in ordered:
        child = _apply_move_swap(b, mv)
        val = -_negamax(child, depth - 1, -beta, -alpha, deadline, ply + 1)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def _generate_moves(b):
    moves = []
    append = moves.append

    for r in range(N):
        for c in range(N):
            if b[r][c] != 1:
                continue

            for dr, dc in DIRS:
                tr, tc = r + dr, c + dc
                while 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                    # Move amazon temporarily.
                    b[r][c] = 0
                    b[tr][tc] = 1

                    for adr, adc in DIRS:
                        ar, ac = tr + adr, tc + adc
                        while 0 <= ar < N and 0 <= ac < N and b[ar][ac] == 0:
                            append((r, c, tr, tc, ar, ac))
                            ar += adr
                            ac += adc

                    # Restore.
                    b[tr][tc] = 0
                    b[r][c] = 1

                    tr += dr
                    tc += dc

    return moves


def _apply_move_swap(b, mv):
    fr, fc, tr, tc, ar, ac = mv
    nb = [row[:] for row in b]

    nb[fr][fc] = 0
    nb[tr][tc] = 1
    nb[ar][ac] = -1

    # Swap perspective: next player becomes "1".
    for r in range(N):
        for c in range(N):
            if nb[r][c] == 1:
                nb[r][c] = 2
            elif nb[r][c] == 2:
                nb[r][c] = 1

    return nb


def _order_moves(b, moves, limit=None, strong=False, deadline=None):
    n = len(moves)
    if n == 0:
        return []

    # Full static scoring is used for smaller lists. For huge lists, cheaply
    # rank everything and only statically rescore the most promising subset.
    if strong or n <= 120:
        scored = []
        for i, mv in enumerate(moves):
            if deadline is not None and (i & 63) == 0:
                _check_time(deadline)
            scored.append((_static_move_score(b, mv), mv))
        scored.sort(key=lambda x: x[0], reverse=True)
        ordered = [m for _, m in scored]
        return ordered if limit is None else ordered[:limit]

    cheap = []
    for i, mv in enumerate(moves):
        if deadline is not None and (i & 63) == 0:
            _check_time(deadline)
        cheap.append((_cheap_move_score(b, mv), mv))
    cheap.sort(key=lambda x: x[0], reverse=True)

    if limit is None:
        pre_count = min(n, 160)
    else:
        pre_count = min(n, max(limit, min(60, limit * 2)))

    top = [m for _, m in cheap[:pre_count]]

    rescored = []
    for i, mv in enumerate(top):
        if deadline is not None and (i & 63) == 0:
            _check_time(deadline)
        rescored.append((_static_move_score(b, mv), mv))
    rescored.sort(key=lambda x: x[0], reverse=True)

    ordered_top = [m for _, m in rescored]

    if limit is not None:
        if len(ordered_top) >= limit:
            return ordered_top[:limit]
        used = set(ordered_top)
        for _, mv in cheap:
            if mv not in used:
                ordered_top.append(mv)
                if len(ordered_top) >= limit:
                    break
        return ordered_top[:limit]

    used = set(ordered_top)
    rest = [m for _, m in cheap if m not in used]
    return ordered_top + rest


def _static_move_score(b, mv):
    fr, fc, tr, tc, ar, ac = mv

    b[fr][fc] = 0
    b[tr][tc] = 1
    b[ar][ac] = -1

    my_mob = _total_mobility(b, 1)
    opp_mob = _total_mobility(b, 2)
    landing_lib = _queen_count(b, tr, tc)

    opp_vis = _visible_count(b, ar, ac, 2)
    own_vis = _visible_count(b, ar, ac, 1)
    opp_near = _near_sum(b, ar, ac, 2)
    own_near = _near_sum(b, ar, ac, 1)

    center = _center_score(tr, tc)

    score = (
        4.0 * (my_mob - opp_mob)
        + 2.2 * landing_lib
        + 8.0 * opp_vis
        - 2.0 * own_vis
        + 1.3 * opp_near
        - 0.35 * own_near
        + center
    )

    if opp_mob == 0:
        score += 0.5 * WIN
    if my_mob == 0:
        score -= 20000.0

    # Restore original board.
    b[ar][ac] = 0
    b[tr][tc] = 0
    b[fr][fc] = 1

    return score


def _cheap_move_score(b, mv):
    fr, fc, tr, tc, ar, ac = mv

    lib = _virtual_queen_count(b, tr, tc, fr, fc, ar, ac)

    opp_near = 0
    own_near = 0
    opp_visible = 0

    for r in range(N):
        for c in range(N):
            v = b[r][c]
            if v == 2:
                d = max(abs(ar - r), abs(ac - c))
                opp_near += max(0, 5 - d)
                if _aligned_clear_virtual(b, ar, ac, r, c, fr, fc, tr, tc):
                    opp_visible += 1
            elif v == 1 and not (r == fr and c == fc):
                d = max(abs(ar - r), abs(ac - c))
                own_near += max(0, 5 - d)

    # The moved amazon is now at the landing square.
    d = max(abs(ar - tr), abs(ac - tc))
    own_near += max(0, 5 - d)

    return (
        2.0 * lib
        + 9.0 * opp_visible
        + 1.1 * opp_near
        - 0.30 * own_near
        + _center_score(tr, tc)
    )


def _center_score(r, c):
    # Prefer flexible central landing squares.
    return 5.0 - (abs(r - 2.5) + abs(c - 2.5))


def _virtual_queen_count(b, r, c, fr, fc, ar, ac):
    count = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N:
            if nr == ar and nc == ac:
                break
            if nr == fr and nc == fc:
                count += 1
                nr += dr
                nc += dc
                continue
            if b[nr][nc] != 0:
                break
            count += 1
            nr += dr
            nc += dc
    return count


def _aligned_clear_virtual(b, ar, ac, r, c, fr, fc, tr, tc):
    dr = 0
    dc = 0

    if ar == r:
        dc = 1 if c > ac else -1
    elif ac == c:
        dr = 1 if r > ar else -1
    elif abs(ar - r) == abs(ac - c):
        dr = 1 if r > ar else -1
        dc = 1 if c > ac else -1
    else:
        return False

    nr, nc = ar + dr, ac + dc
    while not (nr == r and nc == c):
        if nr == fr and nc == fc:
            pass
        elif nr == tr and nc == tc:
            return False
        elif b[nr][nc] != 0:
            return False
        nr += dr
        nc += dc

    return True


def _queen_count(b, r, c):
    count = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
            count += 1
            nr += dr
            nc += dc
    return count


def _total_mobility(b, val):
    total = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == val:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                        total += 1
                        nr += dr
                        nc += dc
    return total


def _visible_count(b, ar, ac, val):
    seen = 0
    for dr, dc in DIRS:
        nr, nc = ar + dr, ac + dc
        while 0 <= nr < N and 0 <= nc < N:
            cell = b[nr][nc]
            if cell == 0:
                nr += dr
                nc += dc
                continue
            if cell == val:
                seen += 1
            break
    return seen


def _near_sum(b, ar, ac, val):
    s = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == val:
                d = max(abs(ar - r), abs(ac - c))
                s += max(0, 5 - d)
    return s


def _evaluate(b, my_mob=None):
    if my_mob is None:
        my_mob = _total_mobility(b, 1)
    if my_mob == 0:
        return -WIN

    opp_mob = _total_mobility(b, 2)

    empties = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == 0:
                empties += 1

    territory = _territory_score(b)
    comp_score, separated, my_empty, opp_empty = _component_info(b)

    score = (
        5.0 * (my_mob - opp_mob)
        + 12.0 * territory
        + 6.0 * comp_score
    )

    # If opponent is currently immobile, this is almost always decisive.
    if opp_mob == 0:
        score += 50000.0

    # Once chambers are separated, remaining private space dominates.
    if separated:
        diff = my_empty - opp_empty
        score += 70.0 * diff
        if diff == 0:
            # In an equal independent race, the player to move is usually worse.
            score -= 20.0

    # In late game, exact move-option count is affordable and useful.
    if empties <= 16:
        my_full = _full_move_count(b, 1, 4000)
        opp_full = _full_move_count(b, 2, 4000)
        score += 0.6 * (my_full - opp_full)

    return score


def _full_move_count(b, val, limit):
    total = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] != val:
                continue

            for dr, dc in DIRS:
                tr, tc = r + dr, c + dc
                while 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                    b[r][c] = 0
                    b[tr][tc] = val
                    total += _queen_count(b, tr, tc)
                    b[tr][tc] = 0
                    b[r][c] = val

                    if total >= limit:
                        return limit

                    tr += dr
                    tc += dc

    return total


def _territory_score(b):
    d1 = _queen_distances(b, 1)
    d2 = _queen_distances(b, 2)

    score = 0.0
    for r in range(N):
        for c in range(N):
            if b[r][c] != 0:
                continue

            a = d1[r][c]
            o = d2[r][c]

            if a == INF and o == INF:
                continue
            if o == INF:
                score += 3.0
            elif a == INF:
                score -= 3.0
            elif a < o:
                score += (2.5 if a == 1 else 1.5) + 0.2 * (o - a)
            elif o < a:
                score -= (2.5 if o == 1 else 1.5) + 0.2 * (a - o)

    return score


def _queen_distances(b, val):
    dist = [[INF for _ in range(N)] for _ in range(N)]
    q = []

    for r in range(N):
        for c in range(N):
            if b[r][c] == val:
                dist[r][c] = 0
                q.append((r, c))

    qi = 0
    while qi < len(q):
        r, c = q[qi]
        qi += 1
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                if dist[nr][nc] == INF:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _component_info(b):
    visited = [[False for _ in range(N)] for _ in range(N)]

    score = 0.0
    separated = True
    my_empty_total = 0
    opp_empty_total = 0

    for sr in range(N):
        for sc in range(N):
            if visited[sr][sc] or b[sr][sc] == -1:
                continue

            stack = [(sr, sc)]
            visited[sr][sc] = True

            empty = 0
            my = 0
            opp = 0

            while stack:
                r, c = stack.pop()
                v = b[r][c]
                if v == 0:
                    empty += 1
                elif v == 1:
                    my += 1
                elif v == 2:
                    opp += 1

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < N and 0 <= nc < N
                        and not visited[nr][nc]
                        and b[nr][nc] != -1
                    ):
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            if my and opp:
                separated = False
            elif my:
                my_empty_total += empty
                score += 2.0 * empty + 0.5 * my
            elif opp:
                opp_empty_total += empty
                score -= 2.0 * empty + 0.5 * opp

    return score, separated, my_empty_total, opp_empty_total
