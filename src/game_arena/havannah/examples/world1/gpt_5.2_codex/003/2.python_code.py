
import math
from collections import deque

# Cache for board analysis so we don't recompute each call if mask repeats
_ANALYSIS_CACHE = {}

# Hex neighbor offsets for the coordinate system described
_NEIGHBOR_OFFSETS = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]


def _mask_key(valid_mask):
    """Create a hashable key for caching."""
    if hasattr(valid_mask, "tobytes"):
        return (valid_mask.shape, valid_mask.tobytes())
    else:
        return tuple(tuple(row) for row in valid_mask)


def _analyze_board(valid_mask):
    key = _mask_key(valid_mask)
    if key in _ANALYSIS_CACHE:
        return _ANALYSIS_CACHE[key]

    N = len(valid_mask)
    valid = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    valid_set = set(valid)

    def neighbors(cell):
        r, c = cell
        for dr, dc in _NEIGHBOR_OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                yield (nr, nc)

    neighs = {cell: list(neighbors(cell)) for cell in valid}
    degree = {cell: len(neighs[cell]) for cell in valid}

    corners = [cell for cell in valid if degree[cell] == 3]
    boundary = {cell for cell in valid if degree[cell] < 6}

    # Boundary neighbors
    bneigh = {cell: [n for n in neighs[cell] if n in boundary] for cell in boundary}

    # Traverse boundary cycle to assign edges between corners
    start = corners[0]
    order = []
    curr = start
    prev = None
    guard = 0
    while True:
        order.append(curr)
        neigh = bneigh[curr]
        if prev is None:
            nxt = neigh[0]
        else:
            if len(neigh) == 1:
                nxt = neigh[0]
            else:
                nxt = neigh[0] if neigh[1] == prev else neigh[1]
        prev, curr = curr, nxt
        if curr == start:
            break
        guard += 1
        if guard > len(boundary) + 5:
            break  # safety

    edge_id = {}
    current_edge = 0
    for cell in order:
        if cell in corners:
            if cell != start:
                current_edge = (current_edge + 1) % 6
        else:
            edge_id[cell] = current_edge

    # Compute center of mass of valid cells
    rs = [r for r, c in valid]
    cs = [c for r, c in valid]
    center = (sum(rs) / len(rs), sum(cs) / len(cs))

    data = (neighs, set(corners), edge_id, center, valid_set)
    _ANALYSIS_CACHE[key] = data
    return data


def _component_win(start_cell, player_set, neighs, corners_set, edge_id):
    """Check if the component containing start_cell forms a bridge or fork."""
    stack = [start_cell]
    visited = {start_cell}
    comp_corners = set()
    comp_edges = set()
    while stack:
        cur = stack.pop()
        if cur in corners_set:
            comp_corners.add(cur)
        if cur in edge_id:
            comp_edges.add(edge_id[cur])
        for nb in neighs[cur]:
            if nb not in visited and (nb in player_set or nb == start_cell):
                visited.add(nb)
                stack.append(nb)
    if len(comp_corners) >= 2:
        return True
    if len(comp_edges) >= 3:
        return True
    return False


def policy(me, opp, valid_mask):
    neighs, corners_set, edge_id, center, valid_set = _analyze_board(valid_mask)

    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empties = [cell for cell in valid_set if cell not in occupied]

    # If no moves available (should not happen), return any valid cell
    if not empties:
        return next(iter(valid_set))

    # 1) Winning move for me
    for cell in empties:
        if _component_win(cell, me_set, neighs, corners_set, edge_id):
            return cell

    # 2) Block opponent winning move
    for cell in empties:
        if _component_win(cell, opp_set, neighs, corners_set, edge_id):
            return cell

    # 3) Heuristic move
    best_score = -1e9
    best_cell = None
    cr, cc = center

    for cell in empties:
        r, c = cell
        adj_me = 0
        adj_opp = 0
        for nb in neighs[cell]:
            if nb in me_set:
                adj_me += 1
            elif nb in opp_set:
                adj_opp += 1

        score = 0.0
        score += 3.0 * adj_me
        score -= 2.0 * adj_opp
        if cell in corners_set:
            score += 1.0
        if cell in edge_id:
            score += 0.5

        # Prefer center-ish
        dist = abs(r - cr) + abs(c - cc)
        score -= 0.1 * dist

        if score > best_score:
            best_score = score
            best_cell = cell

    return best_cell
