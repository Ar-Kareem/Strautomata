
import heapq
import time

N = 11
SIZE = N * N
CENTER = (N - 1) / 2.0
INF = 10 ** 8
WIN_SCORE = 1_000_000.0

DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

ROWS = [i // N for i in range(SIZE)]
COLS = [i % N for i in range(SIZE)]

NEIGHBORS = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NEIGHBORS.append(tuple(ns))
NEIGHBORS = tuple(NEIGHBORS)

STARTS = {
    "b": tuple(c for c in range(N)),
    "w": tuple(r * N for r in range(N)),
}
TARGETS = {
    "b": tuple((N - 1) * N + c for c in range(N)),
    "w": tuple(r * N + (N - 1) for r in range(N)),
}

TARGET_MASKS = {}
for k, ts in TARGETS.items():
    mask = [False] * SIZE
    for t in ts:
        mask[t] = True
    TARGET_MASKS[k] = tuple(mask)


def _build_bridges():
    bridge_endpoints = [[] for _ in range(SIZE)]
    connector_pairs = [[] for _ in range(SIZE)]
    bridge_vectors = ((1, 1), (-1, -1), (1, -2), (-1, 2), (2, -1), (-2, 1))
    neighbor_sets = [set(x) for x in NEIGHBORS]
    seen = set()

    for i in range(SIZE):
        r, c = ROWS[i], COLS[i]
        for dr, dc in bridge_vectors:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                j = rr * N + cc
                common = tuple(sorted(neighbor_sets[i].intersection(neighbor_sets[j])))
                if len(common) == 2:
                    a, b = common
                    bridge_endpoints[i].append((j, a, b))
                    key = (i, j) if i < j else (j, i)
                    if key not in seen:
                        seen.add(key)
                        connector_pairs[a].append((key[0], key[1], b))
                        connector_pairs[b].append((key[0], key[1], a))

    return (
        tuple(tuple(x) for x in bridge_endpoints),
        tuple(tuple(x) for x in connector_pairs),
    )


BRIDGE_ENDPOINTS, CONNECTOR_PAIRS = _build_bridges()


def _rc(i):
    return (ROWS[i], COLS[i])


def _distance_map(board, player, sources):
    enemy = 3 - player
    dist = [INF] * SIZE
    heap = []

    for s in sources:
        v = board[s]
        if v == enemy:
            continue
        d = 0 if v == player else 1
        if d < dist[s]:
            dist[s] = d
            heapq.heappush(heap, (d, s))

    while heap:
        d, i = heapq.heappop(heap)
        if d != dist[i]:
            continue

        for nb in NEIGHBORS[i]:
            v = board[nb]
            if v == enemy:
                continue
            nd = d + (0 if v == player else 1)
            if nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return dist


def _connection_distance(board, player, orient):
    enemy = 3 - player
    starts = STARTS[orient]
    target_mask = TARGET_MASKS[orient]

    dist = [INF] * SIZE
    heap = []

    for s in starts:
        v = board[s]
        if v == enemy:
            continue
        d = 0 if v == player else 1
        if d < dist[s]:
            dist[s] = d
            heapq.heappush(heap, (d, s))

    while heap:
        d, i = heapq.heappop(heap)
        if d != dist[i]:
            continue

        if target_mask[i]:
            return d

        for nb in NEIGHBORS[i]:
            v = board[nb]
            if v == enemy:
                continue
            nd = d + (0 if v == player else 1)
            if nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return INF


def _weighted_costs(board, player, orient):
    enemy = 3 - player
    costs = [INF] * SIZE

    for i in range(SIZE):
        v = board[i]
        if v == player:
            costs[i] = 0.0
            continue
        if v == enemy:
            costs[i] = INF
            continue

        adj_own = 0
        adj_enemy = 0
        for nb in NEIGHBORS[i]:
            if board[nb] == player:
                adj_own += 1
            elif board[nb] == enemy:
                adj_enemy += 1

        bridge_end = 0.0
        for j, a, b in BRIDGE_ENDPOINTS[i]:
            if board[j] == player:
                if board[a] != enemy and board[b] != enemy:
                    bridge_end += 1.0
                elif board[a] != enemy or board[b] != enemy:
                    bridge_end += 0.35

        bridge_conn = 0.0
        for a, b, other in CONNECTOR_PAIRS[i]:
            if board[a] == player and board[b] == player:
                bridge_conn += 1.4 if board[other] == enemy else 1.0

        r, c = ROWS[i], COLS[i]
        cost = (
            1.0
            - 0.115 * adj_own
            - 0.075 * bridge_end
            - 0.180 * bridge_conn
            + 0.025 * adj_enemy
        )

        cost += 0.010 * (abs(r - CENTER) + abs(c - CENTER))

        if orient == "b":
            cost += 0.016 * abs(c - CENTER)
            if c == 0 or c == N - 1:
                cost += 0.035
            if r == 0 or r == N - 1:
                cost -= 0.015
        else:
            cost += 0.016 * abs(r - CENTER)
            if r == 0 or r == N - 1:
                cost += 0.035
            if c == 0 or c == N - 1:
                cost -= 0.015

        if cost < 0.20:
            cost = 0.20
        costs[i] = cost

    return costs


def _weighted_distance(board, player, orient):
    costs = _weighted_costs(board, player, orient)
    starts = STARTS[orient]
    target_mask = TARGET_MASKS[orient]

    dist = [float(INF)] * SIZE
    heap = []

    for s in starts:
        c = costs[s]
        if c >= INF:
            continue
        if c < dist[s]:
            dist[s] = c
            heapq.heappush(heap, (c, s))

    while heap:
        d, i = heapq.heappop(heap)
        if d != dist[i]:
            continue

        if target_mask[i]:
            return d

        for nb in NEIGHBORS[i]:
            c = costs[nb]
            if c >= INF:
                continue
            nd = d + c
            if nd + 1e-12 < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return float(INF)


def _winning_moves(board, player, orient):
    ds = _distance_map(board, player, STARTS[orient])
    base = min(ds[t] for t in TARGETS[orient])
    if base != 1:
        return []

    dg = _distance_map(board, player, TARGETS[orient])
    wins = []
    for i in range(SIZE):
        if board[i] == 0 and ds[i] < INF and dg[i] < INF and ds[i] + dg[i] == 2:
            wins.append(i)
    return wins


def _local_score(board, i, player, orient):
    enemy = 3 - player

    adj_own = 0
    adj_enemy = 0
    for nb in NEIGHBORS[i]:
        if board[nb] == player:
            adj_own += 1
        elif board[nb] == enemy:
            adj_enemy += 1

    score = 9.0 * adj_own + 3.0 * adj_enemy

    for j, a, b in BRIDGE_ENDPOINTS[i]:
        if board[j] == player:
            if board[a] != enemy and board[b] != enemy:
                score += 6.0
            elif board[a] != enemy or board[b] != enemy:
                score += 2.5
        elif board[j] == enemy:
            if board[a] != player and board[b] != player:
                score += 2.0

    for a, b, other in CONNECTOR_PAIRS[i]:
        va, vb = board[a], board[b]
        if va == player and vb == player:
            score += 14.0 if board[other] == enemy else 9.0
        elif va == enemy and vb == enemy:
            score += 12.0 if board[other] == player else 6.0

    r, c = ROWS[i], COLS[i]
    center_dist = abs(r - CENTER) + abs(c - CENTER)
    score += 7.0 - 0.85 * center_dist

    if orient == "b":
        score -= 0.55 * abs(c - CENTER)
        if r == 0 or r == N - 1:
            score += 1.5 + 1.2 * adj_own
        if c == 0 or c == N - 1:
            score -= 0.8
    else:
        score -= 0.55 * abs(r - CENTER)
        if c == 0 or c == N - 1:
            score += 1.5 + 1.2 * adj_own
        if r == 0 or r == N - 1:
            score -= 0.8

    return score


def _formation_score(board, player, orient):
    enemy = 3 - player
    count = 0
    min_axis = N
    max_axis = -1
    lane_penalty = 0.0
    edge_stones = 0
    adj_pairs = 0
    bridge_pairs = 0

    for i in range(SIZE):
        if board[i] != player:
            continue

        count += 1
        r, c = ROWS[i], COLS[i]

        if orient == "b":
            axis = r
            off_axis = c
            if r == 0 or r == N - 1:
                edge_stones += 1
        else:
            axis = c
            off_axis = r
            if c == 0 or c == N - 1:
                edge_stones += 1

        if axis < min_axis:
            min_axis = axis
        if axis > max_axis:
            max_axis = axis

        lane_penalty += abs(off_axis - CENTER)

        for nb in NEIGHBORS[i]:
            if nb > i and board[nb] == player:
                adj_pairs += 1

        for j, a, b in BRIDGE_ENDPOINTS[i]:
            if j > i and board[j] == player and board[a] != enemy and board[b] != enemy:
                bridge_pairs += 1

    if count == 0:
        return 0.0

    span = max_axis - min_axis
    return (
        3.0 * span
        + 1.1 * adj_pairs
        + 1.5 * bridge_pairs
        + 1.8 * edge_stones
        - 0.12 * lane_penalty
    )


def _static_eval(board, my_orient, opp_orient, myd=None, oppd=None):
    if myd is None:
        myd = _connection_distance(board, 1, my_orient)
    if oppd is None:
        oppd = _connection_distance(board, 2, opp_orient)

    if myd == 0:
        return WIN_SCORE
    if oppd == 0:
        return -WIN_SCORE

    md = myd if myd < INF else 40
    od = oppd if oppd < INF else 40

    score = 520.0 * (od - md)

    if md == 1:
        score += 12000.0
    if od == 1:
        score -= 10000.0

    score += 180.0 / (md + 1.0) - 180.0 / (od + 1.0)

    myw = _weighted_distance(board, 1, my_orient)
    oppw = _weighted_distance(board, 2, opp_orient)
    if myw < INF / 2 and oppw < INF / 2:
        score += 80.0 * (oppw - myw)
        score += 35.0 / (myw + 0.7) - 35.0 / (oppw + 0.7)

    score += 4.0 * (
        _formation_score(board, 1, my_orient)
        - _formation_score(board, 2, opp_orient)
    )

    return score


def _candidate_list(board, player, orient, enemy_orient, limit, include=()):
    empties = [i for i in range(SIZE) if board[i] == 0]
    if not empties:
        return []

    if limit < 1:
        limit = 1

    include_set = set(include) if include else set()
    enemy = 3 - player

    ds_p = _distance_map(board, player, STARTS[orient])
    dg_p = _distance_map(board, player, TARGETS[orient])
    base_p = min(ds_p[t] for t in TARGETS[orient])

    ds_e = _distance_map(board, enemy, STARTS[enemy_orient])
    dg_e = _distance_map(board, enemy, TARGETS[enemy_orient])
    base_e = min(ds_e[t] for t in TARGETS[enemy_orient])

    own_wins = set()
    if base_p == 1:
        for i in empties:
            if ds_p[i] < INF and dg_p[i] < INF and ds_p[i] + dg_p[i] == 2:
                own_wins.add(i)

    enemy_wins = set()
    if base_e == 1:
        for i in empties:
            if ds_e[i] < INF and dg_e[i] < INF and ds_e[i] + dg_e[i] == 2:
                enemy_wins.add(i)

    include_set.update(own_wins)
    include_set.update(enemy_wins)

    scored = []
    for i in empties:
        score = _local_score(board, i, player, orient)

        if i in include_set:
            score += 50000.0
        if i in enemy_wins:
            score += 70000.0
        if i in own_wins:
            score += 140000.0

        if base_p < INF and ds_p[i] < INF and dg_p[i] < INF:
            old_path = ds_p[i] + dg_p[i] - 1
            after_est = old_path - 1
            gain = base_p - after_est
            if gain > 0:
                score += 155.0 * gain
            score += 45.0 / (1.0 + after_est)
            score -= 4.0 * after_est

        if base_e < INF and ds_e[i] < INF and dg_e[i] < INF:
            enemy_path = ds_e[i] + dg_e[i] - 1
            block = (base_e + 1.35) - enemy_path
            if block > 0:
                score += 115.0 * block
            score += 28.0 / (1.0 + enemy_path)

        center_tie = -((ROWS[i] - CENTER) ** 2 + (COLS[i] - CENTER) ** 2)
        scored.append((score, center_tie, -i, i))

    scored.sort(reverse=True)
    ordered = [x[3] for x in scored]
    take = max(limit, sum(1 for x in include_set if 0 <= x < SIZE and board[x] == 0))
    return ordered[:take]


def _fallback_move(board, orient):
    best = None
    best_score = -10 ** 18

    for i in range(SIZE):
        if board[i] != 0:
            continue

        r, c = ROWS[i], COLS[i]
        score = -((r - CENTER) ** 2 + (c - CENTER) ** 2)

        if orient == "b":
            score -= 0.20 * abs(c - CENTER)
        else:
            score -= 0.20 * abs(r - CENTER)

        if score > best_score:
            best_score = score
            best = i

    return best if best is not None else 0


def _choose_tactical(board, moves, player, orient):
    best = moves[0]
    best_score = -10 ** 18

    for m in moves:
        if board[m] != 0:
            continue
        s = _local_score(board, m, player, orient)
        s -= 0.01 * ((ROWS[m] - CENTER) ** 2 + (COLS[m] - CENTER) ** 2)
        if s > best_score:
            best_score = s
            best = m

    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    my_orient = (color or "b").lower()
    if my_orient not in ("b", "w"):
        my_orient = "b"
    opp_orient = "w" if my_orient == "b" else "b"

    board = [0] * SIZE

    for r, c in me:
        r, c = int(r), int(c)
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = 1

    for r, c in opp:
        r, c = int(r), int(c)
        if 0 <= r < N and 0 <= c < N:
            idx = r * N + c
            if board[idx] == 0:
                board[idx] = 2

    empties = [i for i in range(SIZE) if board[i] == 0]

    if not empties:
        return (0, 0)

    if len(empties) == SIZE:
        return (5, 5)

    if len(empties) == 1:
        return _rc(empties[0])

    fallback = _fallback_move(board, my_orient)

    my_wins = _winning_moves(board, 1, my_orient)
    if my_wins:
        return _rc(_choose_tactical(board, my_wins, 1, my_orient))

    opp_wins = _winning_moves(board, 2, opp_orient)
    if len(opp_wins) == 1:
        return _rc(opp_wins[0])

    e = len(empties)
    if e > 90:
        root_limit, reply_limit = 24, 12
    elif e > 65:
        root_limit, reply_limit = 28, 14
    elif e > 35:
        root_limit, reply_limit = 32, 16
    else:
        root_limit, reply_limit = min(40, e), min(22, max(1, e - 1))

    root_candidates = _candidate_list(
        board, 1, my_orient, opp_orient, root_limit, include=opp_wins
    )

    if not root_candidates:
        root_candidates = [fallback]

    best_move = root_candidates[0]
    best_score = -10 ** 30

    for m in root_candidates:
        if board[m] != 0:
            continue
        if time.perf_counter() > deadline:
            break

        board[m] = 1

        myd = _connection_distance(board, 1, my_orient)
        if myd == 0:
            board[m] = 0
            return _rc(m)

        oppd = _connection_distance(board, 2, opp_orient)

        if oppd == 0:
            score = -WIN_SCORE
        elif oppd == 1:
            score = -WIN_SCORE + 10.0
        else:
            if time.perf_counter() > deadline:
                score = _static_eval(board, my_orient, opp_orient, myd, oppd)
            else:
                replies = _candidate_list(board, 2, opp_orient, my_orient, reply_limit)

                if not replies:
                    score = _static_eval(board, my_orient, opp_orient, myd, oppd)
                else:
                    worst = 10 ** 30

                    for o in replies:
                        if board[o] != 0:
                            continue
                        if time.perf_counter() > deadline:
                            break

                        board[o] = 2

                        od2 = _connection_distance(board, 2, opp_orient)
                        if od2 == 0:
                            val = -WIN_SCORE
                        else:
                            md2 = _connection_distance(board, 1, my_orient)
                            if md2 == 0:
                                val = WIN_SCORE
                            elif md2 == 1:
                                val = WIN_SCORE - 250.0
                            else:
                                val = _static_eval(board, my_orient, opp_orient, md2, od2)

                        board[o] = 0

                        if val < worst:
                            worst = val

                        if worst <= best_score:
                            break

                    if worst == 10 ** 30:
                        score = _static_eval(board, my_orient, opp_orient, myd, oppd)
                    else:
                        score = worst

        board[m] = 0

        if score > best_score:
            best_score = score
            best_move = m

    if best_move is None or not (0 <= best_move < SIZE) or board[best_move] != 0:
        best_move = fallback

    if board[best_move] != 0:
        best_move = empties[0]

    return _rc(best_move)
