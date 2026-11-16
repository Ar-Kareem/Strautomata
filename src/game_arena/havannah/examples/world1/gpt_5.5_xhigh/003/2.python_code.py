
from __future__ import annotations

from collections import deque
import math

_INF = 10**6
_GEOM_CACHE = {}

try:
    (1).bit_count()

    def _popcount(x: int) -> int:
        return x.bit_count()

except AttributeError:

    def _popcount(x: int) -> int:
        return bin(x).count("1")


# Axial directions for the column-offset coordinate system described in the prompt.
# offset row = axial_r + ceil(col / 2)
_AX_DIRS = ((0, -1), (1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0))


def _off_to_ax(row: int, col: int) -> tuple[int, int]:
    return col, row - ((col + 1) // 2)


def _ax_to_off(q: int, a: int) -> tuple[int, int]:
    return a + ((q + 1) // 2), q


def _ordered_neighbor_coords(row: int, col: int) -> tuple[tuple[int, int], ...]:
    q, a = _off_to_ax(row, col)
    return tuple(_ax_to_off(q + dq, a + da) for dq, da in _AX_DIRS)


def _dims(valid_mask) -> tuple[int, int]:
    try:
        sh = valid_mask.shape
        return int(sh[0]), int(sh[1])
    except Exception:
        r = len(valid_mask)
        c = len(valid_mask[0]) if r else 0
        return r, c


class _Geom:
    def __init__(self, mask_rows, rows: int, cols: int):
        self.R = rows
        self.C = cols

        valid = [[False] * cols for _ in range(rows)]
        idx = [[-1] * cols for _ in range(rows)]
        cells = []

        for r in range(rows):
            for c in range(cols):
                if bool(mask_rows[r][c]):
                    idx[r][c] = len(cells)
                    valid[r][c] = True
                    cells.append((r, c))

        self.valid = valid
        self.idx = idx
        self.cells = cells
        self.M = len(cells)

        if self.M == 0:
            self.neigh = []
            self.ordered = []
            self.degree = []
            self.edge_mask = []
            self.edge_groups = [[] for _ in range(6)]
            self.corner_bit = []
            self.corner_indices = []
            self.center_score = []
            self.center_order = []
            self.noise = []
            self.ext_n = 0
            self.ext_boundary = []
            self.ext_neighbors = []
            self.ext_to_cell = []
            self.valid_ext = []
            return

        ordered = []
        neigh = []
        for r, c in cells:
            oi = []
            ni = []
            for nr, nc in _ordered_neighbor_coords(r, c):
                j = -1
                if 0 <= nr < rows and 0 <= nc < cols and valid[nr][nc]:
                    j = idx[nr][nc]
                    ni.append(j)
                oi.append(j)
            ordered.append(tuple(oi))
            neigh.append(tuple(ni))

        self.ordered = ordered
        self.neigh = neigh
        self.degree = [len(n) for n in neigh]

        ax = []
        qs, aa, bb = [], [], []
        for r, c in cells:
            q, a = _off_to_ax(r, c)
            b = -q - a
            ax.append((q, a, b))
            qs.append(q)
            aa.append(a)
            bb.append(b)

        qmin, qmax = min(qs), max(qs)
        amin, amax = min(aa), max(aa)
        bmin, bmax = min(bb), max(bb)

        line_masks = []
        for q, a, b in ax:
            lm = 0
            if q == qmin:
                lm |= 1 << 0
            if q == qmax:
                lm |= 1 << 1
            if a == amin:
                lm |= 1 << 2
            if a == amax:
                lm |= 1 << 3
            if b == bmin:
                lm |= 1 << 4
            if b == bmax:
                lm |= 1 << 5
            line_masks.append(lm)

        cr = sum(r for r, _ in cells) / float(self.M)
        cc = sum(c for _, c in cells) / float(self.M)

        corner_candidates = [i for i, lm in enumerate(line_masks) if _popcount(lm) >= 2]
        if len(corner_candidates) != 6:
            ranked = sorted(
                range(self.M),
                key=lambda i: (
                    self.degree[i],
                    -((cells[i][0] - cr) ** 2 + (cells[i][1] - cc) ** 2),
                ),
            )
            corner_candidates = ranked[: min(6, self.M)]

        corner_candidates = sorted(
            corner_candidates,
            key=lambda i: math.atan2(cells[i][0] - cr, cells[i][1] - cc),
        )[:6]

        self.corner_indices = corner_candidates
        corner_set = set(corner_candidates)

        corner_bit = [0] * self.M
        for k, i in enumerate(corner_candidates):
            corner_bit[i] = 1 << k
        self.corner_bit = corner_bit

        edge_mask = [0] * self.M
        edge_groups = [[] for _ in range(6)]
        for i, lm in enumerate(line_masks):
            if i in corner_set:
                continue
            if lm and (lm & (lm - 1)) == 0:
                e = lm.bit_length() - 1
                if 0 <= e < 6:
                    edge_mask[i] = lm
                    edge_groups[e].append(i)

        self.edge_mask = edge_mask
        self.edge_groups = edge_groups

        side_d = []
        for q, a, b in ax:
            d = min(q - qmin, qmax - q, a - amin, amax - a, b - bmin, bmax - b)
            side_d.append(max(0, d))
        max_side = max(side_d) if side_d else 1

        if max_side > 0:
            self.center_score = [d / float(max_side) for d in side_d]
        else:
            self.center_score = [1.0] * self.M

        center_dist2 = [((r - cr) ** 2 + (c - cc) ** 2) for r, c in cells]
        self.center_order = sorted(
            range(self.M),
            key=lambda i: (-self.center_score[i], center_dist2[i], cells[i][0], cells[i][1]),
        )

        self.noise = [
            (((r * 92821 + c * 68917 + 17) & 1023) / 1024.0) * 0.001
            for r, c in cells
        ]

        # Extended board used for ring flood-fill. Invalid cells are passable outside space.
        w = cols + 2
        ext_n = (rows + 2) * (cols + 2)

        def eidx(rr: int, cc_: int) -> int:
            return (rr + 1) * w + (cc_ + 1)

        ext_to_cell = [-1] * ext_n
        valid_ext = [0] * self.M
        for i, (r, c) in enumerate(cells):
            ex = eidx(r, c)
            ext_to_cell[ex] = i
            valid_ext[i] = ex

        ext_neighbors = []
        ext_boundary = []
        for rr in range(-1, rows + 1):
            for cc_ in range(-1, cols + 1):
                here = eidx(rr, cc_)
                if rr == -1 or rr == rows or cc_ == -1 or cc_ == cols:
                    ext_boundary.append(here)
                ns = []
                for nr, nc in _ordered_neighbor_coords(rr, cc_):
                    if -1 <= nr <= rows and -1 <= nc <= cols:
                        ns.append(eidx(nr, nc))
                ext_neighbors.append(tuple(ns))

        self.ext_n = ext_n
        self.ext_boundary = tuple(ext_boundary)
        self.ext_neighbors = tuple(ext_neighbors)
        self.ext_to_cell = ext_to_cell
        self.valid_ext = valid_ext

    def has_cell_ring_after(self, player_bool: bytearray, add_idx: int) -> bool:
        # Catches single-cell rings, including when the surrounded cell is our own stone.
        for center in self.neigh[add_idx]:
            ok = True
            for nb in self.ordered[center]:
                if nb < 0 or (not player_bool[nb] and nb != add_idx):
                    ok = False
                    break
            if ok:
                return True
        return False

    def has_ring_after(self, player_bool: bytearray, add_idx: int) -> bool:
        if self.has_cell_ring_after(player_bool, add_idx):
            return True

        if self.ext_n <= 0:
            return False

        seen = bytearray(self.ext_n)
        q = deque()
        ext_to_cell = self.ext_to_cell

        for s in self.ext_boundary:
            ci = ext_to_cell[s]
            if ci >= 0 and (player_bool[ci] or ci == add_idx):
                continue
            seen[s] = 1
            q.append(s)

        while q:
            v = q.popleft()
            for nb in self.ext_neighbors[v]:
                if seen[nb]:
                    continue
                ci = ext_to_cell[nb]
                if ci >= 0 and (player_bool[ci] or ci == add_idx):
                    continue
                seen[nb] = 1
                q.append(nb)

        for ci, ex in enumerate(self.valid_ext):
            if ci == add_idx or player_bool[ci]:
                continue
            if not seen[ex]:
                return True

        return False


def _get_geom(valid_mask) -> _Geom:
    rows, cols = _dims(valid_mask)
    mask_rows = tuple(
        tuple(1 if bool(valid_mask[r][c]) else 0 for c in range(cols))
        for r in range(rows)
    )
    key = (rows, cols, mask_rows)
    geom = _GEOM_CACHE.get(key)
    if geom is None:
        if len(_GEOM_CACHE) > 3:
            _GEOM_CACHE.clear()
        geom = _Geom(mask_rows, rows, cols)
        _GEOM_CACHE[key] = geom
    return geom


def _stones_to_bool(stones, geom: _Geom) -> bytearray:
    b = bytearray(geom.M)
    if stones is None:
        return b
    for p in stones:
        try:
            r, c = int(p[0]), int(p[1])
        except Exception:
            continue
        if 0 <= r < geom.R and 0 <= c < geom.C:
            i = geom.idx[r][c]
            if i >= 0:
                b[i] = 1
    return b


def _build_components(player_bool: bytearray, geom: _Geom):
    comp_id = [-1] * geom.M
    edge_masks = []
    corner_masks = []
    sizes = []

    cid = 0
    for i in range(geom.M):
        if not player_bool[i] or comp_id[i] >= 0:
            continue

        stack = [i]
        comp_id[i] = cid
        em = 0
        cm = 0
        sz = 0

        while stack:
            v = stack.pop()
            sz += 1
            em |= geom.edge_mask[v]
            cm |= geom.corner_bit[v]
            for nb in geom.neigh[v]:
                if player_bool[nb] and comp_id[nb] < 0:
                    comp_id[nb] = cid
                    stack.append(nb)

        edge_masks.append(em)
        corner_masks.append(cm)
        sizes.append(sz)
        cid += 1

    return comp_id, edge_masks, corner_masks, sizes


def _after_masks(idx: int, player_bool: bytearray, comp, geom: _Geom):
    comp_id, edge_masks, corner_masks, sizes = comp

    em = geom.edge_mask[idx]
    cm = geom.corner_bit[idx]
    size = 1
    own_adj = 0
    seen = []

    for nb in geom.neigh[idx]:
        if player_bool[nb]:
            own_adj += 1
            cid = comp_id[nb]
            if cid >= 0 and cid not in seen:
                seen.append(cid)
                em |= edge_masks[cid]
                cm |= corner_masks[cid]
                size += sizes[cid]

    return em, cm, size, own_adj, len(seen)


def _is_win_after_idx(idx: int, player_bool: bytearray, comp, geom: _Geom) -> bool:
    em, cm, _size, own_adj, unique = _after_masks(idx, player_bool, comp, geom)

    if _popcount(cm) >= 2:
        return True
    if _popcount(em) >= 3:
        return True

    # A newly created ring must connect two neighbours already in the same component.
    if own_adj >= 2 and own_adj > unique:
        if geom.has_ring_after(player_bool, idx):
            return True

    return False


def _find_winning_moves(legal, player_bool: bytearray, comp, geom: _Geom):
    out = []
    for idx in legal:
        if _is_win_after_idx(idx, player_bool, comp, geom):
            out.append(idx)
    return out


def _multi_source_dist(sources, player_bool: bytearray, blocker_bool: bytearray, geom: _Geom):
    dist = [_INF] * geom.M
    q = deque()

    for s in sources:
        if s < 0 or s >= geom.M or blocker_bool[s]:
            continue
        start = 0 if player_bool[s] else 1
        if start < dist[s]:
            dist[s] = start
            if start == 0:
                q.appendleft(s)
            else:
                q.append(s)

    while q:
        v = q.popleft()
        dv = dist[v]
        for nb in geom.neigh[v]:
            if blocker_bool[nb]:
                continue
            w = 0 if player_bool[nb] else 1
            nd = dv + w
            if nd < dist[nb]:
                dist[nb] = nd
                if w == 0:
                    q.appendleft(nb)
                else:
                    q.append(nb)

    return dist


def _compute_dist_maps(geom: _Geom, player_bool: bytearray, blocker_bool: bytearray):
    edge_dists = [
        _multi_source_dist(group, player_bool, blocker_bool, geom)
        for group in geom.edge_groups
    ]
    corner_dists = [
        _multi_source_dist([ci], player_bool, blocker_bool, geom)
        for ci in geom.corner_indices
    ]
    return edge_dists, corner_dists


def _ring_potential(idx: int, player_bool: bytearray, geom: _Geom) -> float:
    score = 0.0

    # Near-surrounds of neighbouring cells.
    for center in geom.neigh[idx]:
        cnt = 0
        valid6 = True
        for nb in geom.ordered[center]:
            if nb < 0:
                valid6 = False
                break
            if nb == idx or player_bool[nb]:
                cnt += 1
        if valid6:
            if cnt >= 5:
                score += 75.0
            elif cnt == 4:
                score += 20.0
            elif cnt == 3:
                score += 5.0

    # Separated arms around the candidate are useful for future rings.
    own_dirs = []
    for k, nb in enumerate(geom.ordered[idx]):
        if nb >= 0 and player_bool[nb]:
            own_dirs.append(k)

    n = len(own_dirs)
    if n >= 2:
        adj_pairs = 0
        sep_pairs = 0
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(own_dirs[i] - own_dirs[j])
                d = min(d, 6 - d)
                if d == 1:
                    adj_pairs += 1
                else:
                    sep_pairs += 1
        score += 2.0 * adj_pairs + 6.0 * sep_pairs
        if n >= 3:
            score += 4.0 * (n - 2)

    return score


def _connection_eval(
    idx: int,
    player_bool: bytearray,
    enemy_bool: bytearray,
    comp,
    edge_dists,
    corner_dists,
    geom: _Geom,
    total_moves: int,
) -> float:
    em, cm, size, own_adj, unique = _after_masks(idx, player_bool, comp, geom)

    edge_count = _popcount(em)
    corner_count = _popcount(cm)

    enemy_adj = 0
    for nb in geom.neigh[idx]:
        if enemy_bool[nb]:
            enemy_adj += 1
    empty_adj = len(geom.neigh[idx]) - own_adj - enemy_adj

    phase = 1.0 - total_moves / max(1.0, geom.M * 0.45)
    if phase < 0.0:
        phase = 0.0

    score = 0.0

    # Center is strongest early; edges become valuable once components exist.
    score += (18.0 + 24.0 * phase) * geom.center_score[idx]

    # Local connectivity.
    score += 3.4 * own_adj
    score += 11.0 * max(0, unique - 1)
    score += 1.8 * math.sqrt(size)
    score += 0.22 * min(size, 35)

    if total_moves > 8 and own_adj == 0:
        score -= 7.5

    # Liberties and contact.
    score += 1.2 * empty_adj
    score += 1.0 * enemy_adj
    if empty_adj <= 1 and own_adj < 4:
        score -= 3.5 * (2 - empty_adj)

    # Direct structural progress.
    if edge_count == 1:
        score += 16.0
    elif edge_count == 2:
        score += 115.0
    elif edge_count >= 3:
        score += 100000.0

    if corner_count == 1:
        score += 34.0
    elif corner_count >= 2:
        score += 100000.0

    if edge_count == 2 and unique >= 2:
        score += 28.0
    if corner_count == 1 and size >= 3:
        score += 12.0

    # Fork potential by shortest empty-cell connection costs to edges.
    edge_costs = []
    for e in range(6):
        if em & (1 << e):
            edge_costs.append(0.0)
        elif e < len(edge_dists):
            d = edge_dists[e][idx]
            edge_costs.append(99.0 if d >= _INF else float(max(0, d - 1)))
        else:
            edge_costs.append(99.0)

    finite_edges = sorted(c for c in edge_costs if c < 90.0)
    if len(finite_edges) >= 3:
        s3 = finite_edges[0] + finite_edges[1] + finite_edges[2]
        score += 285.0 / ((s3 + 2.2) ** 1.22)
        score += 16.0 / (finite_edges[0] + 1.0)
        score += 11.0 / (finite_edges[1] + 1.0)
        score += 8.0 / (finite_edges[2] + 1.0)

        if edge_count == 2:
            third = finite_edges[2]
            score += 145.0 / (third + 1.0)
            if third <= 1.0:
                score += 55.0
        elif edge_count == 1:
            score += 45.0 / (finite_edges[1] + 1.0)
            score += 25.0 / (finite_edges[2] + 1.0)

    # Bridge potential by shortest costs to corners.
    corner_costs = []
    for k, dmap in enumerate(corner_dists):
        if cm & (1 << k):
            corner_costs.append(0.0)
        else:
            d = dmap[idx]
            corner_costs.append(99.0 if d >= _INF else float(max(0, d - 1)))

    finite_corners = sorted(c for c in corner_costs if c < 90.0)
    if len(finite_corners) >= 2:
        s2 = finite_corners[0] + finite_corners[1]
        score += 135.0 / ((s2 + 2.5) ** 1.18)
        if corner_count == 1 and len(finite_corners) > 1:
            score += 65.0 / (finite_corners[1] + 1.0)
        elif corner_count == 0:
            score += 14.0 / (finite_corners[0] + 1.0)
            score += 10.0 / (finite_corners[1] + 1.0)

    score += _ring_potential(idx, player_bool, geom)

    return score


def _count_winning_replies(
    first_idx: int,
    player_bool: bytearray,
    legal_indices,
    geom: _Geom,
    limit: int = 3,
) -> int:
    old = player_bool[first_idx]
    player_bool[first_idx] = 1
    try:
        comp = _build_components(player_bool, geom)
        cnt = 0
        for idx in legal_indices:
            if idx == first_idx:
                continue
            if _is_win_after_idx(idx, player_bool, comp, geom):
                cnt += 1
                if cnt >= limit:
                    return cnt
        return cnt
    finally:
        player_bool[first_idx] = old


def _idx_to_move(geom: _Geom, idx: int) -> tuple[int, int]:
    r, c = geom.cells[idx]
    return int(r), int(c)


def _static_choice(candidates, geom: _Geom, my_bool: bytearray, opp_bool: bytearray) -> int:
    best = candidates[0]
    best_s = -1e100
    for idx in candidates:
        own_adj = 0
        opp_adj = 0
        for nb in geom.neigh[idx]:
            if my_bool[nb]:
                own_adj += 1
            if opp_bool[nb]:
                opp_adj += 1
        s = 30.0 * geom.center_score[idx] + 2.0 * own_adj + 1.3 * opp_adj + geom.noise[idx]
        if s > best_s:
            best_s = s
            best = idx
    return best


def _policy_core(me, opp, valid_mask) -> tuple[int, int]:
    geom = _get_geom(valid_mask)
    if geom.M == 0:
        return _fallback_move(me, opp, valid_mask)

    my_bool = _stones_to_bool(me, geom)
    opp_bool = _stones_to_bool(opp, geom)

    legal = [i for i in range(geom.M) if not my_bool[i] and not opp_bool[i]]
    if not legal:
        return _fallback_move(me, opp, valid_mask)

    total_moves = int(sum(my_bool) + sum(opp_bool))

    # Strong deterministic opening.
    if total_moves == 0:
        for idx in geom.center_order:
            if idx in legal:
                return _idx_to_move(geom, idx)

    my_comp = _build_components(my_bool, geom)
    opp_comp = _build_components(opp_bool, geom)

    # 1. Win immediately if possible.
    my_wins = _find_winning_moves(legal, my_bool, my_comp, geom)
    if my_wins:
        return _idx_to_move(geom, _static_choice(my_wins, geom, my_bool, opp_bool))

    # 2. Block opponent's immediate win.
    opp_wins = _find_winning_moves(legal, opp_bool, opp_comp, geom)
    if opp_wins:
        return _idx_to_move(geom, _static_choice(opp_wins, geom, my_bool, opp_bool))

    # 3. Positional scoring.
    my_edge_d, my_corner_d = _compute_dist_maps(geom, my_bool, opp_bool)
    opp_edge_d, opp_corner_d = _compute_dist_maps(geom, opp_bool, my_bool)

    defense_weight = 0.82 + 0.18 * (total_moves / max(1.0, float(geom.M)))
    if defense_weight > 0.98:
        defense_weight = 0.98

    scores = {}
    my_values = {}
    opp_values = {}

    for idx in legal:
        mv = _connection_eval(
            idx, my_bool, opp_bool, my_comp, my_edge_d, my_corner_d, geom, total_moves
        )
        ov = _connection_eval(
            idx, opp_bool, my_bool, opp_comp, opp_edge_d, opp_corner_d, geom, total_moves
        )
        my_values[idx] = mv
        opp_values[idx] = ov
        scores[idx] = mv + defense_weight * ov + geom.noise[idx]

    # 4. Shallow tactical threat search: create/block double threats.
    if total_moves >= 6 and len(legal) > 1:
        if len(legal) <= 60:
            deep = set(legal)
        else:
            ranked_combined = sorted(legal, key=lambda i: scores[i], reverse=True)
            ranked_my = sorted(legal, key=lambda i: my_values[i], reverse=True)
            ranked_opp = sorted(legal, key=lambda i: opp_values[i], reverse=True)
            deep = set(ranked_combined[:18])
            deep.update(ranked_my[:10])
            deep.update(ranked_opp[:12])

        for idx in deep:
            mt = _count_winning_replies(idx, my_bool, legal, geom, limit=3)
            if mt >= 2:
                scores[idx] += 220000.0 + 5000.0 * mt
            elif mt == 1:
                scores[idx] += 900.0

            ot = _count_winning_replies(idx, opp_bool, legal, geom, limit=3)
            if ot >= 2:
                scores[idx] += 180000.0 + 4500.0 * ot
            elif ot == 1:
                scores[idx] += 520.0

    best = max(legal, key=lambda i: (scores[i], geom.center_score[i], geom.noise[i]))
    return _idx_to_move(geom, best)


def _fallback_move(me, opp, valid_mask) -> tuple[int, int]:
    try:
        rows, cols = _dims(valid_mask)
        occupied = set()
        for stones in (me, opp):
            if stones is None:
                continue
            for p in stones:
                try:
                    occupied.add((int(p[0]), int(p[1])))
                except Exception:
                    pass

        cr = (rows - 1) / 2.0
        cc = (cols - 1) / 2.0
        best = None
        best_s = -1e100

        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    s = -((r - cr) ** 2 + (c - cc) ** 2)
                    if s > best_s:
                        best_s = s
                        best = (r, c)

        if best is not None:
            return int(best[0]), int(best[1])

        # Should never be needed in a non-full game.
        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]):
                    return int(r), int(c)
    except Exception:
        pass

    return 0, 0


def _move_is_legal(move, me, opp, valid_mask) -> bool:
    try:
        r, c = int(move[0]), int(move[1])
        rows, cols = _dims(valid_mask)
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        if not bool(valid_mask[r][c]):
            return False

        for stones in (me, opp):
            if stones is None:
                continue
            for p in stones:
                if (int(p[0]), int(p[1])) == (r, c):
                    return False
        return True
    except Exception:
        return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        mv = _policy_core(me, opp, valid_mask)
        if _move_is_legal(mv, me, opp, valid_mask):
            return int(mv[0]), int(mv[1])
    except Exception:
        pass

    return _fallback_move(me, opp, valid_mask)
