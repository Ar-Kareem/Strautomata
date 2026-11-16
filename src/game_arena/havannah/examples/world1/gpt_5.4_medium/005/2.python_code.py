
from collections import deque

# Cache board metadata across calls
_META_CACHE = {}


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    meta = _get_meta(valid_mask)
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    legal = [p for p in meta["valid_cells"] if p not in occupied]
    if not legal:
        # Should never happen, but return something safe-looking if it does.
        for p in meta["valid_cells"]:
            return p
        return (0, 0)

    # Opening: take center if available.
    center = meta["center"]
    if center in legal and not me_set and not opp_set:
        return center

    me_comp = _compute_components(me_set, meta)
    opp_comp = _compute_components(opp_set, meta)

    # 1) Immediate winning move for us
    winning_moves = []
    for mv in legal:
        if _is_winning_move(mv, me_set, me_comp, meta):
            winning_moves.append(mv)
    if winning_moves:
        return max(
            winning_moves,
            key=lambda mv: _base_score(mv, me_set, opp_set, me_comp, opp_comp, meta)
        )

    # 2) Immediate winning move for opponent: block
    opp_wins = []
    for mv in legal:
        if _is_winning_move(mv, opp_set, opp_comp, meta):
            opp_wins.append(mv)
    if opp_wins:
        # If multiple winning blocks exist, choose the best blocking square.
        return max(
            opp_wins,
            key=lambda mv: _base_score(mv, me_set, opp_set, me_comp, opp_comp, meta) +
                           0.8 * _base_score(mv, opp_set, me_set, opp_comp, me_comp, meta)
        )

    # 3) General heuristic
    # Also compute opponent's view of each move so we value denial.
    best_move = legal[0]
    best_score = -10**18

    for mv in legal:
        score = _base_score(mv, me_set, opp_set, me_comp, opp_comp, meta)
        deny = _base_score(mv, opp_set, me_set, opp_comp, me_comp, meta)
        total = score + 0.7 * deny

        # Mild preference for moves that may create a near-term threat.
        if _creates_strong_shape(mv, me_set, me_comp, meta):
            total += 12.0

        if total > best_score:
            best_score = total
            best_move = mv

    return best_move


def _get_meta(valid_mask):
    key = (valid_mask.shape, valid_mask.tobytes())
    meta = _META_CACHE.get(key)
    if meta is not None:
        return meta

    n = len(valid_mask)
    valid_cells = []
    row_start = [None] * n
    row_end = [None] * n
    row_len = [0] * n

    for r in range(n):
        cols = [c for c in range(n) if bool(valid_mask[r][c])]
        if cols:
            row_start[r] = cols[0]
            row_end[r] = cols[-1]
            row_len[r] = len(cols)
            for c in cols:
                valid_cells.append((r, c))

    # Standard 15x15 Havannah board has a unique longest middle row.
    max_len = max(row_len)
    middle_candidates = [r for r, L in enumerate(row_len) if L == max_len]
    mid = middle_candidates[len(middle_candidates) // 2]

    # Neighbors for standard skew embedding:
    # (r-1,c-1), (r-1,c), (r,c-1), (r,c+1), (r+1,c), (r+1,c+1)
    dirs = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]
    valid_set = set(valid_cells)

    neighbors = {}
    for r, c in valid_cells:
        ns = []
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if (nr, nc) in valid_set:
                ns.append((nr, nc))
        neighbors[(r, c)] = ns

    # Corners in perimeter order
    corners = [
        (0, row_start[0]),
        (0, row_end[0]),
        (mid, row_end[mid]),
        (n - 1, row_end[n - 1]),
        (n - 1, row_start[n - 1]),
        (mid, row_start[mid]),
    ]
    corner_mask = {p: 1 << i for i, p in enumerate(corners)}

    edge_mask = {}

    def add_edge(cell, idx):
        if cell in corner_mask:
            return
        edge_mask[cell] = edge_mask.get(cell, 0) | (1 << idx)

    # Edge 0: top row, excluding corners
    if row_start[0] is not None:
        for c in range(row_start[0] + 1, row_end[0]):
            add_edge((0, c), 0)

    # Edge 1: upper-right side
    for r in range(1, mid):
        add_edge((r, row_end[r]), 1)

    # Edge 2: lower-right side
    for r in range(mid + 1, n - 1):
        add_edge((r, row_end[r]), 2)

    # Edge 3: bottom row
    if row_start[n - 1] is not None:
        for c in range(row_start[n - 1] + 1, row_end[n - 1]):
            add_edge((n - 1, c), 3)

    # Edge 4: lower-left side
    for r in range(mid + 1, n - 1):
        add_edge((r, row_start[r]), 4)

    # Edge 5: upper-left side
    for r in range(1, mid):
        add_edge((r, row_start[r]), 5)

    boundary = set(corners) | set(edge_mask.keys())

    center = (mid, (row_start[mid] + row_end[mid]) // 2)

    meta = {
        "n": n,
        "mid": mid,
        "valid_cells": valid_cells,
        "valid_set": valid_set,
        "neighbors": neighbors,
        "corners": corners,
        "corner_mask": corner_mask,
        "edge_mask": edge_mask,
        "boundary": boundary,
        "center": center,
    }
    _META_CACHE[key] = meta
    return meta


def _compute_components(stones, meta):
    neighbors = meta["neighbors"]
    corner_mask_map = meta["corner_mask"]
    edge_mask_map = meta["edge_mask"]

    comp_id = {}
    comp_sizes = []
    comp_corner_bits = []
    comp_edge_bits = []

    cid = 0
    for s in stones:
        if s in comp_id:
            continue
        stack = [s]
        comp_id[s] = cid
        size = 0
        cbits = 0
        ebits = 0

        while stack:
            p = stack.pop()
            size += 1
            cbits |= corner_mask_map.get(p, 0)
            ebits |= edge_mask_map.get(p, 0)

            for q in neighbors[p]:
                if q in stones and q not in comp_id:
                    comp_id[q] = cid
                    stack.append(q)

        comp_sizes.append(size)
        comp_corner_bits.append(cbits)
        comp_edge_bits.append(ebits)
        cid += 1

    return {
        "comp_id": comp_id,
        "sizes": comp_sizes,
        "corner_bits": comp_corner_bits,
        "edge_bits": comp_edge_bits,
    }


def _aggregate_after_move(move, stones, comp_info, meta):
    comp_id = comp_info["comp_id"]
    sizes = comp_info["sizes"]
    cbs = comp_info["corner_bits"]
    ebs = comp_info["edge_bits"]

    adj_count = 0
    adj_ids = set()
    total_size = 1
    corner_bits = meta["corner_mask"].get(move, 0)
    edge_bits = meta["edge_mask"].get(move, 0)

    for nb in meta["neighbors"][move]:
        if nb in stones:
            adj_count += 1
            cid = comp_id[nb]
            if cid not in adj_ids:
                adj_ids.add(cid)
                total_size += sizes[cid]
                corner_bits |= cbs[cid]
                edge_bits |= ebs[cid]

    return {
        "adj_count": adj_count,
        "adj_ids": adj_ids,
        "merged_size": total_size,
        "corner_bits": corner_bits,
        "edge_bits": edge_bits,
    }


def _is_winning_move(move, stones, comp_info, meta):
    agg = _aggregate_after_move(move, stones, comp_info, meta)

    # Bridge
    if agg["corner_bits"].bit_count() >= 2:
        return True

    # Fork
    if agg["edge_bits"].bit_count() >= 3:
        return True

    # Ring
    # Usually requires connecting at least two nearby stones/components.
    if agg["adj_count"] >= 2 and _forms_ring(move, stones, meta):
        return True

    return False


def _forms_ring(move, stones, meta):
    stones2 = set(stones)
    stones2.add(move)
    seen = set()
    boundary = meta["boundary"]
    neighbors = meta["neighbors"]

    # Only regions adjacent to the newly placed stone can become newly enclosed.
    for nb in neighbors[move]:
        if nb in stones2 or nb in seen:
            continue

        q = [nb]
        seen.add(nb)
        touches_boundary = False

        while q:
            p = q.pop()
            if p in boundary:
                touches_boundary = True
            for z in neighbors[p]:
                if z not in stones2 and z not in seen:
                    seen.add(z)
                    q.append(z)

        if not touches_boundary:
            return True

    return False


def _hex_distance(a, b):
    # For coordinates on mask abs(r-c)<=k with skew-neighbor model:
    # use cube-like distance via axes (r, c, r-c)
    ar, ac = a
    br, bc = b
    dr = ar - br
    dc = ac - bc
    dz = (ar - ac) - (br - bc)
    return max(abs(dr), abs(dc), abs(dz))


def _base_score(move, my_stones, opp_stones, my_comp, opp_comp, meta):
    center = meta["center"]
    neighbors = meta["neighbors"]

    my_agg = _aggregate_after_move(move, my_stones, my_comp, meta)
    opp_agg = _aggregate_after_move(move, opp_stones, opp_comp, meta)

    score = 0.0

    # Centrality
    d = _hex_distance(move, center)
    score += 28.0 - 3.0 * d

    # Connect our stones / merge groups
    score += 12.0 * my_agg["adj_count"]
    score += 18.0 * len(my_agg["adj_ids"])
    score += 0.9 * my_agg["merged_size"]

    # Progress toward structural wins
    ccount = my_agg["corner_bits"].bit_count()
    ecount = my_agg["edge_bits"].bit_count()
    score += 14.0 * ccount
    score += 10.0 * ecount
    if ccount >= 1 and ecount >= 2:
        score += 8.0
    if ecount >= 2:
        score += 10.0

    # Blocking / contesting opponent locally
    score += 8.0 * opp_agg["adj_count"]
    score += 12.0 * len(opp_agg["adj_ids"])

    # Prefer cells with room to grow
    liberties = 0
    for nb in neighbors[move]:
        if nb not in my_stones and nb not in opp_stones:
            liberties += 1
    score += 1.5 * liberties

    # Mild bonuses for strategic boundary features, but not too much
    if move in meta["corner_mask"]:
        score += 4.0
    if move in meta["edge_mask"]:
        score += 2.0

    # Small anti-isolation penalty
    if my_agg["adj_count"] == 0 and opp_agg["adj_count"] == 0:
        score -= 6.0

    return score


def _creates_strong_shape(move, stones, comp_info, meta):
    agg = _aggregate_after_move(move, stones, comp_info, meta)
    ccount = agg["corner_bits"].bit_count()
    ecount = agg["edge_bits"].bit_count()

    # Not a win, but close to bridge/fork pressure
    if ccount >= 1 and ecount >= 2:
        return True
    if ecount >= 2 and len(agg["adj_ids"]) >= 2:
        return True
    if agg["adj_count"] >= 3:
        return True
    return False
