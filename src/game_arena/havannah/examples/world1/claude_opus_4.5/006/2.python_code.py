
import numpy as np
from collections import defaultdict
import random
import time

# Hexagonal neighbors: same column (up/down), left column, right column
NEIGHBOR_OFFSETS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]

def get_neighbors(r, c, size=15):
    neighbors = []
    for dr, dc in NEIGHBOR_OFFSETS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            neighbors.append((nr, nc))
    return neighbors

def get_valid_neighbors(r, c, valid_mask):
    size = len(valid_mask)
    neighbors = []
    for dr, dc in NEIGHBOR_OFFSETS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size and valid_mask[nr][nc]:
            neighbors.append((nr, nc))
    return neighbors

def get_corners(valid_mask):
    size = len(valid_mask)
    corners = []
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c]:
                valid_neighs = get_valid_neighbors(r, c, valid_mask)
                if len(valid_neighs) == 3:
                    corners.append((r, c))
    return corners

def get_edge_cells(valid_mask, corners):
    size = len(valid_mask)
    corner_set = set(corners)
    edges = defaultdict(set)
    
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c] and (r, c) not in corner_set:
                valid_neighs = get_valid_neighbors(r, c, valid_mask)
                if len(valid_neighs) < 6:
                    if r == 0:
                        edges[0].add((r, c))
                    elif c == 0:
                        edges[1].add((r, c))
                    elif r + c == size - 1 and c < size // 2:
                        edges[2].add((r, c))
                    elif r == size - 1:
                        edges[3].add((r, c))
                    elif c == size - 1:
                        edges[4].add((r, c))
                    elif r + c == size - 1 and c >= size // 2:
                        edges[5].add((r, c))
    return edges

def find_connected_components(stones):
    if not stones:
        return []
    stone_set = set(stones)
    visited = set()
    components = []
    
    for stone in stones:
        if stone not in visited:
            component = set()
            stack = [stone]
            while stack:
                curr = stack.pop()
                if curr in visited:
                    continue
                visited.add(curr)
                component.add(curr)
                for nr, nc in get_neighbors(curr[0], curr[1]):
                    if (nr, nc) in stone_set and (nr, nc) not in visited:
                        stack.append((nr, nc))
            components.append(component)
    return components

def check_bridge(component, corners):
    corner_set = set(corners)
    corners_in_comp = component & corner_set
    return len(corners_in_comp) >= 2

def check_fork(component, edges):
    edge_count = 0
    for edge_id, edge_cells in edges.items():
        if component & edge_cells:
            edge_count += 1
    return edge_count >= 3

def check_ring(component, valid_mask):
    if len(component) < 6:
        return False
    size = len(valid_mask)
    for r, c in component:
        for nr, nc in get_neighbors(r, c, size):
            if valid_mask[nr][nc] and (nr, nc) not in component:
                visited = set()
                stack = [(nr, nc)]
                reachable_edge = False
                while stack:
                    curr = stack.pop()
                    if curr in visited or curr in component:
                        continue
                    visited.add(curr)
                    neighs = get_valid_neighbors(curr[0], curr[1], valid_mask)
                    if len(neighs) < 6:
                        reachable_edge = True
                        break
                    for n in neighs:
                        if n not in visited and n not in component:
                            stack.append(n)
                if not reachable_edge:
                    return True
    return False

def check_win(stones, valid_mask, corners, edges):
    components = find_connected_components(stones)
    for comp in components:
        if check_bridge(comp, corners):
            return True
        if check_fork(comp, edges):
            return True
        if check_ring(comp, valid_mask):
            return True
    return False

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    size = len(valid_mask)
    valid_mask_np = np.array(valid_mask)
    
    me_set = set(me)
    opp_set = set(opp)
    
    valid_moves = []
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    
    if not valid_moves:
        for r in range(size):
            for c in range(size):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    corners = get_corners(valid_mask)
    edges = get_edge_cells(valid_mask, corners)
    
    # Check for immediate wins
    for move in valid_moves:
        new_me = me + [move]
        if check_win(new_me, valid_mask, corners, edges):
            return move
    
    # Block opponent wins
    for move in valid_moves:
        new_opp = opp + [move]
        if check_win(new_opp, valid_mask, corners, edges):
            return move
    
    # MCTS-lite with heuristics
    center = size // 2
    
    def move_score(move):
        r, c = move
        score = 0
        dist_to_center = abs(r - center) + abs(c - center)
        score -= dist_to_center * 0.5
        
        for nr, nc in get_neighbors(r, c, size):
            if (nr, nc) in me_set:
                score += 3
            elif (nr, nc) in opp_set:
                score += 1
        
        if move in corners:
            score += 2
        
        for edge_cells in edges.values():
            if move in edge_cells:
                score += 1
                break
        
        return score
    
    scored_moves = [(move_score(m), random.random(), m) for m in valid_moves]
    scored_moves.sort(reverse=True)
    
    # Simple Monte Carlo sampling on top candidates
    top_moves = [m for _, _, m in scored_moves[:min(15, len(scored_moves))]]
    
    best_move = top_moves[0]
    best_wins = -1
    
    start_time = time.time()
    simulations_per_move = 20
    
    for move in top_moves:
        if time.time() - start_time > 0.8:
            break
        
        wins = 0
        for _ in range(simulations_per_move):
            sim_me = set(me_set)
            sim_opp = set(opp_set)
            sim_me.add(move)
            
            remaining = [m for m in valid_moves if m != move and m not in sim_me and m not in sim_opp]
            random.shuffle(remaining)
            
            turn = 1  # opponent's turn
            for m in remaining[:30]:
                if turn == 1:
                    sim_opp.add(m)
                else:
                    sim_me.add(m)
                turn = 1 - turn
            
            if check_win(list(sim_me), valid_mask, corners, edges):
                wins += 1
            elif not check_win(list(sim_opp), valid_mask, corners, edges):
                wins += 0.5
        
        if wins > best_wins:
            best_wins = wins
            best_move = move
    
    return best_move
