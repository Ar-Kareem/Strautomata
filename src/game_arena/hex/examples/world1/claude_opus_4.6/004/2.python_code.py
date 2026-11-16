
import time
import random
import math

def policy(me, opp, color):
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in occupied]
    
    if not empty:
        return me[0]  # shouldn't happen
    
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    if len(me) == 0 and len(opp) == 1 and (5, 5) in opp_set:
        return (4, 5)
    if len(me) == 0:
        return (5, 5)
    
    NEIGHBORS = {}
    for r in range(SIZE):
        for c in range(SIZE):
            nbrs = []
            for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    nbrs.append((nr, nc))
            NEIGHBORS[(r, c)] = nbrs
    
    def check_win(stones_set, player_color):
        if len(stones_set) < SIZE:
            return False
        parent = {}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            a, b = find(a), find(b)
            if a != b:
                parent[a] = b
        
        START, END = 'S', 'E'
        parent[START] = START
        parent[END] = END
        
        for s in stones_set:
            parent[s] = s
        
        for s in stones_set:
            r, c = s
            if player_color == 'b':
                if r == 0: union(s, START)
                if r == SIZE - 1: union(s, END)
            else:
                if c == 0: union(s, START)
                if c == SIZE - 1: union(s, END)
            for nb in NEIGHBORS[s]:
                if nb in stones_set:
                    union(s, nb)
        
        return find(START) == find(END)
    
    def rollout(me_s, opp_s, empty_list):
        random.shuffle(empty_list)
        me_r = set(me_s)
        opp_r = set(opp_s)
        turn = 0  # 0 = me, 1 = opp
        for move in empty_list:
            if turn == 0:
                me_r.add(move)
            else:
                opp_r.add(move)
            turn = 1 - turn
        
        opp_color = 'w' if color == 'b' else 'b'
        if check_win(me_r, color):
            return 1
        if check_win(opp_r, opp_color):
            return 0
        return 0.5
    
    start_time = time.time()
    move_scores = {m: [0, 0] for m in empty}
    
    time_limit = 0.85
    iterations = 0
    
    while time.time() - start_time < time_limit:
        for move in empty:
            if time.time() - start_time >= time_limit:
                break
            new_me = me_set | {move}
            new_empty = [m for m in empty if m != move]
            result = rollout(new_me, opp_set, new_empty)
            move_scores[move][0] += result
            move_scores[move][1] += 1
        iterations += 1
        if iterations >= 2 and time.time() - start_time > 0.3:
            break
    
    best_move = max(empty, key=lambda m: move_scores[m][0] / max(move_scores[m][1], 1))
    return best_move
