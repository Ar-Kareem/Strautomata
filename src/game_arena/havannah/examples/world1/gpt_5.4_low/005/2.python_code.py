
from __future__ import annotations

from collections import deque, defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np

# Hex-neighbor deltas matching the problem statement's board geometry.
# For cell (r, c), neighbors are:
#   (r-1,c), (r+1,c), (r-1,c-1), (r,c-1), (r,c+1), (r-1,c+1)
NEIGHBORS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]

# Circular order for local shape scoring
RING_ORDER = [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]

_CACHE = {}


class BoardInfo:
    def __init__(self, valid_mask):
        self.valid_mask = np.asarray(valid_mask, dtype=bool)
        self.n = self.valid_mask.shape[0]

        self.cells: List[Tuple[int, int]] = []
        self.cell_set: Set[Tuple[int, int]] = set()
        for r in range(self.n):
            for c in range(self.n):
                if self.valid_mask[r, c]:
                    self.cells.append((r, c))
                    self.cell_set.add((r, c))

        self.neigh: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self.degree: Dict[Tuple[int, int], int] = {}

        for cell in self.cells:
            r, c = cell
            ns = []
            for dr, dc in NEIGHBORS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.n and 0 <= nc < self.n and self.valid_mask[nr, nc]:
                    ns.append((nr, nc))
            self.neigh[cell] = ns
            self.degree[cell] = len(ns)

        self.boundary = {cell for cell in self.cells if self.degree[cell] < 6}
        self.boundary_neigh = {
            cell: [nb for nb in self.neigh[cell] if nb in self.boundary]
            for cell in self.boundary
        }

        # On a Havannah hex board represented this way, corners have degree 3.
        self.corners = [cell for cell in self.boundary if self.degree[cell] == 3]

        # Fallback if representation is unusual
        if len(self.corners) != 6:
            self.corners = self._find_corners_fallback()

        self.corner_id = {cell: i for i, cell in enumerate(self.corners)}

        self.boundary_cycle = self._build_boundary_cycle()
        self.edge_id = self._build_edge_ids()

        coords = np.array(self.cells, dtype=float)
        self.center = coords.mean(axis=0) if len(coords) else np.array([self.n / 2.0, self.n / 2.0])

    def _find_corners_fallback(self) -> List[Tuple[int, int]]:
        # Geometric fallback: select six extreme boundary points.
        b = list(self.boundary)
        if not b:
            return []
        scored = []
        for cell in b:
            r, c = cell
            scored.append((r, cell))
            scored.append((c, cell))
            scored.append((r + c, cell))
            scored.append((r - c, cell))
        # pick unique extrema across multiple directions
        candidates = set()
        rs = [r for r, c in b]
        cs = [c for r, c in b]
        sums = [r + c for r, c in b]
        diffs = [r - c for r, c in b]
        vals = [
            min(rs), max(rs),
            min(cs), max(cs),
            min(sums), max(sums),
            min(diffs), max(diffs),
        ]
        for cell in b:
            r, c = cell
            if r in vals or c in vals or (r + c) in vals or (r - c) in vals:
                candidates.add(cell)
        # Prefer boundary cells with smallest degree.
        cand = sorted(candidates, key=lambda x: (self.degree.get(x, 99), x))
        out = []
        used = set()
        for cell in cand:
            if cell not in used:
                out.append(cell)
                used.add(cell)
            if len(out) == 6:
                break
        if len(out) < 6:
            for cell in sorted(b, key=lambda x: (self.degree.get(x, 99), x)):
                if cell not in used:
                    out.append(cell)
                    used.add(cell)
                if len(out) == 6:
                    break
        return out[:6]

    def _build_boundary_cycle(self) -> List[Tuple[int, int]]:
        if not self.boundary:
            return []

        # Boundary should form a cycle. Walk it.
        start = min(self.boundary)
        bneigh = self.boundary_neigh

        if not bneigh[start]:
            return [start]

        # Pick a deterministic next boundary cell.
        nxt = min(bneigh[start])
        cycle = [start]
        prev = None
        cur = start

        for _ in range(len(self.boundary) + 5):
            cycle.append(nxt)
            prev, cur = cur, nxt
            candidates = bneigh[cur]
            if not candidates:
                break
            if len(candidates) == 1:
                nxt = candidates[0]
            else:
                # Continue along the cycle, not backtracking if possible.
                if candidates[0] == prev:
                    nxt = candidates[1]
                elif candidates[1] == prev:
                    nxt = candidates[0]
                else:
                    nxt = min(candidates)
            if nxt == start:
                break

        if cycle and cycle[-1] == start:
            cycle.pop()
        # If this did not capture everything, use all boundary cells in a stable order.
        if len(set(cycle)) < len(self.boundary):
            cycle = sorted(self.boundary)
        return cycle

    def _build_edge_ids(self) -> Dict[Tuple[int, int], int]:
        edge_id = {}
        if len(self.corners) != 6 or not self.boundary_cycle:
            return edge_id

        cycle = self.boundary_cycle
        m = len(cycle)
        corner_pos = []
        corner_set = set(self.corners)
        for i, cell in enumerate(cycle):
            if cell in corner_set:
                corner_pos.append((i, cell))

        # If traversal order missed/reordered corners, repair with a scan
        if len(corner_pos) != 6:
            cycle = sorted(self.boundary)
            m = len(cycle)
            corner_pos = [(i, cell) for i, cell in enumerate(cycle) if cell in corner_set]
            if len(corner_pos) != 6:
                return edge_id

        corner_positions = [i for i, _ in corner_pos]
        for k in range(6):
            a = corner_positions[k]
            b = corner_positions[(k + 1) % 6]
            idx = (a + 1) % m
            while idx != b:
                cell = cycle[idx]
                if cell not in corner_set:
                    edge_id[cell] = k
                idx = (idx + 1) % m
        return edge_id


def get_board_info(valid_mask) -> BoardInfo:
    arr = np.asarray(valid_mask, dtype=bool)
    key = (arr.shape, arr.tobytes())
    info = _CACHE.get(key)
    if info is None:
        info = BoardInfo(arr)
        _CACHE[key] = info
    return info


def connected_components(stones: Set[Tuple[int, int]], info: BoardInfo):
    comps = []
    label = {}
    cid = 0
    for s in stones:
        if s in label:
            continue
        q = [s]
        label[s] = cid
        comp = []
        while q:
            u = q.pop()
            comp.append(u)
            for v in info.neigh[u]:
                if v in stones and v not in label:
                    label[v] = cid
                    q.append(v)
        comps.append(comp)
        cid += 1
    return comps, label


def win_by_bridge_or_fork(stones: Set[Tuple[int, int]], info: BoardInfo) -> bool:
    comps, _ = connected_components(stones, info)
    corner_id = info.corner_id
    edge_id = info.edge_id

    for comp in comps:
        corners = set()
        edges = set()
        for cell in comp:
            if cell in corner_id:
                corners.add(corner_id[cell])
            eid = edge_id.get(cell)
            if eid is not None:
                edges.add(eid)
        if len(corners) >= 2:
            return True
        if len(edges) >= 3:
            return True
    return False


def win_by_ring(stones: Set[Tuple[int, int]], info: BoardInfo) -> bool:
    # Ring exists iff some non-stone region is disconnected from the board boundary.
    nonstones = info.cell_set - stones
    if not nonstones:
        return False

    start_cells = [cell for cell in info.boundary if cell in nonstones]
    seen = set(start_cells)
    dq = deque(start_cells)

    while dq:
        u = dq.popleft()
        for v in info.neigh[u]:
            if v in nonstones and v not in seen:
                seen.add(v)
                dq.append(v)

    # Any non-stone cell unreachable from boundary is enclosed.
    for cell in nonstones:
        if cell not in seen:
            return True
    return False


def is_win(stones: Set[Tuple[int, int]], info: BoardInfo) -> bool:
    return win_by_bridge_or_fork(stones, info) or win_by_ring(stones, info)


def immediate_winning_moves(stones: Set[Tuple[int, int]], occupied: Set[Tuple[int, int]], info: BoardInfo):
    wins = []
    for cell in info.cells:
        if cell in occupied:
            continue
        stones.add(cell)
        if is_win(stones, info):
            wins.append(cell)
        stones.remove(cell)
    return wins


def component_touch_info(stones: Set[Tuple[int, int]], info: BoardInfo):
    comps, label = connected_components(stones, info)
    comp_corners = []
    comp_edges = []
    for comp in comps:
        corners = set()
        edges = set()
        for cell in comp:
            if cell in info.corner_id:
                corners.add(info.corner_id[cell])
            eid = info.edge_id.get(cell)
            if eid is not None:
                edges.add(eid)
        comp_corners.append(corners)
        comp_edges.append(edges)
    return comps, label, comp_corners, comp_edges


def circular_adjacent_pair_count(cell: Tuple[int, int], stones: Set[Tuple[int, int]], info: BoardInfo) -> int:
    r, c = cell
    occ = []
    for dr, dc in RING_ORDER:
        nb = (r + dr, c + dc)
        occ.append(nb in stones and nb in info.cell_set)
    cnt = 0
    for i in range(6):
        if occ[i] and occ[(i + 1) % 6]:
            cnt += 1
    return cnt


def move_score(
    move: Tuple[int, int],
    my_stones: Set[Tuple[int, int]],
    opp_stones: Set[Tuple[int, int]],
    occupied: Set[Tuple[int, int]],
    info: BoardInfo,
    my_label,
    my_comp_corners,
    my_comp_edges,
):
    r, c = move
    score = 0.0

    # Centrality
    dr = r - info.center[0]
    dc = c - info.center[1]
    score -= 0.45 * (dr * dr + dc * dc)

    # Neighbor structure
    my_neighbor_cells = [nb for nb in info.neigh[move] if nb in my_stones]
    opp_neighbor_cells = [nb for nb in info.neigh[move] if nb in opp_stones]
    my_neighbor_comps = {my_label[nb] for nb in my_neighbor_cells}

    score += 9.0 * len(my_neighbor_cells)
    score += 26.0 * len(my_neighbor_comps)
    if len(my_neighbor_comps) >= 2:
        score += 30.0

    score += 5.5 * len(opp_neighbor_cells)

    # Touch corners / edges after merge
    merged_corners = set()
    merged_edges = set()
    for cid in my_neighbor_comps:
        merged_corners |= my_comp_corners[cid]
        merged_edges |= my_comp_edges[cid]

    if move in info.corner_id:
        merged_corners.add(info.corner_id[move])
        score += 12.0
    eid = info.edge_id.get(move)
    if eid is not None:
        merged_edges.add(eid)
        score += 4.0

    score += 18.0 * len(merged_corners)
    score += 10.0 * len(merged_edges)

    # Local ring / shape potential
    pair_cnt = circular_adjacent_pair_count(move, my_stones, info)
    score += 8.0 * pair_cnt

    # Slight preference for keeping contact with action
    if not my_neighbor_cells and not opp_neighbor_cells:
        score -= 8.0

    return score


def choose_centerish_legal(legal_moves: List[Tuple[int, int]], info: BoardInfo) -> Tuple[int, int]:
    best = None
    best_d = None
    for cell in legal_moves:
        r, c = cell
        d = (r - info.center[0]) ** 2 + (c - info.center[1]) ** 2
        if best is None or d < best_d or (d == best_d and cell < best):
            best = cell
            best_d = d
    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    info = get_board_info(valid_mask)

    my_stones = set(map(tuple, me))
    opp_stones = set(map(tuple, opp))
    occupied = my_stones | opp_stones

    legal_moves = [cell for cell in info.cells if cell not in occupied]
    if not legal_moves:
        # Should not happen in legal game states, but always return something legal if possible.
        for cell in info.cells:
            return cell
        return (0, 0)

    # Opening: take center-ish move.
    if not occupied:
        return choose_centerish_legal(legal_moves, info)

    # 1) Immediate win
    my_wins = immediate_winning_moves(my_stones, occupied, info)
    if my_wins:
        # If several winning moves exist, prefer the most central / stable one.
        return choose_centerish_legal(my_wins, info)

    # 2) Immediate block
    opp_wins = immediate_winning_moves(opp_stones, occupied, info)
    if opp_wins:
        blockers = [m for m in opp_wins if m in legal_moves]
        if blockers:
            return choose_centerish_legal(blockers, info)

    # Precompute my components for heuristic
    _, my_label, my_comp_corners, my_comp_edges = component_touch_info(my_stones, info)

    # 3) Heuristic ranking
    scored = []
    for mv in legal_moves:
        sc = move_score(mv, my_stones, opp_stones, occupied, info, my_label, my_comp_corners, my_comp_edges)
        scored.append((sc, mv))
    scored.sort(reverse=True)

    # 4) Avoid moves that give opponent an immediate win next turn
    top_candidates = [mv for _, mv in scored[: min(12, len(scored))]]
    safe_best = None
    safe_best_score = None

    for mv in top_candidates:
        my_stones.add(mv)
        occ2 = occupied | {mv}
        opp_reply_wins = immediate_winning_moves(opp_stones, occ2, info)
        my_stones.remove(mv)

        # Penalize by number of opponent winning replies
        base_score = next(sc for sc, m in scored if m == mv)
        adj_score = base_score - 120.0 * len(opp_reply_wins)

        if safe_best is None or adj_score > safe_best_score or (adj_score == safe_best_score and mv < safe_best):
            safe_best = mv
            safe_best_score = adj_score

    if safe_best is not None:
        return safe_best

    # Final fallback: best heuristic legal move
    return scored[0][1] if scored else legal_moves[0]
