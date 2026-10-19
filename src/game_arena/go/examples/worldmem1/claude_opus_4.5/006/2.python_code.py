
import random

def policy(me, opponent, memory):
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def neighbors(r, c):
        result = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                result.append((nr, nc))
        return result
    
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
                elif nb not in all_stones:
                    liberties.add(nb)
        return group, liberties
    
    def would_capture(r, c, my_stones, opp_stones):
        captured = set()
        for nb in neighbors(r, c):
            if nb in opp_stones:
                group, libs = get_group_and_liberties(nb, opp_stones)
                new_libs = libs - {(r, c)}
                if len(new_libs) == 0:
                    captured |= group
        return captured
    
    def is_legal(r, c):
        if (r, c) in all_stones:
            return False
        temp_opp = opp_set - would_capture(r, c, me_set, opp_set)
        temp_me = me_set | {(r, c)}
        temp_all = temp_me | temp_opp
        _, libs = get_group_and_liberties((r, c), temp_me)
        return len(libs) > 0 or len(would_capture(r, c, me_set, opp_set)) > 0
    
    def score_move(r, c):
        score = 0
        captures = would_capture(r, c, me_set, opp_set)
        score += len(captures) * 100
        
        for nb in neighbors(r, c):
            if nb in me_set:
                group, libs = get_group_and_liberties(nb, me_set)
                if len(libs) == 1:
                    score += 80
        
        for nb in neighbors(r, c):
            if nb in opp_set:
                group, libs = get_group_and_liberties(nb, opp_set)
                if len(libs) == 2:
                    score += 30
        
        star_points = [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]
        if (r, c) in star_points:
            score += 15
        
        if r in [1,19] or c in [1,19]:
            score -= 5
        elif r in [2,18] or c in [2,18]:
            score -= 2
        
        if 3 <= r <= 5 and 3 <= c <= 5: score += 8
        elif 3 <= r <= 5 and 14 <= c <= 17: score += 8
        elif 14 <= r <= 17 and 3 <= c <= 5: score += 8
        elif 14 <= r <= 17 and 14 <= c <= 17: score += 8
        
        for stone in me:
            dist = abs(r - stone[0]) + abs(c - stone[1])
            if 2 <= dist <= 4:
                score += 5
            elif dist == 1:
                score += 3
        
        return score + random.random() * 0.1
    
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal(r, c):
                legal_moves.append((r, c))
    
    if not legal_moves:
        return ((0, 0), memory)
    
    best_move = max(legal_moves, key=lambda m: score_move(m[0], m[1]))
    return (best_move, memory)
