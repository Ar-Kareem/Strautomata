
from __future__ import annotations

from heapq import heappush, heappop

N = 11
INF = 10**9

# Hex neighbors for coordinate system described in the prompt:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def winner(stones: set[tuple[int, int]], color: str) -> bool:
    """Check whether given stones already connect the required sides."""
    stack = []
    seen = set()

    if color == 'b':
        for c in range(N):
            if (0, c) in stones:
                stack.append((0, c))
                seen.add((0, c))
        target_row = N - 1
        while stack:
            r, c = stack.pop()
            if r == target_row:
                return True
            for nr, nc in neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
    else:
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))
        target_col = N - 1
        while stack:
            r, c = stack.pop()
            if c == target_col:
                return True
            for nr, nc in neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
    return False


def shortest_path_cost(my_stones: set[tuple[int, int]],
                       opp_stones: set[tuple[int, int]],
                       color: str) -> int:
    """
    Dijkstra-style connection cost:
    - my stone: cost 0
    - empty: cost 1
    - opponent stone: blocked
    Returns min number of empty cells needed to complete a connection.
    """
    dist = [[INF] * N for _ in range(N)]
    pq = []

    def cell_cost(r: int, c: int) -> int:
        if (r, c) in opp_stones:
            return INF
        if (r, c) in my_stones:
            return 0
        return 1

    if color == 'b':
        for c in range(N):
            w = cell_cost(0, c)
            if w < INF:
                dist[0][c] = w
                heappush(pq, (w, 0, c))
        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                return d
            for nr, nc in neighbors(r, c):
                w = cell_cost(nr, nc)
                if w >= INF:
                    continue
                nd = d + w
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))
    else:
        for r in range(N):
            w = cell_cost(r, 0)
            if w < INF:
                dist[r][0] = w
                heappush(pq, (w, r, 0))
        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                return d
            for nr, nc in neighbors(r, c):
                w = cell_cost(nr, nc)
                if w >= INF:
                    continue
                nd = d + w
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    return INF


def local_features(move: tuple[int, int],
                   me: set[tuple[int, int]],
                   opp: set[tuple[int, int]],
                   color: str) -> float:
    """Fast positional heuristics for tie-breaking."""
    r, c = move
    score = 0.0

    my_adj = 0
    opp_adj = 0
    empty_adj = 0
    for nb in neighbors(r, c):
        if nb in me:
            my_adj += 1
        elif nb in opp:
            opp_adj += 1
        else:
            empty_adj += 1

    # Prefer connecting to own stones strongly.
    score += 2.2 * my_adj

    # Some value for contesting/blocking near opponent.
    score += 0.8 * opp_adj

    # Centrality is generally good in Hex.
    center_r = (N - 1) / 2
    center_c = (N - 1) / 2
    score -= 0.18 * (abs(r - center_r) + abs(c - center_c))

    # Progress toward both goal sides.
    if color == 'b':
        # Prefer cells that are not too close to just one edge only.
        score -= 0.10 * abs(r - center_r)
    else:
        score -= 0.10 * abs(c - center_c)

    # Mild preference for flexibility.
    score += 0.10 * empty_adj

    # Tiny preference for occupying strategic center exactly.
    if (r, c) == (5, 5):
        score += 0.6

    return score


def candidate_moves(empties: list[tuple[int, int]],
                    me: set[tuple[int, int]],
                    opp: set[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Usually consider moves near existing stones first.
    If that set is too small, include all empties.
    """
    if not me and not opp:
        return empties

    near = []
    seen = set()
    occupied = me | opp
    for r, c in empties:
        keep = False
        for nr, nc in neighbors(r, c):
            if (nr, nc) in occupied:
                keep = True
                break
        if keep:
            near.append((r, c))
            seen.add((r, c))

    # Include center if free.
    if (5, 5) in empties and (5, 5) not in seen:
        near.append((5, 5))

    # If the board is sparse, broaden search.
    if len(near) < 16:
        return empties
    return near


def preferred_opening(empties: list[tuple[int, int]], color: str) -> tuple[int, int] | None:
    prefs = [
        (5, 5), (5, 4), (4, 5), (5, 6), (6, 5),
        (4, 6), (6, 4), (4, 4), (6, 6),
        (5, 3), (3, 5), (5, 7), (7, 5),
    ]
    for mv in prefs:
        if mv in empties:
            return mv
    return None


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    # Must always return a legal move.
    if not empties:
        return (0, 0)

    # Opening preference.
    if len(occupied) <= 1:
        mv = preferred_opening(empties, color)
        if mv is not None:
            return mv

    opp_color = 'w' if color == 'b' else 'b'

    # 1) Immediate winning move.
    for mv in empties:
        if winner(me_set | {mv}, color):
            return mv

    # 2) Immediate block if opponent has a winning move next turn.
    opp_winning_moves = []
    for mv in empties:
        if winner(opp_set | {mv}, opp_color):
            opp_winning_moves.append(mv)

    if opp_winning_moves:
        # If exactly one direct threat, block it.
        if len(opp_winning_moves) == 1:
            return opp_winning_moves[0]
        # If multiple threats exist, choose among them with local tie-break.
        best_block = None
        best_block_score = -10**18
        for mv in opp_winning_moves:
            sc = local_features(mv, me_set, opp_set, color)
            if sc > best_block_score:
                best_block_score = sc
                best_block = mv
        if best_block is not None:
            return best_block

    # 3) Heuristic search over candidates.
    my_before = shortest_path_cost(me_set, opp_set, color)
    opp_before = shortest_path_cost(opp_set, me_set, opp_color)

    moves = candidate_moves(empties, me_set, opp_set)

    best_move = None
    best_score = -10**18

    for mv in moves:
        new_me = me_set | {mv}

        my_after = shortest_path_cost(new_me, opp_set, color)
        opp_after = shortest_path_cost(opp_set, new_me, opp_color)

        my_improve = my_before - my_after
        opp_worsen = opp_after - opp_before

        sc = 0.0
        sc += 11.0 * my_improve
        sc += 9.0 * opp_worsen
        sc += -3.0 * my_after
        sc += 1.5 * opp_after
        sc += local_features(mv, me_set, opp_set, color)

        # Extra preference for moves that touch both own and opponent areas.
        r, c = mv
        touches_me = any((nr, nc) in me_set for nr, nc in neighbors(r, c))
        touches_opp = any((nr, nc) in opp_set for nr, nc in neighbors(r, c))
        if touches_me and touches_opp:
            sc += 0.7

        if sc > best_score:
            best_score = sc
            best_move = mv

    if best_move is not None and best_move in occupied:
        best_move = None

    if best_move is not None:
        return best_move

    # 4) Safe fallback: center-most legal move.
    empties_sorted = sorted(
        empties,
        key=lambda x: (abs(x[0] - 5) + abs(x[1] - 5), x[0], x[1])
    )
    return empties_sorted[0]
