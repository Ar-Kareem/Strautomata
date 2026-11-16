
#!/usr/bin/env python3
import random
from collections import deque, defaultdict

def policy(me, opp, valid_mask):
    """
    Havannah policy for 15x15 board:
    me, opp: lists of (r,c)
    valid_mask: 2D array-like of booleans shape NxN where True indicates a playable cell
    Returns (r,c) legal move
    """
    # Convert valid_mask to python list of lists for indexing robustness
    try:
        rows = len(valid_mask)
        cols = len(valid_mask[0])
    except Exception:
        import numpy as np
        valid_mask = valid_mask.tolist()
        rows = len(valid_mask)
        cols = len(valid_mask[0])
    # neighbor function according to the representation given in the prompt
    def neighbors(cell):
        r, c = cell
        # neighbor rules based on description
        cand = [(r-1, c), (r+1, c), (r-1, c-1), (r, c-1), (r, c+1), (r-1, c+1)]
        for nr, nc in cand:
            if 0 <= nr < rows and 0 <= nc < cols and valid_mask[nr][nc]:
                yield (nr, nc)

    # Build sets for quick lookup
    me_set = set(me)
    opp_set = set(opp)

    # Build list of all valid empty cells
    empties = []
    for r in range(rows):
        for c in range(cols):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                empties.append((r, c))
    if not empties:
        # Shouldn't happen per rules, but just in case
        for r in range(rows):
            for c in range(cols):
                if valid_mask[r][c] and (r,c) not in me_set and (r,c) not in opp_set:
                    return (r,c)
        # fallback pick any valid cell
        for r in range(rows):
            for c in range(cols):
                if valid_mask[r][c]:
                    return (r,c)

    # Precompute degrees (number of valid neighbors) for boundary detection
    deg = {}
    boundary_cells = set()
    for r in range(rows):
        for c in range(cols):
            if not valid_mask[r][c]:
                continue
            d = 0
            for nb in neighbors((r,c)):
                d += 1
            deg[(r,c)] = d
            if d < 6:
                boundary_cells.add((r,c))

    # Identify the six corners as boundary cells with minimal degree (likely 3)
    # If not exactly 6 with degree 3, relax threshold to smallest degrees found until we get 6
    corners = []
    for cell in boundary_cells:
        if deg[cell] == 3:
            corners.append(cell)
    if len(corners) != 6:
        # relax: pick 6 smallest-degree boundary cells
        sorted_b = sorted(boundary_cells, key=lambda x: deg[x])
        corners = sorted_b[:6]

    # Build ordered boundary cycle starting from one corner
    boundary_neighbors = {}
    for cell in boundary_cells:
        boundary_neighbors[cell] = [nb for nb in neighbors(cell) if nb in boundary_cells]

    def build_boundary_order():
        if not corners:
            return []
        start = corners[0]
        # pick a neighbor of start along boundary to go
        neighs = boundary_neighbors.get(start, [])
        if not neighs:
            return [start]
        # choose neighbor that continues boundary
        path = [start, neighs[0]]
        visited = {start}
        # Walk until loop back to start
        while True:
            cur = path[-1]
            prev = path[-2]
            # pick next neighbor among boundary neighbors except prev
            next_cell = None
            for nb in boundary_neighbors.get(cur, []):
                if nb == prev:
                    continue
                # prefer not yet visited to move forward
                next_cell = nb
                break
            if next_cell is None:
                # cannot proceed; stop
                break
            if next_cell == start:
                path.append(next_cell)
                break
            if next_cell in path:
                # loop encountered, break
                path.append(next_cell)
                break
            path.append(next_cell)
            if len(path) > len(boundary_cells) + 5:
                break
        # remove last repeated start if present
        if len(path) >= 2 and path[-1] == path[0]:
            path = path[:-1]
        return path

    boundary_order = build_boundary_order()
    edge_index = {}  # map boundary cell -> edge id 0..5
    if boundary_order and len(corners) == 6:
        # find corner indices in order
        # find nearest positions of corners in order
        corner_positions = []
        corner_set = set(corners)
        # locate indices where boundary_order item is a corner
        indices = [i for i,cell in enumerate(boundary_order) if cell in corner_set]
        if len(indices) >= 6:
            # produce segments between consecutive corner indices
            # choose first six in cyclic manner
            indices = indices[:6]
            n = len(boundary_order)
            for k in range(6):
                i = indices[k]
                j = indices[(k+1)%6]
                # traverse from i to j (exclusive of j), modulo n
                idx = i
                while True:
                    cell = boundary_order[idx]
                    edge_index[cell] = k
                    if idx == j:
                        break
                    idx = (idx+1) % n
                    if idx == i:
                        break
        else:
            # fallback: partition boundary_order evenly into 6 segments
            L = len(boundary_order)
            if L == 0:
                pass
            else:
                seg = max(1, L // 6)
                k = 0
                for idx, cell in enumerate(boundary_order):
                    edge_index[cell] = min(5, idx // seg)
    else:
        # fallback: label each boundary cell with a pseudo-edge via hashing to 6 buckets
        for cell in boundary_cells:
            edge_index[cell] = (cell[0]*31 + cell[1]) % 6

    # Helper: build player's adjacency graph (only among their stones)
    def build_player_graph(stones_set):
        adj = {}
        for s in stones_set:
            nbrs = [nb for nb in neighbors(s) if nb in stones_set]
            adj[s] = nbrs
        return adj

    # Win detection for a player's stones set
    def check_win(stones_set):
        if not stones_set:
            return False
        adj = build_player_graph(stones_set)
        visited = set()
        # precompute components via BFS/DFS
        components = []
        for s in stones_set:
            if s in visited:
                continue
            comp = []
            stack = [s]
            visited.add(s)
            while stack:
                u = stack.pop()
                comp.append(u)
                for v in adj.get(u, []):
                    if v not in visited:
                        visited.add(v)
                        stack.append(v)
            components.append(comp)
        # corners touched by each component
        corner_set = set(corners)
        for comp in components:
            comp_set = set(comp)
            # Bridge: touches two distinct corners
            touched_corners = corner_set.intersection(comp_set)
            if len(touched_corners) >= 2:
                return True
            # Fork: touches >=3 distinct edges
            touched_edges = set()
            for cell in comp:
                if cell in edge_index:
                    touched_edges.add(edge_index[cell])
            if len(touched_edges) >= 3:
                return True
            # Ring: detect cycle in component graph with length >=6
            # DFS with parent tracking and depths
            depth = {}
            parent = {}
            found_ring = False
            def dfs(u, d):
                nonlocal found_ring
                depth[u] = d
                for v in adj.get(u, []):
                    if v not in depth:
                        parent[v] = u
                        dfs(v, d+1)
                        if found_ring:
                            return
                    else:
                        if parent.get(u) == v:
                            continue
                        # found back edge from u to v
                        cycle_len = depth[u] - depth[v] + 1
                        if cycle_len >= 6:
                            found_ring = True
                            return
            for start in comp:
                if start not in depth:
                    parent[start] = None
                    dfs(start, 0)
                if found_ring:
                    return True
        return False

    # Quick immediate win check for our moves
    # For speed, we simulate by adding the cell to me_set and using check_win
    # (small sets so acceptable)
    for mv in empties:
        new_me = set(me_set)
        new_me.add(mv)
        if check_win(new_me):
            return mv

    # Block opponent immediate wins
    for mv in empties:
        new_opp = set(opp_set)
        new_opp.add(mv)
        if check_win(new_opp):
            return mv

    # Precompute components for me to evaluate merge effects
    me_adj = build_player_graph(me_set)
    # map cell -> component id
    comp_id = {}
    comp_cells = []
    visited = set()
    for s in me_set:
        if s in visited:
            continue
        cid = len(comp_cells)
        stack = [s]
        comp_cells.append([])
        visited.add(s)
        while stack:
            u = stack.pop()
            comp_id[u] = cid
            comp_cells[cid].append(u)
            for v in me_adj.get(u, []):
                if v not in visited:
                    visited.add(v)
                    stack.append(v)

    # Precompute touched edges and corners per component
    comp_touched_edges = [set() for _ in comp_cells]
    comp_touched_corners = [set() for _ in comp_cells]
    for cid, cells in enumerate(comp_cells):
        for cell in cells:
            if cell in edge_index:
                comp_touched_edges[cid].add(edge_index[cell])
            if cell in corners:
                comp_touched_corners[cid].add(cell)

    # Heuristic scoring for each empty cell
    best_move = None
    best_score = -10**9
    base_center = ((rows-1)/2.0, (cols-1)/2.0)
    for mv in empties:
        r, c = mv
        score = 0
        # center preference
        cr, cc = base_center
        distc = abs(r-cr) + abs(c-cc)
        score -= 0.2 * distc

        # adjacency counts
        adj_me = 0
        adj_opp = 0
        adjacent_me_components = set()
        for nb in neighbors(mv):
            if nb in me_set:
                adj_me += 1
                adjacent_me_components.add(comp_id.get(nb, -1))
            if nb in opp_set:
                adj_opp += 1
        score += 6 * adj_me
        score += 2 * adj_opp  # also helpful to be near opponent (block/connect)

        # Evaluate how this move merges components and increases edges/corners
        # New component would include mv plus all adjacent me components
        merged_edges = set()
        merged_corners = set()
        merged_cells_count = 1
        for nb in neighbors(mv):
            if nb in me_set:
                cid = comp_id.get(nb)
                if cid is not None:
                    merged_edges |= comp_touched_edges[cid]
                    merged_corners |= comp_touched_corners[cid]
                    merged_cells_count += len(comp_cells[cid])
        # If mv itself on edge/corner
        if mv in edge_index:
            merged_edges.add(edge_index[mv])
        if mv in corners:
            merged_corners.add(mv)
        # Reward touching more edges (toward fork)
        # compute delta edges vs max present in adjacent components
        prev_edges_count = 0
        for cid in adjacent_me_components:
            if cid != -1:
                prev_edges_count = max(prev_edges_count, len(comp_touched_edges[cid]))
        delta_edges = max(0, len(merged_edges) - prev_edges_count)
        score += 40 * delta_edges

        # Reward corner touches leading towards bridge
        prev_corners_count = 0
        for cid in adjacent_me_components:
            if cid != -1:
                prev_corners_count = max(prev_corners_count, len(comp_touched_corners[cid]))
        delta_corners = max(0, len(merged_corners) - prev_corners_count)
        score += 60 * delta_corners

        # Encourage making larger connected component
        score += 0.5 * merged_cells_count

        # Penalize moves that are isolated (no adjacency) slightly
        if adj_me == 0 and adj_opp == 0:
            score -= 1.0

        # Try to block opponent connectivity: if this move touches opponent stones that belong to different opponent components, reward
        # quick compute neighbor opponent components
        opp_adj_sets = {}
        opp_adj_list = []
        for nb in neighbors(mv):
            if nb in opp_set:
                opp_adj_list.append(nb)
        # if this move is adjacent to multiple distinct opponent components, reward blocking
        # Build small BFS for opp components
        opp_comp_ids = {}
        # Build opponent graph
        opp_adj = {}
        for s in opp_set:
            opp_adj[s] = [nb for nb in neighbors(s) if nb in opp_set]
        visited_opp = set()
        cid = 0
        for s in opp_set:
            if s in visited_opp:
                continue
            stack = [s]
            compmembers = set()
            visited_opp.add(s)
            while stack:
                u = stack.pop()
                compmembers.add(u)
                for v in opp_adj.get(u, []):
                    if v not in visited_opp:
                        visited_opp.add(v)
                        stack.append(v)
            for mmb in compmembers:
                opp_comp_ids[mmb] = cid
            cid += 1
        opp_neigh_comps = set(opp_comp_ids.get(nb) for nb in opp_adj_list if nb in opp_comp_ids)
        if len(opp_neigh_comps) >= 2:
            score += 20 * (len(opp_neigh_comps)-1)

        # small random tie-breaker
        score += random.random() * 0.001

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is None:
        # pick random empty just in case
        return random.choice(empties)
    return best_move

# This allows file to be used as a module; the required function is policy(...)
if __name__ == "__main__":
    # small self-test on empty board (15x15 valid hex shape not enforced here)
    N = 15
    valid = [[True]*N for _ in range(N)]
    print(policy([], [], valid))
