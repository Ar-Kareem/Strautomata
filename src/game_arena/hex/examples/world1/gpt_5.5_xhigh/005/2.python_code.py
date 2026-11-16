
from collections import deque
import time

N = 11
SIZE = N * N
INF = 10000
WIN_SCORE = 1_000_000_000
CENTER = (N // 2) * N + (N // 2)

# Hex neighbors for the coordinate system in the prompt:
# all 8 grid neighbors except NW and SE.
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

ROW = [0] * SIZE
COL = [0] * SIZE
NEIGH = [[] for _ in range(SIZE)]

for r in range(N):
    for c in range(N):
        i = r * N + c
        ROW[i] = r
        COL[i] = c
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NEIGH[i] = tuple(ns)

TOUCH_MASK = {"b": [0] * SIZE, "w": [0] * SIZE}
for i in range(SIZE):
    r, c = ROW[i], COL[i]
    mb = 0
    if r == 0:
        mb |= 1
    if r == N - 1:
        mb |= 2
    TOUCH_MASK["b"][i] = mb

    mw = 0
    if c == 0:
        mw |= 1
    if c == N - 1:
        mw |= 2
    TOUCH_MASK["w"][i] = mw

EDGE_CELL = tuple(bool(TOUCH_MASK["b"][i] or TOUCH_MASK["w"][i]) for i in range(SIZE))
CORNERS = {0, N - 1, (N - 1) * N, SIZE - 1}

def _hex_center_dist(i):
    dr = ROW[i] - N // 2
    dc = COL[i] - N // 2
    return max(abs(dr), abs(dc), abs(dr + dc))

CENTER_DIST = tuple(_hex_center_dist(i) for i in range(SIZE))
CENTER_ORDER = tuple(sorted(range(SIZE), key=lambda i: (CENTER_DIST[i], abs(ROW[i] - 5) + abs(COL[i] - 5), i)))

AXIS_OFF = {
    "b": tuple(abs(COL[i] - N // 2) for i in range(SIZE)),
    "w": tuple(abs(ROW[i] - N // 2) for i in range(SIZE)),
}

SIDE_CELLS = {
    ("b", 0): tuple(c for c in range(N)),
    ("b", 1): tuple((N - 1) * N + c for c in range(N)),
    ("w", 0): tuple(r * N for r in range(N)),
    ("w", 1): tuple(r * N + (N - 1) for r in range(N)),
}

# Virtual edge templates: a stone one line away from its edge can be
# virtually connected if the two carrier cells are not both cut.
VIRTUAL_SIDE = {(o, s): [] for o in ("b", "w") for s in (0, 1)}
SIDE_CARRIER = [[] for _ in range(SIZE)]
SIDE_ENDPOINT = [[] for _ in range(SIZE)]

def _add_virtual_side(orient, side, stone, a, b):
    VIRTUAL_SIDE[(orient, side)].append((stone, a, b))
    SIDE_ENDPOINT[stone].append((orient, side, a, b))
    SIDE_CARRIER[a].append((orient, side, stone, b))
    SIDE_CARRIER[b].append((orient, side, stone, a))

# Black top/bottom edge templates.
for c in range(N - 1):
    _add_virtual_side("b", 0, 1 * N + c, c, c + 1)
for c in range(1, N):
    _add_virtual_side("b", 1, (N - 2) * N + c, (N - 1) * N + c, (N - 1) * N + c - 1)

# White left/right edge templates.
for r in range(N - 1):
    _add_virtual_side("w", 0, r * N + 1, r * N, (r + 1) * N)
for r in range(1, N):
    _add_virtual_side("w", 1, r * N + (N - 2), r * N + (N - 1), (r - 1) * N + (N - 1))

# Standard Hex bridge templates.
BRIDGE_OFFSETS = ((1, 1), (-1, -1), (-1, 2), (1, -2), (-2, 1), (2, -1))
NEIGH_SET = [set(ns) for ns in NEIGH]
BRIDGES = [[] for _ in range(SIZE)]
CARRIER_BRIDGES = [[] for _ in range(SIZE)]

for i in range(SIZE):
    r, c = ROW[i], COL[i]
    for dr, dc in BRIDGE_OFFSETS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            j = rr * N + cc
            common = tuple(sorted(NEIGH_SET[i].intersection(NEIGH_SET[j])))
            if len(common) == 2:
                a, b = common
                BRIDGES[i].append((j, a, b))
                if i < j:
                    CARRIER_BRIDGES[a].append((i, j, b))
                    CARRIER_BRIDGES[b].append((i, j, a))


def _opp_orient(color):
    return "w" if color == "b" else "b"


def _fallback_idx(board):
    for i in CENTER_ORDER:
        if board[i] == 0:
            return i
    return 0


def _best_center(moves):
    return min(moves, key=lambda i: (CENTER_DIST[i], i))


def _dval(d):
    return 40 if d >= INF else d


def _carrier_ok(board, player, a, b):
    """Whether the two carrier cells still support a virtual connection."""
    enemy = 3 - player
    return board[a] == player or board[b] == player or (board[a] != enemy and board[b] != enemy)


def _side_distance(board, player, orient, side, virtual=False):
    """0-1 BFS distance from one edge to every cell.

    Own stones cost 0, empty cells cost 1, enemy stones are blocked.
    If virtual=True, intact bridge and edge templates are treated as 0-cost links.
    """
    enemy = 3 - player
    dist = [INF] * SIZE
    dq = deque()

    for i in SIDE_CELLS[(orient, side)]:
        if board[i] == enemy:
            continue
        d = 0 if board[i] == player else 1
        if d < dist[i]:
            dist[i] = d
            if d == 0:
                dq.appendleft(i)
            else:
                dq.append(i)

    if virtual:
        for stone, a, b in VIRTUAL_SIDE[(orient, side)]:
            if board[stone] == player and _carrier_ok(board, player, a, b):
                if dist[stone] > 0:
                    dist[stone] = 0
                    dq.appendleft(stone)

    while dq:
        u = dq.popleft()
        du = dist[u]

        for v in NEIGH[u]:
            bv = board[v]
            if bv == enemy:
                continue
            nd = du + (0 if bv == player else 1)
            if nd < dist[v]:
                dist[v] = nd
                if bv == player:
                    dq.appendleft(v)
                else:
                    dq.append(v)

        if virtual and board[u] == player:
            for v, a, b in BRIDGES[u]:
                if board[v] == player and _carrier_ok(board, player, a, b) and du < dist[v]:
                    dist[v] = du
                    dq.appendleft(v)

    return dist


def _target_best(dist, board, player, orient, side, virtual=False):
    best = INF
    for i in SIDE_CELLS[(orient, side)]:
        if dist[i] < best:
            best = dist[i]

    if virtual:
        for stone, a, b in VIRTUAL_SIDE[(orient, side)]:
            if board[stone] == player and _carrier_ok(board, player, a, b):
                if dist[stone] < best:
                    best = dist[stone]

    return best


def _connection_distance(board, player, orient, virtual=False):
    d0 = _side_distance(board, player, orient, 0, virtual)
    return _target_best(d0, board, player, orient, 1, virtual)


def _both_distances(board, player, orient, virtual=False):
    d0 = _side_distance(board, player, orient, 0, virtual)
    d1 = _side_distance(board, player, orient, 1, virtual)
    conn = _target_best(d0, board, player, orient, 1, virtual)
    return d0, d1, conn


def _path_after(d0, d1, idx):
    a, b = d0[idx], d1[idx]
    if a >= INF or b >= INF:
        return INF
    # The empty move itself is counted in both side distances; after playing it,
    # remove two counted empty costs.
    x = a + b - 2
    return 0 if x < 0 else x


def _components(board, player, orient):
    labels = [-1] * SIZE
    masks = []
    comp = 0

    for i in range(SIZE):
        if board[i] != player or labels[i] >= 0:
            continue

        labels[i] = comp
        stack = [i]
        mask = 0

        while stack:
            u = stack.pop()
            mask |= TOUCH_MASK[orient][u]
            for v in NEIGH[u]:
                if board[v] == player and labels[v] < 0:
                    labels[v] = comp
                    stack.append(v)

        masks.append(mask)
        comp += 1

    return labels, masks


def _span(board, player, orient):
    mn = 99
    mx = -1
    touch = 0

    if orient == "b":
        for i, x in enumerate(board):
            if x == player:
                r = ROW[i]
                if r < mn:
                    mn = r
                if r > mx:
                    mx = r
                if r == 0:
                    touch |= 1
                if r == N - 1:
                    touch |= 2
    else:
        for i, x in enumerate(board):
            if x == player:
                c = COL[i]
                if c < mn:
                    mn = c
                if c > mx:
                    mx = c
                if c == 0:
                    touch |= 1
                if c == N - 1:
                    touch |= 2

    if mx < 0:
        return 0.0

    edge_bonus = (1 if touch & 1 else 0) + (1 if touch & 2 else 0)
    return float(mx - mn) + 2.5 * edge_bonus


def _local_score(board, idx, us, them, us_orient, them_orient,
                 lab_us, masks_us, lab_th, masks_th, stones_played):
    score = 0.0

    early = max(0.25, 1.15 - stones_played / 70.0)
    score += early * (4.2 * max(0, 7 - CENTER_DIST[idx]) - 0.7 * AXIS_OFF[us_orient][idx])

    if idx in CORNERS:
        score -= 18.0 if stones_played < 35 else 5.0
    elif EDGE_CELL[idx] and stones_played < 25:
        score -= 4.0

    own_n = 0
    opp_n = 0
    us_comps = set()
    th_comps = set()

    for nb in NEIGH[idx]:
        b = board[nb]
        if b == us:
            own_n += 1
            us_comps.add(lab_us[nb])
        elif b == them:
            opp_n += 1
            th_comps.add(lab_th[nb])

    score += 4.0 * own_n + 1.4 * own_n * own_n + 2.6 * opp_n
    score += 10.0 * max(0, len(us_comps) - 1) + 4.0 * len(us_comps)
    score += 7.0 * max(0, len(th_comps) - 1) + 2.5 * len(th_comps)

    mask = TOUCH_MASK[us_orient][idx]
    for c in us_comps:
        if c >= 0:
            mask |= masks_us[c]
    if mask == 3:
        score += 10000.0
    elif mask:
        score += 11.0

    tmask = TOUCH_MASK[them_orient][idx]
    for c in th_comps:
        if c >= 0:
            tmask |= masks_th[c]
    if tmask == 3:
        score += 8500.0
    elif tmask:
        score += 8.0

    # Making our bridges, or occupying bridge endpoints the opponent wants.
    for v, a, b in BRIDGES[idx]:
        if board[v] == us and _carrier_ok(board, us, a, b):
            adv = abs(ROW[idx] - ROW[v]) if us_orient == "b" else abs(COL[idx] - COL[v])
            score += 18.0 + 5.0 * adv
        elif board[v] == them and _carrier_ok(board, them, a, b):
            adv = abs(ROW[idx] - ROW[v]) if them_orient == "b" else abs(COL[idx] - COL[v])
            score += 9.0 + 3.0 * adv

    # Playing bridge carrier cells: save our cut bridges or attack theirs.
    save = reinforce = cut = attack = 0
    for a, b, other in CARRIER_BRIDGES[idx]:
        if board[a] == us and board[b] == us:
            if board[other] == them:
                save += 1
            elif board[other] == 0:
                reinforce += 1
        elif board[a] == them and board[b] == them:
            if board[other] == us:
                cut += 1
            elif board[other] == 0:
                attack += 1

    score += 52.0 * save + 6.0 * reinforce + 42.0 * cut + 13.0 * attack

    # Edge-template endpoints and carriers.
    for orient, side, a, b in SIDE_ENDPOINT[idx]:
        if orient == us_orient and _carrier_ok(board, us, a, b):
            score += 13.0
        elif orient == them_orient and _carrier_ok(board, them, a, b):
            score += 8.0

    for orient, side, stone, other in SIDE_CARRIER[idx]:
        if orient == us_orient and board[stone] == us:
            if board[other] == them:
                score += 38.0
            elif board[other] == 0:
                score += 14.0
            elif board[other] == us:
                score += 5.0

        if orient == them_orient and board[stone] == them:
            if board[other] == us:
                score += 32.0
            elif board[other] == 0:
                score += 10.0

    return score


def _rank_moves(board, us, us_orient, them, them_orient, limit=None, exact=False, deadline=None):
    empties = [i for i, x in enumerate(board) if x == 0]
    if not empties:
        return []

    stones_played = SIZE - len(empties)

    lab_us, masks_us = _components(board, us, us_orient)
    lab_th, masks_th = _components(board, them, them_orient)

    du0, du1, us_real = _both_distances(board, us, us_orient, False)
    dt0, dt1, th_real = _both_distances(board, them, them_orient, False)
    vu0, vu1, us_virt = _both_distances(board, us, us_orient, True)
    vt0, vt1, th_virt = _both_distances(board, them, them_orient, True)

    bu = _dval(us_real)
    bt = _dval(th_real)
    buv = _dval(us_virt)
    btv = _dval(th_virt)

    scored = []

    for idx in empties:
        score = _local_score(
            board, idx, us, them, us_orient, them_orient,
            lab_us, masks_us, lab_th, masks_th, stones_played
        )

        up = _path_after(du0, du1, idx)
        tp = _path_after(dt0, dt1, idx)
        uvp = _path_after(vu0, vu1, idx)
        tvp = _path_after(vt0, vt1, idx)

        if up < INF:
            score += 30.0 * max(0, 12 - up)
            score += 70.0 / (1.0 + max(0, up - max(0, bu - 1)))
        if tp < INF:
            score += 28.0 * max(0, 12 - tp)
            score += 68.0 / (1.0 + max(0, tp - max(0, bt - 1)))
        if uvp < INF:
            score += 16.0 * max(0, 10 - uvp)
            score += 36.0 / (1.0 + max(0, uvp - max(0, buv - 1)))
        if tvp < INF:
            score += 15.0 * max(0, 10 - tvp)
            score += 34.0 / (1.0 + max(0, tvp - max(0, btv - 1)))

        if exact and (deadline is None or time.perf_counter() < deadline):
            # If we play here.
            board[idx] = us
            ur = _connection_distance(board, us, us_orient, False)
            trb = _connection_distance(board, them, them_orient, False)
            uv = _connection_distance(board, us, us_orient, True)
            tvb = _connection_distance(board, them, them_orient, True)
            board[idx] = 0

            # If opponent plays here instead.
            board[idx] = them
            tri = _connection_distance(board, them, them_orient, False)
            uib = _connection_distance(board, us, us_orient, False)
            tvi = _connection_distance(board, them, them_orient, True)
            uvib = _connection_distance(board, us, us_orient, True)
            board[idx] = 0

            urv = _dval(ur)
            trbv = _dval(trb)
            uvv = _dval(uv)
            tvbv = _dval(tvb)
            triv = _dval(tri)
            uibv = _dval(uib)
            tviv = _dval(tvi)
            uvibv = _dval(uvib)

            score += 150.0 * (bu - urv)
            score += 105.0 * (bt - triv)
            score += 80.0 * (trbv - bt)
            score += 60.0 * (uibv - bu)

            score += 85.0 * (buv - uvv)
            score += 65.0 * (btv - tviv)
            score += 45.0 * (tvbv - btv)
            score += 35.0 * (uvibv - buv)

            score += 22.0 * ((trbv - urv) + 0.6 * (tvbv - uvv))

            if ur == 0:
                score += 1_000_000.0
            if tri == 0:
                score += 500_000.0
            if ur == 1:
                score += 4500.0
            if tri == 1:
                score += 3600.0

        scored.append((score, idx))

    scored.sort(key=lambda x: (-x[0], CENTER_DIST[x[1]], x[1]))
    if limit is not None:
        return scored[:limit]
    return scored


def _winning_moves(board, player, orient, max_count=None):
    wins = []
    for i in CENTER_ORDER:
        if board[i] != 0:
            continue
        board[i] = player
        if _connection_distance(board, player, orient, False) == 0:
            wins.append(i)
            board[i] = 0
            if max_count is not None and len(wins) >= max_count:
                break
        else:
            board[i] = 0
    return wins


def _static_evaluate(board, my_orient, opp_orient, mr=None, orr=None, turn=1):
    """Board value from root player's view.

    turn=1 means root player to move.
    turn=2 means opponent to move.
    """
    if mr is None:
        mr = _connection_distance(board, 1, my_orient, False)
    if orr is None:
        orr = _connection_distance(board, 2, opp_orient, False)

    if mr == 0:
        return float(WIN_SCORE)
    if orr == 0:
        return -float(WIN_SCORE)

    if turn == 1 and mr == 1:
        return WIN_SCORE * 0.35
    if turn == 2 and orr == 1:
        return -WIN_SCORE * 0.35

    mv = _connection_distance(board, 1, my_orient, True)
    ov = _connection_distance(board, 2, opp_orient, True)

    val = 165.0 * (_dval(orr) - _dval(mr)) + 80.0 * (_dval(ov) - _dval(mv))

    if mr == 1:
        val += 9000.0
    elif mr == 2:
        val += 1800.0
    elif mr == 3:
        val += 450.0

    if orr == 1:
        val -= 9000.0
    elif orr == 2:
        val -= 1300.0
    elif orr == 3:
        val -= 350.0

    if mv == 0:
        val += 900.0
    elif mv == 1:
        val += 350.0

    if ov == 0:
        val -= 900.0
    elif ov == 1:
        val -= 350.0

    val += 7.0 * (_span(board, 1, my_orient) - _span(board, 2, opp_orient))
    return val


def _reply_value(board, my_orient, opp_orient):
    """Value after an opponent reply, with root player to move next.

    Includes a small quiescence step for single forced blocks.
    """
    mr = _connection_distance(board, 1, my_orient, False)
    orr = _connection_distance(board, 2, opp_orient, False)

    if mr == 0:
        return float(WIN_SCORE)
    if orr == 0:
        return -float(WIN_SCORE)
    if mr == 1:
        return WIN_SCORE * 0.35

    if orr == 1:
        threats = _winning_moves(board, 2, opp_orient, max_count=2)
        if len(threats) >= 2:
            return -WIN_SCORE * 0.35
        if len(threats) == 1:
            block = threats[0]
            board[block] = 1
            val = _static_evaluate(board, my_orient, opp_orient, turn=2)
            board[block] = 0
            return val - 500.0

    return _static_evaluate(board, my_orient, opp_orient, mr, orr, turn=1)


def _choose_move(board, color, deadline, fallback):
    my_orient = "b" if color == "b" else "w"
    opp_orient = _opp_orient(my_orient)

    my_count = sum(1 for x in board if x == 1)
    opp_count = sum(1 for x in board if x == 2)
    stones = my_count + opp_count
    empty_count = SIZE - stones

    if empty_count <= 0:
        return fallback

    # Opening: take the center if available on our first move.
    if stones == 0 and board[CENTER] == 0:
        return CENTER
    if my_count == 0 and board[CENTER] == 0:
        return CENTER

    # Immediate win.
    my_real = _connection_distance(board, 1, my_orient, False)
    if my_real == 0:
        return fallback
    if my_real == 1:
        wins = _winning_moves(board, 1, my_orient)
        if wins:
            return _best_center(wins)

    # Forced immediate block.
    opp_real = _connection_distance(board, 2, opp_orient, False)
    if opp_real == 1:
        blocks = _winning_moves(board, 2, opp_orient)
        if blocks:
            if len(blocks) == 1:
                return blocks[0]
            ranked_blocks = _rank_moves(
                board, 1, my_orient, 2, opp_orient,
                limit=None, exact=True, deadline=deadline - 0.05
            )
            allowed = set(blocks)
            for _, idx in ranked_blocks:
                if idx in allowed:
                    return idx
            return _best_center(blocks)

    # Root move ranking.
    ranked = _rank_moves(
        board, 1, my_orient, 2, opp_orient,
        limit=None, exact=True, deadline=deadline - 0.20
    )
    if not ranked:
        return fallback

    top_move = ranked[0][1]
    if time.perf_counter() > deadline:
        return top_move

    if empty_count > 95:
        root_limit, reply_limit = 14, 7
    elif empty_count > 65:
        root_limit, reply_limit = 16, 8
    elif empty_count > 35:
        root_limit, reply_limit = 20, 9
    else:
        root_limit, reply_limit = min(30, empty_count), min(12, max(1, empty_count - 1))

    candidates = ranked[:root_limit]
    best_idx = top_move
    best_val = -float("inf")

    for root_score, idx in candidates:
        if time.perf_counter() > deadline:
            break

        if board[idx] != 0:
            continue

        board[idx] = 1

        mr_after = _connection_distance(board, 1, my_orient, False)
        if mr_after == 0:
            board[idx] = 0
            return idx

        # If this move creates two different immediate winning cells,
        # opponent cannot block both.
        our_threats = []
        if mr_after == 1:
            our_threats = _winning_moves(board, 1, my_orient, max_count=2)
            if len(our_threats) >= 2:
                board[idx] = 0
                return idx

        replies = []
        seen = set()

        def add_reply(j):
            if 0 <= j < SIZE and board[j] == 0 and j not in seen:
                seen.add(j)
                replies.append(j)

        for t in our_threats:
            add_reply(t)

        opp_ranked = _rank_moves(
            board, 2, opp_orient, 1, my_orient,
            limit=reply_limit, exact=False
        )

        target_replies = reply_limit + len(our_threats)
        for _, j in opp_ranked:
            add_reply(j)
            if len(replies) >= target_replies:
                break

        if not replies:
            val = _static_evaluate(board, my_orient, opp_orient, turn=2)
        else:
            worst = float("inf")
            for rep in replies:
                if time.perf_counter() > deadline:
                    break

                board[rep] = 2
                rv = _reply_value(board, my_orient, opp_orient)
                board[rep] = 0

                if rv < worst:
                    worst = rv

                if best_val > -1e100 and worst + 0.03 * root_score < best_val - 5000.0:
                    break

            if worst == float("inf"):
                worst = _static_evaluate(board, my_orient, opp_orient, turn=2)

            val = worst + 0.03 * root_score

        board[idx] = 0

        if val > best_val:
            best_val = val
            best_idx = idx

    return best_idx


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board = [0] * SIZE

    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = 1

    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            i = r * N + c
            if board[i] == 0:
                board[i] = 2

    fallback = _fallback_idx(board)

    try:
        color = color.lower() if isinstance(color, str) else "b"
        deadline = time.perf_counter() + 0.93
        idx = _choose_move(board, color, deadline, fallback)
        if not (0 <= idx < SIZE) or board[idx] != 0:
            idx = fallback
    except Exception:
        idx = fallback

    return (idx // N, idx % N)
