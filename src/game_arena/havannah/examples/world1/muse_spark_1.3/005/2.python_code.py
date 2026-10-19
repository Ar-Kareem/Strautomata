
import random

_INFO = None

def _popcnt(x):
    return bin(x).count("1")

def _get_info(valid_mask):
    global _INFO
    # extract valid cells
    try:
        import numpy as _np
        _arr = _np.asarray(valid_mask)
        if _arr.ndim == 2:
            nR, nC = _arr.shape
            valid_list = [(r, c) for r in range(nR) for c in range(nC) if bool(_arr[r, c])]
            N = nR
        else:
            raise Exception("fallback")
    except Exception:
        nR = len(valid_mask)
        nC = len(valid_mask[0]) if nR else 0
        N = nR
        valid_list = []
        for r in range(nR):
            row = valid_mask[r]
            for c in range(nC):
                try:
                    v = bool(row[c])
                except Exception:
                    v = False
                if v:
                    valid_list.append((r, c))
    valid_set = set(valid_list)
    if _INFO is not None and _INFO.get("valid_set") == valid_set:
        return _INFO
    # adjacency with column parity (even-q)
    adj = {}
    for (r, c) in valid_list:
        if c & 1:  # odd -> side neighbours up
            offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]
        else:  # even -> side neighbours down
            offs = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1)]
        lst = []
        for dr, dc in offs:
            nr, nc = r + dr, c + dc
            if (nr, nc) in valid_set:
                lst.append((nr, nc))
        adj[(r, c)] = lst
    # cube coords raw
    raw = {}
    sx = sy = sz = 0
    for (r, c) in valid_list:
        x = c
        z = r - (c + (c & 1)) // 2
        y = -x - z
        raw[(r, c)] = (x, y, z)
        sx += x; sy += y; sz += z
    n = max(1, len(valid_list))
    mx = sx / n; my = sy / n; mz = sz / n
    cube = {}
    maxd = 0
    for k, (x, y, z) in raw.items():
        xc = int(round(x - mx)); yc = int(round(y - my)); zc = int(round(z - mz))
        cube[k] = (xc, yc, zc)
        m = max(abs(xc), abs(yc), abs(zc))
        if m > maxd:
            maxd = m
    S = maxd + 1
    corners = []
    edge_id = {}
    for k in valid_list:
        edge_id[k] = -1
    corner_idx = {}
    for k in valid_list:
        xc, yc, zc = cube[k]
        m = max(abs(xc), abs(yc), abs(zc))
        if m == S - 1:
            cnt = (1 if abs(xc) == S - 1 else 0) + (1 if abs(yc) == S - 1 else 0) + (1 if abs(zc) == S - 1 else 0)
            if cnt >= 2:
                corner_idx[k] = len(corners)
                corners.append(k)
            else:
                if xc == S - 1:
                    eid = 0
                elif xc == -(S - 1):
                    eid = 1
                elif yc == S - 1:
                    eid = 2
                elif yc == -(S - 1):
                    eid = 3
                elif zc == S - 1:
                    eid = 4
                else:
                    eid = 5
                edge_id[k] = eid
    # center
    center = valid_list[0] if valid_list else (0, 0)
    best = 10 ** 9
    for k in valid_list:
        xc, yc, zc = cube[k]
        d = max(abs(xc), abs(yc), abs(zc))
        if d < best:
            best = d
            center = k
    info = {
        "valid_set": valid_set,
        "valid_list": valid_list,
        "adj": adj,
        "cube": cube,
        "S": S,
        "corners": corners,
        "corner_idx": corner_idx,
        "edge_id": edge_id,
        "center": center,
    }
    _INFO = info
    return info

def _build_dsu(player_set, adj, edge_id, corner_idx):
    parent = {}
    sz = {}
    emask = {}
    cmask = {}
    for c in player_set:
        parent[c] = c
        sz[c] = 1
        e = edge_id.get(c, -1)
        em = (1 << e) if e != -1 else 0
        emask[c] = em
        ci = corner_idx.get(c, -1)
        cm = (1 << ci) if ci != -1 else 0
        cmask[c] = cm
    def find(x):
        p = parent
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x
    has_cycle = False
    for c in player_set:
        for nb in adj.get(c, ()):
            if nb in parent and nb > c:
                ra = find(c); rb = find(nb)
                if ra == rb:
                    has_cycle = True
                else:
                    if sz[ra] < sz[rb]:
                        ra, rb = rb, ra
                    parent[rb] = ra
                    sz[ra] += sz[rb]
                    emask[ra] |= emask[rb]
                    cmask[ra] |= cmask[rb]
    # compress roots
    roots = {}
    for c in player_set:
        r = find(c)
        roots[c] = r
    return {
        "parent": parent,
        "sz": sz,
        "emask": emask,
        "cmask": cmask,
        "roots": roots,
        "find": find,
        "has_cycle": has_cycle,
    }

def _would_win(cell, player_set, dsu, adj, edge_id, corner_idx):
    nbs = [nb for nb in adj.get(cell, ()) if nb in player_set]
    if not nbs:
        return False
    find = dsu["find"]
    rset = set()
    for nb in nbs:
        try:
            rset.add(find(nb))
        except Exception:
            pass
    # ring: two neighbours already connected
    if len(rset) < len(nbs):
        return True
    em = 0
    cm = 0
    emd = dsu["emask"]; cmd = dsu["cmask"]
    for r in rset:
        em |= emd.get(r, 0)
        cm |= cmd.get(r, 0)
    e = edge_id.get(cell, -1)
    if e != -1:
        em |= (1 << e)
    ci = corner_idx.get(cell, -1)
    if ci != -1:
        cm |= (1 << ci)
    if _popcnt(em) >= 3:
        return True
    if _popcnt(cm) >= 2:
        return True
    return False

def _hex_dist(a, b, cube):
    if a not in cube or b not in cube:
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
    x1, y1, z1 = cube[a]
    x2, y2, z2 = cube[b]
    return (abs(x1-x2) + abs(y1-y2) + abs(z1-z2)) // 2

def policy(me, opp, valid_mask) -> tuple[int, int]:
    try:
        info = _get_info(valid_mask)
        adj = info["adj"]
        valid_set = info["valid_set"]
        valid_list = info["valid_list"]
        edge_id = info["edge_id"]
        corner_idx = info["corner_idx"]
        cube = info["cube"]
        center = info["center"]
        me_set = set(me) if me is not None else set()
        opp_set = set(opp) if opp is not None else set()
        me_set = set([t for t in me_set if t in valid_set])
        opp_set = set([t for t in opp_set if t in valid_set])
        occupied = me_set | opp_set
        empty_set = set([c for c in valid_list if c not in occupied])
        if not empty_set:
            # no move, return anything valid
            return valid_list[0] if valid_list else (0, 0)
        def _legal(c):
            return c in empty_set
        # opening
        if len(me_set) == 0 and len(opp_set) == 0:
            if center in empty_set:
                return center
        if len(me_set) == 0 and len(occupied) < 3:
            if center in empty_set:
                return center
            # nearest to center
            best = None; bd = 10**9
            for c in empty_set:
                d = _hex_dist(c, center, cube)
                if d < bd:
                    bd = d; best = c
            return best
        # DSUs
        dsu_me = _build_dsu(me_set, adj, edge_id, corner_idx)
        dsu_opp = _build_dsu(opp_set, adj, edge_id, corner_idx)
        # neighbour empties
        def neigh_empty(base_set):
            s = set()
            for c in base_set:
                for nb in adj.get(c, ()):
                    if nb in empty_set:
                        s.add(nb)
            return s
        cand_me = neigh_empty(me_set)
        cand_opp = neigh_empty(opp_set)
        # immediate win for me
        if cand_me:
            for c in cand_me:
                if _would_win(c, me_set, dsu_me, adj, edge_id, corner_idx):
                    return c
        else:
            # isolated but check all empty (rare)
            if len(me_set) < 5:
                for c in empty_set:
                    if _would_win(c, me_set, dsu_me, adj, edge_id, corner_idx):
                        return c
        # opponent immediate wins -> block
        opp_wins = []
        for c in cand_opp:
            if _would_win(c, opp_set, dsu_opp, adj, edge_id, corner_idx):
                opp_wins.append(c)
        if opp_wins:
            if len(opp_wins) == 1:
                return opp_wins[0]
            # multiple: pick best by heuristic among them
            best = opp_wins[0]; bs = -10**18
            for c in opp_wins:
                s = 0
                # prefer also adjacent to me / central
                nm = sum(1 for nb in adj.get(c, ()) if nb in me_set)
                s += nm * 5 - _hex_dist(c, center, cube) * 0.1
                if s > bs:
                    bs = s; best = c
            return best
        # candidate pool for tactics / heuristic
        pool = cand_me | cand_opp
        # add center area if pool small
        if len(pool) < 8:
            # add empties near center
            cl = sorted(list(empty_set), key=lambda x: _hex_dist(x, center, cube))[:8]
            for c in cl:
                pool.add(c)
        if not pool:
            pool = set(list(empty_set)[:20])
        pool = list(pool)
        total = len(me_set) + len(opp_set)
        # scoring function
        def score_move(m):
            nbs_me = [nb for nb in adj.get(m, ()) if nb in me_set]
            nbs_opp = [nb for nb in adj.get(m, ()) if nb in opp_set]
            find_me = dsu_me["find"]
            rset = set()
            for nb in nbs_me:
                try:
                    rset.add(find_me(nb))
                except Exception:
                    pass
            em = 0; cm = 0; msz = 1
            for r in rset:
                em |= dsu_me["emask"].get(r, 0)
                cm |= dsu_me["cmask"].get(r, 0)
                msz += dsu_me["sz"].get(r, 0) - 1 if False else 0
            # size sum
            ssum = 0
            for r in rset:
                ssum += dsu_me["sz"].get(r, 0)
            e = edge_id.get(m, -1)
            if e != -1:
                em |= (1 << e)
            ci = corner_idx.get(m, -1)
            if ci != -1:
                cm |= (1 << ci)
            ec = _popcnt(em); cc = _popcnt(cm)
            sc = 0.0
            sc += len(nbs_me) * 3.0
            if len(rset) >= 2:
                sc += (len(rset) - 1) * 10.0 + ssum * 0.4
            else:
                sc += ssum * 0.2
            if ec == 1:
                sc += 4
            elif ec == 2:
                sc += 22
            elif ec >= 3:
                sc += 1000
            if cc == 1:
                sc += 14
            elif cc >= 2:
                sc += 1000
            if len(nbs_me) >= 2:
                sc += 2.0
            if nbs_opp:
                find_o = dsu_opp["find"]
                oset = set()
                for nb in nbs_opp:
                    try:
                        oset.add(find_o(nb))
                    except Exception:
                        pass
                omax_e = 0; omax_c = 0; osum = 0
                for r in oset:
                    omax_e = max(omax_e, _popcnt(dsu_opp["emask"].get(r, 0)))
                    omax_c = max(omax_c, _popcnt(dsu_opp["cmask"].get(r, 0)))
                    osum += dsu_opp["sz"].get(r, 0)
                sc += len(nbs_opp) * 2.0 + omax_e * 5.0 + omax_c * 7.0 + osum * 0.25
                # occupying edge/corner denies opponent
                if e != -1:
                    sc += 3
                if ci != -1:
                    sc += 5
            d = _hex_dist(m, center, cube)
            if total < 24:
                sc += -d * 0.9
            elif total < 60:
                sc += -d * 0.15
            else:
                sc += d * 0.25
            sc += ((m[0] * 7 + m[1] * 13) % 7) * 0.05
            return sc
        scored = [(score_move(m), m) for m in pool]
        scored.sort(reverse=True, key=lambda x: x[0])
        top = [m for _, m in scored[:20]]
        # double-threat attack: mate in 2
        # for each m, build dsu after and count winning replies
        for m in top:
            new_set = me_set | {m}
            dsu_after = _build_dsu(new_set, adj, edge_id, corner_idx)
            # winning replies = neighbour empties of new_set
            wr = set()
            for c in new_set:
                for nb in adj.get(c, ()):
                    if nb in empty_set and nb != m:
                        wr.add(nb)
            cnt = 0
            for w in wr:
                if _would_win(w, new_set, dsu_after, adj, edge_id, corner_idx):
                    cnt += 1
                    if cnt >= 2:
                        break
            if cnt >= 2:
                return m
        # defensive: opponent double-threat creation
        # find opp moves that would create >=2 wins
        danger = []
        opp_pool = list(cand_opp) if cand_opp else list(empty_set)[:20]
        # limit opp_pool by proximity score
        if len(opp_pool) > 20:
            # keep those near opp components with progress
            def oscore(m):
                n = sum(1 for nb in adj.get(m, ()) if nb in opp_set)
                return n - _hex_dist(m, center, cube) * 0.05
            opp_pool = sorted(opp_pool, key=oscore, reverse=True)[:20]
        for o in opp_pool:
            if o not in empty_set:
                continue
            new_o = opp_set | {o}
            dsu_o_after = _build_dsu(new_o, adj, edge_id, corner_idx)
            wr = set()
            for c in new_o:
                for nb in adj.get(c, ()):
                    if nb in empty_set and nb != o:
                        wr.add(nb)
            cnt = 0
            for w in wr:
                if _would_win(w, new_o, dsu_o_after, adj, edge_id, corner_idx):
                    cnt += 1
                    if cnt >= 2:
                        break
            if cnt >= 2:
                danger.append(o)
        if danger:
            # must block creation cell; if multiple, pick highest scored
            best = None; bs = -10**18
            smap = {m: s for s, m in scored}
            for dcell in danger:
                s = smap.get(dcell, score_move(dcell) if dcell in empty_set else -10**9)
                if s > bs:
                    bs = s; best = dcell
            if best is not None and best in empty_set:
                return best
        # otherwise best heuristic
        for _, m in scored:
            if m in empty_set:
                return m
        # fallback
        for c in valid_list:
            if c in empty_set:
                return c
        return valid_list[0]
    except Exception:
        try:
            empt = []
            # try to parse valid_mask
            try:
                import numpy as _np2
                _a = _np2.asarray(valid_mask)
                if _a.ndim == 2:
                    occ = set(me) | set(opp)
                    for r in range(_a.shape[0]):
                        for cc in range(_a.shape[1]):
                            if bool(_a[r, cc]) and (r, cc) not in occ:
                                empt.append((r, cc))
                    if empt:
                        return empt[0]
            except Exception:
                pass
            occ = set(me) | set(opp)
            for r in range(len(valid_mask)):
                for cc in range(len(valid_mask[r])):
                    if valid_mask[r][cc] and (r, cc) not in occ:
                        return (r, cc)
        except Exception:
            pass
        return (0, 0)
