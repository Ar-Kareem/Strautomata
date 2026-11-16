
import numpy as np
from collections import deque

BOARD_SIZE = 11

NEIGHBOR_DELTAS = [
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
]

# 6 bridge directions: (dr, dc) -> two shared neighbor deltas
BRIDGE_DELTAS = [
    ((-1, 2), [(-1, 1), (0, 1)]),
    ((1, 1), [(0, 1), (1, 0)]),
    ((2, -1), [(1, 0), (1, -1)]),
    ((1, -2), [(1, -1), (0, -1)]),
    ((-1, -1), [(0, -1), (-1, 0)]),
    ((-2, 1), [(-1, 0), (-1, 1)]),
]


def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    neighbors = []
    for dr, dc in NEIGHBOR_DELTAS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            neighbors.append((nr, nc))
    return neighbors


def get_dists_black(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    dist_top = {}
    q = deque()
    for c in range(BOARD_SIZE):
        pos = (0, c)
        if pos not in opp_set:
            cost = 0 if pos in me_set else 1
            dist_top[pos] = cost
            if cost == 0:
                q.appendleft(pos)
            else:
                q.append(pos)

    while q:
        r, c = q.popleft()
        d = dist_top[(r, c)]
        for nr, nc in get_neighbors(r, c):
            npos = (nr, nc)
            if npos not in opp_set:
                cost = 0 if npos in me_set else 1
                if npos not in dist_top or d + cost < dist_top[npos]:
                    dist_top[npos] = d + cost
                    if cost == 0:
                        q.appendleft(npos)
                    else:
                        q.append(npos)

    dist_bot = {}
    q = deque()
    for c in range(BOARD_SIZE):
        pos = (BOARD_SIZE - 1, c)
        if pos not in opp_set:
            cost = 0 if pos in me_set else 1
            dist_bot[pos] = cost
            if cost == 0:
                q.appendleft(pos)
            else:
                q.append(pos)

    while q:
        r, c = q.popleft()
        d = dist_bot[(r, c)]
        for nr, nc in get_neighbors(r, c):
            npos = (nr, nc)
            if npos not in opp_set:
                cost = 0 if npos in me_set else 1
                if npos not in dist_bot or d + cost < dist_bot[npos]:
                    dist_bot[npos] = d + cost
                    if cost == 0:
                        q.appendleft(npos)
                    else:
                        q.append(npos)

    return dist_top, dist_bot


def get_dists_white(opp_set: set[tuple[int, int]], me_set: set[tuple[int, int]]):
    dist_left = {}
    q = deque()
    for r in range(BOARD_SIZE):
        pos = (r, 0)
        if pos not in me_set:
            cost = 0 if pos in opp_set else 1
            dist_left[pos] = cost
            if cost == 0:
                q.appendleft(pos)
            else:
                q.append(pos)

    while q:
        r, c = q.popleft()
        d = dist_left[(r, c)]
        for nr, nc in get_neighbors(r, c):
            npos = (nr, nc)
            if npos not in me_set:
                cost = 0 if npos in opp_set else 1
                if npos not in dist_left or d + cost < dist_left[npos]:
                    dist_left[npos] = d + cost
                    if cost == 0:
                        q.appendleft(npos)
                    else:
                        q.append(npos)

    dist_right = {}
    q = deque()
    for r in range(BOARD_SIZE):
        pos = (r, BOARD_SIZE - 1)
        if pos not in me_set:
            cost = 0 if pos in opp_set else 1
            dist_right[pos] = cost
            if cost == 0:
                q.appendleft(pos)
            else:
                q.append(pos)

    while q:
        r, c = q.popleft()
        d = dist_right[(r, c)]
        for nr, nc in get_neighbors(r, c):
            npos = (nr, nc)
            if npos not in me_set:
                cost = 0 if npos in opp_set else 1
                if npos not in dist_right or d + cost < dist_right[npos]:
                    dist_right[npos] = d + cost
                    if cost == 0:
                        q.appendleft(npos)
                    else:
                        q.append(npos)

    return dist_left, dist_right


def solve_currents_black(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    N = BOARD_SIZE * BOARD_SIZE
    A = np.zeros((N, N), dtype=np.float64)
    b = np.zeros(N, dtype=np.float64)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            idx = r * BOARD_SIZE + c
            pos = (r, c)
            if pos in opp_set:
                A[idx, idx] = 1.0
                b[idx] = 0.0
                continue

            is_me = pos in me_set
            diag = 0.0

            if r == 0:
                g_top = 40.0 if is_me else 2.0
                diag += g_top
                b[idx] += g_top * 1.0

            if r == BOARD_SIZE - 1:
                g_bot = 40.0 if is_me else 2.0
                diag += g_bot

            for nr, nc in get_neighbors(r, c):
                npos = (nr, nc)
                if npos in opp_set:
                    continue
                nidx = nr * BOARD_SIZE + nc
                is_nme = npos in me_set
                if is_me and is_nme:
                    g = 25.0
                elif is_me or is_nme:
                    g = 2.5
                else:
                    g = 1.0
                diag += g
                A[idx, nidx] -= g

            A[idx, idx] = diag + 1e-5

    try:
        V = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return {}

    currents = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            pos = (r, c)
            if pos in me_set or pos in opp_set:
                continue
            idx = r * BOARD_SIZE + c
            val = V[idx]
            cur = 0.0
            if r == 0:
                cur += 2.0 * abs(val - 1.0)
            if r == BOARD_SIZE - 1:
                cur += 2.0 * abs(val - 0.0)
            for nr, nc in get_neighbors(r, c):
                npos = (nr, nc)
                if npos in opp_set:
                    continue
                nidx = nr * BOARD_SIZE + nc
                g = 2.5 if npos in me_set else 1.0
                cur += g * abs(val - V[nidx])
            currents[pos] = 0.5 * cur

    return currents


def solve_currents_white(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    N = BOARD_SIZE * BOARD_SIZE
    A = np.zeros((N, N), dtype=np.float64)
    b = np.zeros(N, dtype=np.float64)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            idx = r * BOARD_SIZE + c
            pos = (r, c)
            if pos in me_set:
                A[idx, idx] = 1.0
                b[idx] = 0.0
                continue

            is_opp = pos in opp_set
            diag = 0.0

            if c == 0:
                g_left = 40.0 if is_opp else 2.0
                diag += g_left
                b[idx] += g_left * 1.0

            if c == BOARD_SIZE - 1:
                g_right = 40.0 if is_opp else 2.0
                diag += g_right

            for nr, nc in get_neighbors(r, c):
                npos = (nr, nc)
                if npos in me_set:
                    continue
                nidx = nr * BOARD_SIZE + nc
                is_nopp = npos in opp_set
                if is_opp and is_nopp:
                    g = 25.0
                elif is_opp or is_nopp:
                    g = 2.5
                else:
                    g = 1.0
                diag += g
                A[idx, nidx] -= g

            A[idx, idx] = diag + 1e-5

    try:
        V = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return {}

    currents = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            pos = (r, c)
            if pos in me_set or pos in opp_set:
                continue
            idx = r * BOARD_SIZE + c
            val = V[idx]
            cur = 0.0
            if c == 0:
                cur += 2.0 * abs(val - 1.0)
            if c == BOARD_SIZE - 1:
                cur += 2.0 * abs(val - 0.0)
            for nr, nc in get_neighbors(r, c):
                npos = (nr, nc)
                if npos in me_set:
                    continue
                nidx = nr * BOARD_SIZE + nc
                g = 2.5 if npos in opp_set else 1.0
                cur += g * abs(val - V[nidx])
            currents[pos] = 0.5 * cur

    return currents


def solve_black(me: list[tuple[int, int]], opp: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    empty_cells = [
        (r, c)
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
        if (r, c) not in occupied
    ]

    if not empty_cells:
        return (0, 0)

    center = (BOARD_SIZE // 2, BOARD_SIZE // 2)
    if len(occupied) <= 1 and center in empty_cells:
        return center

    dist_top, dist_bot = get_dists_black(me_set, opp_set)
    dist_left, dist_right = get_dists_white(opp_set, me_set)

    l_me = {}
    for pos in empty_cells:
        if pos in dist_top and pos in dist_bot:
            l_me[pos] = dist_top[pos] + dist_bot[pos] - 1
        else:
            l_me[pos] = 999

    l_opp = {}
    for pos in empty_cells:
        if pos in dist_left and pos in dist_right:
            l_opp[pos] = dist_left[pos] + dist_right[pos] - 1
        else:
            l_opp[pos] = 999

    # 1. Immediate Win Detection
    for pos in empty_cells:
        if l_me[pos] == 1:
            return pos

    # 2. Immediate Block Detection
    threat_blocks = [pos for pos in empty_cells if l_opp[pos] == 1]

    cur_b = solve_currents_black(me_set, opp_set)
    cur_w = solve_currents_white(me_set, opp_set)

    # 3. Tactical Bridge Analysis
    threatened_bridge_saves = set()
    new_bridge_moves = set()

    for r, c in me_set:
        for (dr, dc), shared in BRIDGE_DELTAS:
            tr, tc = r + dr, c + dc
            if 0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE:
                target = (tr, tc)
                n1 = (r + shared[0][0], c + shared[0][1])
                n2 = (r + shared[1][0], c + shared[1][1])
                if not (0 <= n1[0] < BOARD_SIZE and 0 <= n1[1] < BOARD_SIZE):
                    continue
                if not (0 <= n2[0] < BOARD_SIZE and 0 <= n2[1] < BOARD_SIZE):
                    continue

                if target in me_set:
                    # An established bridge between two of our stones
                    if n1 in opp_set and n2 not in occupied:
                        threatened_bridge_saves.add(n2)
                    elif n2 in opp_set and n1 not in occupied:
                        threatened_bridge_saves.add(n1)
                elif target not in occupied:
                    # Opportunity to form an intact bridge
                    if n1 not in occupied and n2 not in occupied:
                        new_bridge_moves.add(target)

    min_l_me = min(l_me.values()) if l_me else 999
    min_l_opp = min(l_opp.values()) if l_opp else 999

    def evaluate_cell(pos: tuple[int, int]) -> float:
        r, c = pos
        cb = cur_b.get(pos, 0.0)
        cw = cur_w.get(pos, 0.0)

        # Resistor potential score: Shannon/Anshelevich critical points
        score = (cb * cw) + 0.25 * (cb + cw)

        # Distance path rewards
        if l_me[pos] == min_l_me:
            score += 0.35 / (min_l_me + 0.1)
        if l_opp[pos] == min_l_opp:
            score += 0.45 / (min_l_opp + 0.1)

        # Tactical bridge bonuses
        if pos in threatened_bridge_saves:
            score += 0.60
        if pos in new_bridge_moves:
            score += 0.12

        # Gentle center attraction
        center_dist = abs(r - 5) + abs(c - 5)
        score += 0.015 * (10 - center_dist)

        return score

    if threat_blocks:
        return max(threat_blocks, key=evaluate_cell)

    return max(empty_cells, key=evaluate_cell)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    if color == 'w':
        # Transpose coordinates to leverage exact board symmetry
        me_t = [(c, r) for r, c in me]
        opp_t = [(c, r) for r, c in opp]
        best_r, best_c = solve_black(me_t, opp_t)
        return (best_c, best_r)
    else:
        return solve_black(me, opp)
