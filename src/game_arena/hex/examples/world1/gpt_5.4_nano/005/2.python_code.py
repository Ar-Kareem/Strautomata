
from __future__ import annotations

from heapq import heappush, heappop


BOARD_N = 11

# Hex-grid neighbor definition for this arena:
# For a cell (r,c), neighbors are the 6 "hex-adjacent" cells:
# (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
def neighbors(cell: tuple[int, int]):
    r, c = cell
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_N and 0 <= nc < BOARD_N:
            yield (nr, nc)


def legal_moves(me: list[tuple[int, int]], opp: list[tuple[int, int]]):
    occ = set(me)
    occ.update(opp)
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if (r, c) not in occ:
                yield (r, c)


def would_connect(me_set: set[tuple[int, int]], move: tuple[int, int], color: str) -> bool:
    # Place the move, then BFS from one side to the other using only own stones.
    r, c = move
    own = set(me_set)
    own.add((r, c))

    if color == 'b':
        # black: top (row 0) to bottom (row 10)
        start = [(0, j) for j in range(BOARD_N) if (0, j) in own]
        target_row = BOARD_N - 1
        if not start:
            return False
        seen = set(start)
        stack = start[:]
        while stack:
            cr, cc = stack.pop()
            if cr == target_row:
                return True
            for nb in neighbors((cr, cc)):
                if nb in own and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False
    else:
        # white: left (col 0) to right (col 10)
        start = [(i, 0) for i in range(BOARD_N) if (i, 0) in own]
        target_col = BOARD_N - 1
        if not start:
            return False
        seen = set(start)
        stack = start[:]
        while stack:
            cr, cc = stack.pop()
            if cc == target_col:
                return True
            for nb in neighbors((cr, cc)):
                if nb in own and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False


def dijkstra_distance(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str):
    # Compute minimal "placement cost" to connect my sides using a standard hex strategy:
    # own cells cost 0, empty cells cost 1, opponent cells are blocked (infinite).
    # Then run multi-source Dijkstra from the appropriate start side.
    INF = 10**9

    # Dist array
    dist = [[INF] * BOARD_N for _ in range(BOARD_N)]
    pq = []

    if color == 'b':
        # top to bottom
        for j in range(BOARD_N):
            cell = (0, j)
            if cell in opp_set:
                continue
            cost = 0 if cell in me_set else 1
            if cost < dist[0][j]:
                dist[0][j] = cost
                heappush(pq, (cost, cell))
        target_check = lambda r, c: r == BOARD_N - 1
    else:
        # left to right
        for i in range(BOARD_N):
            cell = (i, 0)
            if cell in opp_set:
                continue
            cost = 0 if cell in me_set else 1
            if cost < dist[i][0]:
                dist[i][0] = cost
                heappush(pq, (cost, cell))
        target_check = lambda r, c: c == BOARD_N - 1

    while pq:
        d, (r, c) = heappop(pq)
        if d != dist[r][c]:
            continue
        if target_check(r, c):
            # Early exit: first time we reach any target cell gives optimal cost.
            return d

        for nb in neighbors((r, c)):
            nr, nc = nb
            if nb in opp_set:
                continue
            nd = d + (0 if nb in me_set else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nb))

    return INF


def score_move(me_set, opp_set, color: str, move: tuple[int, int]) -> float:
    # Higher is better.
    # We combine:
    # - immediate connection improvement via Dijkstra distances after placement
    # - immediate opponent blocking improvement
    # - adjacency to own stones
    # - centrality bias
    r, c = move

    # If move is actually blocked (shouldn't happen), score as very low.
    if move in me_set or move in opp_set:
        return -1e9

    # Evaluate distances after making the move.
    new_me = set(me_set)
    new_me.add(move)

    my_before = dijkstra_distance(me_set, opp_set, color)
    my_after = dijkstra_distance(new_me, opp_set, color)

    opp_color = 'w' if color == 'b' else 'b'
    opp_before = dijkstra_distance(opp_set, me_set, opp_color)  # treat opp stones as "me" for their metric
    opp_after = dijkstra_distance(opp_set, new_me, opp_color)

    # Centrality (prefer near center)
    center = (BOARD_N - 1) / 2.0
    centrality = -((r - center) ** 2 + (c - center) ** 2)  # closer to center -> higher

    # Adjacency: count own neighbors and "useful" neighbors (avoid opponent neighbors slightly)
    own_adj = 0
    opp_adj = 0
    for nb in neighbors(move):
        if nb in new_me:
            own_adj += 1
        elif nb in opp_set:
            opp_adj += 1

    # Side-progress heuristic (encourage getting closer to my target side)
    if color == 'b':
        # target: top=0 to bottom=10 => distance to bottom
        progress = r  # larger r closer to bottom
        # also include closeness to top through complement to stabilize
        progress = progress - (BOARD_N - 1 - r) * 0.15
    else:
        progress = c  # larger c closer to right
        progress = progress - (BOARD_N - 1 - c) * 0.15

    # Convert distance improvements to score.
    # my_after smaller is better; opponent after larger is better (block).
    # Use strong weights.
    if my_after >= 10**8:
        # shouldn't happen unless fully blocked, but keep safe
        my_term = -1000.0
    else:
        my_term = (my_before - my_after) * 50.0  # big reward for reducing required empty cells

    # Blocking term
    if opp_after >= 10**8:
        opp_term = 200.0
    else:
        opp_term = (opp_after - opp_before) * 40.0  # reward if opponent needs more

    # Immediate adjacency/tempo
    adj_term = own_adj * 10.0 - opp_adj * 4.0

    # Combine
    return my_term + opp_term + adj_term + centrality * 0.8 + progress * 0.6


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    # 1) Win immediately if possible.
    for mv in legal_moves(me, opp):
        if would_connect(me_set, mv, color):
            return mv

    # 2) Block opponent immediate win.
    opp_color = 'w' if color == 'b' else 'b'
    for mv in legal_moves(me, opp):
        # If opponent would win after they play mv, we block by playing mv now.
        # That means: check connectivity if we place mv as opponent stones.
        if would_connect(opp_set, mv, opp_color):
            return mv

    # 3) Otherwise, pick best scored move.
    best_mv = None
    best_sc = -1e18

    for mv in legal_moves(me, opp):
        sc = score_move(me_set, opp_set, color, mv)
        if sc > best_sc:
            best_sc = sc
            best_mv = mv

    # As a fallback (should never be needed), return any legal move.
    if best_mv is None:
        return next(legal_moves(me, opp))

    return best_mv
