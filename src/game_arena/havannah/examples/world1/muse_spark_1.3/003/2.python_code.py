
import numpy as np
import math
import time
from collections import deque

_CACHE = {}
DIRS8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def _build_info(vm):
    N = vm.shape[0]
    coords = []
    coord_to_vi = {}
    for r in range(N):
        for c in range(N):
            if vm[r, c]:
                vi = len(coords)
                coords.append((r, c))
                coord_to_vi[(r, c)] = vi
    V = len(coords)
    nbrs = [[] for _ in range(V)]
    for vi, (r, c) in enumerate(coords):
        lst = []
        for dr, dc in DIRS8:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and vm[nr, nc]:
                lst.append(coord_to_vi[(nr, nc)])
        nbrs[vi] = lst
    # border: <8 valid king neighbours
    border_vi = [vi for vi in range(V) if len(nbrs[vi]) < 8]
    # if board is full (should not happen) fallback
    if len(border_vi) == 0:
        border_vi = list(range(V))
    border_set = set(border_vi)
    cr = sum(r for r, c in coords) / V
    cc = sum(c for r, c in coords) / V
    # order border by angle
    angs = []
    for vi in border_vi:
        r, c = coords[vi]
        angs.append(math.atan2(r - cr, c - cc))
    order = sorted(range(len(border_vi)), key=lambda i: angs[i])
    bord_order = [border_vi[i] for i in order]
    B = len(bord_order)
    # curvature scores
    k = 4 if B > 30 else 2
    if B < 12:
        k = 1
    pos = np.array([coords[vi] for vi in bord_order], dtype=float)
    scores = [0.0]*B
    for i in range(B):
        a = pos[i] - pos[(i-k) % B]
        b = pos[(i+k) % B] - pos[i]
        na = math.hypot(a[0], a[1]) + 1e-9
        nb = math.hypot(b[0], b[1]) + 1e-9
        dot = (a[0]*b[0]+a[1]*b[1])/(na*nb)
        dot = max(-1.0, min(1.0, dot))
        scores[i] = 1.0 - dot
    # pick 6 corners with separation
    idx_sorted = sorted(range(B), key=lambda i: scores[i], reverse=True)
    corners_order_pos = []
    min_dist = max(2, B // 14)
    for ii in idx_sorted:
        ok = True
        for cj in corners_order_pos:
            d = abs(ii-cj)
            d = min(d, B-d)
            if d < min_dist:
                ok = False
                break
        if ok:
            corners_order_pos.append(ii)
            if len(corners_order_pos) == 6:
                break
    if len(corners_order_pos) < 6:
        # fallback equally spaced
        corners_order_pos = [(i*B)//6 for i in range(6)]
    corners_order_pos = sorted(corners_order_pos)
    corner_vi_set = set(bord_order[p] for p in corners_order_pos)
    # edge id for non-corner border cells: segment between corners
    edge_of = {}
    for vi in border_vi:
        edge_of[vi] = -2
    for vi in corner_vi_set:
        edge_of[vi] = -1
    for e in range(6):
        a = corners_order_pos[e]
        b = corners_order_pos[(e+1) % 6]
        j = (a+1) % B
        while j != b:
            vi = bord_order[j]
            edge_of[vi] = e
            j = (j+1) % B
    info = {
        'N': N, 'V': V, 'coords': coords, 'coord_to_vi': coord_to_vi,
        'nbrs': nbrs, 'border_vi': border_vi, 'border_set': border_set,
        'corner_set': corner_vi_set, 'edge_of': edge_of,
        'bord_order': bord_order, 'cr': cr, 'cc': cc,
    }
    return info

def _get_info(valid_mask):
    vm = np.asarray(valid_mask, dtype=bool)
    key = (vm.shape, vm.tobytes())
    if key not in _CACHE:
        _CACHE[key] = _build_info(vm)
    return _CACHE[key]

def _has_bridge_fork(me_set, info):
    nbrs = info['nbrs']
    edge_of = info['edge_of']
    corner_set = info['corner_set']
    visited = set()
    for s in me_set:
        if s in visited:
            continue
        # bfs component
        stack = [s]
        visited.add(s)
        comp = [s]
        qi = 0
        while qi < len(stack):
            u = stack[qi]; qi += 1
            for w in nbrs[u]:
                if w in me_set and w not in visited:
                    visited.add(w)
                    stack.append(w)
                    comp.append(w)
        # check touches
        c_touch = 0
        e_touch = set()
        for v in comp:
            if v in corner_set:
                c_touch += 1
            else:
                e = edge_of.get(v, -2)
                if e is not None and e >= 0:
                    e_touch.add(e)
        if c_touch >= 2:
            return True
        if len(e_touch) >= 3:
            return True
    return False

def _has_ring(me_set, info):
    # complement components; if any has no border cell -> ring
    nbrs = info['nbrs']
    V = info['V']
    border_set = info['border_set']
    # quick prune: need at least 6 stones to enclose
    if len(me_set) < 6:
        return False
    visited = set()
    # iterate over all non-me
    # build me_set for O(1)
    for start in range(V):
        if start in me_set or start in visited:
            continue
        # bfs complement component
        stack = [start]
        visited.add(start)
        touches_border = (start in border_set)
        qi = 0
        while qi < len(stack):
            u = stack[qi]; qi += 1
            for w in nbrs[u]:
                if w in me_set or w in visited:
                    continue
                visited.add(w)
                stack.append(w)
                if w in border_set:
                    touches_border = True
        if not touches_border:
            return True
    return False

def _is_win(me_set, info):
    if _has_bridge_fork(me_set, info):
        return True
    if _has_ring(me_set, info):
        return True
    return False

def policy(me, opp, valid_mask) -> tuple[int, int]:
    t0 = time.time()
    try:
        info = _get_info(valid_mask)
        N = info['N']
        coords = info['coords']
        coord_to_vi = info['coord_to_vi']
        nbrs = info['nbrs']
        border_set = info['border_set']
        corner_set = info['corner_set']
        edge_of = info['edge_of']
        cr = info['cr']; cc = info['cc']
        V = info['V']

        me_set = set()
        for r, c in me:
            vi = coord_to_vi.get((int(r), int(c)))
            if vi is not None:
                me_set.add(vi)
        opp_set = set()
        for r, c in opp:
            vi = coord_to_vi.get((int(r), int(c)))
            if vi is not None:
                opp_set.add(vi)
        occupied = me_set | opp_set
        empty = [vi for vi in range(V) if vi not in occupied]
        empty_set = set(empty)
        if not empty:
            return (int(me[0][0]), int(me[0][1])) if me else (0, 0)

        def vi_to_rc(vi):
            return coords[vi]

        # opening: centre
        total = len(me_set) + len(opp_set)
        # find centre vi
        best_c = None
        best_d = 1e9
        for vi in range(V):
            r, c = coords[vi]
            d = abs(r-cr)+abs(c-cc)
            if d < best_d:
                best_d = d
                best_c = vi
        if total == 0:
            if best_c in empty_set:
                r, c = coords[best_c]
                return (int(r), int(c))
        if total < 3:
            if best_c in empty_set:
                r, c = coords[best_c]
                return (int(r), int(c))
            # neighbour of centre
            for w in nbrs[best_c]:
                if w in empty_set:
                    r, c = coords[w]
                    return (int(r), int(c))

        # helper: adjacent empties to a set
        def adj_empty(base_set):
            s = set()
            for u in base_set:
                for w in nbrs[u]:
                    if w in empty_set:
                        s.add(w)
            return s

        me_adj = adj_empty(me_set) if me_set else set(empty)
        opp_adj = adj_empty(opp_set) if opp_set else set()

        # 1) immediate winning moves
        # order me_adj by centrality for speed
        def centrality(vi):
            r, c = coords[vi]
            return abs(r-cr)+abs(c-cc)
        me_cands = sorted(me_adj, key=centrality) if me_adj else []
        # if me empty (should not), use all
        if not me_cands and empty:
            me_cands = sorted(empty, key=centrality)[:20]

        win_move = None
        for vi in me_cands:
            if time.time()-t0 > 0.35:
                break
            me_set.add(vi)
            w = _has_bridge_fork(me_set, info)
            if w:
                me_set.discard(vi)
                win_move = vi
                break
            # ring only if plausible (component size)
            # quick check ring
            # only check ring if bridge not found to save time; check ring rarely
            # we check ring for all (still cheap enough for ~30 cands)
            rwin = _has_ring(me_set, info)
            me_set.discard(vi)
            if rwin:
                win_move = vi
                break
        if win_move is not None:
            r, c = coords[win_move]
            return (int(r), int(c))

        # 2) block opponent immediate wins
        opp_cands = sorted(opp_adj, key=centrality) if opp_adj else []
        opp_wins = []
        for vi in opp_cands:
            if time.time()-t0 > 0.6:
                break
            opp_set.add(vi)
            if _has_bridge_fork(opp_set, info):
                opp_wins.append(vi)
                opp_set.discard(vi)
                if len(opp_wins) >= 2:
                    # need to know more? keep checking a bit but break early
                    # continue to collect all? limit
                    pass
                continue
            rwin = _has_ring(opp_set, info)
            opp_set.discard(vi)
            if rwin:
                opp_wins.append(vi)
            if len(opp_wins) >= 3:
                break
        if len(opp_wins) == 1:
            r, c = coords[opp_wins[0]]
            return (int(r), int(c))
        if len(opp_wins) >= 2:
            # losing position: try to occupy one of them that also helps us most
            # pick the one with most own adjacency
            best = opp_wins[0]
            best_s = -1
            for vi in opp_wins:
                s = sum(1 for w in nbrs[vi] if w in me_set)
                # bonus centrality
                if s > best_s:
                    best_s = s
                    best = vi
            # if we have a double threat ourselves, prefer it (computed below)
            # for now block
            # fall through to double-threat search; if found, use it, else block
            block_fallback = best
        else:
            block_fallback = None

        # 3) double threat creation (bridge/fork only for speed)
        # prune to top K
        K = 18
        # score quick for pruning
        def quick_score(vi):
            ao = 0
            ap = 0
            for w in nbrs[vi]:
                if w in me_set:
                    ao += 1
                if w in opp_set:
                    ap += 1
            r, c = coords[vi]
            d = abs(r-cr)+abs(c-cc)
            bonus = 0
            if vi in corner_set:
                bonus += 3
            elif edge_of.get(vi, -2) >= 0:
                bonus += 1
            return ao*3 + ap*2 + bonus - d*0.3
        ranked = sorted(me_cands, key=quick_score, reverse=True)[:K] if me_cands else sorted(empty, key=quick_score, reverse=True)[:K]
        # for each, count follow-up wins
        double_move = None
        for vi in ranked:
            if time.time()-t0 > 0.9:
                break
            me_set.add(vi)
            # winning cells next turn = adj empties (excluding vi)
            # compute new adj set
            new_adj = set()
            for w in nbrs[vi]:
                if w in empty_set and w != vi:
                    new_adj.add(w)
            for u in me_set:
                if u == vi:
                    continue
                for w in nbrs[u]:
                    if w in empty_set and w != vi:
                        new_adj.add(w)
            # quick limit: need at least 2
            cnt = 0
            # order by quick
            for w2 in new_adj:
                # skip if time
                opp_occ = False
                me_set.add(w2)
                if _has_bridge_fork(me_set, info):
                    cnt += 1
                me_set.discard(w2)
                if cnt >= 2:
                    break
            me_set.discard(vi)
            if cnt >= 2:
                double_move = vi
                break
        if double_move is not None:
            r, c = coords[double_move]
            return (int(r), int(c))

        if block_fallback is not None:
            r, c = coords[block_fallback]
            return (int(r), int(c))

        # 4) greedy heuristic evaluation (1-ply with component analysis)
        pool = set()
        pool.update(me_adj)
        pool.update(opp_adj)
        if not pool:
            pool = set(empty)
        # limit pool size
        if len(pool) > 45:
            pool = set(sorted(pool, key=quick_score, reverse=True)[:45])
        # also ensure centre considered early
        best_vi = None
        best_sc = -1e18
        # precompute opp best size for reference (static)
        for vi in pool:
            if time.time()-t0 > 0.97:
                break
            r, c = coords[vi]
            d = abs(r-cr)+abs(c-cc)
            # bfs own component containing vi
            # union of me+vi
            # bfs limited
            stack = [vi]
            seen = {vi}
            qi = 0
            # use me_set for membership (vi treated as me)
            while qi < len(stack):
                u = stack[qi]; qi += 1
                for w in nbrs[u]:
                    if w == vi or w in me_set:
                        if w not in seen:
                            seen.add(w)
                            stack.append(w)
            size = len(seen)
            e_touch = set()
            c_touch = 0
            for v in seen:
                if v in corner_set:
                    c_touch += 1
                else:
                    e = edge_of.get(v, -2)
                    if e is not None and e >= 0:
                        e_touch.add(e)
            ao = 0
            ap = 0
            for w in nbrs[vi]:
                if w in me_set:
                    ao += 1
                if w in opp_set:
                    ap += 1
            # edge/corner occupation bonus
            occ_bonus = 0
            if vi in corner_set:
                occ_bonus = 6
            elif edge_of.get(vi, -2) >= 0:
                occ_bonus = 2
            sc = size*2.0 + len(e_touch)*15.0 + c_touch*22.0 + ao*2.0 + ap*3.0 + occ_bonus - d*0.8
            # bonus for being adjacent to multiple own components (connection)
            # approximate by ao
            if sc > best_sc:
                best_sc = sc
                best_vi = vi
        if best_vi is not None:
            r, c = coords[best_vi]
            return (int(r), int(c))

        # fallback
        for vi in empty:
            r, c = coords[vi]
            return (int(r), int(c))
    except Exception:
        pass
    # ultimate fallback: scan mask
    try:
        vm = np.asarray(valid_mask, dtype=bool)
        N = vm.shape[0]
        occ = set((int(r), int(c)) for r, c in list(me)+list(opp))
        for r in range(N):
            for c in range(N):
                if vm[r, c] and (r, c) not in occ:
                    return (int(r), int(c))
    except Exception:
        pass
    return (7, 7)
