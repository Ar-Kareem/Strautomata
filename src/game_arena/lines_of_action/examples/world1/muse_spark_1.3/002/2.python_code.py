
import time

WIN = 10000
INF = 10**9

class _Timeout(Exception):
    pass

def _to_flat(board):
    try:
        import numpy as np
        if isinstance(board, np.ndarray):
            return [int(x) for x in board.flatten().tolist()]
    except Exception:
        pass
    # list of lists / tuple of tuples
    try:
        if len(board) == 8 and isinstance(board[0], (list, tuple)):
            flat = []
            for r in range(8):
                row = board[r]
                for c in range(8):
                    flat.append(int(row[c]))
            return flat
    except Exception:
        pass
    # already flat length 64
    try:
        if len(board) == 64:
            return [int(x) for x in board]
    except Exception:
        pass
    # generic fallback: try to flatten
    flat = []
    try:
        for row in board:
            try:
                for x in row:
                    flat.append(int(x))
            except TypeError:
                flat.append(int(row))
    except Exception:
        pass
    if len(flat) == 64:
        return flat
    return flat

def _gen_moves(flat):
    row = [0]*8
    col = [0]*8
    d1 = [0]*15
    d2 = [0]*15
    for i, v in enumerate(flat):
        if v != 0:
            r = i >> 3
            c = i & 7
            row[r] += 1
            col[c] += 1
            d1[r - c + 7] += 1
            d2[r + c] += 1
    moves = []
    for i, v in enumerate(flat):
        if v != 1:
            continue
        r = i >> 3
        c = i & 7
        rd = row[r]
        cd = col[c]
        d1c = d1[r - c + 7]
        d2c = d2[r + c]
        # (dr, dc, dist)
        # unrolled for speed
        # 0,1
        dist = rd
        nr = r
        nc = c + dist
        if nc < 8:
            if flat[nr*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[r*8 + (c+k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, 1 if flat[nr*8+nc]==-1 else 0))
        nc = c - dist
        if nc >= 0:
            if flat[r*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[r*8 + (c-k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, r, nc, 1 if flat[r*8+nc]==-1 else 0))
        # vertical
        dist = cd
        nr = r + dist
        if nr < 8:
            if flat[nr*8+c] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r+k)*8 + c] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, c, 1 if flat[nr*8+c]==-1 else 0))
        nr = r - dist
        if nr >= 0:
            if flat[nr*8+c] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r-k)*8 + c] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, c, 1 if flat[nr*8+c]==-1 else 0))
        # diag NW-SE
        dist = d1c
        nr = r + dist
        nc = c + dist
        if nr < 8 and nc < 8:
            if flat[nr*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r+k)*8 + (c+k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, 1 if flat[nr*8+nc]==-1 else 0))
        nr = r - dist
        nc = c - dist
        if nr >= 0 and nc >= 0:
            if flat[nr*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r-k)*8 + (c-k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, 1 if flat[nr*8+nc]==-1 else 0))
        # diag NE-SW
        dist = d2c
        nr = r + dist
        nc = c - dist
        if nr < 8 and nc >= 0:
            if flat[nr*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r+k)*8 + (c-k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, 1 if flat[nr*8+nc]==-1 else 0))
        nr = r - dist
        nc = c + dist
        if nr >= 0 and nc < 8:
            if flat[nr*8+nc] != 1:
                blocked = False
                for k in range(1, dist):
                    if flat[(r-k)*8 + (c+k)] == -1:
                        blocked = True
                        break
                if not blocked:
                    moves.append((r, c, nr, nc, 1 if flat[nr*8+nc]==-1 else 0))
    return moves

def _is_connected(flat, color):
    first = -1
    cnt = 0
    for i, v in enumerate(flat):
        if v == color:
            if first == -1:
                first = i
            cnt += 1
    if cnt <= 1:
        return True if cnt == 1 else True
    stack = [first]
    seen = {first}
    # BFS 8-dir
    while stack:
        cur = stack.pop()
        r = cur >> 3
        c = cur & 7
        for dr in (-1, 0, 1):
            nr = r + dr
            if nr < 0 or nr >= 8:
                continue
            base = nr * 8
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nc = c + dc
                if nc < 0 or nc >= 8:
                    continue
                ni = base + nc
                if flat[ni] == color and ni not in seen:
                    seen.add(ni)
                    stack.append(ni)
                    if len(seen) == cnt:
                        return True
    return len(seen) == cnt

def _groups_largest(flat, positions, color):
    n = len(positions)
    if n == 0:
        return 0, 0
    if n == 1:
        return 1, 1
    seen = set()
    groups = 0
    largest = 0
    pos_set = set(positions)
    for p in positions:
        if p in seen:
            continue
        groups += 1
        stack = [p]
        seen.add(p)
        sz = 0
        while stack:
            cur = stack.pop()
            sz += 1
            r = cur >> 3
            c = cur & 7
            for dr in (-1, 0, 1):
                nr = r + dr
                if nr < 0 or nr >= 8:
                    continue
                base = nr * 8
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nc = c + dc
                    if nc < 0 or nc >= 8:
                        continue
                    ni = base + nc
                    if ni in pos_set and ni not in seen:
                        seen.add(ni)
                        stack.append(ni)
        if sz > largest:
            largest = sz
            if largest == n:
                groups = 1
                break
        if len(seen) == n:
            break
    return groups, largest

def _evaluate(flat):
    O = []
    X = []
    for i, v in enumerate(flat):
        if v == 1:
            O.append(i)
        elif v == -1:
            X.append(i)
    on = len(O)
    xn = len(X)
    if on == 0:
        return -WIN
    if xn == 0:
        return WIN
    if on == 1:
        return WIN
    # groups
    og, ol = _groups_largest(flat, O, 1)
    if og == 1:
        return WIN
    if xn == 1:
        return -WIN
    xg, xl = _groups_largest(flat, X, -1)
    if xg == 1:
        return -WIN
    # centroids and dispersion
    or_s = 0
    oc_s = 0
    for p in O:
        or_s += p >> 3
        oc_s += p & 7
    xr_s = 0
    xc_s = 0
    for p in X:
        xr_s += p >> 3
        xc_s += p & 7
    mr = or_s / on
    mc = oc_s / on
    xr = xr_s / xn
    xc = xc_s / xn
    od = 0.0
    ocd = 0.0
    for p in O:
        r = (p >> 3)
        c = (p & 7)
        dr = r - mr
        dc = c - mc
        od += dr*dr + dc*dc
        dr2 = r - 3.5
        dc2 = c - 3.5
        ocd += dr2*dr2 + dc2*dc2
    od /= on
    ocd /= on
    xd = 0.0
    xcd = 0.0
    for p in X:
        r = (p >> 3)
        c = (p & 7)
        dr = r - xr
        dc = c - xc
        xd += dr*dr + dc*dc
        dr2 = r - 3.5
        dc2 = c - 3.5
        xcd += dr2*dr2 + dc2*dc2
    xd /= xn
    xcd /= xn
    score = 160.0 * (xg - og)
    score += 100.0 * (ol / on - xl / xn)
    score -= 12.0 * (od - xd)
    score -= 6.0 * (ocd - xcd)
    score += 4.0 * (xn - on)
    return score

def _order_key(m):
    _, _, tr, tc, cap = m
    dr = tr - 3.5
    dc = tc - 3.5
    s = -(dr*dr + dc*dc) * 2.0
    if cap:
        s -= 20.0
    fr, fc = m[0], m[1]
    # encourage moving edge pieces
    if fr == 0 or fr == 7 or fc == 0 or fc == 7:
        s += 3.0
    return s

def policy(board) -> str:
    start = time.perf_counter()
    limit = 0.88
    try:
        flat = _to_flat(board)
        if len(flat) != 64:
            # try to interpret as 8x8 differently
            return "0,1:2,1"
        moves = _gen_moves(flat)
        if not moves:
            return "0,0:0,0"
        if len(moves) == 1:
            m = moves[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        # initial ordering
        moves_sorted = sorted(moves, key=_order_key, reverse=True)
        # quick win in 1 ?
        for m in moves_sorted:
            nb = flat[:]
            nb[m[0]*8+m[1]] = 0
            nb[m[2]*8+m[3]] = 1
            if _is_connected(nb, 1):
                return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
            if time.perf_counter() - start > limit * 0.5 and len(moves) > 30:
                break
        # adaptive max depth
        b = len(moves_sorted)
        if b > 26:
            max_depth = 3
        elif b > 16:
            max_depth = 4
        elif b > 10:
            max_depth = 5
        else:
            max_depth = 6
        nodes = [0]
        def check_timeout():
            if (nodes[0] & 255) == 0:
                if time.perf_counter() - start > limit:
                    raise _Timeout()
        # define recursive negamax with closure
        import sys
        sys.setrecursionlimit(10000)
        def negamax(cur, depth, alpha, beta):
            nodes[0] += 1
            check_timeout()
            if depth == 0:
                return _evaluate(cur)
            ms = _gen_moves(cur)
            if not ms:
                return -WIN - depth
            ms.sort(key=_order_key, reverse=True)
            best = -INF
            for mm in ms:
                nb = cur[:]
                nb[mm[0]*8+mm[1]] = 0
                nb[mm[2]*8+mm[3]] = 1
                if _is_connected(nb, 1):
                    sc = WIN + depth
                else:
                    flip = [-x for x in nb]
                    sc = -negamax(flip, depth-1, -beta, -alpha)
                if sc > best:
                    best = sc
                    if best >= beta:
                        break
                    if best > alpha:
                        alpha = best
            return best
        best_move = moves_sorted[0]
        ordered = moves_sorted
        for depth in range(1, max_depth+1):
            try:
                scored = []
                alpha = -INF
                beta = INF
                for mm in ordered:
                    nodes[0] += 1
                    check_timeout()
                    nb = flat[:]
                    nb[mm[0]*8+mm[1]] = 0
                    nb[mm[2]*8+mm[3]] = 1
                    if _is_connected(nb, 1):
                        sc = WIN + depth
                    else:
                        flip = [-x for x in nb]
                        sc = -negamax(flip, depth-1, -beta, -alpha)
                    scored.append((sc, mm))
                    if sc > alpha:
                        alpha = sc
                    # timeout check
                    if time.perf_counter() - start > limit:
                        raise _Timeout()
                scored.sort(key=lambda x: x[0], reverse=True)
                ordered = [mm for _, mm in scored]
                best_move = ordered[0]
                if scored[0][0] >= WIN - 5:
                    break
                # if little time left, stop deepening
                elapsed = time.perf_counter() - start
                if elapsed > limit * 0.75:
                    break
                if depth >= 3 and elapsed > limit * 0.5:
                    # estimate: if branching large, stop
                    if b > 20 and elapsed > limit * 0.5:
                        break
            except _Timeout:
                break
        m = best_move
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
    except _Timeout:
        try:
            # fallback greedy
            flat2 = _to_flat(board)
            ms2 = _gen_moves(flat2)
            if ms2:
                best = None
                bests = -INF
                for mm in ms2:
                    nb = flat2[:]
                    nb[mm[0]*8+mm[1]] = 0
                    nb[mm[2]*8+mm[3]] = 1
                    if _is_connected(nb, 1):
                        return f"{mm[0]},{mm[1]}:{mm[2]},{mm[3]}"
                    flip = [-x for x in nb]
                    sc = -_evaluate(flip)
                    if sc > bests:
                        bests = sc
                        best = mm
                if best is not None:
                    return f"{best[0]},{best[1]}:{best[2]},{best[3]}"
                m0 = ms2[0]
                return f"{m0[0]},{m0[1]}:{m0[2]},{m0[3]}"
        except Exception:
            pass
        return "0,1:2,1"
    except Exception:
        try:
            flat2 = _to_flat(board)
            ms2 = _gen_moves(flat2)
            if ms2:
                m0 = ms2[0]
                return f"{m0[0]},{m0[1]}:{m0[2]},{m0[3]}"
        except Exception:
            pass
        return "0,1:2,1"
