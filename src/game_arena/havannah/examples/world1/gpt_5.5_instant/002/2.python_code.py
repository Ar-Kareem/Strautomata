
from collections import deque, defaultdict
import math
import random

N = 15

# Hex neighbors for the coordinate convention described in the prompt.
DIRS = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]


def _valid_cells(valid_mask):
    cells = []
    n = len(valid_mask)
    for r in range(n):
        row = valid_mask[r]
        for c in range(len(row)):
            if bool(row[c]):
                cells.append((r, c))
    return cells


def _neighbors(cell, valid_set):
    r, c = cell
    for dr, dc in DIRS:
        nb = (r + dr, c + dc)
        if nb in valid_set:
            yield nb


def _geometry(valid_set):
    """Return corners set, edge-id map for non-corners, and center."""
    rows = defaultdict(list)
    cols = defaultdict(list)
    for r, c in valid_set:
        rows[r].append(c)
        cols[c].append(r)

    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    corners = set()
    # The six extreme boundary intersections for this axial-like embedding.
    candidates = [
        (min_r, min(rows[min_r])),
        (min_r, max(rows[min_r])),
        (max_r, min(rows[max_r])),
        (max_r, max(rows[max_r])),
        (min(cols[min_c]), min_c),
        (max(cols[max_c]), max_c),
    ]
    for x in candidates:
        if x in valid_set:
            corners.add(x)

    edge_map = defaultdict(set)
    for r, c in valid_set:
        if (r, c) in corners:
            continue
        if r == min_r:
            edge_map[(r, c)].add(0)
        if c == max(rows[r]):
            edge_map[(r, c)].add(1)
        if c == max_c:
            edge_map[(r, c)].add(2)
        if r == max_r:
            edge_map[(r, c)].add(3)
        if c == min(rows[r]):
            edge_map[(r, c)].add(4)
        if c == min_c:
            edge_map[(r, c)].add(5)

    cr = sum(r for r, c in valid_set) / float(len(valid_set))
    cc = sum(c for r, c in valid_set) / float(len(valid_set))
    return corners, edge_map, (cr, cc)


def _components(stones, valid_set, corners, edge_map):
    stones = set(stones)
    comps = []
    seen = set()
    for s in stones:
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        nodes = []
        corner_touch = set()
        edge_touch = set()
        while q:
            x = q.popleft()
            nodes.append(x)
            if x in corners:
                corner_touch.add(x)
            if x in edge_map:
                edge_touch.update(edge_map[x])
            for nb in _neighbors(x, valid_set):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        comps.append((set(nodes), corner_touch, edge_touch))
    return comps


def _would_make_ring(move, stones, valid_set):
    """Cycle test: if two neighboring friendly stones are already connected without the new move."""
    stones = set(stones)
    neigh = [nb for nb in _neighbors(move, valid_set) if nb in stones]
    if len(neigh) < 2:
        return False

    blocked = move
    for i in range(len(neigh)):
        start = neigh[i]
        targets = set(neigh[i + 1:])
        if not targets:
            break
        q = deque([start])
        seen = {start, blocked}
        while q:
            x = q.popleft()
            if x in targets:
                return True
            for nb in _neighbors(x, valid_set):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
    return False


def _is_win_after(move, stones, valid_set, corners, edge_map):
    stones2 = set(stones)
    stones2.add(move)

    # Component containing move.
    q = deque([move])
    seen = {move}
    corner_touch = set()
    edge_touch = set()
    while q:
        x = q.popleft()
        if x in corners:
            corner_touch.add(x)
        if x in edge_map:
            edge_touch.update(edge_map[x])
        for nb in _neighbors(x, valid_set):
            if nb in stones2 and nb not in seen:
                seen.add(nb)
                q.append(nb)

    if len(corner_touch) >= 2:
        return True
    if len(edge_touch) >= 3:
        return True
    if _would_make_ring(move, stones, valid_set):
        return True
    return False


def _cell_score(move, me_set, opp_set, valid_set, corners, edge_map, center):
    r, c = move
    cr, cc = center
    score = 0.0

    # Center influence is generally strong early.
    dist = abs(r - cr) + abs(c - cc) + abs((r - c) - (cr - cc)) * 0.35
    score += 14.0 - 0.85 * dist

    my_adj = 0
    op_adj = 0
    my_second = 0
    op_second = 0
    empty_adj = 0
    my_comp_ids = set()
    op_comp_ids = set()

    # Local adjacency/support.
    for nb in _neighbors(move, valid_set):
        if nb in me_set:
            my_adj += 1
        elif nb in opp_set:
            op_adj += 1
        else:
            empty_adj += 1
            for nb2 in _neighbors(nb, valid_set):
                if nb2 in me_set:
                    my_second += 1
                elif nb2 in opp_set:
                    op_second += 1

    score += 9.0 * my_adj + 5.0 * op_adj + 0.8 * empty_adj
    score += 0.9 * my_second + 0.55 * op_second

    if my_adj >= 2:
        score += 12.0 + 4.0 * (my_adj - 2)
    if op_adj >= 2:
        score += 9.0 + 3.0 * (op_adj - 2)

    # Boundary goals: prefer connecting to useful edges/corners, but not too much too early.
    if move in corners:
        score += 5.5
    if move in edge_map:
        score += 2.4 * len(edge_map[move])

    # Light liberties / avoid cramped dead placements.
    blocked = my_adj + op_adj
    if blocked >= 5:
        score -= 4.0
    elif empty_adj >= 3:
        score += 2.0

    # Small deterministic jitter for tie-breaking.
    score += ((r * 31 + c * 17) % 13) * 0.01
    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    valid_set = set(_valid_cells(valid_mask))
    occupied = set(me) | set(opp)
    legal = [cell for cell in valid_set if cell not in occupied]

    # Absolute safety: always return a legal move if any exists.
    if not legal:
        # Should never happen in normal play. Return any playable cell.
        return next(iter(valid_set)) if valid_set else (0, 0)

    corners, edge_map, center = _geometry(valid_set)
    me_set = set(me)
    opp_set = set(opp)

    # Opening: take center-ish point.
    if not me and not opp:
        return min(legal, key=lambda x: (x[0] - center[0]) ** 2 + (x[1] - center[1]) ** 2)

    # Candidate reduction: all moves near stones plus boundary tactical cells.
    near = set()
    for s in occupied:
        for nb in _neighbors(s, valid_set):
            if nb not in occupied:
                near.add(nb)
        for nb in _neighbors(s, valid_set):
            for nb2 in _neighbors(nb, valid_set):
                if nb2 not in occupied:
                    near.add(nb2)
    candidates = list(near) if near else legal
    if len(candidates) > 90:
        candidates.sort(key=lambda m: _cell_score(m, me_set, opp_set, valid_set, corners, edge_map, center), reverse=True)
        candidates = candidates[:90]

    # Immediate win.
    for mv in candidates:
        if _is_win_after(mv, me_set, valid_set, corners, edge_map):
            return mv

    # Immediate block.
    opp_wins = []
    for mv in candidates:
        if _is_win_after(mv, opp_set, valid_set, corners, edge_map):
            opp_wins.append(mv)
    if opp_wins:
        # If multiple blocks, choose the one also best for us.
        return max(opp_wins, key=lambda m: _cell_score(m, me_set, opp_set, valid_set, corners, edge_map, center))

    # Score strategic candidates.
    best = None
    best_score = -10**9

    # Precompute component labels and goal touches for better connection scoring.
    my_comps = _components(me_set, valid_set, corners, edge_map)
    op_comps = _components(opp_set, valid_set, corners, edge_map)

    my_label = {}
    op_label = {}
    for idx, (nodes, cor, edg) in enumerate(my_comps):
        for x in nodes:
            my_label[x] = idx
    for idx, (nodes, cor, edg) in enumerate(op_comps):
        for x in nodes:
            op_label[x] = idx

    for mv in candidates:
        score = _cell_score(mv, me_set, opp_set, valid_set, corners, edge_map, center)

        adj_my_comps = set()
        adj_op_comps = set()
        for nb in _neighbors(mv, valid_set):
            if nb in my_label:
                adj_my_comps.add(my_label[nb])
            if nb in op_label:
                adj_op_comps.add(op_label[nb])

        # Reward merging friendly components with diverse goals.
        if adj_my_comps:
            cor = set()
            edg = set()
            size_sum = 0
            for i in adj_my_comps:
                nodes, cset, eset = my_comps[i]
                cor.update(cset)
                edg.update(eset)
                size_sum += len(nodes)
            if mv in corners:
                cor.add(mv)
            if mv in edge_map:
                edg.update(edge_map[mv])
            score += 2.2 * min(size_sum, 10)
            score += 15.0 * max(0, len(cor) - 1)
            score += 8.0 * len(cor)
            score += 12.0 * max(0, len(edg) - 2)
            score += 4.5 * len(edg)
            if len(adj_my_comps) >= 2:
                score += 16.0 * (len(adj_my_comps) - 1)

        # Reward blocking opponent groups close to bridge/fork potential.
        if adj_op_comps:
            cor = set()
            edg = set()
            osize = 0
            for i in adj_op_comps:
                nodes, cset, eset = op_comps[i]
                cor.update(cset)
                edg.update(eset)
                osize += len(nodes)
            score += 1.6 * min(osize, 12)
            score += 10.0 * max(0, len(cor) - 1)
            score += 7.5 * max(0, len(edg) - 2)
            if len(adj_op_comps) >= 2:
                score += 11.0 * (len(adj_op_comps) - 1)

        # Ring threat creation: connecting two stones that were not adjacent is valuable.
        my_adj = [nb for nb in _neighbors(mv, valid_set) if nb in me_set]
        if len(my_adj) >= 2:
            score += 10.0
        op_adj = [nb for nb in _neighbors(mv, valid_set) if nb in opp_set]
        if len(op_adj) >= 2:
            score += 7.0

        if score > best_score:
            best_score = score
            best = mv

    if best is not None and best in valid_set and best not in occupied:
        return best

    # Final fallback: guaranteed legal.
    return legal[0]
