
from collections import deque

N = 11
NN = N * N
CENTER = N // 2
INF = 10 ** 9
WIN_SCORE = 10 ** 7

DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))

BITS = [1 << i for i in range(NN)]
FULL_MASK = (1 << NN) - 1
RC = [(i // N, i % N) for i in range(NN)]

NEIGH = [[] for _ in range(NN)]
for r in range(N):
    for c in range(N):
        i = r * N + c
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                NEIGH[i].append(rr * N + cc)

START = {
    "b": [0 * N + c for c in range(N)],
    "w": [r * N + 0 for r in range(N)],
}
END = {
    "b": [(N - 1) * N + c for c in range(N)],
    "w": [r * N + (N - 1) for r in range(N)],
}
START_MASK = {
    "b": sum(BITS[i] for i in START["b"]),
    "w": sum(BITS[i] for i in START["w"]),
}
END_MASK = {
    "b": sum(BITS[i] for i in END["b"]),
    "w": sum(BITS[i] for i in END["w"]),
}

# Bridge templates: two non-adjacent cells with exactly two common adjacent cells.
BRIDGES = [[] for _ in range(NN)]
CARRIER_PAIRS = [[] for _ in range(NN)]
_seen_pairs = set()

for a in range(NN):
    neigh_a = set(NEIGH[a])
    for x in NEIGH[a]:
        for b in NEIGH[x]:
            if b == a or b in neigh_a:
                continue
            common = sorted(neigh_a.intersection(NEIGH[b]))
            if len(common) == 2:
                aa, bb = (a, b) if a < b else (b, a)
                if (aa, bb) not in _seen_pairs:
                    _seen_pairs.add((aa, bb))
                    c1, c2 = common
                    cm = BITS[c1] | BITS[c2]
                    BRIDGES[aa].append((bb, cm))
                    BRIDGES[bb].append((aa, cm))
                    CARRIER_PAIRS[c1].append((aa, bb, BITS[c2]))
                    CARRIER_PAIRS[c2].append((aa, bb, BITS[c1]))

# Edge virtual templates.  Side 0 is start side, side 1 is end side.
EDGE_VIRTUAL = {
    "b": [[0] * NN, [0] * NN],
    "w": [[0] * NN, [0] * NN],
}

for i, (r, c) in enumerate(RC):
    # Black top virtual connection: stone at row 1 touches two top cells.
    if r == 1 and c + 1 < N:
        EDGE_VIRTUAL["b"][0][i] = BITS[0 * N + c] | BITS[0 * N + c + 1]

    # Black bottom virtual connection: stone at row N-2 touches two bottom cells.
    if r == N - 2 and c - 1 >= 0:
        EDGE_VIRTUAL["b"][1][i] = BITS[(N - 1) * N + c] | BITS[(N - 1) * N + c - 1]

    # White left virtual connection: stone at col 1 touches two left-edge cells.
    if c == 1 and r + 1 < N:
        EDGE_VIRTUAL["w"][0][i] = BITS[r * N + 0] | BITS[(r + 1) * N + 0]

    # White right virtual connection: stone at col N-2 touches two right-edge cells.
    if c == N - 2 and r - 1 >= 0:
        EDGE_VIRTUAL["w"][1][i] = BITS[r * N + (N - 1)] | BITS[(r - 1) * N + (N - 1)]


def _other(color):
    return "w" if color == "b" else "b"


def _idx(r, c):
    return r * N + c


def _iter_bits(mask):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def _to_mask(stones):
    m = 0
    for r, c in stones:
        if 0 <= r < N and 0 <= c < N:
            m |= BITS[r * N + c]
    return m


def _conn_dist(player, blocker, color, virtual, cache):
    key = (player, blocker, color, 1 if virtual else 0)
    old = cache.get(key)
    if old is not None:
        return old

    dist = [INF] * NN
    dq = deque()

    def add(v, d):
        if d < dist[v]:
            dist[v] = d
            if d == 0:
                dq.appendleft(v)
            else:
                dq.append(v)

    # Real start-side entry.
    for s in START[color]:
        if not (blocker & BITS[s]):
            add(s, 0 if (player & BITS[s]) else 1)

    # Virtual edge connection to start side.
    if virtual:
        pm = player
        ev_start = EDGE_VIRTUAL[color][0]
        while pm:
            b = pm & -pm
            i = b.bit_length() - 1
            pm ^= b
            cm = ev_start[i]
            if cm and not (blocker & cm):
                add(i, 0)

    while dq:
        u = dq.popleft()
        du = dist[u]

        for v in NEIGH[u]:
            bv = BITS[v]
            if blocker & bv:
                continue
            nd = du if (player & bv) else du + 1
            if nd < dist[v]:
                dist[v] = nd
                if player & bv:
                    dq.appendleft(v)
                else:
                    dq.append(v)

        # Virtual bridge between own stones, if both bridge carriers are unblocked.
        if virtual and (player & BITS[u]):
            for v, cm in BRIDGES[u]:
                if (player & BITS[v]) and not (blocker & cm):
                    if du < dist[v]:
                        dist[v] = du
                        dq.appendleft(v)

    best = INF
    for g in END[color]:
        if not (blocker & BITS[g]) and dist[g] < best:
            best = dist[g]

    # Virtual edge connection to end side.
    if virtual:
        pm = player
        ev_end = EDGE_VIRTUAL[color][1]
        while pm:
            b = pm & -pm
            i = b.bit_length() - 1
            pm ^= b
            cm = ev_end[i]
            if cm and not (blocker & cm) and dist[i] < best:
                best = dist[i]

    cache[key] = best
    return best


def _winning_moves(player, blocker, color, empty, cache):
    # If the current shortest real completion needs more than one empty cell,
    # there is no immediate winning move.
    if _conn_dist(player, blocker, color, False, cache) > 1:
        return []

    wins = []
    em = empty
    while em:
        b = em & -em
        i = b.bit_length() - 1
        em ^= b
        if _conn_dist(player | b, blocker, color, False, cache) == 0:
            wins.append(i)
    return wins


def _local_score(i, player, blocker, color):
    r, c = RC[i]
    score = 0.0

    # Central and lane preference.
    score += 5.0 * (N - 1 - abs(r - CENTER) - abs(c - CENTER))
    if color == "b":
        score += 4.0 * (CENTER - abs(c - CENTER))
        if r == 0 or r == N - 1:
            score += 10.0
        elif r == 1 or r == N - 2:
            score += 6.0
    else:
        score += 4.0 * (CENTER - abs(r - CENTER))
        if c == 0 or c == N - 1:
            score += 10.0
        elif c == 1 or c == N - 2:
            score += 6.0

    adj_own = 0
    adj_opp = 0
    for nb in NEIGH[i]:
        bit = BITS[nb]
        if player & bit:
            adj_own += 1
        elif blocker & bit:
            adj_opp += 1

    score += 30.0 * adj_own + 9.0 * adj_own * adj_own
    score += 5.0 * adj_opp

    # Playing as one endpoint of a bridge to an existing own stone.
    for v, cm in BRIDGES[i]:
        if (player & BITS[v]) and not (blocker & cm):
            score += 48.0
            if player & cm:
                score += 12.0

    # Playing as a carrier connecting/repairing a bridge between two own stones.
    for a, b, other_carrier_bit in CARRIER_PAIRS[i]:
        if (player & BITS[a]) and (player & BITS[b]):
            if blocker & other_carrier_bit:
                score += 210.0
            else:
                score += 90.0

    return score


def _position_eval(my, opp, color, cache):
    oc = _other(color)

    my_plain = _conn_dist(my, opp, color, False, cache)
    opp_plain = _conn_dist(opp, my, oc, False, cache)

    if my_plain == 0:
        return WIN_SCORE
    if opp_plain == 0:
        return -WIN_SCORE

    my_virtual = _conn_dist(my, opp, color, True, cache)
    opp_virtual = _conn_dist(opp, my, oc, True, cache)

    score = 5200.0 * (opp_virtual - my_virtual)
    score += 1500.0 * (opp_plain - my_plain)

    if my_plain == 1:
        score += 16000.0
    if opp_plain == 1:
        score -= 22000.0

    if my_virtual == 0:
        score += 3500.0
    if opp_virtual == 0:
        score -= 4500.0

    return score


def _move_score(i, my, opp, color, cache):
    bit = BITS[i]
    oc = _other(color)
    new_my = my | bit

    my_plain = _conn_dist(new_my, opp, color, False, cache)
    if my_plain == 0:
        return WIN_SCORE + _local_score(i, my, opp, color)

    opp_plain = _conn_dist(opp, new_my, oc, False, cache)
    my_virtual = _conn_dist(new_my, opp, color, True, cache)
    opp_virtual = _conn_dist(opp, new_my, oc, True, cache)

    score = 5200.0 * (opp_virtual - my_virtual)
    score += 1500.0 * (opp_plain - my_plain)

    if my_plain == 1:
        score += 18000.0

    # Never voluntarily allow an immediate opponent win unless everything loses.
    if opp_plain == 1:
        score -= 120000.0

    if my_virtual == 0:
        score += 4200.0
    if opp_virtual == 0:
        score -= 5200.0

    # Offense plus defense: cells valuable to the opponent are also valuable blocks.
    score += 5.5 * _local_score(i, my, opp, color)
    score += 4.0 * _local_score(i, opp, my, oc)

    # Stable deterministic tie-break toward the center.
    r, c = RC[i]
    score -= 0.01 * (abs(r - CENTER) + abs(c - CENTER))

    return score


def _fallback(empty):
    if empty:
        i = (empty & -empty).bit_length() - 1
        return RC[i]
    return (0, 0)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    if color not in ("b", "w"):
        color = "b"

    my = _to_mask(me)
    op = _to_mask(opp) & ~my
    occupied = my | op
    empty = FULL_MASK & ~occupied

    if not empty:
        return (0, 0)

    cache = {}

    # Opening: take the center when available.
    center_i = _idx(CENTER, CENTER)
    if occupied == 0 and (empty & BITS[center_i]):
        return (CENTER, CENTER)

    if (occupied.bit_count() <= 1) and (empty & BITS[center_i]):
        return (CENTER, CENTER)

    oc = _other(color)

    # Immediate win.
    my_wins = _winning_moves(my, op, color, empty, cache)
    if my_wins:
        best = max(my_wins, key=lambda x: _local_score(x, my, op, color))
        return RC[best]

    # Immediate block.
    opp_wins = _winning_moves(op, my, oc, empty, cache)
    if opp_wins:
        if len(opp_wins) == 1:
            return RC[opp_wins[0]]
        best = max(opp_wins, key=lambda x: _move_score(x, my, op, color, cache))
        return RC[best]

    # Score every legal move.
    scored = []
    em = empty
    while em:
        b = em & -em
        i = b.bit_length() - 1
        em ^= b
        scored.append((_move_score(i, my, op, color, cache), i))

    if not scored:
        return _fallback(empty)

    scored.sort(reverse=True)

    # Shallow minimax on the best root candidates.
    empties_count = empty.bit_count()
    if empties_count > 85:
        top_n = 9
    elif empties_count > 45:
        top_n = 11
    else:
        top_n = 14

    top = scored[:top_n]

    best_i = top[0][1]
    best_final = -INF

    for base, i in top:
        bit_i = BITS[i]
        new_my = my | bit_i

        if _conn_dist(new_my, op, color, False, cache) == 0:
            return RC[i]

        remaining = empty & ~bit_i

        # If this move permits an immediate opponent win, it is almost surely bad.
        if _conn_dist(op, new_my, oc, False, cache) == 1:
            final = -500000.0 + 0.01 * base
        else:
            worst = INF
            rem = remaining

            while rem:
                rb = rem & -rem
                j = rb.bit_length() - 1
                rem ^= rb

                new_op = op | rb

                if _conn_dist(new_op, new_my, oc, False, cache) == 0:
                    val = -WIN_SCORE
                else:
                    val = _position_eval(new_my, new_op, color, cache)
                    # Account for the opponent choosing locally strong moves.
                    val -= 3.0 * _local_score(j, op, new_my, oc)
                    val -= 1.4 * _local_score(j, new_my, op, color)

                if val < worst:
                    worst = val
                    if worst < best_final - 200000.0:
                        break

            final = 0.25 * base + 0.75 * worst

        if final > best_final:
            best_final = final
            best_i = i

    if empty & BITS[best_i]:
        return RC[best_i]

    return _fallback(empty)
