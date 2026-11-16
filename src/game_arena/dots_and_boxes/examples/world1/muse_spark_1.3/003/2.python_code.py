
import numpy as np
import time

EXACT_THRESH = 12
TIME_BUDGET = 0.9

def _legal_list(h, v):
    moves = []
    for r in range(5):
        for c in range(5):
            if h[r, c] == 0:
                moves.append((r, c, 'H'))
            if v[r, c] == 0:
                moves.append((r, c, 'V'))
    return moves

def _sides_mat(h_occ, v_occ):
    return (h_occ[0:4, 0:4].astype(int) + h_occ[1:5, 0:4].astype(int) +
            v_occ[0:4, 0:4].astype(int) + v_occ[0:4, 1:5].astype(int))

def _adj_boxes(r, c, d):
    adj = []
    if d == 'H':
        if c < 4:
            if r < 4:
                adj.append((r, c))
            if r > 0:
                adj.append((r-1, c))
    else:
        if r < 4:
            if c < 4:
                adj.append((r, c))
            if c > 0:
                adj.append((r, c-1))
    # keep only 0..3
    out = []
    for br, bc in adj:
        if 0 <= br < 4 and 0 <= bc < 4:
            out.append((br, bc))
    return out

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        h = np.asarray(horizontal)
        v = np.asarray(vertical)
        # fallback legal list
        legal = _legal_list(h, v)
        if len(legal) == 0:
            return "0,0,H"
        if len(legal) == 1:
            r, c, d = legal[0]
            return f"{r},{c},{d}"

        h_occ = (h != 0)
        v_occ = (v != 0)
        sides = _sides_mat(h_occ, v_occ)  # 4x4

        # captures per move
        cap_of = []
        for (r, c, d) in legal:
            adj = _adj_boxes(r, c, d)
            k = 0
            for br, bc in adj:
                if sides[br, bc] == 3:
                    k += 1
            cap_of.append(k)
        maxcap = max(cap_of) if cap_of else 0
        n = len(legal)

        # ---------- exact endgame solver ----------
        def exact_pick():
            start = time.time()
            # masks
            hm = 0
            for r in range(5):
                for c in range(5):
                    if h[r, c] != 0:
                        hm |= 1 << (r*5+c)
            vm = 0
            for r in range(5):
                for c in range(5):
                    if v[r, c] != 0:
                        vm |= 1 << (r*5+c)
            # box edge bits
            b_ht = [0]*16
            b_hb = [0]*16
            b_vl = [0]*16
            b_vr = [0]*16
            for br in range(4):
                for bc in range(4):
                    idx = br*4+bc
                    b_ht[idx] = br*5+bc
                    b_hb[idx] = (br+1)*5+bc
                    b_vl[idx] = br*5+bc
                    b_vr[idx] = br*5+bc+1
            # adjacency per edge index
            h_adj = [[] for _ in range(25)]
            for i in range(25):
                r = i//5; c = i % 5
                lst = []
                if c < 4:
                    if r < 4:
                        lst.append(r*4+c)
                    if r > 0:
                        lst.append((r-1)*4+c)
                h_adj[i] = lst
            v_adj = [[] for _ in range(25)]
            for i in range(25):
                r = i//5; c = i % 5
                lst = []
                if r < 4:
                    if c < 4:
                        lst.append(r*4+c)
                    if c > 0:
                        lst.append(r*4+c-1)
                v_adj[i] = lst

            memo = {}
            nodes = [0]

            def check_timeout():
                if nodes[0] % 512 == 0:
                    if time.time() - start > TIME_BUDGET:
                        raise TimeoutError()

            import sys
            sys.setrecursionlimit(10000)

            def dfs(chm, cvm, turn, alpha, beta):
                nodes[0] += 1
                check_timeout()
                key = (chm, cvm, turn)
                if key in memo:
                    return memo[key]
                # sides
                s0 = [0]*16
                for bi in range(16):
                    s0[bi] = ((chm >> b_ht[bi]) & 1) + ((chm >> b_hb[bi]) & 1) + ((cvm >> b_vl[bi]) & 1) + ((cvm >> b_vr[bi]) & 1)
                # collect empties
                cands = []  # (cap, nhm, nvm)
                for i in range(25):
                    if not (chm >> i) & 1:
                        lst = h_adj[i]
                        # dummy with no adj still a move
                        cap = 0
                        for b in lst:
                            if s0[b] == 3:
                                cap += 1
                        # also need to ensure edge was legal in root sense?
                        # if dummy was originally occupied it won't be empty here
                        cands.append((cap, chm | (1 << i), cvm, True, i))
                for i in range(25):
                    if not (cvm >> i) & 1:
                        lst = v_adj[i]
                        cap = 0
                        for b in lst:
                            if s0[b] == 3:
                                cap += 1
                        cands.append((cap, chm, cvm | (1 << i), False, i))
                if not cands:
                    return 0
                # order captures first (best first for both)
                cands.sort(key=lambda x: -x[0])
                if turn == 0:  # max (root)
                    best = -1000
                    cut = False
                    for cap, nhm, nvm, is_h, ei in cands:
                        if cap > 0:
                            val = cap + dfs(nhm, nvm, turn, alpha, beta)
                        else:
                            val = dfs(nhm, nvm, 1, alpha, beta)
                        if val > best:
                            best = val
                        if best > alpha:
                            alpha = best
                        if alpha >= beta:
                            cut = True
                            break
                    if not cut:
                        memo[key] = best
                    return best
                else:  # min
                    best = 1000
                    cut = False
                    for cap, nhm, nvm, is_h, ei in cands:
                        if cap > 0:
                            val = -cap + dfs(nhm, nvm, turn, alpha, beta)
                        else:
                            val = dfs(nhm, nvm, 0, alpha, beta)
                        if val < best:
                            best = val
                        if best < beta:
                            beta = best
                        if alpha >= beta:
                            cut = True
                            break
                    if not cut:
                        memo[key] = best
                    return best

            # root move ordering: captures first
            # build root candidates with move info
            s_root = [0]*16
            for bi in range(16):
                s_root[bi] = ((hm >> b_ht[bi]) & 1) + ((hm >> b_hb[bi]) & 1) + ((vm >> b_vl[bi]) & 1) + ((vm >> b_vr[bi]) & 1)
            root_cands = []
            for (r, c, d) in legal:
                if d == 'H':
                    ei = r*5+c
                    lst = h_adj[ei]
                    cap = sum(1 for b in lst if s_root[b] == 3)
                    nhm = hm | (1 << ei); nvm = vm
                else:
                    ei = r*5+c
                    lst = v_adj[ei]
                    cap = sum(1 for b in lst if s_root[b] == 3)
                    nhm = hm; nvm = vm | (1 << ei)
                root_cands.append((cap, r, c, d, nhm, nvm))
            root_cands.sort(key=lambda x: -x[0])
            best_val = -1000
            best_m = root_cands[0]
            alpha = -1000
            beta = 1000
            for cap, r, c, d, nhm, nvm in root_cands:
                if cap > 0:
                    val = cap + dfs(nhm, nvm, 0, alpha, beta)
                else:
                    val = dfs(nhm, nvm, 1, alpha, beta)
                if val > best_val:
                    best_val = val
                    best_m = (cap, r, c, d, nhm, nvm)
                if val > alpha:
                    alpha = val
            _, br, bc, bd, _, _ = best_m
            return f"{br},{bc},{bd}"

        if n <= EXACT_THRESH:
            try:
                return exact_pick()
            except Exception:
                pass  # fall through to heuristic

        if maxcap > 0:
            # greedy capture, tie-break by heuristic (fewer 2s, more safe remaining)
            best = None
            best_key = None
            for idx, (r, c, d) in enumerate(legal):
                k = cap_of[idx]
                if k != maxcap:
                    continue
                adj = _adj_boxes(r, c, d)
                # simulate new sides quickly
                nsides = sides.copy()
                for br, bc in adj:
                    nsides[br, bc] += 1
                twos = int(np.sum(nsides == 2))
                # safe remaining estimate
                # count empties that would be safe
                # quick approx: use nsides
                safe_rem = 0
                for j, (r2, c2, d2) in enumerate(legal):
                    if j == idx:
                        continue
                    adj2 = _adj_boxes(r2, c2, d2)
                    bad = False
                    for br, bc in adj2:
                        # adjust for the candidate move if overlapping box
                        s = nsides[br, bc]
                        if s == 3 or s == 2:
                            # if s==3 -> would be capture (not safe), if s==2 -> would create 3
                            # need to distinguish: capturing moves are not safe
                            bad = True
                            break
                    if not bad:
                        # also need to ensure it is not capturing: if any adj has 3 -> capturing
                        safe_rem += 1
                key = (-maxcap, twos, -safe_rem, r, c, d)
                if best_key is None or key < best_key:
                    best_key = key
                    best = (r, c, d)
            r, c, d = best
            return f"{r},{c},{d}"
        else:
            # no capture: safe vs sacrifice
            safe_idx = []
            for idx, (r, c, d) in enumerate(legal):
                adj = _adj_boxes(r, c, d)
                dangerous = False
                for br, bc in adj:
                    if sides[br, bc] == 2:
                        dangerous = True
                        break
                if not dangerous:
                    safe_idx.append(idx)
            if safe_idx:
                # rank safe moves: fewer new twos, more safe remaining, smaller pre-sum
                best = None
                best_key = None
                # precompute for speed
                for idx in safe_idx:
                    r, c, d = legal[idx]
                    adj = _adj_boxes(r, c, d)
                    pre_sum = sum(int(sides[br, bc]) for br, bc in adj)
                    nsides = sides.copy()
                    for br, bc in adj:
                        nsides[br, bc] += 1
                    twos = int(np.sum(nsides == 2))
                    # safe remaining after
                    safe_rem = 0
                    for j, (r2, c2, d2) in enumerate(legal):
                        if j == idx:
                            continue
                        adj2 = _adj_boxes(r2, c2, d2)
                        bad = False
                        for br, bc in adj2:
                            if nsides[br, bc] >= 2:  # 2->3 dangerous, 3->4 capturing
                                bad = True
                                break
                        if not bad:
                            safe_rem += 1
                    # border (single adj) bonus implicitly via pre_sum/twos, add touches
                    touches = len(adj)
                    key = (twos, -safe_rem, pre_sum, touches, r, c)
                    if best_key is None or key < best_key:
                        best_key = key
                        best = (r, c, d)
                r, c, d = best
                return f"{r},{c},{d}"
            else:
                # loony: choose minimal give-away via greedy sweep simulation
                best = None
                best_key = None
                for idx, (r, c, d) in enumerate(legal):
                    # apply to copies
                    nh_occ = h_occ.copy()
                    nv_occ = v_occ.copy()
                    nsides = sides.copy()
                    if d == 'H':
                        nh_occ[r, c] = True
                    else:
                        nv_occ[r, c] = True
                    adj = _adj_boxes(r, c, d)
                    for br, bc in adj:
                        nsides[br, bc] += 1
                    # remaining empties
                    rem = []
                    for j, (r2, c2, d2) in enumerate(legal):
                        if j == idx:
                            continue
                        rem.append((r2, c2, d2))
                    # simulate opponent taking all captures
                    cur_h = nh_occ
                    cur_v = nv_occ
                    cur_s = nsides
                    # need mutable list of remaining
                    cur_rem = rem[:]
                    given = 0
                    # loop
                    while True:
                        found = -1
                        found_cap = 0
                        for j, (r2, c2, d2) in enumerate(cur_rem):
                            adj2 = _adj_boxes(r2, c2, d2)
                            k = 0
                            for br, bc in adj2:
                                if cur_s[br, bc] == 3:
                                    k += 1
                            if k > found_cap:
                                found_cap = k
                                found = j
                                if k == 2:
                                    break
                        if found == -1 or found_cap == 0:
                            break
                        r2, c2, d2 = cur_rem.pop(found)
                        if d2 == 'H':
                            cur_h[r2, c2] = True
                        else:
                            cur_v[r2, c2] = True
                        adj2 = _adj_boxes(r2, c2, d2)
                        for br, bc in adj2:
                            cur_s[br, bc] += 1
                        given += found_cap
                    # tie-break: fewer twos left, more safe left
                    twos_left = int(np.sum(cur_s == 2))
                    key = (given, twos_left, r, c, d)
                    if best_key is None or key < best_key:
                        best_key = key
                        best = (r, c, d)
                r, c, d = best
                return f"{r},{c},{d}"
    except Exception:
        pass
    # absolute fallback: first empty
    try:
        h = np.asarray(horizontal)
        v = np.asarray(vertical)
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if v[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass
    return "0,0,H"
