
import time

N = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

RAYS = [[None for _ in range(N)] for _ in range(N)]
for r in range(N):
    for c in range(N):
        rays = []
        for dr, dc in DIRS:
            ray = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                ray.append((nr, nc))
                nr += dr
                nc += dc
            rays.append(ray)
        RAYS[r][c] = rays

INF_DIST = 99
WIN = 100000000.0


class _Timeout(Exception):
    pass


def _format_move(m):
    if m is None:
        return "0,0:0,0:0,0"
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def _copy_board(board):
    return [[int(board[r][c]) for c in range(N)] for r in range(N)]


def _do_move(b, m, side):
    fr, fc, tr, tc, ar, ac = m
    b[fr][fc] = 0
    b[tr][tc] = side
    b[ar][ac] = -1


def _undo_move(b, m, side):
    fr, fc, tr, tc, ar, ac = m
    b[ar][ac] = 0
    b[tr][tc] = 0
    b[fr][fc] = side


def _has_move(b, side):
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                for ray in RAYS[r][c]:
                    for nr, nc in ray:
                        if b[nr][nc] != 0:
                            break
                        return True
    return False


def _count_destinations(b, side):
    total = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                for ray in RAYS[r][c]:
                    for nr, nc in ray:
                        if b[nr][nc] != 0:
                            break
                        total += 1
    return total


def _generate_moves(b, side):
    moves = []
    pieces = []
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                pieces.append((r, c))

    for fr, fc in pieces:
        b[fr][fc] = 0

        for move_ray in RAYS[fr][fc]:
            for tr, tc in move_ray:
                if b[tr][tc] != 0:
                    break

                b[tr][tc] = side

                for arrow_ray in RAYS[tr][tc]:
                    for ar, ac in arrow_ray:
                        if b[ar][ac] != 0:
                            break
                        moves.append((fr, fc, tr, tc, ar, ac))

                b[tr][tc] = 0

        b[fr][fc] = side

    return moves


def _first_legal_move(b, side):
    for fr in range(N):
        for fc in range(N):
            if b[fr][fc] != side:
                continue

            b[fr][fc] = 0

            for move_ray in RAYS[fr][fc]:
                for tr, tc in move_ray:
                    if b[tr][tc] != 0:
                        break

                    b[tr][tc] = side

                    for arrow_ray in RAYS[tr][tc]:
                        for ar, ac in arrow_ray:
                            if b[ar][ac] != 0:
                                break
                            b[tr][tc] = 0
                            b[fr][fc] = side
                            return (fr, fc, tr, tc, ar, ac)

                    b[tr][tc] = 0

            b[fr][fc] = side

    return None


def _queen_distances(b, side):
    dist = [[INF_DIST for _ in range(N)] for _ in range(N)]
    q = []

    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                dist[r][c] = 0
                q.append((r, c))

    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1

        for ray in RAYS[r][c]:
            for nr, nc in ray:
                if b[nr][nc] != 0:
                    break
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))

    return dist


def _king_distances(b, side):
    dist = [[INF_DIST for _ in range(N)] for _ in range(N)]
    q = []

    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                dist[r][c] = 0
                q.append((r, c))

    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))

    return dist


def _local_liberties(b, side):
    total = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                        total += 1
    return total


def _component_score(b):
    seen = [[False for _ in range(N)] for _ in range(N)]
    score = 0.0

    for sr in range(N):
        for sc in range(N):
            if seen[sr][sc] or b[sr][sc] == -1:
                continue

            stack = [(sr, sc)]
            seen[sr][sc] = True
            empty = 0
            mine = 0
            opp = 0

            while stack:
                r, c = stack.pop()
                v = b[r][c]
                if v == 0:
                    empty += 1
                elif v == 1:
                    mine += 1
                elif v == 2:
                    opp += 1

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N:
                        if not seen[nr][nc] and b[nr][nc] != -1:
                            seen[nr][nc] = True
                            stack.append((nr, nc))

            if mine and not opp:
                score += 1.4 * empty + 0.2 * mine
            elif opp and not mine:
                score -= 1.4 * empty + 0.2 * opp

    return score


def _evaluate(b, side_to_move):
    q1 = _queen_distances(b, 1)
    q2 = _queen_distances(b, 2)
    k1 = _king_distances(b, 1)
    k2 = _king_distances(b, 2)

    score = 0.0

    for r in range(N):
        for c in range(N):
            if b[r][c] != 0:
                continue

            a = q1[r][c]
            o = q2[r][c]

            if a < o:
                score += 5.0
                if a < INF_DIST:
                    score += 0.35 * (8 - a)
            elif o < a:
                score -= 5.0
                if o < INF_DIST:
                    score -= 0.35 * (8 - o)
            elif a < INF_DIST:
                ka = k1[r][c]
                ko = k2[r][c]
                if ka < ko:
                    score += 1.3
                elif ko < ka:
                    score -= 1.3
                else:
                    score += 0.18 if side_to_move == 1 else -0.18

    score += 0.55 * (_count_destinations(b, 1) - _count_destinations(b, 2))
    score += 0.28 * (_local_liberties(b, 1) - _local_liberties(b, 2))
    score += _component_score(b)
    score += 0.05 if side_to_move == 1 else -0.05

    return score


def _approx_dest_mobility(b, m):
    fr, fc, tr, tc, ar, ac = m
    total = 0

    for ray in RAYS[tr][tc]:
        for nr, nc in ray:
            if nr == ar and nc == ac:
                break
            if nr == fr and nc == fc:
                total += 1
                continue
            if b[nr][nc] != 0:
                break
            total += 1

    return total


def _cheap_move_key(b, m, side):
    fr, fc, tr, tc, ar, ac = m
    opp = 3 - side

    dest_mob = _approx_dest_mobility(b, m)
    near_opp = 0.0
    near_own = 0.0

    for r in range(N):
        for c in range(N):
            if b[r][c] == opp:
                d = max(abs(ar - r), abs(ac - c))
                if d < 5:
                    near_opp += 5 - d
            elif b[r][c] == side and not (r == fr and c == fc):
                d = max(abs(ar - r), abs(ac - c))
                if d < 4:
                    near_own += 4 - d

    center_bonus = 6.0 - (abs(tr - 2.5) + abs(tc - 2.5))
    arrow_center = 3.0 - 0.3 * (abs(ar - 2.5) + abs(ac - 2.5))

    return 1.25 * dest_mob + 1.8 * near_opp - 0.45 * near_own + 0.35 * center_bonus + arrow_center


def _quick_score_after(b, side):
    opp = 3 - side
    opp_mob = _count_destinations(b, opp)
    if opp_mob == 0:
        return WIN / 10.0

    my_mob = _count_destinations(b, side)
    if my_mob == 0:
        return -WIN / 10.0

    val = 2.2 * (my_mob - opp_mob)
    val += 0.45 * (_local_liberties(b, side) - _local_liberties(b, opp))

    comp = _component_score(b)
    val += 0.18 * comp if side == 1 else -0.18 * comp

    return val


def _move_limit(depth, total):
    if total <= 70:
        return total
    if depth >= 4:
        return min(total, 12)
    if depth == 3:
        return min(total, 18)
    if depth == 2:
        return min(total, 30)
    return min(total, 65)


def _ordered_moves(b, side, depth, deadline):
    if time.perf_counter() > deadline:
        raise _Timeout()

    moves = _generate_moves(b, side)
    total = len(moves)

    if total <= 1:
        return moves

    limit = _move_limit(depth, total)

    if total > 360 and limit < total:
        moves.sort(key=lambda m: _cheap_move_key(b, m, side), reverse=True)
        pre_count = min(total, max(90, limit * 4))
        candidates = moves[:pre_count]
    else:
        candidates = moves

    scored = []
    for i, m in enumerate(candidates):
        if (i & 31) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

        _do_move(b, m, side)
        try:
            sc = _quick_score_after(b, side)
        finally:
            _undo_move(b, m, side)

        scored.append((sc, m))

    scored.sort(key=lambda x: x[0], reverse=True)

    if len(scored) > limit:
        scored = scored[:limit]

    return [m for _, m in scored]


def _alphabeta(b, depth, side, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise _Timeout()

    if not _has_move(b, side):
        if side == 1:
            return -WIN - depth
        return WIN + depth

    if depth <= 0:
        return _evaluate(b, side)

    moves = _ordered_moves(b, side, depth, deadline)

    if not moves:
        if side == 1:
            return -WIN - depth
        return WIN + depth

    next_side = 3 - side

    if side == 1:
        value = -WIN * 2.0

        for m in moves:
            _do_move(b, m, side)
            try:
                child = _alphabeta(b, depth - 1, next_side, alpha, beta, deadline)
            finally:
                _undo_move(b, m, side)

            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        return value

    else:
        value = WIN * 2.0

        for m in moves:
            _do_move(b, m, side)
            try:
                child = _alphabeta(b, depth - 1, next_side, alpha, beta, deadline)
            finally:
                _undo_move(b, m, side)

            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                break

        return value


def _root_limit(depth, total):
    if total <= 1:
        return total

    if depth == 2:
        if total <= 100:
            return total
        if total <= 300:
            return 55
        return 30

    if depth == 3:
        if total <= 60:
            return total
        if total <= 250:
            return 24
        return 14

    if depth == 4:
        if total <= 35:
            return total
        return 12

    if total <= 22:
        return total
    return 8


def _policy(board):
    start = time.perf_counter()
    deadline = start + 0.92

    b = _copy_board(board)

    root_moves = _generate_moves(b, 1)
    if not root_moves:
        return _format_move(_first_legal_move(b, 1))

    if len(root_moves) == 1:
        return _format_move(root_moves[0])

    fallback = root_moves[0]
    scored = []

    for i, m in enumerate(root_moves):
        _do_move(b, m, 1)
        try:
            winning = not _has_move(b, 2)
            if winning:
                sc = WIN
            else:
                sc = _evaluate(b, 2)
        finally:
            _undo_move(b, m, 1)

        if winning:
            return _format_move(m)

        scored.append((sc, m))

        if (i & 31) == 31 and time.perf_counter() > deadline:
            break

    if not scored:
        return _format_move(fallback)

    scored.sort(key=lambda x: x[0], reverse=True)
    best_move = scored[0][1]

    for depth in (2, 3, 4, 5):
        if time.perf_counter() > deadline:
            break

        limit = _root_limit(depth, len(scored))
        current_best = best_move
        current_val = -WIN * 2.0
        alpha = -WIN * 2.0
        beta = WIN * 2.0
        searched_scores = {}

        try:
            for _, m in scored[:limit]:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                _do_move(b, m, 1)
                try:
                    val = _alphabeta(b, depth - 1, 2, alpha, beta, deadline)
                finally:
                    _undo_move(b, m, 1)

                searched_scores[m] = val

                if val > current_val:
                    current_val = val
                    current_best = m

                if val > alpha:
                    alpha = val

        except _Timeout:
            break

        if searched_scores:
            best_move = current_best
            rescored = []
            for old_score, m in scored:
                rescored.append((searched_scores.get(m, old_score), m))
            rescored.sort(key=lambda x: x[0], reverse=True)
            scored = rescored

    return _format_move(best_move)


def policy(board) -> str:
    try:
        return _policy(board)
    except Exception:
        try:
            b = _copy_board(board)
            return _format_move(_first_legal_move(b, 1))
        except Exception:
            return "0,0:0,0:0,0"
