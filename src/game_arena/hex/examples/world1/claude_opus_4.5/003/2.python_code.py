
import random
import math
import time
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in me_set and (r, c) not in opp_set]
    
    if not empty:
        return me[0] if me else (0, 0)
    
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    if len(me) == 0 and len(opp) == 1:
        if (5, 5) not in opp_set:
            return (5, 5)
        return (5, 4)
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield (nr, nc)
    
    def check_win(stones, player_color):
        if len(stones) < SIZE:
            return False
        stone_set = set(stones)
        parent = {s: s for s in stones}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            pa, pb = find(a), find(b)
            if pa != pb:
                parent[pa] = pb
        for s in stones:
            for n in neighbors(s[0], s[1]):
                if n in stone_set:
                    union(s, n)
        if player_color == 'b':
            top = [s for s in stones if s[0] == 0]
            bot = [s for s in stones if s[0] == SIZE - 1]
            for t in top:
                for b in bot:
                    if find(t) == find(b):
                        return True
        else:
            left = [s for s in stones if s[1] == 0]
            right = [s for s in stones if s[1] == SIZE - 1]
            for l in left:
                for r in right:
                    if find(l) == find(r):
                        return True
        return False
    
    opp_color = 'w' if color == 'b' else 'b'
    
    def simulate(my_stones, opp_stones, my_turn):
        my_s = set(my_stones)
        op_s = set(opp_stones)
        emp = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in my_s and (r, c) not in op_s]
        random.shuffle(emp)
        turn = my_turn
        for move in emp:
            if turn:
                my_s.add(move)
                if check_win(my_s, color):
                    return 1
            else:
                op_s.add(move)
                if check_win(op_s, opp_color):
                    return 0
            turn = not turn
        return 0.5
    
    visits = defaultdict(int)
    wins = defaultdict(float)
    
    start_time = time.time()
    time_limit = 0.85
    
    iterations = 0
    while time.time() - start_time < time_limit:
        for move in empty:
            new_me = me_set | {move}
            if check_win(new_me, color):
                return move
            result = simulate(new_me, opp_set, False)
            visits[move] += 1
            wins[move] += result
            iterations += 1
            if time.time() - start_time >= time_limit:
                break
    
    if iterations == 0:
        return random.choice(empty)
    
    best_move = max(empty, key=lambda m: wins[m] / max(visits[m], 1) + 0.001 * (5.5 - abs(m[0] - 5)) + 0.001 * (5.5 - abs(m[1] - 5)))
    return best_move
