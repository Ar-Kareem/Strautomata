
import numpy as np

def _edges_box(h, v, r, c):
    return int(h[r,c]!=0) + int(h[r+1,c]!=0) + int(v[r,c]!=0) + int(v[r,c+1]!=0)

def _adj_boxes(r, c, d):
    out = []
    if d == 'H':
        if r > 0: out.append((r-1, c))
        if r < 4: out.append((r, c))
    else:
        if c > 0: out.append((r, c-1))
        if c < 4: out.append((r, c))
    return out

def _missing_edges(h, v, r, c):
    m = []
    if h[r,c]==0: m.append(('H', r, c))
    if h[r+1,c]==0: m.append(('H', r+1, c))
    if v[r,c]==0: m.append(('V', r, c))
    if v[r,c+1]==0: m.append(('V', r, c+1))
    return m

def _legal(h, v):
    mv = []
    for r in range(5):
        for c in range(4):
            if h[r,c]==0: mv.append(('H', r, c))
    for r in range(4):
        for c in range(5):
            if v[r,c]==0: mv.append(('V', r, c))
    return mv

def _simulate_opp_greedy(h, v):
    total = 0
    while True:
        found = None
        for br in range(4):
            for bc in range(4):
                if _edges_box(h, v, br, bc) == 3:
                    found = (br, bc); break
            if found: break
        if not found: break
        br, bc = found
        miss = _missing_edges(h, v, br, bc)
        d, r, c = miss[0]
        if d == 'H': h[r,c] = -1
        else: v[r,c] = -1
        for b2r, b2c in _adj_boxes(r, c, d):
            if _edges_box(h, v, b2r, b2c) == 4:
                total += 1
    return total

def _find_double_cross(h, v):
    three_edged = [(br, bc) for br in range(4) for bc in range(4) if _edges_box(h, v, br, bc) == 3]
    if len(three_edged) != 1:
        return None
    br, bc = three_edged[0]
    miss = _missing_edges(h, v, br, bc)
    if len(miss) != 1:
        return None
    d, r, c = miss[0]
    nbrs = _adj_boxes(r, c, d)
    others = [n for n in nbrs if n != (br, bc)]
    if not others:
        return None
    yr, yc = others[0]
    if _edges_box(h, v, yr, yc) != 2:
        return None
    y_miss = _missing_edges(h, v, yr, yc)
    other_miss = [em for em in y_miss if em != (d, r, c)]
    if len(other_miss) != 1:
        return None
    cand = other_miss[0]
    cd, cr, cc = cand
    for bbr, bbc in _adj_boxes(cr, cc, cd):
        if (bbr, bbc) == (yr, yc):
            continue
        e = _edges_box(h, v, bbr, bbc)
        if e >= 2:
            return None
    return cand

def _has_safe_moves(h, v):
    for r in range(5):
        for c in range(4):
            if h[r,c] != 0: continue
            bad = False
            for br, bc in _adj_boxes(r, c, 'H'):
                e = _edges_box(h, v, br, bc)
                if e >= 2: bad = True; break
            if not bad: return True
    for r in range(4):
        for c in range(5):
            if v[r,c] != 0: continue
            bad = False
            for br, bc in _adj_boxes(r, c, 'V'):
                e = _edges_box(h, v, br, bc)
                if e >= 2: bad = True; break
            if not bad: return True
    return False

def _fmt(m):
    d, r, c = m
    return f"{r},{c},{d}"

def policy(horizontal, vertical, capture):
    h = horizontal.copy().astype(int)
    v = vertical.copy().astype(int)
    
    moves = _legal(h, v)
    if not moves:
        return "0,0,H"
    
    completing = []
    safe = []
    unsafe = []
    
    for m in moves:
        d, r, c = m
        completes = False
        creates3 = False
        for br, bc in _adj_boxes(r, c, d):
            e = _edges_box(h, v, br, bc)
            if e == 3: completes = True
            elif e == 2: creates3 = True
        if completes:
            completing.append(m)
        elif creates3:
            unsafe.append(m)
        else:
            safe.append(m)
    
    if completing:
        dc_move = _find_double_cross(h, v)
        if dc_move is not None:
            # Simulate take-all to see if we'd be forced to sacrifice after
            h_sim = h.copy(); v_sim = v.copy()
            while True:
                found = None
                for br in range(4):
                    for bc in range(4):
                        if _edges_box(h_sim, v_sim, br, bc) == 3:
                            found = (br, bc); break
                    if found: break
                if not found: break
                br, bc = found
                miss = _missing_edges(h_sim, v_sim, br, bc)
                d2, r2, c2 = miss[0]
                if d2 == 'H': h_sim[r2,c2] = 1
                else: v_sim[r2,c2] = 1
            empty_after = int(np.sum(h_sim == 0) + np.sum(v_sim == 0))
            if empty_after >= 2 and not _has_safe_moves(h_sim, v_sim):
                return _fmt(dc_move)
        # Take greedily, preferring multi-captures
        best = completing[0]
        best_caps = -1
        for m in completing:
            d, r, c = m
            caps = 0
            for br, bc in _adj_boxes(r, c, d):
                if _edges_box(h, v, br, bc) == 3:
                    caps += 1
            if caps > best_caps:
                best_caps = caps
                best = m
        return _fmt(best)
    
    if safe:
        best = safe[0]
        best_score = -10**9
        for m in safe:
            d, r, c = m
            score = 0
            for br, bc in _adj_boxes(r, c, d):
                e = _edges_box(h, v, br, bc)
                if e == 1:
                    score -= 10  # creating a 2-edge box (chain precursor)
            # Slight bonus for boundary edges (fewer adjacents)
            if len(_adj_boxes(r, c, d)) == 1:
                score += 1
            if score > best_score:
                best_score = score
                best = m
        return _fmt(best)
    
    # Must sacrifice - pick smallest chain
    best_move = unsafe[0]
    best_loss = 999
    for m in unsafe:
        h2 = h.copy()
        v2 = v.copy()
        d, r, c = m
        if d == 'H': h2[r,c] = 1
        else: v2[r,c] = 1
        loss = _simulate_opp_greedy(h2, v2)
        if loss < best_loss:
            best_loss = loss
            best_move = m
    return _fmt(best_move)
