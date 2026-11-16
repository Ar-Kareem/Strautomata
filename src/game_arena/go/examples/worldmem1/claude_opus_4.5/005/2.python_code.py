
import random

def policy(me, opponent, memory):
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield (nr, nc)
    
    def get_group_and_liberties(start, stones_set):
        group = set()
        liberties = set()
        stack = [start]
        while stack:
            pos = stack.pop()
            if pos in group:
                continue
            group.add(pos)
            for nb in neighbors(*pos):
                if nb in stones_set and nb not in group:
                    stack.append(nb)
                elif nb not in occupied:
                    liberties.add(nb)
        return group, liberties
    
    def would_capture(move, opp_stones):
        for nb in neighbors(*move):
            if nb in opp_stones:
                temp_occ = occupied | {move}
                grp, libs = set(), set()
                stk = [nb]
                while stk:
                    p = stk.pop()
                    if p in grp: continue
                    grp.add(p)
                    for n2 in neighbors(*p):
                        if n2 in opp_stones and n2 not in grp:
                            stk.append(n2)
                        elif n2 not in temp_occ:
                            libs.add(n2)
                if len(libs) == 0:
                    return True
        return False
    
    def is_suicide(move, my_stones, opp_stones):
        if would_capture(move, opp_stones):
            return False
        temp_me = my_stones | {move}
        temp_occ = occupied | {move}
        grp, libs = set(), set()
        stk = [move]
        while stk:
            p = stk.pop()
            if p in grp: continue
            grp.add(p)
            for nb in neighbors(*p):
                if nb in temp_me and nb not in grp:
                    stk.append(nb)
                elif nb not in temp_occ:
                    libs.add(nb)
        return len(libs) == 0
    
    def score_move(r, c):
        score = 0.0
        if would_capture((r,c), opp_set):
            score += 100
        for nb in neighbors(r, c):
            if nb in me_set:
                score += 10
            elif nb in opp_set:
                score += 5
        dist_center = abs(r - 10) + abs(c - 10)
        score += (19 - dist_center) * 0.3
        if (r, c) in [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]:
            score += 8
        if r in [3,4] and c in [3,4,16,17] or r in [16,17] and c in [3,4,16,17]:
            score += 6
        return score + random.random() * 0.1
    
    empty = [(r,c) for r in range(1, BOARD_SIZE+1) for c in range(1, BOARD_SIZE+1) if (r,c) not in occupied]
    legal = [m for m in empty if not is_suicide(m, me_set, opp_set)]
    
    if not legal:
        return ((0, 0), memory)
    
    best_move = max(legal, key=lambda m: score_move(*m))
    return (best_move, memory)
