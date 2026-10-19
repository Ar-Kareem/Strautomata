
import time
from collections import deque

SIZE = 6
N = SIZE * SIZE
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]
INF = 99
MATE = 1_000_000
NEG_INF = -10**18
POS_INF = 10**18

# Precompute rays for queen-like movement from every square.
RAYS = [[[] for _ in range(8)] for _ in range(N)]
NEIGHBORS = [[] for _ in range(N)]
CENTER = [0.0] * N

for idx in range(N):
    r, c = divmod(idx, SIZE)
    CENTER[idx] = 4.5 - ((r - 2.5) ** 2 + (c - 2.5) ** 2)
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            NEIGHBORS[idx].append(nr * SIZE + nc)
    for d_idx, (dr, dc) in enumerate(DIRS):
        ray = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE:
            ray.append(nr * SIZE + nc)
            nr += dr
            nc += dc
        RAYS[idx][d_idx] = ray


class _SearchTimeout(Exception):
    pass


class _State:
    __slots__ = ("deadline", "eval_cache", "nodes")

    def __init__(self, deadline):
        self.deadline = deadline
        self.eval_cache = {}
        self.nodes = 0


def _format_move(move):
    f, t, a = move
    return f"{f // SIZE},{f % SIZE}:{t // SIZE},{t % SIZE}:{a // SIZE},{a % SIZE}"


def _positions(cells):
    p1, p2 = [], []
    for i, v in enumerate(cells):
        if v == 1:
            p1.append(i)
        elif v == 2:
            p2.append(i)
    return p1, p2


def _mobility_stats_positions(cells, positions):
    total = 0
    mask = 0
    for p in positions:
        for ray in RAYS[p]:
            for sq in ray:
                if cells[sq] != 0:
                    break
                total += 1
                mask |= (1 << sq)
    return total, mask


def _mobility_stats(cells, player):
    total = 0
    mask = 0
    for p, v in enumerate(cells):
        if v != player:
            continue
        for ray in RAYS[p]:
            for sq in ray:
                if cells[sq] != 0:
                    break
                total += 1
                mask |= (1 << sq)
    return total, mask


def _liberties_positions(cells, positions):
    s = 0
    for p in positions:
        for nb in NEIGHBORS[p]:
            if cells[nb] == 0:
                s += 1
    return s


def _queen_distances(cells, positions):
    dist = [INF] * N
    if not positions:
        return dist

    q = deque()

    # Start from each amazon and expand to empty squares in one queen move.
    for src in positions:
        for ray in RAYS[src]:
            for sq in ray:
                if cells[sq] != 0:
                    break
                if dist[sq] > 1:
                    dist[sq] = 1
                    q.append(sq)

    while q:
        cur = q.popleft()
        nd = dist[cur] + 1
        for ray in RAYS[cur]:
            for sq in ray:
                if cells[sq] != 0:
                    break
                if dist[sq] == INF:
                    dist[sq] = nd
                    q.append(sq)

    return dist


def _static_eval(cells, state):
    key = tuple(cells)
    cached = state.eval_cache.get(key)
    if cached is not None:
        return cached

    p1, p2 = _positions(cells)
    m1, u1 = _mobility_stats_positions(cells, p1)
    m2, u2 = _mobility_stats_positions(cells, p2)
    l1 = _liberties_positions(cells, p1)
    l2 = _liberties_positions(cells, p2)
    d1 = _queen_distances(cells, p1)
    d2 = _queen_distances(cells, p2)

    ownership = 0.0
    closeness = 0.0
    exclusive = 0.0
    contested = 0

    for i, v in enumerate(cells):
        if v != 0:
            continue
        a = d1[i]
        b = d2[i]

        if a < INF:
            closeness += 1.0 / (1 + a)
        if b < INF:
            closeness -= 1.0 / (1 + b)

        if a < b:
            ownership += 1.0
            if b >= INF:
                exclusive += 1.0
        elif b < a:
            ownership -= 1.0
            if a >= INF:
                exclusive -= 1.0
        elif a < INF:
            contested += 1

    center1 = sum(CENTER[i] for i in p1)
    center2 = sum(CENTER[i] for i in p2)

    score = 10.0 * ownership
    score += 14.0 * closeness
    score += 3.0 * exclusive
    score += 1.8 * (m1 - m2)
    score += 0.9 * (u1.bit_count() - u2.bit_count())
    score += 0.5 * (l1 - l2)
    score += 0.15 * (center1 - center2)

    # In clearly separated positions, mobility matters even more.
    if contested == 0:
        score += 1.5 * (m1 - m2)

    # Large heuristic bonuses for trapping one side.
    if m1 == 0 and m2 > 0:
        score -= 200.0
    elif m2 == 0 and m1 > 0:
        score += 200.0

    state.eval_cache[key] = score
    return score


def _has_any_move(cells, player):
    # If a queen can move anywhere, then a legal arrow always exists
    # by shooting back to the vacated source square.
    for p, v in enumerate(cells):
        if v != player:
            continue
        for ray in RAYS[p]:
            for sq in ray:
                if cells[sq] != 0:
                    break
                return True
    return False


def _ordered_moves(cells, player):
    opp = 3 - player
    scored = []

    for f, v in enumerate(cells):
        if v != player:
            continue

        cells[f] = 0
        for ray in RAYS[f]:
            for t in ray:
                if cells[t] != 0:
                    break

                cells[t] = player
                for aray in RAYS[t]:
                    for a in aray:
                        if cells[a] != 0:
                            break

                        cells[a] = -1

                        my_m, my_u = _mobility_stats(cells, player)
                        opp_m, opp_u = _mobility_stats(cells, opp)

                        score = 6.0 * (my_m - opp_m)
                        score += 2.0 * (my_u.bit_count() - opp_u.bit_count())
                        score += 0.5 * CENTER[t] + 0.15 * CENTER[a]

                        if opp_m == 0:
                            score += 100000.0

                        scored.append((score, (f, t, a)))
                        cells[a] = 0

                cells[t] = 0
        cells[f] = player

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _find_any_legal_move(cells, player):
    for f, v in enumerate(cells):
        if v != player:
            continue

        cells[f] = 0
        for ray in RAYS[f]:
            for t in ray:
                if cells[t] != 0:
                    break

                cells[t] = player
                for aray in RAYS[t]:
                    for a in aray:
                        if cells[a] != 0:
                            break
                        cells[t] = 0
                        cells[f] = player
                        return (f, t, a)
                cells[t] = 0
        cells[f] = player

    return None


def _node_limit(depth, n_moves):
    if n_moves <= 10:
        return n_moves
    if depth >= 4:
        return min(n_moves, 8)
    if depth == 3:
        return min(n_moves, 12)
    if depth == 2:
        return min(n_moves, 14)
    return min(n_moves, 20)


def _root_limit(depth, n_moves):
    if n_moves <= 24:
        return n_moves
    if depth == 2:
        return min(n_moves, 96)
    if depth == 3:
        return min(n_moves, 40)
    return min(n_moves, 22)


def _check_time(state):
    state.nodes += 1
    if (state.nodes & 255) == 0 and time.perf_counter() >= state.deadline:
        raise _SearchTimeout()


def _negamax(cells, depth, alpha, beta, player, state, ply):
    _check_time(state)

    if depth == 0:
        val = _static_eval(cells, state)
        return val if player == 1 else -val

    if not _has_any_move(cells, player):
        return -MATE + ply

    moves = _ordered_moves(cells, player)
    if not moves:
        return -MATE + ply

    limit = _node_limit(depth, len(moves))
    if limit < len(moves):
        moves = moves[:limit]

    opp = 3 - player
    best = NEG_INF

    for _, mv in moves:
        f, t, a = mv
        cells[f] = 0
        cells[t] = player
        cells[a] = -1
        try:
            score = -_negamax(cells, depth - 1, -beta, -alpha, opp, state, ply + 1)
        finally:
            cells[f] = player
            cells[t] = 0
            cells[a] = 0

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def policy(board) -> str:
    cells = [int(x) for x in board.reshape(-1)]

    root_moves = _ordered_moves(cells, 1)
    if not root_moves:
        fallback = _find_any_legal_move(cells, 1)
        if fallback is not None:
            return _format_move(fallback)
        # Terminal positions should not be queried, but keep valid syntax.
        return "0,0:0,0:0,0"

    best_move = root_moves[0][1]

    if len(root_moves) == 1:
        return _format_move(best_move)

    # Immediate tactical win found by move ordering.
    if root_moves[0][0] >= 100000.0:
        return _format_move(best_move)

    deadline = time.perf_counter() + 0.92
    state = _State(deadline)

    empties = sum(1 for v in cells if v == 0)
    max_depth = 4 if (len(root_moves) <= 24 or empties <= 14) else 3

    for depth in range(2, max_depth + 1):
        if time.perf_counter() >= deadline:
            break

        try:
            limit = _root_limit(depth, len(root_moves))
            moves_to_search = root_moves[:limit]

            searched = []
            iter_best_score = NEG_INF
            iter_best_move = best_move

            for _, mv in moves_to_search:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout()

                f, t, a = mv
                cells[f] = 0
                cells[t] = 1
                cells[a] = -1
                try:
                    score = -_negamax(cells, depth - 1, NEG_INF, POS_INF, 2, state, 1)
                finally:
                    cells[f] = 1
                    cells[t] = 0
                    cells[a] = 0

                searched.append((score, mv))

                if score > iter_best_score:
                    iter_best_score = score
                    iter_best_move = mv

            searched.sort(key=lambda x: x[0], reverse=True)
            searched_set = {mv for _, mv in searched}
            root_moves = searched + [item for item in root_moves if item[1] not in searched_set]
            best_move = iter_best_move

        except _SearchTimeout:
            break

    return _format_move(best_move)
