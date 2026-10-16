
import collections
import heapq
import random
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Hex Policy: 1-ply search using Shannon Distance (Shortest Path) heuristic.
    """
    start_time = time.time()
    BOARD_SIZE = 11
    
    # Hex neighbors offsets
    # Neighbors of (r, c): (r, c-1), (r, c+1), (r+1, c), (r+1, c-1), (r-1, c), (r-1, c+1)
    DIRS = [(0, -1), (0, 1), (1, 0), (1, -1), (-1, 0), (-1, 1)]
    
    # 1. Parse Board State
    board_state = {} # (r, c) -> 1 (me), -1 (opp)
    for r, c in me:
        board_state[(r, c)] = 1
    for r, c in opp:
        board_state[(r, c)] = -1
        
    # If board is completely empty, play safest opening (Center)
    if not me and not opp:
        return (5, 5)

    # 2. Candidate Generation
    # Optimization: Only consider empty cells adjacent to occupied cells (active zone to block or extend)
    candidates = set()
    occupied_list = list(me) + list(opp)
    
    for r, c in occupied_list:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if (nr, nc) not in board_state:
                    candidates.add((nr, nc))
    
    # Fallback/Expansion: If very few stones (early game), ensure we consider central area
    # to avoid being led to edges by a weak opponent move.
    if len(occupied_list) < 5:
        for r in range(4, 7):
            for c in range(4, 7):
                if (r, c) not in board_state:
                    candidates.add((r, c))

    candidates_list = list(candidates)
    
    # Safety: If map is oddly full or empty candidates logic missed, scan all
    if not candidates_list:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in board_state:
                    candidates_list.append((r, c))
    
    # Shuffle to ensure variety on equal scores
    random.shuffle(candidates_list)

    # 3. Dijkstra Shortest Path Helper
    # Returns the min cost (number of empty cells needed). 
    # blocked path returns large int.
    def get_shortest_path(temp_board, check_for_me: bool) -> int:
        # Determine target connectivity
        # If I am 'b' (color), I need Top-Bottom. 
        # If I am 'w' (color), I need Left-Right.
        # But we also need to check Opponent path.
        
        my_color = color
        target_color = my_color if check_for_me else ('w' if my_color == 'b' else 'b')
        player_val = 1 if check_for_me else -1
        
        # Priority Queue: (cost, r, c)
        pq = []
        dists = {} # (r, c) -> min_cost
        
        # Initialize Start Nodes (Top Row or Left Col)
        if target_color == 'b': # Top to Bottom
            start_row = 0
            for c in range(BOARD_SIZE):
                cell = (start_row, c)
                val = temp_board.get(cell, 0)
                if val == -player_val: continue # Blocked by enemy
                
                cost = 0 if val == player_val else 1
                if cost < dists.get(cell, 9999):
                    dists[cell] = cost
                    heapq.heappush(pq, (cost, start_row, c))
        else: # 'w': Left to Right
            start_col = 0
            for r in range(BOARD_SIZE):
                cell = (r, start_col)
                val = temp_board.get(cell, 0)
                if val == -player_val: continue
                
                cost = 0 if val == player_val else 1
                if cost < dists.get(cell, 9999):
                    dists[cell] = cost
                    heapq.heappush(pq, (cost, r, start_col))
                    
        min_dist = 9999
        
        while pq:
            d, r, c = heapq.heappop(pq)
            
            # Optimization: If d exceeds current min_dist found
            if d >= min_dist: continue
            if d > dists.get((r, c), 9999): continue
            
            # Check Win Condition (Reached opp side)
            if target_color == 'b':
                if r == BOARD_SIZE - 1:
                    if d < min_dist: 
                        min_dist = d
                    # In Dijkstra, first target pop is optimal, return immediately
                    return d 
            else:
                if c == BOARD_SIZE - 1:
                    return d
            
            # Expand Neighbors
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    val = temp_board.get((nr, nc), 0)
                    if val == -player_val: continue # Wall
                    
                    weight = 0 if val == player_val else 1
                    new_dist = d + weight
                    
                    if new_dist < dists.get((nr, nc), 9999):
                        dists[(nr, nc)] = new_dist
                        heapq.heappush(pq, (new_dist, nr, nc))
                        
        return min_dist

    # 4. Search Loop
    best_score = -float('inf')
    best_move = candidates_list[0]
    
    # We use a time buffer to ensure we don't timeout (0.85s limit inside loop)
    # Average Dijkstra takes <1ms, so we can check many moves.
    
    for r, c in candidates_list:
        if time.time() - start_time > 0.85:
            break
            
        # Apply Move
        board_state[(r, c)] = 1
        
        # Calculate heuristics
        my_dist = get_shortest_path(board_state, True)
        opp_dist = get_shortest_path(board_state, False)
        
        # Scoring Logic
        # Maximize (Opp_Dist - My_Dist)
        # Prioritize Winning (My_Dist == 0) over Blocking
        
        score = 0
        if my_dist == 0:
            score = 100000 # Win found
        elif my_dist >= 9000:
            score = -100000 # Desperation: I am fully blocked
        elif opp_dist >= 9000:
            score = 50000 # Opponent blocked
        else:
             # Regular play
             # Influence multiplier: 100 * Distance Gap
             score = 100 * (opp_dist - my_dist)
             
             # Tie-breaker: Centrality
             # Prefer moves closer to center (5, 5)
             dist_from_center = abs(r - 5) + abs(c - 5)
             score -= dist_from_center
        
        # Revert Move
        del board_state[(r, c)]
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            # Instant win cutoff
            if score >= 100000:
                break

    return best_move
