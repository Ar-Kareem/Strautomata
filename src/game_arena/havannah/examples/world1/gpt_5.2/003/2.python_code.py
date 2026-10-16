
# havannah_policy.py
from __future__ import annotations

from collections import deque, defaultdict
from typing import List, Tuple, Dict, Set, Iterable, Optional

INF = 10 ** 9


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for Havannah on a 15x15 mask-embedded hex board.
    Uses tactical win/block checks + shallow minimax with heuristics.
    """
    N = len(valid_mask)
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)
    occ = me_set | opp_set

    # Collect valid cells and empties
    valid_cells: List[Tuple[int, int]] = []
    empties: List[Tuple[int, int]] = []
    for r in range(N):
        row = valid_mask[r]
        for c in range(N):
            if bool(row[c]):
                valid_cells.append((r, c))
                if (r, c) not in occ:
                    empties.append((r, c))

    # Safety fallback: should never happen in the arena, but keep legal.
    if not empties:
        # If board is full (shouldn't), return something within bounds.
        return (0, 0)

    # Precompute neighbors for valid cells using even-q offset coordinates (column parity).
    # Matches example: for (r,c) with c odd, neighbors include (r,c-1),(r-1,c-1),(r,c+1),(r-1,c+1),(r-1,c),(r+1,c)
    valid_set = set(valid_cells)

    def neighbors(cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = cell
        res = []
        # vertical neighbors always present if valid
        candidates = [(r - 1, c), (r + 1, c)]
        if (c & 1) == 0:  # even column
            # NW, SW, NE, SE
            candidates += [(r, c - 1), (r + 1, c - 1), (r, c + 1), (r + 1, c + 1)]
        else:  # odd column
            candidates += [(r - 1, c - 1), (r, c - 1), (r - 1, c + 1), (r, c + 1)]
        for rr, cc in candidates:
            if (rr, cc) in valid_set:
                res.append((rr, cc))
        return res

    neigh_map: Dict[Tuple[int, int], List[Tuple[int, int]]] = {cell: neighbors(cell) for cell in valid_cells}

    # Boundary / corners / edges detection from mask geometry
    deg: Dict[Tuple[int, int], int] = {cell: len(neigh_map[cell]) for cell in valid_cells}
    boundary: Set[Tuple[int, int]] = {cell for cell in valid_cells if deg[cell] < 6}

    # Corners typically have degree 3 on hex board boundary
    corners = [cell for cell in boundary if deg[cell] == 3]
    if len(corners) != 6:
        # Fallback: take 6 boundary cells with smallest degree, then lexicographic
        # (very unlikely for standard Havannah masks)
        corners = sorted(boundary, key=lambda x: (deg[x], x[0], x[1]))[:6]
    corners_set = set(corners)

    # Build boundary cycle order to segment into 6 edges between corners
    boundary_adj: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for cell in boundary:
        bs = [nb for nb in neigh_map[cell] if nb in boundary]
        boundary_adj[cell] = sorted(bs)

    def boundary_cycle() -> List[Tuple[int, int]]:
        # pick a corner or any boundary cell
        start = min(corners_set) if corners_set else min(boundary)
        nbs = boundary_adj.get(start, [])
        if len(nbs) < 1:
            return [start]
        # choose one direction deterministically
        nxt = nbs[0]
        cycle = [start]
        prev = None
        cur = start
        steps_cap = len(boundary) + 5
        for _ in range(steps_cap):
            cycle.append(nxt)
            prev, cur = cur, nxt
            if cur == start:
                break
            nbs2 = boundary_adj.get(cur, [])
            if not nbs2:
                break
            # boundary cells should have 2 boundary neighbors; choose the one not equal prev
            if len(nbs2) == 1:
                nxt = nbs2[0]
            else:
                nxt = nbs2[0] if nbs2[1] == prev else nbs2[1]
        # Remove last repeated start if present
        if len(cycle) > 1 and cycle[-1] == cycle[0]:
            cycle.pop()
        return cycle

    cycle = boundary_cycle()
    pos_in_cycle = {cell: i for i, cell in enumerate(cycle)}
    corner_positions = sorted([pos_in_cycle[c] for c in corners_set if c in pos_in_cycle])

    # If traversal failed, fallback to crude edge labeling by BFS from each corner segment
    edge_of: Dict[Tuple[int, int], int] = {}
    edge_cells: List[List[Tuple[int, int]]] = [[] for _ in range(6)]

    if len(corner_positions) == 6 and len(cycle) >= 6:
        # Assign edges by segments between consecutive corners in the cycle
        corner_positions_sorted = corner_positions
        L = len(cycle)
        for i in range(6):
            a = corner_positions_sorted[i]
            b = corner_positions_sorted[(i + 1) % 6]
            j = (a + 1) % L
            while j != b:
                cell = cycle[j]
                if cell not in corners_set:
                    edge_of[cell] = i
                    edge_cells[i].append(cell)
                j = (j + 1) % L
    else:
        # Fallback: classify boundary cells by nearest corner index along boundary graph (approx)
        # Not perfect but keeps heuristics functional.
        corner_list = list(corners_set)
        if len(corner_list) < 6:
            corner_list = sorted(list(boundary))[:6]
        corner_list = corner_list[:6]

        # Multi-source BFS on boundary to nearest corner id
        q = deque()
        dist_corner = {cell: INF for cell in boundary}
        owner = {cell: -1 for cell in boundary}
        for i, c0 in enumerate(corner_list):
            if c0 in boundary:
                dist_corner[c0] = 0
                owner[c0] = i
                q.append(c0)
        while q:
            u = q.popleft()
            for v in boundary_adj.get(u, []):
                if dist_corner[v] > dist_corner[u] + 1:
                    dist_corner[v] = dist_corner[u] + 1
                    owner[v] = owner[u]
                    q.append(v)

        # Create 6 "edges" as the sets owned by each corner (excluding corners); rough but usable
        for cell in boundary:
            if cell in corners_set:
                continue
            i = owner.get(cell, -1)
            if i >= 0:
                edge_of[cell] = i
                edge_cells[i].append(cell)

        corners_set = set(corner_list)
        corners = corner_list

    # --- Helper: connected components & win checks ---

    def component_info(player_stones: Set[Tuple[int, int]]) -> List[Tuple[Set[Tuple[int, int]], Set[int], Set[Tuple[int, int]]]]:
        """Return list of (component_cells, edges_touched, corners_touched)."""
        seen: Set[Tuple[int, int]] = set()
        out = []
        for s in player_stones:
            if s in seen:
                continue
            stack = [s]
            comp = set()
            edges_t = set()
            corners_t = set()
            seen.add(s)
            while stack:
                u = stack.pop()
                comp.add(u)
                if u in corners_set:
                    corners_t.add(u)
                eid = edge_of.get(u, None)
                if eid is not None:
                    edges_t.add(eid)
                for v in neigh_map.get(u, []):
                    if v in player_stones and v not in seen:
                        seen.add(v)
                        stack.append(v)
            out.append((comp, edges_t, corners_t))
        return out

    def has_bridge_or_fork(player_stones: Set[Tuple[int, int]]) -> bool:
        for _, edges_t, corners_t in component_info(player_stones):
            if len(corners_t) >= 2:
                return True
            if len(edges_t) >= 3:
                return True
        return False

    def has_ring(player_stones: Set[Tuple[int, int]]) -> bool:
        """
        Ring detection via flood-fill on non-player cells from boundary.
        If any non-player valid cell is unreachable from boundary through non-player cells,
        then player's stones enclose a region - a ring exists.
        """
        # Non-player = valid minus player stones
        # Start BFS from all boundary cells that are non-player
        start_nodes = []
        non_player = set(valid_cells)
        non_player.difference_update(player_stones)
        if not non_player:
            return False

        for b in boundary:
            if b in non_player:
                start_nodes.append(b)

        if not start_nodes:
            # Entire boundary occupied by player stones implies enclosure exists if any interior non-player exists
            return True

        vis = set()
        dq = deque(start_nodes)
        vis.update(start_nodes)
        while dq:
            u = dq.popleft()
            for v in neigh_map[u]:
                if v in non_player and v not in vis:
                    vis.add(v)
                    dq.append(v)

        # If any non-player cell is not reachable from boundary, it's enclosed
        return len(vis) != len(non_player)

    def is_win(player_stones: Set[Tuple[int, int]]) -> bool:
        # Fast checks first
        if has_bridge_or_fork(player_stones):
            return True
        # Ring check is heavier but still small on 15x15
        return has_ring(player_stones)

    # --- Candidate generation ---

    def dist2(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return (a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1])

    # Rough "center" among valid cells
    cr = sum(r for r, _ in valid_cells) / len(valid_cells)
    cc = sum(c for _, c in valid_cells) / len(valid_cells)
    center = (int(round(cr)), int(round(cc)))

    def local_counts(move: Tuple[int, int], pset: Set[Tuple[int, int]], oset: Set[Tuple[int, int]]) -> Tuple[int, int, int]:
        my_adj = 0
        opp_adj = 0
        empty_adj = 0
        for nb in neigh_map[move]:
            if nb in pset:
                my_adj += 1
            elif nb in oset:
                opp_adj += 1
            else:
                empty_adj += 1
        return my_adj, opp_adj, empty_adj

    def near_candidates(radius: int = 2) -> Set[Tuple[int, int]]:
        seeds = list(me_set | opp_set)
        if not seeds:
            return set(empties)
        out: Set[Tuple[int, int]] = set()
        for s in seeds:
            # BFS up to radius collecting empty cells
            dq = deque([(s, 0)])
            seen = {s}
            while dq:
                u, d = dq.popleft()
                if d == radius:
                    continue
                for v in neigh_map[u]:
                    if v in seen:
                        continue
                    seen.add(v)
                    if v not in occ:
                        out.add(v)
                    dq.append((v, d + 1))
        return out

    cand_set = near_candidates(radius=2)
    if not cand_set:
        cand_set = set(empties)

    # Ensure some strategic boundary presence even if not "near"
    # (helps versus overly-local opponents)
    for b in boundary:
        if b not in occ:
            cand_set.add(b)

    # Score candidates quickly and keep top K
    cand_list = list(cand_set)

    def quick_score(mv: Tuple[int, int]) -> float:
        my_adj, opp_adj, empty_adj = local_counts(mv, me_set, opp_set)
        central = -dist2(mv, center)
        edge_bonus = 2.0 if mv in edge_of else 0.0
        corner_bonus = 3.0 if mv in corners_set else 0.0
        # Prefer connecting/merging and not being smothered
        return 3.5 * my_adj - 1.8 * opp_adj + 0.2 * empty_adj + 0.01 * central + edge_bonus + corner_bonus

    cand_list.sort(key=lambda x: (quick_score(x), -x[0], -x[1]), reverse=True)
    K = 60
    cand_list = cand_list[:K] if len(cand_list) > K else cand_list

    # If no stones: play most central legal cell
    if not me_set and not opp_set:
        best = max(empties, key=lambda mv: (-dist2(mv, center), -quick_score(mv)))
        return best

    # --- Immediate win for me ---
    for mv in cand_list:
        new_me = set(me_set)
        new_me.add(mv)
        if is_win(new_me):
            return mv

    # --- Immediate block: opponent winning moves (only moves adjacent to opponent stones) ---
    # In Havannah, an immediate win completion must connect to existing stones, so adjacency is a strong filter.
    if opp_set:
        opp_adj_empties: Set[Tuple[int, int]] = set()
        for s in opp_set:
            for nb in neigh_map[s]:
                if nb not in occ:
                    opp_adj_empties.add(nb)

        threat_moves = []
        for mv in opp_adj_empties:
            new_opp = set(opp_set)
            new_opp.add(mv)
            if is_win(new_opp):
                # Prefer blocks that also improve us
                threat_moves.append(mv)

        if threat_moves:
            # Choose the blocking move that maximizes our quick score (and is legal by construction)
            threat_moves.sort(key=lambda x: (quick_score(x), -x[0], -x[1]), reverse=True)
            return threat_moves[0]

    # --- 0-1 BFS distances for heuristic ---
    def zero_one_bfs_dist(player_stones: Set[Tuple[int, int]], block_stones: Set[Tuple[int, int]]) -> Dict[Tuple[int, int], int]:
        """
        0-1 BFS on valid cells:
        - blocked: cells in block_stones (treated as impassable)
        - entering a player stone costs 0, entering an empty costs 1
        Returns dist to all reachable cells from multi-source player stones.
        """
        if not player_stones:
            return {}

        dist = {cell: INF for cell in valid_cells}
        dq = deque()
        for s in player_stones:
            if s in block_stones:
                continue
            dist[s] = 0
            dq.appendleft(s)

        while dq:
            u = dq.popleft()
            du = dist[u]
            for v in neigh_map[u]:
                if v in block_stones:
                    continue
                w = 0 if v in player_stones else 1
                nd = du + w
                if nd < dist[v]:
                    dist[v] = nd
                    if w == 0:
                        dq.appendleft(v)
                    else:
                        dq.append(v)
        return dist

    # Prepare edge targets (excluding corners)
    edge_targets = [edge_cells[i] if edge_cells[i] else [] for i in range(6)]
    corner_targets = list(corners_set) if corners_set else []

    def eval_position(pstones: Set[Tuple[int, int]], ostones: Set[Tuple[int, int]], last_move: Tuple[int, int]) -> float:
        """
        Evaluate from perspective of pstones (player to optimize).
        """
        # Immediate win already handled elsewhere, but keep as huge value
        if is_win(pstones):
            return 1e9

        # Component containing last_move
        comp_size = 1
        touched_edges = set()
        touched_corners = set()
        if last_move in pstones:
            # BFS component
            stack = [last_move]
            seen = {last_move}
            while stack:
                u = stack.pop()
                comp_size += 1
                if u in corners_set:
                    touched_corners.add(u)
                eid = edge_of.get(u, None)
                if eid is not None:
                    touched_edges.add(eid)
                for v in neigh_map[u]:
                    if v in pstones and v not in seen:
                        seen.add(v)
                        stack.append(v)
            comp_size = len(seen)

        my_adj, opp_adj, empty_adj = local_counts(last_move, pstones, ostones)

        # 0-1 BFS distances to edges/corners
        dist = zero_one_bfs_dist(pstones, ostones)
        # If dist dict empty (shouldn't), degrade gracefully
        edge_d = []
        for i in range(6):
            best = INF
            for t in edge_targets[i]:
                d = dist.get(t, INF)
                if d < best:
                    best = d
            edge_d.append(best)
        edge_d.sort()
        corner_d = []
        for t in corner_targets:
            corner_d.append(dist.get(t, INF))
        corner_d.sort()

        # Use sums of best k as "fork/bridge potential"
        best3_edges = sum(edge_d[:3]) if len(edge_d) >= 3 else INF
        best2_corners = sum(corner_d[:2]) if len(corner_d) >= 2 else INF

        # Centrality (slight)
        central = -0.005 * dist2(last_move, center)

        # Touch bonuses (actual contact)
        touch_edges_bonus = 28.0 * len(touched_edges)
        touch_corners_bonus = 24.0 * len(touched_corners)

        # Distance potentials (smaller is better)
        pot_edges = -10.0 * best3_edges if best3_edges < INF else -200.0
        pot_corners = -7.0 * best2_corners if best2_corners < INF else -120.0

        # Local shape
        local = 3.2 * my_adj - 2.0 * opp_adj + 0.3 * empty_adj

        # Growth / cohesion
        cohesion = 1.2 * comp_size

        return touch_edges_bonus + touch_corners_bonus + pot_edges + pot_corners + local + cohesion + central

    # --- Depth-2 search (my move then opponent best reply) ---
    # Opponent reply candidates after my move: near their stones and the new stone.
    def opp_reply_candidates(new_occ: Set[Tuple[int, int]], anchor: Tuple[int, int]) -> List[Tuple[int, int]]:
        # near opponent stones and anchor within radius 2
        seeds = list(opp_set | {anchor})
        out = set()
        for s in seeds:
            dq = deque([(s, 0)])
            seen = {s}
            while dq:
                u, d = dq.popleft()
                if d == 2:
                    continue
                for v in neigh_map[u]:
                    if v in seen:
                        continue
                    seen.add(v)
                    if v not in new_occ:
                        out.add(v)
                    dq.append((v, d + 1))
        if not out:
            out = set([mv for mv in empties if mv not in new_occ])
        lst = list(out)
        lst.sort(key=lambda x: (quick_score(x), -x[0], -x[1]), reverse=True)
        return lst[:40] if len(lst) > 40 else lst

    best_move = None
    best_score = -1e18

    for mv in cand_list:
        if mv in occ:
            continue
        new_me = set(me_set)
        new_me.add(mv)
        new_occ = set(occ)
        new_occ.add(mv)

        # If opponent has an immediate win reply, this move is bad.
        # We'll search a pruned response set; immediate win completion is typically local.
        replies = opp_reply_candidates(new_occ, mv)
        worst_for_us = -1e18  # opponent will maximize their eval
        opp_can_win = False

        for rv in replies:
            if rv in new_occ:
                continue
            new_opp = set(opp_set)
            new_opp.add(rv)
            if is_win(new_opp):
                opp_can_win = True
                break
            # opponent eval from their perspective
            e_opp = eval_position(new_opp, new_me, rv)
            if e_opp > worst_for_us:
                worst_for_us = e_opp

        if opp_can_win:
            score = -1e15
        else:
            my_eval = eval_position(new_me, opp_set, mv)
            # Reduce opponent influence slightly (encourages initiative)
            score = my_eval - 0.9 * worst_for_us

        if score > best_score or (score == best_score and best_move is not None and mv < best_move):
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Ultimate fallback: any legal empty
    return empties[0]
