
import numpy as np
import time
import random
from collections import deque
import math

def policy(me, opp, valid_mask):
    board_size = len(valid_mask)
    me_set = set(me)
    opp_set = set(opp)
    
    valid_moves = [(r, c) for r in range(board_size) for c in range(board_size) 
                   if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    if not valid_moves:
        for r in range(board_size):
            for c in range(board_size):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # Hexagonal neighbors
    def neighbors(r, c):
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c-1)]
    
    def valid_hex(r, c):
        return 0 <= r < board_size and 0 <= c < board_size and valid_mask[r][c]
    
    # Identify corners and edges
    # For a hex board stored in 2D with size N, the valid cells form a hexagon
    # Corners are the 6 corner cells of the hexagonal board
    N = board_size  # 15 for size-8 Havannah (board_size = 2*8 - 1)
    S = (N + 1) // 2  # 8
    
    def get_corners():
        corners = set()
        # Find all valid cells and identify corners as valid cells with exactly 2 valid neighbors
        # Actually, let's compute corners geometrically
        # For a hex board of size S stored in NxN grid (N = 2S-1):
        # Corners at: (0,0), (0, S-1), (S-1, 0), (S-1, N-1), (N-1, S-1), (N-1, N-1)
        candidates = []
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    n_valid = sum(1 for nr, nc in neighbors(r, c) if valid_hex(nr, nc))
                    if n_valid <= 2:
                        candidates.append((r, c))
        return set(candidates)
    
    def get_edges():
        corners = get_corners()
        edges = {}  # cell -> edge_id
        edge_cells = []
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in corners:
                    n_valid = sum(1 for nr, nc in neighbors(r, c) if valid_hex(nr, nc))
                    if n_valid < 6:
                        edge_cells.append((r, c))
        
        # Group edge cells into 6 edges using BFS excluding corners
        edge_id = 0
        visited = set()
        for cell in edge_cells:
            if cell not in visited:
                q = deque([cell])
                visited.add(cell)
                while q:
                    cr, cc = q.popleft()
                    edges[(cr, cc)] = edge_id
                    for nr, nc in neighbors(cr, cc):
                        if (nr, nc) in edge_cells and (nr, nc) not in visited and (nr, nc) not in corners:
                            # Check adjacency along edge
                            if (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
                edge_id += 1
        return corners, edges
    
    corners, edges = get_edges()
    
    def check_win(stones_set):
        if len(stones_set) < 3:
            return False
        
        # Check bridge: two corners connected
        corner_stones = stones_set & corners
        if len(corner_stones) >= 2:
            corner_list = list(corner_stones)
            for i in range(len(corner_list)):
                for j in range(i+1, len(corner_list)):
                    if connected(corner_list[i], corner_list[j], stones_set):
                        return True
        
        # Check fork: three edges connected
        edge_stones = {e: [] for e in set(edges.values())}
        for s in stones_set:
            if s in edges:
                edge_stones[edges[s]].append(s)
        touched_edges = [eid for eid, cells in edge_stones.items() if cells]
        if len(touched_edges) >= 3:
            # Check if three edge cells from different edges are in the same component
            components = get_components(stones_set)
            for comp in components:
                comp_edges = set()
                for s in comp:
                    if s in edges:
                        comp_edges.add(edges[s])
                if len(comp_edges) >= 3:
                    return True
        
        # Check ring
        if check_ring(stones_set):
            return True
        
        return False
    
    def connected(a, b, stones_set):
        if a == b:
            return True
        visited = {a}
        q = deque([a])
        while q:
            cr, cc = q.popleft()
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) == b:
                    return True
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return False
    
    def get_components(stones_set):
        visited = set()
        components = []
        for s in stones_set:
            if s not in visited:
                comp = set()
                q = deque([s])
                visited.add(s)
                while q:
                    cr, cc = q.popleft()
                    comp.add((cr, cc))
                    for nr, nc in neighbors(cr, cc):
                        if (nr, nc) in stones_set and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append((nr, nc))
                components.append(comp)
        return components
    
    def check_ring(stones_set):
        # A ring exists if there's a cycle in the stone graph
        # Equivalent: some connected component has more edges than vertices - 1
        # In hex graph: if |edges_in_component| > |nodes_in_component| - 1
        for comp in get_components(stones_set):
            if len(comp) < 6:
                continue
            edge_count = 0
            for r, c in comp:
                for nr, nc in neighbors(r, c):
                    if (nr, nc) in comp:
                        edge_count += 1
            edge_count //= 2
            if edge_count > len(comp) - 1:
                return True
        return False
    
    # Check immediate wins / blocks
    for move in valid_moves:
        test = me_set | {move}
        if check_win(test):
            return move
    
    for move in valid_moves:
        test = opp_set | {move}
        if check_win(test):
            return move
    
    # Heuristic scoring for move ordering
    center = (N // 2, N // 2)
    
    def score_move(move):
        r, c = move
        s = 0
        # Adjacency to own stones
        for nr, nc in neighbors(r, c):
            if (nr, nc) in me_set:
                s += 3
            if (nr, nc) in opp_set:
                s += 1
        # Center preference
        dist = abs(r - center[0]) + abs(c - center[1])
        s -= dist * 0.1
        return s
    
    scored = sorted(valid_moves, key=score_move, reverse=True)
    
    # MCTS
    start_time = time.time()
    time_limit = 0.85
    
    move_wins = {m: 0 for m in scored[:60]}
    move_visits = {m: 0 for m in scored[:60]}
    candidate_moves = list(move_wins.keys())
    
    if not candidate_moves:
        candidate_moves = valid_moves
        move_wins = {m: 0 for m in candidate_moves}
        move_visits = {m: 0 for m in candidate_moves}
    
    iterations = 0
    while time.time() - start_time < time_limit:
        # Select move using UCB1
        total_visits = iterations + 1
        best_ucb = -float('inf')
        best_move = candidate_moves[0]
        for m in candidate_moves:
            if move_visits[m] == 0:
                best_move = m
                break
            ucb = move_wins[m] / move_visits[m] + 1.41 * math.sqrt(math.log(total_visits) / move_visits[m])
            if ucb > best_ucb:
                best_ucb = ucb
                best_move = m
        
        # Simulate
        sim_me = me_set | {best_move}
        sim_opp = set(opp_set)
        sim_valid = [v for v in valid_moves if v != best_move]
        random.shuffle(sim_valid)
        
        current_is_opp = True
        result = 0
        
        # Quick rollout (limited depth)
        max_depth = min(30, len(sim_valid))
        for i in range(max_depth):
            if i >= len(sim_valid):
                break
            mv = sim_valid[i]
            if current_is_opp:
                sim_opp.add(mv)
                if len(sim_opp) >= 6 and check_ring(sim_opp):
                    result = -1
                    break
            else:
                sim_me.add(mv)
                if len(sim_me) >= 6 and check_ring(sim_me):
                    result = 1
                    break
            current_is_opp = not current_is_opp
        
        move_visits[best_move] += 1
        if result == 1:
            move_wins[best_move] += 1
        elif result == 0:
            move_wins[best_move] += 0.5
        
        iterations += 1
        if iterations > 500:
            break
    
    if iterations > 0:
        best_move = max(candidate_moves, key=lambda m: move_wins[m] / max(move_visits[m], 1))
        return best_move
    
    return scored[0] if scored else valid_moves[0]
