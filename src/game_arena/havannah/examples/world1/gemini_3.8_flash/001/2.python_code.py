
import math
from collections import deque

# Global board structure cache
_BOARD_CACHE = {}


def _get_neighbors(r: int, c: int):
    """Return the 6 hexagonal neighbors in odd-q coordinate system."""
    if c % 2 == 1:
        return [
            (r - 1, c), (r + 1, c),
            (r, c - 1), (r - 1, c - 1),
            (r, c + 1), (r - 1, c + 1)
        ]
    else:
        return [
            (r - 1, c), (r + 1, c),
            (r, c - 1), (r + 1, c - 1),
            (r, c + 1), (r + 1, c + 1)
        ]


def _to_cube(r: int, c: int):
    """Convert (r, c) to hex cube coordinates (q, r_hex, s)."""
    q = c
    shift = (c + (c & 1)) // 2
    r_hex = r - shift
    s = -q - r_hex
    return q, r_hex, s


def _hex_dist(p1, p2):
    """Hexagonal Manhattan distance between two cells."""
    q1, r1, s1 = _to_cube(p1[0], p1[1])
    q2, r2, s2 = _to_cube(p2[0], p2[1])
    return (abs(q1 - q2) + abs(r1 - r2) + abs(s1 - s2)) // 2


def _init_board(valid_mask):
    """Precompute and cache board geometry, adjacency, corners, and edges."""
    H = len(valid_mask)
    W = len(valid_mask[0])

    valid_cells = set()
    for r in range(H):
        for c in range(W):
            if valid_mask[r][c]:
                valid_cells.add((r, c))

    adj = {}
    for u in valid_cells:
        adj[u] = [v for v in _get_neighbors(u[0], u[1]) if v in valid_cells]

    boundary_cells = {u for u in valid_cells if len(adj[u]) < 6}
    corners = [u for u in valid_cells if len(adj[u]) == 3]

    all_r = [u[0] for u in valid_cells]
    all_c = [u[1] for u in valid_cells]
    center_r = (min(all_r) + max(all_r)) / 2.0
    center_c = (min(all_c) + max(all_c)) / 2.0
    center_cell = min(valid_cells, key=lambda p: (p[0] - center_r) ** 2 + (p[1] - center_c) ** 2)

    if len(corners) != 6:
        # Fallback to extreme cube coordinate points
        c_set = set()
        c_set.add(max(valid_cells, key=lambda p: _to_cube(*p)[0]))
        c_set.add(min(valid_cells, key=lambda p: _to_cube(*p)[0]))
        c_set.add(max(valid_cells, key=lambda p: _to_cube(*p)[1]))
        c_set.add(min(valid_cells, key=lambda p: _to_cube(*p)[1]))
        c_set.add(max(valid_cells, key=lambda p: _to_cube(*p)[2]))
        c_set.add(min(valid_cells, key=lambda p: _to_cube(*p)[2]))
        corners = list(c_set)

    # Sort corners cyclically around the center
    corners = sorted(corners, key=lambda p: math.atan2(p[0] - center_r, p[1] - center_c))

    cell_to_corner = {c_cell: idx for idx, c_cell in enumerate(corners)}
    cell_to_edge = {}

    # Trace perimeter to find edges between consecutive corners
    for i in range(6):
        c1 = corners[i]
        c2 = corners[(i + 1) % 6]

        # BFS on boundary to find direct edge between c1 and c2
        q = deque([[c1]])
        visited = {c1}
        found_path = None
        while q:
            path = q.popleft()
            curr = path[-1]
            if curr == c2 and len(path) > 2:
                found_path = path
                break
            for nb in adj[curr]:
                if nb in boundary_cells and nb not in visited:
                    # Do not pass through other corners
                    if nb in cell_to_corner and nb != c2:
                        continue
                    visited.add(nb)
                    q.append(path + [nb])

        if found_path:
            # Edge cells are strictly between c1 and c2
            for edge_node in found_path[1:-1]:
                cell_to_edge[edge_node] = i

    return {
        'valid_cells': valid_cells,
        'adj': adj,
        'boundary_cells': boundary_cells,
        'corners': corners,
        'cell_to_corner': cell_to_corner,
        'cell_to_edge': cell_to_edge,
        'center_cell': center_cell
    }


def _check_ring(stones_set, board_info):
    """Check if stones_set forms a closed loop enclosing at least one cell."""
    valid_cells = board_info['valid_cells']
    total_non_p = len(valid_cells) - len(stones_set)
    if total_non_p <= 0:
        return False

    boundary_cells = board_info['boundary_cells']
    adj = board_info['adj']

    exterior = set()
    queue = deque()
    for b in boundary_cells:
        if b not in stones_set:
            exterior.add(b)
            queue.append(b)

    while queue:
        curr = queue.popleft()
        for nb in adj[curr]:
            if nb not in stones_set and nb not in exterior:
                exterior.add(nb)
                queue.append(nb)

    return len(exterior) < total_non_p


def _find_components(stones_set, board_info):
    """Find connected components and their attached corners/edges."""
    adj = board_info['adj']
    cell_to_corner = board_info['cell_to_corner']
    cell_to_edge = board_info['cell_to_edge']

    comp_map = {}
    comp_corners = {}
    comp_edges = {}
    visited = set()
    cid = 0

    for s in stones_set:
        if s not in visited:
            corners = set()
            edges = set()
            q = [s]
            visited.add(s)
            comp_map[s] = cid
            while q:
                curr = q.pop()
                if curr in cell_to_corner:
                    corners.add(cell_to_corner[curr])
                if curr in cell_to_edge:
                    edges.add(cell_to_edge[curr])
                for nb in adj[curr]:
                    if nb in stones_set and nb not in visited:
                        visited.add(nb)
                        comp_map[nb] = cid
                        q.append(nb)

            comp_corners[cid] = corners
            comp_edges[cid] = edges
            cid += 1

    return comp_map, comp_corners, comp_edges


def _move_wins(m, stones_set, comp_map, comp_corners, comp_edges, board_info):
    """Fast check whether adding move m achieves victory."""
    adj = board_info['adj']
    cell_to_corner = board_info['cell_to_corner']
    cell_to_edge = board_info['cell_to_edge']

    nb_comps = set()
    for nb in adj[m]:
        if nb in stones_set:
            nb_comps.add(comp_map[nb])

    merged_corners = set()
    merged_edges = set()

    if m in cell_to_corner:
        merged_corners.add(cell_to_corner[m])
    if m in cell_to_edge:
        merged_edges.add(cell_to_edge[m])

    for cid in nb_comps:
        merged_corners |= comp_corners[cid]
        merged_edges |= comp_edges[cid]

    # Bridge win: 2+ distinct corners
    if len(merged_corners) >= 2:
        return True

    # Fork win: 3+ distinct edges
    if len(merged_edges) >= 3:
        return True

    # Ring win: requires at least 2 adjacent stones and total >= 6
    if len(stones_set) + 1 >= 6:
        nb_count = sum(1 for nb in adj[m] if nb in stones_set)
        if nb_count >= 2:
            if _check_ring(stones_set | {m}, board_info):
                return True

    return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Cache initialization
    mask_key = (len(valid_mask), len(valid_mask[0]))
    if mask_key not in _BOARD_CACHE:
        _BOARD_CACHE[mask_key] = _init_board(valid_mask)
    board_info = _BOARD_CACHE[mask_key]

    me_set = set(me)
    opp_set = set(opp)
    valid_cells = board_info['valid_cells']
    adj = board_info['adj']
    center_cell = board_info['center_cell']
    cell_to_corner = board_info['cell_to_corner']
    cell_to_edge = board_info['cell_to_edge']

    legal_moves = [cell for cell in valid_cells if cell not in me_set and cell not in opp_set]
    if not legal_moves:
        return (0, 0)

    # Opening turn
    if len(me) == 0 and len(opp) == 0:
        if center_cell in legal_moves:
            return center_cell

    me_map, me_corners, me_edges = _find_components(me_set, board_info)
    opp_map, opp_corners, opp_edges = _find_components(opp_set, board_info)

    # 1. Immediate winning move check
    for m in legal_moves:
        if _move_wins(m, me_set, me_map, me_corners, me_edges, board_info):
            return m

    # 2. Immediate opponent win blocking check
    opp_wins = []
    for m in legal_moves:
        if _move_wins(m, opp_set, opp_map, opp_corners, opp_edges, board_info):
            opp_wins.append(m)

    if len(opp_wins) == 1:
        return opp_wins[0]
    elif len(opp_wins) > 1:
        # Multiple threats: choose the one with the highest strategic value
        return max(opp_wins, key=lambda m: -_hex_dist(m, center_cell))

    # 3. Two-step win search (unblockable double-threats)
    # Score candidate moves heuristically first to test top candidates
    def quick_score(m):
        score = 0.0
        # Distance to center
        dist_c = _hex_dist(m, center_cell)
        score -= dist_c * 15.0

        # Adjacency to me and opp
        my_adj = 0
        opp_adj = 0
        empty_adj = 0
        for nb in adj[m]:
            if nb in me_set:
                my_adj += 1
            elif nb in opp_set:
                opp_adj += 1
            else:
                empty_adj += 1

        score += my_adj * 40.0
        score += opp_adj * 25.0
        score += empty_adj * 10.0

        # Corner / Edge values
        if m in cell_to_corner:
            score += 250.0
        elif m in cell_to_edge:
            score += 150.0

        # Component connection progress for me
        nb_me_comps = {me_map[nb] for nb in adj[m] if nb in me_set}
        if len(nb_me_comps) >= 2:
            score += 300.0 * len(nb_me_comps)

        mc = set()
        me_edges_count = set()
        if m in cell_to_corner:
            mc.add(cell_to_corner[m])
        if m in cell_to_edge:
            me_edges_count.add(cell_to_edge[m])
        for cid in nb_me_comps:
            mc |= me_corners[cid]
            me_edges_count |= me_edges[cid]

        if len(me_edges_count) >= 2:
            score += 800.0
        elif len(me_edges_count) == 1:
            score += 200.0
        if len(mc) == 1:
            score += 300.0

        # Component connection denial for opponent
        nb_opp_comps = {opp_map[nb] for nb in adj[m] if nb in opp_set}
        if len(nb_opp_comps) >= 2:
            score += 250.0 * len(nb_opp_comps)

        oc = set()
        oe = set()
        if m in cell_to_corner:
            oc.add(cell_to_corner[m])
        if m in cell_to_edge:
            oe.add(cell_to_edge[m])
        for cid in nb_opp_comps:
            oc |= opp_corners[cid]
            oe |= opp_edges[cid]

        if len(oe) >= 2:
            score += 650.0
        if len(oc) == 1:
            score += 200.0

        return score

    scored_moves = [(quick_score(m), m) for m in legal_moves]
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    # Check top 20 candidate moves for double winning threats
    top_candidates = [m for _, m in scored_moves[:20]]
    for m in top_candidates:
        temp_me = me_set | {m}
        t_map, t_corners, t_edges = _find_components(temp_me, board_info)
        winning_replies = 0

        # Only evaluate replies adjacent to temp_me, corners, or edges
        relevant_replies = set()
        for s in temp_me:
            for nb in adj[s]:
                if nb in legal_moves and nb != m:
                    relevant_replies.add(nb)
        for c in board_info['corners']:
            if c in legal_moves and c != m:
                relevant_replies.add(c)

        for r_move in relevant_replies:
            if _move_wins(r_move, temp_me, t_map, t_corners, t_edges, board_info):
                winning_replies += 1
                if winning_replies >= 2:
                    return m  # Unblockable double threat found!

    # Return top ranked move
    return scored_moves[0][1]
