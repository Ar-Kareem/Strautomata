
import numpy as np
import time

DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
INF = 10 ** 9
WIN = 10000

def _generate_moves(b, player):
    res = []
    # b is 6x6 list of lists
    for fr in range(6):
        brow_fr = b[fr]
        for fc in range(6):
            if brow_fr[fc] != player:
                continue
            for dr, dc in DIRS:
                r = fr + dr
                c = fc + dc
                while 0 <= r < 6 and 0 <= c < 6 and b[r][c] == 0:
                    tr = r
                    tc = c
                    # arrows from tr,tc
                    for adr, adc in DIRS:
                        ar = tr + adr
                        ac = tc + adc
                        while 0 <= ar < 6 and 0 <= ac < 6:
                            if ar == fr and ac == fc:
                                res.append((fr, fc, tr, tc, ar, ac))
                                ar += adr
                                ac += adc
                                continue
                            if b[ar][ac] != 0:
                                break
                            res.append((fr, fc, tr, tc, ar, ac))
                            ar += adr
                            ac += adc
                    r += dr
                    c += dc
    return res

def _apply(b, m):
    fr, fc, tr, tc, ar, ac = m
    nb = [row[:] for row in b]
    p = nb[fr][fc]
    nb[fr][fc] = 0
    nb[tr][tc] = p
    nb[ar][ac] = -1
    return nb

def _evaluate(b):
    my_moves = 0
    opp_moves = 0
    my_trapped = 0
    opp_trapped = 0
    my_cen = 0
    opp_cen = 0
    my_reach = [[False]*6 for _ in range(6)]
    opp_reach = [[False]*6 for _ in range(6)]
    # collect amazons
    for r in range(6):
        br = b[r]
        for c in range(6):
            v = br[c]
            if v != 1 and v != 2:
                continue
            cnt = 0
            for dr, dc in DIRS:
                nr = r + dr
                nc = c + dc
                while 0 <= nr < 6 and 0 <= nc < 6 and b[nr][nc] == 0:
                    cnt += 1
                    if v == 1:
                        my_reach[nr][nc] = True
                    else:
                        opp_reach[nr][nc] = True
                    nr += dr
                    nc += dc
            # centrality: 5 - manhattan to center (2.5,2.5)
            cen = 5.0 - (abs(r - 2.5) + abs(c - 2.5))
            if v == 1:
                my_moves += cnt
                my_cen += cen
                if cnt == 0:
                    my_trapped += 1
            else:
                opp_moves += cnt
                opp_cen += cen
                if cnt == 0:
                    opp_trapped += 1
    excl_my = 0
    excl_opp = 0
    my_rc = 0
    opp_rc = 0
    for r in range(6):
        br = b[r]
        mr = my_reach[r]
        opr = opp_reach[r]
        for c in range(6):
            if br[c] != 0:
                continue
            m = mr[c]
            o = opr[c]
            if m:
                my_rc += 1
            if o:
                opp_rc += 1
            if m and not o:
                excl_my += 1
            elif o and not m:
                excl_opp += 1
    score = (my_moves - opp_moves) * 10.0
    score += (excl_my - excl_opp) * 15.0
    score += (my_rc - opp_rc) * 2.0
    score += (my_cen - opp_cen) * 3.0
    score -= my_trapped * 60.0
    score += opp_trapped * 60.0
    return score

def _first_legal_move(b, player=1):
    for fr in range(6):
        for fc in range(6):
            if b[fr][fc] != player:
                continue
            for dr, dc in DIRS:
                r = fr + dr
                c = fc + dc
                while 0 <= r < 6 and 0 <= c < 6 and b[r][c] == 0:
                    tr, tc = r, c
                    for adr, adc in DIRS:
                        ar = tr + adr
                        ac = tc + adc
                        while 0 <= ar < 6 and 0 <= ac < 6:
                            if ar == fr and ac == fc:
                                return (fr, fc, tr, tc, ar, ac)
                            if b[ar][ac] != 0:
                                break
                            return (fr, fc, tr, tc, ar, ac)
                    r += dr
                    c += dc
    return None

def policy(board) -> str:
    t0 = time.monotonic()
    deadline = t0 + 0.90
    try:
        try:
            arr = np.asarray(board)
            b = arr.tolist()
            # ensure 6x6 ints
            # coerce to int
            for r in range(6):
                for c in range(6):
                    b[r][c] = int(b[r][c])
        except Exception:
            return "0,0:0,1:0,2"

        root_moves = _generate_moves(b, 1)
        if not root_moves:
            return "0,0:0,1:0,2"
        if len(root_moves) == 1:
            m = root_moves[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"

        # static ordering
        scored = []
        for m in root_moves:
            nb = _apply(b, m)
            s = _evaluate(nb)
            scored.append((s, m, nb))
            if time.monotonic() > deadline - 0.15:
                break
        if not scored:
            fm = _first_legal_move(b, 1)
            if fm is None:
                return "0,0:0,1:0,2"
            return f"{fm[0]},{fm[1]}:{fm[2]},{fm[3]}:{fm[4]},{fm[5]}"
        scored.sort(key=lambda x: x[0], reverse=True)
        best_move = scored[0][1]

        n = len(scored)
        # adaptive depth / widths
        if n > 150:
            max_depth = 2
            root_K = {2: 12}
            width_inner = {2: 12}
        elif n > 80:
            max_depth = 2
            root_K = {2: 22}
            width_inner = {2: 15}
        elif n > 30:
            max_depth = 3
            root_K = {2: 25, 3: 12}
            width_inner = {2: 15, 3: 12}
        elif n > 15:
            max_depth = 4
            root_K = {2: 30, 3: 14, 4: 10}
            width_inner = {2: 20, 3: 14, 4: 10}
        else:
            max_depth = 5
            root_K = {2: 40, 3: 18, 4: 12, 5: 8}
            width_inner = {2: 25, 3: 18, 4: 12, 5: 8}

        nodes = [0]

        def search(nb, depth, alpha, beta, maximizing):
            nodes[0] += 1
            if (nodes[0] & 127) == 0:
                if time.monotonic() > deadline:
                    raise TimeoutError()
            if depth == 0:
                return _evaluate(nb)
            player = 1 if maximizing else 2
            moves = _generate_moves(nb, player)
            if not moves:
                if maximizing:
                    return -WIN - depth * 50
                else:
                    return WIN + depth * 50
            if depth == 1:
                if maximizing:
                    best = -INF
                    for m in moves:
                        ch = _apply(nb, m)
                        s = _evaluate(ch)
                        if s > best:
                            best = s
                        if best >= beta:
                            break
                        if best > alpha:
                            alpha = best
                    return best
                else:
                    best = INF
                    for m in moves:
                        ch = _apply(nb, m)
                        s = _evaluate(ch)
                        if s < best:
                            best = s
                        if best <= alpha:
                            break
                        if best < beta:
                            beta = best
                    return best
            # depth > 1 : order and truncate
            w = width_inner.get(depth, 12)
            tmp = []
            for m in moves:
                ch = _apply(nb, m)
                s = _evaluate(ch)
                tmp.append((s, m, ch))
            if maximizing:
                tmp.sort(key=lambda x: x[0], reverse=True)
            else:
                tmp.sort(key=lambda x: x[0])
            if len(tmp) > w:
                tmp = tmp[:w]
            if maximizing:
                val = -INF
                for _, m, ch in tmp:
                    v = search(ch, depth - 1, alpha, beta, False)
                    if v > val:
                        val = v
                    if val >= beta:
                        break
                    if val > alpha:
                        alpha = val
                return val
            else:
                val = INF
                for _, m, ch in tmp:
                    v = search(ch, depth - 1, alpha, beta, True)
                    if v < val:
                        val = v
                    if val <= alpha:
                        break
                    if val < beta:
                        beta = val
                return val

        # iterative deepening from depth 2
        for D in range(2, max_depth + 1):
            if time.monotonic() > deadline - 0.08:
                break
            K = root_K.get(D, 10)
            cands = scored[:K] if len(scored) > K else scored[:]
            alpha = -INF
            beta = INF
            cur_best_move = best_move
            cur_best_val = -INF
            cur_vals = []
            try:
                for _, m, ch in cands:
                    if time.monotonic() > deadline - 0.03:
                        raise TimeoutError()
                    v = search(ch, D - 1, alpha, beta, False)
                    cur_vals.append((v, m, ch))
                    if v > cur_best_val:
                        cur_best_val = v
                        cur_best_move = m
                    if v > alpha:
                        alpha = v
                # completed depth -> update best and reorder for next depth
                best_move = cur_best_move
                # reorder scored: searched ones first by value, then rest
                cur_vals.sort(key=lambda x: x[0], reverse=True)
                seen = set([x[1] for x in cur_vals])
                rest = [x for x in scored if x[1] not in seen]
                # rebuild scored list (keep nb)
                scored = cur_vals + rest
            except TimeoutError:
                break
            except Exception:
                break

        m = best_move
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"
    except Exception:
        try:
            try:
                arr2 = np.asarray(board)
                b2 = arr2.tolist()
            except Exception:
                return "0,0:0,1:0,2"
            fm = _first_legal_move(b2, 1)
            if fm is None:
                return "0,0:0,1:0,2"
            return f"{fm[0]},{fm[1]}:{fm[2]},{fm[3]}:{fm[4]},{fm[5]}"
        except Exception:
            return "0,0:0,1:0,2"
