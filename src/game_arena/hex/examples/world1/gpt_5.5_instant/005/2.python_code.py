
from heapq import heappush, heappop
from math import inf

N = 11

# Hex neighbors for the coordinate system described:
# all 8 surrounding grid cells except (r-1,c-1) and (r+1,c+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

def _inside(r, c):
    return 0 <= r < N and 0 <= c < N

def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc

def _other(color):
    return 'w' if color == 'b' else 'b'

def _goal_reached(stones, color):
    """True if stones connect their required sides."""
    stones = set(stones)
    if not stones:
        return False

    stack = []
    seen = set()

    if color == 'b':  # top to bottom
        for c in range(N):
            if (0, c) in stones:
                stack.append((0, c))
                seen.add((0, c))
        target = lambda r, c: r == N - 1
    else:             # left to right
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))
        target = lambda r, c: c == N - 1

    while stack:
        r, c = stack.pop()
        if target(r, c):
            return True
        for nb in _neighbors(r, c):
            if nb in stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False

def _component_info(stones, color):
    """Return maps from stone to component id and component side-touch flags."""
    stones = set(stones)
    comp = {}
    flags = []
    cid = 0

    for s in stones:
        if s in comp:
            continue
        stack = [s]
        comp[s] = cid
        if color == 'b':
            f1 = (s[0] == 0)
            f2 = (s[0] == N - 1)
        else:
            f1 = (s[1] == 0)
            f2 = (s[1] == N - 1)

        while stack:
            r, c = stack.pop()
            if color == 'b':
                f1 = f1 or (r == 0)
                f2 = f2 or (r == N - 1)
            else:
                f1 = f1 or (c == 0)
                f2 = f2 or (c == N - 1)

            for nb in _neighbors(r, c):
                if nb in stones and nb not in comp:
                    comp[nb] = cid
                    stack.append(nb)
        flags.append((f1, f2))
        cid += 1

    return comp, flags

def _would_win(move, stones, color):
    """Fast-ish win test after adding move."""
    return _goal_reached(set(stones) | {move}, color)

def _dijkstra_cost(my_stones, opp_stones, color):
    """
    Minimal connection cost for color.
    Existing own stones cost 0, empty cells cost 1, opponent stones blocked.
    Includes virtual start side and target side.
    """
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)

    dist = [[inf] * N for _ in range(N)]
    pq = []

    if color == 'b':
        # Start from top side
        for c in range(N):
            cell = (0, c)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[0][c] = cost
            heappush(pq, (cost, 0, c))
        is_target = lambda r, c: r == N - 1
    else:
        # Start from left side
        for r in range(N):
            cell = (r, 0)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[r][0] = cost
            heappush(pq, (cost, r, 0))
        is_target = lambda r, c: c == N - 1

    best = inf
    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if is_target(r, c):
            best = d
            break
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue
            add = 0 if (nr, nc) in my_stones else 1
            nd = d + add
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    return best, dist

def _two_ended_empty_wins(stones, opp, color):
    """
    Return empty cells that connect two components touching opposite sides,
    a useful immediate tactical pattern.
    """
    stones = set(stones)
    opp = set(opp)
    comp, flags = _component_info(stones, color)
    wins = set()

    for r in range(N):
        for c in range(N):
            cell = (r, c)
            if cell in stones or cell in opp:
                continue

            touches_a = False
            touches_b = False

            if color == 'b':
                touches_a = (r == 0)
                touches_b = (r == N - 1)
            else:
                touches_a = (c == 0)
                touches_b = (c == N - 1)

            adjacent_components = set()
            for nb in _neighbors(r, c):
                if nb in comp:
                    adjacent_components.add(comp[nb])

            for cid in adjacent_components:
                fa, fb = flags[cid]
                touches_a = touches_a or fa
                touches_b = touches_b or fb

            if touches_a and touches_b:
                wins.add(cell)

    return wins

def _bridge_bonus(move, my_stones, opp_stones, color):
    """
    Small bonuses for common loose Hex connection patterns.
    We reward cells that complete or support distance-2 diagonal/knight-like links
    where the intermediate cells are not occupied by opponent.
    """
    r, c = move
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    bonus = 0.0

    # Pairs at hex-distance 2 that often represent useful bridge influence.
    patterns = [
        ((-1, -1), [(0, -1), (-1, 0)]),
        ((-1, 2), [(-1, 1), (0, 1)]),
        ((1, -2), [(1, -1), (0, -1)]),
        ((1, 1), [(0, 1), (1, 0)]),
        ((-2, 1), [(-1, 0), (-1, 1)]),
        ((2, -1), [(1, 0), (1, -1)]),
    ]

    for (dr, dc), mids in patterns:
        ar, ac = r + dr, c + dc
        if _inside(ar, ac) and (ar, ac) in my_stones:
            safe = True
            open_mid = 0
            for mr, mc in mids:
                x, y = r + mr, c + mc
                if not _inside(x, y) or (x, y) in opp_stones:
                    safe = False
                elif (x, y) not in my_stones:
                    open_mid += 1
            if safe:
                bonus += 1.4 + 0.25 * open_mid

    return bonus

def _local_features(move, my_stones, opp_stones, color):
    r, c = move
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)

    friendly_adj = 0
    enemy_adj = 0
    empty_adj = 0
    for nb in _neighbors(r, c):
        if nb in my_stones:
            friendly_adj += 1
        elif nb in opp_stones:
            enemy_adj += 1
        else:
            empty_adj += 1

    # Center is generally good in Hex, but not too dominant.
    center_dist = abs(r - 5) + abs(c - 5)
    center_bonus = 3.0 - 0.28 * center_dist

    # Progress / edge relevance by color.
    if color == 'b':
        # Prefer central columns and useful vertical progress.
        axis_bonus = 1.4 - 0.18 * abs(c - 5)
        edge_bonus = 0.0
        if r == 0 or r == N - 1:
            edge_bonus += 0.35
        if 2 <= r <= 8:
            edge_bonus += 0.25
    else:
        axis_bonus = 1.4 - 0.18 * abs(r - 5)
        edge_bonus = 0.0
        if c == 0 or c == N - 1:
            edge_bonus += 0.35
        if 2 <= c <= 8:
            edge_bonus += 0.25

    # Friendly adjacency helps connection; enemy adjacency helps blocking,
    # but too much contact can be inefficient, so weights are moderate.
    return (
        center_bonus
        + axis_bonus
        + edge_bonus
        + 1.15 * friendly_adj
        + 0.55 * enemy_adj
        + 0.10 * empty_adj
        + _bridge_bonus(move, my_stones, opp_stones, color)
    )

def _best_fallback(empty):
    # Deterministic good opening/fallback ordering: center outward.
    return min(empty, key=lambda x: (abs(x[0] - 5) + abs(x[1] - 5), abs(x[0] - x[1]), x[0], x[1]))

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me = set(tuple(x) for x in me)
    opp = set(tuple(x) for x in opp)
    occupied = me | opp

    empty = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not empty:
        # Should never happen in a valid game, but keep API safe.
        return (0, 0)

    opp_color = _other(color)

    # Strong opening preference.
    if len(occupied) == 0:
        return (5, 5)
    if len(me) == 0 and (5, 5) not in occupied:
        return (5, 5)

    # 1. Immediate winning move.
    tactical_wins = _two_ended_empty_wins(me, opp, color)
    if tactical_wins:
        return _best_fallback(list(tactical_wins))

    for mv in empty:
        if _would_win(mv, me, color):
            return mv

    # 2. Block opponent's immediate winning move.
    opp_tactical_wins = _two_ended_empty_wins(opp, me, opp_color)
    if opp_tactical_wins:
        return _best_fallback([mv for mv in opp_tactical_wins if mv in empty])

    for mv in empty:
        if _would_win(mv, opp, opp_color):
            return mv

    # 3. Evaluate moves using connection costs.
    base_my_cost, _ = _dijkstra_cost(me, opp, color)
    base_opp_cost, _ = _dijkstra_cost(opp, me, opp_color)

    best_move = None
    best_score = -10**18

    # Candidate pruning: in early/mid game evaluate all 121 cells is still fine,
    # but prioritize local/central candidates if desired. Full evaluation is okay.
    for mv in empty:
        my2 = me | {mv}
        opp_blocked = opp

        new_my_cost, _ = _dijkstra_cost(my2, opp_blocked, color)
        # The move also acts as a blocker for opponent.
        new_opp_cost, _ = _dijkstra_cost(opp, my2, opp_color)

        my_gain = base_my_cost - new_my_cost
        opp_harm = new_opp_cost - base_opp_cost

        score = 0.0
        score += 9.0 * my_gain
        score += 7.4 * opp_harm
        score += _local_features(mv, me, opp, color)

        # Critical race handling: if opponent is close, defense becomes urgent.
        if base_opp_cost <= 2:
            score += 8.0 * opp_harm
            score += 1.0 * _local_features(mv, opp, me, opp_color)

        # If we are close, push winning connection.
        if base_my_cost <= 3:
            score += 5.0 * my_gain

        # Prefer moves lying on at least one of our current shortest-path fronts.
        # Approximate by giving a bonus to cells whose placement reaches low cost.
        if color == 'b':
            progress = min(mv[0], N - 1 - mv[0])
        else:
            progress = min(mv[1], N - 1 - mv[1])
        score += 0.08 * progress

        # Deterministic tie-breaking toward center.
        score -= 0.001 * (abs(mv[0] - 5) + abs(mv[1] - 5))
        score -= 0.00001 * (mv[0] * N + mv[1])

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None and best_move not in occupied and _inside(best_move[0], best_move[1]):
        return best_move

    return _best_fallback(empty)
