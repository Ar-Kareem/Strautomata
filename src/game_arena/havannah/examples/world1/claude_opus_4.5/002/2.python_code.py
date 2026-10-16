
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    me_set = set(me)
    opp_set = set(opp)
    
    # Get valid moves
    valid_moves = [(r, c) for r in range(N) for c in range(N) 
                   if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    if not valid_moves:
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    return (r, c)
    
    # Hexagonal neighbors
    def get_neighbors(r, c):
        deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        return [(r + dr, c + dc) for dr, dc in deltas 
                if 0 <= r + dr < N and 0 <= c + dc < N and valid_mask[r + dr][c + dc]]
    
    # Identify corners and edges
    corners = set()
    edges = defaultdict(set)  # edge_id -> set of positions
    
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c]:
                continue
            neighs = get_neighbors(r, c)
            valid_neighs = [n for n in neighs if valid_mask[n[0]][n[1]]]
            if len(valid_neighs) <= 3:
                corners.add((r, c))
            elif len(valid_neighs) == 4:
                # Edge cell - determine which edge
                if r == 0: edges[0].add((r, c))
                elif r == N - 1: edges[3].add((r, c))
                elif c == 0: edges[1].add((r, c))
                elif c == N - 1: edges[4].add((r, c))
                elif r + c == N - 1: edges[2].add((r, c))
                elif r + c == 2 * (N - 1) - (N - 1): edges[5].add((r, c))
    
    def get_edge_id(r, c):
        if (r, c) in corners:
            return -1
        for eid, cells in edges.items():
            if (r, c) in cells:
                return eid
        return -1
    
    # Union-Find for connectivity
    def find_component(stones):
        parent = {s: s for s in stones}
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        for s in stones:
            for n in get_neighbors(s[0], s[1]):
                if n in stones:
                    union(s, n)
        components = defaultdict(set)
        for s in stones:
            components[find(s)].add(s)
        return list(components.values())
    
    def check_win(stones):
        stones_set = set(stones)
        comps = find_component(stones_set)
        for comp in comps:
            comp_corners = [s for s in comp if s in corners]
            comp_edges = set(get_edge_id(s[0], s[1]) for s in comp if get_edge_id(s[0], s[1]) >= 0)
            if len(comp_corners) >= 2: return True  # Bridge
            if len(comp_edges) >= 3: return True  # Fork
        return False
    
    # Check immediate wins
    for move in valid_moves:
        if check_win(me_set | {move}):
            return move
    
    # Block opponent wins
    for move in valid_moves:
        if check_win(opp_set | {move}):
            return move
    
    # Heuristic scoring
    center = N // 2
    def score_move(move):
        r, c = move
        score = 0
        # Prefer center
        dist_center = abs(r - center) + abs(c - center)
        score -= dist_center * 0.5
        # Prefer connecting to own stones
        for n in get_neighbors(r, c):
            if n in me_set:
                score += 3
            elif n in opp_set:
                score += 0.5
        # Edge/corner bonuses for strategic positions
        if (r, c) in corners:
            score += 2
        elif get_edge_id(r, c) >= 0:
            score += 1
        return score
    
    best_move = max(valid_moves, key=score_move)
    return best_move
