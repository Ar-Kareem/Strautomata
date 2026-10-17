
import math
import time
from collections import deque

try:
    import numpy as np
    _HAS_NP = True
except Exception:
    _HAS_NP = False

_CACHE = {}

def _neigh_candidates(r, c, mode):
    if mode == 'col_odd_up':
        base = [(r-1, c), (r+1, c)]
        if c % 2 == 1:
            base += [(r-1, c-1), (r, c-1), (r-1, c+1), (r, c+1)]
        else:
            base += [(r, c-1), (r+1, c-1), (r, c+1), (r+1, c+1)]
        return base
    elif mode == 'col_even_up':
        base = [(r-1, c), (r+1, c)]
        if c % 2 == 0:
            base += [(r-1, c-1), (r, c-1), (r-1, c+1), (r, c+1)]
        else:
            base += [(r, c-1), (r+1, c-1), (r, c+1), (r+1, c+1)]
        return base
    else:  # row model
        base = [(r, c-1), (r, c+1)]
        if r % 2 == 0:
            base += [(r-1, c-1), (r-1, c), (r+1, c-1), (r+1, c)]
        else:
            base += [(r-1, c), (r-1, c+1), (r+1, c), (r+1, c+1)]
        return base

def _build_topo(static_valid):
    # static_valid: 2D bool array/list, NxN
    if _HAS_NP and isinstance(static_valid, np.ndarray):
        N = static_valid.shape[0]
        vm = static_valid
        def is_valid(rr, cc):
            return 0 <= rr < N and 0 <= cc < N and bool(vm[rr, cc])
    else:
        N = len(static_valid)
        vm = static_valid
        def is_valid(rr, cc):
            return 0 <= rr < N and 0 <= cc < N and bool(vm[rr][cc])
    valid_list = []
    for rr in range(N):
        for cc in range(N):
            if is_valid(rr, cc):
                valid_list.append((rr, cc))
    valid_set = set(valid_list)
    modes = ['col_odd_up', 'col_even_up', 'row']
    best = None
    best_score = -1
    best_data = None
    for mode in modes:
        neigh = {}
        for (rr, cc) in valid_list:
            lst = []
            for (nr, nc) in _neigh_candidates(rr, cc, mode):
                if (nr, nc) in valid_set:
                    lst.append((nr, nc))
            neigh[(rr, cc)] = lst
        deg3 = sum(1 for v in valid_list if len(neigh[v]) == 3)
        interior = sum(1 for v in valid_list if len(neigh[v]) == 6)
        score = interior + (10000 if deg3 == 6 else 0) - abs(deg3 - 6) * 100
        if score > best_score:
            best_score = score
            best = mode
            best_data = neigh
    neigh = best_data
    # center
    cr = sum(r for r, c in valid_list) / max(1, len(valid_list))
    cc_ = sum(c for r, c in valid_list) / max(1, len(valid_list))
    center_cell = min(valid_list, key=lambda x: (x[0]-cr)**2 + (x[1]-cc_)**2)
    # corners: degree 3, fallback closest to 3
    corners = [v for v in valid_list if len(neigh[v]) == 3]
    if len(corners) != 6:
        # pick 6 cells with smallest degree then farthest
        srt = sorted(valid_list, key=lambda x: (len(neigh[x]), -((x[0]-cr)**2+(x[1]-cc_)**2)))
        corners = srt[:6]
    # boundary
    edge_cells_set = set(v for v in valid_list if len(neigh[v]) < 6)
    # angular order
    def ang(cell):
        a = math.atan2(cell[0]-cr, cell[1]-cc_)
        if a < 0:
            a += 2*math.pi
        return a
    corner_angles = sorted([(ang(c), c) for c in corners])
    corners_sorted = [c for _, c in corner_angles]
    angs_sorted = [a for a, _ in corner_angles]
    edge_id = {}
    for v in edge_cells_set:
        if v in set(corners):
            continue
        a = ang(v)
        # find interval i where a in [angs[i], angs[i+1])
        assigned = 0
        for i in range(6):
            a1 = angs_sorted[i]
            a2 = angs_sorted[(i+1) % 6]
            if i < 5:
                if a1 <= a < a2 or (a2 < a1 and (a >= a1 or a < a2)):
                    assigned = i
                    break
            else:
                # last interval wraps, it must contain a if not found
                assigned = 5
                # verify: need correct interval search for wrap
                # redo generic: check each interval with wrap logic
                pass
        # generic correct search
        found = None
        for i in range(6):
            a1 = angs_sorted[i]
            a2 = angs_sorted[(i+1) % 6]
            if a1 <= a2:
                if a1 <= a < a2 or (i == 5 and a >= a1) or (a < angs_sorted[0] and i == 5):
                    # handle wrap cell before first corner belongs to last edge
                    found = i
                    # need wrap case: a < a0 belongs to edge 5
                    break
            else:  # wrap interval
                if a >= a1 or a < a2:
                    found = i
                    break
        # fix wrap-before-first
        if found is None:
            # a < smallest and not captured -> belongs to last edge
            found = 5
        else:
            if a < angs_sorted[0]:
                found = 5
        edge_id[v] = found
    # distances to each edge side (static BFS)
    INF = 10**9
    dist_edge = {v: [INF]*6 for v in valid_list}
    for e in range(6):
        sources = [v for v in valid_list if edge_id.get(v) == e]
        if not sources:
            continue
        dq = deque()
        seen = set()
        for s in sources:
            dist_edge[s][e] = 0
            dq.append(s)
            seen.add(s)
        while dq:
            cur = dq.popleft()
            d = dist_edge[cur][e]
            for nb in neigh[cur]:
                if nb not in seen:
                    seen.add(nb)
                    dist_edge[nb][e] = d+1
                    dq.append(nb)
    # distances to each corner
    dist_corner = {v: [INF]*6 for v in valid_list}
    for idx, cor in enumerate(corners_sorted):
        dq = deque([cor])
        seen = {cor}
        dist_corner[cor][idx] = 0
        while dq:
            cur = dq.popleft()
            d = dist_corner[cur][idx]
            for nb in neigh[cur]:
                if nb not in seen:
                    seen.add(nb)
                    dist_corner[nb][idx] = d+1
                    dq.append(nb)
    topo = {
        'N': N, 'neigh': neigh, 'valid_list': valid_list, 'valid_set': valid_set,
        'corners': corners_sorted, 'corners_set': set(corners_sorted),
        'edge_cells_set': edge_cells_set, 'edge_id': edge_id,
        'dist_edge': dist_edge, 'dist_corner': dist_corner,
        'center_cell': center_cell, 'cr': cr, 'cc': cc_, 'mode': best
    }
    return topo

def _get_topo(static_key, static_valid):
    if static_key in _CACHE:
        return _CACHE[static_key]
    t = _build_topo(static_valid)
    _CACHE[static_key] = t
    return t

def _is_win(player_set, topo):
    if len(player_set) < 2:
        return False
    neigh = topo['neigh']
    corners_set = topo['corners_set']
    edge_id = topo['edge_id']
    visited = set()
    for start in player_set:
        if start in visited:
            continue
        # BFS component
        stack = [start]
        visited.add(start)
        comp = [start]
        idx = 0
        edge_t = set()
        corn_t = 0
        if start in corners_set:
            corn_t += 1
        elif start in edge_id:
            edge_t.add(edge_id[start])
        while idx < len(comp):
            cur = comp[idx]; idx += 1
            for nb in neigh.get(cur, ()):
                if nb in player_set and nb not in visited:
                    visited.add(nb)
                    comp.append(nb)
                    if nb in corners_set:
                        corn_t += 1
                    elif nb in edge_id:
                        edge_t.add(edge_id[nb])
        if corn_t >= 2:
            return True
        if len(edge_t) >= 3:
            return True
    if len(player_set) >= 6:
        edge_cells = topo['edge_cells_set']
        seen = set()
        q = deque()
        for c in edge_cells:
            if c not in player_set and c not in seen:
                seen.add(c)
                q.append(c)
        while q:
            cur = q.popleft()
            for nb in neigh.get(cur, ()):
                if nb not in player_set and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        total_non = len(topo['valid_list']) - len(player_set)
        if len(seen) < total_non:
            return True
    return False

def _potential(player_set, topo):
    if not player_set:
        return -50.0
    neigh = topo['neigh']
    edge_id = topo['edge_id']
    corners_set = topo['corners_set']
    dist_edge = topo['dist_edge']
    dist_corner = topo['dist_corner']
    visited = set()
    best = -1e18
    for start in player_set:
        if start in visited:
            continue
        comp = [start]
        visited.add(start)
        idx = 0
        while idx < len(comp):
            cur = comp[idx]; idx += 1
            for nb in neigh.get(cur, ()):
                if nb in player_set and nb not in visited:
                    visited.add(nb)
                    comp.append(nb)
        es = set()
        ccnt = 0
        for c in comp:
            if c in corners_set:
                ccnt += 1
            elif c in edge_id:
                es.add(edge_id[c])
        ec = len(es)
        sz = len(comp)
        # min dists to edges
        # init
        min_e = [10**9]*6
        min_c = [10**9]*6
        for c in comp:
            de = dist_edge.get(c)
            dc = dist_corner.get(c)
            if de:
                for e in range(6):
                    d = de[e]
                    if d < min_e[e]:
                        min_e[e] = d
            if dc:
                for k in range(6):
                    d = dc[k]
                    if d < min_c[k]:
                        min_c[k] = d
        fork_cost = 0
        if ec < 3:
            uncovered = [min_e[e] for e in range(6) if e not in es]
            uncovered = [d if d < 10**8 else 12 for d in uncovered]
            uncovered.sort()
            fork_cost = sum(uncovered[:3-ec])
        bridge_cost = 0
        if ccnt < 2:
            # need distinct corners; approx use smallest distances
            # exclude corners already occupied? min_c for those is 0, but they are occupied so ignore?
            # collect distances to corners not in comp
            comp_set = set(comp)
            cand = []
            for k, cor in enumerate(topo['corners']):
                if cor in comp_set:
                    continue
                d = min_c[k]
                if d >= 10**8:
                    d = 12
                cand.append(d)
            cand.sort()
            need = 2 - ccnt
            if len(cand) >= need:
                bridge_cost = sum(cand[:need])
            else:
                bridge_cost = 12*need
        score = ec*20.0 + ccnt*30.0 - fork_cost*3.0 - bridge_cost*3.0 + sz*0.4
        if score > best:
            best = score
    return best

def _eval_board(me_set, opp_set, topo):
    a = _potential(me_set, topo)
    b = _potential(opp_set, topo)
    return a - b

def _score_move(mv, P_set, O_set, P_edge_set, O_edge_set, P_cor_set, topo):
    neigh = topo['neigh']
    corners_set = topo['corners_set']
    edge_id = topo['edge_id']
    dist_edge = topo['dist_edge']
    dist_corner = topo['dist_corner']
    cr = topo['cr']; cc_ = topo['cc']
    my_n = 0
    opp_n = 0
    for nb in neigh.get(mv, ()):
        if nb in P_set:
            my_n += 1
        elif nb in O_set:
            opp_n += 1
    s = my_n*5.0 + opp_n*4.0
    if my_n >= 2:
        s += (my_n-1)*6.0
    if opp_n >= 2:
        s += (opp_n-1)*6.0
    dcen = math.hypot(mv[0]-cr, mv[1]-cc_)
    s += (12.0 - dcen)*0.5
    if mv in corners_set:
        s += 4.0
    elif mv in edge_id:
        s += 2.0
    if len(P_edge_set) < 3:
        try:
            d = min(dist_edge[mv][e] for e in range(6) if e not in P_edge_set)
            if d > 100:
                d = 12
            s += (15 - d)*1.0
        except Exception:
            pass
    # corner proximity for P
    try:
        dc = dist_corner[mv]
        dm = min(dc)
        if dm > 100:
            dm = 12
        if len(P_cor_set) < 2:
            s += (15 - dm)*0.7
    except Exception:
        pass
    if len(O_edge_set) < 3:
        try:
            d2 = min(dist_edge[mv][e] for e in range(6) if e not in O_edge_set)
            if d2 > 100:
                d2 = 12
            s += (15 - d2)*0.9
        except Exception:
            pass
    return s

def policy(me, opp, valid_mask) -> tuple[int, int]:
    t0 = time.time()
    try:
        # normalize valid mask to numpy bool if possible
        if _HAS_NP and isinstance(valid_mask, np.ndarray):
            vm_np = np.asarray(valid_mask, dtype=bool)
            N = int(vm_np.shape[0])
        else:
            # list-like
            try:
                N = len(valid_mask)
                if _HAS_NP:
                    vm_np = np.asarray(valid_mask, dtype=bool)
                else:
                    vm_np = valid_mask
            except Exception:
                # fallback: return 0,0
                return (0, 0)
        # normalize sets
        try:
            me_list = list(me) if me is not None else []
        except Exception:
            me_list = []
        try:
            opp_list = list(opp) if opp is not None else []
        except Exception:
            opp_list = []
        me_set = set()
        for x in me_list:
            try:
                me_set.add((int(x[0]), int(x[1])))
            except Exception:
                continue
        opp_set = set()
        for x in opp_list:
            try:
                opp_set.add((int(x[0]), int(x[1])))
            except Exception:
                continue
        # static valid = vm True union occupied (handles masks that hide stones)
        if _HAS_NP and isinstance(vm_np, np.ndarray):
            static_arr = vm_np.copy()
            for (r, c) in me_set | opp_set:
                if 0 <= r < N and 0 <= c < N:
                    static_arr[r, c] = True
            key = (N, static_arr.tobytes())
            topo = _get_topo(key, static_arr)
        else:
            # pure python path
            static_py = [row[:] if isinstance(row, list) else list(row) for row in vm_np] if isinstance(vm_np, list) else vm_np
            key = (N, tuple(sorted(me_set))[:0])  # dummy, rebuild each time
            # build with vm_np directly plus occupied
            # create bool matrix
            import copy
            # fallback: use vm_np as is
            topo = _build_topo(vm_np)
        neigh = topo['neigh']
        valid_list = topo['valid_list']
        occupied = me_set | opp_set
        empty = [v for v in valid_list if v not in occupied]
        if not empty:
            # no move? return something (will be illegal but unavoidable)
            return (0, 0)
        empty_set = set(empty)
        if len(me_set) == 0 and len(opp_set) == 0:
            c = topo['center_cell']
            return (int(c[0]), int(c[1]))
        def adj_empty(pset):
            s = set()
            for p in pset:
                for nb in neigh.get(p, ()):
                    if nb in empty_set:
                        s.add(nb)
            return s
        my_adj = adj_empty(me_set) if me_set else set(empty)
        opp_adj = adj_empty(opp_set) if opp_set else set()
        # immediate win
        # order my_adj by heuristic-ish (neighbors count) to find fast win
        for m in my_adj:
            if time.time() - t0 > 0.85:
                break
            if _is_win(me_set | {m}, topo):
                return (int(m[0]), int(m[1]))
        # block
        threats = []
        for o in opp_adj:
            if time.time() - t0 > 0.9:
                break
            if _is_win(opp_set | {o}, topo):
                threats.append(o)
        if threats:
            if len(threats) == 1:
                return (int(threats[0][0]), int(threats[0][1]))
            # pick best threat by own heuristic
            edge_id = topo['edge_id']
            my_edge_set = set(edge_id[c] for c in me_set if c in edge_id)
            opp_edge_set = set(edge_id[c] for c in opp_set if c in edge_id)
            my_cor = set(c for c in me_set if c in topo['corners_set'])
            best_t = threats[0]
            best_s = -1e18
            for t in threats:
                s = _score_move(t, me_set, opp_set, my_edge_set, opp_edge_set, my_cor, topo)
                if s > best_s:
                    best_s = s
                    best_t = t
            return (int(best_t[0]), int(best_t[1]))
        # heuristic search
        edge_id = topo['edge_id']
        my_edge_set = set(edge_id[c] for c in me_set if c in edge_id)
        opp_edge_set = set(edge_id[c] for c in opp_set if c in edge_id)
        my_cor = set(c for c in me_set if c in topo['corners_set'])
        opp_cor = set(c for c in opp_set if c in topo['corners_set'])
        # score all empty (limit to distance-2 vicinity if too many? score all, it's cheap)
        scored = []
        for e in empty:
            s = _score_move(e, me_set, opp_set, my_edge_set, opp_edge_set, my_cor, topo)
            scored.append((s, e))
        scored.sort(reverse=True, key=lambda x: x[0])
        K1 = 10 if len(empty) > 20 else len(empty)
        cand_my = [e for _, e in scored[:K1]]
        # if very early, ensure center included
        best_move = cand_my[0]
        best_val = -1e18
        # precompute for opp reply scoring needs updated sets per my move
        for m in cand_my:
            if time.time() - t0 > 0.88:
                break
            me2 = me_set | {m}
            # update edge sets for me2
            me2_edge = set(my_edge_set)
            if m in edge_id:
                me2_edge.add(edge_id[m])
            me2_cor = set(my_cor)
            if m in topo['corners_set']:
                me2_cor.add(m)
            # opp candidates: score empty\{m} from opp perspective
            # to save time, reuse scored order but rescore top subset
            # generate opp scored list over top 30 of scored + neighbors of m
            subset = set(e for _, e in scored[:30])
            subset.add(m)
            # add neighbors of m
            for nb in neigh.get(m, ()):
                if nb in empty_set and nb != m:
                    subset.add(nb)
            subset.discard(m)
            opp_scored = []
            for e in subset:
                if e not in empty_set or e == m:
                    continue
                s = _score_move(e, opp_set, me2, opp_edge_set, me2_edge, opp_cor, topo)
                opp_scored.append((s, e))
            opp_scored.sort(reverse=True, key=lambda x: x[0])
            K2 = 8
            opp_cands = [e for _, e in opp_scored[:K2]]
            if not opp_cands:
                v = _eval_board(me2, opp_set, topo)
                if v > best_val:
                    best_val = v
                    best_move = m
                continue
            worst = 1e18
            for o in opp_cands:
                if time.time() - t0 > 0.92:
                    break
                if _is_win(opp_set | {o}, topo):
                    worst = -1e15
                    break
                v = _eval_board(me2, opp_set | {o}, topo)
                if v < worst:
                    worst = v
            if worst > best_val:
                best_val = worst
                best_move = m
        return (int(best_move[0]), int(best_move[1]))
    except Exception:
        pass
    # ultimate fallback: scan valid_mask for legal empty
    try:
        if _HAS_NP and isinstance(valid_mask, np.ndarray):
            N = valid_mask.shape[0]
            occ = set()
            try:
                for x in me:
                    occ.add((int(x[0]), int(x[1])))
                for x in opp:
                    occ.add((int(x[0]), int(x[1])))
            except Exception:
                pass
            for r in range(N):
                for c in range(N):
                    if bool(valid_mask[r, c]) and (r, c) not in occ:
                        return (r, c)
        else:
            N = len(valid_mask)
            occ = set()
            try:
                for x in me:
                    occ.add((int(x[0]), int(x[1])))
                for x in opp:
                    occ.add((int(x[0]), int(x[1])))
            except Exception:
                pass
            for r in range(N):
                for c in range(N):
                    if bool(valid_mask[r][c]) and (r, c) not in occ:
                        return (r, c)
    except Exception:
        pass
    return (0, 0)
