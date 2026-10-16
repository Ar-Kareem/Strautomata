
from collections import deque

N = 11
SIZE = N * N
INF = 10**9
TOP_K = 12
CENTER_IDX = 5 * N + 5

# Hex neighbors in this board convention:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

IDX_TO_RC = [(i // N, i % N) for i in range(SIZE)]
ROWS = [r for r, _ in IDX_TO_RC]
COLS = [c for _, c in IDX_TO_RC]

NEI = [[] for _ in range(SIZE)]
for i, (r, c) in enumerate(IDX_TO_RC):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            NEI[i].append(rr * N + cc)

# Side masks / lists
B_START = [ROWS[i] == 0 for i in range(SIZE)]
B_GOAL = [ROWS[i] == N - 1 for i in range(SIZE)]
W_START = [COLS[i] == 0 for i in range(SIZE)]
W_GOAL = [COLS[i] == N - 1 for i in range(SIZE)]

B_START_IDX = [i for i in range(SIZE) if B_START[i]]
W_START_IDX = [i for i in range(SIZE) if W_START[i]]

STARTS = (None, B_START_IDX, W_START_IDX)
GOALS = (None, B_GOAL, W_GOAL)

# Bridge patterns:
# Endpoints like (r,c) and (r+1,c+1) have carriers (r,c+1) and (r+1,c)
ENDPOINT_BRIDGES = [[] for _ in range(SIZE)]   # idx -> [(partner, carrier1, carrier2), ...]
CARRIER_BRIDGES = [[] for _ in range(SIZE)]    # idx -> [(end1, end2, other_carrier), ...]

for r in range(N - 1):
    for c in range(N - 1):
        a = r * N + c
        b = (r + 1) * N + (c + 1)
        x = r * N + (c + 1)
        y = (r + 1) * N + c

        ENDPOINT_BRIDGES[a].append((b, x, y))
        ENDPOINT_BRIDGES[b].append((a, x, y))

        CARRIER_BRIDGES[x].append((a, b, y))
        CARRIER_BRIDGES[y].append((a, b, x))


def _on_start(idx: int, code: int) -> bool:
    return B_START[idx] if code == 1 else W_START[idx]


def _on_goal(idx: int, code: int) -> bool:
    return B_GOAL[idx] if code == 1 else W_GOAL[idx]


def _norm_dist(d: int) -> int:
    return 25 if d >= INF // 2 else d


def _simple_priority(idx: int, code: int) -> int:
    r, c = IDX_TO_RC[idx]
    if code == 1:  # black wants vertical, prefer central columns
        return 30 - 3 * abs(c - 5) - abs(r - 5)
    else:          # white wants horizontal, prefer central rows
        return 30 - 3 * abs(r - 5) - abs(c - 5)


def _is_win_occ(occ: list[int], code: int) -> bool:
    start = STARTS[code]
    goal_mask = GOALS[code]

    seen = [False] * SIZE
    stack = []

    for s in start:
        if occ[s] == code:
            seen[s] = True
            stack.append(s)

    while stack:
        u = stack.pop()
        if goal_mask[u]:
            return True
        for v in NEI[u]:
            if not seen[v] and occ[v] == code:
                seen[v] = True
                stack.append(v)

    return False


def _shortest_path_dist_occ(occ: list[int], code: int) -> int:
    """0-1 BFS on cells:
    own stone = 0 cost
    empty = 1 cost
    opponent = blocked
    """
    opp = 3 - code
    start = STARTS[code]
    goal_mask = GOALS[code]

    dist = [INF] * SIZE
    dq = deque()

    for s in start:
        o = occ[s]
        if o == opp:
            continue
        d = 0 if o == code else 1
        if d < dist[s]:
            dist[s] = d
            if d == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        if goal_mask[u]:
            return du

        for v in NEI[u]:
            o = occ[v]
            if o == opp:
                continue
            w = 0 if o == code else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return INF


def _compute_components(occ: list[int], code: int):
    comp = [-1] * SIZE
    sizes = []
    touch_start = []
    touch_goal = []

    cid = 0
    for i in range(SIZE):
        if occ[i] != code or comp[i] != -1:
            continue

        stack = [i]
        comp[i] = cid
        size = 0
        ts = False
        tg = False

        while stack:
            u = stack.pop()
            size += 1
            if _on_start(u, code):
                ts = True
            if _on_goal(u, code):
                tg = True
            for v in NEI[u]:
                if occ[v] == code and comp[v] == -1:
                    comp[v] = cid
                    stack.append(v)

        sizes.append(size)
        touch_start.append(ts)
        touch_goal.append(tg)
        cid += 1

    return comp, sizes, touch_start, touch_goal


def _axis_span(occ: list[int], code: int) -> int:
    axis = ROWS if code == 1 else COLS
    mn = 99
    mx = -1
    for i, o in enumerate(occ):
        if o == code:
            v = axis[i]
            if v < mn:
                mn = v
            if v > mx:
                mx = v
    return 0 if mx == -1 else (mx - mn)


def _bridge_bonus(idx: int, occ: list[int], code: int) -> int:
    opp = 3 - code
    bonus = 0

    # If this move is an endpoint in a bridge with an existing own endpoint
    for partner, x, y in ENDPOINT_BRIDGES[idx]:
        p = occ[partner]
        ox = occ[x]
        oy = occ[y]
        if p == code:
            if ox == opp and oy == opp:
                continue
            if ox == code or oy == code:
                bonus += 16
            elif ox == 0 and oy == 0:
                bonus += 10
            else:
                bonus += 6

    # If this move is a carrier in a bridge
    for a, b, other in CARRIER_BRIDGES[idx]:
        oa = occ[a]
        ob = occ[b]
        oo = occ[other]

        # Secure our own bridge if one carrier is already lost or contested
        if oa == code and ob == code:
            if oo == opp:
                bonus += 18
            elif oo == 0:
                bonus += 5

        # Block opponent's bridge
        elif oa == opp and ob == opp:
            if oo == 0:
                bonus += 14
            elif oo == code:
                bonus += 3

    return bonus


def _local_score(
    idx: int,
    occ: list[int],
    code: int,
    my_comp,
    my_sizes,
    my_touch_s,
    my_touch_g,
    opp_comp,
    opp_sizes,
    opp_touch_s,
    opp_touch_g,
) -> int:
    opp = 3 - code

    adj_me = 0
    adj_opp = 0
    my_adj = set()
    opp_adj = set()

    for n in NEI[idx]:
        o = occ[n]
        if o == code:
            adj_me += 1
            my_adj.add(my_comp[n])
        elif o == opp:
            adj_opp += 1
            opp_adj.add(opp_comp[n])

    score = 0

    # Basic local contact
    score += 6 * adj_me + 4 * adj_opp

    # Joining own components / sides
    my_links = len(my_adj) + int(_on_start(idx, code)) + int(_on_goal(idx, code))
    if my_links >= 2:
        score += 24 * my_links * (my_links - 1)
    else:
        score += 8 * my_links

    # Blocking opponent joins
    opp_links = len(opp_adj) + int(_on_start(idx, opp)) + int(_on_goal(idx, opp))
    if opp_links >= 2:
        score += 15 * opp_links * (opp_links - 1)
    else:
        score += 5 * opp_links

    # Side-coverage of connected nearby friendly components
    my_bits = 0
    if _on_start(idx, code):
        my_bits |= 1
    if _on_goal(idx, code):
        my_bits |= 2
    for cid in my_adj:
        if my_touch_s[cid]:
            my_bits |= 1
        if my_touch_g[cid]:
            my_bits |= 2
        score += min(my_sizes[cid], 5)
    if my_bits == 3:
        score += 45

    # Side-coverage of nearby opponent components: taking this cell can disrupt it
    opp_bits = 0
    if _on_start(idx, opp):
        opp_bits |= 1
    if _on_goal(idx, opp):
        opp_bits |= 2
    for cid in opp_adj:
        if opp_touch_s[cid]:
            opp_bits |= 1
        if opp_touch_g[cid]:
            opp_bits |= 2
        score += min(opp_sizes[cid], 4)
    if opp_bits == 3:
        score += 28

    # Center / lane preference
    r, c = IDX_TO_RC[idx]
    if code == 1:  # black
        score += 12 - 2 * abs(c - 5) - abs(r - 5)
    else:          # white
        score += 12 - 2 * abs(r - 5) - abs(c - 5)

    score += _bridge_bonus(idx, occ, code)
    return score


def _heuristic_move_score(
    idx: int,
    occ: list[int],
    code: int,
    my_base: int,
    opp_base: int,
    my_comp,
    my_sizes,
    my_touch_s,
    my_touch_g,
    opp_comp,
    opp_sizes,
    opp_touch_s,
    opp_touch_g,
) -> int:
    occ[idx] = code
    my_after = _shortest_path_dist_occ(occ, code)
    opp_after = _shortest_path_dist_occ(occ, 3 - code)
    occ[idx] = 0

    mb = _norm_dist(my_base)
    ob = _norm_dist(opp_base)
    ma = _norm_dist(my_after)
    oa = _norm_dist(opp_after)

    score = 0
    score += 100 * (oa - ma)
    score += 25 * (mb - ma)
    score += 25 * (oa - ob)

    score += _local_score(
        idx,
        occ,
        code,
        my_comp,
        my_sizes,
        my_touch_s,
        my_touch_g,
        opp_comp,
        opp_sizes,
        opp_touch_s,
        opp_touch_g,
    )
    return score


def _state_eval(occ: list[int], my_code: int) -> int:
    opp = 3 - my_code

    myd = _shortest_path_dist_occ(occ, my_code)
    if myd == 0:
        return 1_000_000

    opd = _shortest_path_dist_occ(occ, opp)
    if opd == 0:
        return -1_000_000

    if myd >= INF // 2 and opd >= INF // 2:
        base = 0
    elif myd >= INF // 2:
        base = -50_000
    elif opd >= INF // 2:
        base = 50_000
    else:
        base = 100 * (opd - myd)

    base += 6 * (_axis_span(occ, my_code) - _axis_span(occ, opp))
    return base


def _move_is_safe_one_ply(occ: list[int], idx: int, code: int, empties: list[int]) -> bool:
    opp = 3 - code
    occ[idx] = code
    for r in empties:
        if r == idx:
            continue
        occ[r] = opp
        if _is_win_occ(occ, opp):
            occ[r] = 0
            occ[idx] = 0
            return False
        occ[r] = 0
    occ[idx] = 0
    return True


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_code = 1 if color == "b" else 2
    opp_code = 3 - my_code

    occ = [0] * SIZE

    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            occ[r * N + c] = my_code
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            idx = r * N + c
            if occ[idx] == 0:
                occ[idx] = opp_code

    empties = [i for i in range(SIZE) if occ[i] == 0]
    if not empties:
        return (0, 0)  # should not happen in normal play

    total_stones = len(me) + len(opp)

    # Opening preference
    if total_stones == 0 and occ[CENTER_IDX] == 0:
        return IDX_TO_RC[CENTER_IDX]
    if total_stones <= 1 and occ[CENTER_IDX] == 0:
        return IDX_TO_RC[CENTER_IDX]

    # 1) Immediate winning move
    winning_moves = []
    for idx in empties:
        occ[idx] = my_code
        if _is_win_occ(occ, my_code):
            winning_moves.append(idx)
        occ[idx] = 0

    if winning_moves:
        best = max(winning_moves, key=lambda i: _simple_priority(i, my_code))
        return IDX_TO_RC[best]

    # 2) Must-block opponent immediate win(s)
    opp_wins_now = []
    for idx in empties:
        occ[idx] = opp_code
        if _is_win_occ(occ, opp_code):
            opp_wins_now.append(idx)
        occ[idx] = 0

    if opp_wins_now:
        # If there is exactly one, we must block it.
        if len(opp_wins_now) == 1:
            return IDX_TO_RC[opp_wins_now[0]]

        # Multiple current immediate threats means we cannot stop all of them.
        # Still pick the most useful blocking cell.
        my_base = _shortest_path_dist_occ(occ, my_code)
        opp_base = _shortest_path_dist_occ(occ, opp_code)
        my_comp, my_sizes, my_touch_s, my_touch_g = _compute_components(occ, my_code)
        op_comp, op_sizes, op_touch_s, op_touch_g = _compute_components(occ, opp_code)

        best_idx = opp_wins_now[0]
        best_score = -10**18
        for idx in opp_wins_now:
            sc = _heuristic_move_score(
                idx,
                occ,
                my_code,
                my_base,
                opp_base,
                my_comp,
                my_sizes,
                my_touch_s,
                my_touch_g,
                op_comp,
                op_sizes,
                op_touch_s,
                op_touch_g,
            )
            if sc > best_score:
                best_score = sc
                best_idx = idx
        return IDX_TO_RC[best_idx]

    # 3) Heuristic scoring of all legal moves
    my_base = _shortest_path_dist_occ(occ, my_code)
    opp_base = _shortest_path_dist_occ(occ, opp_code)

    my_comp, my_sizes, my_touch_s, my_touch_g = _compute_components(occ, my_code)
    op_comp, op_sizes, op_touch_s, op_touch_g = _compute_components(occ, opp_code)

    scored_moves = []
    for idx in empties:
        sc = _heuristic_move_score(
            idx,
            occ,
            my_code,
            my_base,
            opp_base,
            my_comp,
            my_sizes,
            my_touch_s,
            my_touch_g,
            op_comp,
            op_sizes,
            op_touch_s,
            op_touch_g,
        )
        scored_moves.append((sc, idx))

    scored_moves.sort(key=lambda x: x[0], reverse=True)

    # 4) Safety filter: prefer moves that do not allow an immediate opponent win
    safe_scored = []
    for sc, idx in scored_moves:
        if _move_is_safe_one_ply(occ, idx, my_code, empties):
            safe_scored.append((sc, idx))

    candidates = safe_scored if safe_scored else scored_moves
    candidates = candidates[:TOP_K]

    # 5) One-ply minimax over the strongest candidates
    best_idx = candidates[0][1]
    best_value = -10**18

    for sc, idx in candidates:
        occ[idx] = my_code

        reply_found = False
        worst_reply_value = 10**18

        for r in empties:
            if r == idx:
                continue
            reply_found = True
            occ[r] = opp_code

            # If unsafe candidates are being considered, allow early tactical cutoff
            if not safe_scored and _is_win_occ(occ, opp_code):
                val = -1_000_000
                occ[r] = 0
                worst_reply_value = val
                break

            val = _state_eval(occ, my_code)
            occ[r] = 0

            if val < worst_reply_value:
                worst_reply_value = val

        if not reply_found:
            worst_reply_value = _state_eval(occ, my_code)

        occ[idx] = 0

        final_value = worst_reply_value + sc // 5
        if final_value > best_value:
            best_value = final_value
            best_idx = idx

    # Final legality fallback
    if 0 <= best_idx < SIZE and occ[best_idx] == 0:
        return IDX_TO_RC[best_idx]

    return IDX_TO_RC[empties[0]]
