
import time
import math
import heapq
import random
from collections import deque

N = 11
NN = N * N
MID = N // 2
INF = 10 ** 9
FINF = 1e9
WIN_SCORE = 1_000_000.0

OFFS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))
OPP = {"b": "w", "w": "b"}

ROWS = [i // N for i in range(NN)]
COLS = [i % N for i in range(NN)]


def _idx(r, c):
    return r * N + c


NEI = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in OFFS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(_idx(rr, cc))
        NEI.append(tuple(ns))

NEI_SET = [set(x) for x in NEI]

SIDES = {
    "b": (
        tuple(_idx(0, c) for c in range(N)),
        tuple(_idx(N - 1, c) for c in range(N)),
    ),
    "w": (
        tuple(_idx(r, 0) for r in range(N)),
        tuple(_idx(r, N - 1) for r in range(N)),
    ),
}

SIDE_BOOL = {}
for col in ("b", "w"):
    for side in (0, 1):
        arr = [False] * NN
        for x in SIDES[col][side]:
            arr[x] = True
        SIDE_BOOL[(col, side)] = arr

CENTER_ORDER = tuple(
    sorted(
        range(NN),
        key=lambda i: (
            abs(ROWS[i] - MID) + abs(COLS[i] - MID),
            (ROWS[i] - MID) ** 2 + (COLS[i] - MID) ** 2,
            i,
        ),
    )
)

CAND_POS = {"b": [0.0] * NN, "w": [0.0] * NN}
STONE_POS = {"b": [0.0] * NN, "w": [0.0] * NN}
for i in range(NN):
    r, c = ROWS[i], COLS[i]
    CAND_POS["b"][i] = 10.0 - 1.35 * abs(c - MID) - 0.25 * abs(r - MID)
    CAND_POS["w"][i] = 10.0 - 1.35 * abs(r - MID) - 0.25 * abs(c - MID)
    STONE_POS["b"][i] = 2.0 * (MID - abs(c - MID)) + 0.35 * (MID - abs(r - MID))
    STONE_POS["w"][i] = 2.0 * (MID - abs(r - MID)) + 0.35 * (MID - abs(c - MID))


def _pref(seq):
    out = []
    seen = set()
    for r, c in seq:
        if 0 <= r < N and 0 <= c < N:
            i = _idx(r, c)
            if i not in seen:
                out.append(i)
                seen.add(i)
    return tuple(out)


OPENING_PREFS = {
    "b": _pref(
        [
            (5, 5),
            (4, 5),
            (6, 5),
            (5, 4),
            (5, 6),
            (4, 6),
            (6, 4),
            (3, 5),
            (7, 5),
            (4, 4),
            (6, 6),
            (5, 3),
            (5, 7),
        ]
    ),
    "w": _pref(
        [
            (5, 5),
            (5, 4),
            (5, 6),
            (4, 5),
            (6, 5),
            (6, 4),
            (4, 6),
            (5, 3),
            (5, 7),
            (4, 4),
            (6, 6),
            (3, 5),
            (7, 5),
        ]
    ),
}

# Hex bridge templates: two non-adjacent cells with exactly two common neighbors.
BRIDGE_TRIPLES = []
BRIDGE_LINKS = [[] for _ in range(NN)]
for a in range(NN):
    for b in range(a + 1, NN):
        if b in NEI_SET[a]:
            continue
        common = NEI_SET[a].intersection(NEI_SET[b])
        if len(common) == 2:
            c1, c2 = tuple(common)
            BRIDGE_TRIPLES.append((a, b, c1, c2))
            BRIDGE_LINKS[a].append((b, c1, c2))
            BRIDGE_LINKS[b].append((a, c1, c2))

# Virtual bridge-to-edge templates.
SIDE_BRIDGES = {("b", 0): [], ("b", 1): [], ("w", 0): [], ("w", 1): []}
for c in range(N - 1):
    SIDE_BRIDGES[("b", 0)].append((_idx(1, c), _idx(0, c), _idx(0, c + 1)))
for c in range(1, N):
    SIDE_BRIDGES[("b", 1)].append((_idx(N - 2, c), _idx(N - 1, c - 1), _idx(N - 1, c)))
for r in range(N - 1):
    SIDE_BRIDGES[("w", 0)].append((_idx(r, 1), _idx(r, 0), _idx(r + 1, 0)))
for r in range(1, N):
    SIDE_BRIDGES[("w", 1)].append((_idx(r, N - 2), _idx(r - 1, N - 1), _idx(r, N - 1)))


def legal_fallback(own, enemy):
    occ = own | enemy
    for i in CENTER_ORDER:
        if i not in occ:
            return i
    return None


def has_connection(stones, color):
    starts = [i for i in SIDES[color][0] if i in stones]
    if not starts:
        return False
    target = SIDE_BOOL[(color, 1)]
    seen = set(starts)
    stack = starts[:]
    while stack:
        u = stack.pop()
        if target[u]:
            return True
        for v in NEI[u]:
            if v in stones and v not in seen:
                seen.add(v)
                stack.append(v)
    return False


def zero_one_dist(own, enemy, color, side=0):
    dist = [INF] * NN
    dq = deque()

    for i in SIDES[color][side]:
        if i in enemy:
            continue
        w = 0 if i in own else 1
        if w < dist[i]:
            dist[i] = w
            if w == 0:
                dq.appendleft(i)
            else:
                dq.append(i)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEI[u]:
            if v in enemy:
                continue
            w = 0 if v in own else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return dist


def shortest_distance_int(own, enemy, color):
    dist = zero_one_dist(own, enemy, color, 0)
    return min(dist[i] for i in SIDES[color][1])


def shortest_info(own, enemy, color):
    ds = zero_one_dist(own, enemy, color, 0)
    dt = zero_one_dist(own, enemy, color, 1)
    best = min(ds[i] for i in SIDES[color][1])
    return ds, dt, best


def immediate_winning_moves(own, enemy, color, empties=None):
    if empties is None:
        occ = own | enemy
        empties = [i for i in range(NN) if i not in occ]

    ds, dt, d = shortest_info(own, enemy, color)
    if d != 1:
        return []

    wins = []
    for i in empties:
        if ds[i] < INF and dt[i] < INF and ds[i] + dt[i] - 1 == 1:
            wins.append(i)
    return wins


def make_weights(own, enemy, color):
    occ = own | enemy
    weights = [1.0] * NN

    for i in range(NN):
        if i in occ:
            weights[i] = 0.0 if i in own else FINF
            continue

        r, c = ROWS[i], COLS[i]
        lateral = abs(c - MID) if color == "b" else abs(r - MID)
        w = 1.0 + 0.025 * lateral

        ao = ae = 0
        for nb in NEI[i]:
            if nb in own:
                ao += 1
            elif nb in enemy:
                ae += 1

        w -= 0.045 * min(ao, 4)
        w += 0.015 * min(ae, 4)

        if color == "b" and (r == 0 or r == N - 1):
            w -= 0.03
        elif color == "w" and (c == 0 or c == N - 1):
            w -= 0.03

        if w < 0.45:
            w = 0.45
        elif w > 1.22:
            w = 1.22
        weights[i] = w

    # Make bridge repair/maintenance cells cheaper for this player's connection estimate.
    for a, b, c1, c2 in BRIDGE_TRIPLES:
        if a in own and b in own:
            c1_empty = c1 not in occ
            c2_empty = c2 not in occ
            if c1_empty and c2_empty:
                weights[c1] = min(weights[c1], 0.58)
                weights[c2] = min(weights[c2], 0.58)
            elif c1 in enemy and c2_empty:
                weights[c2] = min(weights[c2], 0.34)
            elif c2 in enemy and c1_empty:
                weights[c1] = min(weights[c1], 0.34)

    for side in (0, 1):
        for stone, c1, c2 in SIDE_BRIDGES[(color, side)]:
            if stone in own:
                c1_empty = c1 not in occ
                c2_empty = c2 not in occ
                if c1_empty and c2_empty:
                    weights[c1] = min(weights[c1], 0.56)
                    weights[c2] = min(weights[c2], 0.56)
                elif c1 in enemy and c2_empty:
                    weights[c2] = min(weights[c2], 0.36)
                elif c2 in enemy and c1_empty:
                    weights[c1] = min(weights[c1], 0.36)

    return weights


def weighted_dist_from_side(own, enemy, color, side, weights):
    dist = [FINF] * NN
    heap = []

    def push(i, d):
        if d + 1e-9 < dist[i]:
            dist[i] = d
            heapq.heappush(heap, (d, i))

    for i in SIDES[color][side]:
        if i in enemy:
            continue
        push(i, 0.0 if i in own else weights[i])

    # Virtual side bridges.
    for stone, c1, c2 in SIDE_BRIDGES[(color, side)]:
        if stone in own and c1 not in enemy and c2 not in enemy:
            push(stone, 0.08)

    while heap:
        du, u = heapq.heappop(heap)
        if du > dist[u] + 1e-9:
            continue

        for v in NEI[u]:
            if v in enemy:
                continue
            nd = du + (0.0 if v in own else weights[v])
            if nd + 1e-9 < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

        # Virtual stone-to-stone bridges.
        if u in own:
            for v, c1, c2 in BRIDGE_LINKS[u]:
                if v in own and c1 not in enemy and c2 not in enemy:
                    bridge_cost = 0.0 if (c1 in own or c2 in own) else 0.08
                    nd = du + bridge_cost
                    if nd + 1e-9 < dist[v]:
                        dist[v] = nd
                        heapq.heappush(heap, (nd, v))

    return dist


def weighted_connection_distance(own, enemy, color):
    weights = make_weights(own, enemy, color)
    dist = weighted_dist_from_side(own, enemy, color, 0, weights)

    best = min(dist[i] for i in SIDES[color][1])
    for stone, c1, c2 in SIDE_BRIDGES[(color, 1)]:
        if stone in own and c1 not in enemy and c2 not in enemy:
            best = min(best, dist[stone] + 0.08)

    if best >= FINF / 2:
        return 80.0
    return best


def two_side_distance(own, enemy, color, side):
    vals = [FINF] * NN
    side_bool = SIDE_BOOL[(color, side)]

    for _ in range(64):
        changed = False
        for i in range(NN):
            if i in enemy:
                continue

            first = second = FINF
            if side_bool[i]:
                first = second = 0.0

            for nb in NEI[i]:
                v = vals[nb]
                if v < first:
                    second = first
                    first = v
                elif v < second:
                    second = v

            if i in own:
                new = first
            else:
                new = 1.0 + second

            if new + 1e-9 < vals[i]:
                vals[i] = new
                changed = True

        if not changed:
            break

    return vals


def two_connection_distance(own, enemy, color):
    vals = two_side_distance(own, enemy, color, 0)
    best = min(vals[i] for i in SIDES[color][1])
    if best >= FINF / 2:
        return 80.0
    return best


def component_maps(stones, color):
    comp = {}
    flags = []
    seen = set()

    for s in stones:
        if s in seen:
            continue

        cid = len(flags)
        f0 = f1 = False
        stack = [s]
        seen.add(s)

        while stack:
            u = stack.pop()
            comp[u] = cid
            if SIDE_BOOL[(color, 0)][u]:
                f0 = True
            if SIDE_BOOL[(color, 1)][u]:
                f1 = True

            for v in NEI[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    stack.append(v)

        flags.append((f0, f1))

    return comp, flags


def connection_potential(i, comp, flags, color):
    seen = set()
    f0 = SIDE_BOOL[(color, 0)][i]
    f1 = SIDE_BOOL[(color, 1)][i]

    for nb in NEI[i]:
        cid = comp.get(nb)
        if cid is not None and cid not in seen:
            seen.add(cid)
            cf0, cf1 = flags[cid]
            f0 = f0 or cf0
            f1 = f1 or cf1

    k = len(seen)
    bonus = 0.0
    if k:
        bonus += 3.0 * k
    if k >= 2:
        bonus += 14.0 * (k - 1)
    if k and (SIDE_BOOL[(color, 0)][i] or SIDE_BOOL[(color, 1)][i]):
        bonus += 8.0
    if f0 and f1:
        bonus += 250.0
    elif f0 or f1:
        bonus += 6.0

    return bonus


def bridge_bonus(own, enemy, color):
    occ = own | enemy
    bonus = {}

    def add(i, v):
        if i not in occ:
            bonus[i] = bonus.get(i, 0.0) + v

    for a, b, c1, c2 in BRIDGE_TRIPLES:
        if a in own and b in own:
            c1_empty = c1 not in occ
            c2_empty = c2 not in occ
            if c1_empty and c2_empty:
                add(c1, 10.0)
                add(c2, 10.0)
            elif c1 in enemy and c2_empty:
                add(c2, 88.0)
            elif c2 in enemy and c1_empty:
                add(c1, 88.0)

    for side in (0, 1):
        for stone, c1, c2 in SIDE_BRIDGES[(color, side)]:
            if stone in own:
                c1_empty = c1 not in occ
                c2_empty = c2 not in occ
                if c1_empty and c2_empty:
                    add(c1, 9.0)
                    add(c2, 9.0)
                elif c1 in enemy and c2_empty:
                    add(c2, 80.0)
                elif c2 in enemy and c1_empty:
                    add(c1, 80.0)

    return bonus


def group_strength(stones, color):
    if not stones:
        return 0.0

    seen = set()
    best = 0.0
    total = 0.0

    for s in stones:
        if s in seen:
            continue

        stack = [s]
        seen.add(s)
        size = 0
        lo = 99
        hi = -1
        touch0 = touch1 = False

        while stack:
            u = stack.pop()
            size += 1
            axis = ROWS[u] if color == "b" else COLS[u]
            lo = min(lo, axis)
            hi = max(hi, axis)
            if SIDE_BOOL[(color, 0)][u]:
                touch0 = True
            if SIDE_BOOL[(color, 1)][u]:
                touch1 = True

            for v in NEI[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    stack.append(v)

        span = hi - lo + 1
        val = 8.0 * span + 1.7 * math.sqrt(size)
        if touch0:
            val += 8.0
        if touch1:
            val += 8.0

        best = max(best, val)
        total += 0.25 * val

    return best + total


def positional_sum(stones, color):
    return sum(STONE_POS[color][i] for i in stones)


def evaluate_details(my, op, my_color, full=False):
    op_color = OPP[my_color]

    my_d = shortest_distance_int(my, op, my_color)
    op_d = shortest_distance_int(op, my, op_color)

    if my_d == 0:
        return WIN_SCORE, my_d, op_d
    if op_d == 0:
        return -WIN_SCORE, my_d, op_d

    md = min(my_d, 50)
    od = min(op_d, 50)

    score = 1120.0 * (od - md)

    if my_d == 1:
        score += 700.0
    elif my_d == 2:
        score += 130.0

    if op_d == 1:
        score -= 900.0
    elif op_d == 2:
        score -= 165.0

    my_w = weighted_connection_distance(my, op, my_color)
    op_w = weighted_connection_distance(op, my, op_color)
    score += 165.0 * (op_w - my_w)

    if full:
        my_two = two_connection_distance(my, op, my_color)
        op_two = two_connection_distance(op, my, op_color)
        score += 28.0 * (op_two - my_two)

    score += 4.5 * (group_strength(my, my_color) - group_strength(op, op_color))
    score += 0.55 * (positional_sum(my, my_color) - positional_sum(op, op_color))

    return score, my_d, op_d


def basic_move_score(i, own, enemy, color):
    s = CAND_POS[color][i]
    ao = ae = 0
    for nb in NEI[i]:
        if nb in own:
            ao += 1
        elif nb in enemy:
            ae += 1
    s += 6.0 * ao + 3.8 * ae
    return s


def order_subset(cands, own, enemy, color):
    return sorted(cands, key=lambda x: basic_move_score(x, own, enemy, color), reverse=True)


def candidate_moves(own, enemy, color, limit=30):
    occ = own | enemy
    empties = [i for i in range(NN) if i not in occ]
    if not empties:
        return []

    wins = immediate_winning_moves(own, enemy, color, empties)
    if wins:
        return order_subset(wins, own, enemy, color)[: max(1, min(len(wins), limit))]

    enemy_color = OPP[color]
    enemy_wins = immediate_winning_moves(enemy, own, enemy_color, empties)
    if enemy_wins:
        # If the opponent threatens an immediate win, legal blocks dominate all non-blocks.
        return order_subset(enemy_wins, own, enemy, color)

    my_ds, my_dt, my_d = shortest_info(own, enemy, color)
    op_ds, op_dt, op_d = shortest_info(enemy, own, enemy_color)

    my_bridge = bridge_bonus(own, enemy, color)
    op_bridge = bridge_bonus(enemy, own, enemy_color)

    my_comp, my_flags = component_maps(own, color)
    op_comp, op_flags = component_maps(enemy, enemy_color)

    scores = {}
    for i in empties:
        s = CAND_POS[color][i]

        if my_d < INF and my_ds[i] < INF and my_dt[i] < INF:
            through = my_ds[i] + my_dt[i] - 1
            gap = through - my_d
            if gap <= 3:
                att_w = 78.0 + 12.0 * max(0, min(4, op_d - my_d))
                s += att_w / (1.0 + max(0, gap)) + 16.0 * max(0, 3 - gap)
            if my_d <= 2 and gap <= 1:
                s += 65.0

        if op_d < INF and op_ds[i] < INF and op_dt[i] < INF:
            through = op_ds[i] + op_dt[i] - 1
            gap = through - op_d
            if gap <= 3:
                def_w = 84.0 + 18.0 * max(0, min(4, my_d - op_d + 1))
                s += def_w / (1.0 + max(0, gap)) + 14.0 * max(0, 3 - gap)
            if op_d <= 2 and gap <= 1:
                s += 90.0

        ao = ae = 0
        for nb in NEI[i]:
            if nb in own:
                ao += 1
            elif nb in enemy:
                ae += 1

        s += 5.2 * ao + 3.4 * ae
        if ao == 0 and own:
            s -= 2.5

        s += 1.25 * connection_potential(i, my_comp, my_flags, color)
        s += 1.05 * connection_potential(i, op_comp, op_flags, enemy_color)

        s += my_bridge.get(i, 0.0)
        s += 0.88 * op_bridge.get(i, 0.0)

        scores[i] = s

    ordered = sorted(empties, key=lambda x: scores[x], reverse=True)
    return ordered[: min(limit, len(ordered))]


def board_seed(own, enemy, color):
    mask = (1 << 64) - 1
    seed = 0x9E3779B97F4A7C15 ^ (1 if color == "b" else 2)
    for i in sorted(own):
        seed ^= (i + 1) * 0xBF58476D1CE4E5B9
        seed = (seed * 0x94D049BB133111EB) & mask
    for i in sorted(enemy):
        seed ^= (i + 17) * 0xD6E8FEB86659FD93
        seed = (seed * 0x94D049BB133111EB) & mask
    return seed & mask


def playout_probability(my_after, op, color, rng, samples, deadline):
    occ = my_after | op
    empties = [i for i in range(NN) if i not in occ]
    if not empties:
        return (1.0 if has_connection(my_after, color) else 0.0), 1

    wins = 0
    done = 0

    for _ in range(samples):
        if time.perf_counter() > deadline:
            break

        arr = empties[:]
        rng.shuffle(arr)

        my_final = set(my_after)
        op_final = set(op)

        # After our candidate move, opponent moves first.
        op_final.update(arr[0::2])
        my_final.update(arr[1::2])

        if has_connection(my_final, color):
            wins += 1
        done += 1

    if done == 0:
        return 0.5, 0
    return wins / done, done


def choose_move(own, enemy, color, deadline):
    occ = own | enemy
    empties = [i for i in range(NN) if i not in occ]
    fallback = legal_fallback(own, enemy)
    if fallback is None:
        return 0

    # Opening: take the center or an orientation-aware nearby point.
    if len(own) == 0 and len(enemy) <= 1:
        for i in OPENING_PREFS[color]:
            if i not in occ:
                return i
        return fallback

    # Immediate tactical obligations.
    wins = immediate_winning_moves(own, enemy, color, empties)
    if wins:
        return order_subset(wins, own, enemy, color)[0]

    enemy_color = OPP[color]
    blocks = immediate_winning_moves(enemy, own, enemy_color, empties)
    if len(blocks) == 1:
        return blocks[0]

    move_count = len(occ)
    if move_count < 12:
        root_limit = 22
        opp_limit = 10
    elif move_count < 70:
        root_limit = 30
        opp_limit = 12
    else:
        root_limit = min(42, len(empties))
        opp_limit = 16

    if blocks:
        cands = order_subset(blocks, own, enemy, color)
    else:
        cands = candidate_moves(own, enemy, color, root_limit)
        if fallback not in cands:
            cands.append(fallback)

    if not cands:
        return fallback

    best = cands[0]
    best_score = -FINF
    results = []

    for ci, m in enumerate(cands):
        if time.perf_counter() > deadline:
            break

        my2 = set(own)
        my2.add(m)

        if has_connection(my2, color):
            return m

        full_eval = ci < 8 and time.perf_counter() < deadline - 0.10
        q, md, od = evaluate_details(my2, enemy, color, full=full_eval)

        # If opponent has an immediate win after our move, this move is almost always losing.
        if od == 1:
            val = -0.45 * WIN_SCORE + q
        else:
            ocands = candidate_moves(enemy, my2, enemy_color, opp_limit)
            if not ocands:
                val = q
            else:
                worst = FINF
                saw_child = False

                for om in ocands:
                    if time.perf_counter() > deadline:
                        break
                    saw_child = True

                    op2 = set(enemy)
                    op2.add(om)

                    if has_connection(op2, enemy_color):
                        child = -WIN_SCORE
                    else:
                        child, cmd, cod = evaluate_details(my2, op2, color, full=False)

                        # It is our turn after this child. If we have an immediate win, that is decisive.
                        if cmd == 1:
                            child += 0.35 * WIN_SCORE
                        elif cod == 1:
                            child -= 450.0
                            if time.perf_counter() < deadline - 0.025:
                                ow = immediate_winning_moves(op2, my2, enemy_color)
                                if len(ow) >= 2:
                                    child -= 0.18 * WIN_SCORE

                    if child < worst:
                        worst = child

                    if worst < best_score - 1800.0:
                        break

                if not saw_child:
                    worst = q

                val = 0.72 * worst + 0.28 * q

        # Reward moves that create multiple immediate winning threats.
        if md == 1 and od > 1 and time.perf_counter() < deadline - 0.03:
            nxt = immediate_winning_moves(my2, enemy, color)
            if len(nxt) >= 2:
                val += 0.20 * WIN_SCORE

        results.append((val, m, q))

        if val > best_score:
            best_score = val
            best = m

    # Small deterministic flat Monte Carlo tie-break among the top heuristic choices.
    if results and not blocks and time.perf_counter() < deadline - 0.11:
        rng = random.Random(board_seed(own, enemy, color))
        top = sorted(results, key=lambda x: x[0], reverse=True)[: min(5, len(results))]
        mc_best = best
        mc_best_score = best_score

        samples = 10 if move_count < 50 else 5
        for val, m, _ in top:
            if time.perf_counter() > deadline - 0.035:
                break

            my2 = set(own)
            my2.add(m)

            # Do not let random playouts rescue a tactically losing move.
            if shortest_distance_int(enemy, my2, enemy_color) == 1:
                continue

            p, n = playout_probability(my2, enemy, color, rng, samples, deadline - 0.02)
            if n:
                adjusted = val + (p - 0.5) * 260.0
                if adjusted > mc_best_score:
                    mc_best_score = adjusted
                    mc_best = m

        best = mc_best

    if best is None or best in own or best in enemy or not (0 <= best < NN):
        best = fallback
    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    own = set()
    enemy = set()

    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            own.add(_idx(r, c))

    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            enemy.add(_idx(r, c))

    color = "b" if color == "b" else "w"
    fallback = legal_fallback(own, enemy)
    if fallback is None:
        # A full board should never be queried, but keep the function total.
        return (0, 0)

    try:
        deadline = time.perf_counter() + 0.92
        move = choose_move(own, enemy, color, deadline)
    except Exception:
        move = fallback

    if move is None or move in own or move in enemy or not (0 <= move < NN):
        move = fallback

    return (ROWS[move], COLS[move])
