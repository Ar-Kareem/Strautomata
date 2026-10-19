
from heapq import heappush, heappop

N = 11

# Hex neighbors in the coordinate system described:
# all 8 surrounding cells except (i-1,j-1) and (i+1,j+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def sides_for_color(color):
    if color == 'b':
        # black connects top to bottom
        start = [(0, c) for c in range(N)]
        goal_check = lambda r, c: r == N - 1
    else:
        # white connects left to right
        start = [(r, 0) for r in range(N)]
        goal_check = lambda r, c: c == N - 1
    return start, goal_check


def connected_win(stones, color):
    """Check if given stones already connect that color's sides."""
    stone_set = set(stones)
    start, goal_check = sides_for_color(color)
    stack = [p for p in start if p in stone_set]
    seen = set(stack)
    while stack:
        r, c = stack.pop()
        if goal_check(r, c):
            return True
        for nb in neighbors(r, c):
            if nb in stone_set and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def path_cost(my_set, opp_set, color):
    """
    Dijkstra shortest path from one side to the opposite for 'color'.
    Cost:
      own stone = 0
      empty = 1
      opponent stone = blocked
    Lower is better.
    """
    INF = 10**9
    dist = [[INF] * N for _ in range(N)]
    pq = []
    start, goal_check = sides_for_color(color)

    for r, c in start:
        if (r, c) in opp_set:
            continue
        w = 0 if (r, c) in my_set else 1
        dist[r][c] = w
        heappush(pq, (w, r, c))

    best = INF
    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if goal_check(r, c):
            best = d
            break
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            nd = d + (0 if (nr, nc) in my_set else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return best


def immediate_winning_move(me_set, opp_set, color, empties):
    for mv in empties:
        me_set.add(mv)
        won = connected_win(me_set, color)
        me_set.remove(mv)
        if won:
            return mv
    return None


def opponent_immediate_wins(me_set, opp_set, opp_color, empties):
    wins = []
    for mv in empties:
        opp_set.add(mv)
        won = connected_win(opp_set, opp_color)
        opp_set.remove(mv)
        if won:
            wins.append(mv)
    return wins


def centrality(r, c):
    cr = (N - 1) / 2
    cc = (N - 1) / 2
    return -((r - cr) ** 2 + (c - cc) ** 2)


def side_progress(r, c, color):
    # encourages progress along connection axis while staying not too edge-bound
    if color == 'b':
        return -abs(r - (N - 1) / 2) * 0.2 + (N - abs(c - (N - 1) / 2)) * 0.05
    else:
        return -abs(c - (N - 1) / 2) * 0.2 + (N - abs(r - (N - 1) / 2)) * 0.05


def local_support(move, me_set, opp_set, color):
    r, c = move
    score = 0.0
    my_n = 0
    opp_n = 0
    empty_n = 0
    for nr, nc in neighbors(r, c):
        if (nr, nc) in me_set:
            my_n += 1
        elif (nr, nc) in opp_set:
            opp_n += 1
        else:
            empty_n += 1

    score += 1.8 * my_n
    score += 0.4 * opp_n  # useful contact / blocking
    score += 0.1 * empty_n

    # Light bridge-pattern encouragement: second-ring along useful hex diagonals
    bridge_offsets = [(-1, 1), (1, -1), (-2, 1), (2, -1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in bridge_offsets:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc) and (rr, cc) in me_set:
            score += 0.35

    # Slight bonus for touching own sides
    if color == 'b':
        if r == 0 or r == N - 1:
            score += 0.6
    else:
        if c == 0 or c == N - 1:
            score += 0.6

    return score


def evaluate_move(move, me_set, opp_set, color, opp_color):
    r, c = move

    me_set.add(move)
    my_cost = path_cost(me_set, opp_set, color)
    opp_cost_after = path_cost(opp_set, me_set, opp_color)
    me_set.remove(move)

    base_my_cost = path_cost(me_set, opp_set, color)
    base_opp_cost = path_cost(opp_set, me_set, opp_color)

    improve_me = base_my_cost - my_cost
    worsen_opp = opp_cost_after - base_opp_cost

    score = 0.0
    score += 14.0 * improve_me
    score += 11.0 * worsen_opp
    score += local_support(move, me_set, opp_set, color)
    score += 0.12 * centrality(r, c)
    score += side_progress(r, c, color)

    # Prefer moves that lie on many shortest-ish routes
    if color == 'b':
        axis_bias = min(r, N - 1 - r)
    else:
        axis_bias = min(c, N - 1 - c)
    score += 0.15 * axis_bias

    return score


def opening_move(me_set, opp_set, color, empties):
    # Strong, safe opening preferences near center.
    prefs = [
        (5, 5), (5, 4), (4, 5), (6, 5), (5, 6),
        (4, 6), (6, 4), (4, 4), (6, 6),
        (5, 3), (3, 5), (7, 5), (5, 7)
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

    # Absolute safety fallback
    if not empties:
        return (0, 0)

    opp_color = 'w' if color == 'b' else 'b'

    # Opening
    if len(me) + len(opp) <= 1:
        mv = opening_move(me_set, opp_set, color, set(empties))
        if mv is not None:
            return mv

    # 1. Win immediately if possible
    mv = immediate_winning_move(me_set, opp_set, color, empties)
    if mv is not None:
        return mv

    # 2. Block opponent immediate win(s)
    opp_wins = opponent_immediate_wins(me_set, opp_set, opp_color, empties)
    if opp_wins:
        # If multiple, choose the block with best evaluation.
        best = None
        best_score = -10**18
        for m in opp_wins:
            s = evaluate_move(m, me_set, opp_set, color, opp_color)
            if s > best_score:
                best_score = s
                best = m
        return best

    # 3. Candidate reduction for speed: evaluate promising cells first
    # Keep cells near existing stones, otherwise all.
    near = []
    empty_set = set(empties)
    for mv in empties:
        r, c = mv
        close = False
        for nb in neighbors(r, c):
            if nb in occupied:
                close = True
                break
        if close:
            near.append(mv)

    candidates = near if near else empties

    # If too many candidates, prefilter by cheap heuristic.
    if len(candidates) > 28:
        scored = []
        for mv in candidates:
            r, c = mv
            s = local_support(mv, me_set, opp_set, color) + 0.15 * centrality(r, c) + side_progress(r, c, color)
            scored.append((s, mv))
        scored.sort(reverse=True)
        candidates = [mv for _, mv in scored[:28]]

    # 4. Full evaluation
    best = None
    best_score = -10**18
    for mv in candidates:
        s = evaluate_move(mv, me_set, opp_set, color, opp_color)
        if s > best_score:
            best_score = s
            best = mv

    if best is not None and best in empty_set:
        return best

    # Final legal fallback
    return empties[0]
