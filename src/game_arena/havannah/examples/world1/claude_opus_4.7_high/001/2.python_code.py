
N = 15
CORNERS = [(0,0), (0,7), (7,14), (14,14), (14,7), (7,0)]
EDGES = [
    frozenset((0,c) for c in range(1,7)),
    frozenset((r, r+7) for r in range(1,7)),
    frozenset((r, 14) for r in range(8,14)),
    frozenset((14, c) for c in range(8,14)),
    frozenset((r, r-7) for r in range(8,14)),
    frozenset((r, 0) for r in range(1,7)),
]
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)]

def hex_dist(r1,c1,r2,c2):
    dr=r2-r1; dc=c2-c1
    if (dr>=0 and dc>=0) or (dr<=0 and dc<=0):
        return max(abs(dr),abs(dc))
    return abs(dr)+abs(dc)

def is_border(r,c):
    return r==0 or r==14 or c==0 or c==14 or r-c==7 or c-r==7

def check_win_after(stones_set, vm, move):
    r0, c0 = move
    comp = {move}
    stack = [move]
    while stack:
        sr, sc = stack.pop()
        for dr, dc in DIRS:
            nr, nc = sr+dr, sc+dc
            if 0<=nr<N and 0<=nc<N and vm[nr][nc] and (nr,nc) in stones_set and (nr,nc) not in comp:
                comp.add((nr,nc)); stack.append((nr,nc))
    ct = sum(1 for cn in CORNERS if cn in comp)
    if ct >= 2: return True
    et = sum(1 for edge in EDGES if not edge.isdisjoint(comp))
    if et >= 3: return True
    fc = 0
    for dr, dc in DIRS:
        nr, nc = r0+dr, c0+dc
        if 0<=nr<N and 0<=nc<N and vm[nr][nc] and (nr,nc) in stones_set:
            fc += 1
    if fc < 2: return False
    outside = set(); queue = []
    for r in range(N):
        for c in range(N):
            if vm[r][c] and (r,c) not in stones_set and is_border(r,c):
                outside.add((r,c)); queue.append((r,c))
    while queue:
        r, c = queue.pop()
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0<=nr<N and 0<=nc<N and vm[nr][nc] and (nr,nc) not in stones_set and (nr,nc) not in outside:
                outside.add((nr,nc)); queue.append((nr,nc))
    for r in range(N):
        for c in range(N):
            if vm[r][c] and (r,c) not in stones_set and (r,c) not in outside:
                return True
    return False

def policy(me, opp, valid_mask):
    try:
        vm = valid_mask.tolist() if hasattr(valid_mask, 'tolist') else [list(row) for row in valid_mask]
    except:
        vm = valid_mask
    me_set = set((r,c) for r,c in me)
    opp_set = set((r,c) for r,c in opp)
    occupied = me_set | opp_set
    valid_moves = []
    for r in range(N):
        for c in range(N):
            if vm[r][c] and (r,c) not in occupied:
                valid_moves.append((r,c))
    if not valid_moves:
        for r in range(N):
            for c in range(N):
                if vm[r][c]: return (r,c)
        return (7,7)
    if not me_set and not opp_set:
        return (7,7)
    for mv in valid_moves:
        me_set.add(mv)
        if check_win_after(me_set, vm, mv):
            return mv
        me_set.discard(mv)
    for mv in valid_moves:
        opp_set.add(mv)
        if check_win_after(opp_set, vm, mv):
            opp_set.discard(mv)
            return mv
        opp_set.discard(mv)
    best_mv = valid_moves[0]
    best_score = -1e18
    for mv in valid_moves:
        r, c = mv
        d = hex_dist(r,c,7,7)
        fc = 0; oc = 0
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0<=nr<N and 0<=nc<N and vm[nr][nc]:
                if (nr,nc) in me_set: fc += 1
                elif (nr,nc) in opp_set: oc += 1
        eb = 0.0
        for corner in CORNERS:
            dd = hex_dist(r,c,corner[0],corner[1])
            if dd <= 3: eb += (3-dd)*0.2
        score = fc * 3.0 + oc * 0.8 - d * 0.15 + eb
        if score > best_score:
            best_score = score
            best_mv = mv
    return best_mv
