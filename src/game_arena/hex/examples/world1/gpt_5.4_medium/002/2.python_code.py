
from collections import deque

N = 11
INF = 10**9
CELLS = [(r, c) for r in range(N) for c in range(N)]

# Hex neighbors in the board coordinate system described in the prompt.
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]

NEI = {}
NEI_SET = {}
for r in range(N):
    for c in range(N):
        lst = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                lst.append((rr, cc))
        NEI[(r, c)] = lst
        NEI_SET[(r, c)] = frozenset(lst)


def other(color: str) -> str:
    return "w" if color == "b" else "b"


def side_cells(color: str, start: bool):
    if color == "b":
        row = 0 if start else N - 1
        return [(row, c) for c in range(N)]
    else:
        col = 0 if start else N - 1
        return [(r, col) for r in range(N)]


def is_win(stones: set[tuple[int, int]], color: str) -> bool:
    if not stones:
        return False

    q = deque()
    seen = set()

    if color == "b":
        for c in range(N):
            cell = (0, c)
            if cell in stones:
                q.append(cell)
                seen.add(cell)
        target = N - 1
        while q:
            r, c = q.popleft()
            if r == target:
                return True
            for nb in NEI[(r, c)]:
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
    else:
        for r in range(N):
            cell = (r, 0)
            if cell in stones:
                q.append(cell)
                seen.add(cell)
        target = N - 1
        while q:
            r, c = q.popleft()
            if c == target:
                return True
            for nb in NEI[(r, c)]:
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
    return False


def zero_one_bfs(me: set[tuple[int, int]], opp: set[tuple[int, int]], color: str, start: bool):
    dist = [[INF] * N for _ in range(N)]
    dq = deque()

    for cell in side_cells(color, start):
        if cell in opp:
            continue
        r, c = cell
        w = 0 if cell in me else 1
        if w < dist[r][c]:
            dist[r][c] = w
            if w == 0:
                dq.appendleft(cell)
            else:
                dq.append(cell)

    while dq:
        r, c = dq.popleft()
        base = dist[r][c]
        for rr, cc in NEI[(r, c)]:
            if (rr, cc) in opp:
                continue
            w = 0 if (rr, cc) in me else 1
            nd = base + w
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                if w == 0:
                    dq.appendleft((rr, cc))
                else:
                    dq.append((rr, cc))
    return dist


def shortest_path_cost(me: set[tuple[int, int]], opp: set[tuple[int, int]], color: str) -> int:
    dist = zero_one_bfs(me, opp, color, True)
    best = INF
    if color == "b":
        row = N - 1
        for c in range(N):
            if dist[row][c] < best:
                best = dist[row][c]
    else:
        col = N - 1
        for r in range(N):
            if dist[r][col] < best:
                best = dist[r][col]
    return best


def critical_empty_scores(
    me: set[tuple[int, int]],
    opp: set[tuple[int, int]],
    color: str,
    empties: list[tuple[int, int]],
):
    fwd = zero_one_bfs(me, opp, color, True)
    bwd = zero_one_bfs(me, opp, color, False)

    best = INF
    if color == "b":
        row = N - 1
        for c in range(N):
            if fwd[row][c] < best:
                best = fwd[row][c]
    else:
        col = N - 1
        for r in range(N):
            if fwd[r][col] < best:
                best = fwd[r][col]

    crit = {}
    if best >= INF:
        return crit, best

    for r, c in empties:
        a = fwd[r][c]
        b = bwd[r][c]
        if a >= INF or b >= INF:
            continue
        total = a + b - 1  # empty cell counted twice otherwise
        crit[(r, c)] = total - best  # 0 means on a shortest path
    return crit, best


def component_span_score(stones: set[tuple[int, int]], color: str) -> int:
    if not stones:
        return 0

    axis = 0 if color == "b" else 1
    seen = set()
    best = 0

    for s in stones:
        if s in seen:
            continue
        stack = [s]
        seen.add(s)
        size = 0
        mn = s[axis]
        mx = s[axis]
        touch_lo = False
        touch_hi = False

        while stack:
            u = stack.pop()
            size += 1
            v = u[axis]
            if v < mn:
                mn = v
            if v > mx:
                mx = v
            if v == 0:
                touch_lo = True
            if v == N - 1:
                touch_hi = True
            for nb in NEI[u]:
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

        score = 4 * (mx - mn) + size
        if touch_lo:
            score += 2
        if touch_hi:
            score += 2
        if score > best:
            best = score
    return best


def eval_state(me: set[tuple[int, int]], opp: set[tuple[int, int]], color: str) -> int:
    myc = shortest_path_cost(me, opp, color)
    oppc = shortest_path_cost(opp, me, other(color))

    if myc == 0:
        return 100000
    if oppc == 0:
        return -100000
    if myc >= INF and oppc >= INF:
        base = 0
    elif myc >= INF:
        return -50000
    elif oppc >= INF:
        return 50000
    else:
        base = 120 * (oppc - myc)

    span_me = component_span_score(me, color)
    span_opp = component_span_score(opp, other(color))
    base += 3 * (span_me - span_opp)

    return base


def bridge_potential(move, me: set[tuple[int, int]], opp: set[tuple[int, int]]) -> int:
    near2 = set()
    for n in NEI[move]:
        near2.update(NEI[n])

    total = 0
    for s in near2:
        if s == move or s not in me or s in NEI_SET[move]:
            continue
        common = 0
        for x in NEI[move]:
            if x in NEI_SET[s] and x not in opp:
                common += 1
        if common >= 2:
            total += 1
    return total


def local_move_heuristic(
    move,
    me: set[tuple[int, int]],
    opp: set[tuple[int, int]],
    color: str,
    my_crit: dict,
    opp_crit: dict,
) -> int:
    adj_me = 0
    adj_opp = 0
    for nb in NEI[move]:
        if nb in me:
            adj_me += 1
        elif nb in opp:
            adj_opp += 1

    score = 8 * adj_me + 6 * adj_opp

    if move in my_crit:
        slack = my_crit[move]
        score += max(0, 30 - 6 * slack)
    if move in opp_crit:
        slack = opp_crit[move]
        score += max(0, 24 - 6 * slack)

    score += 4 * bridge_potential(move, me, opp)

    r, c = move
    if color == "b":
        score -= 2 * abs(c - 5) + abs(r - 5)
    else:
        score -= 2 * abs(r - 5) + abs(c - 5)

    return score


def generate_candidates(
    me: set[tuple[int, int]],
    opp: set[tuple[int, int]],
    color: str,
    empties: list[tuple[int, int]],
    limit: int,
):
    if len(empties) <= limit:
        return list(empties)

    my_crit, _ = critical_empty_scores(me, opp, color, empties)
    opp_crit, _ = critical_empty_scores(opp, me, other(color), empties)

    scored = []
    for mv in empties:
        s = local_move_heuristic(mv, me, opp, color, my_crit, opp_crit)
        scored.append((s, mv))
    scored.sort(reverse=True)
    return [mv for _, mv in scored[:limit]]


def find_winning_moves(
    player: set[tuple[int, int]],
    opp: set[tuple[int, int]],
    color: str,
    empties: list[tuple[int, int]],
    max_count=None,
):
    wins = []
    for mv in empties:
        if is_win(player | {mv}, color):
            wins.append(mv)
            if max_count is not None and len(wins) >= max_count:
                break
    return wins


def fallback_move(empties: list[tuple[int, int]], color: str):
    if not empties:
        return (0, 0)
    def key(mv):
        r, c = mv
        if color == "b":
            return (2 * abs(c - 5) + abs(r - 5), abs(r - 5) + abs(c - 5), r, c)
        else:
            return (2 * abs(r - 5) + abs(c - 5), abs(r - 5) + abs(c - 5), r, c)
    return min(empties, key=key)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    # Safety against malformed overlap.
    me_set -= opp_set

    occupied = me_set | opp_set
    empties = [cell for cell in CELLS if cell not in occupied]

    if not empties:
        return (0, 0)

    # Opening: center is strong on 11x11 Hex.
    if not me_set and not opp_set:
        return (5, 5)

    # 1) Immediate win if available.
    my_wins = find_winning_moves(me_set, opp_set, color, empties, max_count=1)
    if my_wins:
        return my_wins[0]

    opp_color = other(color)

    # 2) Immediate block if opponent has a forced win next turn.
    opp_wins = find_winning_moves(opp_set, me_set, opp_color, empties, max_count=3)
    if len(opp_wins) == 1:
        return opp_wins[0]

    # Root candidate set:
    # - if multiple opponent winning threats exist, try only threat cells
    # - otherwise evaluate all legal moves
    root_moves = opp_wins[:] if len(opp_wins) > 1 else empties

    # Root critical maps for local tie-breaking.
    my_crit, _ = critical_empty_scores(me_set, opp_set, color, empties)
    opp_crit, _ = critical_empty_scores(opp_set, me_set, opp_color, empties)

    prelim = []
    for mv in root_moves:
        me2 = me_set | {mv}
        score = eval_state(me2, opp_set, color)
        score += local_move_heuristic(mv, me_set, opp_set, color, my_crit, opp_crit)
        prelim.append((score, mv))

    if not prelim:
        return fallback_move(empties, color)

    prelim.sort(reverse=True)

    # Small minimax lookahead on best candidates.
    top_k = 8 if len(prelim) > 8 else len(prelim)
    best_move = prelim[0][1]
    best_score = -10**18

    for pre_score, mv in prelim[:top_k]:
        me2 = me_set | {mv}
        empties2 = [x for x in empties if x != mv]

        # If this move allows an immediate winning reply, heavily punish it.
        opp_immediate = find_winning_moves(opp_set, me2, opp_color, empties2, max_count=1)
        if opp_immediate:
            final_score = -100000 + pre_score // 100
        else:
            opp_cands = generate_candidates(opp_set, me2, opp_color, empties2, limit=8)

            if not opp_cands:
                final_score = eval_state(me2, opp_set, color)
            else:
                worst_reply = 10**18
                for omv in opp_cands:
                    opp2 = opp_set | {omv}
                    if is_win(opp2, opp_color):
                        reply_score = -100000
                    else:
                        reply_score = eval_state(me2, opp2, color)
                    if reply_score < worst_reply:
                        worst_reply = reply_score
                final_score = worst_reply + pre_score // 20  # slight tie-break from root quality

        if final_score > best_score:
            best_score = final_score
            best_move = mv

    # Final legality guard.
    if best_move in occupied or not (0 <= best_move[0] < N and 0 <= best_move[1] < N):
        return fallback_move(empties, color)
    return best_move
