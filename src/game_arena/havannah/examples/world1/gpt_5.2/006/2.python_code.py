
# Havannah policy for 15x15 (geometry derived from valid_mask)
# API:
#   def policy(me: list[tuple[int,int]], opp: list[tuple[int,int]], valid_mask) -> tuple[int,int]

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional

import numpy as np


# ------------------------- Hex-neighborhood (per prompt) -------------------------
# For (r,c): neighbors are (r-1,c),(r+1,c),(r,c-1),(r-1,c-1),(r,c+1),(r-1,c+1)
_NEI6 = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]


# ------------------------- DSU (Union-Find) -------------------------
class DSU:
    __slots__ = ("p", "sz")

    def __init__(self, n: int):
        self.p = list(range(n))
        self.sz = [1] * n

    def find(self, a: int) -> int:
        p = self.p
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def union(self, a: int, b: int) -> int:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        self.sz[ra] += self.sz[rb]
        return ra


# ------------------------- Geometry Cache -------------------------
@dataclass
class Geo:
    N: int
    valid: np.ndarray                       # bool NxN
    valid_list: List[int]                   # flat indices
    valid_set: Set[int]                     # flat indices
    adj: List[List[int]]                    # length N*N, neighbors (flat) that are valid
    boundary_list: List[int]                # valid cells with degree < 6
    corners: List[int]                      # 6 corners (flat)
    edges: List[Set[int]]                   # 6 edge cell sets (excluding corners)
    edge_bit: List[int]                     # per flat idx, 1<<edge_id or 0
    corner_bit: List[int]                   # per flat idx, 1<<corner_id or 0
    center_idx: int                         # chosen central valid cell
    dist_center: List[int]                  # per flat idx, BFS distance to center (large for invalid)
    _visit_stamp: List[int]                 # per flat idx for flood-fill
    _stamp: int                             # stamp counter


_GEO: Optional[Geo] = None
_GEO_KEY: Optional[Tuple[int, int, int]] = None  # (N, sum(valid), hash-ish)


def _flat(N: int, r: int, c: int) -> int:
    return r * N + c


def _unflat(N: int, idx: int) -> Tuple[int, int]:
    return divmod(idx, N)


def _init_geo(valid_mask) -> Geo:
    valid = np.asarray(valid_mask, dtype=bool)
    N = int(valid.shape[0])
    assert valid.shape == (N, N)

    # Build valid list/set
    valid_list = [i for i in range(N * N) if valid[i // N, i % N]]
    valid_set = set(valid_list)

    # Adjacency on the hex grid restricted to valid_mask
    adj: List[List[int]] = [[] for _ in range(N * N)]
    for idx in valid_list:
        r, c = divmod(idx, N)
        neigh = []
        for dr, dc in _NEI6:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N and valid[rr, cc]:
                neigh.append(_flat(N, rr, cc))
        adj[idx] = neigh

    # Boundary cells: degree < 6
    boundary_list = [idx for idx in valid_list if len(adj[idx]) < 6]
    boundary_set = set(boundary_list)

    # Corners: on a proper Havannah board, corners have degree 3
    corners = [idx for idx in boundary_list if len(adj[idx]) == 3]

    # Fallback corner detection if needed (rare): pick extremes in 6 directions
    if len(corners) != 6:
        coords = [(idx, *divmod(idx, N)) for idx in boundary_list]
        # Directions in (r,c): min/max of r, c, (r+c), (r-c)
        cand = set()
        if coords:
            cand.add(min(coords, key=lambda x: x[1])[0])  # min r
            cand.add(max(coords, key=lambda x: x[1])[0])  # max r
            cand.add(min(coords, key=lambda x: x[2])[0])  # min c
            cand.add(max(coords, key=lambda x: x[2])[0])  # max c
            cand.add(min(coords, key=lambda x: x[1] + x[2])[0])  # min r+c
            cand.add(max(coords, key=lambda x: x[1] + x[2])[0])  # max r+c
            cand.add(min(coords, key=lambda x: x[1] - x[2])[0])  # min r-c
            cand.add(max(coords, key=lambda x: x[1] - x[2])[0])  # max r-c
        corners = list(cand)
        # If still not 6, prune/expand by greedy farthest (graph distance on valid graph)
        # Compute BFS distances from each candidate to others (small graph).
        if len(corners) > 6:
            # Keep 6 that are spread out: greedy by pairwise graph distances
            # BFS precompute from each corner candidate
            distmat = {}
            for s in corners:
                q = deque([s])
                dist = {s: 0}
                while q:
                    u = q.popleft()
                    for v in adj[u]:
                        if v in valid_set and v not in dist:
                            dist[v] = dist[u] + 1
                            q.append(v)
                distmat[s] = dist

            chosen = [corners[0]]
            while len(chosen) < 6 and len(chosen) < len(corners):
                best = None
                bestd = -1
                for x in corners:
                    if x in chosen:
                        continue
                    mind = min(distmat[c].get(x, -10**9) for c in chosen)
                    if mind > bestd:
                        bestd = mind
                        best = x
                if best is None:
                    break
                chosen.append(best)
            corners = chosen
        elif len(corners) < 6:
            # Add more boundary extremes if missing
            extra = [idx for idx in boundary_list if idx not in corners]
            corners = corners + extra[: max(0, 6 - len(corners))]
        corners = corners[:6]

    corner_set = set(corners)

    # Boundary neighbors restricted to boundary
    b_adj: Dict[int, List[int]] = {}
    for idx in boundary_list:
        b_adj[idx] = [nb for nb in adj[idx] if nb in boundary_set]

    # Extract the 6 edge segments by walking boundary between adjacent corners
    edges: List[Set[int]] = []
    seen_pairs = set()
    for c in corners:
        for nb in b_adj.get(c, []):
            prev = c
            cur = nb
            path = []
            # Walk until next corner
            steps = 0
            while cur not in corner_set and steps < 10000:
                path.append(cur)
                nbs = b_adj.get(cur, [])
                # boundary path should have degree 2; choose the one not equal prev
                nxt = None
                for x in nbs:
                    if x != prev:
                        nxt = x
                        break
                if nxt is None:
                    break
                prev, cur = cur, nxt
                steps += 1
            if cur in corner_set and cur != c:
                a, b = (c, cur) if c < cur else (cur, c)
                if (a, b) in seen_pairs:
                    continue
                seen_pairs.add((a, b))
                edges.append(set(path))

    # If extraction did not yield 6, do a robust fallback classification into 6 boundary sectors.
    if len(edges) != 6:
        # Choose a center and split boundary (excluding corners) into 6 angular bins.
        # This is only for heuristics/win-detection approximation if mask is weird.
        # (Typical arena mask should succeed above.)
        # Center chosen below; for now compute rough center coords:
        vr = [idx // N for idx in valid_list]
        vc = [idx % N for idx in valid_list]
        cr = int(round(sum(vr) / len(vr))) if vr else N // 2
        cc = int(round(sum(vc) / len(vc))) if vc else N // 2
        # choose nearest valid to that
        best = None
        bestd = 10**9
        for idx in valid_list:
            r, c = divmod(idx, N)
            d = abs(r - cr) + abs(c - cc)
            if d < bestd:
                bestd = d
                best = idx
        center_idx = best if best is not None else (valid_list[0] if valid_list else 0)
        cr, cc = divmod(center_idx, N)

        import math
        bins = [set() for _ in range(6)]
        for idx in boundary_list:
            if idx in corner_set:
                continue
            r, c = divmod(idx, N)
            ang = math.atan2(r - cr, c - cc)  # -pi..pi
            k = int(((ang + math.pi) / (2 * math.pi)) * 6) % 6
            bins[k].add(idx)
        edges = bins

    # Build edge_bit and corner_bit maps
    edge_bit = [0] * (N * N)
    for ei, es in enumerate(edges[:6]):
        bit = 1 << ei
        for idx in es:
            edge_bit[idx] = bit

    corner_bit = [0] * (N * N)
    for ci, idx in enumerate(corners[:6]):
        corner_bit[idx] = 1 << ci

    # Choose a central valid cell (closest to (N//2,N//2))
    target_r, target_c = N // 2, N // 2
    center_idx = None
    bestd = 10**9
    for idx in valid_list:
        r, c = divmod(idx, N)
        d = abs(r - target_r) + abs(c - target_c)
        if d < bestd:
            bestd = d
            center_idx = idx
    if center_idx is None:
        center_idx = 0

    # BFS distances to center on the valid graph
    dist_center = [10**9] * (N * N)
    dq = deque([center_idx])
    dist_center[center_idx] = 0
    while dq:
        u = dq.popleft()
        du = dist_center[u]
        for v in adj[u]:
            if v in valid_set and dist_center[v] == 10**9:
                dist_center[v] = du + 1
                dq.append(v)

    geo = Geo(
        N=N,
        valid=valid,
        valid_list=valid_list,
        valid_set=valid_set,
        adj=adj,
        boundary_list=boundary_list,
        corners=corners[:6],
        edges=edges[:6],
        edge_bit=edge_bit,
        corner_bit=corner_bit,
        center_idx=center_idx,
        dist_center=dist_center,
        _visit_stamp=[0] * (N * N),
        _stamp=1,
    )
    return geo


def _get_geo(valid_mask) -> Geo:
    global _GEO, _GEO_KEY
    v = np.asarray(valid_mask, dtype=bool)
    N = int(v.shape[0])
    key = (N, int(v.sum()), hash(v.tobytes()) & 0xFFFFFFFF)
    if _GEO is None or _GEO_KEY != key:
        _GEO = _init_geo(v)
        _GEO_KEY = key
    return _GEO


# ------------------------- Helpers: components and win tests -------------------------
@dataclass
class CompInfo:
    dsu: DSU
    idx_to_node: Dict[int, int]      # flat idx -> DSU node id
    root_edge: Dict[int, int]        # root -> edges bitmask
    root_corner: Dict[int, int]      # root -> corners bitmask
    root_size: Dict[int, int]        # root -> size


def _build_components(stones: Set[int], geo: Geo) -> CompInfo:
    idx_to_node: Dict[int, int] = {}
    nodes = list(stones)
    for i, idx in enumerate(nodes):
        idx_to_node[idx] = i
    dsu = DSU(len(nodes))
    # union adjacent stones
    for i, idx in enumerate(nodes):
        for nb in geo.adj[idx]:
            j = idx_to_node.get(nb)
            if j is not None:
                dsu.union(i, j)

    # collect root info
    root_edge: Dict[int, int] = {}
    root_corner: Dict[int, int] = {}
    root_size: Dict[int, int] = {}
    for i, idx in enumerate(nodes):
        r = dsu.find(i)
        root_size[r] = root_size.get(r, 0) + 1
        root_edge[r] = root_edge.get(r, 0) | geo.edge_bit[idx]
        root_corner[r] = root_corner.get(r, 0) | geo.corner_bit[idx]

    return CompInfo(dsu=dsu, idx_to_node=idx_to_node,
                    root_edge=root_edge, root_corner=root_corner, root_size=root_size)


def _neighbor_counts(idx: int, my: Set[int], opp: Set[int], geo: Geo) -> Tuple[int, int]:
    mn = 0
    on = 0
    for nb in geo.adj[idx]:
        if nb in my:
            mn += 1
        elif nb in opp:
            on += 1
    return mn, on


def _merge_masks_for_move(move: int, stones: Set[int], comp: CompInfo, geo: Geo) -> Tuple[int, int, int, int]:
    """
    Returns (edge_mask, corner_mask, merged_size, distinct_neighbor_components).
    """
    seen_roots = set()
    edge_mask = geo.edge_bit[move]
    corner_mask = geo.corner_bit[move]
    merged_size = 1
    for nb in geo.adj[move]:
        node = comp.idx_to_node.get(nb)
        if node is None:
            continue
        root = comp.dsu.find(node)
        if root in seen_roots:
            continue
        seen_roots.add(root)
        edge_mask |= comp.root_edge.get(root, 0)
        corner_mask |= comp.root_corner.get(root, 0)
        merged_size += comp.root_size.get(root, 0)
    return edge_mask, corner_mask, merged_size, len(seen_roots)


def _has_ring_after_move(stones: Set[int], move: int, geo: Geo) -> bool:
    """
    Flood-fill from boundary through all cells that are NOT occupied by the player
    (opponent stones are passable). If any non-player cell is unreachable, player has a ring.
    """
    geo._stamp += 1
    stamp = geo._stamp
    vis = geo._visit_stamp

    def blocked(i: int) -> bool:
        return i == move or i in stones

    dq = deque()
    for b in geo.boundary_list:
        if not blocked(b) and vis[b] != stamp:
            vis[b] = stamp
            dq.append(b)

    while dq:
        u = dq.popleft()
        for v in geo.adj[u]:
            if v in geo.valid_set and not blocked(v) and vis[v] != stamp:
                vis[v] = stamp
                dq.append(v)

    for idx in geo.valid_list:
        if not blocked(idx) and vis[idx] != stamp:
            return True
    return False


def _is_win_after_move(stones: Set[int], move: int, comp: CompInfo, geo: Geo) -> bool:
    # Fast bridge/fork checks using component-edge/corner union
    edge_mask, corner_mask, _msz, _k = _merge_masks_for_move(move, stones, comp, geo)
    if corner_mask.bit_count() >= 2:
        return True  # bridge
    if edge_mask.bit_count() >= 3:
        return True  # fork

    # Ring check: only plausible if move connects to at least 2 friendly neighbors
    friendly_n, _ = _neighbor_counts(move, stones, set(), geo)
    if friendly_n < 2:
        return False
    return _has_ring_after_move(stones, move, geo)


# ------------------------- Move selection -------------------------
def _frontier(stones: Set[int], occupied: Set[int], geo: Geo) -> Set[int]:
    out = set()
    for s in stones:
        for nb in geo.adj[s]:
            if nb in geo.valid_set and nb not in occupied:
                out.add(nb)
    return out


def _choose_best_by_heuristic(cands: List[int], me_set: Set[int], opp_set: Set[int],
                              comp_me: CompInfo, geo: Geo) -> int:
    # Heuristic scoring tuned for Havannah: grow strong groups and increase edge/corner reach.
    best = None
    best_score = -1e100

    for mv in cands:
        # merge information (fork/bridge potential)
        edge_mask, corner_mask, merged_size, comps = _merge_masks_for_move(mv, me_set, comp_me, geo)
        mn, on = _neighbor_counts(mv, me_set, opp_set, geo)

        # Prefer connecting separate groups
        merge_bonus = 4.0 * max(0, comps - 1)

        # Fork/bridge progress
        edge_cnt = edge_mask.bit_count()
        corner_cnt = corner_mask.bit_count()
        goal_bonus = 10.0 * edge_cnt + 12.0 * corner_cnt

        # Shape/strength
        local_bonus = 3.0 * mn + 1.2 * on

        # Size matters a bit (stability)
        size_bonus = 1.0 * (merged_size ** 0.5)

        # Centrality: important early, less later
        # (distance array is large for invalid; mv always valid)
        dcen = geo.dist_center[mv]
        center_bonus = -0.35 * dcen

        score = goal_bonus + merge_bonus + local_bonus + size_bonus + center_bonus

        # Tie-break: deterministic tiny noise from index
        score += (mv % 17) * 1e-6

        if score > best_score:
            best_score = score
            best = mv

    return best if best is not None else cands[0]


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    geo = _get_geo(valid_mask)
    N = geo.N

    me_set = {_flat(N, r, c) for (r, c) in me}
    opp_set = {_flat(N, r, c) for (r, c) in opp}
    occupied = me_set | opp_set

    # Legal moves
    legal = [idx for idx in geo.valid_list if idx not in occupied]
    if not legal:
        # Should never happen in Havannah, but must return something legal-looking.
        # Pick center if possible else (0,0).
        r, c = _unflat(N, geo.center_idx)
        return (r, c)

    # First move: play center
    if not me_set and geo.center_idx in legal:
        return _unflat(N, geo.center_idx)

    comp_me = _build_components(me_set, geo)
    comp_opp = _build_components(opp_set, geo)

    # Candidate set: frontier near either player + a few central options
    cset = set()
    if me_set:
        cset |= _frontier(me_set, occupied, geo)
    if opp_set:
        cset |= _frontier(opp_set, occupied, geo)
    if len(cset) < 30:
        # Add closest-to-center legal cells
        by_center = sorted(legal, key=lambda x: geo.dist_center[x])
        for x in by_center[: (30 - len(cset))]:
            cset.add(x)
    if not cset:
        cset = set(legal)

    cands = [x for x in cset if x in geo.valid_set and x not in occupied]
    if not cands:
        cands = legal

    # 1) Immediate winning move
    # Check a widened candidate set for tactics (frontier + a few more)
    tactical = cands
    if len(tactical) < len(legal) and len(tactical) < 60:
        # include some extra legal moves to be safe
        extra = sorted(legal, key=lambda x: geo.dist_center[x])[:60]
        tactical = list(dict.fromkeys(tactical + extra))  # unique preserving order

    for mv in tactical:
        if _is_win_after_move(me_set, mv, comp_me, geo):
            return _unflat(N, mv)

    # 2) Block opponent's immediate win (if any)
    opp_threats = []
    if opp_set:
        opp_front = _frontier(opp_set, occupied, geo)
        # If frontier empty (rare), no immediate win is possible
        for mv in opp_front:
            if _is_win_after_move(opp_set, mv, comp_opp, geo):
                opp_threats.append(mv)

    if opp_threats:
        # Block by playing on the threatened winning cell.
        # If multiple, choose the block that is best for us.
        block_moves = [mv for mv in opp_threats if mv in geo.valid_set and mv not in occupied]
        if block_moves:
            best_block = _choose_best_by_heuristic(block_moves, me_set, opp_set, comp_me, geo)
            return _unflat(N, best_block)
        # If somehow no block move is legal, fall through (will lose anyway).

    # 3) Positional move by heuristic
    best = _choose_best_by_heuristic(cands, me_set, opp_set, comp_me, geo)
    if best in geo.valid_set and best not in occupied:
        return _unflat(N, best)

    # Absolute fallback: first legal move
    return _unflat(N, legal[0])
