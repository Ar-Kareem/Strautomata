
import numpy as np
from collections import deque

def policy(me, opp, valid_mask):
    N = 15
    vm = np.asarray(valid_mask)
    if vm.dtype != bool:
        vm = vm.astype(bool)

    def get_neighbors_raw(r, c):
        if c & 1:
            deltas = ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1))
        else:
            deltas = ((-1,0),(1,0),(0,-1),(0,1),(1,-1),(1,1))
        res = []
        for dr, dc in deltas:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and vm[nr, nc]:
                res.append((nr, nc))
        return res

    valid_cells = [(r,c) for r in range(N) for c in range(N) if vm[r,c]]
    neighbors_cache = {}
    degrees = {}
    for p in valid_cells:
        nbs = get_neighbors_raw(*p)
        neighbors_cache[p] = nbs
        degrees[p] = len(nbs)

    corners = frozenset(p for p in valid_cells if degrees[p] == 3)
    edge_cells = set(p for p in valid_cells if degrees[p] == 4)

    edge_groups = []
    seen = set()
    for cell in list(edge_cells):
        if cell in seen: continue
        group = set([cell]); seen.add(cell); q = deque([cell])
        while q:
            curr = q.popleft()
            for nb in neighbors_cache[curr]:
                if nb in edge_cells and nb not in seen:
                    seen.add(nb); group.add(nb); q.append(nb)
        edge_groups.append(frozenset(group))

    me_set = set(tuple(p) for p in me)
    opp_set = set(tuple(p) for p in opp)
    occupied = me_set | opp_set

    def connected_components(stones):
        comps = []; cid = {}
        for s in stones:
            if s in cid: continue
            idx = len(comps); cid[s] = idx
            comp = set([s]); q = deque([s])
            while q:
                curr = q.popleft()
                for nb in neighbors_cache[curr]:
                    if nb in stones and nb not in cid:
                        cid[nb] = idx; comp.add(nb); q.append(nb)
            comps.append(comp)
        return comps

    def has_ring(comp):
        starts = [p for p in valid_cells if p not in comp and degrees[p] < 6]
        if not starts: return False
        visited = set(starts); q = deque(starts)
        while q:
            curr = q.popleft()
            for nb in neighbors_cache[curr]:
                if nb not in comp and nb not in visited:
                    visited.add(nb); q.append(nb)
        for p in valid_cells:
            if p not in comp and p not in visited:
                return True
        return False

    def check_win(stones):
        if not stones: return False
        for comp in connected_components(stones):
            if sum(1 for cr in corners if cr in comp) >= 2: return True
            if sum(1 for eg in edge_groups if not comp.isdisjoint(eg)) >= 3: return True
            if len(comp) >= 6 and has_ring(comp): return True
        return False

    legal = [p for p in valid_cells if p not in occupied]
    if not legal:
        return valid_cells[0]

    if not me_set and not opp_set and (7,7) not in occupied and vm[7,7]:
        return (7,7)

    for mv in legal:
        if check_win(me_set | {mv}):
            return mv

    for mv in legal:
        if check_win(opp_set | {mv}):
            return mv

    def score(mv):
        r, c = mv
        s = -(abs(r-7) + abs(c-7)) * 0.1
        nbs = neighbors_cache[mv]
        my_adj = sum(1 for nb in nbs if nb in me_set)
        opp_adj = sum(1 for nb in nbs if nb in opp_set)
        s += my_adj * 3.0 + opp_adj * 1.5
        ext = 0.0
        for nb in nbs:
            if nb in occupied: continue
            for nn in neighbors_cache[nb]:
                if nn in me_set:
                    ext += 0.3
        s += ext
        if mv in corners: s += 1.5
        return s

    best_mv = legal[0]; best_s = score(best_mv)
    for mv in legal[1:]:
        sc = score(mv)
        if sc > best_s:
            best_s = sc; best_mv = mv
    return best_mv
