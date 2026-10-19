
import heapq
import numpy as np

BOARD_SIZE = 11

NEIGHBOR_OFFSETS = [
    (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0)
]

def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    """Returns valid hexagonal board neighbors for (r, c)."""
    nbrs = []
    for dr, dc in NEIGHBOR_OFFSETS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            nbrs.append((nr, nc))
    return nbrs

def dijkstra_distances(color: str, my_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    """
    Computes shortest path distances from source and sink for the given color.
    Returns (dist_src, dist_snk).
    """
    def run_dijkstra(starts):
        dist = {}
        pq = []
        for pos in starts:
            if pos not in opp_set:
                cost = 0 if pos in my_set else 1
                dist[pos] = cost
                heapq.heappush(pq, (cost, pos))
        while pq:
            d, (r, c) = heapq.heappop(pq)
            if d > dist.get((r, c), 9999):
                continue
            for nr, nc in get_neighbors(r, c):
                npos = (nr, nc)
                if npos in opp_set:
                    continue
                step = 0 if npos in my_set else 1
                nd = d + step
                if nd < dist.get(npos, 9999):
                    dist[npos] = nd
                    heapq.heappush(pq, (nd, npos))
        return dist

    if color == 'b':
        src_cells = [(0, c) for c in range(BOARD_SIZE)]
        snk_cells = [(BOARD_SIZE - 1, c) for c in range(BOARD_SIZE)]
    else:
        src_cells = [(r, 0) for r in range(BOARD_SIZE)]
        snk_cells = [(r, BOARD_SIZE - 1) for r in range(BOARD_SIZE)]

    return run_dijkstra(src_cells), run_dijkstra(snk_cells)

def solve_circuit(color: str, my_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    """
    Solves the resistor network Laplacian for the board.
    Returns (V, G_eff, sensitivities).
    """
    n_nodes = BOARD_SIZE * BOARD_SIZE
    A = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    b = np.zeros(n_nodes, dtype=np.float64)
    g_src = np.zeros(n_nodes, dtype=np.float64)
    g_snk = np.zeros(n_nodes, dtype=np.float64)

    # Boundary conductances
    if color == 'b':
        for c in range(BOARD_SIZE):
            idx_src = 0 * BOARD_SIZE + c
            if (0, c) in my_set:
                g_src[idx_src] = 25.0
            elif (0, c) not in opp_set:
                g_src[idx_src] = 3.0

            idx_snk = (BOARD_SIZE - 1) * BOARD_SIZE + c
            if (BOARD_SIZE - 1, c) in my_set:
                g_snk[idx_snk] = 25.0
            elif (BOARD_SIZE - 1, c) not in opp_set:
                g_snk[idx_snk] = 3.0
    else:
        for r in range(BOARD_SIZE):
            idx_src = r * BOARD_SIZE + 0
            if (r, 0) in my_set:
                g_src[idx_src] = 25.0
            elif (r, 0) not in opp_set:
                g_src[idx_src] = 3.0

            idx_snk = r * BOARD_SIZE + (BOARD_SIZE - 1)
            if (r, BOARD_SIZE - 1) in my_set:
                g_snk[idx_snk] = 25.0
            elif (r, BOARD_SIZE - 1) not in opp_set:
                g_snk[idx_snk] = 3.0

    # Build matrix
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            u = (r, c)
            ku = r * BOARD_SIZE + c
            if u in opp_set:
                A[ku, ku] = 1.0
                continue

            diag = g_src[ku] + g_snk[ku]
            b[ku] = g_src[ku]

            for nr, nc in get_neighbors(r, c):
                v = (nr, nc)
                if v in opp_set:
                    continue
                kv = nr * BOARD_SIZE + nc
                if u in my_set and v in my_set:
                    g = 25.0
                elif u in my_set or v in my_set:
                    g = 4.0
                else:
                    g = 1.0
                diag += g
                A[ku, kv] -= g

            A[ku, ku] = diag + 1e-5

    try:
        V = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        V = np.zeros(n_nodes)

    G_eff = float(np.sum(g_src * (1.0 - V)))

    # Compute first-order sensitivity for empty cells
    sens = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            u = (r, c)
            if u in my_set or u in opp_set:
                continue
            ku = r * BOARD_SIZE + c
            vu = V[ku]
            s = 0.0
            if g_src[ku] > 0:
                s += 22.0 * ((1.0 - vu) ** 2)
            if g_snk[ku] > 0:
                s += 22.0 * (vu ** 2)

            for nr, nc in get_neighbors(r, c):
                v = (nr, nc)
                if v in opp_set:
                    continue
                kv = nr * BOARD_SIZE + nc
                dg = 21.0 if v in my_set else 3.0
                s += dg * ((vu - V[kv]) ** 2)
            sens[u] = s

    return V, G_eff, sens

def solve_circuit_geff_only(color: str, my_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]) -> float:
    """Fast circuit solver returning only effective conductance."""
    n_nodes = BOARD_SIZE * BOARD_SIZE
    A = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    b = np.zeros(n_nodes, dtype=np.float64)
    g_src = np.zeros(n_nodes, dtype=np.float64)
    g_snk = np.zeros(n_nodes, dtype=np.float64)

    if color == 'b':
        for c in range(BOARD_SIZE):
            idx_src = c
            g_src[idx_src] = 25.0 if (0, c) in my_set else (0.0 if (0, c) in opp_set else 3.0)
            idx_snk = (BOARD_SIZE - 1) * BOARD_SIZE + c
            g_snk[idx_snk] = 25.0 if (BOARD_SIZE - 1, c) in my_set else (0.0 if (BOARD_SIZE - 1, c) in opp_set else 3.0)
    else:
        for r in range(BOARD_SIZE):
            idx_src = r * BOARD_SIZE
            g_src[idx_src] = 25.0 if (r, 0) in my_set else (0.0 if (r, 0) in opp_set else 3.0)
            idx_snk = r * BOARD_SIZE + (BOARD_SIZE - 1)
            g_snk[idx_snk] = 25.0 if (r, BOARD_SIZE - 1) in my_set else (0.0 if (r, BOARD_SIZE - 1) in opp_set else 3.0)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            u = (r, c)
            ku = r * BOARD_SIZE + c
            if u in opp_set:
                A[ku, ku] = 1.0
                continue
            diag = g_src[ku] + g_snk[ku]
            b[ku] = g_src[ku]
            for nr, nc in get_neighbors(r, c):
                v = (nr, nc)
                if v in opp_set:
                    continue
                kv = nr * BOARD_SIZE + nc
                g = 25.0 if (u in my_set and v in my_set) else (4.0 if (u in my_set or v in my_set) else 1.0)
                diag += g
                A[ku, kv] -= g
            A[ku, ku] = diag + 1e-5

    try:
        V = np.linalg.solve(A, b)
        return float(np.sum(g_src * (1.0 - V)))
    except np.linalg.LinAlgError:
        return 0.0

def count_immediate_wins(color: str, my_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]) -> int:
    """Counts how many 1-move wins exist for player."""
    d_src, d_snk = dijkstra_distances(color, my_set, opp_set)
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            u = (r, c)
            if u not in my_set and u not in opp_set:
                if d_src.get(u, 9999) + d_snk.get(u, 9999) - 1 == 1:
                    count += 1
    return count

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'

    empty_cells = [
        (r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
        if (r, c) not in my_set and (r, c) not in opp_set
    ]

    if not empty_cells:
        return (0, 0)

    # 1. Opening Move: Center cell is game-theoretically strongest
    center = (BOARD_SIZE // 2, BOARD_SIZE // 2)
    if not me and not opp and center in empty_cells:
        return center

    # 2. Dual Dijkstra Check for Immediate 1-Move Wins and Blocks
    my_d_src, my_d_snk = dijkstra_distances(color, my_set, opp_set)
    opp_d_src, opp_d_snk = dijkstra_distances(opp_color, opp_set, my_set)

    my_winning_moves = [
        u for u in empty_cells
        if my_d_src.get(u, 9999) + my_d_snk.get(u, 9999) - 1 == 1
    ]
    if my_winning_moves:
        return my_winning_moves[0]

    opp_winning_moves = [
        u for u in empty_cells
        if opp_d_src.get(u, 9999) + opp_d_snk.get(u, 9999) - 1 == 1
    ]
    if len(opp_winning_moves) == 1:
        return opp_winning_moves[0]
    elif len(opp_winning_moves) > 1:
        candidate_pool = opp_winning_moves
    else:
        candidate_pool = empty_cells

    # 3. Base Circuit Sensitivity Solves (Offense & Defense)
    _, _, sens_me = solve_circuit(color, my_set, opp_set)
    _, _, sens_opp = solve_circuit(opp_color, opp_set, my_set)

    # 4. Rank Candidates by Combined Heuristic Score
    ranked_candidates = []
    for u in candidate_pool:
        d_m = max(1, my_d_src.get(u, 99) + my_d_snk.get(u, 99) - 1)
        d_o = max(1, opp_d_src.get(u, 99) + opp_d_snk.get(u, 99) - 1)

        bonus_m = 1.0 / (d_m ** 1.35)
        bonus_o = 1.0 / (d_o ** 1.35)

        s_m = sens_me.get(u, 0.0)
        s_o = sens_opp.get(u, 0.0)

        # Center proximity prior
        r, c = u
        dist_center = abs(r - 5) + abs(c - 5)
        center_bias = 0.05 * (10 - dist_center)

        score_init = (s_m + 0.01) * bonus_m + 1.15 * (s_o + 0.01) * bonus_o + center_bias
        ranked_candidates.append((score_init, u))

    ranked_candidates.sort(reverse=True)
    top_candidates = [u for _, u in ranked_candidates[:28]]

    # 5. Exact 1-Ply Simulation on Top Candidates
    best_move = top_candidates[0]
    best_eval = -1e9

    for u in top_candidates:
        sim_my = my_set | {u}
        g_me = solve_circuit_geff_only(color, sim_my, opp_set)
        g_opp = solve_circuit_geff_only(opp_color, opp_set, sim_my)

        # Detect double-threat forks (forced win next turn)
        threats_created = count_immediate_wins(color, sim_my, opp_set)

        eval_score = (
            np.log(g_me + 1e-4)
            - 1.15 * np.log(g_opp + 1e-4)
            + 8.0 * threats_created
        )

        if eval_score > best_eval:
            best_eval = eval_score
            best_move = u

    return best_move
