
from typing import List, Tuple, Dict, Set


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah policy for a 15x15 valid-mask board.

    The implementation is deliberately self-contained and deterministic.
    It uses the neighbour convention described in the prompt:
    for odd columns the diagonal neighbours are one row upward;
    for even columns they are one row downward.
    """

    n = len(valid_mask)
    m = len(valid_mask[0]) if n else 0

    def is_valid_cell(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < m and bool(valid_mask[r][c])

    def step(r: int, c: int, d: int) -> tuple[int, int]:
        # Direction labels around the hex, clockwise.
        # 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW
        if d == 0:
            return r - 1, c
        if d == 3:
            return r + 1, c

        if c & 1:
            # Odd column: diagonals go to current/up rows.
            if d == 1:
                return r - 1, c + 1
            if d == 2:
                return r, c + 1
            if d == 4:
                return r, c - 1
            return r - 1, c - 1
        else:
            # Even column: diagonals go to current/down rows.
            if d == 1:
                return r, c + 1
            if d == 2:
                return r + 1, c + 1
            if d == 4:
                return r + 1, c - 1
            return r, c - 1

    def neighbours(cell: tuple[int, int]):
        r, c = cell
        for d in range(6):
            nr, nc = step(r, c, d)
            if is_valid_cell(nr, nc):
                yield nr, nc

    valid_cells: list[tuple[int, int]] = []
    for r in range(n):
        for c in range(m):
            if is_valid_cell(r, c):
                valid_cells.append((r, c))

    occupied: set[tuple[int, int]] = set(me) | set(opp)
    legal: list[tuple[int, int]] = [x for x in valid_cells if x not in occupied]

    if not legal:
        # Should never happen in a legal game, but return some valid coordinate if possible.
        return valid_cells[0] if valid_cells else (0, 0)

    legal_set = set(legal)
    me_set = set(me)
    opp_set = set(opp)

    # -------------------------------------------------------------------------
    # Board geometry: corner masks and edge masks.
    # -------------------------------------------------------------------------

    missing_dirs: dict[tuple[int, int], list[int]] = {}
    raw_corners: list[tuple[int, int]] = []

    for cell in valid_cells:
        r, c = cell
        miss = []
        for d in range(6):
            nr, nc = step(r, c, d)
            if not is_valid_cell(nr, nc):
                miss.append(d)
        missing_dirs[cell] = miss

        # True Havannah corners have at least two adjacent missing directions.
        is_corner = False
        if len(miss) >= 2:
            s = set(miss)
            for d in s:
                if (d + 1) % 6 in s or (d - 1) % 6 in s:
                    is_corner = True
                    break
        if is_corner:
            raw_corners.append(cell)

    # Usually this is exactly six. If the mask is slightly unusual, recover
    # six extreme boundary cells as a fallback.
    if len(raw_corners) != 6:
        candidates = list(raw_corners)

        def add_extreme(key_func, reverse=False):
            if not valid_cells:
                return
            best = max(valid_cells, key=key_func) if reverse else min(valid_cells, key=key_func)
            if best not in candidates:
                candidates.append(best)

        add_extreme(lambda x: x[0], False)
        add_extreme(lambda x: x[0], True)
        add_extreme(lambda x: x[1], False)
        add_extreme(lambda x: x[1], True)
        add_extreme(lambda x: x[0] - x[1], False)
        add_extreme(lambda x: x[0] - x[1], True)

        # If still too many, keep the most corner-like cells.
        candidates = sorted(
            set(candidates),
            key=lambda x: (-len(missing_dirs.get(x, [])), x[0], x[1])
        )
        raw_corners = candidates[:6]

    corners = sorted(raw_corners)
    corner_index = {cell: i for i, cell in enumerate(corners[:6])}

    cell_corner_mask: dict[tuple[int, int], int] = {}
    cell_edge_mask: dict[tuple[int, int], int] = {}

    for cell in valid_cells:
        if cell in corner_index:
            cell_corner_mask[cell] = 1 << corner_index[cell]
            # Corner points are not considered edge points for fork purposes.
            cell_edge_mask[cell] = 0
        else:
            cell_corner_mask[cell] = 0
            mask = 0
            for d in missing_dirs[cell]:
                mask |= 1 << d
            cell_edge_mask[cell] = mask

    def popcount(x: int) -> int:
        return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")

    # -------------------------------------------------------------------------
    # Win detection.
    # Bridge/fork: component masks.
    # Ring: any cycle in a connected component of same-colour stones.
    # -------------------------------------------------------------------------

    def is_win(stones_iter) -> bool:
        stones = list(set(stones_iter))
        k = len(stones)
        if k < 2:
            return False

        idx = {p: i for i, p in enumerate(stones)}
        parent = list(range(k))
        rank = [0] * k

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1

        edges = []
        for i, p in enumerate(stones):
            for nb in neighbours(p):
                j = idx.get(nb)
                if j is not None and i < j:
                    edges.append((i, j))
                    union(i, j)

        comp_vertices: Dict[int, int] = {}
        comp_edges: Dict[int, int] = {}
        comp_corner: Dict[int, int] = {}
        comp_edge: Dict[int, int] = {}

        for i, p in enumerate(stones):
            r0 = find(i)
            comp_vertices[r0] = comp_vertices.get(r0, 0) + 1
            comp_corner[r0] = comp_corner.get(r0, 0) | cell_corner_mask.get(p, 0)
            comp_edge[r0] = comp_edge.get(r0, 0) | cell_edge_mask.get(p, 0)

        for a, b in edges:
            r0 = find(a)
            comp_edges[r0] = comp_edges.get(r0, 0) + 1

        for r0 in comp_vertices:
            # Bridge: connects any two corners.
            if popcount(comp_corner.get(r0, 0)) >= 2:
                return True

            # Fork: connects any three edges, corners excluded from edge masks.
            if popcount(comp_edge.get(r0, 0)) >= 3:
                return True

            # Ring approximation/exact graph-cycle test on the hex adjacency graph.
            # On the hex lattice, a same-colour graph cycle corresponds to a loop
            # surrounding at least one cell.
            if comp_edges.get(r0, 0) >= comp_vertices.get(r0, 0):
                return True

        return False

    # -------------------------------------------------------------------------
    # Immediate tactics.
    # -------------------------------------------------------------------------

    # Win immediately if possible.
    for mv in legal:
        if is_win(me + [mv]):
            return mv

    # Block opponent immediate wins.
    opp_winning_moves = []
    for mv in legal:
        if is_win(opp + [mv]):
            opp_winning_moves.append(mv)

    # -------------------------------------------------------------------------
    # Component analysis for heuristic scoring.
    # -------------------------------------------------------------------------

    def build_components(stones_set: set[tuple[int, int]]):
        stones = list(stones_set)
        idx = {p: i for i, p in enumerate(stones)}
        k = len(stones)
        parent = list(range(k))
        rank = [0] * k

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1

        for i, p in enumerate(stones):
            for nb in neighbours(p):
                j = idx.get(nb)
                if j is not None:
                    union(i, j)

        comps = {}
        root_of = {}

        for i, p in enumerate(stones):
            r0 = find(i)
            root_of[p] = r0
            if r0 not in comps:
                comps[r0] = {
                    "size": 0,
                    "edge": 0,
                    "corner": 0,
                    "libs": set(),
                }
            comps[r0]["size"] += 1
            comps[r0]["edge"] |= cell_edge_mask.get(p, 0)
            comps[r0]["corner"] |= cell_corner_mask.get(p, 0)

        for p in stones:
            r0 = root_of[p]
            for nb in neighbours(p):
                if nb not in occupied:
                    comps[r0]["libs"].add(nb)

        return {"root_of": root_of, "comps": comps}

    my_info = build_components(me_set)
    opp_info = build_components(opp_set)

    # Centre preference.
    cr = sum(r for r, _ in valid_cells) / max(1, len(valid_cells))
    cc = sum(c for _, c in valid_cells) / max(1, len(valid_cells))

    def component_potential(mv: tuple[int, int], info, defensive: bool = False):
        roots = set()
        adj_count = 0
        for nb in neighbours(mv):
            root = info["root_of"].get(nb)
            if root is not None:
                roots.add(root)
                adj_count += 1

        size = 1
        edge_mask = cell_edge_mask.get(mv, 0)
        corner_mask = cell_corner_mask.get(mv, 0)
        liberties = 0

        for nb in neighbours(mv):
            if nb not in occupied:
                liberties += 1

        for r0 in roots:
            comp = info["comps"][r0]
            size += comp["size"]
            edge_mask |= comp["edge"]
            corner_mask |= comp["corner"]
            liberties += len(comp["libs"])

        edge_count = popcount(edge_mask)
        corner_count = popcount(corner_mask)

        score = 0.0

        # General connection value.
        score += 35.0 * size
        score += 180.0 * adj_count
        score += 500.0 * max(0, len(roots) - 1)
        score += 28.0 * liberties

        # Fork/bridge construction value.
        score += 1150.0 * edge_count
        score += 1550.0 * corner_count

        if edge_count == 2:
            score += 3400.0
        elif edge_count >= 3:
            score += 15000.0

        if corner_count == 1:
            score += 2100.0
        elif corner_count >= 2:
            score += 17000.0

        # Ring-shape encouragement: moves touching multiple friendly stones,
        # especially if they join separate groups, are often tactically strong.
        if adj_count >= 2:
            score += 650.0 * adj_count
        if len(roots) >= 2:
            score += 1600.0

        if defensive:
            # Defensive score values opponent threats slightly less than our own
            # constructive threats, except near immediate bridge/fork structures.
            score *= 0.78
            if edge_count >= 2:
                score += 2200.0
            if corner_count >= 1:
                score += 1600.0

        return score, edge_count, corner_count, size, adj_count, len(roots)

    def heuristic_score(mv: tuple[int, int]) -> float:
        r, c = mv

        my_pot, my_e, my_c, my_size, my_adj, my_roots = component_potential(mv, my_info, False)
        op_pot, op_e, op_c, op_size, op_adj, op_roots = component_potential(mv, opp_info, True)

        score = my_pot + op_pot

        # Prefer central flexible cells early/mid-game.
        dist2 = (r - cr) * (r - cr) + (c - cc) * (c - cc)
        score += 900.0 / (1.0 + dist2)

        # Small local shape bonuses.
        empty_nei = 0
        my_nei = 0
        opp_nei = 0
        for nb in neighbours(mv):
            if nb in me_set:
                my_nei += 1
            elif nb in opp_set:
                opp_nei += 1
            else:
                empty_nei += 1

        score += 75.0 * empty_nei
        score += 220.0 * my_nei
        score += 145.0 * opp_nei

        # If this move is one of several opponent wins, heavily favour it.
        if mv in opp_winning_moves:
            score += 50000.0

        # Deterministic tiny tie-breaker.
        score += ((r * 31 + c * 17) % 13) * 0.01
        return score

    if opp_winning_moves:
        # If there is exactly one immediate threat, block it. If several, choose
        # the block that gives us the best counterplay.
        if len(opp_winning_moves) == 1:
            return opp_winning_moves[0]
        best_block = max(opp_winning_moves, key=heuristic_score)
        if best_block in legal_set:
            return best_block

    # -------------------------------------------------------------------------
    # Threat creation search on top heuristic candidates.
    # -------------------------------------------------------------------------

    scored = [(heuristic_score(mv), mv) for mv in legal]
    scored.sort(reverse=True, key=lambda x: x[0])

    # In the opening, if the board is empty, simply take the most central cell.
    if not me and not opp:
        return scored[0][1]

    top_count = min(24, len(scored))
    best_score, best_move = scored[0]

    # Reward moves that create multiple immediate winning replies.
    for base, mv in scored[:top_count]:
        remaining = [x for x in legal if x != mv]
        my_after = me + [mv]

        threats = 0
        # Stop counting after two; double threats are already decisive.
        for reply in remaining:
            if is_win(my_after + [reply]):
                threats += 1
                if threats >= 2:
                    break

        tactical = base
        if threats >= 2:
            tactical += 65000.0
        elif threats == 1:
            tactical += 8500.0

        if tactical > best_score:
            best_score = tactical
            best_move = mv

    if best_move in legal_set:
        return best_move

    # Absolute safety fallback: always return a legal move.
    return legal[0]
