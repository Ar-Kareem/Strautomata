
import numpy as np

def _format(m):
    return f"{m[0]},{m[1]},{m[2]}"

def _box_edges(r, c, H, V):
    return int(H[r,c]!=0) + int(H[r+1,c]!=0) + int(V[r,c]!=0) + int(V[r,c+1]!=0)

def _legal(H, V):
    moves = []
    for r in range(5):
        for c in range(4):
            if H[r,c] == 0:
                moves.append((r,c,'H'))
    for r in range(4):
        for c in range(5):
            if V[r,c] == 0:
                moves.append((r,c,'V'))
    return moves

def _apply(move, H, V, C, p=1):
    r, c, d = move
    H2, V2, C2 = H.copy(), V.copy(), C.copy()
    n = 0
    if d == 'H':
        H2[r,c] = p
        for br in (r-1, r):
            if 0 <= br < 4 and _box_edges(br, c, H2, V2) == 4:
                C2[br,c] = p; n += 1
    else:
        V2[r,c] = p
        for bc in (c-1, c):
            if 0 <= bc < 4 and _box_edges(r, bc, H2, V2) == 4:
                C2[r,bc] = p; n += 1
    return H2, V2, C2, n

def _makes_3(move, H, V):
    r, c, d = move
    H2, V2 = H.copy(), V.copy()
    if d == 'H':
        H2[r,c] = 1
        for br in (r-1, r):
            if 0 <= br < 4 and _box_edges(br, c, H2, V2) == 3:
                return True
    else:
        V2[r,c] = 1
        for bc in (c-1, c):
            if 0 <= bc < 4 and _box_edges(r, bc, H2, V2) == 3:
                return True
    return False

def _missing(br, bc, H, V):
    e = []
    if H[br,bc] == 0: e.append((br, bc, 'H'))
    if H[br+1,bc] == 0: e.append((br+1, bc, 'H'))
    if V[br,bc] == 0: e.append((br, bc, 'V'))
    if V[br,bc+1] == 0: e.append((br, bc+1, 'V'))
    return e

def _neighbor(br, bc, edge):
    r, c, d = edge
    if d == 'H':
        other = (br-1, bc) if r == br else (br+1, bc)
    else:
        other = (br, bc-1) if c == bc else (br, bc+1)
    if 0 <= other[0] < 4 and 0 <= other[1] < 4:
        return other
    return None

def _greedy_take(H, V, C):
    total = 0
    while True:
        legal = _legal(H, V); found = None
        for m in legal:
            _, _, _, n = _apply(m, H, V, C)
            if n > 0: found = m; break
        if found is None: break
        H, V, C, n = _apply(found, H, V, C); total += n
    return total

def _try_dc(H, V, C):
    remaining = int(np.sum(C == 0))
    for br in range(4):
        for bc in range(4):
            if C[br, bc] != 0: continue
            if _box_edges(br, bc, H, V) != 3: continue
            miss = _missing(br, bc, H, V)
            if len(miss) != 1: continue
            shared = miss[0]
            nb = _neighbor(br, bc, shared)
            if nb is None: continue
            nbr, nbc = nb
            if C[nbr, nbc] != 0: continue
            nbm = _missing(nbr, nbc, H, V)
            if len(nbm) != 2: continue
            outer = [e for e in nbm if e != shared]
            if len(outer) != 1: continue
            dc = outer[0]
            Ht, Vt, Ct, nn = _apply(dc, H, V, C)
            if nn != 0: continue
            greedy = _greedy_take(H, V, C)
            if greedy < 2: continue
            if remaining - greedy < 3: continue
            leg2 = _legal(Ht, Vt)
            num_cap = 0; max_cap = 0
            for m in leg2:
                _, _, _, k = _apply(m, Ht, Vt, Ct)
                if k > 0:
                    num_cap += 1
                    if k > max_cap: max_cap = k
            if max_cap == 2 and num_cap == 1:
                return dc
    return None

def _sac_size(move, H, V, C):
    Ht, Vt, Ct, _ = _apply(move, H, V, C)
    total = 0
    while True:
        legal = _legal(Ht, Vt)
        best_m = None; best_n = 0
        for m in legal:
            _, _, _, n = _apply(m, Ht, Vt, Ct, -1)
            if n > best_n: best_n = n; best_m = m
        if best_m is None: break
        Ht, Vt, Ct, n = _apply(best_m, Ht, Vt, Ct, -1); total += n
    return total

def policy(horizontal, vertical, capture):
    H, V, C = horizontal, vertical, capture
    legal = _legal(H, V)
    if not legal: return "0,0,H"
    captures = []
    for m in legal:
        _, _, _, n = _apply(m, H, V, C)
        if n > 0: captures.append((m, n))
    if captures:
        dc = _try_dc(H, V, C)
        if dc is not None: return _format(dc)
        captures.sort(key=lambda x: -x[1])
        return _format(captures[0][0])
    safe = [m for m in legal if not _makes_3(m, H, V)]
    if safe:
        best = safe[0]; best_score = None
        for m in safe:
            H2, V2, _, _ = _apply(m, H, V, C)
            score = 0
            for r in range(4):
                for c in range(4):
                    if _box_edges(r, c, H2, V2) == 2: score += 1
            if best_score is None or score < best_score:
                best_score = score; best = m
        return _format(best)
    best = legal[0]; best_size = 1e9
    for m in legal:
        s = _sac_size(m, H, V, C)
        if s < best_size: best_size = s; best = m
    return _format(best)
