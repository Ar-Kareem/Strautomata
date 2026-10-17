
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    from random import random
    
    N = 19
    my = frozenset(me)
    opp = frozenset(opponent)
    
    def nbrs(p):
        r, c = p
        return [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                if 1 <= r+dr <= N and 1 <= c+dc <= N]
    
    def diag(p):
        r, c = p
        return [(r+dr, c+dc) for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]
                if 1 <= r+dr <= N and 1 <= c+dc <= N]
    
    def grp_lib(start, player, enemy):
        grp, lib = {start}, set()
        stk = [start]
        while stk:
            p = stk.pop()
            for n in nbrs(p):
                if n in player and n not in grp:
                    grp.add(n)
                    stk.append(n)
                elif n not in player and n not in enemy:
                    lib.add(n)
        return grp, lib
    
    def simulate(mv, pl, en):
        if mv in pl or mv in en:
            return False, None, None, 0
        new_pl = set(pl) | {mv}
        new_en = set(en)
        cap = 0
        for n in nbrs(mv):
            if n in new_en:
                g, l = grp_lib(n, frozenset(new_en), frozenset(new_pl))
                if not l:
                    cap += len(g)
                    new_en -= g
        _, my_l = grp_lib(mv, frozenset(new_pl), frozenset(new_en))
        if not my_l and cap == 0:
            return False, None, None, 0
        return True, frozenset(new_pl), frozenset(new_en), cap
    
    def is_eye(p):
        if not all(n in my for n in nbrs(p)):
            return False
        r, c = p
        on_edge = (r in [1, N]) or (c in [1, N])
        bad = sum(1 for d in diag(p) if d in opp or d not in my)
        return bad <= (0 if on_edge else 1)
    
    occupied = my | opp
    empty = [(r, c) for r in range(1, N+1) for c in range(1, N+1) if (r, c) not in occupied]
    legal = [m for m in empty if simulate(m, my, opp)[0] and not is_eye(m)]
    
    if not legal:
        return (0, 0)
    
    def score(mv):
        ok, new_my, new_opp, cap = simulate(mv, my, opp)
        r, c = mv
        s = cap * 500.0
        
        seen = set()
        for st in my:
            if st in seen:
                continue
            g, l = grp_lib(st, my, opp)
            seen |= g
            if len(l) == 1 and mv in l:
                _, nl = grp_lib(st, new_my, new_opp)
                s += len(g) * (400 if len(nl) >= 2 else 100)
        
        for n in nbrs(mv):
            if n in opp:
                g, l = grp_lib(n, new_opp, new_my)
                if len(l) == 1:
                    s += len(g) * 150
                elif len(l) == 2:
                    s += len(g) * 30
        
        for n in nbrs(mv):
            if n in opp:
                _, old_l = grp_lib(n, opp, my)
                _, new_l = grp_lib(n, opp, new_my)
                s += (len(old_l) - len(new_l)) * 15
        
        edge = min(r-1, N-r, c-1, N-c)
        s += [-25, -10, 10, 15, 12, 9, 7, 5, 4, 3][min(edge, 9)]
        
        turn = len(my) + len(opp)
        if turn < 30:
            if mv in {(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)}:
                s += 55
            elif mv in {(3,4),(4,3),(3,16),(4,17),(16,3),(17,4),(16,17),(17,16)}:
                s += 50
            elif mv in {(3,3),(3,17),(17,3),(17,17)}:
                s += 45
        
        own_adj = [n for n in nbrs(mv) if n in my]
        if len(own_adj) == 1:
            s += 18
        elif len(own_adj) == 2:
            n1, n2 = own_adj
            if abs(n1[0]-n2[0]) + abs(n1[1]-n2[1]) == 1:
                s -= 10
            else:
                s += 22
        
        s += sum(12 for n in nbrs(mv) if n in opp)
        
        if my:
            d = min(abs(r-mr) + abs(c-mc) for mr, mc in my)
            if 2 <= d <= 5:
                s += 10
            elif d == 1:
                s += 5
            elif d > 8:
                s -= 5
        
        s += random() * 0.3
        return s
    
    return max(legal, key=score)
