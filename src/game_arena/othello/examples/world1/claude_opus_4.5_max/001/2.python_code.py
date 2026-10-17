
import numpy as np
import time

DIRS = ((-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1))

WEIGHTS = np.array([
    [ 20, -3, 11,  8,  8, 11, -3,  20],
    [ -3, -7, -4,  1,  1, -4, -7,  -3],
    [ 11, -4,  2,  2,  2,  2, -4,  11],
    [  8,  1,  2, -3, -3,  2,  1,   8],
    [  8,  1,  2, -3, -3,  2,  1,   8],
    [ 11, -4,  2,  2,  2,  2, -4,  11],
    [ -3, -7, -4,  1,  1, -4, -7,  -3],
    [ 20, -3, 11,  8,  8, 11, -3,  20]
])

CORNERS = ((0,0), (0,7), (7,0), (7,7))
XSQUARES = ((1,1), (1,6), (6,1), (6,6))

def get_moves(me, opp):
    result = []
    for r in range(8):
        for c in range(8):
            if me[r,c] or opp[r,c]:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and opp[nr,nc]:
                    while 0 <= nr < 8 and 0 <= nc < 8 and opp[nr,nc]:
                        nr, nc = nr + dr, nc + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and me[nr,nc]:
                        result.append((r, c))
                        break
    return result

def do_move(me, opp, r, c):
    new_me, new_opp = me.copy(), opp.copy()
    new_me[r,c] = 1
    for dr, dc in DIRS:
        flip = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opp[nr,nc]:
            flip.append((nr, nc))
            nr, nc = nr + dr, nc + dc
        if flip and 0 <= nr < 8 and 0 <= nc < 8 and me[nr,nc]:
            for fr, fc in flip:
                new_me[fr,fc], new_opp[fr,fc] = 1, 0
    return new_me, new_opp

def evaluate(me, opp):
    mc, oc = int(np.sum(me)), int(np.sum(opp))
    total = mc + oc
    
    cs = 0
    for r, c in CORNERS:
        if me[r,c]: cs += 100
        elif opp[r,c]: cs -= 100
    
    xs = 0
    for xr, xc, cr, cc in [(1,1,0,0), (1,6,0,7), (6,1,7,0), (6,6,7,7)]:
        if not me[cr,cc] and not opp[cr,cc]:
            if me[xr,xc]: xs -= 50
            elif opp[xr,xc]: xs += 50
    
    ys = 0
    for yr, yc, cr, cc in [(0,1,0,0),(1,0,0,0),(0,6,0,7),(1,7,0,7),
                           (6,0,7,0),(7,1,7,0),(6,7,7,7),(7,6,7,7)]:
        if not me[cr,cc] and not opp[cr,cc]:
            if me[yr,yc]: ys -= 15
            elif opp[yr,yc]: ys += 15
    
    mm, om = len(get_moves(me, opp)), len(get_moves(opp, me))
    mob = (mm - om) * 10
    
    pos = int(np.sum(me * WEIGHTS) - np.sum(opp * WEIGHTS))
    
    if total > 55:
        return cs + (mc - oc) * 20
    elif total > 44:
        return cs + xs + ys + mob + pos
    return cs + xs + ys + mob * 2 + pos

def search(me, opp, d, a, b, end):
    if time.time() > end:
        return None, None
    
    moves = get_moves(me, opp)
    
    if d == 0:
        return evaluate(me, opp), None
    
    if not moves:
        omoves = get_moves(opp, me)
        if not omoves:
            diff = int(np.sum(me)) - int(np.sum(opp))
            return (10000 if diff > 0 else -10000 if diff < 0 else 0), None
        v, _ = search(opp, me, d, -b, -a, end)
        return (None, None) if v is None else (-v, None)
    
    def prio(m):
        r, c = m
        if (r,c) in CORNERS: return 10000
        if (r,c) in XSQUARES: return -1000
        return WEIGHTS[r,c]
    moves.sort(key=prio, reverse=True)
    
    best, bm = -100000, moves[0]
    for m in moves:
        nme, nop = do_move(me, opp, m[0], m[1])
        v, _ = search(nop, nme, d-1, -b, -a, end)
        if v is None:
            return None, None
        v = -v
        if v > best:
            best, bm = v, m
        a = max(a, v)
        if a >= b:
            break
    return best, bm

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_moves(you, opponent)
    if not moves:
        return "pass"
    
    st = time.time()
    end = st + 0.9
    bm = moves[0]
    
    for d in range(1, 15):
        if time.time() > st + 0.7:
            break
        _, m = search(you, opponent, d, -100000, 100000, end)
        if m:
            bm = m
    
    return chr(ord('a') + bm[1]) + str(bm[0] + 1)
