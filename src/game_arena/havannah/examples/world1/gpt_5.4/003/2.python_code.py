
from collections import deque, defaultdict
import math

N = 15

# Hex neighbors for the board embedding described in the prompt:
# (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]


def _inside(r, c, valid_mask):
    return 0 <= r < len(valid_mask) and 0 <= c < len(valid_mask[0]) and bool(valid_mask[r][c])


def _neighbors(r, c, valid_mask):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc, valid_mask):
            yield nr, nc


def _occupied_set(me, opp):
    s = set()
    for x in me:
        s.add(tuple(x))
    for x in opp:
        s.add(tuple(x))
    return s


def _valid_cells(valid_mask):
    cells = []
    for r in range(len(valid_mask)):
        for c in range(len(valid_mask[0])):
            if bool(valid_mask[r][c]):
                cells.append((r, c))
    return cells


def _compute_corners_edges(valid_mask):
    cells = _valid_cells(valid_mask)
    row_counts = defaultdict(int)
    col_counts = defaultdict(int)
    s_counts = defaultdict(int)  # r + c

    for r, c in cells:
        row_counts[r] += 1
        col_counts[c] += 1
        s_counts[r + c] += 1

    min_row = min(row_counts)
    max_row = max(row_counts)
    min_col = min(col_counts)
    max_col = max(col_counts)
    min_s = min(s_counts)
    max_s = max(s_counts)

    corners = set()
    edge_map = {}

    for r, c in cells:
        flags = [
            r == min_row,
            r == max_row,
            c == min_col,
            c == max_col,
            (r + c) == min_s,
            (r + c) == max_s,
        ]
        cnt = sum(flags)
        if cnt >= 2:
            corners.add((r, c))

    # Edge ids 0..5, excluding corners from edges
    for r, c in cells:
        if (r, c) in corners:
            continue
        edges = set()
        if r == min_row:
            edges.add(0)
        if (r + c) == max_s:
            edges.add(1)
        if c == max_col:
            edges.add(2)
        if r == max_row:
            edges.add(3)
        if (r + c) == min_s:
            edges.add(4)
        if c == min_col:
            edges.add(5)
        edge_map[(r, c)] = edges

    return corners, edge_map


def _component_info(start, stones, valid_mask, corners, edge_map):
    q = deque([start])
    seen = {start}
    corner_hits = set()
    edge_hits = set()

    while q:
        v = q.popleft()
        if v in corners:
            corner_hits.add(v)
        if v in edge_map:
            edge_hits |= edge_map[v]
        r, c = v
        for nb in _neighbors(r, c, valid_mask):
            if nb in stones and nb not in seen:
                seen.add(nb)
                q.append(nb)

    return seen, corner_hits, edge_hits


def _has_bridge_or_fork(start, stones, valid_mask, corners, edge_map):
    _, corner_hits, edge_hits = _component_info(start, stones, valid_mask, corners, edge_map)
    if len(corner_hits) >= 2:
        return True
    if len(edge_hits) >= 3:
        return True
    return False


def _has_ring_after_move(move, stones, valid_mask):
    # Ring test:
    # Consider the board cells not occupied by stones.
    # If there exists a non-stone region adjacent to the placed move that cannot reach
    # the outside boundary through non-stone cells, then a ring exists.
    #
    # This is a practical localized test and works well for tactical ring completion.
    blocked = set(stones)

    # Candidate interior seeds are non-stone neighbors of the move
    seeds = []
    mr, mc = move
    for nb in _neighbors(mr, mc, valid_mask):
        if nb not in blocked:
            seeds.append(nb)
    if not seeds:
        return False

    # Any valid non-stone boundary cell acts as exterior access.
    boundary_nonblocked = set()
    rows = len(valid_mask)
    cols = len(valid_mask[0])

    # Determine boundary by missing some neighbor direction due to board edge;
    # equivalently, cells with degree < 6 are on the board border.
    for r in range(rows):
        for c in range(cols):
            if not bool(valid_mask[r][c]) or (r, c) in blocked:
                continue
            deg = 0
            for nr, nc in _neighbors(r, c, valid_mask):
                deg += 1
            if deg < 6:
                boundary_nonblocked.add((r, c))

    # Flood fill from each local seed; if any region does not touch boundary, ring exists.
    visited_global = set()
    for seed in seeds:
        if seed in visited_global or seed in blocked:
            continue
        q = deque([seed])
        seen = {seed}
        touches_boundary = seed in boundary_nonblocked
        while q:
            v = q.popleft()
            vr, vc = v
            for nb in _neighbors(vr, vc, valid_mask):
                if nb in blocked or nb in seen:
                    continue
                seen.add(nb)
                if nb in boundary_nonblocked:
                    touches_boundary = True
                q.append(nb)
        visited_global |= seen
        if not touches_boundary and len(seen) >= 1:
            return True
    return False


def _is_winning_move(move, my_stones, valid_mask, corners, edge_map):
    stones = set(my_stones)
    stones.add(move)
    if _has_bridge_or_fork(move, stones, valid_mask, corners, edge_map):
        return True
    if _has_ring_after_move(move, stones, valid_mask):
        return True
    return False


def _adjacency_count(move, stones, valid_mask):
    r, c = move
    cnt = 0
    for nb in _neighbors(r, c, valid_mask):
        if nb in stones:
            cnt += 1
    return cnt


def _group_sizes_touching(move, stones, valid_mask):
    seen = set()
    sizes = []
    r, c = move
    for nb in _neighbors(r, c, valid_mask):
        if nb in stones and nb not in seen:
            q = deque([nb])
            comp = {nb}
            seen.add(nb)
            while q:
                v = q.popleft()
                vr, vc = v
                for x in _neighbors(vr, vc, valid_mask):
                    if x in stones and x not in comp:
                        comp.add(x)
                        seen.add(x)
                        q.append(x)
            sizes.append(len(comp))
    sizes.sort(reverse=True)
    return sizes


def _distance_to_center(move):
    r, c = move
    # For a size-15 Havannah board in this embedding, (7,7) is central.
    return abs(r - 7) + abs(c - 7)


def _goal_features(move, valid_mask, corners, edge_map):
    score = 0.0
    if move in corners:
        score += 5.0
    if move in edge_map:
        score += 2.0 * len(edge_map[move])

    # proximity to corners
    mr, mc = move
    dmin = min(abs(mr - r) + abs(mc - c) for r, c in corners)
    score += max(0.0, 4.0 - 0.4 * dmin)
    return score


def _local_opp_pressure(move, opp_stones, valid_mask):
    r, c = move
    score = 0.0
    for nb in _neighbors(r, c, valid_mask):
        if nb in opp_stones:
            score += 1.5
            nbr, nbc = nb
            for nb2 in _neighbors(nbr, nbc, valid_mask):
                if nb2 in opp_stones and nb2 != move:
                    score += 0.3
    return score


def _legal_moves(me, opp, valid_mask):
    occ = _occupied_set(me, opp)
    moves = []
    for r in range(len(valid_mask)):
        for c in range(len(valid_mask[0])):
            if bool(valid_mask[r][c]) and (r, c) not in occ:
                moves.append((r, c))
    return moves


def policy(me, opp, valid_mask):
    me = [tuple(x) for x in me]
    opp = [tuple(x) for x in opp]
    my_stones = set(me)
    opp_stones = set(opp)

    legal = _legal_moves(me, opp, valid_mask)
    if not legal:
        # Should never happen in a valid game state, but remain total.
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask[0])):
                if bool(valid_mask[r][c]):
                    return (r, c)
        return (0, 0)

    corners, edge_map = _compute_corners_edges(valid_mask)

    # Opening
    if not me and not opp:
        if (7, 7) in legal and bool(valid_mask[7][7]):
            return (7, 7)

    # 1) Immediate win
    for mv in legal:
        if _is_winning_move(mv, my_stones, valid_mask, corners, edge_map):
            return mv

    # 2) Immediate block
    for mv in legal:
        if _is_winning_move(mv, opp_stones, valid_mask, corners, edge_map):
            return mv

    # 3) Heuristic evaluation
    best_mv = legal[0]
    best_sc = -10**18

    occupied = my_stones | opp_stones
    has_any_neighbors = any(_adjacency_count(mv, occupied, valid_mask) > 0 for mv in legal)

    for mv in legal:
        sc = 0.0

        dcent = _distance_to_center(mv)
        sc += 8.0 - 0.6 * dcent

        my_adj = _adjacency_count(mv, my_stones, valid_mask)
        opp_adj = _adjacency_count(mv, opp_stones, valid_mask)
        sc += 3.5 * my_adj + 1.2 * opp_adj

        gs = _group_sizes_touching(mv, my_stones, valid_mask)
        if gs:
            sc += 1.8 * gs[0]
            if len(gs) >= 2:
                sc += 2.2 * gs[1] + 4.0  # reward merging groups

        sc += _goal_features(mv, valid_mask, corners, edge_map)
        sc += _local_opp_pressure(mv, opp_stones, valid_mask)

        # Prefer relevance: if any adjacent move exists, penalize isolated moves
        if has_any_neighbors and _adjacency_count(mv, occupied, valid_mask) == 0:
            sc -= 6.0

        # Slight preference for flexibility (empty neighborhood)
        empty_nbs = 0
        r, c = mv
        for nb in _neighbors(r, c, valid_mask):
            if nb not in occupied:
                empty_nbs += 1
        sc += 0.2 * empty_nbs

        # Tiny deterministic tie-break
        sc += 1e-4 * (7 - abs(mv[0] - 7)) + 1e-5 * (7 - abs(mv[1] - 7))

        if sc > best_sc:
            best_sc = sc
            best_mv = mv

    return best_mv
