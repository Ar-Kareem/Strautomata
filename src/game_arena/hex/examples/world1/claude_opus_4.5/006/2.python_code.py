
import random
import math
import time
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set | opp_set
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in all_occupied]
    
    if not empty:
        return (0, 0)  # Should never happen
    
    if len(empty) == SIZE * SIZE:
        # First move - take center
        return (5, 5)
    
    def get_neighbors(r, c):
        candidates = [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
        return [(nr, nc) for nr, nc in candidates if 0 <= nr < SIZE and 0 <= nc < SIZE]
    
    def check_win(stones, player_color):
        if len(stones) < SIZE:
            return False
        stone_set = set(stones)
        parent = {s: s for s in stone_set}
        rank = {s: 0 for s in stone_set}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                if rank[rx] < rank[ry]:
                    rx, ry = ry, rx
                parent[ry] = rx
                if rank[rx] == rank[ry]:
                    rank[rx] += 1
        
        for s in stone_set:
            for n in get_neighbors(s[0], s[1]):
                if n in stone_set:
                    union(s, n)
        
        if player_color == 'b':
            top = [s for s in stone_set if s[0] == 0]
            bottom = [s for s in stone_set if s[0] == SIZE - 1]
            for t in top:
                for b in bottom:
                    if find(t) == find(b):
                        return True
        else:
            left = [s for s in stone_set if s[1] == 0]
            right = [s for s in stone_set if s[1] == SIZE - 1]
            for l in left:
                for r in right:
                    if find(l) == find(r):
                        return True
        return False
    
    def simulate(my_stones, opp_stones, my_turn, my_color):
        my_s = set(my_stones)
        opp_s = set(opp_stones)
        opp_color = 'w' if my_color == 'b' else 'b'
        avail = [pos for pos in empty if pos not in my_s and pos not in opp_s]
        random.shuffle(avail)
        
        turn = my_turn
        for move in avail:
            if turn:
                my_s.add(move)
            else:
                opp_s.add(move)
            turn = not turn
        
        if check_win(my_s, my_color):
            return 1
        elif check_win(opp_s, opp_color):
            return 0
        return 0.5
    
    # MCTS
    wins = defaultdict(float)
    visits = defaultdict(int)
    
    start_time = time.time()
    iterations = 0
    
    while time.time() - start_time < 0.85:
        for move in empty:
            new_me = me_set | {move}
            if check_win(new_me, color):
                return move
            result = simulate(new_me, opp_set, False, color)
            wins[move] += result
            visits[move] += 1
        iterations += 1
        if iterations > 50:
            break
    
    best_move = max(empty, key=lambda m: wins[m] / visits[m] if visits[m] > 0 else 0)
    return best_move
