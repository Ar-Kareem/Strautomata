
from heapq import heappush, heappop

N = 11
NN = N * N
INF = 10 ** 9

# Hex neighbor directions for the coordinate system described in the prompt.
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _idx(r, c):
    return r * N + c


def _rc(i):
    return divmod(i, N)


NEIGH = [[] for _ in range(NN)]
NEIGH_SET = [set() for _ in range(NN)]
for r in range(N):
    for c in range(N):
        i = _idx(r, c)
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                j = _idx(rr, cc)
                NEIGH[i].append(j)
                NEIGH_SET[i].add(j)

BLACK_START = [_idx(0, c) for c in range(N)]
BLACK_GOAL = set(_idx(N - 1, c) for c in range(N))
WHITE_START = [_idx(r, 0) for r in range(N)]
WHITE_GOAL = set(_idx(r, N - 1) for r in range(N))

CENTER_ORDER = sorted(
    range(NN),
    key=lambda x: (abs(_rc(x)[0] - 5) + abs(_rc(x)[1] - 5),
                   (_rc(x)[0] - 5) ** 2 + (_rc(x)[1] - 5) ** 2)
)

# Precompute bridge-like relations.
# Two stones at hex distance 2 with exactly two common neighbors form a typical Hex bridge.
BRIDGE_DATA = [[] for _ in range(NN)]
CUT_DATA = [[] for _ in range(NN)]
for a in range(NN):
    ar, ac = _rc(a)
    for b in range(a + 1, NN):
        br, bc = _rc(b)
        if abs(ar - br) > 2 or abs(ac - bc) > 2:
            continue
        if b in NEIGH_SET[a]:
            continue
        common = list(NEIGH_SET[a].intersection(NEIGH_SET[b]))
        if len(common) == 2:
            t = (common[0], common[1])
            BRIDGE_DATA[a].append((b, t))
            BRIDGE_DATA[b].append((a, t))
            CUT_DATA[common[0]].append((a, b, common[1]))
            CUT_DATA[common[1]].append((a, b, common[0]))


def _other(color):
    return 'w' if color == 'b' else 'b'


def _start_goal(color):
    if color == 'b':
        return BLACK_START, BLACK_GOAL
    return WHITE_START, WHITE_GOAL


def _cell_cost(i, mine, theirs):
    if i in theirs:
        return INF
    if i in mine:
        return 0
    return 1


def _shortest(mine, theirs, color, want_path=False):
    """Minimum number of empty cells still needed to connect."""
    starts, goals = _start_goal(color)
    dist = [INF] * NN
    prev = [-1] * NN
    heap = []

    for s in starts:
        cs = _cell_cost(s, mine, theirs)
        if cs < dist[s]:
            dist[s] = cs
            prev[s] = -2
            heappush(heap, (cs, s))

    best_goal = -1
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue
        if u in goals:
            best_goal = u
            if not want_path:
                return d
            break
        for v in NEIGH[u]:
            cv = _cell_cost(v, mine, theirs)
            if cv >= INF:
                continue
            nd = d + cv
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heappush(heap, (nd, v))

    if want_path:
        if best_goal < 0:
            best = INF
            for g in goals:
                if dist[g] < best:
                    best = dist[g]
                    best_goal = g
            if best_goal < 0 or best >= INF:
                return INF, set()

        path = set()
        x = best_goal
        while x >= 0:
            path.add(x)
            if prev[x] == -2:
                break
            x = prev[x]
        return dist[best_goal], path

    return INF


def _component_span(stones, color):
    if not stones:
        return 0

    seen = set()
    best = 0

    for s in stones:
        if s in seen:
            continue
        stack = [s]
        seen.add(s)

        rows = []
        cols = []

        while stack:
            u = stack.pop()
            r, c = _rc(u)
            rows.append(r)
            cols.append(c)

            for v in NEIGH[u]:
                if v in stones and v not in seen:
                    seen.add(v)
                    stack.append(v)

        if color == 'b':
            span = max(rows) - min(rows) + 1
            if min(rows) == 0:
                span += 2
            if max(rows) == N - 1:
                span += 2
        else:
            span = max(cols) - min(cols) + 1
            if min(cols) == 0:
                span += 2
            if max(cols) == N - 1:
                span += 2

        if span > best:
            best = span

    return best


def _static_eval(mine, theirs, color):
    opp_color = _other(color)

    my_d = _shortest(mine, theirs, color)
    op_d = _shortest(theirs, mine, opp_color)

    if my_d == 0:
        return 100000
    if op_d == 0:
        return -100000

    my_span = _component_span(mine, color)
    op_span = _component_span(theirs, opp_color)

    # Main term is the connection race. Span is a tie-breaker.
    return 1400 * (op_d - my_d) + 35 * (my_span - op_span)


def _shape_bonus(move, mine, theirs):
    r, c = _rc(move)
    center_penalty = abs(r - 5) + abs(c - 5)

    adj_own = 0
    adj_opp = 0
    for n in NEIGH[move]:
        if n in mine:
            adj_own += 1
        elif n in theirs:
            adj_opp += 1

    score = 12 * adj_own + 5 * adj_opp - 4 * center_penalty

    # Avoid totally isolated moves once we already have stones.
    if mine and adj_own == 0:
        score -= 20

    # Own bridge formation.
    for other, commons in BRIDGE_DATA[move]:
        if other in mine:
            a, b = commons
            if a not in theirs and b not in theirs:
                if a not in mine and b not in mine:
                    score += 26
                else:
                    score += 16
            elif a in mine or b in mine:
                score += 8

    # Cutting opponent bridges.
    for a, b, other_common in CUT_DATA[move]:
        if a in theirs and b in theirs:
            if other_common in mine:
                score += 42
            elif other_common not in theirs:
                score += 32

    return score


def _top_moves(mine, theirs, color, empties, limit=10):
    opp_color = _other(color)

    cur_my_d, my_path = _shortest(mine, theirs, color, True)
    cur_op_d, op_path = _shortest(theirs, mine, opp_color, True)

    scored = []

    for m in empties:
        if m in mine or m in theirs:
            continue

        mine2 = set(mine)
        mine2.add(m)

        my_d = _shortest(mine2, theirs, color)
        op_d = _shortest(theirs, mine2, opp_color)

        if my_d == 0:
            score = 100000 + _shape_bonus(m, mine, theirs)
        elif op_d == 0:
            score = -100000 + _shape_bonus(m, mine, theirs)
        else:
            score = 1400 * (op_d - my_d)
            score += 320 * (cur_my_d - my_d)
            score += 260 * (op_d - cur_op_d)

            if m in my_path:
                score += 90
            if m in op_path:
                score += 120
                if cur_op_d <= 2:
                    score += 180

            score += _shape_bonus(m, mine, theirs)

        scored.append((score, m))

    scored.sort(reverse=True)
    if limit is not None:
        scored = scored[:limit]
    return [(m, s) for s, m in scored]


def _first_legal(occupied):
    for i in CENTER_ORDER:
        if i not in occupied:
            return _rc(i)
    return (0, 0)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        mine = set(_idx(r, c) for r, c in me)
        theirs = set(_idx(r, c) for r, c in opp)
        occupied = mine | theirs

        empties = [i for i in range(NN) if i not in occupied]
        if not empties:
            return (0, 0)

        # Strong opening preference.
        if not occupied:
            return (5, 5)

        if not mine:
            for i in CENTER_ORDER:
                if i not in occupied:
                    return _rc(i)

        opp_color = _other(color)

        # Immediate win check.
        winning = []
        for m in empties:
            mine2 = set(mine)
            mine2.add(m)
            if _shortest(mine2, theirs, color) == 0:
                winning.append(m)

        if winning:
            # Prefer the most central/shape-sensible winning move.
            best = max(winning, key=lambda x: _shape_bonus(x, mine, theirs))
            return _rc(best)

        # Immediate opponent win block.
        opp_winning = []
        for m in empties:
            opp2 = set(theirs)
            opp2.add(m)
            if _shortest(opp2, mine, opp_color) == 0:
                opp_winning.append(m)

        if len(opp_winning) == 1:
            return _rc(opp_winning[0])

        # If opponent has multiple immediate wins, choose the best among blocking cells.
        forced = set(opp_winning) if opp_winning else None

        if forced:
            ranked_all = _top_moves(mine, theirs, color, empties, limit=None)
            candidates = [(m, s) for (m, s) in ranked_all if m in forced]
            if not candidates:
                candidates = [(m, _shape_bonus(m, mine, theirs)) for m in forced]
        else:
            candidates = _top_moves(mine, theirs, color, empties, limit=10)

        if not candidates:
            return _first_legal(occupied)

        best_move = candidates[0][0]
        best_score = -10 ** 18

        # Shallow defensive minimax:
        # for each candidate, assume opponent chooses one of its best replies.
        for m, oneply_score in candidates:
            if m in occupied:
                continue

            mine2 = set(mine)
            mine2.add(m)

            # Candidate itself may have become a win through a tactical path.
            if _shortest(mine2, theirs, color) == 0:
                return _rc(m)

            occ2 = occupied | {m}
            empties2 = [x for x in empties if x != m]

            replies = _top_moves(theirs, mine2, opp_color, empties2, limit=6)

            if not replies:
                final_score = _static_eval(mine2, theirs, color) + 0.15 * oneply_score
            else:
                worst = 10 ** 18
                for om, _os in replies:
                    theirs2 = set(theirs)
                    theirs2.add(om)

                    # If opponent can win immediately after our move, this is very bad.
                    if _shortest(theirs2, mine2, opp_color) == 0:
                        ev = -100000
                    else:
                        ev = _static_eval(mine2, theirs2, color)

                    if ev < worst:
                        worst = ev

                final_score = worst + 0.15 * oneply_score + 0.01 * _shape_bonus(m, mine, theirs)

            if final_score > best_score:
                best_score = final_score
                best_move = m

        if best_move not in occupied and 0 <= best_move < NN:
            return _rc(best_move)

        return _first_legal(occupied)

    except Exception:
        # Absolute safety fallback: always return a legal move if possible.
        occupied = set()
        for r, c in me:
            if 0 <= r < N and 0 <= c < N:
                occupied.add(_idx(r, c))
        for r, c in opp:
            if 0 <= r < N and 0 <= c < N:
                occupied.add(_idx(r, c))
        return _first_legal(occupied)
