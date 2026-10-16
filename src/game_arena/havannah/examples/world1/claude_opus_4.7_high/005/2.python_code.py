
import numpy as np

N = 15
CORNERS_SET = frozenset([(0, 7), (0, 14), (7, 14), (14, 7), (14, 0), (7, 0)])
DIRS = [(-1,0), (1,0), (0,-1), (0,1), (-1,1), (1,-1)]

def get_neighbors(r, c):
    return [(r+dr, c+dc) for dr, dc in DIRS]

def edge_of(r, c):
    if (r, c) in CORNERS_SET:
        return -1
    if r == 0 and 7 < c < 14: return 0
    if c == 14 and 0 < r < 7: return 1
    if r + c == 21 and 7 < r < 14: return 2
    if r == 14 and 0 < c < 7: return 3
    if c == 0 and 7 < r < 14: return 4
    if r + c == 7 and 0 < r < 7: return 5
    return -1

def group_of(start, stones):
    group = {start}
    stack = [start]
    while stack:
        s = stack.pop()
        for n in get_neighbors(*s):
            if n in stones and n not in group:
                group.add(n)
                stack.append(n)
    return group

def check_bridge_fork(stones_set, move):
    stones_with = stones_set | {move}
    group = group_of(move, stones_with)
    cc = sum(1 for c in CORNERS_SET if c in group)
    if cc >= 2:
        return True
    es = set()
    for s in group:
        e = edge_of(*s)
        if e >= 0:
            es.add(e)
    return len(es) >= 3

def check_ring(stones_set, move, valid_mask):
    mn = sum(1 for n in get_neighbors(*move) if n in stones_set)
    if mn < 2:
        return False
    stones_with = stones_set | {move}
    outside = set()
    stack = []
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c]: continue
            if (r, c) in stones_with: continue
            is_boundary = False
            for nr, nc in get_neighbors(r, c):
                if not (0 <= nr < N and 0 <= nc < N) or not valid_mask[nr][nc]:
                    is_boundary = True; break
            if is_boundary:
                outside.add((r, c)); stack.append((r, c))
    while stack:
        s = stack.pop()
        for n in get_neighbors(*s):
            nr, nc = n
            if not (0 <= nr < N and 0 <= nc < N): continue
            if not valid_mask[nr][nc]: continue
            if n in stones_with or n in outside: continue
            outside.add(n); stack.append(n)
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in stones_with and (r, c) not in outside:
                return True
    return False

def is_winning_move(stones_set, move, valid_mask):
    if check_bridge_fork(stones_set, move):
        return True
    if len(stones_set) >= 5 and check_ring(stones_set, move, valid_mask):
        return True
    return False

def policy(me, opp, valid_mask):
    me_set = set(tuple(s) for s in me)
    opp_set = set(tuple(s) for s in opp)
    occupied = me_set | opp_set
    valid_empty = []
    for r in range(N):
        for c in range(N):
            try:
                if valid_mask[r][c] and (r, c) not in occupied:
                    valid_empty.append((r, c))
            except: pass
    if not valid_empty:
        for r in range(N):
            for c in range(N):
                try:
                    if valid_mask[r][c]: return (r, c)
                except: pass
        return (7, 7)
    if not me_set and not opp_set:
        try:
            if valid_mask[7][7]: return (7, 7)
        except: pass
    for m in valid_empty:
        if is_winning_move(me_set, m, valid_mask):
            return m
    for m in valid_empty:
        if is_winning_move(opp_set, m, valid_mask):
            return m
    my_groups = []; visited = set()
    for s in me_set:
        if s in visited: continue
        g = group_of(s, me_set); visited |= g; my_groups.append(g)
    opp_groups = []; visited = set()
    for s in opp_set:
        if s in visited: continue
        g = group_of(s, opp_set); visited |= g; opp_groups.append(g)
    group_corners = [set(c for c in CORNERS_SET if c in g) for g in my_groups]
    group_edges = [set(edge_of(*s) for s in g if edge_of(*s) >= 0) for g in my_groups]
    opp_gc = [set(c for c in CORNERS_SET if c in g) for g in opp_groups]
    opp_ge = [set(edge_of(*s) for s in g if edge_of(*s) >= 0) for g in opp_groups]
    stone_to_my = {}
    for i, g in enumerate(my_groups):
        for s in g: stone_to_my[s] = i
    stone_to_opp = {}
    for i, g in enumerate(opp_groups):
        for s in g: stone_to_opp[s] = i
    best_score = -1e18; best_move = valid_empty[0]
    for (r, c) in valid_empty:
        score = 0.0; my_adj = 0; opp_adj = 0
        my_ga = set(); opp_ga = set()
        for (nr, nc) in get_neighbors(r, c):
            if (nr, nc) in stone_to_my:
                my_adj += 1; my_ga.add(stone_to_my[(nr, nc)])
            elif (nr, nc) in stone_to_opp:
                opp_adj += 1; opp_ga.add(stone_to_opp[(nr, nc)])
        score += my_adj * 3 + opp_adj * 1.5
        score += len(my_ga) * 10 + len(opp_ga) * 4
        tc = set(); te = set()
        for i in my_ga:
            tc |= group_corners[i]; te |= group_edges[i]
        if (r, c) in CORNERS_SET:
            tc.add((r, c)); score += 6
        e_id = edge_of(r, c)
        if e_id >= 0:
            te.add(e_id); score += 3
        score += len(tc) ** 2 * 4 + len(te) ** 2 * 3
        otc = set(); ote = set()
        for i in opp_ga:
            otc |= opp_gc[i]; ote |= opp_ge[i]
        score += len(otc) * 2 + len(ote) * 1.5
        dist_axial = (abs(r-7) + abs(c-7) + abs(r+c-14)) / 2
        score -= dist_axial * 0.2
        if score > best_score:
            best_score = score; best_move = (r, c)
    return best_move
