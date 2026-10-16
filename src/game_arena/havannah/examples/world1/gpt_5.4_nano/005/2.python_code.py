
import random
from collections import deque

# 15x15 Havannah-like board on a skewed 2D indexing.
# We treat the 2D array (r,c) as a hex grid using the neighbor pattern implied by the prompt:
# Example store at (4,1) touches (5,1),(3,1),(3,0),(4,0),(4,2),(3,2).
NEIGHBORS = {
    (r, c): [
        (r + 1, c),     # b+1
        (r - 1, c),     # b-1
        (r - 1, c - 1), # left column
        (r, c - 1),     # left column
        (r, c + 1),     # right column
        (r - 1, c + 1), # right column
    ]
    for r in range(15) for c in range(15)
}

# Corner/edge sets in terms of (row,col) for the 15x15 representation.
# Using the common mapping for this 2D-indexed hex embedding:
# - corners: (0,0), (0,14), (14,0), (14,14), (0,7), (14,7)
# However, different arenas may use a different corner definition.
# We'll instead infer "outer corners" from valid_mask by selecting playable cells
# with minimal/maximal row and col patterns.
# To stay robust, we compute corners as the six extreme points along the three axes.
def _compute_corners(valid_mask):
    N = len(valid_mask)
    # For this embedding, use three axial-like axes:
    # axis1: (r)
    # axis2: (c)
    # axis3: (r - c)
    # Corners correspond to extremes of each axis.
    cells = [(r,c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    if not cells:
        return []
    # Pick min/max along each axis; then dedupe and keep 6 by farthest extremes.
    extrema = []
    for key in ("r", "c", "d"):
        pass
    def axis1(x): return x[0]
    def axis2(x): return x[1]
    def axis3(x): return x[0]-x[1]
    axes = [axis1, axis2, axis3]
    extreme_pairs = []
    for ax in axes:
        mn = min(cells, key=ax)
        mx = max(cells, key=ax)
        extreme_pairs.append(mn)
        extreme_pairs.append(mx)
    # Deduplicate
    uniq = []
    seen = set()
    for x in extreme_pairs:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    # If more/less than 6 due to invalid-mask peculiarities, refine:
    # choose candidates among farthest along each axis by selecting multiple tied extrema.
    if len(uniq) != 6:
        # Recompute by selecting top/bottom few for each axis and taking union.
        cand = set()
        for ax in axes:
            vals = sorted(set(ax(x) for x in cells))
            minv = vals[0]
            maxv = vals[-1]
            # include all cells close to extremes within 1 step (for stability)
            for v in vals[:2]:
                for x in cells:
                    if ax(x) == v:
                        cand.add(x)
            for v in vals[-2:]:
                for x in cells:
                    if ax(x) == v:
                        cand.add(x)
        # Pick up to 6 by a scoring using distance to board center on each axis.
        center = (N-1)/2
        def dist(x):
            r,c=x
            # larger spread
            return (abs(r-center)+abs(c-center)+abs((r-c)-0))
        uniq = sorted(list(cand), key=dist, reverse=True)[:6]
    # If still not 6, pad with repeats (should be rare); later checks remain safe.
    while len(uniq) < 6:
        uniq.append(uniq[-1])
    return uniq[:6]

def _build_sets(me, opp):
    me_set = set(me)
    opp_set = set(opp)
    return me_set, opp_set

def _legal_moves(valid_mask, me_set, opp_set):
    N = len(valid_mask)
    occ = me_set | opp_set
    moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r,c) not in occ:
                moves.append((r,c))
    return moves

def _neighbors(cell, N=15):
    r,c = cell
    res = []
    for rr,cc in NEIGHBORS[(r,c)]:
        if 0 <= rr < N and 0 <= cc < N:
            res.append((rr,cc))
    return res

def _would_win(move, player_set, opp_set, valid_mask):
    # Place move and check ring/bridge/fork by graph analysis.
    N = len(valid_mask)
    if not valid_mask[move[0]][move[1]]:
        return False

    stones = set(player_set)
    stones.add(move)

    # BFS connected components on our stones
    unvisited = set(stones)
    visited = set()
    for start in list(unvisited):
        if start not in unvisited:
            continue
        q = deque([start])
        comp = []
        unvisited.remove(start)
        visited.add(start)
        while q:
            u = q.popleft()
            comp.append(u)
            for v in _neighbors(u, N):
                if v in stones and v in unvisited:
                    unvisited.remove(v)
                    q.append(v)
        # For each component, check bridge/fork/ring
        if _component_wins(comp, stones, valid_mask, N):
            return True
    return False

def _component_wins(comp, stones, valid_mask, N):
    # comp is a connected set of player stones.
    # Bridge & Fork require edge/corner membership; Ring requires detecting a loop.
    corners, edges = _corners_and_edges(valid_mask, N)
    comp_set = set(comp)

    # Bridge: connect any two corner cells
    comp_corners = [x for x in corners if x in comp_set]
    if len(comp_corners) >= 2:
        # Any two of the six corners
        # since component is connected, if it includes both corners, it's a bridge.
        return True if len(comp_corners) >= 2 else False

    # Fork: connect any three edges (corners not counted as edges intersections)
    # We'll define edges as 6 lines' endpoints? Instead we derive 6 edge cells and treat
    # membership in edge sets excluding corners.
    if edges:
        edge_hits = set()
        for ei, eset in enumerate(edges):
            if any(x in comp_set for x in eset):
                edge_hits.add(ei)
        # Fork is any three edges
        if len(edge_hits) >= 3:
            return True

    # Ring detection:
    # Need to see if stones form a loop around at least one cell.
    # Robust ring detection is complex; we approximate using planar embedding on this 2D index.
    # Practical approach:
    # - Consider the "dual" of the hex grid by constructing a grid graph of faces/cells (board cells).
    # - Ring exists if there's an enclosed area not reachable from outside when treating stones as barriers.
    # We'll do this with a flood fill on empty/other cells in the board using adjacency that matches
    # hex-grid face adjacency.
    return _ring_exists_by_flood(comp_set, stones, valid_mask, N)

def _corners_and_edges(valid_mask, N):
    corners = _compute_corners(valid_mask)
    # Define 6 edges as strips between corners (excluding corners).
    # We approximate edges by grouping cells near each extreme axis direction.
    cells = [(r,c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    # Axis values
    def axis1(x): return x[0]
    def axis2(x): return x[1]
    def axis3(x): return x[0]-x[1]
    axes = [axis1, axis2, axis3]
    # Edge sets: top, bottom, left, right, diag1, diag2 based on extremes with thresholds.
    # Determine thresholds from corners:
    # For each axis, define min-side and max-side "edge".
    edge_sets = []
    for ax in axes:
        minv = min(ax(x) for x in corners)
        maxv = max(ax(x) for x in corners)
        # include cells within 0..1 of extreme (robust to invalid mask thickness)
        # and not on corners.
        minset = set()
        maxset = set()
        for x in cells:
            if x in corners:
                continue
            v = ax(x)
            # allow within 1 from extreme
            if v <= minv + 1:
                minset.add(x)
            if v >= maxv - 1:
                maxset.add(x)
        edge_sets.append(minset)
        edge_sets.append(maxset)
    # edge_sets currently has 6 sets (2 per axis). Ensure length=6.
    if len(edge_sets) != 6:
        # fallback: split into any 6 by unique mapping
        edge_sets = edge_sets[:6] + [set()] * max(0, 6-len(edge_sets))
    # dedupe by content (not required)
    edges = edge_sets
    return corners, edges

def _ring_exists_by_flood(comp_set, stones, valid_mask, N):
    # Flood fill "space" consisting of all board cells (playable cells).
    # Treat stones as walls. If there exists an empty cell region that is not reachable
    # from outside when expanding through non-stone cells, then stones surround it => ring.
    # To allow "outside", we also allow positions just beyond the playable set; but we can
    # emulate by starting flood from all non-stone cells on the outer boundary.
    # Outer boundary: cells with at least one neighbor not valid_mask (or outside board).
    playable = {(r,c) for r in range(N) for c in range(N) if valid_mask[r][c]}
    empty_cells = playable - stones

    if not empty_cells:
        return False

    # Determine boundary empty cells
    boundary = set()
    for (r,c) in empty_cells:
        for rr,cc in _neighbors((r,c), N):
            if not (0 <= rr < N and 0 <= cc < N) or not valid_mask[rr][cc]:
                boundary.add((r,c))
                break

    # Flood fill reachable empty cells
    q = deque(boundary)
    reachable = set(boundary)
    while q:
        u = q.popleft()
        for v in _neighbors(u, N):
            if v in empty_cells and v not in reachable:
                reachable.add(v)
                q.append(v)

    # If there is any empty cell not reachable, it's enclosed.
    return len(reachable) < len(empty_cells)

def _score_move(move, me_set, opp_set, valid_mask):
    # Higher is better for player-0 (us)
    N = len(valid_mask)
    # Immediate tactical: if opponent threatens ring/bridge/fork, block already handled elsewhere.
    # Here use heuristic:
    stones = me_set | {move}

    corners, edges = _corners_and_edges(valid_mask, N)

    # Connectivity: number of adjacent friendly stones
    adj_f = 0
    adj_o = 0
    for nb in _neighbors(move, N):
        if valid_mask[nb[0]][nb[1]]:
            if nb in me_set:
                adj_f += 1
            elif nb in opp_set:
                adj_o += 1

    # Cluster size after move
    cluster_size = _component_size_with_move(move, me_set, valid_mask, N)
    # Centrality preference (helps general strength)
    center = (N-1)/2
    r,c = move
    centrality = - (abs(r-center) + abs(c-center))  # closer to center is higher (less negative)

    # Bridge potential: how many corners become connected within our component if we play here.
    comp_corners = _component_corners_with_move(move, me_set, valid_mask, N, corners)
    corner_count = len(comp_corners)
    bridge_bonus = 0
    if corner_count >= 2:
        bridge_bonus = 50 + 10 * corner_count
    else:
        # partial progress
        bridge_bonus = 8 * corner_count

    # Fork potential: edge intersections
    edge_hits = set()
    comp_set = _component_with_move_set(move, me_set, valid_mask, N)
    for ei, eset in enumerate(edges):
        if any(x in comp_set for x in eset):
            edge_hits.add(ei)
    fork_bonus = 0
    if len(edge_hits) >= 3:
        fork_bonus = 50 + 10 * len(edge_hits)
    else:
        fork_bonus = 6 * len(edge_hits)

    # Ring encouragement: heuristic based on adjacency to our stones and "span" near boundary
    ring_hint = 0
    # If move is near many friendly stones that could create enclosure, reward.
    ring_hint += 2 * adj_f
    # If move is on/near boundary, ring is easier in Havannah; small bias.
    boundary_bias = 0
    for rr,cc in _neighbors(move, N):
        if not (0 <= rr < N and 0 <= cc < N) or not valid_mask[rr][cc]:
            boundary_bias = 3
            break

    # Penalty if it gives opponent too much adjacency
    danger = 2 * adj_o

    # Total
    return (10 * cluster_size) + (3 * adj_f) + bridge_bonus + fork_bonus + 1.5 * ring_hint + boundary_bias + 0.2 * centrality - danger

def _component_size_with_move(move, me_set, valid_mask, N):
    # BFS component size of our stones including move
    stones = me_set | {move}
    visited = set()
    q = deque([move])
    visited.add(move)
    while q:
        u = q.popleft()
        for v in _neighbors(u, N):
            if valid_mask[v[0]][v[1]] and v in stones and v not in visited:
                visited.add(v)
                q.append(v)
    return len(visited)

def _component_with_move_set(move, me_set, valid_mask, N):
    stones = me_set | {move}
    visited = set([move])
    q = deque([move])
    while q:
        u = q.popleft()
        for v in _neighbors(u, N):
            if valid_mask[v[0]][v[1]] and v in stones and v not in visited:
                visited.add(v)
                q.append(v)
    return visited

def _component_corners_with_move(move, me_set, valid_mask, N, corners):
    comp = _component_with_move_set(move, me_set, valid_mask, N)
    return [x for x in corners if x in comp]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask):
    me_set, opp_set = _build_sets(me, opp)
    moves = _legal_moves(valid_mask, me_set, opp_set)
    if not moves:
        # Should never happen if valid_mask correct; return any legal-looking fallback
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask)):
                if valid_mask[r][c] and (r,c) not in me_set and (r,c) not in opp_set:
                    return (r,c)
        return (0,0)

    # Seeded randomness for tie-breaking
    rng = random.Random(0)

    # 1) Win immediately
    for mv in moves:
        if _would_win(mv, me_set, opp_set, valid_mask):
            return mv

    # 2) Block opponent immediate win
    for mv in moves:
        if _would_win(mv, opp_set, me_set, valid_mask):
            return mv

    # 3) Otherwise score
    best_mv = moves[0]
    best_score = -10**18
    for mv in moves:
        sc = _score_move(mv, me_set, opp_set, valid_mask)
        # Small jitter
        sc += rng.uniform(-0.25, 0.25)
        if sc > best_score:
            best_score = sc
            best_mv = mv
    return best_mv
