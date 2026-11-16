
import heapq

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    BOARD_SIZE = 11
    
    occupied = set(me) | set(opp)
    
    def get_neighbors(r, c):
        # Hex neighbors: (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
        potential = [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
        return [(nr, nc) for nr, nc in potential if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE]

    def get_shortest_path_nodes(player_stones, opponent_stones, player_color):
        # Dijkstra to find the shortest path for a given color
        # returns (distance, path_list)
        target_dist = {} # (r, c) -> distance
        parent = {}
        pq = [] # (distance, r, c)

        # Virtual start and end nodes logic
        # For 'b', start is top (row -1), end is bottom (row 11)
        # For 'w', start is left (col -1), end is right (col 11)
        
        starts = []
        if player_color == 'b':
            starts = [(0, c) for c in range(BOARD_SIZE)]
        else:
            starts = [(r, 0) for r in range(BOARD_SIZE)]
            
        for r, c in starts:
            if (r, c) in opponent_stones: continue
            dist = 0 if (r, c) in player_stones else 1
            target_dist[(r, c)] = dist
            heapq.heappush(pq, (dist, r, c))
            parent[(r, c)] = None

        best_dist = float('inf')
        best_end_node = None
        
        while pq:
            d, r, c = heapq.heappop(pq)
            if d > target_dist.get((r, c), float('inf')):
                continue
            
            # Check if reached target boundary
            is_end = (player_color == 'b' and r == BOARD_SIZE - 1) or \
                     (player_color == 'w' and c == BOARD_SIZE - 1)
            
            if is_end:
                if d < best_dist:
                    best_dist = d
                    best_end_node = (r, c)
                # If we found a path of distance 0, we can't do better
                if d == 0: break

            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opponent_stones:
                    continue
                
                weight = 0 if (nr, nc) in player_stones else 1
                new_dist = d + weight
                
                if new_dist < target_dist.get((nr, nc), float('inf')):
                    target_dist[(nr, nc)] = new_dist
                    parent[(nr, nc)] = (r, c)
                    heapq.heappush(pq, (new_dist, nr, nc))
        
        path = []
        curr = best_end_node
        while curr is not None:
            if curr not in player_stones:
                path.append(curr)
            curr = parent.get(curr)
        return best_dist, path

    # 1. Opening Move
    if not me and not opp:
        return (5, 5)
    if len(occupied) < 2:
        if (5, 5) not in occupied: return (5, 5)
        else: return (5, 4)

    # 2. Get shortest paths
    opp_color = 'w' if color == 'b' else 'b'
    my_dist, my_path = get_shortest_path_nodes(me, opp, color)
    opp_dist, opp_path = get_shortest_path_nodes(opp, me, opp_color)

    # 3. Decision Logic
    # If we can win in one move or need to block an immediate win
    if not my_path and not opp_path:
        # Fallback to any empty cell
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in occupied: return (r, c)

    # Strategy: if opponent is closer to winning, block them. 
    # Otherwise, advance our own path.
    if opp_dist <= my_dist and opp_path:
        # Prioritize blocking opponent's shortest path
        # Try to pick a center-most cell in their path
        return opp_path[len(opp_path)//2]
    
    if my_path:
        return my_path[len(my_path)//2]

    # Extreme fallback
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r, c) not in occupied: return (r, c)
    
    return (0, 0)
