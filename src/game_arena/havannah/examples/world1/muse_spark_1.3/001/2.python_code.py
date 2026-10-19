
import time
from collections import deque

_BOARD_CACHE = {}

def _build_nbr(valid_set, N, flip):
    nbr = [[] for _ in range(N*N)]
    for idx in valid_set:
        r = idx // N
        c = idx % N
        lst = []
        # same column
        if r-1 >= 0:
            nidx = (r-1)*N+c
            if nidx in valid_set:
                lst.append(nidx)
        if r+1 < N:
            nidx = (r+1)*N+c
            if nidx in valid_set:
                lst.append(nidx)
        # up-biased if (odd col) xor flip == False? example col1 odd is up
        # flip==False => odd up, even down
        up = ((c & 1) == 1) ^ flip
        if up:
            drs = (-1, 0)
        else:
            drs = (0, 1)
        for dc in (-1, 1):
            nc = c+dc
            if nc < 0 or nc >= N:
                continue
            for dr in drs:
                nr = r+dr
                if nr < 0 or nr >= N:
                    continue
                nidx = nr*N+nc
                if nidx in valid_set:
                    lst.append(nidx)
        nbr[idx] = lst
    return nbr

def _get_info(valid_mask):
    # N
    try:
        N = int(valid_mask.shape[0])
    except Exception:
        N = len(valid_mask)
    valid_list = []
    for r in range(N):
        for c in range(N):
            try:
                v = valid_mask[r][c]
            except Exception:
                v = False
            # numpy bool
            if v is True or v == True or (hasattr(v, '__bool__') and bool(v)):
                # need to handle numpy True
                valid_list.append(r*N+c)
            elif v:
                # just in case
                try:
                    if bool(v):
                        if (r*N+c) not in valid_list:
                            pass
                except:
                    pass
    # deduplicate (above logic may double) - rebuild cleanly
    # rebuild correctly:
    valid_list = []
    for r in range(N):
        for c in range(N):
            try:
                vv = valid_mask[r][c]
                is_valid = bool(vv)
            except Exception:
                is_valid = False
            if is_valid:
                valid_list.append(r*N+c)
    valid_set = set(valid_list)
    key = (N, tuple(sorted(valid_list)))
    if key in _BOARD_CACHE:
        return _BOARD_CACHE[key]
    # try both flips, prefer flip=False (odd up) if it gives 6 corners
    best = None
    for flip in (False, True):
        nbr = _build_nbr(valid_set, N, flip)
        corners = [idx for idx in valid_list if len(nbr[idx]) == 3]
        if len(corners) == 6 and flip is False:
            best = (nbr, corners, flip)
            break
        if len(corners) == 6 and best is None:
            best = (nbr, corners, flip)
    if best is None:
        # fallback: use flip False
        nbr = _build_nbr(valid_set, N, False)
        corners = [idx for idx in valid_list if len(nbr[idx]) == 3]
        flip = False
    else:
        nbr, corners, flip = best
    border_set = set(idx for idx in valid_list if len(nbr[idx]) < 6)
    corner_set = set(corners)
    corner_id = {idx:i for i, idx in enumerate(corners)}
    edge_cells = [idx for idx in border_set if idx not in corner_set]
    edge_set = set(edge_cells)
    edge_id = {}
    comp_cnt = 0
    visited_e = set()
    for s in edge_cells:
        if s in visited_e:
            continue
        # bfs component
        stack = [s]
        visited_e.add(s)
        qpos = 0
        while qpos < len(stack):
            u = stack[qpos]; qpos += 1
            edge_id[u] = comp_cnt
            for v in nbr[u]:
                if v in edge_set and v not in visited_e:
                    visited_e.add(v)
                    stack.append(v)
        comp_cnt += 1
    # center: closest valid to middle
    mr = N//2; mc = N//2
    center_idx = valid_list[0]
    bestd = 10**9
    for idx in valid_list:
        r = idx//N; c = idx%N
        d = (r-mr)*(r-mr)+(c-mc)*(c-mc)
        if d < bestd:
            bestd = d; center_idx = idx
    # distances from center (hex steps)
    dist = {center_idx:0}
    dq = deque([center_idx])
    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in nbr[u]:
            if v not in dist:
                dist[v] = du+1
                dq.append(v)
    maxd = 1
    for idx in valid_list:
        if idx not in dist:
            dist[idx] = 20
        if dist[idx] > maxd and dist[idx] < 20:
            maxd = dist[idx]
    info = {
        'N': N,
        'valid_list': valid_list,
        'valid_set': valid_set,
        'nbr': nbr,
        'border_set': border_set,
        'corner_list': corners,
        'corner_id': corner_id,
        'edge_id': edge_id,
        'center': center_idx,
        'dist': dist,
        'maxd': maxd if maxd>0 else 10,
        'flip': flip,
    }
    _BOARD_CACHE[key] = info
    return info

def _has_bridge_fork(p_set, info):
    if len(p_set) < 2:
        return False
    nbr = info['nbr']
    edge_id = info['edge_id']
    corner_id = info['corner_id']
    visited = set()
    for s in p_set:
        if s in visited:
            continue
        stack = [s]
        visited.add(s)
        edges = set()
        corners = set()
        pos = 0
        # quick check single cell corner/edge
        while pos < len(stack):
            u = stack[pos]; pos += 1
            eid = edge_id.get(u)
            if eid is not None:
                edges.add(eid)
                if len(edges) >= 3:
                    return True
            cid = corner_id.get(u)
            if cid is not None:
                corners.add(cid)
                if len(corners) >= 2:
                    return True
            for v in nbr[u]:
                if v in p_set and v not in visited:
                    visited.add(v)
                    stack.append(v)
        if len(edges) >= 3 or len(corners) >= 2:
            return True
    return False

def _has_ring(p_set, info):
    if len(p_set) < 6:
        return False
    valid_set = info['valid_set']
    border_set = info['border_set']
    nbr = info['nbr']
    # flood from border non-player
    visited = set()
    dq = deque()
    for b in border_set:
        if b not in p_set and b not in visited:
            visited.add(b)
            dq.append(b)
    while dq:
        u = dq.popleft()
        for v in nbr[u]:
            if v not in p_set and v not in visited:
                visited.add(v)
                dq.append(v)
    # number of non-player cells
    num_non = len(valid_set) - len(p_set)
    if len(visited) < num_non:
        return True
    return False

def _is_win(p_set, info):
    if _has_bridge_fork(p_set, info):
        return True
    if _has_ring(p_set, info):
        return True
    return False

def _score_for(p_set, info):
    if not p_set:
        return 0.0
    nbr = info['nbr']
    edge_id = info['edge_id']
    corner_id = info['corner_id']
    dist = info['dist']
    maxd = info['maxd']
    visited = set()
    total = 0.0
    for s in p_set:
        if s in visited:
            continue
        stack = [s]
        visited.add(s)
        pos = 0
        edges = set()
        corners = set()
        sum_c = 0.0
        while pos < len(stack):
            u = stack[pos]; pos += 1
            eid = edge_id.get(u)
            if eid is not None:
                edges.add(eid)
            cid = corner_id.get(u)
            if cid is not None:
                corners.add(cid)
            d = dist.get(u, maxd)
            # central weight: closer is better
            w = (maxd - d + 2) * 0.6
            if w < 0:
                w = 0
            sum_c += w
            for v in nbr[u]:
                if v in p_set and v not in visited:
                    visited.add(v)
                    stack.append(v)
        size = len(stack)
        g = size*2.0 + size*size*0.18 + sum_c*0.5
        ne = len(edges); nc = len(corners)
        if ne == 1:
            g += 8
        elif ne == 2:
            g += 130
        elif ne >= 3:
            g += 10000
        if nc == 1:
            g += 38
        elif nc >= 2:
            g += 10000
        # edge+corner synergy
        if ne >= 1 and nc >= 1:
            g += 12
        total += g
    return total

def _evaluate(me_set, opp_set, info):
    return _score_for(me_set, info) - _score_for(opp_set, info)

def policy(me, opp, valid_mask) -> tuple[int, int]:
    try:
        t0 = time.time()
        info = _get_info(valid_mask)
        N = info['N']
        nbr = info['nbr']
        dist = info['dist']
        valid_list = info['valid_list']
        valid_set = info['valid_set']
        me_set = set(r*N+c for (r, c) in me)
        opp_set = set(r*N+c for (r, c) in opp)
        # keep only valid (safety)
        me_set = set(x for x in me_set if x in valid_set)
        opp_set = set(x for x in opp_set if x in valid_set)
        empty_set = set(x for x in valid_list if x not in me_set and x not in opp_set)
        if not empty_set:
            return (0, 0)
        def to_rc(idx):
            return (idx//N, idx % N)
        # opening: first move play center
        if len(me_set)+len(opp_set) < 2:
            c0 = info['center']
            if c0 in empty_set:
                return to_rc(c0)
            # nearest to center
            best = None; bestd = 10**9
            for e in empty_set:
                d = dist.get(e, 99)
                if d < bestd:
                    bestd = d; best = e
            return to_rc(best)
        # adjacency sets
        adj_me = set()
        for s in me_set:
            for nb in nbr[s]:
                if nb in empty_set:
                    adj_me.add(nb)
        adj_opp = set()
        for s in opp_set:
            for nb in nbr[s]:
                if nb in empty_set:
                    adj_opp.add(nb)
        # 1. immediate win (only need to check adjacent)
        # order by center distance to be deterministic
        cand_win = sorted(adj_me, key=lambda x: dist.get(x, 99)) if adj_me else []
        for e in cand_win:
            me_set.add(e)
            w = _is_win(me_set, info)
            me_set.remove(e)
            if w:
                return to_rc(e)
            if time.time()-t0 > 0.85:
                break
        # if no adj win but very few stones, also check all? skip for speed
        # 2. block opponent immediate wins
        opp_wins = []
        cand_opp = sorted(adj_opp, key=lambda x: dist.get(x, 99)) if adj_opp else []
        for e in cand_opp:
            opp_set.add(e)
            w = _is_win(opp_set, info)
            opp_set.remove(e)
            if w:
                opp_wins.append(e)
            if time.time()-t0 > 0.9:
                break
        if len(opp_wins) == 1:
            return to_rc(opp_wins[0])
        if len(opp_wins) > 1:
            # try to find a move that blocks and also creates threat? just block first
            # prefer block closest to our stones / center
            # if one of opp wins is also our win? already checked none
            # return the one with best eval after blocking
            best_e = opp_wins[0]
            best_s = -1e18
            for e in opp_wins:
                me_set.add(e)
                sc = _evaluate(me_set, opp_set, info)
                me_set.remove(e)
                if sc > best_s:
                    best_s = sc; best_e = e
            return to_rc(best_e)
        # 3. heuristic search
        occupied = me_set | opp_set
        cand_set = set()
        cand_set.update(adj_me)
        cand_set.update(adj_opp)
        # 2-hop expansion
        # expand one more hop from adj cells
        extra = set()
        for s in list(occupied):
            for nb in nbr[s]:
                for nb2 in nbr[nb]:
                    if nb2 in empty_set:
                        extra.add(nb2)
        cand_set.update(extra)
        if len(cand_set) < 15:
            # add central empties
            central = sorted(empty_set, key=lambda x: dist.get(x, 99))
            for x in central[:15]:
                cand_set.add(x)
        # prune if too large: keep 40 best by cheap heuristic
        if len(cand_set) > 45:
            scored_cheap = []
            for e in cand_set:
                # adjacency count + centrality
                adj_cnt = 0
                for nb in nbr[e]:
                    if nb in me_set:
                        adj_cnt += 2
                    elif nb in opp_set:
                        adj_cnt += 1
                cheap = adj_cnt*3 - dist.get(e, 20)*0.7
                scored_cheap.append((cheap, e))
            scored_cheap.sort(reverse=True)
            cand_set = set(e for _, e in scored_cheap[:45])
        cand_list = list(cand_set)
        # 1-ply scores
        scored = []
        for e in cand_list:
            me_set.add(e)
            sc = _evaluate(me_set, opp_set, info)
            me_set.remove(e)
            scored.append((sc, e))
            if time.time()-t0 > 0.75:
                break
        scored.sort(reverse=True)
        if not scored:
            return to_rc(next(iter(empty_set)))
        # if little time, return best 1-ply
        if time.time()-t0 > 0.8 or len(scored) <= 1:
            return to_rc(scored[0][1])
        K1 = min(12, len(scored))
        top_moves = [e for _, e in scored[:K1]]
        # 2-ply minimax: opponent replies
        # precompute opp candidate base (reuse cand_set)
        best_move = top_moves[0]
        best_val = -1e18
        # limit opp replies to keep time
        for m in top_moves:
            if time.time()-t0 > 0.92:
                break
            me_set.add(m)
            # generate opp replies: empty after m within 2 hops
            empty2 = empty_set - {m}
            # quick opp candidate set: those in cand_set minus m plus neighbors of m
            opp_cands = set()
            for e in cand_set:
                if e != m and e in empty2:
                    opp_cands.add(e)
            for nb in nbr[m]:
                if nb in empty2:
                    opp_cands.add(nb)
                for nb2 in nbr[nb]:
                    if nb2 in empty2:
                        opp_cands.add(nb2)
            # prune opp cands to ~12 best for opp (evaluate from opp perspective cheaply?)
            # score opp moves by eval drop
            if len(opp_cands) > 14:
                # cheap prune: keep those near opp stones or center
                tmp = []
                for o in opp_cands:
                    adjc = 0
                    for nb in nbr[o]:
                        if nb in opp_set:
                            adjc += 2
                        elif nb in me_set:
                            adjc += 1
                    tmp.append((adjc*3 - dist.get(o, 20)*0.5, o))
                tmp.sort(reverse=True)
                opp_cands = set(o for _, o in tmp[:14])
            worst = 1e18
            # if no opp cands, worst = current eval
            if not opp_cands:
                worst = _evaluate(me_set, opp_set, info)
            else:
                for o in opp_cands:
                    opp_set.add(o)
                    v = _evaluate(me_set, opp_set, info)
                    opp_set.remove(o)
                    if v < worst:
                        worst = v
                    if time.time()-t0 > 0.92:
                        break
            me_set.remove(m)
            # worst is value after opp best reply; maximize it
            # add tiny bonus for 1-ply to break ties toward central
            tie = dict(scored).get(m, 0)*0.01
            val = worst + tie
            if val > best_val:
                best_val = val
                best_move = m
        return to_rc(best_move)
    except Exception:
        try:
            # fallback: first valid empty
            N2 = len(valid_mask)
            occ = set((r, c) for (r, c) in me) | set((r, c) for (r, c) in opp)
            for r in range(N2):
                for c in range(N2):
                    try:
                        if valid_mask[r][c] and (r, c) not in occ:
                            return (r, c)
                    except Exception:
                        continue
        except Exception:
            pass
        return (0, 0)
