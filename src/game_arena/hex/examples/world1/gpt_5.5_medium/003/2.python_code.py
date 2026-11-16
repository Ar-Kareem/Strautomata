
from heapq import heappush, heappop

N = 11
INF = 10 ** 9
BIG = 10 ** 8

DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
CELLS = [(r, c) for r in range(N) for c in range(N)]


def _in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


NEIGH = {}
for r, c in CELLS:
    ns = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if _in_bounds(rr, cc):
            ns.append((rr, cc))
    NEIGH[(r, c)] = ns


BRIDGE_PARTNERS = {cell: [] for cell in CELLS}
for a in CELLS:
    sa = set(NEIGH[a])
    for b in CELLS:
        if a == b or b in sa:
            continue
        common = tuple(x for x in NEIGH[a] if x in NEIGH[b])
        if len(common) == 2:
            BRIDGE_PARTNERS[a].append((b, common))


COMMON_BRIDGES = {cell: [] for cell in CELLS}
for a in CELLS:
    for b, commons in BRIDGE_PARTNERS[a]:
        if a < b:
            x, y = commons
            COMMON_BRIDGES[x].append((a, b, y))
            COMMON_BRIDGES[y].append((a, b, x))


def _opp_color(color):
    return "w" if color == "b" else "b"


def _start_side_cells(color, side):
    if color == "b":
        row = 0 if side == 0 else N - 1
        return [(row, c) for c in range(N)]
    else:
        col = 0 if side == 0 else N - 1
        return [(r, col) for r in range(N)]


def _is_target(cell, color):
    r, c = cell
    if color == "b":
        return r == N - 1
    return c == N - 1


def _cell_cost(cell, own, block):
    if cell in block:
        return INF
    if cell in own:
        return 0
    return 1


def _path_distance(own, block, color):
    """Minimum number of empty cells needed for color to connect."""
    dist = [[INF] * N for _ in range(N)]
    heap = []

    for cell in _start_side_cells(color, 0):
        cost = _cell_cost(cell, own, block)
        if cost >= INF:
            continue
        r, c = cell
        if cost < dist[r][c]:
            dist[r][c] = cost
            heappush(heap, (cost, r, c))

    while heap:
        d, r, c = heappop(heap)
        if d != dist[r][c]:
            continue
        if _is_target((r, c), color):
            return d
        for rr, cc in NEIGH[(r, c)]:
            step = _cell_cost((rr, cc), own, block)
            if step >= INF:
                continue
            nd = d + step
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                heappush(heap, (nd, rr, cc))

    return INF


def _dist_from_side(own, block, color, side):
    dist = [[INF] * N for _ in range(N)]
    heap = []

    for cell in _start_side_cells(color, side):
        cost = _cell_cost(cell, own, block)
        if cost >= INF:
            continue
        r, c = cell
        dist[r][c] = cost
        heappush(heap, (cost, r, c))

    while heap:
        d, r, c = heappop(heap)
        if d != dist[r][c]:
            continue
        for rr, cc in NEIGH[(r, c)]:
            step = _cell_cost((rr, cc), own, block)
            if step >= INF:
                continue
            nd = d + step
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                heappush(heap, (nd, rr, cc))

    return dist


def _connected(own, color):
    if color == "b":
        starts = [s for s in own if s[0] == 0]
        target = lambda x: x[0] == N - 1
    else:
        starts = [s for s in own if s[1] == 0]
        target = lambda x: x[1] == N - 1

    if not starts:
        return False

    seen = set(starts)
    stack = starts[:]
    while stack:
        x = stack.pop()
        if target(x):
            return True
        for nb in NEIGH[x]:
            if nb in own and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def _winning_moves(own, block, color, empties):
    wins = []
    for mv in empties:
        new_own = set(own)
        new_own.add(mv)
        if _connected(new_own, color):
            wins.append(mv)
    return wins


def _shape_heuristic(mv, own, opp, color):
    r, c = mv

    # Centrality is a useful opening and tie-breaking principle in Hex.
    center = abs(r - 5) + abs(c - 5)
    score = -2.0 * center

    own_n = 0
    opp_n = 0
    for nb in NEIGH[mv]:
        if nb in own:
            own_n += 1
        elif nb in opp:
            opp_n += 1

    # Prefer useful contact, but avoid valuing pure clumping too highly.
    if own_n == 0:
        score -= 4
    else:
        score += 10 + 5 * own_n
    score += 3 * opp_n

    # Endpoint bridge creation: a classic Hex virtual-connection pattern.
    for p, commons in BRIDGE_PARTNERS[mv]:
        if p in own:
            blocked = any(x in opp for x in commons)
            if not blocked:
                own_common = sum(1 for x in commons if x in own)
                score += 15 + 5 * own_common

    # Cutting or contesting opponent bridges.
    for a, b, other in COMMON_BRIDGES[mv]:
        if a in opp and b in opp:
            if other not in own:
                score += 9
            else:
                score += 2

    # Mild side-awareness: stones near the relevant axis center are more flexible.
    if color == "b":
        score -= 0.5 * abs(c - 5)
    else:
        score -= 0.5 * abs(r - 5)

    return score


def _eval_position(my, opp, color):
    oc = _opp_color(color)

    if _connected(my, color):
        return BIG
    if _connected(opp, oc):
        return -BIG

    md = _path_distance(my, opp, color)
    od = _path_distance(opp, my, oc)

    if md >= INF:
        md = 1000
    if od >= INF:
        od = 1000

    score = (od - md) * 1500

    # One-move threats matter enormously.
    if md == 1:
        score += 7000
    if od == 1:
        score -= 9000
    if md == 2:
        score += 900
    if od == 2:
        score -= 1100

    return score


def _score_move(mv, own, opp, color):
    new_own = set(own)
    new_own.add(mv)

    if _connected(new_own, color):
        return BIG + _shape_heuristic(mv, own, opp, color)

    score = _eval_position(new_own, opp, color)
    score += 8.0 * _shape_heuristic(mv, own, opp, color)
    return score


def _fast_reply_scores(own, opp, color, empties):
    """
    Fast approximate move ordering for the side represented by own/color.
    Used only to choose plausible opponent replies for shallow minimax.
    """
    oc = _opp_color(color)

    cur_my = _path_distance(own, opp, color)
    cur_opp = _path_distance(opp, own, oc)

    ds_my = _dist_from_side(own, opp, color, 0)
    de_my = _dist_from_side(own, opp, color, 1)
    ds_opp = _dist_from_side(opp, own, oc, 0)
    de_opp = _dist_from_side(opp, own, oc, 1)

    result = []
    for mv in empties:
        r, c = mv

        # Estimate how much playing mv shortens our own path.
        my_est = cur_my
        if ds_my[r][c] < INF and de_my[r][c] < INF:
            # mv changes from empty cost 1 to own cost 0, improving paths through it by 1.
            my_est = min(my_est, ds_my[r][c] + de_my[r][c] - 2)

        # Estimate how important mv is for blocking opponent paths.
        block_value = 0
        if ds_opp[r][c] < INF and de_opp[r][c] < INF:
            opp_through = ds_opp[r][c] + de_opp[r][c] - 1
            block_value = max(0, cur_opp + 3 - opp_through)

        val = -900 * my_est + 550 * block_value
        if my_est <= 0:
            val += BIG // 2
        if my_est == 1:
            val += 5000
        val += 8.0 * _shape_heuristic(mv, own, opp, color)
        result.append((val, mv))

    result.sort(reverse=True, key=lambda x: x[0])
    return result


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my = set(me)
    op = set(opp)
    occupied = my | op
    empties = [cell for cell in CELLS if cell not in occupied]

    # Legal fallback; a valid Hex game should always have an empty cell here.
    if not empties:
        return (0, 0)

    # Strong simple openings.
    if len(occupied) == 0:
        return (5, 5)

    if len(occupied) == 1:
        opening = []
        if color == "b":
            opening = [(5, 5), (4, 5), (6, 5), (5, 4), (5, 6), (4, 6), (6, 4)]
        else:
            opening = [(5, 5), (5, 4), (5, 6), (4, 5), (6, 5), (4, 6), (6, 4)]
        for mv in opening:
            if mv in empties:
                return mv

    oc = _opp_color(color)

    # Immediate win.
    my_wins = _winning_moves(my, op, color, empties)
    if my_wins:
        return max(my_wins, key=lambda m: _shape_heuristic(m, my, op, color))

    # Forced immediate block.
    opp_wins = _winning_moves(op, my, oc, empties)
    if opp_wins:
        return max(opp_wins, key=lambda m: _shape_heuristic(m, my, op, color))

    # Exact one-ply scoring for every legal move.
    scored = [(_score_move(mv, my, op, color), mv) for mv in empties]
    scored.sort(reverse=True, key=lambda x: x[0])

    # Shallow minimax over the most plausible moves.
    if len(empties) > 80:
        cand_limit = 10
        reply_limit = 9
    else:
        cand_limit = 14
        reply_limit = 12

    candidates = scored[:cand_limit]
    best_move = candidates[0][1]
    best_value = -INF

    for first_score, mv in candidates:
        new_my = set(my)
        new_my.add(mv)

        if _connected(new_my, color):
            return mv

        rem = [x for x in empties if x != mv]
        if not rem:
            val = _eval_position(new_my, op, color)
            if val > best_value:
                best_value = val
                best_move = mv
            continue

        reply_set = set()

        # Always include opponent instant wins if we accidentally allow any.
        opp_instant = _winning_moves(op, new_my, oc, rem)
        for x in opp_instant:
            reply_set.add(x)

        # Include blocks to our own one-move wins.
        my_next_wins = _winning_moves(new_my, op, color, rem)
        for x in my_next_wins:
            reply_set.add(x)

        # Add likely opponent replies by fast ordering.
        fast_replies = _fast_reply_scores(op, new_my, oc, rem)
        for _, x in fast_replies[:reply_limit]:
            reply_set.add(x)

        if not reply_set:
            val = _eval_position(new_my, op, color)
        else:
            # Opponent chooses the reply that is worst for us.
            worst = INF
            for reply in reply_set:
                new_op = set(op)
                new_op.add(reply)
                v = _eval_position(new_my, new_op, color)
                if v < worst:
                    worst = v
            val = worst

        # Tie-break with the first-ply score/shape.
        val += 0.01 * first_score

        if val > best_value:
            best_value = val
            best_move = mv

    # Final legality guard.
    if best_move in empties:
        return best_move

    return empties[0]
