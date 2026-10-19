
from collections import deque

_DIRS_A = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1))
_DIRS_B = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1))

_CACHE = {}


class _Board:
    __slots__ = (
        "R", "C", "valid", "idx", "cells", "n", "dirs", "diag_kind", "neigh",
        "edge_mask", "corner_mask", "boundary", "boundary_flag",
        "center", "centrality", "maxdist"
    )


class _Comps:
    __slots__ = ("comp_id", "sizes", "edges", "corners")


def _popcount(x):
    return x.bit_count()


def _third(r, c, diag_kind):
    return r - c if diag_kind == 0 else r + c


def _hex_dist(a, b, diag_kind):
    r1, c1 = a
    r2, c2 = b
    dr = abs(r1 - r2)
    dc = abs(c1 - c2)
    dt = abs(_third(r1, c1, diag_kind) - _third(r2, c2, diag_kind))
    return max(dr, dc, dt)


def _dir_score(valid, R, C, dirs):
    degs = []
    for r in range(R):
        row = valid[r]
        for c in range(C):
            if not row[c]:
                continue
            d = 0
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < R and 0 <= nc < C and valid[nr][nc]:
                    d += 1
            degs.append(d)
    if not degs:
        return -10**9
    cnt3 = sum(1 for d in degs if d == 3)
    cnt4 = sum(1 for d in degs if d == 4)
    cnt5 = sum(1 for d in degs if d == 5)
    cnt6 = sum(1 for d in degs if d == 6)
    low = sum(1 for d in degs if d < 3)
    return cnt6 * 8 + cnt5 * 3 + cnt4 * 4 + cnt3 * 5 - low * 30 - abs(cnt3 - 6) * 18


def _get_board(valid_mask):
    R = len(valid_mask)
    C = len(valid_mask[0]) if R else 0

    valid = []
    row_masks = []
    for r in range(R):
        row = []
        mask = 0
        for c in range(C):
            b = bool(valid_mask[r][c])
            row.append(b)
            if b:
                mask |= (1 << c)
        valid.append(row)
        row_masks.append(mask)

    key = (R, C, tuple(row_masks))
    if key in _CACHE:
        return _CACHE[key]

    b = _Board()
    b.R = R
    b.C = C
    b.valid = valid

    score_a = _dir_score(valid, R, C, _DIRS_A)
    score_b = _dir_score(valid, R, C, _DIRS_B)
    b.dirs = _DIRS_A if score_a >= score_b else _DIRS_B
    b.diag_kind = 0 if b.dirs == _DIRS_A else 1

    idx = [[-1 for _ in range(C)] for _ in range(R)]
    cells = []
    for r in range(R):
        for c in range(C):
            if valid[r][c]:
                idx[r][c] = len(cells)
                cells.append((r, c))

    b.idx = idx
    b.cells = cells
    b.n = len(cells)

    neigh = [[] for _ in range(b.n)]
    for i, (r, c) in enumerate(cells):
        ns = neigh[i]
        for dr, dc in b.dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C:
                j = idx[nr][nc]
                if j >= 0:
                    ns.append(j)
    b.neigh = neigh

    if b.n == 0:
        b.edge_mask = []
        b.corner_mask = []
        b.boundary = []
        b.boundary_flag = []
        b.center = -1
        b.centrality = []
        b.maxdist = 0
        _CACHE[key] = b
        return b

    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    ts = [_third(r, c, b.diag_kind) for r, c in cells]

    minr, maxr = min(rs), max(rs)
    minc, maxc = min(cs), max(cs)
    mint, maxt = min(ts), max(ts)

    conds = []
    corner_candidates = []
    for i, (r, c) in enumerate(cells):
        t = _third(r, c, b.diag_kind)
        cc = (
            r == minr,
            t == mint,
            c == maxc,
            r == maxr,
            t == maxt,
            c == minc,
        )
        conds.append(cc)
        if sum(1 for x in cc if x) >= 2:
            corner_candidates.append(i)

    if len(corner_candidates) != 6 and b.n >= 6:
        mr = sum(rs) / float(b.n)
        mc = sum(cs) / float(b.n)
        boundary_like = [i for i in range(b.n) if len(neigh[i]) < 6]
        if len(boundary_like) < 6:
            boundary_like = list(range(b.n))
        boundary_like.sort(
            key=lambda i: (
                len(neigh[i]),
                -((cells[i][0] - mr) ** 2 + (cells[i][1] - mc) ** 2),
            )
        )
        corner_candidates = boundary_like[:6]

    corner_mask = [0] * b.n
    for k, i in enumerate(corner_candidates):
        corner_mask[i] = 1 << k

    edge_mask = [0] * b.n
    for i in range(b.n):
        if corner_mask[i]:
            continue
        m = 0
        for k, flag in enumerate(conds[i]):
            if flag:
                m |= 1 << k
        edge_mask[i] = m

    b.edge_mask = edge_mask
    b.corner_mask = corner_mask

    boundary = []
    boundary_flag = [0] * b.n
    for i in range(b.n):
        if edge_mask[i] or corner_mask[i] or len(neigh[i]) < 6:
            boundary.append(i)
            boundary_flag[i] = 1
    b.boundary = boundary
    b.boundary_flag = boundary_flag

    mr = sum(rs) / float(b.n)
    mc = sum(cs) / float(b.n)
    center = min(range(b.n), key=lambda i: (cells[i][0] - mr) ** 2 + (cells[i][1] - mc) ** 2)
    b.center = center

    dists = [_hex_dist(cells[i], cells[center], b.diag_kind) for i in range(b.n)]
    maxdist = max(dists) if dists else 0
    b.maxdist = maxdist
    b.centrality = [maxdist - d for d in dists]

    _CACHE[key] = b
    return b


def _build_components(stones, board):
    comp = _Comps()
    comp_id = [-1] * board.n
    sizes = []
    edges = []
    corners = []

    for s in stones:
        if s < 0 or s >= board.n or comp_id[s] >= 0:
            continue
        cid = len(sizes)
        stack = [s]
        comp_id[s] = cid
        size = 0
        em = 0
        cm = 0
        while stack:
            x = stack.pop()
            size += 1
            em |= board.edge_mask[x]
            cm |= board.corner_mask[x]
            for nb in board.neigh[x]:
                if nb in stones and comp_id[nb] < 0:
                    comp_id[nb] = cid
                    stack.append(nb)
        sizes.append(size)
        edges.append(em)
        corners.append(cm)

    comp.comp_id = comp_id
    comp.sizes = sizes
    comp.edges = edges
    comp.corners = corners
    return comp


def _has_ring_after(stones, move, board):
    # Flood all non-own cells from the outer boundary.  If any non-own cell is
    # unreachable, own stones enclose a region, which is a Havannah ring.
    seen = set()
    q = []

    for s in board.boundary:
        if s != move and s not in stones:
            seen.add(s)
            q.append(s)

    head = 0
    while head < len(q):
        x = q[head]
        head += 1
        for nb in board.neigh[x]:
            if nb == move or nb in stones or nb in seen:
                continue
            seen.add(nb)
            q.append(nb)

    for i in range(board.n):
        if i != move and i not in stones and i not in seen:
            return True
    return False


def _is_win_after(stones, move, board):
    stack = [move]
    seen = {move}
    em = board.edge_mask[move]
    cm = board.corner_mask[move]
    friendly_neighbors = 0

    for nb in board.neigh[move]:
        if nb in stones:
            friendly_neighbors += 1

    while stack:
        x = stack.pop()
        for nb in board.neigh[x]:
            if nb != move and nb not in stones:
                continue
            if nb in seen:
                continue
            seen.add(nb)
            em |= board.edge_mask[nb]
            cm |= board.corner_mask[nb]
            stack.append(nb)

    if _popcount(cm) >= 2:
        return True
    if _popcount(em) >= 3:
        return True

    if friendly_neighbors >= 2 and _has_ring_after(stones, move, board):
        return True

    return False


def _winning_moves_for(stones, legal, board, stop=None):
    out = []
    for m in legal:
        if _is_win_after(stones, m, board):
            out.append(m)
            if stop is not None and len(out) >= stop:
                break
    return out


def _count_winning(stones, legal, board, stop=3):
    cnt = 0
    for m in legal:
        if _is_win_after(stones, m, board):
            cnt += 1
            if cnt >= stop:
                return cnt
    return cnt


def _value_for_side(m, comps, side_stones, other_stones, occupied, board):
    cids = set()
    friendly_n = 0
    enemy_n = 0
    empty_n = 0

    for nb in board.neigh[m]:
        cid = comps.comp_id[nb]
        if cid >= 0:
            friendly_n += 1
            cids.add(cid)
        elif nb in other_stones:
            enemy_n += 1
        else:
            empty_n += 1

    em = board.edge_mask[m]
    cm = board.corner_mask[m]
    size = 1
    largest = 0

    for cid in cids:
        sz = comps.sizes[cid]
        size += sz
        if sz > largest:
            largest = sz
        em |= comps.edges[cid]
        cm |= comps.corners[cid]

    edge_count = _popcount(em)
    corner_count = _popcount(cm)
    unique_components = len(cids)
    same_component_extra = max(0, friendly_n - unique_components)

    phase = len(occupied) / float(max(1, board.n))
    central_weight = 8.0 - 5.0 * min(1.0, phase)

    score = 0.0
    score += central_weight * board.centrality[m]
    score += 6.0 * empty_n

    if len(side_stones) <= 2 and board.boundary_flag[m]:
        score -= 38.0

    score += 12.0 * friendly_n
    score += 32.0 * max(0, unique_components - 1)
    score += 1.10 * size
    score += 0.20 * largest
    score += 42.0 * same_component_extra

    score += 22.0 * edge_count * edge_count
    score += 28.0 * corner_count * corner_count

    if edge_count == 2:
        score += 90.0
    elif edge_count == 1:
        score += 12.0

    if corner_count == 1:
        score += 45.0

    if board.edge_mask[m] and friendly_n:
        score += 18.0
    if board.corner_mask[m] and friendly_n:
        score += 30.0

    if board.corner_mask[m] and friendly_n == 0 and len(side_stones) < 5:
        score -= 25.0

    score += 3.0 * enemy_n
    return score


def _combined_score(m, my_comps, opp_comps, me_set, opp_set, occupied, board):
    my_v = _value_for_side(m, my_comps, me_set, opp_set, occupied, board)
    opp_v = _value_for_side(m, opp_comps, opp_set, me_set, occupied, board)
    return my_v + 0.72 * opp_v


def _fallback(me, opp, valid_mask):
    try:
        occ = set(tuple(x) for x in (me or [])) | set(tuple(x) for x in (opp or []))
        R = len(valid_mask)
        C = len(valid_mask[0]) if R else 0
        cr = (R - 1) / 2.0
        cc = (C - 1) / 2.0
        best = None
        best_score = -10**100
        for r in range(R):
            for c in range(C):
                if bool(valid_mask[r][c]) and (r, c) not in occ:
                    sc = -((r - cr) ** 2 + (c - cc) ** 2)
                    if sc > best_score:
                        best_score = sc
                        best = (r, c)
        if best is not None:
            return best
    except Exception:
        pass
    return (0, 0)


def _policy(me, opp, valid_mask):
    board = _get_board(valid_mask)

    me_set = set()
    opp_set = set()

    for r, c in me:
        r = int(r)
        c = int(c)
        if 0 <= r < board.R and 0 <= c < board.C:
            i = board.idx[r][c]
            if i >= 0:
                me_set.add(i)

    for r, c in opp:
        r = int(r)
        c = int(c)
        if 0 <= r < board.R and 0 <= c < board.C:
            i = board.idx[r][c]
            if i >= 0:
                opp_set.add(i)

    occupied = me_set | opp_set
    legal = [i for i in range(board.n) if i not in occupied]

    if not legal:
        return _fallback(me, opp, valid_mask)

    if not occupied and board.center in legal:
        return board.cells[board.center]

    my_comps = _build_components(me_set, board)
    opp_comps = _build_components(opp_set, board)

    # 1. Win immediately if possible.
    my_wins = _winning_moves_for(me_set, legal, board)
    if my_wins:
        best = max(
            my_wins,
            key=lambda m: _combined_score(m, my_comps, opp_comps, me_set, opp_set, occupied, board)
        )
        return board.cells[best]

    # 2. Block opponent's immediate win.
    opp_wins = _winning_moves_for(opp_set, legal, board)
    if opp_wins:
        best = max(
            opp_wins,
            key=lambda m: _combined_score(m, my_comps, opp_comps, me_set, opp_set, occupied, board)
        )
        return board.cells[best]

    # 3. Static scoring.
    scored = []
    for m in legal:
        scored.append((
            _combined_score(m, my_comps, opp_comps, me_set, opp_set, occupied, board),
            m
        ))
    scored.sort(reverse=True)

    # 4. Find our forcing double-threat moves.
    my_threat_counts = {}
    top_my = scored[:min(24, len(scored))]
    forcing = []
    for base, m in top_my:
        me_after = set(me_set)
        me_after.add(m)
        legal_after = [x for x in legal if x != m]
        cnt = _count_winning(me_after, legal_after, board, stop=3)
        my_threat_counts[m] = cnt
        if cnt >= 2:
            forcing.append((cnt, base, m))

    if forcing:
        forcing.sort(reverse=True)
        return board.cells[forcing[0][2]]

    # 5. Block opponent's double-threat creators.
    opp_scored = []
    for m in legal:
        ov = _value_for_side(m, opp_comps, opp_set, me_set, occupied, board)
        dv = _value_for_side(m, my_comps, me_set, opp_set, occupied, board)
        opp_scored.append((ov + 0.35 * dv, m))
    opp_scored.sort(reverse=True)

    dangers = []
    for _, m in opp_scored[:min(24, len(opp_scored))]:
        opp_after = set(opp_set)
        opp_after.add(m)
        legal_after = [x for x in legal if x != m]
        cnt = _count_winning(opp_after, legal_after, board, stop=3)
        if cnt >= 2:
            dangers.append((
                cnt,
                _combined_score(m, my_comps, opp_comps, me_set, opp_set, occupied, board),
                m
            ))

    if dangers:
        dangers.sort(reverse=True)
        return board.cells[dangers[0][2]]

    # 6. Final choice: prefer best heuristic move, with a bonus for single threats.
    best_m = scored[0][1]
    best_s = -10**100
    for rank, (base, m) in enumerate(scored[:min(36, len(scored))]):
        s = base - 0.05 * rank
        cnt = my_threat_counts.get(m)
        if cnt is None and rank < 16:
            me_after = set(me_set)
            me_after.add(m)
            legal_after = [x for x in legal if x != m]
            cnt = _count_winning(me_after, legal_after, board, stop=2)
            my_threat_counts[m] = cnt
        if cnt:
            s += 420.0 * cnt
        if s > best_s:
            best_s = s
            best_m = m

    return board.cells[best_m]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        mv = _policy(me or [], opp or [], valid_mask)
        r, c = int(mv[0]), int(mv[1])
        occupied = set(tuple(x) for x in (me or [])) | set(tuple(x) for x in (opp or []))
        if (r, c) not in occupied and bool(valid_mask[r][c]):
            return (r, c)
    except Exception:
        pass
    return _fallback(me, opp, valid_mask)
