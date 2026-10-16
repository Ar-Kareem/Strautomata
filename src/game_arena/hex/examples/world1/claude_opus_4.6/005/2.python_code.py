
import random
import time
import heapq
from math import log, sqrt

def policy(me, opp, color):
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield nr, nc
    
    def get_empty():
        return [(r,c) for r in range(SIZE) for c in range(SIZE) if (r,c) not in occupied]
    
    empty = get_empty()
    if not empty:
        return (0,0)
    if not me and not opp:
        return (5, 5)
    if not me:
        if (5,5) not in opp_set:
            return (5,5)
        return (5,4)
    
    # Dijkstra shortest path for a player
    def dijkstra_cost(stones_set, player_color):
        # Cost to connect the two sides
        dist = {}
        heap = []
        for r in range(SIZE):
            for c in range(SIZE):
                if (r,c) in opp_set if player_color == color else (r,c) in me_set:
                    continue
                cost = 0 if (r,c) in stones_set else 1
                if player_color == 'b' and r == 0:
                    heapq.heappush(heap, (cost, r, c))
                    dist[(r,c)] = cost
                elif player_color == 'w' and c == 0:
                    heapq.heappush(heap, (cost, r, c))
                    dist[(r,c)] = cost
        
        while heap:
            d, r, c = heapq.heappop(heap)
            if d > dist.get((r,c), float('inf')):
                continue
            if player_color == 'b' and r == SIZE-1:
                return d
            if player_color == 'w' and c == SIZE-1:
                return d
            for nr, nc in neighbors(r, c):
                if player_color == color and (nr,nc) in opp_set:
                    continue
                if player_color != color and (nr,nc) in me_set:
                    continue
                nd = d + (0 if (nr,nc) in stones_set else 1)
                if nd < dist.get((nr,nc), float('inf')):
                    dist[(nr,nc)] = nd
                    heapq.heappush(heap, (nd, nr, nc))
        return float('inf')
    
    # Find cells on shortest path using Dijkstra
    def best_moves_dijkstra(my_stones, my_color, block_set):
        scores = []
        for r, c in empty:
            new_stones = my_stones | {(r,c)}
            cost = dijkstra_cost(new_stones, my_color)
            scores.append((cost, r, c))
        scores.sort()
        return [(r,c) for _,r,c in scores[:15]]
    
    opp_color = 'w' if color == 'b' else 'b'
    
    # Get candidate moves
    candidates = set()
    for r, c in me | opp:
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in occupied:
                candidates.add((nr, nc))
                for nr2, nc2 in neighbors(nr, nc):
                    if (nr2, nc2) not in occupied:
                        candidates.add((nr2, nc2))
    
    if not candidates:
        candidates = set(empty)
    
    # Add some strategic cells
    for r, c in [(5,5),(4,5),(5,4),(6,5),(5,6),(4,6),(6,4)]:
        if (r,c) not in occupied:
            candidates.add((r,c))
    
    candidates = list(candidates)
    
    # Score candidates with Dijkstra
    def score_move(rc):
        r, c = rc
        new_me = me_set | {(r,c)}
        my_cost = dijkstra_cost(new_me, color)
        new_opp = opp_set | {(r,c)}
        opp_cost_with = dijkstra_cost(new_opp, opp_color)
        opp_cost_without = dijkstra_cost(opp_set, opp_color)
        # Lower my cost + block opponent
        return my_cost - 0.5 * (opp_cost_with - opp_cost_without)
    
    scored = [(score_move(m), m) for m in candidates]
    scored.sort()
    top_moves = [m for _, m in scored[:20]]
    
    # MCTS
    start = time.time()
    
    class Node:
        __slots__ = ['move','parent','children','wins','visits','untried','player_is_me']
        def __init__(self, move, parent, untried, player_is_me):
            self.move = move
            self.parent = parent
            self.children = []
            self.wins = 0.0
            self.visits = 0
            self.untried = untried
            self.player_is_me = player_is_me
    
    def check_win(stones, pl_color):
        if len(stones) < SIZE:
            return False
        visited = set()
        start_cells = []
        for r, c in stones:
            if pl_color == 'b' and r == 0:
                start_cells.append((r,c))
            elif pl_color == 'w' and c == 0:
                start_cells.append((r,c))
        stack = list(start_cells)
        while stack:
            r, c = stack.pop()
            if (r,c) in visited:
                continue
            visited.add((r,c))
            if pl_color == 'b' and r == SIZE-1:
                return True
            if pl_color == 'w' and c == SIZE-1:
                return True
            for nr, nc in neighbors(r, c):
                if (nr,nc) in stones and (nr,nc) not in visited:
                    stack.append((nr,nc))
        return False
    
    def rollout(my_s, op_s, is_my_turn, emp):
        random.shuffle(emp)
        ms = set(my_s)
        os = set(op_s)
        turn = is_my_turn
        for cell in emp:
            if turn:
                ms.add(cell)
            else:
                os.add(cell)
            turn = not turn
        if check_win(ms, color):
            return 1.0
        return 0.0
    
    root_untried = list(top_moves)
    random.shuffle(root_untried)
    root = Node(None, None, root_untried, True)
    
    iterations = 0
    while time.time() - start < 0.85:
        node = root
        sim_me = set(me_set)
        sim_opp = set(opp_set)
        sim_empty = list(set(empty) - set(top_moves))
        
        # Selection
        while not node.untried and node.children:
            node = max(node.children, key=lambda c: c.wins/c.visits + 1.41*sqrt(log(node.visits)/c.visits))
            if node.player_is_me:
                sim_me.add(node.move)
            else:
                sim_opp.add(node.move)
            if node.move in sim_empty:
                sim_empty.remove(node.move)
        
        # Expansion
        if node.untried:
            m = node.untried.pop()
            if node.player_is_me:
                sim_me.add(m)
            else:
                sim_opp.add(m)
            if m in sim_empty:
                sim_empty.remove(m)
            child = Node(m, node, [], not node.player_is_me)
            node.children.append(child)
            node = child
        
        # Rollout
        result = rollout(sim_me, sim_opp, not node.player_is_me if node.move else True, list(sim_empty))
        
        # Backprop
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent
        iterations += 1
    
    if root.children:
        best = max(root.children, key=lambda c: c.visits)
        return best.move
    
    return top_moves[0] if top_moves else empty[0]
