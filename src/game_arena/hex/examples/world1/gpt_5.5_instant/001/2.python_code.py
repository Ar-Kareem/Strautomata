
from heapq import heappush, heappop
import math

N = 11

# Hex neighbors under the coordinate convention described in the prompt:
# all 8 surrounding grid neighbors except (r-1,c-1) and (r+1,c+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _opp_color(color):
    return "w" if color == "b" else "b"


def _has_win(stones, color):
    """Check whether stones of color connect their target sides."""
    S = set(stones)
    if not S:
        return False

    stack = []
    seen = set()

    if color == "b":  # top to bottom
        for c in range(N):
            if (0, c) in S:
                stack.append((0, c))
                seen.add((0, c))
        target = lambda r, c: r == N - 1
    else:             # left to right
        for r in range(N):
            if (r, 0) in S:
                stack.append((r, 0))
                seen.add((r, 0))
        target = lambda r, c: c == N - 1

    while stack:
        r, c = stack.pop()
        if target(r, c):
            return True
        for nb in _neighbors(r, c):
            if nb in S and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def _connection_cost(my_stones, opp_stones, color):
    """
    Minimum number of additional empty cells needed to connect sides.
    Own stones cost 0, empty cells cost 1, opponent stones are blocked.
    """
    mine = set(my_stones)
    opp = set(opp_stones)
    INF = 10 ** 9
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == "b":
        # start from top edge
        for c in range(N):
            cell = (0, c)
            if cell in opp:
                continue
            w = 0 if cell in mine else 1
            dist[0][c] = w
            heappush(pq, (w, 0, c))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in opp:
                    continue
                nd = d + (0 if (nr, nc) in mine else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))
    else:
        # start from left edge
        for r in range(N):
            cell = (r, 0)
            if cell in opp:
                continue
            w = 0 if cell in mine else 1
            dist[r][0] = w
            heappush(pq, (w, r, 0))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in opp:
                    continue
                nd = d + (0 if (nr, nc) in mine else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    return INF


def _dist_field(my_stones, opp_stones, color, reverse=False):
    """
    Dijkstra distance from one target side. Used to identify cells lying on
    good shortest/near-shortest routes.
    """
    mine = set(my_stones)
    opp = set(opp_stones)
    INF = 10 ** 9
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == "b":
        row = N - 1 if reverse else 0
        for c in range(N):
            if (row, c) in opp:
                continue
            w = 0 if (row, c) in mine else 1
            dist[row][c] = w
            heappush(pq, (w, row, c))
    else:
        col = N - 1 if reverse else 0
        for r in range(N):
            if (r, col) in opp:
                continue
            w = 0 if (r, col) in mine else 1
            dist[r][col] = w
            heappush(pq, (w, r, col))

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp:
                continue
            nd = d + (0 if (nr, nc) in mine else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return dist


def _local_score(move, me_set, opp_set, color):
    r, c = move
    score = 0.0

    # Center is usually flexible in Hex.
    center = (N - 1) / 2.0
    score += 2.2 * (N - abs(r - center) - abs(c - center)) / N

    # Prefer spreading in own connection direction, but not extreme edges too early.
    if color == "b":
        score += 0.18 * (N - abs(c - center))
        if r == 0 or r == N - 1:
            score += 0.35
    else:
        score += 0.18 * (N - abs(r - center))
        if c == 0 or c == N - 1:
            score += 0.35

    # Adjacent friendly support and adjacent blocking contact.
    friendly_adj = 0
    opp_adj = 0
    for nb in _neighbors(r, c):
        if nb in me_set:
            friendly_adj += 1
        elif nb in opp_set:
            opp_adj += 1
    score += 1.15 * friendly_adj + 0.55 * opp_adj

    # Hex "bridge" patterns: two friendly stones at distance forming a virtual connection.
    # If the intermediate common-neighbor cells are not occupied by opponent, this is valuable.
    bridge_pairs = [
        ((-1, -1), (-1, 1)),
        ((-1, 1), (1, 0)),
        ((0, -1), (1, -1)),
        ((0, 1), (-1, 1)),
        ((1, -1), (1, 1)),
        ((-1, 0), (1, -1)),
        ((-1, 0), (0, 1)),
        ((0, -1), (1, 0)),
    ]
    for (a, b) in bridge_pairs:
        ar, ac = r + a[0], c + a[1]
        br, bc = r + b[0], c + b[1]
        if 0 <= ar < N and 0 <= ac < N and 0 <= br < N and 0 <= bc < N:
            if (ar, ac) in me_set and (br, bc) in me_set:
                score += 1.4

    return score


def _ordered_candidates(empty, me_set, opp_set):
    """Limit full evaluation to plausible moves, while keeping safety fallback."""
    if not me_set and not opp_set:
        return [(N // 2, N // 2)]

    hot = set()
    occupied = me_set | opp_set
    for r, c in occupied:
        hot.add((r, c))
        for nb in _neighbors(r, c):
            hot.add(nb)
        # include radius-2 neighborhood cheaply
        for nr, nc in list(_neighbors(r, c)):
            for nb2 in _neighbors(nr, nc):
                hot.add(nb2)

    cand = [x for x in hot if x in empty]
    if len(cand) < 18:
        cand = list(empty)

    # If very many candidates, keep central-ish local ones.
    center = (N - 1) / 2.0
    cand.sort(key=lambda x: abs(x[0] - center) + abs(x[1] - center))
    return cand[:70]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = {(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied}

    # Absolute safety fallback: should only happen on full board.
    if not empty:
        return (0, 0)

    # Strong opening moves.
    if len(occupied) == 0:
        return (5, 5)
    if len(me_set) == 0 and (5, 5) in empty:
        return (5, 5)

    oppc = _opp_color(color)

    candidates = _ordered_candidates(empty, me_set, opp_set)

    # Immediate win.
    for mv in candidates:
        if _has_win(me_set | {mv}, color):
            return mv

    # Immediate block opponent win.
    urgent_blocks = []
    for mv in candidates:
        if _has_win(opp_set | {mv}, oppc):
            urgent_blocks.append(mv)
    if urgent_blocks:
        # Choose the block that is also best for us.
        return max(urgent_blocks, key=lambda x: _local_score(x, me_set, opp_set, color))

    base_my = _connection_cost(me_set, opp_set, color)
    base_opp = _connection_cost(opp_set, me_set, oppc)

    # Distance fields before playing, to reward cells on shortest corridors.
    my_a = _dist_field(me_set, opp_set, color, False)
    my_b = _dist_field(me_set, opp_set, color, True)
    op_a = _dist_field(opp_set, me_set, oppc, False)
    op_b = _dist_field(opp_set, me_set, oppc, True)

    best = None
    best_score = -1e100

    for mv in candidates:
        new_me = me_set | {mv}

        my_cost = _connection_cost(new_me, opp_set, color)
        opp_cost_after = _connection_cost(opp_set, new_me, oppc)

        r, c = mv

        score = 0.0

        # Main strategic terms.
        score += 18.0 * (base_my - my_cost)
        score += 13.0 * (opp_cost_after - base_opp)
        score += -4.0 * my_cost + 3.0 * opp_cost_after

        # Corridor terms: a good cell has low sum of distances from both own sides.
        own_corr = my_a[r][c] + my_b[r][c]
        opp_corr = op_a[r][c] + op_b[r][c]
        if own_corr < 10 ** 8:
            score += 8.0 / (1.0 + own_corr)
            score += max(0.0, 7.0 - own_corr) * 0.7
        if opp_corr < 10 ** 8:
            # Blocking opponent's best corridors matters.
            score += 7.0 / (1.0 + opp_corr)
            score += max(0.0, 7.0 - opp_corr) * 0.55

        score += _local_score(mv, me_set, opp_set, color)

        # Slight deterministic tie-breaker to avoid predictable corner bias.
        score += ((r * 13 + c * 7) % 17) * 1e-4

        if score > best_score:
            best_score = score
            best = mv

    if best in empty:
        return best

    # Final legal fallback.
    center = (N // 2, N // 2)
    if center in empty:
        return center
    return min(empty, key=lambda x: abs(x[0] - N // 2) + abs(x[1] - N // 2))
