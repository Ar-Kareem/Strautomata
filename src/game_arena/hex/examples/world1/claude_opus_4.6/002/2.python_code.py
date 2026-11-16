
import time
import random
import math
from collections import defaultdict

BOARD_SIZE = 11

def get_neighbors(r, c):
    for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if (r, c) not in occupied]
    
    if not empty:
        return me[0]  # shouldn't happen
    
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    
    if len(me) == 0 and len(opp) == 1:
        # Swap rule consideration - just play center area
        if (5, 5) not in occupied:
            return (5, 5)
        return (5, 4)
    
    # Dijkstra shortest path for a color
    def shortest_path_cost(stones_set, player_color, board_occupied):
        import heapq
        dist = {}
        heap = []
        
        if player_color == 'b':
            # connect top (row=0) to bottom (row=10)
            for c in range(BOARD_SIZE):
                if (0, c) in stones_set:
                    dist[(0, c)] = 0
                    heapq.heappush(heap, (0, 0, c))
                elif (0, c) not in board_occupied:
                    dist[(0, c)] = 1
                    heapq.heappush(heap, (1, 0, c))
            
            while heap:
                cost, r, c = heapq.heappop(heap)
                if cost > dist.get((r, c), float('inf')):
                    continue
                if r == BOARD_SIZE - 1:
                    return cost
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones_set:
                        ncost = cost
                    elif (nr, nc) not in board_occupied:
                        ncost = cost + 1
                    else:
                        continue
                    if ncost < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = ncost
                        heapq.heappush(heap, (ncost, nr, nc))
        else:
            for r in range(BOARD_SIZE):
                if (r, 0) in stones_set:
                    dist[(r, 0)] = 0
                    heapq.heappush(heap, (0, r, 0))
                elif (r, 0) not in board_occupied:
                    dist[(r, 0)] = 1
                    heapq.heappush(heap, (1, r, 0))
            
            while heap:
                cost, r, c = heapq.heappop(heap)
                if cost > dist.get((r, c), float('inf')):
                    continue
                if c == BOARD_SIZE - 1:
                    return cost
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones_set:
                        ncost = cost
                    elif (nr, nc) not in board_occupied:
                        ncost = cost + 1
                    else:
                        continue
                    if ncost < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = ncost
                        heapq.heappush(heap, (ncost, nr, nc))
        return float('inf')
    
    opp_color = 'w' if color == 'b' else 'b'
    
    # Check for immediate wins
    for move in empty:
        new_me = me_set | {move}
        if shortest_path_cost(new_me, color, occupied | {move}) == 0:
            return move
    
    # Check for opponent immediate wins and block
    blocking_moves = []
    for move in empty:
        new_opp = opp_set | {move}
        if shortest_path_cost(new_opp, opp_color, occupied | {move}) == 0:
            blocking_moves.append(move)
    
    if len(blocking_moves) == 1:
        return blocking_moves[0]
    
    # MCTS
    start_time = time.time()
    time_limit = 0.85
    
    # Evaluate moves with shortest path heuristic for prioritization
    def evaluate_move(move):
        new_me = me_set | {move}
        new_occ = occupied | {move}
        my_cost = shortest_path_cost(new_me, color, new_occ)
        opp_cost = shortest_path_cost(opp_set, opp_color, new_occ)
        return opp_cost - my_cost
    
    # Rank moves
    move_scores = []
    for move in empty:
        score = evaluate_move(move)
        move_scores.append((score, move))
    move_scores.sort(reverse=True)
    
    # Take top candidates for deeper analysis
    candidates = [m for _, m in move_scores[:min(25, len(move_scores))]]
    
    if not candidates:
        return empty[0]
    
    # Simple MCTS with random playouts
    wins = defaultdict(int)
    visits = defaultdict(int)
    total_visits = 0
    
    def simulate(move):
        # Play out randomly from this position
        my_stones = me_set | {move}
        opp_stones = set(opp_set)
        remaining = [m for m in empty if m != move]
        random.shuffle(remaining)
        
        # Assign remaining moves alternately: opponent first, then me, etc.
        turn_opp = True
        for m in remaining:
            if turn_opp:
                opp_stones.add(m)
            else:
                my_stones.add(m)
            turn_opp = not turn_opp
        
        # Check who won
        all_occupied = my_stones | opp_stones
        my_cost = shortest_path_cost(my_stones, color, all_occupied)
        return 1 if my_cost == 0 else 0
    
    iterations = 0
    while time.time() - start_time < time_limit:
        # UCT selection
        if total_visits < len(candidates):
            move = candidates[total_visits]
        else:
            best_ucb = -float('inf')
            move = candidates[0]
            log_total = math.log(total_visits)
            for m in candidates:
                if visits[m] == 0:
                    move = m
                    break
                ucb = wins[m] / visits[m] + 1.414 * math.sqrt(log_total / visits[m])
                if ucb > best_ucb:
                    best_ucb = ucb
                    move = m
        
        result = simulate(move)
        wins[move] += result
        visits[move] += 1
        total_visits += 1
        iterations += 1
        
        if iterations % 50 == 0 and time.time() - start_time >= time_limit:
            break
    
    # Pick move with highest win rate (with enough visits)
    best_move = candidates[0]
    best_rate = -1
    for m in candidates:
        if visits[m] > 0:
            rate = wins[m] / visits[m]
            if rate > best_rate:
                best_rate = rate
                best_move = m
    
    return best_move
