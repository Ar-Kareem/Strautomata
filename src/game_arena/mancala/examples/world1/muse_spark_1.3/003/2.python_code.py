
import time

def policy(you, opponent):
    # copy board: you=south to move, opponent=north
    try:
        sp0 = [int(you[i]) for i in range(6)]
        ss0 = int(you[6])
        np0 = [int(opponent[i]) for i in range(6)]
        ns0 = int(opponent[6])
    except Exception:
        return 0

    legal_root = [i for i in range(6) if sp0[i] > 0]
    if not legal_root:
        return 0
    if len(legal_root) == 1:
        return legal_root[0]

    start = time.monotonic() if hasattr(time, 'monotonic') else time.time()
    try:
        now_fn = time.monotonic
    except Exception:
        now_fn = time.time
    deadline = start + 0.90

    class _Timeout(Exception):
        pass

    counter = [0]

    def _check():
        counter[0] += 1
        if counter[0] & 1023 == 0:
            if now_fn() > deadline:
                raise _Timeout()

    # apply move, return new state
    # turn 0=south, 1=north
    def apply(sp, ss, npp, ns, turn, mv):
        nsp = sp[:]  # len 6
        nnp = npp[:]
        nss = ss
        nns = ns
        if turn == 0:
            seeds = nsp[mv]
            nsp[mv] = 0
            idx = mv + 1  # position in 13-cycle: 0-5 sp, 6 store, 7-12 np
            # sow
            for _ in range(seeds):
                cur = idx % 13
                if cur <= 5:
                    nsp[cur] += 1
                elif cur == 6:
                    nss += 1
                else:
                    nnp[cur - 7] += 1
                idx += 1
            last = (mv + seeds) % 13
            nturn = 1
            if last == 6:
                nturn = 0
            elif last <= 5:
                if nsp[last] == 1 and nnp[5 - last] > 0:
                    cap = nnp[5 - last]
                    nnp[5 - last] = 0
                    nsp[last] = 0
                    nss += 1 + cap
            # game over? either side empty
            over = False
            term = 0
            # fast empty check
            e1 = True
            for v in nsp:
                if v != 0:
                    e1 = False
                    break
            e2 = True
            for v in nnp:
                if v != 0:
                    e2 = False
                    break
            if e1 or e2:
                over = True
                term = (nss + nsp[0] + nsp[1] + nsp[2] + nsp[3] + nsp[4] + nsp[5]) - (nns + nnp[0] + nnp[1] + nnp[2] + nnp[3] + nnp[4] + nnp[5])
                # if extra but game over, extra irrelevant
            return (nsp, nss, nnp, nns, nturn, over, term)
        else:
            seeds = nnp[mv]
            nnp[mv] = 0
            idx = mv + 1  # 0-5 np, 6 nstore, 7-12 sp
            for _ in range(seeds):
                cur = idx % 13
                if cur <= 5:
                    nnp[cur] += 1
                elif cur == 6:
                    nns += 1
                else:
                    nsp[cur - 7] += 1
                idx += 1
            last = (mv + seeds) % 13
            nturn = 0
            if last == 6:
                nturn = 1
            elif last <= 5:
                if nnp[last] == 1 and nsp[5 - last] > 0:
                    cap = nsp[5 - last]
                    nsp[5 - last] = 0
                    nnp[last] = 0
                    nns += 1 + cap
            over = False
            term = 0
            e1 = True
            for v in nsp:
                if v != 0:
                    e1 = False
                    break
            e2 = True
            for v in nnp:
                if v != 0:
                    e2 = False
                    break
            if e1 or e2:
                over = True
                term = (nss + nsp[0] + nsp[1] + nsp[2] + nsp[3] + nsp[4] + nsp[5]) - (nns + nnp[0] + nnp[1] + nnp[2] + nnp[3] + nnp[4] + nnp[5])
            return (nsp, nss, nnp, nns, nturn, over, term)

    def evaluate(sp, ss, npp, ns, turn):
        s_sum = sp[0]+sp[1]+sp[2]+sp[3]+sp[4]+sp[5]
        n_sum = npp[0]+npp[1]+npp[2]+npp[3]+npp[4]+npp[5]
        total = s_sum + n_sum
        if total > 30:
            w = 0.10
        elif total > 20:
            w = 0.15
        elif total > 10:
            w = 0.25
        elif total > 4:
            w = 0.50
        else:
            w = 0.80
        store_diff = ss - ns
        pit_diff = s_sum - n_sum
        # side to move bonus (from south perspective)
        t = 0.25 if turn == 0 else -0.25
        # free move availability
        eb = 0.0
        # extra if seeds == distance to store mod 13
        # south distance = 6-i, north distance = 6-i
        if sp[0] > 0 and (sp[0] - 6) % 13 == 0:
            eb += 0.35
        if sp[1] > 0 and (sp[1] - 5) % 13 == 0:
            eb += 0.35
        if sp[2] > 0 and (sp[2] - 4) % 13 == 0:
            eb += 0.35
        if sp[3] > 0 and (sp[3] - 3) % 13 == 0:
            eb += 0.35
        if sp[4] > 0 and (sp[4] - 2) % 13 == 0:
            eb += 0.35
        if sp[5] > 0 and (sp[5] - 1) % 13 == 0:
            eb += 0.35
        if npp[0] > 0 and (npp[0] - 6) % 13 == 0:
            eb -= 0.35
        if npp[1] > 0 and (npp[1] - 5) % 13 == 0:
            eb -= 0.35
        if npp[2] > 0 and (npp[2] - 4) % 13 == 0:
            eb -= 0.35
        if npp[3] > 0 and (npp[3] - 3) % 13 == 0:
            eb -= 0.35
        if npp[4] > 0 and (npp[4] - 2) % 13 == 0:
            eb -= 0.35
        if npp[5] > 0 and (npp[5] - 1) % 13 == 0:
            eb -= 0.35
        # slight right-pit positional weight
        pos = 0.02 * ((sp[5]*1.3 + sp[4]*1.1 + sp[3]*0.9 + sp[2]*0.7 + sp[1]*0.5 + sp[0]*0.3) - (npp[5]*1.3 + npp[4]*1.1 + npp[3]*0.9 + npp[2]*0.7 + npp[1]*0.5 + npp[0]*0.3))
        return store_diff + w * pit_diff + t + eb + pos

    # alpha-beta, score from south perspective
    def search(sp, ss, npp, ns, turn, depth, alpha, beta):
        _check()
        if depth <= 0:
            return evaluate(sp, ss, npp, ns, turn)
        if turn == 0:
            # max node
            moves = []
            for i in range(6):
                if sp[i] > 0:
                    moves.append(i)
            if not moves:
                return (ss + sp[0]+sp[1]+sp[2]+sp[3]+sp[4]+sp[5]) - (ns + npp[0]+npp[1]+npp[2]+npp[3]+npp[4]+npp[5])
            # generate children once for ordering
            childs = []
            for m in moves:
                nsp, nss, nnp, nns, nturn, over, term = apply(sp, ss, npp, ns, 0, m)
                if over:
                    key = term + 1000  # terminals first, higher better
                else:
                    # immediate store diff + extra bonus for ordering
                    key = (nss - nns) * 2.0
                    if nturn == 0:
                        key += 5.0
                    # capture gain approximated by store jump
                    key += (nss - ss) * 1.0
                childs.append((key, m, (nsp, nss, nnp, nns, nturn, over, term)))
            childs.sort(key=lambda x: x[0], reverse=True)
            best = -1e18
            for _, m, tup in childs:
                nsp, nss, nnp, nns, nturn, over, term = tup
                if over:
                    s = float(term)
                else:
                    s = search(nsp, nss, nnp, nns, nturn, depth - 1, alpha, beta)
                if s > best:
                    best = s
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            moves = []
            for i in range(6):
                if npp[i] > 0:
                    moves.append(i)
            if not moves:
                return (ss + sp[0]+sp[1]+sp[2]+sp[3]+sp[4]+sp[5]) - (ns + npp[0]+npp[1]+npp[2]+npp[3]+npp[4]+npp[5])
            childs = []
            for m in moves:
                nsp, nss, nnp, nns, nturn, over, term = apply(sp, ss, npp, ns, 1, m)
                if over:
                    key = term  # smaller better for min, sort ascending
                else:
                    key = (nss - nns) * 2.0
                    if nturn == 1:
                        key -= 5.0
                    key -= (nns - ns) * 1.0
                childs.append((key, m, (nsp, nss, nnp, nns, nturn, over, term)))
            childs.sort(key=lambda x: x[0])  # ascending: best for north first
            best = 1e18
            for _, m, tup in childs:
                nsp, nss, nnp, nns, nturn, over, term = tup
                if over:
                    s = float(term)
                else:
                    s = search(nsp, nss, nnp, nns, nturn, depth - 1, alpha, beta)
                if s < best:
                    best = s
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    # greedy fallback ordering for root
    def greedy_pick():
        best = legal_root[0]
        best_key = -1e18
        for m in legal_root:
            try:
                nsp, nss, nnp, nns, nturn, over, term = apply(sp0, ss0, np0, ns0, 0, m)
            except Exception:
                continue
            if over:
                key = float(term) + 1000
            else:
                key = (nss - ss0) * 10.0
                if nturn == 0:
                    key += 20.0
                key += sp0[m] * 0.05
            if key > best_key:
                best_key = key
                best = m
        return best

    best_move = greedy_pick()
    ordered = sorted(legal_root, key=lambda m: 0)
    # initial order by greedy heuristic
    tmp = []
    for m in legal_root:
        try:
            nsp, nss, nnp, nns, nturn, over, term = apply(sp0, ss0, np0, ns0, 0, m)
            if over:
                k = term + 1000
            else:
                k = (nss - ss0) * 10 + (5 if nturn == 0 else 0)
        except Exception:
            k = -1e9
        tmp.append((k, m))
    tmp.sort(key=lambda x: x[0], reverse=True)
    ordered = [m for _, m in tmp]

    try:
        # iterative deepening
        max_depth = 12
        for depth in range(1, max_depth + 1):
            if now_fn() > deadline - 0.05:
                break
            alpha = -1e18
            beta = 1e18
            cur_best = ordered[0]
            cur_best_val = -1e18
            # search each root move
            scored = []
            for m in ordered:
                nsp, nss, nnp, nns, nturn, over, term = apply(sp0, ss0, np0, ns0, 0, m)
                if over:
                    s = float(term)
                else:
                    if depth == 1:
                        # depth 1 means evaluate after move (with correct turn)
                        # use search with depth-1 =0
                        s = search(nsp, nss, nnp, nns, nturn, 0, alpha, beta)
                    else:
                        s = search(nsp, nss, nnp, nns, nturn, depth - 1, alpha, beta)
                scored.append((s, m))
                if s > cur_best_val:
                    cur_best_val = s
                    cur_best = m
                if s > alpha:
                    alpha = s
            # reorder for next depth
            scored.sort(key=lambda x: x[0], reverse=True)
            ordered = [m for _, m in scored]
            best_move = cur_best
            # early exit if winning by large margin and time low
            if depth >= 6 and now_fn() > deadline - 0.15:
                break
    except _Timeout:
        pass
    except Exception:
        pass

    if best_move not in legal_root:
        best_move = legal_root[0]
    if sp0[best_move] <= 0:
        for m in legal_root:
            if sp0[m] > 0:
                best_move = m
                break
    return int(best_move)
