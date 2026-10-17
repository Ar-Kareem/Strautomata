
from collections import deque
from typing import List, Tuple

BOARD_N = 11

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    my_turn = True  # always true per prompt

    # Determine target sides based on color
    if color == 'b':  # connect top (0) to bottom (N-1)
        MY_TOP = 0
        MY_BOTTOM = BOARD_N - 1
        # For BFS "touching" sides, a stone on row 0 is connected to top.
        # We'll represent sides as virtual nodes in BFS logic.
        my_starts = [(MY_TOP, c) for c in range(BOARD_N) if (MY_TOP, c) in me_set]
        my_goal_row = MY_BOTTOM
        opp_starts_row = 0  # opponent for 'b' would be 'w', but we use generic functions below
    else:  # 'w' connect left to right
        MY_LEFT = 0
        MY_RIGHT = BOARD_N - 1
        my_starts = [(r, MY_LEFT) for r in range(BOARD_N) if (r, MY_LEFT) in me_set]
        my_goal_col = MY_RIGHT

    def inb(r, c):
        return 0 <= r < BOARD_N and 0 <= c < BOARD_N

    # Hex adjacency: (r,c) touches 6 neighbors: (r, c-1), (r, c+1), (r-1,c), (r+1,c), (r-1,c+1), (r+1,c-1)
    # This matches common axial mapping for "flat-topped" hex on square coordinates.
    def neighbors(r, c):
        cand = [
            (r, c - 1),
            (r, c + 1),
            (r - 1, c),
            (r + 1, c),
            (r - 1, c + 1),
            (r + 1, c - 1),
        ]
        return [(rr, cc) for rr, cc in cand if inb(rr, cc)]

    def is_empty(cell):
        return cell not in me_set and cell not in opp_set

    def can_win_after(move, stones_set):
        # stones_set contains current player's stones; add move; check path.
        r, c = move
        new_set = set(stones_set)
        new_set.add(move)

        if color == 'b':
            # BFS from top edge stones of player
            q = deque()
            visited = set()
            for cc in range(BOARD_N):
                if (0, cc) in new_set:
                    q.append((0, cc))
                    visited.add((0, cc))
            while q:
                rr, cc = q.popleft()
                if rr == BOARD_N - 1:
                    return True
                for nr, nc in neighbors(rr, cc):
                    if (nr, nc) in new_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
            return False
        else:
            # 'w': BFS from left edge stones
            q = deque()
            visited = set()
            for rr in range(BOARD_N):
                if (rr, 0) in new_set:
                    q.append((rr, 0))
                    visited.add((rr, 0))
            while q:
                rr, cc = q.popleft()
                if cc == BOARD_N - 1:
                    return True
                for nr, nc in neighbors(rr, cc):
                    if (nr, nc) in new_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
            return False

    def opponent_color(c):
        return 'w' if c == 'b' else 'b'

    # 1) Immediate win
    empties = [(r, c) for r in range(BOARD_N) for c in range(BOARD_N) if (r, c) not in me_set and (r, c) not in opp_set]

    for mv in empties:
        if can_win_after(mv, me_set):
            return mv

    # 2) Block opponent immediate win
    opp_can_win = []
    opp_color = opponent_color(color)
    # For block, we need to test opponent's win after placing at mv.
    # We'll reuse can_win_after by temporarily treating "color" logic? Easier: implement generic checker.
    def can_win_generic(stones_set, player_color):
        if player_color == 'b':
            q = deque()
            visited = set()
            for cc in range(BOARD_N):
                if (0, cc) in stones_set:
                    q.append((0, cc))
                    visited.add((0, cc))
            while q:
                rr, cc = q.popleft()
                if rr == BOARD_N - 1:
                    return True
                for nr, nc in neighbors(rr, cc):
                    if (nr, nc) in stones_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
            return False
        else:
            q = deque()
            visited = set()
            for rr in range(BOARD_N):
                if (rr, 0) in stones_set:
                    q.append((rr, 0))
                    visited.add((rr, 0))
            while q:
                rr, cc = q.popleft()
                if cc == BOARD_N - 1:
                    return True
                for nr, nc in neighbors(rr, cc):
                    if (nr, nc) in stones_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
            return False

    for mv in empties:
        test_set = set(opp_set)
        test_set.add(mv)
        if can_win_generic(test_set, opp_color):
            opp_can_win.append(mv)

    if opp_can_win:
        # If multiple blocks, choose one that also best improves our position.
        # Evaluate all such mv with heuristic below.
        pass_block_candidates = opp_can_win
    else:
        pass_block_candidates = None

    # 3) Heuristic shortest path for our color: minimize #empty cells needed to connect sides
    # Compute distance from start edge to all cells using Dijkstra-like (0-1 BFS).
    # cost: our stones 0, empty 1, opponent stones impassable (inf).
    INF = 10**9

    def side_distance(color_for_bfs):
        # returns best cost from one side to the other and also distances
        dist = [[INF] * BOARD_N for _ in range(BOARD_N)]
        dq = deque()

        def push(r, c, d):
            if d < dist[r][c]:
                dist[r][c] = d
                # 0-1 BFS: cost is 0 for our stones, 1 for empty
                if d == dist[r][c] and d >= 0:
                    # We decide based on occupancy, but easier: the new distance delta determines push type.
                    # We'll compute transition cost in main loop; here just push with correct direction handled there.

                    pass

        # Initialize frontier with start edge cells belonging to player or empty?
        # For shortest "through empty", we can start from any cell on start edge: moving into it costs 0 if it's our stone else 1 if empty.
        # Opponent stones are impassable.
        if color_for_bfs == 'b':
            start_cells = [(0, c) for c in range(BOARD_N)]
            goal_test = lambda r, c: r == BOARD_N - 1
        else:
            start_cells = [(r, 0) for r in range(BOARD_N)]
            goal_test = lambda r, c: c == BOARD_N - 1

        for r, c in start_cells:
            if (r, c) in opp_set:
                continue
            cost_here = 0 if (r, c) in me_set else 1  # since we're computing for "our color", we will pass correct set below
            # But if BFS is for opponent, we'd need their stones. We'll only call this for our color.
            # We'll override me_set usage by parameter later. Here: always for 'our' BFS.
            dist[r][c] = cost_here
            if cost_here == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

        # 0-1 BFS where transition cost depends on destination cell occupancy relative to player.
        # We'll only use for our player and our own sets (me_set). Destination: our stone cost 0, empty cost 1.
        while dq:
            r, c = dq.popleft()
            for nr, nc in neighbors(r, c):
                if (nr, nc) in opp_set:
                    continue
                add = 0 if (nr, nc) in me_set else 1
                nd = dist[r][c] + add
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    if add == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))

        best = INF
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                if goal_test(r, c):
                    best = min(best, dist[r][c])
        return best, dist

    my_best, my_dist = side_distance(color)

    # Evaluate candidate moves: primary minimize our resulting distance; secondary block or connectivity.
    def move_score(mv):
        if not is_empty(mv):
            return -INF

        # If we already consider blocks candidate, still score.
        # Approximate: distance from start to goal after adding mv:
        # We can compute by considering paths that use mv as intermediate: dist_to_mv + cost_mv + dist_from_mv_to_goal
        # But we only computed dist from start. We'll compute goal-directed dist too (reverse) by symmetry:
        # For this grid, reversing start/goal corresponds to flipping sides; easiest: rerun BFS with start as goal edge.
        # However that doubles computation; still fine with 11x11 (121 cells).
        return heuristic_score_after_move(mv)

    def heuristic_score_after_move(mv):
        # Run two BFS: from our start edge to all cells (considering current me_set + mv), and from all cells to our goal
        # by initializing from goal edge.
        # Total O(N^2) per candidate is fine? 121*121 too big. We'll do a targeted computation:
        # Instead, use a cheaper proxy: since adding one stone at mv changes occupancy only at mv,
        # we score by (my_dist[start->mv] + 0) + (estimated remaining) using precomputed distance from goal via another BFS.
        # We'll precompute goal-dist once per call.

        # Precompute goal-side distances lazily once.
        return 0  # placeholder, will be replaced after precompute

    # Precompute distances from goal side for our color
    def side_distance_from_start(player_color, start_side):
        dist = [[INF] * BOARD_N for _ in range(BOARD_N)]
        dq = deque()

        if player_color == 'b':
            if start_side == 'top':
                start_cells = [(0, c) for c in range(BOARD_N)]
                is_goal = lambda r, c: r == BOARD_N - 1
            else:  # bottom
                start_cells = [(BOARD_N - 1, c) for c in range(BOARD_N)]
                is_goal = lambda r, c: r == 0
        else:
            if start_side == 'left':
                start_cells = [(r, 0) for r in range(BOARD_N)]
                is_goal = lambda r, c: c == BOARD_N - 1
            else:  # right
                start_cells = [(r, BOARD_N - 1) for r in range(BOARD_N)]
                is_goal = lambda r, c: c == 0

        for r, c in start_cells:
            if (r, c) in opp_set:
                continue
            cost_here = 0 if (r, c) in me_set else 1
            dist[r][c] = cost_here
            if cost_here == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

        while dq:
            r, c = dq.popleft()
            for nr, nc in neighbors(r, c):
                if (nr, nc) in opp_set:
                    continue
                add = 0 if (nr, nc) in me_set else 1
                nd = dist[r][c] + add
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    if add == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))
        return dist

    if color == 'b':
        dist_from_goal = side_distance_from_start(color, 'bottom')  # start at bottom edge
        # Then dist_from_goal[x][y] corresponds to cost to reach top edge
    else:
        dist_from_goal = side_distance_from_start(color, 'right')  # start at right edge

    # Now score: (dist_start[mv] + 0) + (dist_goal[mv] + 0) - we double-count mv's "empty cost"
    # We approximate by: total_cost_if_take_mv = dist_start[mv] + dist_from_goal[mv] - cost_mv_current
    # where cost_mv_current is 0 if mv is our stone (it isn't), else 1. We'll treat it as empty cost=1.
    # Lower total_cost is better, so higher score is negative total_cost.
    def score_move(mv):
        r, c = mv
        if not is_empty(mv):
            return -INF
        # If mv is currently empty, its cost as empty is 1 in both distances.
        # But when we place our stone, its cost becomes 0, effectively saving 1 in each distance.
        # Approximate new total = dist_start[mv] + dist_from_goal[mv] - 2.
        if my_dist[r][c] >= INF or dist_from_goal[r][c] >= INF:
            base = INF
        else:
            base = my_dist[r][c] + dist_from_goal[r][c] - 2
        # Tactical tie-break: count friendly neighbors and penalize enemy neighbors
        friendly = sum((nr, nc) in me_set for nr, nc in neighbors(r, c))
        enemy_adj = sum((nr, nc) in opp_set for nr, nc in neighbors(r, c))
        # Prefer moves that are near our stones and away from opponent.
        # Combine: primary minimize base, secondary maximize friendly, minimize enemy_adj.
        return (-base, friendly, -enemy_adj, -(abs(r - (BOARD_N//2)) + abs(c - (BOARD_N//2))))

    # If blocking candidates exist, search among them first; else all empties.
    candidates = pass_block_candidates if pass_block_candidates is not None else empties

    best_mv = None
    best_val = None
    for mv in candidates:
        val = score_move(mv)
        if best_val is None or val > best_val:
            best_val = val
            best_mv = mv

    # Fallback (should never be needed)
    if best_mv is None:
        return empties[0]
    return best_mv
