
from heapq import heappush, heappop

N = 11
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def legal_moves(me_set, opp_set):
    for r in range(N):
        for c in range(N):
            if (r, c) not in me_set and (r, c) not in opp_set:
                yield (r, c)


def is_goal_cell(color, rc):
    r, c = rc
    return r == N - 1 if color == 'b' else c == N - 1


def start_cells(color):
    if color == 'b':
        return [(0, c) for c in range(N)]
    else:
        return [(r, 0) for r in range(N)]


def cell_cost(cell, me_set, opp_set):
    if cell in opp_set:
        return None
    if cell in me_set:
        return 0
    return 1


def shortest_path_cost(me_set, opp_set, color):
    INF = 10**9
    dist = {}
    pq = []

    for s in start_cells(color):
        cc = cell_cost(s, me_set, opp_set)
        if cc is None:
            continue
        dist[s] = cc
        heappush(pq, (cc, s))

    best = INF
    while pq:
        d, u = heappop(pq)
        if d != dist.get(u, INF):
            continue
        if is_goal_cell(color, u):
            best = d
            break
        for v in neighbors(*u):
            cc = cell_cost(v, me_set, opp_set)
            if cc is None:
                continue
            nd = d + cc
            if nd < dist.get(v, INF):
                dist[v] = nd
                heappush(pq, (nd, v))
    return best


def connected_to_both_sides(me_set, color):
    if not me_set:
        return False
    stack = []
    seen = set()

    if color == 'b':
        for c in range(N):
            if (0, c) in me_set:
                stack.append((0, c))
                seen.add((0, c))
        while stack:
            u = stack.pop()
            if u[0] == N - 1:
                return True
            for v in neighbors(*u):
                if v in me_set and v not in seen:
                    seen.add(v)
                    stack.append(v)
    else:
        for r in range(N):
            if (r, 0) in me_set:
                stack.append((r, 0))
                seen.add((r, 0))
        while stack:
            u = stack.pop()
            if u[1] == N - 1:
                return True
            for v in neighbors(*u):
                if v in me_set and v not in seen:
                    seen.add(v)
                    stack.append(v)
    return False


def winning_move_exists(me_set, opp_set, color):
    for mv in legal_moves(me_set, opp_set):
        new_me = set(me_set)
        new_me.add(mv)
        if connected_to_both_sides(new_me, color):
            return mv
    return None


def center_bias(r, c):
    cr = (N - 1) / 2
    cc = (N - 1) / 2
    return -((r - cr) ** 2 + (c - cc) ** 2)


def side_progress(color, r, c):
    if color == 'b':
        return -abs(r - (N - 1) / 2)
    else:
        return -abs(c - (N - 1) / 2)


def local_features(move, me_set, opp_set, color):
    r, c = move
    my_adj = 0
    opp_adj = 0
    empty_adj = 0
    for nb in neighbors(r, c):
        if nb in me_set:
            my_adj += 1
        elif nb in opp_set:
            opp_adj += 1
        else:
            empty_adj += 1

    score = 0.0
    score += 2.2 * my_adj
    score += 0.8 * opp_adj
    score += 0.15 * empty_adj
    score += 0.08 * center_bias(r, c)
    score += 0.3 * side_progress(color, r, c)

    # Tiny preference for edges relevant to my goal
    if color == 'b':
        if r == 0 or r == N - 1:
            score += 0.25
    else:
        if c == 0 or c == N - 1:
            score += 0.25

    # Bridge-like patterns: if two friendly stones are reachable around this move
    nb_list = list(neighbors(r, c))
    for i in range(len(nb_list)):
        for j in range(i + 1, len(nb_list)):
            a, b = nb_list[i], nb_list[j]
            if a in me_set and b in me_set:
                score += 0.55
            if a in opp_set and b in opp_set:
                score += 0.18

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    empties = list(legal_moves(me_set, opp_set))
    if not empties:
        return (0, 0)  # should never happen in legal Hex positions

    # Opening: prefer center if available
    if len(me_set) + len(opp_set) == 0:
        if (5, 5) in empties:
            return (5, 5)
        return min(empties, key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))

    # 1) Immediate win
    mv = winning_move_exists(me_set, opp_set, color)
    if mv is not None:
        return mv

    # 2) Immediate block of opponent win
    opp_color = 'w' if color == 'b' else 'b'
    mv = winning_move_exists(opp_set, me_set, opp_color)
    if mv is not None and mv in empties:
        return mv

    # Baseline path costs
    my_base = shortest_path_cost(me_set, opp_set, color)
    opp_base = shortest_path_cost(opp_set, me_set, opp_color)

    best_move = None
    best_score = -10**18

    for mv in empties:
        r, c = mv

        new_me = set(me_set)
        new_me.add(mv)

        my_new = shortest_path_cost(new_me, opp_set, color)
        opp_new = shortest_path_cost(opp_set, new_me, opp_color)

        # Improvement for me and damage to opponent
        my_gain = my_base - my_new
        opp_hurt = opp_new - opp_base

        score = 0.0
        score += 8.0 * my_gain
        score += 5.5 * opp_hurt
        score += local_features(mv, me_set, opp_set, color)

        # Prefer moves that create immediate strong connected structure
        my_adj = sum((nb in me_set) for nb in neighbors(r, c))
        if my_adj >= 2:
            score += 1.0
        if my_adj >= 3:
            score += 0.8

        # Mild urgency if opponent is close
        if opp_base <= 2:
            score += 1.5 * opp_hurt

        # Tiny deterministic tiebreak
        score += 1e-4 * (10 - abs(r - 5) - abs(c - 5))
        score += 1e-6 * (r * N + c)

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Fallback: guaranteed legal
    return empties[0]
