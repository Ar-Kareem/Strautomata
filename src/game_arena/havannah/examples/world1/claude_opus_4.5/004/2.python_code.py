
import numpy as np
from collections import defaultdict
import random
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    size = 15
    board_size = 8  # Havannah board parameter (size 8 means 15x15 grid)
    
    me_set = set(me)
    opp_set = set(opp)
    
    valid_moves = [(r, c) for r in range(size) for c in range(size) 
                   if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    if not valid_moves:
        for r in range(size):
            for c in range(size):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    def get_neighbors(r, c):
        candidates = [(r-1, c), (r+1, c), (r-1, c-1), (r, c-1), (r, c+1), (r+1, c+1)]
        return [(nr, nc) for nr, nc in candidates if 0 <= nr < size and 0 <= nc < size and valid_mask[nr][nc]]
    
    corners = set()
    edges = defaultdict(set)
    
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c]:
                neighbors = get_neighbors(r, c)
                valid_neighbors = [n for n in neighbors if valid_mask[n[0]][n[1]]]
                if len(valid_neighbors) == 3:
                    corners.add((r, c))
                elif len(valid_neighbors) < 6:
                    if r == 0:
                        edges[0].add((r, c))
                    elif r == size - 1:
                        edges[3].add((r, c))
                    elif c == 0 and r < size // 2:
                        edges[5].add((r, c))
                    elif c == 0:
                        edges[4].add((r, c))
                    else:
                        if r < size // 2:
                            if c > r:
                                edges[1].add((r, c))
                            else:
                                edges[5].add((r, c))
                        else:
                            if c > size - 1 - (r - size // 2 + 1):
                                edges[2].add((r, c))
                            else:
                                edges[4].add((r, c))
    
    for edge_id in list(edges.keys()):
        edges[edge_id] -= corners
    
    def score_move(move):
        r, c = move
        score = 0
        
        if move in corners:
            score += 50
        
        for edge_cells in edges.values():
            if move in edge_cells:
                score += 30
                break
        
        center = size // 2
        dist_to_center = abs(r - center) + abs(c - center)
        score += max(0, 15 - dist_to_center)
        
        neighbors = get_neighbors(r, c)
        my_neighbors = sum(1 for n in neighbors if n in me_set)
        opp_neighbors = sum(1 for n in neighbors if n in opp_set)
        score += my_neighbors * 20
        score += opp_neighbors * 15
        
        return score
    
    # Quick check for winning moves or blocking moves
    for move in valid_moves:
        test_me = me_set | {move}
        # Simple connectivity bonus - prefer extending groups
        neighbors = get_neighbors(move[0], move[1])
        if any(n in me_set for n in neighbors):
            pass  # Good - extends our group
    
    scored_moves = [(score_move(m), random.random(), m) for m in valid_moves]
    scored_moves.sort(reverse=True)
    
    top_moves = [m for _, _, m in scored_moves[:min(20, len(scored_moves))]]
    
    if len(me) + len(opp) < 5:
        best_move = top_moves[0]
        return best_move
    
    start_time = time.time()
    time_limit = 0.85
    
    move_scores = defaultdict(lambda: [0, 0])
    
    iterations = 0
    while time.time() - start_time < time_limit:
        iterations += 1
        
        if iterations <= len(top_moves):
            move = top_moves[iterations - 1]
        else:
            total_visits = sum(v[1] for v in move_scores.values()) + 1
            best_ucb = -float('inf')
            move = top_moves[0]
            for m in top_moves:
                wins, visits = move_scores[m]
                if visits == 0:
                    ucb = float('inf')
                else:
                    ucb = wins / visits + 1.4 * np.sqrt(np.log(total_visits) / visits)
                if ucb > best_ucb:
                    best_ucb = ucb
                    move = m
        
        sim_me = me_set | {move}
        sim_opp = opp_set.copy()
        sim_valid = [m for m in valid_moves if m != move]
        current_player = 1
        
        for _ in range(min(30, len(sim_valid))):
            if not sim_valid:
                break
            
            rand_move = random.choice(sim_valid)
            sim_valid.remove(rand_move)
            
            if current_player == 1:
                sim_opp.add(rand_move)
            else:
                sim_me.add(rand_move)
            current_player = 1 - current_player
        
        my_score = len(sim_me)
        opp_score = len(sim_opp)
        
        my_connectivity = 0
        for stone in sim_me:
            neighbors = get_neighbors(stone[0], stone[1])
            my_connectivity += sum(1 for n in neighbors if n in sim_me)
        
        opp_connectivity = 0
        for stone in sim_opp:
            neighbors = get_neighbors(stone[0], stone[1])
            opp_connectivity += sum(1 for n in neighbors if n in sim_opp)
        
        if my_connectivity > opp_connectivity:
            result = 1
        elif my_connectivity < opp_connectivity:
            result = 0
        else:
            result = 0.5
        
        move_scores[move][0] += result
        move_scores[move][1] += 1
    
    best_move = top_moves[0]
    best_ratio = -1
    for m in top_moves:
        wins, visits = move_scores[m]
        if visits > 0:
            ratio = wins / visits
            if ratio > best_ratio:
                best_ratio = ratio
                best_move = m
    
    return best_move
