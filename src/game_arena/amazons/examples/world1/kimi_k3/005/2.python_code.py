
import time
from collections import deque
import numpy as np

N = 6
NSQ = 36
DIRS = ((-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1))

RAYS = []
KNEI = []
CENTER = []
for r in range(N):
    for c in range(N):
        rays = []
        kn = []
        for dr, dc in DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                if abs(rr - r) == 1 and abs(cc - c) == 1:
                    pass
                rr += dr
                cc += dc
            rays.append(tuple(ray))
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    kn.append(rr * N + cc)
        RAYS.append(tuple(rays))
        KNEI.append(tuple(kn))
        CENTER.append(abs(r - 2.5) + abs(c - 2.5))

INF = float("inf")
WIN = 1000000.0
DIST_INF = 127


class SearchTimeout(Exception):
    pass


def _apply(b, code, player):
    ft, a = divmod(code, NSQ)
    f, t = divmod(ft, NSQ)
    nb = b.copy()
    nb[f] = 0
    nb[t] = player
    nb[a] = -1
    return nb


def _gen_moves(b, player):
    moves = []
    R = RAYS
    bb = b
    for f in range(NSQ):
        if bb[f] != player:
            continue
        base = f * NSQ
        for ray in R[f]:
            for t in ray:
                if bb[t] != 0:
                    break
                ft = (base + t) * NSQ
                for aray in R[t]:
                    for a in aray:
                        if a == f:
                            moves.append(ft + a)
                            continue
                        if bb[a] != 0:
                            break
                        moves.append(ft + a)
    return moves


def _has_amazon_move(b, player):
    bb = b
    for f in range(NSQ):
        if bb[f] != player:
            continue
        for ray in RAYS[f]:
            for t in ray:
                if bb[t] == 0:
                    return True
                break
    return False


def _mobility_count(b, player):
    cnt = 0
    bb = b
    for f in range(NSQ):
        if bb[f] != player:
            continue
        for ray in RAYS[f]:
            for t in ray:
                if bb[t] != 0:
                    break
                cnt += 1
    return cnt


def _king_liberty(b, player):
    cnt = 0
    bb = b
    for f in range(NSQ):
        if bb[f] == player:
            for v in KNEI[f]:
                if bb[v] == 0:
                    cnt += 1
    return cnt


def _center_sum(b, player):
    s = 0.0
    for i, v in enumerate(b):
        if v == player:
            s += CENTER[i]
    return s


def _queen_dist(b, player):
    # Heuristic territory distance: arrows are permanent; amazons are movable.
    dist = [DIST_INF] * NSQ
    dq = deque()
    for i, v in enumerate(b):
        if v == player:
            dist[i] = 0
            dq.append(i)
    bb = b
    R = RAYS
    while dq:
        u = dq.popleft()
        nd = dist[u] + 1
        for ray in R[u]:
            for v in ray:
                if bb[v] == -1:
                    break
                if dist[v] == DIST_INF:
                    dist[v] = nd
                    dq.append(v)
    return dist


def _quick_eval_nb(nb):
    return (5.0 * (_mobility_count(nb, 1) - _mobility_count(nb, 2))
            + 1.2 * (_king_liberty(nb, 1) - _king_liberty(nb, 2))
            + 0.35 * (_center_sum(nb, 2) - _center_sum(nb, 1)))


def _evaluate(b, side_to_move):
    d1 = _queen_dist(b, 1)
    d2 = _queen_dist(b, 2)
    terr = 0.0
    for i in range(NSQ):
        if b[i] != 0:
            continue
        x = d1[i]
        y = d2[i]
        if x >= DIST_INF and y >= DIST_INF:
            continue
        if x < y:
            if y >= DIST_INF:
                terr += 2.6
            else:
                terr += 1.0 + 0.14 * min(y - x, 5)
        elif y < x:
            if x >= DIST_INF:
                terr -= 2.6
            else:
                terr -= 1.0 + 0.14 * min(x - y, 5)
        else:
            terr += 0.18 if side_to_move == 1 else -0.18
    mob = _mobility_count(b, 1) - _mobility_count(b, 2)
    lib = _king_liberty(b, 1) - _king_liberty(b, 2)
    cen = _center_sum(b, 2) - _center_sum(b, 1)
    return 16.0 * terr + 3.2 * mob + 1.0 * lib + 0.30 * cen


def _order_moves(b, moves, player, cap, st):
    if len(moves) <= 1:
        return moves
    scored = []
    rev = (player == 1)
    deadline = st["deadline"]
    for i, code in enumerate(moves):
        if (i & 31) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout
        nb = _apply(b, code, player)
        scored.append((_quick_eval_nb(nb), code))
    scored.sort(reverse=rev)
    if len(scored) > cap:
        scored = scored[:cap]
    return [code for _, code in scored]


def _search(b, depth, alpha, beta, player, st):
    st["nodes"] += 1
    if (st["nodes"] & 63) == 0:
        if time.perf_counter() > st["deadline"] or st["nodes"] > st["max_nodes"]:
            raise SearchTimeout

    if not _has_amazon_move(b, player):
        return (WIN + depth) if player == 2 else (-WIN - depth)
    if depth <= 0:
        return _evaluate(b, player)

    moves = _gen_moves(b, player)
    if time.perf_counter() > st["deadline"]:
        raise SearchTimeout
    if not moves:
        return (WIN + depth) if player == 2 else (-WIN - depth)

    if depth == 1:
        cap = 120 if player == 2 else 80
    else:
        cap = 34 if player == 1 else 30
    moves = _order_moves(b, moves, player, cap, st)

    if player == 1:
        val = -INF
        for code in moves:
            nb = _apply(b, code, 1)
            sc = _search(nb, depth - 1, alpha, beta, 2, st)
            if sc > val:
                val = sc
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        return val
    else:
        val = INF
        for code in moves:
            nb = _apply(b, code, 2)
            sc = _search(nb, depth - 1, alpha, beta, 1, st)
            if sc < val:
                val = sc
            if val < beta:
                beta = val
            if alpha >= beta:
                break
        return val


def _code_to_str(code):
    ft, a = divmod(code, NSQ)
    f, t = divmod(ft, NSQ)
    fr, fc = divmod(f, N)
    tr, tc = divmod(t, N)
    ar, ac = divmod(a, N)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _fallback_move(b):
    for f in range(NSQ):
        if b[f] == 1:
            fr, fc = divmod(f, N)
            for ray in RAYS[f]:
                for t in ray:
                    if b[t] != 0:
                        break
                    tr, tc = divmod(t, N)
                    return f"{fr},{fc}:{tr},{tc}:{fr},{fc}"
    return "0,0:0,0:0,0"


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90
    b = np.asarray(board, dtype=np.int8).reshape(-1).tolist()

    moves = _gen_moves(b, 1)
    if not moves:
        return _fallback_move(b)

    best_code = moves[0]
    try:
        # Fast root ordering, plus exact immediate-win detection.
        quick = []
        for i, code in enumerate(moves):
            if (i & 31) == 0 and time.perf_counter() > deadline:
                raise SearchTimeout
            nb = _apply(b, code, 1)
            if not _has_amazon_move(nb, 2):
                return _code_to_str(code)
            quick.append((_quick_eval_nb(nb), code))
        if not quick:
            return _code_to_str(best_code)
        quick.sort(reverse=True)
        best_code = quick[0][1]

        # Full evaluation of the plausible root set.
        full_limit = len(quick) if len(quick) <= 1600 else 1200
        root_scores = []
        for i, (_, code) in enumerate(quick[:full_limit]):
            if (i & 15) == 0 and time.perf_counter() > deadline:
                raise SearchTimeout
            nb = _apply(b, code, 1)
            root_scores.append((_evaluate(nb, 2), code))
        if not root_scores:
            return _code_to_str(best_code)
        root_scores.sort(reverse=True)
        best_code = root_scores[0][1]

        empty_count = 0
        for v in b:
            if v == 0:
                empty_count += 1
        late = empty_count <= 16 or len(moves) <= 80
        plan = ((2, 90), (3, 28), (4, 10)) if late else ((2, 44), (3, 14))

        st = {"deadline": deadline, "nodes": 0, "max_nodes": 14000}
        for depth, cand_n in plan:
            need = 0.14 + 0.06 * depth
            if deadline - time.perf_counter() < need:
                break
            new_scores = []
            best_val = -INF
            first = True
            for _, code in root_scores[:cand_n]:
                if time.perf_counter() > deadline:
                    raise SearchTimeout
                nb = _apply(b, code, 1)
                if not _has_amazon_move(nb, 2):
                    return _code_to_str(code)
                alpha = -INF if first else best_val
                val = _search(nb, depth - 1, alpha, INF, 2, st)
                new_scores.append((val, code))
                if val > best_val:
                    best_val = val
                    best_code = code
                first = False
            new_scores.sort(reverse=True)
            root_scores = new_scores

        return _code_to_str(best_code)
    except SearchTimeout:
        return _code_to_str(best_code)
