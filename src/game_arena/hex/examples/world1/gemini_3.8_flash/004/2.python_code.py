
import time
from collections import deque
import numpy as np

# Board dimension
N = 11

# Precompute neighbor offsets for standard Hex grid
HEX_OFFSETS = [
    (0, -1), (0, 1),
    (-1, 0), (-1, 1),
    (1, -1), (1, 0)
]

# Precompute 2-bridge offsets and their two common neighbors
# (dr, dc, (r_nb1, c_nb1), (r_nb2, c_nb2))
BRIDGE_OFFSETS = [
    (-1, 2, (-1, 1), (0, 1)),
    (1, 1, (0, 1), (1, 0)),
    (2, -1, (1, -1), (1, 0)),
    (1, -2, (0, -1), (1, -1)),
    (-1, -1, (-1, 0), (0, -1)),
    (-2, 1, (-1, 0), (-1, 1)),
]

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N

def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    return [(r + dr, c + dc) for dr, dc in HEX_OFFSETS if in_bounds(r + dr, c + dc)]

def get_bridges(r: int, c: int) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]]:
    res = []
    for dr, dc, nb1, nb2 in BRIDGE_OFFSETS:
        tr, tc = r + dr, c + dc
        if in_bounds(tr, tc):
            n1 = (r + nb1[0], c + nb1[1])
            n2 = (r + nb2[0], c + nb2[1])
            if in_bounds(n1[0], n1[1]) and in_bounds(n2[0], n2[1]):
                res.append(((tr, tc), n1, n2))
    return res

def bfs_distances(stones_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str):
    """
    Computes shortest path distances (in terms of empty stones needed)
    from Side 1 and Side 2 for the specified color.
    """
    dist1 = np.full((N, N), 999, dtype=np.int32)
    dist2 = np.full((N, N), 999, dtype=np.int32)

    # Side 1 boundary
    q1 = deque()
    if color == 'b':
        side1_cells = [(0, c) for c in range(N)]
        side2_cells = [(N - 1, c) for c in range(N)]
    else:
        side1_cells = [(r, 0) for r in range(N)]
        side2_cells = [(r, N - 1) for r in range(N)]

    for cell in side1_cells:
        if cell in opp_set:
            continue
        if cell in stones_set:
            dist1[cell] = 0
            q1.appendleft(cell)
        else:
            dist1[cell] = 1
            q1.append(cell)

    while q1:
        u = q1.popleft()
        d = dist1[u]
        # Standard neighbors
        for v in get_neighbors(u[0], u[1]):
            if v in opp_set:
                continue
            w = 0 if v in stones_set else 1
            if d + w < dist1[v]:
                dist1[v] = d + w
                if w == 0:
                    q1.appendleft(v)
                else:
                    q1.append(v)
        # 2-bridge shortcuts for existing stones
        if u in stones_set:
            for v, nb1, nb2 in get_bridges(u[0], u[1]):
                if v in stones_set and nb1 not in stones_set and nb1 not in opp_set and nb2 not in stones_set and nb2 not in opp_set:
                    if d < dist1[v]:
                        dist1[v] = d
                        q1.appendleft(v)

    # Side 2 boundary
    q2 = deque()
    for cell in side2_cells:
        if cell in opp_set:
            continue
        if cell in stones_set:
            dist2[cell] = 0
            q2.appendleft(cell)
        else:
            dist2[cell] = 1
            q2.append(cell)

    while q2:
        u = q2.popleft()
        d = dist2[u]
        for v in get_neighbors(u[0], u[1]):
            if v in opp_set:
                continue
            w = 0 if v in stones_set else 1
            if d + w < dist2[v]:
                dist2[v] = d + w
                if w == 0:
                    q2.appendleft(v)
                else:
                    q2.append(v)
        if u in stones_set:
            for v, nb1, nb2 in get_bridges(u[0], u[1]):
                if v in stones_set and nb1 not in stones_set and nb1 not in opp_set and nb2 not in stones_set and nb2 not in opp_set:
                    if d < dist2[v]:
                        dist2[v] = d
                        q2.appendleft(v)

    return dist1, dist2

def solve_electrical_currents(stones_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str, empty_cells: list[tuple[int, int]]):
    """
    Computes electric current flowing through each empty cell using a resistor network.
    """
    K = N * N
    A = np.zeros((K, K), dtype=np.float64)
    b = np.zeros(K, dtype=np.float64)

    is_black = (color == 'b')

    for r in range(N):
        for c in range(N):
            idx = r * N + c
            cell = (r, c)
            if cell in opp_set:
                A[idx, idx] = 1.0
                b[idx] = 0.0
                continue

            on_s1 = (r == 0) if is_black else (c == 0)
            on_s2 = (r == N - 1) if is_black else (c == N - 1)

            g_s1 = 0.0
            if on_s1:
                g_s1 = 40.0 if cell in stones_set else 2.0
            g_s2 = 0.0
            if on_s2:
                g_s2 = 40.0 if cell in stones_set else 2.0

            diag = g_s1 + g_s2 + 1e-4

            for nr, nc in get_neighbors(r, c):
                n_cell = (nr, nc)
                if n_cell in opp_set:
                    continue
                n_idx = nr * N + nc

                if cell in stones_set and n_cell in stones_set:
                    g = 40.0
                elif cell in stones_set or n_cell in stones_set:
                    g = 3.0
                else:
                    g = 1.0

                diag += g
                A[idx, n_idx] -= g

            if cell in stones_set:
                for target, nb1, nb2 in get_bridges(r, c):
                    if target in stones_set:
                        if nb1 not in stones_set and nb1 not in opp_set and nb2 not in stones_set and nb2 not in opp_set:
                            t_idx = target[0] * N + target[1]
                            diag += 15.0
                            A[idx, t_idx] -= 15.0

            A[idx, idx] = diag
            b[idx] = g_s1 * 1.0

    try:
        V = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return {cell: 0.0 for cell in empty_cells}

    currents = {}
    for cell in empty_cells:
        r, c = cell
        idx = r * N + c
        Vi = V[idx]
        cur = 0.0

        on_s1 = (r == 0) if is_black else (c == 0)
        on_s2 = (r == N - 1) if is_black else (c == N - 1)

        if on_s1:
            cur += 2.0 * abs(1.0 - Vi)
        if on_s2:
            cur += 2.0 * abs(Vi - 0.0)

        for nr, nc in get_neighbors(r, c):
            n_cell = (nr, nc)
            if n_cell not in opp_set:
                n_idx = nr * N + nc
                g = 3.0 if n_cell in stones_set else 1.0
                cur += g * abs(Vi - V[n_idx])

        currents[cell] = cur * 0.5

    return currents

def evaluate_position(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str, opp_color: str) -> float:
    """
    Static evaluation based on BFS distance differential.
    """
    d1_me, d2_me = bfs_distances(me_set, opp_set, color)
    d1_opp, d2_opp = bfs_distances(opp_set, me_set, opp_color)

    min_me = min(d1_me[r, c] for r, c in ([(N - 1, c) for c in range(N)] if color == 'b' else [(r, N - 1) for r in range(N)]))
    min_opp = min(d1_opp[r, c] for r, c in ([(N - 1, c) for c in range(N)] if opp_color == 'b' else [(r, N - 1) for r in range(N)]))

    return float(min_opp - min_me) * 20.0

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    start_time = time.time()

    me_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'

    empty = [(r, c) for r in range(N) for c in range(N) if (r, c) not in me_set and (r, c) not in opp_set]

    # Edge cases
    if not empty:
        return (5, 5)
    if len(empty) == 1:
        return empty[0]

    # Opening center preference for early moves
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)

    # 1. Compute BFS distances
    d1_me, d2_me = bfs_distances(me_set, opp_set, color)
    d1_opp, d2_opp = bfs_distances(opp_set, me_set, opp_color)

    # Path lengths through each empty cell
    path_len_me = {cell: int(d1_me[cell] + d2_me[cell] - 1) for cell in empty}
    path_len_opp = {cell: int(d1_opp[cell] + d2_opp[cell] - 1) for cell in empty}

    # 2. Check immediate win
    my_instant_wins = [c for c in empty if path_len_me[c] == 1]
    if my_instant_wins:
        return my_instant_wins[0]

    # 3. Check immediate block
    opp_instant_wins = [c for c in empty if path_len_opp[c] == 1]
    if len(opp_instant_wins) == 1:
        return opp_instant_wins[0]

    # 4. Resistor network currents
    i_me = solve_electrical_currents(me_set, opp_set, color, empty)
    i_opp = solve_electrical_currents(opp_set, me_set, opp_color, empty)

    # Candidate scoring function
    def score_cell(cell: tuple[int, int]) -> float:
        r, c = cell
        center_bonus = 1.0 - 0.06 * (abs(r - 5) + abs(c - 5))
        l_me = path_len_me[cell]
        l_opp = path_len_opp[cell]

        score = (
            - 4.0 * l_me
            - 4.5 * l_opp
            + 14.0 * i_me.get(cell, 0.0)
            + 16.0 * i_opp.get(cell, 0.0)
            + center_bonus
        )
        return score

    # If opponent has multiple immediate winning moves, we must block one of them!
    pool = opp_instant_wins if opp_instant_wins else empty
    ranked_candidates = sorted(pool, key=score_cell, reverse=True)

    # If already forced to block from opp_instant_wins, choose the top-ranked one
    if opp_instant_wins:
        return ranked_candidates[0]

    # 5. Lookahead search on top candidates
    top_candidates = ranked_candidates[:8]
    best_move = top_candidates[0]
    best_val = -float('inf')

    for m1 in top_candidates:
        if time.time() - start_time > 0.85:
            break

        temp_me = me_set | {m1}

        # Check if m1 creates double or unstoppable winning threats
        d1_temp, d2_temp = bfs_distances(temp_me, opp_set, color)
        threats = [e for e in empty if e != m1 and d1_temp[e] + d2_temp[e] - 1 == 1]
        if len(threats) >= 2:
            return m1  # Unstoppable win!

        # Opponent's counter-moves
        if len(threats) == 1:
            opp_responses = [threats[0]]  # Opponent must block
        else:
            # Top 4 opponent responses
            opp_responses = sorted([e for e in empty if e != m1], key=lambda e: (path_len_opp[e], -i_opp.get(e, 0.0)))[:4]

        worst_counter_val = float('inf')
        for m2 in opp_responses:
            temp_opp = opp_set | {m2}
            val = evaluate_position(temp_me, temp_opp, color, opp_color)
            if val < worst_counter_val:
                worst_counter_val = val

        if worst_counter_val > best_val:
            best_val = worst_counter_val
            best_move = m1

    return best_move
