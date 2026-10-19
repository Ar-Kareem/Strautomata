
from heapq import heappush, heappop

N = 11
INF = 10 ** 9

# Hex neighbors for the coordinate system described in the prompt.
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not empties:
        return (0, 0)  # Should never happen in a legal game.

    # Strong, safe opening preference.
    opening = [
        (5, 5), (5, 4), (4, 5), (6, 5), (5, 6),
        (4, 6), (6, 4), (4, 4), (6, 6)
    ]
    if len(occupied) <= 1:
        for mv in opening:
            if mv not in occupied:
                return mv

    opp_color = "w" if color == "b" else "b"

    # 1. Win immediately if possible.
    for mv in ordered_by_center(empties):
        if is_win(me_set | {mv}, color):
            return mv

    # 2. Block an immediate opponent win if one exists.
    opp_wins = []
    for mv in empties:
        if is_win(opp_set | {mv}, opp_color):
            opp_wins.append(mv)

    if opp_wins:
        # If there are several winning points, choose the one that is also best for us.
        return max(opp_wins, key=lambda m: quick_static_score(m, me_set, opp_set, color))

    # Current shortest-path fields.
    my_ds, my_de, my_dist = dijkstra_fields(me_set, opp_set, color)
    op_ds, op_de, op_dist = dijkstra_fields(opp_set, me_set, opp_color)

    scored = []
    for mv in empties:
        r, c = mv

        new_me = me_set | {mv}

        # Exact one-ply distances after our move.
        my_after = shortest_distance(new_me, opp_set, color)
        op_after = shortest_distance(opp_set, new_me, opp_color)

        # Potential of this cell on current shortest paths.
        my_pot = path_potential(mv, my_ds, my_de)
        op_pot = path_potential(mv, op_ds, op_de)

        own_adj = 0
        opp_adj = 0
        empty_adj = 0
        for nb in neighbors(r, c):
            if nb in me_set:
                own_adj += 1
            elif nb in opp_set:
                opp_adj += 1
            else:
                empty_adj += 1

        center_bonus = 12 - (abs(r - 5) + abs(c - 5))

        # Encourage playing on useful own paths and important opponent paths.
        pot_score = 0
        if my_pot < INF:
            pot_score += 650.0 / (1.0 + my_pot)
            if my_pot == my_dist:
                pot_score += 180
        if op_pot < INF:
            pot_score += 780.0 / (1.0 + op_pot)
            if op_pot == op_dist:
                pot_score += 230

        # Main score: reduce our connection cost, increase opponent's.
        score = 0.0
        score += 5200 * (my_dist - my_after)
        score += 5000 * (op_after - op_dist)
        score += 1100 * (op_after - my_after)

        # Threat logic.
        if my_after == 1:
            score += 4200
        if op_after == 1:
            # Opponent would have an immediate winning reply.
            score -= 20000

        # Local shape and board-control terms.
        score += pot_score
        score += 90 * own_adj
        score += 55 * opp_adj
        score += 12 * empty_adj
        score += 9 * center_bonus
        score += bridge_bonus(mv, me_set, opp_set)

        scored.append((score, mv, my_after, op_after))

    scored.sort(reverse=True, key=lambda x: x[0])

    # If the top move is very forcing, avoid unnecessary lookahead risk.
    if scored and scored[0][2] == 1 and scored[0][3] > 1:
        return scored[0][1]

    # 3. Small opponent-reply lookahead among the best candidates.
    best_move = scored[0][1]
    best_value = -INF

    top_my = scored[:min(10, len(scored))]
    for base_score, mv, my_after, op_after in top_my:
        new_me = me_set | {mv}
        new_occ = occupied | {mv}
        reply_empties = [e for e in empties if e != mv]

        # If opponent has an immediate win after this move, heavily penalize.
        if op_after == 1:
            value = -100000 + base_score
            if value > best_value:
                best_value = value
                best_move = mv
            continue

        # Generate likely opponent replies from opponent perspective.
        reply_scored = []
        op_ds2, op_de2, op_dist2 = dijkstra_fields(opp_set, new_me, opp_color)
        my_ds2, my_de2, my_dist2 = dijkstra_fields(new_me, opp_set, color)

        for rep in reply_empties:
            rp = path_potential(rep, op_ds2, op_de2)
            mp = path_potential(rep, my_ds2, my_de2)
            rs = quick_static_score(rep, opp_set, new_me, opp_color)
            if rp < INF:
                rs += 500.0 / (1.0 + rp)
                if rp == op_dist2:
                    rs += 160
            if mp < INF:
                # Opponent likes blocking our good path too.
                rs += 450.0 / (1.0 + mp)
                if mp == my_dist2:
                    rs += 150
            reply_scored.append((rs, rep))

        reply_scored.sort(reverse=True, key=lambda x: x[0])
        likely_replies = reply_scored[:min(14, len(reply_scored))]

        # Opponent chooses the reply that is worst for us.
        worst_for_us = INF
        for _, rep in likely_replies:
            after_opp = opp_set | {rep}

            if is_win(after_opp, opp_color):
                val = -100000
            else:
                my_d = shortest_distance(new_me, after_opp, color)
                op_d = shortest_distance(after_opp, new_me, opp_color)

                val = 1500 * (op_d - my_d)

                # Prefer positions where we retain immediate threats and opponent does not.
                if my_d == 1:
                    val += 2500
                if op_d == 1:
                    val -= 4500

                # Modest carry-over from the original move quality.
                val += 0.18 * base_score

            if val < worst_for_us:
                worst_for_us = val

        if not likely_replies:
            worst_for_us = base_score

        if worst_for_us > best_value:
            best_value = worst_for_us
            best_move = mv

    # Absolute legality guard.
    if best_move in occupied or not on_board(*best_move):
        return ordered_by_center(empties)[0]

    return best_move


def on_board(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield (nr, nc)


def ordered_by_center(cells):
    return sorted(cells, key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))


def is_win(stones: set[tuple[int, int]], color: str) -> bool:
    if not stones:
        return False

    stack = []
    seen = set()

    if color == "b":
        for c in range(N):
            p = (0, c)
            if p in stones:
                stack.append(p)
                seen.add(p)

        while stack:
            r, c = stack.pop()
            if r == N - 1:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    else:
        for r in range(N):
            p = (r, 0)
            if p in stones:
                stack.append(p)
                seen.add(p)

        while stack:
            r, c = stack.pop()
            if c == N - 1:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    return False


def cell_index(r: int, c: int) -> int:
    return r * N + c


def index_cell(i: int) -> tuple[int, int]:
    return divmod(i, N)


def edge_cells(color: str, start: bool):
    if color == "b":
        row = 0 if start else N - 1
        return [(row, c) for c in range(N)]
    else:
        col = 0 if start else N - 1
        return [(r, col) for r in range(N)]


def dijkstra_fields(own: set[tuple[int, int]], enemy: set[tuple[int, int]], color: str):
    ds = dijkstra_from_edge(own, enemy, color, True)
    de = dijkstra_from_edge(own, enemy, color, False)

    if color == "b":
        total = min(ds[cell_index(N - 1, c)] for c in range(N))
    else:
        total = min(ds[cell_index(r, N - 1)] for r in range(N))

    return ds, de, total


def dijkstra_from_edge(own: set[tuple[int, int]], enemy: set[tuple[int, int]], color: str, start: bool):
    dist = [INF] * (N * N)
    heap = []

    for r, c in edge_cells(color, start):
        if (r, c) in enemy:
            continue
        cost = 0 if (r, c) in own else 1
        idx = cell_index(r, c)
        if cost < dist[idx]:
            dist[idx] = cost
            heappush(heap, (cost, r, c))

    while heap:
        d, r, c = heappop(heap)
        idx = cell_index(r, c)
        if d != dist[idx]:
            continue

        for nr, nc in neighbors(r, c):
            if (nr, nc) in enemy:
                continue
            step = 0 if (nr, nc) in own else 1
            nd = d + step
            ni = cell_index(nr, nc)
            if nd < dist[ni]:
                dist[ni] = nd
                heappush(heap, (nd, nr, nc))

    return dist


def shortest_distance(own: set[tuple[int, int]], enemy: set[tuple[int, int]], color: str) -> int:
    ds = dijkstra_from_edge(own, enemy, color, True)
    if color == "b":
        return min(ds[cell_index(N - 1, c)] for c in range(N))
    else:
        return min(ds[cell_index(r, N - 1)] for r in range(N))


def path_potential(cell: tuple[int, int], ds, de) -> int:
    r, c = cell
    idx = cell_index(r, c)
    if ds[idx] >= INF or de[idx] >= INF:
        return INF
    # The cell is empty when used for candidate potential, so subtract its cost once.
    return ds[idx] + de[idx] - 1


def quick_static_score(mv: tuple[int, int], own: set[tuple[int, int]], enemy: set[tuple[int, int]], color: str) -> float:
    r, c = mv

    own_adj = 0
    enemy_adj = 0
    empty_adj = 0
    for nb in neighbors(r, c):
        if nb in own:
            own_adj += 1
        elif nb in enemy:
            enemy_adj += 1
        else:
            empty_adj += 1

    center = 12 - (abs(r - 5) + abs(c - 5))

    # Slight orientation preference: black likes central columns, white likes central rows.
    if color == "b":
        orient = 5 - abs(c - 5)
    else:
        orient = 5 - abs(r - 5)

    score = 0.0
    score += 95 * own_adj
    score += 60 * enemy_adj
    score += 10 * empty_adj
    score += 10 * center
    score += 8 * orient
    score += bridge_bonus(mv, own, enemy)

    return score


def bridge_bonus(mv: tuple[int, int], own: set[tuple[int, int]], enemy: set[tuple[int, int]]) -> float:
    """
    Rewards moves that participate in simple Hex bridge-like patterns.
    This is intentionally lightweight and conservative.
    """
    r, c = mv
    bonus = 0.0

    # Common two-step patterns in this coordinate system.
    patterns = [
        ((-1, -1), ((-1, 0), (0, -1))),
        ((-1, 2), ((-1, 1), (0, 1))),
        ((1, -2), ((1, -1), (0, -1))),
        ((1, 1), ((1, 0), (0, 1))),
        ((-2, 1), ((-1, 0), (-1, 1))),
        ((2, -1), ((1, 0), (1, -1))),
    ]

    for (dr, dc), mids in patterns:
        far = (r + dr, c + dc)
        if not on_board(*far) or far not in own:
            continue

        clear = True
        for mr, mc in mids:
            mid = (r + mr, c + mc)
            if not on_board(*mid) or mid in enemy:
                clear = False
                break

        if clear:
            bonus += 75

    return bonus
