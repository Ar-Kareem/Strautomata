
import heapq
import time

N = 11
NN = N * N
INF = 10 ** 9
WIN_SCORE = 100_000_000

DIRECTIONS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

COORDS = [(i // N, i % N) for i in range(NN)]

NEIGH = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRECTIONS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NEIGH.append(ns)

NEIGH_SETS = [set(x) for x in NEIGH]

SIDES = {
    ("b", 0): [c for c in range(N)],
    ("b", 1): [(N - 1) * N + c for c in range(N)],
    ("w", 0): [r * N for r in range(N)],
    ("w", 1): [r * N + (N - 1) for r in range(N)],
}

SIDE_BOOL = {}
for key, cells in SIDES.items():
    arr = [False] * NN
    for x in cells:
        arr[x] = True
    SIDE_BOOL[key] = arr

CENTER = (N // 2) * N + (N // 2)

def _hex_dist_from_center(idx):
    r, c = COORDS[idx]
    dr = r - N // 2
    dc = c - N // 2
    return max(abs(dr), abs(dc), abs(dr + dc))

CENTER_DIST = [_hex_dist_from_center(i) for i in range(NN)]
CENTER_ORDER = sorted(range(NN), key=lambda i: (CENTER_DIST[i], abs(COORDS[i][0] - 5) + abs(COORDS[i][1] - 5), i))

# Bridge endpoint table: two non-adjacent cells with exactly two common neighbours.
BRIDGE_PARTNERS = [[] for _ in range(NN)]
COMMON2 = {}
for i in range(NN):
    for j in range(i + 1, NN):
        if j in NEIGH_SETS[i]:
            continue
        common = [x for x in NEIGH[i] if x in NEIGH_SETS[j]]
        if len(common) == 2:
            a, b = common[0], common[1]
            BRIDGE_PARTNERS[i].append((j, a, b))
            BRIDGE_PARTNERS[j].append((i, a, b))
            COMMON2[(i, j)] = (a, b)


def _other_color(color):
    return "w" if color == "b" else "b"


def _idx(r, c):
    return r * N + c


def _on_board(r, c):
    return 0 <= r < N and 0 <= c < N


def _has_connection(board, val, orient):
    starts = SIDES[(orient, 0)]
    goal = SIDE_BOOL[(orient, 1)]

    stack = [i for i in starts if board[i] == val]
    if not stack:
        return False

    seen = [False] * NN
    for i in stack:
        seen[i] = True

    while stack:
        x = stack.pop()
        if goal[x]:
            return True
        for nb in NEIGH[x]:
            if not seen[nb] and board[nb] == val:
                seen[nb] = True
                stack.append(nb)
    return False


def _bridge_formation_count(board, idx, val):
    # Candidate idx as a new endpoint of a secure bridge to an existing own stone.
    cnt = 0
    for j, c1, c2 in BRIDGE_PARTNERS[idx]:
        if board[j] == val and board[c1] == 0 and board[c2] == 0:
            cnt += 1
            if cnt >= 4:
                break
    return cnt


def _bridge_completion_count(board, idx, val):
    # Candidate idx as a common neighbour connecting/cutting two non-adjacent stones.
    own = [nb for nb in NEIGH[idx] if board[nb] == val]
    cnt = 0
    ln = len(own)
    for a_i in range(ln):
        a = own[a_i]
        for b in own[a_i + 1:]:
            if b in NEIGH_SETS[a]:
                continue
            key = (a, b) if a < b else (b, a)
            if key in COMMON2:
                c1, c2 = COMMON2[key]
                if c1 == idx:
                    other = c2
                elif c2 == idx:
                    other = c1
                else:
                    other = -1
                if other >= 0:
                    if board[other] == 0:
                        cnt += 2
                    else:
                        cnt += 1
                else:
                    cnt += 1
            else:
                cnt += 1
    return cnt


def _make_weights(board, val, orient, weighted):
    enemy = -val
    weights = [INF] * NN

    for i, b in enumerate(board):
        if b == enemy:
            continue
        if b == val:
            weights[i] = 0
            continue

        if not weighted:
            weights[i] = 1
            continue

        own_count = 0
        enemy_count = 0
        own_list = []

        for nb in NEIGH[i]:
            bv = board[nb]
            if bv == val:
                own_count += 1
                own_list.append(nb)
            elif bv == enemy:
                enemy_count += 1

        w = 100
        w -= 8 * min(own_count, 4)
        w += 3 * min(enemy_count, 3)

        r, c = COORDS[i]
        if orient == "b":
            if r == 0 or r == N - 1:
                w -= 7
            elif r == 1 or r == N - 2:
                w -= 2
        else:
            if c == 0 or c == N - 1:
                w -= 7
            elif c == 1 or c == N - 2:
                w -= 2

        pairs = 0
        ln = len(own_list)
        for a_i in range(ln):
            a = own_list[a_i]
            for b2 in own_list[a_i + 1:]:
                if b2 not in NEIGH_SETS[a]:
                    pairs += 1
        if pairs:
            w -= 7 * min(pairs, 3)

        forms = _bridge_formation_count(board, i, val)
        if forms:
            w -= 6 * min(forms, 3)

        weights[i] = max(42, w)

    return weights


def _dijkstra_from_side(weights, starts):
    dist = [INF] * NN
    heap = []

    for s in starts:
        w = weights[s]
        if w < INF and w < dist[s]:
            dist[s] = w
            heapq.heappush(heap, (w, s))

    while heap:
        d, x = heapq.heappop(heap)
        if d != dist[x]:
            continue
        for nb in NEIGH[x]:
            w = weights[nb]
            if w >= INF:
                continue
            nd = d + w
            if nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return dist


def _shortest_total(board, val, orient, weighted=False):
    weights = _make_weights(board, val, orient, weighted)
    dist = _dijkstra_from_side(weights, SIDES[(orient, 0)])
    total = min(dist[i] for i in SIDES[(orient, 1)])
    return total


def _dist_info(board, val, orient, weighted=False):
    weights = _make_weights(board, val, orient, weighted)
    ds = _dijkstra_from_side(weights, SIDES[(orient, 0)])
    de = _dijkstra_from_side(weights, SIDES[(orient, 1)])
    total = min(ds[i] for i in SIDES[(orient, 1)])
    return total, ds, de, weights


def _find_winning_moves(board, val, orient, limit=20):
    # A winning move exists only when the pure connection distance is exactly one.
    if _shortest_total(board, val, orient, weighted=False) != 1:
        return []

    out = []
    for i in range(NN):
        if board[i] != 0:
            continue
        board[i] = val
        if _has_connection(board, val, orient):
            out.append(i)
            board[i] = 0
            if len(out) >= limit:
                break
        else:
            board[i] = 0
    return out


def _component_strength(board, val, orient):
    seen = [False] * NN
    best = 0.0
    total = 0.0

    for i in range(NN):
        if board[i] != val or seen[i]:
            continue

        stack = [i]
        seen[i] = True
        size = 0
        mn = 99
        mx = -1
        touch0 = False
        touch1 = False

        while stack:
            x = stack.pop()
            size += 1
            r, c = COORDS[x]
            axis = r if orient == "b" else c
            mn = min(mn, axis)
            mx = max(mx, axis)
            if axis == 0:
                touch0 = True
            if axis == N - 1:
                touch1 = True

            for nb in NEIGH[x]:
                if not seen[nb] and board[nb] == val:
                    seen[nb] = True
                    stack.append(nb)

        span = mx - mn + 1
        sc = size * 3 + span * span * 5
        if touch0:
            sc += 20 + span * 4
        if touch1:
            sc += 20 + span * 4

        best = max(best, sc)
        total += sc

    return best + 0.2 * total


def _static_eval(board, my_color, opp_color, turn_val=1):
    if _has_connection(board, 1, my_color):
        return WIN_SCORE
    if _has_connection(board, -1, opp_color):
        return -WIN_SCORE

    mp = _shortest_total(board, 1, my_color, weighted=False)
    op = _shortest_total(board, -1, opp_color, weighted=False)
    mw = _shortest_total(board, 1, my_color, weighted=True)
    ow = _shortest_total(board, -1, opp_color, weighted=True)

    mp = min(mp, 99)
    op = min(op, 99)
    mw = min(mw, 10000)
    ow = min(ow, 10000)

    score = 1400.0 * (op - mp) + 2.15 * (ow - mw)

    if mp == 1:
        score += 60000 if turn_val == 1 else 9000
    elif mp == 2:
        score += 1800
    elif mp == 3:
        score += 450

    if op == 1:
        score -= 60000 if turn_val == -1 else 10000
    elif op == 2:
        score -= 2000
    elif op == 3:
        score -= 500

    score += 2.5 * (
        _component_strength(board, 1, my_color)
        - _component_strength(board, -1, opp_color)
    )

    return score


def _central_empty(board):
    for i in CENTER_ORDER:
        if board[i] == 0:
            return i
    return None


def _generate_candidates(board, val, orient, enemy_orient, maxn):
    empties = [i for i in range(NN) if board[i] == 0]
    if not empties:
        return []

    forced = []
    forced_set = set()

    def add_forced(x):
        if 0 <= x < NN and board[x] == 0 and x not in forced_set:
            forced_set.add(x)
            forced.append(x)

    for m in _find_winning_moves(board, val, orient, limit=10):
        add_forced(m)
    for m in _find_winning_moves(board, -val, enemy_orient, limit=10):
        add_forced(m)

    if len(empties) <= maxn:
        ordered = sorted(empties, key=lambda i: (0 if i in forced_set else 1, CENTER_DIST[i], i))
        return ordered

    my_total, my_s, my_e, my_w = _dist_info(board, val, orient, weighted=False)
    en_total, en_s, en_e, en_w = _dist_info(board, -val, enemy_orient, weighted=False)

    played = NN - len(empties)
    scored = []

    for i in empties:
        if i in forced_set:
            continue

        s = 0.0

        if my_s[i] < INF and my_e[i] < INF:
            through = my_s[i] + my_e[i] - my_w[i]
            gap = through - my_total
            if gap <= 0:
                s += 180
            elif gap <= 1:
                s += 120
            elif gap <= 2:
                s += 70
            elif gap <= 3:
                s += 35

        if en_s[i] < INF and en_e[i] < INF:
            through = en_s[i] + en_e[i] - en_w[i]
            gap = through - en_total
            if gap <= 0:
                s += 200
            elif gap <= 1:
                s += 130
            elif gap <= 2:
                s += 75
            elif gap <= 3:
                s += 38

        own_n = 0
        enemy_n = 0
        for nb in NEIGH[i]:
            if board[nb] == val:
                own_n += 1
            elif board[nb] == -val:
                enemy_n += 1

        s += own_n * 12
        s += enemy_n * 10

        if own_n + enemy_n == 0:
            s -= 35 if played > 4 else 5

        s += (10 - CENTER_DIST[i]) * 4

        s += _bridge_completion_count(board, i, val) * 22
        s += _bridge_completion_count(board, i, -val) * 24
        s += _bridge_formation_count(board, i, val) * 16
        s += _bridge_formation_count(board, i, -val) * 8

        scored.append((s, i))

    scored.sort(key=lambda x: (-x[0], CENTER_DIST[x[1]], x[1]))

    out = list(forced)
    for _, i in scored:
        if len(out) >= maxn:
            break
        out.append(i)

    return out


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    if color not in ("b", "w"):
        color = "b"

    opp_color = _other_color(color)

    board = [0] * NN

    for r, c in opp:
        if _on_board(r, c):
            board[_idx(r, c)] = -1

    for r, c in me:
        if _on_board(r, c):
            board[_idx(r, c)] = 1

    empties = [i for i in range(NN) if board[i] == 0]
    if not empties:
        return (0, 0)

    played = NN - len(empties)

    # Opening: take the centre, or contest it if the opponent took it.
    if played == 0 and board[CENTER] == 0:
        return COORDS[CENTER]

    if len(me) == 0 and len(opp) <= 1:
        if board[CENTER] == 0:
            return COORDS[CENTER]

        if color == "b":
            pref = [(4, 5), (6, 5), (4, 6), (6, 4), (5, 4), (5, 6), (3, 5), (7, 5)]
        else:
            pref = [(5, 4), (5, 6), (4, 6), (6, 4), (4, 5), (6, 5), (5, 3), (5, 7)]

        for r, c in pref:
            i = _idx(r, c)
            if board[i] == 0:
                return (r, c)

    # Tactical must-play checks.
    my_wins = _find_winning_moves(board, 1, color, limit=20)
    if my_wins:
        return COORDS[my_wins[0]]

    opp_wins = _find_winning_moves(board, -1, opp_color, limit=20)
    if len(opp_wins) == 1:
        return COORDS[opp_wins[0]]

    start_time = time.monotonic()
    deadline = start_time + 0.86

    if played < 20:
        root_max = 26
        search_max = 16
        reply_max = 10
    elif played < 70:
        root_max = 30
        search_max = 18
        reply_max = 12
    else:
        root_max = 42
        search_max = 24
        reply_max = 16

    root_candidates = _generate_candidates(board, 1, color, opp_color, root_max)

    if not root_candidates:
        fallback = _central_empty(board)
        if fallback is None:
            return (0, 0)
        return COORDS[fallback]

    # First rank candidate moves statically.
    scored = []
    for m in root_candidates:
        if board[m] != 0:
            continue
        board[m] = 1
        if _has_connection(board, 1, color):
            board[m] = 0
            return COORDS[m]
        sc = _static_eval(board, color, opp_color, turn_val=-1)
        board[m] = 0
        scored.append((sc, m))

        if time.monotonic() > deadline:
            break

    if not scored:
        fallback = _central_empty(board)
        if fallback is None:
            return (0, 0)
        return COORDS[fallback]

    scored.sort(key=lambda x: x[0], reverse=True)

    best_idx = scored[0][1]
    best_score = -float("inf")

    # Shallow minimax: choose the move with the best worst opponent reply.
    for first_sc, m in scored[:search_max]:
        if time.monotonic() > deadline:
            break

        if board[m] != 0:
            continue

        board[m] = 1

        replies = _generate_candidates(board, -1, opp_color, color, reply_max)
        if not replies:
            value = first_sc
        else:
            worst = float("inf")
            evaluated_reply = False

            for rmove in replies:
                if time.monotonic() > deadline:
                    break
                if board[rmove] != 0:
                    continue

                board[rmove] = -1

                if _has_connection(board, -1, opp_color):
                    sc = -WIN_SCORE
                else:
                    sc = _static_eval(board, color, opp_color, turn_val=1)

                board[rmove] = 0
                evaluated_reply = True

                if sc < worst:
                    worst = sc

            if evaluated_reply:
                value = worst + 0.04 * first_sc
            else:
                value = first_sc

        board[m] = 0

        if value > best_score:
            best_score = value
            best_idx = m

    if best_idx is None or board[best_idx] != 0:
        fallback = _central_empty(board)
        if fallback is None:
            return (0, 0)
        best_idx = fallback

    return COORDS[best_idx]
