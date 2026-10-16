
import math

# Cached board representation
_BOARD_CACHE = {}


def get_board_data(valid_mask):
    """
    Initializes and caches graph topology, neighbor adjacencies,
    corners, edges, and distance metrics for the given board.
    """
    mask_bytes = valid_mask.tobytes()
    if mask_bytes in _BOARD_CACHE:
        return _BOARD_CACHE[mask_bytes]

    N = len(valid_mask)
    valid_cells = []
    cell_to_id = {}
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c]:
                idx = len(valid_cells)
                cell_to_id[(r, c)] = idx
                valid_cells.append((r, c))

    V = len(valid_cells)
    neighbors = [[] for _ in range(V)]

    # Hexagonal neighbor offsets in odd-q column coordinate system
    for idx, (r, c) in enumerate(valid_cells):
        if c % 2 == 1:
            candidates = [
                (r - 1, c),
                (r + 1, c),
                (r - 1, c - 1),
                (r, c - 1),
                (r - 1, c + 1),
                (r, c + 1),
            ]
        else:
            candidates = [
                (r - 1, c),
                (r + 1, c),
                (r, c - 1),
                (r + 1, c - 1),
                (r, c + 1),
                (r + 1, c + 1),
            ]
        for nr, nc in candidates:
            if (nr, nc) in cell_to_id:
                neighbors[idx].append(cell_to_id[(nr, nc)])

    degrees = [len(neighbors[i]) for i in range(V)]
    boundary_cells = set(i for i in range(V) if degrees[i] < 6)

    # Corners have degree 3 on a regular hexagonal board
    min_deg = min(degrees[i] for i in boundary_cells) if boundary_cells else 3
    corners = [i for i in boundary_cells if degrees[i] == min_deg]

    if len(corners) != 6:
        # Fallback in case of non-standard boundaries
        sorted_boundary = sorted(boundary_cells, key=lambda i: degrees[i])
        corners = sorted_boundary[:6]

    corner_set = set(corners)
    non_corner_boundary = boundary_cells - corner_set

    # Partition non-corner boundary into 6 distinct edge components
    visited = set()
    edge_components = []
    for cell in non_corner_boundary:
        if cell not in visited:
            comp = []
            q = [cell]
            visited.add(cell)
            for curr in q:
                comp.append(curr)
                for nbr in neighbors[curr]:
                    if nbr in non_corner_boundary and nbr not in visited:
                        visited.add(nbr)
                        q.append(nbr)
            edge_components.append(comp)

    corner_idx = [-1] * V
    for idx, c in enumerate(corners):
        corner_idx[c] = idx

    edge_idx = [-1] * V
    for idx, comp in enumerate(edge_components):
        for c in comp:
            edge_idx[c] = idx

    # Precompute distances from each corner and each edge
    dist_to_corner = []
    for c in corners:
        d = [-1] * V
        d[c] = 0
        q = [c]
        for curr in q:
            for nbr in neighbors[curr]:
                if d[nbr] == -1:
                    d[nbr] = d[curr] + 1
                    q.append(nbr)
        dist_to_corner.append(d)

    dist_to_edge = []
    for comp in edge_components:
        d = [-1] * V
        q = []
        for c in comp:
            d[c] = 0
            q.append(c)
        for curr in q:
            for nbr in neighbors[curr]:
                if d[nbr] == -1:
                    d[nbr] = d[curr] + 1
                    q.append(nbr)
        dist_to_edge.append(d)

    avg_r = sum(r for r, c in valid_cells) / V
    avg_c = sum(c for r, c in valid_cells) / V
    center_cell = min(
        range(V),
        key=lambda i: (valid_cells[i][0] - avg_r) ** 2
        + (valid_cells[i][1] - avg_c) ** 2,
    )

    board_data = {
        "V": V,
        "valid_cells": valid_cells,
        "cell_to_id": cell_to_id,
        "neighbors": neighbors,
        "boundary_list": list(boundary_cells),
        "corner_idx": corner_idx,
        "edge_idx": edge_idx,
        "dist_to_corner": dist_to_corner,
        "dist_to_edge": dist_to_edge,
        "center_cell": center_cell,
    }
    _BOARD_CACHE[mask_bytes] = board_data
    return board_data


class DisjointSet:
    def __init__(self, V, corner_idx, edge_idx):
        self.parent = list(range(V))
        self.size = [1] * V
        self.corners_mask = [
            (1 << corner_idx[i]) if corner_idx[i] >= 0 else 0 for i in range(V)
        ]
        self.edges_mask = [
            (1 << edge_idx[i]) if edge_idx[i] >= 0 else 0 for i in range(V)
        ]

    def find(self, i):
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            self.corners_mask[root_i] |= self.corners_mask[root_j]
            self.edges_mask[root_i] |= self.edges_mask[root_j]
            return True
        return False


def build_dsu(stones_set, board):
    dsu = DisjointSet(board["V"], board["corner_idx"], board["edge_idx"])
    neighbors = board["neighbors"]
    for u in stones_set:
        for v in neighbors[u]:
            if v in stones_set and v < u:
                dsu.union(u, v)
    return dsu


def check_ring(u, stones_set, board):
    """
    Checks if a ring is completed enclosing one or more cells.
    Any cell not reachable from the boundary through non-player cells is enclosed.
    """
    V = board["V"]
    blocked = [False] * V
    for s in stones_set:
        blocked[s] = True
    blocked[u] = True

    visited = [False] * V
    q = []
    for b in board["boundary_list"]:
        if not blocked[b]:
            visited[b] = True
            q.append(b)

    head = 0
    neighbors = board["neighbors"]
    while head < len(q):
        curr = q[head]
        head += 1
        for nbr in neighbors[curr]:
            if not blocked[nbr] and not visited[nbr]:
                visited[nbr] = True
                q.append(nbr)

    total_unblocked = V - len(stones_set) - 1
    return len(q) < total_unblocked


def check_win(u, stones_set, dsu, board):
    """
    Checks whether placing a stone at candidate cell `u` immediately wins.
    """
    c_mask = (
        (1 << board["corner_idx"][u]) if board["corner_idx"][u] >= 0 else 0
    )
    e_mask = (1 << board["edge_idx"][u]) if board["edge_idx"][u] >= 0 else 0

    seen_roots = set()
    has_cycle = False

    for nbr in board["neighbors"][u]:
        if nbr in stones_set:
            r = dsu.find(nbr)
            if r in seen_roots:
                has_cycle = True
            else:
                seen_roots.add(r)
                c_mask |= dsu.corners_mask[r]
                e_mask |= dsu.edges_mask[r]

    # Bridge: connects at least 2 distinct corners
    if (c_mask & (c_mask - 1)) != 0:
        return True

    # Fork: connects at least 3 distinct edges
    if bin(e_mask).count("1") >= 3:
        return True

    # Ring: completed cycle enclosing cells
    if has_cycle and check_ring(u, stones_set, board):
        return True

    return False


def evaluate_candidate(u, stones_set, dsu, board, opp_stones_set):
    """
    Heuristic value for a non-winning candidate move.
    """
    score = 0
    r, c = board["valid_cells"][u]
    cr, cc = board["valid_cells"][board["center_cell"]]
    dist_center = abs(r - cr) + abs(c - cc)
    score += max(0, 10 - dist_center) * 6

    c_mask = (
        (1 << board["corner_idx"][u]) if board["corner_idx"][u] >= 0 else 0
    )
    e_mask = (1 << board["edge_idx"][u]) if board["edge_idx"][u] >= 0 else 0

    neighbor_stones = 0
    merged_roots = set()
    merged_size = 1

    for nbr in board["neighbors"][u]:
        if nbr in stones_set:
            neighbor_stones += 1
            r_nbr = dsu.find(nbr)
            if r_nbr not in merged_roots:
                merged_roots.add(r_nbr)
                c_mask |= dsu.corners_mask[r_nbr]
                e_mask |= dsu.edges_mask[r_nbr]
                merged_size += dsu.size[r_nbr]

    num_corners = bin(c_mask).count("1")
    num_edges = bin(e_mask).count("1")

    # High incentive for edge and corner combinations
    if num_edges == 2:
        score += 400
    elif num_edges == 1:
        score += 120

    if num_corners == 1:
        score += 180

    if len(merged_roots) > 1:
        score += len(merged_roots) * 70 + min(merged_size, 20) * 5
    elif neighbor_stones == 1:
        score += 30
    elif neighbor_stones >= 2:
        score += 75

    # Shortest path progression toward remaining edges
    if 0 < num_edges < 3:
        min_ed = 999
        for e in range(len(board["dist_to_edge"])):
            if not (e_mask & (1 << e)):
                d = board["dist_to_edge"][e][u]
                if d < min_ed:
                    min_ed = d
        score += max(0, 8 - min_ed) * 18

    # Shortest path progression toward remaining corners
    if num_corners == 1:
        min_cd = 999
        for cr_idx in range(len(board["dist_to_corner"])):
            if not (c_mask & (1 << cr_idx)):
                d = board["dist_to_corner"][cr_idx][u]
                if d < min_cd:
                    min_cd = d
        score += max(0, 8 - min_cd) * 18

    # Two-bridge (virtual connection) bonus
    for nbr in board["neighbors"][u]:
        if nbr not in stones_set and nbr not in opp_stones_set:
            for nbr2 in board["neighbors"][nbr]:
                if nbr2 != u and nbr2 in stones_set:
                    score += 14

    return score


def policy(
    me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask
) -> tuple[int, int]:
    board = get_board_data(valid_mask)
    cell_to_id = board["cell_to_id"]
    valid_cells = board["valid_cells"]

    me_set = set(cell_to_id[pt] for pt in me if pt in cell_to_id)
    opp_set = set(cell_to_id[pt] for pt in opp if pt in cell_to_id)
    occupied = me_set | opp_set

    # 1. Opening move: take center if vacant
    center_id = board["center_cell"]
    if center_id not in occupied:
        if len(me_set) == 0:
            return valid_cells[center_id]

    legal_moves = [i for i in range(board["V"]) if i not in occupied]
    if not legal_moves:
        return (0, 0)

    me_dsu = build_dsu(me_set, board)
    opp_dsu = build_dsu(opp_set, board)

    # 2. Check for immediate winning move for 'me'
    for m in legal_moves:
        if check_win(m, me_set, me_dsu, board):
            return valid_cells[m]

    # 3. Check for immediate winning move for 'opp' and block
    opp_wins = [m for m in legal_moves if check_win(m, opp_set, opp_dsu, board)]
    if len(opp_wins) == 1:
        return valid_cells[opp_wins[0]]
    elif len(opp_wins) > 1:
        # Multiple opponent wins: pick the move that blocks most or optimizes counter-play
        best_block = max(
            opp_wins,
            key=lambda m: evaluate_candidate(m, me_set, me_dsu, board, opp_set),
        )
        return valid_cells[best_block]

    # 4. Evaluate all legal moves for tactical & strategic strength
    move_scores = {}
    for m in legal_moves:
        my_val = evaluate_candidate(m, me_set, me_dsu, board, opp_set)
        opp_val = evaluate_candidate(m, opp_set, opp_dsu, board, me_set)
        move_scores[m] = my_val + 0.9 * opp_val

    sorted_candidates = sorted(
        legal_moves, key=lambda m: move_scores[m], reverse=True
    )

    # 5. Double-threat detection (forced win in 2 moves)
    top_candidates = sorted_candidates[:20]
    for m in top_candidates:
        sim_me_set = me_set | {m}
        sim_me_dsu = build_dsu(sim_me_set, board)

        winning_threats = 0
        for cand in legal_moves:
            if cand != m:
                if check_win(cand, sim_me_set, sim_me_dsu, board):
                    winning_threats += 1
                    if winning_threats >= 2:
                        break

        if winning_threats >= 2:
            return valid_cells[m]

    # 6. Block opponent double-threats
    top_opp_candidates = sorted(
        legal_moves,
        key=lambda m: evaluate_candidate(m, opp_set, opp_dsu, board, me_set),
        reverse=True,
    )[:12]

    for opp_m in top_opp_candidates:
        sim_opp_set = opp_set | {opp_m}
        sim_opp_dsu = build_dsu(sim_opp_set, board)

        opp_threats = 0
        for cand in legal_moves:
            if cand != opp_m:
                if check_win(cand, sim_opp_set, sim_opp_dsu, board):
                    opp_threats += 1
                    if opp_threats >= 2:
                        break

        if opp_threats >= 2:
            move_scores[opp_m] += 800

    best_move = max(legal_moves, key=lambda m: move_scores[m])
    return valid_cells[best_move]
