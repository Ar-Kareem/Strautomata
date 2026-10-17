
from collections import deque
import time

_BOARD = None
_BOARD_KEY = None

def _build_board(valid_mask):
    N = len(valid_mask)
    valid_set = set()
    for r in range(N):
        row = valid_mask[r]
        for c in range(N):
            try:
                v = row[c]
            except Exception:
                v = False
            if v:
                # numpy bool or python bool
                try:
                    ok = bool(v)
                except Exception:
                    ok = False
                if ok:
                    valid_set.add(r * N + c)
    def make_adj(swap):
        adj = {}
        for vid in valid_set:
            r = vid // N
            c = vid % N
            odd = (c % 2 == 1)
            if not swap:
                is_odd_type = odd
            else:
                is_odd_type = not odd
            if is_odd_type:
                deltas = ((-1,0),(1,0),(-1,-1),(0,-1),(-1,1),(0,1))
            else:
                deltas = ((-1,0),(1,0),(0,-1),(1,-1),(0,1),(1,1))
            lst = []
            for dr, dc in deltas:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    nid = nr * N + nc
                    if nid in valid_set:
                        lst.append(nid)
            adj[vid] = lst
        return adj
    adjA = make_adj(False)
    adjB = make_adj(True)
    sumA = sum(len(v) for v in adjA.values())
    sumB = sum(len(v) for v in adjB.values())
    adj = adjA if sumA >= sumB else adjB

    border_set = set(v for v in valid_set if len(adj[v]) < 6)
    # corners are degree <=3
    corner_set = set(v for v in border_set if len(adj[v]) <= 3)
    if len(corner_set) != 6:
        # fallback: take 6 lowest degree border cells
        sorted_b = sorted(list(border_set), key=lambda x: (len(adj[x]), x))
        # if more than 6 with degree 3, keep spacing by angle
        if len(corner_set) > 6:
            # thin by angle
            cr = sum((v // N) for v in valid_set) / max(1, len(valid_set))
            cc = sum((v % N) for v in valid_set) / max(1, len(valid_set))
            import math
            def ang(v):
                return math.atan2((v // N) - cr, (v % N) - cc)
            cands = list(corner_set)
            cands.sort(key=ang)
            # pick 6 evenly
            step = len(cands) / 6.0
            picked = set()
            for i in range(6):
                picked.add(cands[int(i * step) % len(cands)])
            corner_set = picked
        else:
            # pad with lowest degree
            corner_set = set(sorted_b[:6])

    edge_map = {}
    edge_cells = [[] for _ in range(6)]
    corner_list = list(corner_set)
    try:
        # order border cycle
        border_list_set = border_set
        start = corner_list[0]
        ordered = []
        visited = set()
        prev = None
        cur = start
        while True:
            ordered.append(cur)
            visited.add(cur)
            neigh = [nb for nb in adj[cur] if nb in border_list_set and nb != prev]
            nxt = None
            for nb in neigh:
                if nb not in visited:
                    nxt = nb
                    break
            if nxt is None:
                break
            prev, cur = cur, nxt
            if cur == start:
                break
            if len(ordered) > len(border_list_set) + 5:
                break
        if len(ordered) == len(border_list_set) and len(ordered) > 6:
            idx = sorted([ordered.index(c) for c in corner_set])
            for ei in range(6):
                s = idx[ei]
                e = idx[(ei + 1) % 6]
                k = (s + 1) % len(ordered)
                while k != e:
                    vid = ordered[k]
                    edge_map[vid] = ei
                    edge_cells[ei].append(vid)
                    k = (k + 1) % len(ordered)
        else:
            raise ValueError("order fail")
    except Exception:
        # geometric fallback: assign by angle sector
        import math
        cr = sum((v // N) for v in valid_set) / max(1, len(valid_set))
        cc = sum((v % N) for v in valid_set) / max(1, len(valid_set))
        # order corners by angle
        def ang(v):
            return math.atan2((v // N) - cr, (v % N) - cc)
        corner_list_sorted = sorted(corner_list, key=ang)
        # for each border non-corner, assign to nearest segment midpoint angle
        mids = []
        for i in range(6):
            a1 = ang(corner_list_sorted[i])
            a2 = ang(corner_list_sorted[(i+1) % 6])
            # circular mean approx
            # unwrap
            d = a2 - a1
            while d <= -math.pi:
                d += 2*math.pi
            while d > math.pi:
                d -= 2*math.pi
            mids.append(a1 + d/2)
        for v in border_set:
            if v in corner_set:
                continue
            a = ang(v)
            best = 0
            bestd = 1e9
            for i, m in enumerate(mids):
                d = abs(a - m)
                d = min(d, 2*math.pi - d)
                if d < bestd:
                    bestd = d
                    best = i
            edge_map[v] = best
            edge_cells[best].append(v)

    # center
    cr = sum((v // N) for v in valid_set) / max(1, len(valid_set))
    cc = sum((v % N) for v in valid_set) / max(1, len(valid_set))
    center = None
    bestd = 1e9
    for v in valid_set:
        d = abs((v // N) - cr) + abs((v % N) - cc)
        if d < bestd:
            bestd = d
            center = v
    return {
        'N': N,
        'valid_set': valid_set,
        'valid_list': list(valid_set),
        'adj': adj,
        'border_set': border_set,
        'corner_set': corner_set,
        'corner_list': corner_list,
        'edge_map': edge_map,
        'edge_cells': edge_cells,
        'center': center,
        'cr': cr,
        'cc': cc,
    }

def _get_board(valid_mask):
    global _BOARD, _BOARD_KEY
    N = len(valid_mask)
    # quick key: N and count
    cnt = 0
    for r in range(N):
        row = valid_mask[r]
        for c in range(N):
            try:
                if row[c]:
                    cnt += 1
            except Exception:
                pass
    key = (N, cnt)
    if _BOARD is not None and _BOARD_KEY == key and _BOARD['N'] == N:
        return _BOARD
    _BOARD = _build_board(valid_mask)
    _BOARD_KEY = key
    return _BOARD

def _bfs_component(board, player_set, start):
    adj = board['adj']
    edge_map = board['edge_map']
    corner_set = board['corner_set']
    visited = set([start])
    stack = [start]
    corners = set()
    edges = set()
    if start in corner_set:
        corners.add(start)
    if start in edge_map:
        edges.add(edge_map[start])
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v in player_set and v not in visited:
                visited.add(v)
                stack.append(v)
                if v in corner_set:
                    corners.add(v)
                if v in edge_map:
                    edges.add(edge_map[v])
    return visited, corners, edges

def _has_ring_global(board, player_set):
    # quick prune: need at least 6 stones
    if len(player_set) < 6:
        return False
    adj = board['adj']
    valid_set = board['valid_set']
    border_set = board['border_set']
    # non-player cells
    # BFS exterior through non-player
    exterior = set()
    dq = deque()
    for b in border_set:
        if b not in player_set and b not in exterior:
            exterior.add(b)
            dq.append(b)
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v not in player_set and v not in exterior:
                exterior.add(v)
                dq.append(v)
    # interior = non-player - exterior
    # build interior components
    seen = set()
    for vid in valid_set:
        if vid in player_set or vid in exterior or vid in seen:
            continue
        # new interior component
        comp = set([vid])
        seen.add(vid)
        q = deque([vid])
        neigh_players = set()
        while q:
            u = q.popleft()
            for w in adj[u]:
                if w in player_set:
                    neigh_players.add(w)
                elif w not in exterior and w not in seen:
                    # interior cell
                    seen.add(w)
                    comp.add(w)
                    q.append(w)
                # if neighbour is exterior -> then this comp actually connects to exterior?
                # that cannot happen because exterior already flood-filled through all non-player,
                # so no interior cell is adjacent via non-player to exterior without being exterior.
                # but adjacency via player wall is fine.
            # end
        if not comp:
            continue
        if len(neigh_players) == 0:
            continue
        # check if neigh_players are connected via player_set
        # BFS from one through player_set
        start_p = next(iter(neigh_players))
        reach = set([start_p])
        st = [start_p]
        while st:
            u = st.pop()
            for v in adj[u]:
                if v in player_set and v not in reach:
                    reach.add(v)
                    st.append(v)
        if neigh_players.issubset(reach):
            return True
    return False

def _is_win_after(board, player_set, move):
    # bridge / fork via move component
    visited, corners, edges = _bfs_component(board, player_set, move)
    if len(corners) >= 2:
        return True
    if len(edges) >= 3:
        return True
    # ring prune: need cycle in visited
    if len(visited) >= 6:
        # count internal edges
        adj = board['adj']
        ecount = 0
        for u in visited:
            for v in adj[u]:
                if v in visited:
                    ecount += 1
        ecount //= 2
        if ecount >= len(visited):
            # possible cycle, do global check
            if _has_ring_global(board, player_set):
                return True
    return False

def _winning_moves(board, player_set, empty_set, limit=3):
    if len(player_set) == 0:
        return []
    adj = board['adj']
    # frontier only
    cands = []
    for e in empty_set:
        found = False
        for nb in adj[e]:
            if nb in player_set:
                found = True
                break
        if found:
            cands.append(e)
    res = []
    for m in cands:
        # simulate
        player_set.add(m)
        try:
            if _is_win_after(board, player_set, m):
                res.append(m)
                if len(res) >= limit:
                    player_set.discard(m)
                    break
        finally:
            player_set.discard(m)
    return res

def _connection_cost(board, player_set, opp_set):
    INF = 1000
    if len(player_set) == 0:
        return INF
    adj = board['adj']
    edge_cells = board['edge_cells']
    corner_list = board['corner_list']
    dist = {}
    dq = deque()
    for p in player_set:
        dist[p] = 0
        dq.append(p)
    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in adj[u]:
            if v in opp_set:
                continue
            w = 0 if v in player_set else 1
            nd = du + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    edge_costs = []
    for ec in edge_cells:
        best = INF
        for v in ec:
            if v in dist and dist[v] < best:
                best = dist[v]
        edge_costs.append(best)
    corner_costs = []
    for v in corner_list:
        if v in dist:
            corner_costs.append(dist[v])
        else:
            corner_costs.append(INF)
    edge_costs.sort()
    corner_costs.sort()
    fork = sum(edge_costs[:3]) if len(edge_costs) >= 3 else INF
    bridge = sum(corner_costs[:2]) if len(corner_costs) >= 2 else INF
    return fork if fork < bridge else bridge

def policy(me, opp, valid_mask):
    try:
        t0 = time.time()
        board = _get_board(valid_mask)
        N = board['N']
        valid_set = board['valid_set']
        adj = board['adj']
        corner_set = board['corner_set']
        edge_map = board['edge_map']
        center = board['center']
        cr = board['cr']
        cc = board['cc']

        me_set = set(r * N + c for (r, c) in me)
        opp_set = set(r * N + c for (r, c) in opp)
        # keep only valid (safety)
        me_set = me_set.intersection(valid_set)
        opp_set = opp_set.intersection(valid_set)
        empty_set = valid_set - me_set - opp_set
        if not empty_set:
            return (0, 0)
        # first move
        if len(me_set) == 0 and len(opp_set) == 0:
            return (center // N, center % N)
        if len(me_set) == 0:
            # play center if free else nearest to center
            if center in empty_set:
                return (center // N, center % N)
        def to_rc(vid):
            return (vid // N, vid % N)

        # 1) immediate win
        # frontier for me
        if me_set:
            my_front = [e for e in empty_set if any(nb in me_set for nb in adj[e])]
        else:
            my_front = list(empty_set)
        for m in my_front:
            me_set.add(m)
            try:
                if _is_win_after(board, me_set, m):
                    return to_rc(m)
            finally:
                me_set.discard(m)
            if time.time() - t0 > 0.85:
                break

        # 2) block opponent immediate win
        opp_wins = []
        if opp_set:
            opp_front = [e for e in empty_set if any(nb in opp_set for nb in adj[e])]
        else:
            opp_front = []
        for m in opp_front:
            opp_set.add(m)
            try:
                if _is_win_after(board, opp_set, m):
                    opp_wins.append(m)
            finally:
                opp_set.discard(m)
            if time.time() - t0 > 0.9:
                break
        if len(opp_wins) == 1:
            return to_rc(opp_wins[0])
        if len(opp_wins) > 1:
            # must block one; pick one with best eval (below) - for now pick first but try to prefer central/connected
            # evaluate quickly: prefer move that is also adjacent to us
            opp_wins.sort(key=lambda v: (0 if any(nb in me_set for nb in adj[v]) else 1, abs((v//N)-cr)+abs((v%N)-cc)))
            return to_rc(opp_wins[0])

        # helper pre-score for pruning
        def pre_score(vid):
            r = vid // N; c = vid % N
            own_n = 0; opp_n = 0
            for nb in adj[vid]:
                if nb in me_set:
                    own_n += 1
                elif nb in opp_set:
                    opp_n += 1
            d = abs(r - cr) + abs(c - cc)
            bonus = 0
            if vid in corner_set:
                bonus += 1.5
            if vid in edge_map:
                bonus += 0.8
            return own_n * 3 + opp_n * 2.2 + bonus - d * 0.15

        # 3) my double threat (create 2 wins)
        # limit candidates to top K by pre_score among frontier + corners/edges
        cand_all = list(empty_set)
        cand_all.sort(key=pre_score, reverse=True)
        K1 = 28 if len(empty_set) > 40 else len(cand_all)
        top1 = cand_all[:K1]
        # only consider those adjacent to me or corner/edge for threat creation
        for m in top1:
            if time.time() - t0 > 0.9:
                break
            # must be plausible: adjacent to me or corner
            if me_set and not any(nb in me_set for nb in adj[m]):
                if m not in corner_set and m not in edge_map:
                    continue
            me_set.add(m)
            empty2 = empty_set - {m}
            try:
                wins2 = _winning_moves(board, me_set, empty2, limit=3)
                if len(wins2) >= 2:
                    return to_rc(m)
            finally:
                me_set.discard(m)

        # 4) block opponent double threat
        if opp_set:
            # top opp candidates
            def pre_score_opp(vid):
                own_n = 0
                for nb in adj[vid]:
                    if nb in opp_set:
                        own_n += 1
                r = vid // N; c = vid % N
                d = abs(r - cr) + abs(c - cc)
                bonus = 1.5 if vid in corner_set else (0.8 if vid in edge_map else 0)
                return own_n * 3 + bonus - d * 0.15
            cand_o = list(empty_set)
            cand_o.sort(key=pre_score_opp, reverse=True)
            K2 = 24 if len(empty_set) > 40 else len(cand_o)
            top2 = cand_o[:K2]
            dangerous = []
            for m in top2:
                if time.time() - t0 > 0.92:
                    break
                if not any(nb in opp_set for nb in adj[m]):
                    if m not in corner_set and m not in edge_map:
                        continue
                opp_set.add(m)
                empty2 = empty_set - {m}
                try:
                    wins2 = _winning_moves(board, opp_set, empty2, limit=3)
                    if len(wins2) >= 2:
                        dangerous.append(m)
                finally:
                    opp_set.discard(m)
            if dangerous:
                # block the most dangerous (prefer also good for us)
                dangerous.sort(key=pre_score, reverse=True)
                return to_rc(dangerous[0])

        # 5) 1-ply virtual connection evaluation
        cands_eval = cand_all[:60] if len(cand_all) > 60 else cand_all
        best = None
        best_val = -1e18
        # cache opp/me base? compute per candidate
        for m in cands_eval:
            if time.time() - t0 > 0.97:
                break
            me_set.add(m)
            try:
                my_cost = _connection_cost(board, me_set, opp_set)
                # opp cost with m blocked
                opp_blocked = opp_set  # m not in opp_set, but m in me_set blocks opp via me_set check? our cost func blocks via opp_set param only.
                # For opp cost, blocked set is me_set (includes m). So call with swapped roles:
                opp_cost = _connection_cost(board, opp_set, me_set)
                val = opp_cost - my_cost
                r = m // N; c = m % N
                # tie breakers
                own_n = sum(1 for nb in adj[m] if nb in me_set)
                opp_n = sum(1 for nb in adj[m] if nb in opp_set)
                val += own_n * 0.05 + opp_n * 0.04
                val -= (abs(r - cr) + abs(c - cc)) * 0.01
                if m in corner_set:
                    val += 0.15
                if m in edge_map:
                    val += 0.05
                # small deterministic jitter to avoid repeats
                val += ((m * 7919) % 100) * 0.0001
                if val > best_val:
                    best_val = val
                    best = m
            finally:
                me_set.discard(m)
        if best is not None:
            return to_rc(best)

        # fallback: best pre_score
        cand_all.sort(key=pre_score, reverse=True)
        return to_rc(cand_all[0])
    except Exception:
        pass
    # ultimate fallback: first legal
    try:
        N = len(valid_mask)
        occ = set()
        for (r, c) in me:
            occ.add((r, c))
        for (r, c) in opp:
            occ.add((r, c))
        for r in range(N):
            for c in range(N):
                try:
                    ok = valid_mask[r][c]
                except Exception:
                    ok = False
                if ok and (r, c) not in occ:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)
