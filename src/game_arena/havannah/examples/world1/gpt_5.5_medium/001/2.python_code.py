
import math
from collections import deque, defaultdict


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah policy for a 15x15 embedded hex board.

    Always returns a legal empty playable cell.
    """
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0

    me_set = set(tuple(x) for x in me)
    opp_set = set(tuple(x) for x in opp)
    occupied = me_set | opp_set

    valid_cells = []
    valid_set = set()
    for r in range(rows):
        for c in range(cols):
            if bool(valid_mask[r][c]):
                cell = (r, c)
                valid_cells.append(cell)
                valid_set.add(cell)

    legal = [cell for cell in valid_cells if cell not in occupied]

    # Absolute fallback. In a normal game this branch is never reached.
    if not legal:
        return valid_cells[0] if valid_cells else (0, 0)

    # Odd-q vertical layout. This matches the prompt's example for column 1.
    def ordered_neighbor_coords(cell):
        r, c = cell
        if c & 1:
            # N, NE, SE, S, SW, NW
            return [
                (r - 1, c),
                (r - 1, c + 1),
                (r, c + 1),
                (r + 1, c),
                (r, c - 1),
                (r - 1, c - 1),
            ]
        else:
            return [
                (r - 1, c),
                (r, c + 1),
                (r + 1, c + 1),
                (r + 1, c),
                (r + 1, c - 1),
                (r, c - 1),
            ]

    neighbors = {}
    for cell in valid_cells:
        neighbors[cell] = [n for n in ordered_neighbor_coords(cell) if n in valid_set]

    # Axial/cube-like coordinates for identifying the six sides.
    def axial(cell):
        r, c = cell
        q = c
        ar = r - ((c - (c & 1)) // 2)
        return q, ar

    axes = {}
    xs, ys, zs = [], [], []
    for cell in valid_cells:
        x, z = axial(cell)
        y = -x - z
        axes[cell] = (x, y, z)
        xs.append(x)
        ys.append(y)
        zs.append(z)

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)

    def side_ids(cell):
        x, y, z = axes[cell]
        ids = []
        if x == minx:
            ids.append(0)
        if x == maxx:
            ids.append(1)
        if y == miny:
            ids.append(2)
        if y == maxy:
            ids.append(3)
        if z == minz:
            ids.append(4)
        if z == maxz:
            ids.append(5)
        return ids

    corner_cells = []
    raw_side_ids = {}
    for cell in valid_cells:
        sids = side_ids(cell)
        raw_side_ids[cell] = sids
        if len(sids) >= 2:
            corner_cells.append(cell)

    corner_cells = sorted(corner_cells)
    cell_corner = {cell: i for i, cell in enumerate(corner_cells)}

    cell_edges = {}
    for cell in valid_cells:
        if cell in cell_corner:
            cell_edges[cell] = set()
        else:
            cell_edges[cell] = set(raw_side_ids[cell])

    boundary_cells = [cell for cell in valid_cells if len(neighbors[cell]) < 6]

    def edge_distance(cell):
        x, y, z = axes[cell]
        return min(x - minx, maxx - x, y - miny, maxy - y, z - minz, maxz - z)

    center_r = sum(r for r, _ in valid_cells) / float(len(valid_cells))
    center_c = sum(c for _, c in valid_cells) / float(len(valid_cells))

    def build_components(stones):
        comp_id = {}
        comps = []
        seen = set()

        for start in stones:
            if start in seen:
                continue

            cid = len(comps)
            q = deque([start])
            seen.add(start)

            size = 0
            corners = set()
            edges = set()

            while q:
                cur = q.popleft()
                comp_id[cur] = cid
                size += 1

                if cur in cell_corner:
                    corners.add(cell_corner[cur])
                edges.update(cell_edges.get(cur, set()))

                for nb in neighbors.get(cur, ()):
                    if nb in stones and nb not in seen:
                        seen.add(nb)
                        q.append(nb)

            comps.append({
                "size": size,
                "corners": corners,
                "edges": edges,
            })

        return comp_id, comps

    def has_ring(player_stones):
        """
        Ring test by flood filling all non-player cells from the board boundary.
        Any non-player cell not reachable from the boundary is enclosed.
        """
        visited = set()
        q = deque()

        for b in boundary_cells:
            if b not in player_stones:
                visited.add(b)
                q.append(b)

        while q:
            cur = q.popleft()
            for nb in neighbors[cur]:
                if nb not in player_stones and nb not in visited:
                    visited.add(nb)
                    q.append(nb)

        for cell in valid_cells:
            if cell not in player_stones and cell not in visited:
                return True
        return False

    def is_win_after(stones, move):
        if move in stones:
            return False

        new_stones = set(stones)
        new_stones.add(move)

        # Only the component containing the new move can create a new bridge/fork.
        q = deque([move])
        seen = {move}
        corners = set()
        edges = set()

        while q:
            cur = q.popleft()
            if cur in cell_corner:
                corners.add(cell_corner[cur])
            edges.update(cell_edges.get(cur, set()))

            for nb in neighbors[cur]:
                if nb in new_stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)

        if len(corners) >= 2:
            return True
        if len(edges) >= 3:
            return True

        # A ring-closing move must normally touch at least two friendly stones.
        adj_friendly = sum(1 for nb in neighbors[move] if nb in stones)
        if adj_friendly >= 2 and has_ring(new_stones):
            return True

        return False

    # 1. Play an immediate winning move.
    for mv in legal:
        if is_win_after(me_set, mv):
            return mv

    # Build components once for heuristic evaluation.
    me_comp_id, me_comps = build_components(me_set)
    opp_comp_id, opp_comps = build_components(opp_set)

    def combination2(n):
        return n * (n - 1) / 2.0

    def pattern_score(move, comp_id, stones):
        ordered = [n for n in ordered_neighbor_coords(move)]
        ids = []
        friendly_count = 0

        for nb in ordered:
            if nb in stones:
                friendly_count += 1
                ids.append(comp_id.get(nb, -1))
            else:
                ids.append(None)

        if friendly_count < 2:
            return 0.0

        score = 7.0 * friendly_count
        L = len(ids)

        for i in range(L):
            if ids[i] is None:
                continue
            for j in range(i + 1, L):
                if ids[j] is None:
                    continue
                cyclic_dist = min(j - i, L - (j - i))
                if cyclic_dist > 1:
                    score += 9.0
                    if ids[i] == ids[j] and ids[i] != -1:
                        score += 24.0

        if friendly_count >= 3:
            score += 18.0

        return score

    def potential_value(move, comp_id, comps, stones):
        adj_ids = set()
        adj_count = 0

        for nb in neighbors[move]:
            if nb in stones:
                adj_count += 1
                cid = comp_id.get(nb)
                if cid is not None:
                    adj_ids.add(cid)

        size = 1
        corners = set()
        edges = set()

        if move in cell_corner:
            corners.add(cell_corner[move])
        edges.update(cell_edges.get(move, set()))

        for cid in adj_ids:
            comp = comps[cid]
            size += comp["size"]
            corners.update(comp["corners"])
            edges.update(comp["edges"])

        empty_liberties = 0
        enemy_adj = 0
        for nb in neighbors[move]:
            if nb not in occupied:
                empty_liberties += 1
            elif nb not in stones:
                enemy_adj += 1

        val = 0.0

        # Local connection strength.
        val += 8.5 * adj_count
        val += 24.0 * max(0, len(adj_ids) - 1)
        val += 2.4 * math.sqrt(size)

        # Bridge potential.
        nc = len(corners)
        val += 36.0 * nc
        val += 58.0 * combination2(nc)

        # Fork potential.
        ne = len(edges)
        val += 20.0 * ne
        val += 42.0 * combination2(ne)
        if ne >= 2:
            val += 30.0

        # Liberties and shape.
        val += 3.0 * empty_liberties
        val -= 1.8 * enemy_adj
        val += pattern_score(move, comp_id, stones)

        return val

    def evaluate(move):
        attack = potential_value(move, me_comp_id, me_comps, me_set)
        defense = potential_value(move, opp_comp_id, opp_comps, opp_set)

        # Centrality: Havannah openings and ring/fork plans benefit from central influence.
        er = edge_distance(move)
        dr = move[0] - center_r
        dc = move[1] - center_c
        center_score = 4.0 * er - 0.18 * math.sqrt(dr * dr + dc * dc)

        adj_me = sum(1 for nb in neighbors[move] if nb in me_set)
        adj_opp = sum(1 for nb in neighbors[move] if nb in opp_set)
        adj_any = adj_me + adj_opp

        score = 1.08 * attack + 0.92 * defense + center_score

        # Early game: prefer strong central cells.
        total_stones = len(me_set) + len(opp_set)
        if total_stones <= 1:
            score += 8.0 * er

        # Avoid completely detached late moves unless they are central.
        if total_stones > 3 and adj_any == 0:
            score -= 18.0

        # Slightly prefer contested tactically relevant cells.
        score += 2.5 * adj_opp + 1.5 * adj_me

        # Deterministic tiny tie-breaker.
        score += ((move[0] * 37 + move[1] * 101) % 997) * 1e-6
        return score

    # 2. Block immediate opponent wins.
    opp_winning_moves = [mv for mv in legal if is_win_after(opp_set, mv)]
    if opp_winning_moves:
        return max(opp_winning_moves, key=evaluate)

    # 3. Otherwise play the highest-scoring strategic move.
    best = max(legal, key=evaluate)

    # Final legality guard.
    if best in valid_set and best not in occupied and bool(valid_mask[best[0]][best[1]]):
        return best

    # Last-resort legal fallback.
    for mv in legal:
        if bool(valid_mask[mv[0]][mv[1]]) and mv not in occupied:
            return mv

    return legal[0]
