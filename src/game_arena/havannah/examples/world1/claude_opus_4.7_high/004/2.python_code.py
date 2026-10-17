
import numpy as np
from collections import deque

N = 15
NEIGHBORS = [(-1,0),(1,0),(-1,-1),(0,-1),(0,1),(1,1)]
CORNERS = [(0,0), (0,7), (7,0), (7,14), (14,7), (14,14)]
EDGES = [
    [(0,c) for c in range(1,7)],
    [(i,7+i) for i in range(1,7)],
    [(7+i,14) for i in range(1,7)],
    [(14,c) for c in range(8,14)],
    [(14-i,7-i) for i in range(1,7)],
    [(7-i,0) for i in range(1,7)],
]
EDGE_SETS = [set(e) for e in EDGES]

def get_component(start, stones_set):
    comp = set()
    stack = [start]
    while stack:
        x = stack.pop()
        if x in comp:
            continue
        comp.add(x)
        r, c = x
        for dr, dc in NEIGHBORS:
            nb = (r+dr, c+dc)
            if nb in stones_set and nb not in comp:
                stack.append(nb)
    return comp

def has_ring(comp, vm):
    visited = [[False]*N for _ in range(N)]
    q = deque()
    for r in range(N):
        for c in range(N):
            if not vm[r][c]:
                continue
            if (r,c) in comp:
                continue
            outer = False
            for dr, dc in NEIGHBORS:
                nr, nc = r+dr, c+dc
                if not (0<=nr<N and 0<=nc<N and vm[nr][nc]):
                    outer = True
                    break
            if outer:
                visited[r][c] = True
                q.append((r,c))
    while q:
        r, c = q.popleft()
        for dr, dc in NEIGHBORS:
            nr, nc = r+dr, c+dc
            if 0<=nr<N and 0<=nc<N and vm[nr][nc] and not visited[nr][nc] and (nr,nc) not in comp:
                visited[nr][nc] = True
                q.append((nr,nc))
    for r in range(N):
        for c in range(N):
            if vm[r][c] and (r,c) not in comp and not visited[r][c]:
                return True
    return False

def creates_win(mv, stones_set, vm):
    new_stones = stones_set | {mv}
    comp = get_component(mv, new_stones)
    if sum(1 for c in CORNERS if c in comp) >= 2:
        return True
    if sum(1 for es in EDGE_SETS if not es.isdisjoint(comp)) >= 3:
        return True
    if len(comp) >= 6 and has_ring(comp, vm):
        return True
    return False

def policy(me, opp, valid_mask):
    vm = valid_mask
    me_set = set((int(r),int(c)) for r,c in me)
    opp_set = set((int(r),int(c)) for r,c in opp)
    occupied = me_set | opp_set
    legal = []
    for r in range(N):
        for c in range(N):
            if bool(vm[r][c]) and (r,c) not in occupied:
                legal.append((r,c))
    if not legal:
        for r in range(N):
            for c in range(N):
                if bool(vm[r][c]):
                    return (r,c)
        return (7,7)
    if not me_set and not opp_set:
        return (7,7) if (7,7) in legal else legal[0]
    for mv in legal:
        if creates_win(mv, me_set, vm):
            return mv
    for mv in legal:
        if creates_win(mv, opp_set, vm):
            return mv
    my_comps = []
    seen = set()
    for s in me_set:
        if s in seen: continue
        comp = get_component(s, me_set)
        seen |= comp
        my_comps.append(comp)
    opp_comps = []
    seen = set()
    for s in opp_set:
        if s in seen: continue
        comp = get_component(s, opp_set)
        seen |= comp
        opp_comps.append(comp)
    interesting = set()
    for s in occupied:
        r, c = s
        for dr, dc in NEIGHBORS:
            nr, nc = r+dr, c+dc
            if 0<=nr<N and 0<=nc<N and bool(vm[nr][nc]) and (nr,nc) not in occupied:
                interesting.add((nr,nc))
            for dr2, dc2 in NEIGHBORS:
                nr2, nc2 = r+dr+dr2, c+dc+dc2
                if 0<=nr2<N and 0<=nc2<N and bool(vm[nr2][nc2]) and (nr2,nc2) not in occupied:
                    interesting.add((nr2,nc2))
    candidates = list(interesting) if interesting else legal
    best_score = -1e18
    best_mv = candidates[0]
    for mv in candidates:
        r, c = mv
        score = 0.0
        score -= (abs(r-7) + abs(c-7)) * 0.05
        my_adj = 0
        opp_adj = 0
        my_comps_adj = set()
        opp_comps_adj = set()
        for dr, dc in NEIGHBORS:
            nb = (r+dr, c+dc)
            if nb in me_set:
                my_adj += 1
                for i, comp in enumerate(my_comps):
                    if nb in comp:
                        my_comps_adj.add(i)
                        break
            elif nb in opp_set:
                opp_adj += 1
                for i, comp in enumerate(opp_comps):
                    if nb in comp:
                        opp_comps_adj.add(i)
                        break
        score += my_adj * 0.5
        score += len(my_comps_adj) * 3.0
        score += opp_adj * 0.3
        score += len(opp_comps_adj) * 1.5
        if (r,c) in CORNERS:
            score += 0.5
        for es in EDGE_SETS:
            if (r,c) in es:
                score += 0.2
        if score > best_score:
            best_score = score
            best_mv = mv
    return best_mv
