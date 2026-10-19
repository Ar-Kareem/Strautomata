
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah (15x15) policy.
    Returns a legal move (row, col) for the player to move.
    """

    N = 15
    me_set = set(me)
    opp_set = set(opp)

    # Build list of legal moves
    legal = []
    for r in range(N):
        rowmask = valid_mask[r]
        for c in range(N):
            if rowmask[c] and (r, c) not in me_set and (r, c) not in opp_set:
                legal.append((r, c))
    if not legal:
        # Should not happen; but for safety, return any valid unoccupied cell
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                    return (r, c)
        return (0, 0)

    # --- Neighbour model for this arena's coordinate system ---
    # Based on the prompt example, store at (4,1) touches:
    # (5,1), (3,1), (4,2), (3,2), (4,0), (5,0)
    # So general neighbors:
    # same column: (r-1,c), (r+1,c)
    # left column: (r,c-1), (r+1,c-1)
    # right column: (r,c+1), (r-1,c+1)
    def nbrs(cell):
        r, c = cell
        res = []
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r+1, c-1), (r, c+1), (r-1, c+1)):
            if 0 <= rr < N and 0 <= cc < N and valid_mask[rr][cc]:
                res.append((rr, cc))
        return res

    # --- Connectivity / Union-Find helpers ---
    parent = {}
    rank = {}
    def uf_make(nodes):
        for x in nodes:
            parent[x] = x
            rank[x] = 0
    def uf_find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def uf_union(a, b):
        ra = uf_find(a)
        rb = uf_find(b)
        if ra == rb:
            return ra
        if rank[ra] < rank[rb]:
            parent[ra] = rb
            return rb
        if rank[rb] < rank[ra]:
            parent[rb] = ra
            return ra
        parent[rb] = ra
        rank[ra] += 1
        return ra

    def component_id_map(stones):
        # returns dict cell->component root id
        uf_make(stones)
        for s in stones:
            for t in nbrs(s):
                if t in stones:
                    uf_union(s, t)
        out = {}
        for s in stones:
            out[s] = uf_find(s)
        return out, uf_find

    # Corner coordinates in this coordinate system (approx based on hex grid indexing):
    # We only need "six corner cells". In this 2D representation of a hex board,
    # the six corners are typically at:
    # leftmost top/mid/bottom, rightmost top/mid/bottom along valid cells.
    # We infer corners by scanning valid_mask extremes.
    valid_cells = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    # Compute extreme candidates for each of 3 directions to get 6 corners.
    # We'll use (c), (r), and (r+c) extremes as proxies:
    # - left edge: min c
    # - right edge: max c
    # - top-left edge and bottom-right edge: min r and max r among those on side
    # This yields corner set consistently for standard 15x15 Havannah masks.
    min_c = min(c for r, c in valid_cells)
    max_c = max(c for r, c in valid_cells)
    min_r = min(r for r, c in valid_cells)
    max_r = max(r for r, c in valid_cells)
    min_rc = min(r + c for r, c in valid_cells)
    max_rc = max(r + c for r, c in valid_cells)
    min_rm = min(r - c for r, c in valid_cells)
    max_rm = max(r - c for r, c in valid_cells)

    corners = set()
    # left-top, left-bottom: min c with min r and max r
    left_cells = [(r, c) for r, c in valid_cells if c == min_c]
    corners.add(min(left_cells, key=lambda x: x[0]))
    corners.add(max(left_cells, key=lambda x: x[0]))
    # right-top, right-bottom: max c with min r and max r
    right_cells = [(r, c) for r, c in valid_cells if c == max_c]
    corners.add(min(right_cells, key=lambda x: x[0]))
    corners.add(max(right_cells, key=lambda x: x[0]))
    # top-most and bottom-most corners among remaining extremes:
    top_cells = [(r, c) for r, c in valid_cells if r == min_r]
    bottom_cells = [(r, c) for r, c in valid_cells if r == max_r]
    corners.add(min(top_cells, key=lambda x: x[1]))  # top-left on top edge
    corners.add(max(bottom_cells, key=lambda x: x[1]))  # bottom-right on bottom edge

    # If more than 6 due to degeneracy, reduce to 6 unique by heuristic:
    # pick 6 that are most extreme under (c, r, r+c, r-c)
    def extremeness(cell):
        r, c = cell
        return (c, -r, r+c, r-c)  # arbitrary but stable
    corners = list(corners)
    corners.sort(key=extremeness)
    # keep up to 6 unique: choose 3 smallest and 3 largest by complementary
    if len(corners) > 6:
        # Rebuild corners by standard extremes in 3 axes (each gives 2 corners)
        corners = []
        # axis c: (min_c at min_r, max_r), (max_c at min_r, max_r)
        corners_set = set()
        corners_set.add(min(left_cells, key=lambda x: x[0]))
        corners_set.add(max(left_cells, key=lambda x: x[0]))
        corners_set.add(min(right_cells, key=lambda x: x[0]))
        corners_set.add(max(right_cells, key=lambda x: x[0]))
        # axis r: min_r at min_c/max_c, max_r at min_c/max_c
        top_cells = [(r, c) for r, c in valid_cells if r == min_r]
        bot_cells = [(r, c) for r, c in valid_cells if r == max_r]
        corners_set.add(min(top_cells, key=lambda x: x[1]))
        corners_set.add(max(bot_cells, key=lambda x: x[1]))
        corners = list(corners_set)
    if len(corners) != 6:
        # Fallback: pick 6 most extreme by score
        scored = sorted(valid_cells, key=lambda x: (x[1], -x[0], x[0]+x[1], x[0]-x[1]))
        corners = scored[:3] + scored[-3:]
        # unique
        uniq = []
        for x in corners:
            if x not in uniq:
                uniq.append(x)
        corners = uniq[:6]

    corners = corners[:6]

    # Edges (for fork detection): "six edges of board; corner points not part of an edge"
    # We'll approximate edges as groups of valid cells near boundary excluding corners.
    # Determine boundary cells: cells with any neighbor invalid -> boundary.
    boundary = set()
    for v in valid_cells:
        for t in nbrs(v):
            pass
        # boundary if any of the 6 "directions" steps exits valid
        # i.e., at least one neighbor coordinate is out of valid_mask
        for rr, cc in ((v[0]-1, v[1]), (v[0]+1, v[1]), (v[0], v[1]-1), (v[0]+1, v[1]-1), (v[0], v[1]+1), (v[0]-1, v[1]+1)):
            if not (0 <= rr < N and 0 <= cc < N and valid_mask[rr][cc]):
                boundary.add(v)
                break

    corner_set = set(corners)
    edge_cells = [cell for cell in boundary if cell not in corner_set]

    # Split edge_cells into 6 edge groups by proximity to the 6 corners:
    # each edge is roughly between two adjacent corners; use nearest corner distance
    # and keep cells that are closer to that corner than opposite.
    def nearest_corner(cell):
        r, c = cell
        best = None
        bestd = 10**9
        for i, (cr, cc) in enumerate(corners):
            d = abs(r-cr) + abs(c-cc)
            if d < bestd:
                bestd = d
                best = i
        return best

    # But for fork, we need "connect any three edges", not corners.
    # We'll define 6 edges as: i=0..5 determined by nearest corner; exclude cells near corners already.
    edge_of = {cell: nearest_corner(cell) for cell in edge_cells}

    # For bridge: connect any two of six corner cells.
    def check_bridge(stones):
        # components over stones
        stones_set = set(stones)
        if len(stones_set) < 2:
            return False
        uf_make(stones_set)
        for s in stones_set:
            for t in nbrs(s):
                if t in stones_set:
                    uf_union(s, t)
        corner_roots = set()
        for cr in corners:
            if cr in stones_set:
                corner_roots.add(uf_find(cr))
        # bridge if any component contains at least two corners
        roots_by = {}
        for cr in corners:
            if cr in stones_set:
                root = uf_find(cr)
                roots_by.setdefault(root, 0)
                roots_by[root] += 1
                if roots_by[root] >= 2:
                    return True
        return False

    def check_fork(stones):
        stones_set = set(stones)
        if not stones_set:
            return False
        uf_make(stones_set)
        for s in stones_set:
            for t in nbrs(s):
                if t in stones_set:
                    uf_union(s, t)
        # Determine which components touch which edges (excluding corners)
        comp_edges = {}  # root -> set(edge_index)
        for cell, ei in edge_of.items():
            if cell in stones_set:
                root = uf_find(cell)
                comp_edges.setdefault(root, set()).add(ei)
        # also consider that stones adjacent to edge-cells not included? We already included boundary excluding corners.
        for es in comp_edges.values():
            if len(es) >= 3:
                return True
        return False

    # Ring detection (cycle) is complex on a hex board.
    # We'll implement a practical approximation using planar graph cycle test:
    # - Construct adjacency graph of our stones plus candidate.
    # - Build "face" enclosure isn't easy; instead use BFS in complement to detect separation is heavy.
    # We'll use a known heuristic: a ring exists if our stones form a cycle in neighbor graph
    # that encloses at least one valid cell. We'll approximate by:
    #   - Temporarily perform flood-fill on empty cells excluding our stones.
    #   - If there is an empty region completely surrounded by our stones (no connection to boundary empties),
    #     then we likely have a ring.
    # This is still fast enough for 15x15 and good at beating casual policies.
    def check_ring(stones):
        stones_set = set(stones)
        # If too few stones, can't form ring
        if len(stones_set) < 6:
            return False

        # Empty cells
        empty = [v for v in valid_cells if v not in stones_set]
        if not empty:
            return False

        # BFS from boundary-empty cells to mark "outside" regions
        outside = set()
        q = deque()
        boundary_empty = [v for v in boundary if v not in stones_set]
        for v in boundary_empty:
            outside.add(v)
            q.append(v)
        while q:
            x = q.popleft()
            for t in nbrs(x):
                if t not in stones_set and t not in outside:
                    outside.add(t)
                    q.append(t)
        # If any empty cell not connected to outside, it is enclosed -> ring-like
        for v in valid_cells:
            if v not in stones_set and v not in outside:
                return True
        return False

    def is_win_after(move, stones_me):
        new_stones = stones_me | {move}
        return check_bridge(new_stones) or check_fork(new_stones) or check_ring(new_stones)

    # Precompute opponent legal moves for one-move win threats
    opp_stones = set(opp_set)
    my_stones = set(me_set)

    # 1) Immediate win
    for mv in legal:
        if is_win_after(mv, my_stones):
            return mv

    # 2) Block opponent immediate wins
    # Find any opponent winning moves; if our move can block any of them, try those cells.
    winning_opp_moves = []
    # (We don't know exact ring structure blocking, so we block by direct collision: if opponent wins by placing there, we take it.)
    # This catches bridge/fork reliably and ring in many cases.
    for mv in legal:
        # simulate opponent placing at mv (i.e., assume opponent can play there)
        if is_win_after(mv, opp_stones):
            winning_opp_moves.append(mv)
    # If opponent has immediate win by playing some cell, play one of those cells if it's legal (it is legal w.r.t current me/opp)
    if winning_opp_moves:
        return winning_opp_moves[0]

    # 3) Threat scoring: connectivity + adjacency + corner/edge pressure
    corners_set = set(corners)

    def component_info(stones):
        stones_set = set(stones)
        uf_make(stones_set)
        for s in stones_set:
            for t in nbrs(s):
                if t in stones_set:
                    uf_union(s, t)
        # compute for each component root: corner_count, edge_count, size
        comp = {}
        for s in stones_set:
            r = uf_find(s)
            comp.setdefault(r, {"size":0, "corners":set(), "edges":set()})
            comp[r]["size"] += 1
            if s in corners_set:
                comp[r]["corners"].add(corners.index(s))
            if s in edge_of:
                comp[r]["edges"].add(edge_of[s])
        return comp, uf_find

    def evaluate_move(mv):
        # base occupancy
        score = 0.0
        # adjacency: count friendly neighbors
        adj = 0
        for t in nbrs(mv):
            if t in my_stones:
                adj += 1
        score += 8.0 * adj

        # strategic bias towards center-ish
        score += 0.15 * (7 - abs(mv[0]-7)) + 0.15 * (7 - abs(mv[1]-7))

        # corner/edge proximity
        r, c = mv
        # distance to corners
        dmin = min(abs(r-cr)+abs(c-cc) for cr,cc in corners)
        score += 2.5 * (14 - dmin) / 14.0

        # simulate and check bridge/fork/ring with lighter weights (not full win check to save time)
        new_stones = my_stones | {mv}
        # If move is already very strong, we won't reach here because immediate win handled.
        # But for ordering, approximate with component counts.
        comp, uf_find = component_info(new_stones)
        # locate component root for mv (if mv in stones_set)
        root = uf_find(mv)
        info = comp.get(root, {"size":1, "corners":set(), "edges":set()})
        score += 1.2 * info["size"]
        score += 5.0 * len(info["corners"])  # closer to bridge
        score += 3.5 * len(info["edges"])   # closer to fork

        # ring pressure heuristic: if move reduces number of outside empty regions, reward
        # We'll do a small check: count how many outside-connected empty components remain reduced.
        # For speed, we use outside flood-fill and check if mv is on boundary or near enclosed cells.
        stones_set = set(new_stones)
        outside = set()
        q = deque()
        for v in boundary:
            if v not in stones_set and v not in outside:
                outside.add(v); q.append(v)
        while q:
            x = q.popleft()
            for t in nbrs(x):
                if t not in stones_set and t not in outside:
                    outside.add(t); q.append(t)
        enclosed_empty = sum(1 for v in valid_cells if v not in stones_set and v not in outside)
        score += 0.02 * enclosed_empty  # mild, but helps ring-building

        return score

    best = None
    best_score = -1e18
    for mv in legal:
        sc = evaluate_move(mv)
        if sc > best_score:
            best_score = sc
            best = mv

    # Tie-break randomness
    best_moves = []
    for mv in legal:
        if abs(evaluate_move(mv) - best_score) < 1e-9:
            best_moves.append(mv)
    return random.choice(best_moves) if best_moves else best
