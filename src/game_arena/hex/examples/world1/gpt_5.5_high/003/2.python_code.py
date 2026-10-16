
import heapq
import time
from functools import lru_cache

N = 11
SIZE = N * N
INF = 10 ** 9
WIN = 10_000_000

# Hex adjacency for the coordinate system in the prompt:
# all 8 square-neighbors except NW and SE.
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))

BITS = tuple(1 << i for i in range(SIZE))
COORDS = tuple((i // N, i % N) for i in range(SIZE))

_neighbors = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        _neighbors.append(tuple(ns))
NEIGHBORS = tuple(_neighbors)

NEIGH_MASK = tuple(sum(BITS[j] for j in NEIGHBORS[i]) for i in range(SIZE))

TOP_IDXS = tuple(range(N))
BOTTOM_IDXS = tuple((N - 1) * N + c for c in range(N))
LEFT_IDXS = tuple(r * N for r in range(N))
RIGHT_IDXS = tuple(r * N + (N - 1) for r in range(N))

TOP_MASK = sum(BITS[i] for i in TOP_IDXS)
BOTTOM_MASK = sum(BITS[i] for i in BOTTOM_IDXS)
LEFT_MASK = sum(BITS[i] for i in LEFT_IDXS)
RIGHT_MASK = sum(BITS[i] for i in RIGHT_IDXS)

START_IDXS = {"b": TOP_IDXS, "w": LEFT_IDXS}
START_MASK = {"b": TOP_MASK, "w": LEFT_MASK}
GOAL_MASK = {"b": BOTTOM_MASK, "w": RIGHT_MASK}
OTHER = {"b": "w", "w": "b"}

# Hex distance from board center; useful as a mild centrality prior.
_center = N // 2
_cd = []
for i, (r, c) in enumerate(COORDS):
    dr, dc = r - _center, c - _center
    _cd.append((abs(dr) + abs(dc) + abs(dr + dc)) // 2)
CENTER_DIST = tuple(_cd)

# Base empty-cell weights for weighted Dijkstra.
# Wrong-side edges are mildly discouraged because they have fewer liberties.
_base_b = []
_base_w = []
for i, (r, c) in enumerate(COORDS):
    base = 100 + 3 * CENTER_DIST[i]

    wb = base
    if c == 0 or c == N - 1:
        wb += 10
    if (r == 0 or r == N - 1) and (c == 0 or c == N - 1):
        wb += 8
    _base_b.append(wb)

    ww = base
    if r == 0 or r == N - 1:
        ww += 10
    if (r == 0 or r == N - 1) and (c == 0 or c == N - 1):
        ww += 8
    _base_w.append(ww)

BASE_WEIGHT = {"b": tuple(_base_b), "w": tuple(_base_w)}

# For local scoring: pairs of neighbors of a cell that are not already adjacent.
# Playing the cell connects such pairs, often completing bridge-like shapes.
_nonadj_pairs = []
for i in range(SIZE):
    ns = NEIGHBORS[i]
    pairs = []
    for a_i in range(len(ns)):
        a = ns[a_i]
        for b in ns[a_i + 1:]:
            if not (NEIGH_MASK[a] & BITS[b]):
                pairs.append((BITS[a], BITS[b]))
    _nonadj_pairs.append(tuple(pairs))
NONADJ_PAIRS = tuple(_nonadj_pairs)


def _mask_from_points(points):
    m = 0
    for p in points:
        try:
            r, c = p
            r, c = int(r), int(c)
        except Exception:
            continue
        if 0 <= r < N and 0 <= c < N:
            m |= BITS[r * N + c]
    return m


def _legal_list(occ):
    return [i for i, b in enumerate(BITS) if not (occ & b)]


def _first_legal(occ):
    for i, b in enumerate(BITS):
        if not (occ & b):
            return i
    return 0


@lru_cache(maxsize=50000)
def _has_won(stones, color):
    """Connectivity win test using bitboard flood fill."""
    frontier = stones & START_MASK[color]
    seen = frontier
    goal = GOAL_MASK[color]

    while frontier:
        if seen & goal:
            return True

        f = frontier
        adj = 0
        while f:
            lsb = f & -f
            idx = lsb.bit_length() - 1
            adj |= NEIGH_MASK[idx]
            f ^= lsb

        frontier = adj & stones & ~seen
        seen |= frontier

    return bool(seen & goal)


def _make_weights(player, blocker, color):
    """Cell-entry weights for weighted Dijkstra from player's perspective."""
    base = BASE_WEIGHT[color]
    weights = [INF] * SIZE

    for i, b in enumerate(BITS):
        if blocker & b:
            continue
        if player & b:
            weights[i] = 0
        else:
            adj_player = (NEIGH_MASK[i] & player).bit_count()
            adj_blocker = (NEIGH_MASK[i] & blocker).bit_count()

            # Friendly adjacency and multi-neighbor connection potential lower cost.
            # Opponent adjacency slightly raises cost due to reduced liberties.
            w = base[i] - 14 * adj_player - 7 * max(0, adj_player - 1) + 5 * adj_blocker
            if w < 16:
                w = 16
            weights[i] = w

    return weights


@lru_cache(maxsize=50000)
def _shortest_weighted(player, blocker, color):
    """Weighted shortest connection cost for player; own stones cost 0."""
    weights = _make_weights(player, blocker, color)
    dist = [INF] * SIZE
    heap = []
    heappush = heapq.heappush
    heappop = heapq.heappop
    goal = GOAL_MASK[color]

    for i in START_IDXS[color]:
        w = weights[i]
        if w >= INF:
            continue
        dist[i] = w
        heappush(heap, (w, i))

    while heap:
        d, i = heappop(heap)
        if d != dist[i]:
            continue
        if BITS[i] & goal:
            return d

        for nb in NEIGHBORS[i]:
            w = weights[nb]
            if w >= INF:
                continue
            nd = d + w
            if nd < dist[nb]:
                dist[nb] = nd
                heappush(heap, (nd, nb))

    return INF // 2


@lru_cache(maxsize=50000)
def _shortest_exact(player, blocker, color):
    """Minimum number of empty cells needed to connect."""
    dist = [INF] * SIZE
    heap = []
    heappush = heapq.heappush
    heappop = heapq.heappop
    goal = GOAL_MASK[color]

    for i in START_IDXS[color]:
        b = BITS[i]
        if blocker & b:
            continue
        c = 0 if (player & b) else 1
        dist[i] = c
        heappush(heap, (c, i))

    while heap:
        d, i = heappop(heap)
        if d != dist[i]:
            continue
        if BITS[i] & goal:
            return d

        for nb in NEIGHBORS[i]:
            b = BITS[nb]
            if blocker & b:
                continue
            step = 0 if (player & b) else 1
            nd = d + step
            if nd < dist[nb]:
                dist[nb] = nd
                heappush(heap, (nd, nb))

    return INF // 2


def _winning_moves(stones, color, legal):
    return [i for i in legal if _has_won(stones | BITS[i], color)]


def _count_winning_moves(stones, color, occ, limit=2):
    count = 0
    for i, b in enumerate(BITS):
        if occ & b:
            continue
        if _has_won(stones | b, color):
            count += 1
            if count >= limit:
                return count
    return count


def _local_score(i, player, enemy, color):
    """Fast tactical/shape score for a candidate cell."""
    neigh = NEIGH_MASK[i]
    adj_p = (neigh & player).bit_count()
    adj_e = (neigh & enemy).bit_count()

    score = 24 * adj_p + 18 * adj_e
    score += 10 * adj_p * (adj_p - 1) // 2
    score += 8 * adj_e * (adj_e - 1) // 2

    if adj_p >= 2:
        for a, b in NONADJ_PAIRS[i]:
            if (player & a) and (player & b):
                score += 20

    if adj_e >= 2:
        for a, b in NONADJ_PAIRS[i]:
            if (enemy & a) and (enemy & b):
                score += 15

    r, c = COORDS[i]
    score -= 5 * CENTER_DIST[i]

    if color == "b":
        if c == 0 or c == N - 1:
            score -= 8
    else:
        if r == 0 or r == N - 1:
            score -= 8

    return score


def _evaluate_state(my, opp, color):
    """Static evaluation from my perspective, assuming it is my turn next."""
    opp_color = OTHER[color]

    if _has_won(my, color):
        return WIN
    if _has_won(opp, opp_color):
        return -WIN

    my_e = _shortest_exact(my, opp, color)
    opp_e = _shortest_exact(opp, my, opp_color)

    my_w = _shortest_weighted(my, opp, color)
    opp_w = _shortest_weighted(opp, my, opp_color)

    val = (opp_w - my_w) + 145 * (opp_e - my_e)

    # If it is our turn and we have an immediate win, this is nearly decisive.
    if my_e == 1:
        val += WIN // 3
    elif opp_e == 1:
        # One threat can usually be blocked; multiple immediate threats are very bad.
        cnt = _count_winning_moves(opp, opp_color, my | opp, 2)
        val -= 15000 if cnt >= 2 else 3000

    if my_e == 2:
        val += 700
    if opp_e == 2:
        val -= 650

    return val


def _rank_moves(player, enemy, color, legal, limit, deadline, refine=True, use_weighted=True):
    """Rank candidate moves from player's perspective."""
    if not legal:
        return []

    enemy_color = OTHER[color]
    scored = []

    for n, i in enumerate(legal):
        if (n & 7) == 0 and time.perf_counter() > deadline:
            break

        b = BITS[i]
        new_player = player | b
        local = _local_score(i, player, enemy, color)

        if _has_won(new_player, color):
            score = WIN + local
        elif use_weighted:
            my_w = _shortest_weighted(new_player, enemy, color)
            en_w = _shortest_weighted(enemy, new_player, enemy_color)
            score = (105 * en_w - 115 * my_w) / 100.0 + local
        else:
            score = local - CENTER_DIST[i]

        scored.append([score, i])

    if not scored:
        return legal[:limit]

    scored.sort(reverse=True)

    # Refine only the plausible front-runners with exact distances.
    if refine and time.perf_counter() < deadline:
        refine_n = min(len(scored), max(10, limit * 2))
        for k in range(refine_n):
            if (k & 3) == 0 and time.perf_counter() > deadline:
                break

            i = scored[k][1]
            b = BITS[i]
            new_player = player | b

            if not _has_won(new_player, color):
                my_e = _shortest_exact(new_player, enemy, color)
                en_e = _shortest_exact(enemy, new_player, enemy_color)
                scored[k][0] += 135 * (en_e - my_e)

                # Creating an immediate threat is good, but allowing one is dangerous.
                if my_e == 1:
                    scored[k][0] += 5000
                if en_e == 1:
                    scored[k][0] -= 7000

        scored.sort(reverse=True)

    return [i for _, i in scored[:limit]]


def _search_reply_value(move, my, opp, color, legal, reply_limit, deadline):
    """Evaluate my move after plausible best opponent replies."""
    bit = BITS[move]
    new_my = my | bit
    opp_color = OTHER[color]

    if _has_won(new_my, color):
        return WIN + _local_score(move, my, opp, color)

    legal_after = [i for i in legal if i != move]
    if not legal_after:
        return _evaluate_state(new_my, opp, color)

    # If opponent has a one-move win after our move, this move is losing.
    if _shortest_exact(opp, new_my, opp_color) == 1:
        return -WIN + _local_score(move, my, opp, color)

    replies = []
    seen = set()

    def add_reply(x):
        if x not in seen:
            seen.add(x)
            replies.append(x)

    # If our move creates an immediate threat, opponent should consider blocking it.
    if _shortest_exact(new_my, opp, color) == 1:
        for x in _winning_moves(new_my, color, legal_after):
            add_reply(x)

    # Opponent's own best-looking moves.
    ranked_opp = _rank_moves(
        opp, new_my, opp_color, legal_after,
        reply_limit, deadline, refine=False, use_weighted=True
    )
    for x in ranked_opp:
        add_reply(x)

    # Also include a few cheap "block our shape" moves.
    if time.perf_counter() < deadline and len(replies) < reply_limit + 3:
        blockers = _rank_moves(
            new_my, opp, color, legal_after,
            3, deadline, refine=False, use_weighted=False
        )
        for x in blockers:
            add_reply(x)

    if not replies:
        return _evaluate_state(new_my, opp, color) - 500

    worst_for_us = WIN
    for n, r in enumerate(replies):
        if n > 0 and (n & 3) == 0 and time.perf_counter() > deadline:
            break

        new_opp = opp | BITS[r]
        if _has_won(new_opp, opp_color):
            val = -WIN
        else:
            val = _evaluate_state(new_my, new_opp, color)

        if val < worst_for_us:
            worst_for_us = val

    return worst_for_us


def _safe_return_idx(idx, occ):
    if not (0 <= idx < SIZE) or (occ & BITS[idx]):
        idx = _first_legal(occ)
    return COORDS[idx]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        if color != "w":
            color = "b"

        start = time.perf_counter()
        deadline = start + 0.90

        my = _mask_from_points(me)
        op = _mask_from_points(opp)
        occ = my | op
        legal = _legal_list(occ)

        if not legal:
            return (0, 0)

        center_idx = (N // 2) * N + (N // 2)

        # Strong default opening: take center if available on the first move.
        if my == 0 and op.bit_count() <= 1 and not (occ & BITS[center_idx]):
            return COORDS[center_idx]

        fallback = legal[0]
        opp_color = OTHER[color]

        # 1. Win immediately if possible.
        if _shortest_exact(my, op, color) == 1:
            wins = _winning_moves(my, color, legal)
            if wins:
                best = max(wins, key=lambda i: _local_score(i, my, op, color))
                return _safe_return_idx(best, occ)

        # 2. Block opponent's immediate win if necessary.
        if _shortest_exact(op, my, opp_color) == 1:
            threats = _winning_moves(op, opp_color, legal)
            if threats:
                if len(threats) == 1:
                    return _safe_return_idx(threats[0], occ)

                # If several threats exist, choose the block that survives best.
                best = threats[0]
                best_val = -WIN * 2
                for t in threats:
                    if time.perf_counter() > deadline:
                        break
                    val = _search_reply_value(t, my, op, color, legal, 6, deadline)
                    if val > best_val:
                        best_val = val
                        best = t
                return _safe_return_idx(best, occ)

        empty = len(legal)
        if empty > 90:
            cand_limit, reply_limit = 9, 6
        elif empty > 55:
            cand_limit, reply_limit = 12, 8
        elif empty > 25:
            cand_limit, reply_limit = 15, 10
        else:
            cand_limit, reply_limit = 20, 12

        candidates = _rank_moves(
            my, op, color, legal,
            cand_limit, deadline, refine=True, use_weighted=True
        )

        if not candidates:
            return _safe_return_idx(fallback, occ)

        best_move = candidates[0]
        best_val = -WIN * 2

        for mv in candidates:
            if time.perf_counter() > deadline:
                break

            val = _search_reply_value(mv, my, op, color, legal, reply_limit, deadline)
            if val > best_val:
                best_val = val
                best_move = mv

        return _safe_return_idx(best_move, occ)

    except Exception:
        # Absolute safety fallback: return the first empty cell.
        try:
            my_m = _mask_from_points(me)
            op_m = _mask_from_points(opp)
            occ_m = my_m | op_m
            for i, b in enumerate(BITS):
                if not (occ_m & b):
                    return COORDS[i]
        except Exception:
            pass
        return (0, 0)
