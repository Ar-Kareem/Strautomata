
import random
import time
from collections import defaultdict
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in occupied]
    
    if not empty:
        return (0, 0)
    
    if len(me) == 0:
        center = (5, 5)
        if center not in occupied:
            return center
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, -1), (-1, 1)]:
            nr, nc = 5 + dr, 5 + dc
            if (nr, nc) not in occupied:
                return (nr, nc)
    
    def get_neighbors(r, c):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, -1), (-1, 1)]
        return [(r + dr, c + dc) for dr, dc in directions if 0 <= r + dr < SIZE and 0 <= c + dc < SIZE]
    
    class UnionFind:
        def __init__(self):
            self.parent = {}
        
        def find(self, x):
            if x not in self.parent:
                self.parent[x] = x
            if self.parent[x] != x:
                self.parent[x] = self.find(self.parent[x])
            return self.parent[x]
        
        def union(self, x, y):
            px, py = self.find(x), self.find(y)
            if px != py:
                self.parent[px] = py
    
    def check_win(stones, player_color):
        if len(stones) < SIZE:
            return False
        uf = UnionFind()
        for r, c in stones:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones:
                    uf.union((r, c), (nr, nc))
        
        if player_color == 'b':
            top = [s for s in stones if s[0] == 0]
            bottom = [s for s in stones if s[0] == SIZE - 1]
            for t in top:
                for b in bottom:
                    if uf.find(t) == uf.find(b):
                        return True
        else:
            left = [s for s in stones if s[1] == 0]
            right = [s for s in stones if s[1] == SIZE - 1]
            for l in left:
                for r in right:
                    if uf.find(l) == uf.find(r):
                        return True
        return False
    
    def simulate(my_stones, opp_stones, my_turn, my_color):
        my_stones = set(my_stones)
        opp_stones = set(opp_stones)
        moves = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in my_stones and (r, c) not in opp_stones]
        random.shuffle(moves)
        
        for move in moves:
            if my_turn:
                my_stones.add(move)
                if check_win(my_stones, my_color):
                    return 1
            else:
                opp_stones.add(move)
                opp_color = 'w' if my_color == 'b' else 'b'
                if check_win(opp_stones, opp_color):
                    return 0
            my_turn = not my_turn
        return 0.5
    
    start_time = time.time()
    time_limit = 0.85
    
    wins = defaultdict(float)
    visits = defaultdict(int)
    
    priority_moves = []
    for move in empty:
        score = 0
        r, c = move
        score -= abs(r - 5) + abs(c - 5)
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                score += 10
            elif (nr, nc) in opp_set:
                score += 5
        priority_moves.append((score, move))
    priority_moves.sort(reverse=True)
    candidate_moves = [m for _, m in priority_moves[:min(30, len(priority_moves))]]
    
    if not candidate_moves:
        candidate_moves = empty
    
    iterations = 0
    while time.time() - start_time < time_limit:
        for _ in range(50):
            if visits:
                total_visits = sum(visits[m] for m in candidate_moves)
                best_ucb = -float('inf')
                move = candidate_moves[0]
                for m in candidate_moves:
                    if visits[m] == 0:
                        move = m
                        break
                    ucb = wins[m] / visits[m] + 1.4 * math.sqrt(math.log(total_visits + 1) / visits[m])
                    if ucb > best_ucb:
                        best_ucb = ucb
                        move = m
            else:
                move = random.choice(candidate_moves)
            
            new_me = me_set | {move}
            if check_win(new_me, color):
                return move
            
            opp_color = 'w' if color == 'b' else 'b'
            result = simulate(new_me, opp_set, False, color)
            wins[move] += result
            visits[move] += 1
        iterations += 50
    
    if visits:
        best_move = max(candidate_moves, key=lambda m: visits[m])
    else:
        best_move = candidate_moves[0]
    
    return best_move
