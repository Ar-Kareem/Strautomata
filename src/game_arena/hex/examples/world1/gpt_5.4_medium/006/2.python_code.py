
from collections import deque
from typing import List, Tuple, Dict, Set

N = 11
CELL_COUNT = N * N
INF = 10**9
BLOCKED = 2  # for shortest-path weights


def _idx(r: int, c: int) -> int:
    return r * N + c


def _rc(i: int) -> tuple[int, int]:
    return (i // N, i % N)


# Hex neighbors in the coordinate system described by the prompt:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
NEI = [[] for _ in range(CELL_COUNT)]
for r in range(N):
    for c in range(N):
        i = _idx(r, c)
        for rr, cc in (
            (r, c - 1),
            (r, c + 1),
            (r - 1, c),
            (r - 1, c + 1),
            (r + 1, c),
            (r + 1, c - 1),
        ):
            if 0 <= rr < N and 0 <= cc < N:
                NEI[i].append(_idx(rr, cc))

TOP = [_idx(0, c) for c in range(N)]
BOTTOM = [_idx(N - 1, c) for c in range(N)]
LEFT = [_idx(r, 0) for r in range(N)]
RIGHT = [_idx(r, N - 1) for r in range(N)]

# Center-first deterministic ordering for fallbacks / tie-breaking
CENTER_ORDER = sorted(
    range(CELL_COUNT),
    key=lambda i: (
        (_rc(i)[0] - 5) ** 2 + (_rc(i)[1] - 5) ** 2,
        abs(_rc(i)[0] - 5) + abs(_rc(i)[1] - 5),
        i,
    ),
)

# Precompute "bridge-like" partner relations:
# two cells that are not adjacent but share exactly two common neighbors.
BRIDGES = [[] for _ in range(CELL_COUNT)]
nei_sets = [set(ns) for ns in NEI]
for a in range(CELL_COUNT):
    na = nei_sets[a]
    for b in range(CELL_COUNT):
        if b == a or b in na:
            continue
        common = [x for x in NEI[a] if x in nei_sets[b]]
        if len(common) == 2:
            BRIDGES[a].append((b, common[0], common[1]))


def _opp_color(color: str) -> str:
    return "w" if color == "b" else "b"


def _sides(color: str):
    if color == "b":
        return TOP, BOTTOM
    return LEFT, RIGHT


def _build_weights(my: Set[int], opp: Set[int]) -> list[int]:
    w = [1] * CELL_COUNT
    for i in my:
        w[i] = 0
    for i in opp:
        w[i] = BLOCKED
    return w


def _zero_one_bfs(weights: list[int], sources: list[int]) -> list[int]:
    dist = [INF] * CELL_COUNT
    dq = deque()

    for s in sources:
        ws = weights[s]
        if ws >= BLOCKED:
            continue
        if ws < dist[s]:
            dist[s] = ws
            if ws == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEI[u]:
            wv = weights[v]
            if wv >= BLOCKED:
                continue
            nd = du + wv
            if nd < dist[v]:
                dist[v] = nd
                if wv == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return dist


def _shortest_cost(my: Set[int], opp: Set[int], color: str) -> int:
    weights = _build_weights(my, opp)
    start, goal = _sides(color)
    dist = _zero_one_bfs(weights, start)
    best = INF
    for g in goal:
        if weights[g] < BLOCKED and dist[g] < best:
            best = dist[g]
    return best


def _shortest_maps(my: Set[int], opp: Set[int], color: str):
    weights = _build_weights(my, opp)
    start, goal = _sides(color)
    ds = _zero_one_bfs(weights, start)
    dg = _zero_one_bfs(weights, goal)
    best = INF
    for g in goal:
        if weights[g] < BLOCKED and ds[g] < best:
            best = ds[g]
    return ds, dg, best, weights


def _connected(stones: Set[int], color: str) -> bool:
    if not stones:
        return False

    if color == "b":
        frontier = [i for i in TOP if i in stones]
        target_row = N - 1
        seen = set(frontier)
        stack = frontier[:]
        while stack:
            u = stack.pop()
            if u // N == target_row:
                return True
            for v in NEI[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    stack.append(v)
        return False
    else:
        frontier = [i for i in LEFT if i in stones]
        target_col = N - 1
        seen = set(frontier)
        stack = frontier[:]
        while stack:
            u = stack.pop()
            if (u % N) == target_col:
                return True
            for v in NEI[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    stack.append(v)
        return False


def _label_components(stones: Set[int]) -> Dict[int, int]:
    comp: Dict[int, int] = {}
    cid = 0
    for s in stones:
        if s in comp:
            continue
        comp[s] = cid
        stack = [s]
        while stack:
            u = stack.pop()
            for v in NEI[u]:
                if v in stones and v not in comp:
                    comp[v] = cid
                    stack.append(v)
        cid += 1
    return comp


def _board_score(my: Set[int], opp: Set[int], color: str) -> float:
    oc = _opp_color(color)

    myc = _shortest_cost(my, opp, color)
    if myc == 0:
        return 10000.0

    oppc = _shortest_cost(opp, my, oc)
    if oppc == 0:
        return -10000.0

    m = 50 if myc >= INF else myc
    o = 50 if oppc >= INF else oppc

    # Slightly prioritize improving our own path
    return 5.0 * o - 5.5 * m


def _opening_move(occ: Set[int], color: str):
    center = _idx(5, 5)
    total = len(occ)

    if total == 0 and center not in occ:
        return center

    if total == 1:
        if center not in occ:
            return center
        if color == "w":
            prefs = [(5, 4), (5, 6), (4, 6), (6, 4), (4, 5), (6, 5)]
        else:
            prefs = [(4, 5), (6, 5), (5, 4), (5, 6), (4, 6), (6, 4)]
        for r, c in prefs:
            i = _idx(r, c)
            if i not in occ:
                return i

    return None


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = {_idx(r, c) for r, c in me}
    opp_set = {_idx(r, c) for r, c in opp}
    occ = me_set | opp_set

    legals = [i for i in CENTER_ORDER if i not in occ]
    if not legals:
        # Should not happen in normal Hex play, but keep function total.
        return (0, 0)

    # Opening handling
    om = _opening_move(occ, color)
    if om is not None and om not in occ:
        return _rc(om)

    # 1) Immediate win
    for mv in legals:
        if _connected(me_set | {mv}, color):
            return _rc(mv)

    oc = _opp_color(color)

    # 2) Immediate opponent winning threats
    opp_win_set = set()
    for mv in legals:
        if _connected(opp_set | {mv}, oc):
            opp_win_set.add(mv)

    # Current-board strategic maps
    ds_my, dg_my, base_my, w_my = _shortest_maps(me_set, opp_set, color)
    ds_opp, dg_opp, base_opp, w_opp = _shortest_maps(opp_set, me_set, oc)
    me_comp = _label_components(me_set)
    opp_comp = _label_components(opp_set)

    through_my = [INF] * CELL_COUNT
    through_opp = [INF] * CELL_COUNT
    for i in legals:
        if ds_my[i] < INF and dg_my[i] < INF:
            through_my[i] = ds_my[i] + dg_my[i] - w_my[i]
        if ds_opp[i] < INF and dg_opp[i] < INF:
            through_opp[i] = ds_opp[i] + dg_opp[i] - w_opp[i]

    def local_bonus(i: int) -> float:
        r, c = _rc(i)
        own_adj = 0
        opp_adj = 0
        own_groups = set()
        opp_groups = set()

        for n in NEI[i]:
            if n in me_set:
                own_adj += 1
                own_groups.add(me_comp[n])
            elif n in opp_set:
                opp_adj += 1
                opp_groups.add(opp_comp[n])

        b = 0.8 * len(own_groups) + 0.35 * own_adj
        b += 0.55 * len(opp_groups) + 0.20 * opp_adj

        if base_my < INF and through_my[i] < INF:
            b -= 0.8 * (through_my[i] - base_my)
        if base_opp < INF and through_opp[i] < INF:
            b -= 1.0 * (through_opp[i] - base_opp)

        # Centrality
        b -= 0.03 * ((r - 5) ** 2 + (c - 5) ** 2)

        # Slight edge-touch bonus along our goal sides
        if color == "b" and (r == 0 or r == N - 1):
            b += 0.3 + 0.15 * own_adj
        if color == "w" and (c == 0 or c == N - 1):
            b += 0.3 + 0.15 * own_adj

        # Bridge-like structure bonus
        for partner, x, y in BRIDGES[i]:
            if partner in me_set and x not in opp_set and y not in opp_set:
                add = 0.35
                if x in me_set:
                    add += 0.15
                if y in me_set:
                    add += 0.15
                b += add

        return b

    local_scores = {i: local_bonus(i) for i in legals}

    # Candidate selection:
    # - if there is an immediate threat, only blocking cells matter
    # - otherwise search a strong subset of promising moves
    if opp_win_set:
        candidates = [i for i in legals if i in opp_win_set]
        if not candidates:
            candidates = legals[:1]
    else:
        scored = sorted(((local_scores[i], i) for i in legals), reverse=True)
        if len(legals) > 40:
            k = 26
        elif len(legals) > 20:
            k = 32
        else:
            k = len(legals)
        candidates = [i for _, i in scored[:k]]

    best_move = candidates[0]
    best_value = -1e30

    for mv in candidates:
        me2 = set(me_set)
        me2.add(mv)

        # If opponent already has some immediate winning move other than mv,
        # then this move loses at once.
        if opp_win_set and any(w != mv for w in opp_win_set):
            worst_reply_value = -10000.0
        else:
            worst_reply_value = 1e30
            for reply in legals:
                if reply == mv:
                    continue
                val = _board_score(me2, opp_set | {reply}, color)
                if val < worst_reply_value:
                    worst_reply_value = val
                if worst_reply_value <= -9999:
                    break

        now_value = _board_score(me2, opp_set, color)
        total_value = worst_reply_value + 0.25 * now_value + local_scores[mv]

        if total_value > best_value:
            best_value = total_value
            best_move = mv

    # Absolute legal fallback
    if best_move in occ:
        for i in legals:
            return _rc(i)

    return _rc(best_move)
