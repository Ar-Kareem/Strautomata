
from collections import deque

N = 11
SIZE = N * N
INF = 10**9

# Hex neighbors in the coordinate system from the prompt:
# all 8 surrounding cells except (r-1,c-1) and (r+1,c+1)
DIRS = (
    (0, -1),   # W
    (0, 1),    # E
    (-1, 0),   # N
    (-1, 1),   # NE
    (1, 0),    # S
    (1, -1),   # SW
)

# Bridge patterns as pairs of consecutive hex directions.
BRIDGE_PAIRS = (
    ((0, 1), (-1, 1)),   # endpoint offset (-1, 2)
    ((-1, 1), (-1, 0)),  # endpoint offset (-2, 1)
    ((-1, 0), (0, -1)),  # endpoint offset (-1, -1)
    ((0, -1), (1, -1)),  # endpoint offset (1, -2)
    ((1, -1), (1, 0)),   # endpoint offset (2, -1)
    ((1, 0), (0, 1)),    # endpoint offset (1, 1)
)

ROWS = [i // N for i in range(SIZE)]
COLS = [i % N for i in range(SIZE)]

TOP = [c for c in range(N)]
BOTTOM = [(N - 1) * N + c for c in range(N)]
LEFT = [r * N for r in range(N)]
RIGHT = [r * N + (N - 1) for r in range(N)]

B_SRC = [ROWS[i] == 0 for i in range(SIZE)]
B_TGT = [ROWS[i] == N - 1 for i in range(SIZE)]
W_SRC = [COLS[i] == 0 for i in range(SIZE)]
W_TGT = [COLS[i] == N - 1 for i in range(SIZE)]

CENTER = 5 * N + 5

# Orientation-aware center preference:
CENTER_B = [8.0 - 1.4 * abs(COLS[i] - 5) - 0.35 * abs(ROWS[i] - 5) for i in range(SIZE)]
CENTER_W = [8.0 - 1.4 * abs(ROWS[i] - 5) - 0.35 * abs(COLS[i] - 5) for i in range(SIZE)]

NEI = [[] for _ in range(SIZE)]
for r in range(N):
    for c in range(N):
        i = r * N + c
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                NEI[i].append(nr * N + nc)

# For each cell, precompute bridge endpoints and their two carrier cells.
BRIDGE_ENDS = [[] for _ in range(SIZE)]
for i in range(SIZE):
    r, c = ROWS[i], COLS[i]
    for (dr1, dc1), (dr2, dc2) in BRIDGE_PAIRS:
        er, ec = r + dr1 + dr2, c + dc1 + dc2
        c1r, c1c = r + dr1, c + dc1
        c2r, c2c = r + dr2, c + dc2
        if (
            0 <= er < N and 0 <= ec < N and
            0 <= c1r < N and 0 <= c1c < N and
            0 <= c2r < N and 0 <= c2c < N
        ):
            endpoint = er * N + ec
            carrier1 = c1r * N + c1c
            carrier2 = c2r * N + c2c
            BRIDGE_ENDS[i].append((endpoint, carrier1, carrier2))


def other_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def border_lists(color: str):
    return (TOP, BOTTOM) if color == 'b' else (LEFT, RIGHT)


def border_flags(color: str):
    return (B_SRC, B_TGT) if color == 'b' else (W_SRC, W_TGT)


def norm_dist(d: int) -> int:
    return 30 if d >= INF // 2 else d


def total_empty(ds: list[int], dt: list[int], i: int) -> int:
    a = ds[i]
    b = dt[i]
    if a >= INF // 2 or b >= INF // 2:
        return INF
    return a + b - 1


def distance_map(my: set[int], opp: set[int], sources: list[int]) -> list[int]:
    dist = [INF] * SIZE
    dq = deque()

    in_my = my.__contains__
    in_opp = opp.__contains__

    for s in sources:
        if in_opp(s):
            continue
        d = 0 if in_my(s) else 1
        if d < dist[s]:
            dist[s] = d
            if d == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEI[u]:
            if in_opp(v):
                continue
            w = 0 if in_my(v) else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return dist


def analyze_paths(my: set[int], opp: set[int], color: str):
    src, tgt = border_lists(color)
    ds = distance_map(my, opp, src)
    dt = distance_map(my, opp, tgt)
    best = INF
    for x in tgt:
        if ds[x] < best:
            best = ds[x]
    return ds, dt, best


def label_components(stones: set[int], color: str):
    comp = [-1] * SIZE
    src_flag, tgt_flag = border_flags(color)
    touch_s = []
    touch_t = []

    in_stones = stones.__contains__

    for s in stones:
        if comp[s] != -1:
            continue
        cid = len(touch_s)
        comp[s] = cid
        stack = [s]
        ts = src_flag[s]
        tt = tgt_flag[s]

        while stack:
            u = stack.pop()
            for v in NEI[u]:
                if in_stones(v) and comp[v] == -1:
                    comp[v] = cid
                    stack.append(v)
                    if src_flag[v]:
                        ts = True
                    if tgt_flag[v]:
                        tt = True

        touch_s.append(ts)
        touch_t.append(tt)

    return comp, touch_s, touch_t


def candidate_bridge_bonus(i: int, my: set[int], opp: set[int]) -> float:
    bonus = 0.0
    in_my = my.__contains__
    in_opp = opp.__contains__

    for j, c1, c2 in BRIDGE_ENDS[i]:
        if not in_my(j):
            continue

        o1 = in_opp(c1)
        o2 = in_opp(c2)
        if o1 and o2:
            continue

        bonus += 6.0 if (not o1 and not o2) else 3.0
        if in_my(c1) or in_my(c2):
            bonus += 2.0

    return bonus


def bridge_score(my: set[int], opp: set[int]) -> float:
    score = 0.0
    in_my = my.__contains__
    in_opp = opp.__contains__

    for i in my:
        for j, c1, c2 in BRIDGE_ENDS[i]:
            if j <= i or not in_my(j):
                continue
            o1 = in_opp(c1)
            o2 = in_opp(c2)
            if o1 and o2:
                continue
            score += 2.0 if (not o1 and not o2) else 1.0
            if in_my(c1) or in_my(c2):
                score += 1.0

    return score


def stone_centrality(stones: set[int], color: str) -> float:
    arr = CENTER_B if color == 'b' else CENTER_W
    return sum(arr[i] for i in stones)


def score_cell(
    i: int,
    my: set[int],
    opp: set[int],
    my_analysis,
    opp_analysis,
    my_comp_info,
    opp_comp_info,
    opening_factor: float,
    my_src,
    my_tgt,
    opp_src,
    opp_tgt,
    center_arr,
):
    my_ds, my_dt, my_best = my_analysis
    opp_ds, opp_dt, opp_best = opp_analysis

    score = 0.0

    mt = total_empty(my_ds, my_dt, i)
    ot = total_empty(opp_ds, opp_dt, i)

    if mt < INF // 2:
        score += max(0.0, 72.0 - 8.0 * mt)
        if my_best < INF // 2:
            if mt == my_best:
                score += 24.0
            elif mt == my_best + 1:
                score += 12.0

    if ot < INF // 2:
        score += max(0.0, 60.0 - 7.0 * ot)
        if opp_best < INF // 2:
            if ot == opp_best:
                score += 22.0
            elif ot == opp_best + 1:
                score += 10.0

    my_comp, my_touch_s_arr, my_touch_t_arr = my_comp_info
    opp_comp, opp_touch_s_arr, opp_touch_t_arr = opp_comp_info

    own_n = 0
    opp_n = 0
    my_ids = set()
    opp_ids = set()

    for v in NEI[i]:
        cid = my_comp[v]
        if cid != -1:
            own_n += 1
            my_ids.add(cid)
        oid = opp_comp[v]
        if oid != -1:
            opp_n += 1
            opp_ids.add(oid)

    score += 8.0 * own_n + 4.0 * opp_n
    score += 8.0 * len(my_ids) + 12.0 * max(0, len(my_ids) - 1)

    my_touch_s = my_src[i] or any(my_touch_s_arr[cid] for cid in my_ids)
    my_touch_t = my_tgt[i] or any(my_touch_t_arr[cid] for cid in my_ids)
    if my_touch_s:
        score += 4.0
    if my_touch_t:
        score += 4.0
    if my_touch_s and my_touch_t:
        score += 20.0

    score += 4.0 * len(opp_ids) + 6.0 * max(0, len(opp_ids) - 1)
    opp_touch_s = opp_src[i] or any(opp_touch_s_arr[cid] for cid in opp_ids)
    opp_touch_t = opp_tgt[i] or any(opp_touch_t_arr[cid] for cid in opp_ids)
    if opp_touch_s and opp_touch_t:
        score += 14.0

    score += candidate_bridge_bonus(i, my, opp)
    score += opening_factor * center_arr[i]

    return score, mt, ot


def best_scored_move(
    cells: list[int],
    my: set[int],
    opp: set[int],
    color: str,
    my_analysis=None,
    opp_analysis=None,
) -> int:
    if len(cells) == 1:
        return cells[0]

    opp_color = other_color(color)
    if my_analysis is None:
        my_analysis = analyze_paths(my, opp, color)
    if opp_analysis is None:
        opp_analysis = analyze_paths(opp, my, opp_color)

    my_comp = label_components(my, color)
    opp_comp = label_components(opp, opp_color)

    total = len(my) + len(opp)
    opening_factor = 1.8 if total < 6 else (1.2 if total < 14 else 1.0)

    my_src, my_tgt = border_flags(color)
    opp_src, opp_tgt = border_flags(opp_color)
    center_arr = CENTER_B if color == 'b' else CENTER_W

    best = cells[0]
    best_key = (-10**18, -10**18, 0)

    for i in cells:
        sc, _, _ = score_cell(
            i, my, opp,
            my_analysis, opp_analysis,
            my_comp, opp_comp,
            opening_factor,
            my_src, my_tgt,
            opp_src, opp_tgt,
            center_arr,
        )
        key = (sc, center_arr[i], -i)
        if key > best_key:
            best_key = key
            best = i

    return best


def top_candidates(my: set[int], opp: set[int], color: str, max_count: int) -> list[int]:
    empties = [i for i in range(SIZE) if i not in my and i not in opp]
    if not empties:
        return []

    opp_color = other_color(color)
    my_analysis = analyze_paths(my, opp, color)
    opp_analysis = analyze_paths(opp, my, opp_color)

    my_best = my_analysis[2]
    opp_best = opp_analysis[2]
    my_finite = my_best < INF // 2
    opp_finite = opp_best < INF // 2

    my_comp = label_components(my, color)
    opp_comp = label_components(opp, opp_color)

    total = len(my) + len(opp)
    opening_factor = 1.8 if total < 6 else (1.2 if total < 14 else 1.0)

    my_src, my_tgt = border_flags(color)
    opp_src, opp_tgt = border_flags(opp_color)
    center_arr = CENTER_B if color == 'b' else CENTER_W

    scored = []
    important = []

    for i in empties:
        sc, mt, ot = score_cell(
            i, my, opp,
            my_analysis, opp_analysis,
            my_comp, opp_comp,
            opening_factor,
            my_src, my_tgt,
            opp_src, opp_tgt,
            center_arr,
        )
        key = (sc, center_arr[i], -i, i)
        scored.append(key)

        if (
            i == CENTER or
            (my_finite and (mt == my_best or mt == my_best + 1)) or
            (opp_finite and (ot == opp_best or ot == opp_best + 1))
        ):
            important.append(key)

    important.sort(reverse=True)
    scored.sort(reverse=True)

    result = []
    seen = set()

    for _, _, _, i in important:
        if i not in seen:
            seen.add(i)
            result.append(i)
            if len(result) >= max_count:
                return result

    for _, _, _, i in scored:
        if i not in seen:
            seen.add(i)
            result.append(i)
            if len(result) >= max_count:
                break

    return result


def static_eval(my: set[int], opp: set[int], color: str) -> float:
    opp_color = other_color(color)

    my_analysis = analyze_paths(my, opp, color)
    opp_analysis = analyze_paths(opp, my, opp_color)

    my_best = my_analysis[2]
    opp_best = opp_analysis[2]

    if my_best == 0:
        return 1_000_000.0
    if opp_best == 0:
        return -1_000_000.0

    my_ds, my_dt = my_analysis[0], my_analysis[1]
    opp_ds, opp_dt = opp_analysis[0], opp_analysis[1]

    my_short = my_near = 0
    opp_short = opp_near = 0

    if my_best < INF // 2 or opp_best < INF // 2:
        in_my = my.__contains__
        in_opp = opp.__contains__
        for i in range(SIZE):
            if in_my(i) or in_opp(i):
                continue

            mt = total_empty(my_ds, my_dt, i)
            ot = total_empty(opp_ds, opp_dt, i)

            if my_best < INF // 2:
                if mt == my_best:
                    my_short += 1
                elif mt == my_best + 1:
                    my_near += 1

            if opp_best < INF // 2:
                if ot == opp_best:
                    opp_short += 1
                elif ot == opp_best + 1:
                    opp_near += 1

    score = 100.0 * (norm_dist(opp_best) - norm_dist(my_best))

    if my_best == 1:
        score += 220.0
    elif my_best == 2:
        score += 60.0

    if opp_best == 1:
        score -= 220.0
    elif opp_best == 2:
        score -= 60.0

    score += 7.0 * (my_short - opp_short)
    score += 3.0 * (my_near - opp_near)
    score += 5.0 * (bridge_score(my, opp) - bridge_score(opp, my))
    score += 0.6 * (stone_centrality(my, color) - stone_centrality(opp, opp_color))

    return score


def evaluate_root_move(m: int, my: set[int], opp: set[int], color: str, alpha: float) -> float:
    my2 = set(my)
    my2.add(m)

    # Winning now?
    if analyze_paths(my2, opp, color)[2] == 0:
        return 1_000_000.0

    opp_color = other_color(color)
    opp_analysis = analyze_paths(opp, my2, opp_color)
    opp_best = opp_analysis[2]

    # If opponent can win immediately after this, this move is bad.
    if opp_best == 0:
        return -1_000_000.0
    if opp_best == 1:
        center_arr = CENTER_B if color == 'b' else CENTER_W
        return -900_000.0 + center_arr[m]

    total = len(my2) + len(opp)
    opp_k = 8 if total < 18 else (6 if total < 60 else 5)
    opp_cands = top_candidates(opp, my2, opp_color, opp_k)

    if not opp_cands:
        return static_eval(my2, opp, color)

    worst = float('inf')
    for o in opp_cands:
        opp2 = set(opp)
        opp2.add(o)
        sc = static_eval(my2, opp2, color)
        if sc < worst:
            worst = sc
        if worst <= alpha:
            break

    return worst


def _policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my = {r * N + c for r, c in me if 0 <= r < N and 0 <= c < N}
    op = {r * N + c for r, c in opp if 0 <= r < N and 0 <= c < N}

    legal = [i for i in range(SIZE) if i not in my and i not in op]
    if not legal:
        return (0, 0)

    total = len(my) + len(op)

    # Strong opening: take center if available on the very first move or if board has one stone and center is free.
    if total == 0:
        return (5, 5)
    if total == 1 and CENTER not in my and CENTER not in op:
        return (5, 5)

    opp_color = other_color(color)

    my_analysis = analyze_paths(my, op, color)
    opp_analysis = analyze_paths(op, my, opp_color)

    my_best = my_analysis[2]
    opp_best = opp_analysis[2]

    # Should not happen in a normal engine call, but stay legal.
    if my_best == 0 or opp_best == 0:
        i = legal[0]
        return (ROWS[i], COLS[i])

    # Immediate win.
    if my_best == 1:
        wins = [i for i in legal if total_empty(my_analysis[0], my_analysis[1], i) == 1]
        if wins:
            move = best_scored_move(wins, my, op, color, my_analysis, opp_analysis)
            return (ROWS[move], COLS[move])

    # Immediate forced block.
    if opp_best == 1:
        threats = [i for i in legal if total_empty(opp_analysis[0], opp_analysis[1], i) == 1]
        candidates = threats if threats else [legal[0]]
    else:
        k = 12 if total < 18 else (10 if total < 60 else 8)
        candidates = top_candidates(my, op, color, k)

    if not candidates:
        i = legal[0]
        return (ROWS[i], COLS[i])

    if len(candidates) == 1:
        i = candidates[0]
        return (ROWS[i], COLS[i])

    best_move = candidates[0]
    best_score = -10**18
    center_arr = CENTER_B if color == 'b' else CENTER_W

    for m in candidates:
        if m in my or m in op:
            continue
        sc = evaluate_root_move(m, my, op, color, best_score)
        if sc > best_score or (sc == best_score and center_arr[m] > center_arr[best_move]):
            best_score = sc
            best_move = m

    if best_move in my or best_move in op:
        i = legal[0]
        return (ROWS[i], COLS[i])

    return (ROWS[best_move], COLS[best_move])


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        return _policy(me, opp, color)
    except Exception:
        occupied = set(me) | set(opp)
        for r in range(N):
            for c in range(N):
                if (r, c) not in occupied:
                    return (r, c)
        return (0, 0)
