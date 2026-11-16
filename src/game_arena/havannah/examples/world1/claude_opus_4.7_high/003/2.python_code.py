
import numpy as np

N = 15
CORNERS = [(0,0),(0,7),(7,0),(7,14),(14,7),(14,14)]
CORNER_SET = set(CORNERS)
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)]

def neighbors(r, c, valid_set):
    return [(r+dr, c+dc) for dr,dc in DIRS if (r+dr, c+dc) in valid_set]

def edge_of(r, c):
    if (r,c) in CORNER_SET: return -1
    if r == 0: return 0
    if c-r == 7: return 1
    if c == 14: return 2
    if r == 14: return 3
    if r-c == 7: return 4
    if c == 0: return 5
    return -1

def get_components(stones_set, valid_set):
    visited = set()
    comps = []
    for s in stones_set:
        if s in visited: continue
        comp = {s}
        stack = [s]
        while stack:
            cur = stack.pop()
            for n in neighbors(cur[0], cur[1], valid_set):
                if n in stones_set and n not in comp:
                    comp.add(n)
                    stack.append(n)
        visited |= comp
        comps.append(comp)
    return comps

def has_ring(comp, valid_set, border_cells):
    outside = set()
    stack = []
    for cell in border_cells:
        if cell in comp: continue
        outside.add(cell)
        stack.append(cell)
    while stack:
        cur = stack.pop()
        for n in neighbors(cur[0], cur[1], valid_set):
            if n in comp or n in outside: continue
            outside.add(n)
            stack.append(n)
    for cell in valid_set:
        if cell not in comp and cell not in outside:
            return True
    return False

def check_win(stones_set, valid_set, border_cells):
    for comp in get_components(stones_set, valid_set):
        corners = sum(1 for c in CORNERS if c in comp)
        if corners >= 2: return True
        edges = set()
        for cell in comp:
            e = edge_of(cell[0], cell[1])
            if e >= 0: edges.add(e)
        if len(edges) >= 3: return True
        if len(comp) >= 6 and has_ring(comp, valid_set, border_cells):
            return True
    return False

def hex_dist(a, b):
    dr, dc = a[0]-b[0], a[1]-b[1]
    return (abs(dr) + abs(dc) + abs(dr-dc)) // 2

def score_move(r, c, me_set, opp_set, valid_set):
    my_adj = 0
    opp_adj = 0
    for n in neighbors(r,c,valid_set):
        if n in me_set: my_adj += 1
        elif n in opp_set: opp_adj += 1
    score = my_adj * 10 + opp_adj * 6
    score -= hex_dist((r,c), (7,7)) * 0.3
    for corner in CORNERS:
        d = hex_dist((r,c), corner)
        if d <= 4:
            score += (5-d) * 0.5
    return score

def policy(me, opp, valid_mask):
    valid_set = frozenset((r,c) for r in range(N) for c in range(N) if valid_mask[r][c])
    if not valid_set:
        return (7,7)
    border_cells = set()
    for (r,c) in valid_set:
        for dr,dc in DIRS:
            if (r+dr, c+dc) not in valid_set:
                border_cells.add((r,c))
                break
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [cell for cell in valid_set if cell not in occupied]
    if not empty:
        return next(iter(valid_set))
    if len(me) + len(opp) == 0 and (7,7) in valid_set:
        return (7,7)
    my_candidates = set()
    for s in me_set:
        for n in neighbors(s[0], s[1], valid_set):
            if n not in occupied:
                my_candidates.add(n)
    for move in my_candidates:
        if check_win(me_set | {move}, valid_set, border_cells):
            return move
    opp_candidates = set()
    for s in opp_set:
        for n in neighbors(s[0], s[1], valid_set):
            if n not in occupied:
                opp_candidates.add(n)
    blocks = []
    for move in opp_candidates:
        if check_win(opp_set | {move}, valid_set, border_cells):
            blocks.append(move)
    if blocks:
        return max(blocks, key=lambda m: score_move(m[0], m[1], me_set, opp_set, valid_set))
    best = max(empty, key=lambda m: score_move(m[0], m[1], me_set, opp_set, valid_set))
    return best
