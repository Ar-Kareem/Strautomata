
import random
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                yield nr, nc
    
    def get_group(r, c, stones_set):
        group = set()
        queue = deque([(r, c)])
        while queue:
            cr, cc = queue.popleft()
            if (cr, cc) in group:
                continue
            if (cr, cc) in stones_set:
                group.add((cr, cc))
                for nr, nc in neighbors(cr, cc):
                    if (nr, nc) not in group and (nr, nc) in stones_set:
                        queue.append((nr, nc))
        return group
    
    def get_liberties(group, me_s, opp_s):
        libs = set()
        for r, c in group:
            for nr, nc in neighbors(r, c):
                if (nr, nc) not in me_s and (nr, nc) not in opp_s:
                    libs.add((nr, nc))
        return libs
    
    def would_capture(r, c, my_stones, their_stones):
        captures = []
        for nr, nc in neighbors(r, c):
            if (nr, nc) in their_stones:
                group = get_group(nr, nc, their_stones)
                libs = get_liberties(group, their_stones, my_stones | {(r, c)})
                if len(libs) == 0:
                    captures.extend(group)
        return captures
    
    def is_legal(r, c, my_stones, their_stones):
        if (r, c) in my_stones or (r, c) in their_stones:
            return False
        captures = would_capture(r, c, my_stones, their_stones)
        if captures:
            return True
        new_my = my_stones | {(r, c)}
        group = get_group(r, c, new_my)
        libs = get_liberties(group, new_my, their_stones)
        return len(libs) > 0
    
    # Find capturing moves
    for r, c in list(opp_set):
        group = get_group(r, c, opp_set)
        libs = get_liberties(group, opp_set, me_set)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move[0], move[1], me_set, opp_set):
                return move
    
    # Find defensive moves (save my groups in atari)
    for r, c in list(me_set):
        group = get_group(r, c, me_set)
        libs = get_liberties(group, me_set, opp_set)
        if len(libs) == 1:
            lib = list(libs)[0]
            if is_legal(lib[0], lib[1], me_set, opp_set):
                return lib
    
    # Score-based move selection
    def score_move(r, c):
        score = 0
        dist_center = abs(r - 10) + abs(c - 10)
        score -= dist_center * 0.5
        
        if r in [4, 10, 16] and c in [4, 10, 16]:
            score += 15
        if 4 <= r <= 16 and 4 <= c <= 16:
            score += 5
        
        adj_me = sum(1 for nr, nc in neighbors(r, c) if (nr, nc) in me_set)
        adj_opp = sum(1 for nr, nc in neighbors(r, c) if (nr, nc) in opp_set)
        score += adj_opp * 3
        score += adj_me * 1
        
        return score
    
    candidates = []
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal(r, c, me_set, opp_set):
                candidates.append((r, c, score_move(r, c)))
    
    if candidates:
        candidates.sort(key=lambda x: -x[2])
        return (candidates[0][0], candidates[0][1])
    
    return (0, 0)
