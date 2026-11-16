
import heapq
from collections import defaultdict, deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Build set of occupied cells for fast lookup
    occupied = set(me + opp)
    
    # Define direction vectors for hexagonal grid
    # For a cell (i, j), the six neighbors are:
    # (i-1, j), (i-1, j+1)   -> top row
    # (i, j-1), (i, j+1)     -> same row
    # (i+1, j-1), (i+1, j)   -> bottom row
    # Note: We avoid (i-1,j-1) and (i+1,j+1) as they are not adjacent in hex grid
    directions = [
        (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0)
    ]
    
    def is_valid(r, c):
        return 0 <= r <= 10 and 0 <= c <= 10
    
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc):
                neighbors.append((nr, nc))
        return neighbors
    
    # Helper: Get all cells on the target edges
    if color == 'b':  # Black connects top (row 0) to bottom (row 10)
        start_edge = {(0, c) for c in range(11)}
        end_edge = {(10, c) for c in range(11)}
    else:  # White connects left (col 0) to right (col 10)
        start_edge = {(r, 0) for r in range(11)}
        end_edge = {(r, 10) for r in range(11)}
    
    # Get all stones belonging to current player
    my_stones = set(me)
    
    # Check for immediate win: if any move completes a connection
    for r in range(11):
        for c in range(11):
            if (r, c) in occupied:
                continue
            # Try placing a stone here
            if is_winning_move(r, c, my_stones, start_edge, end_edge, get_neighbors, color):
                return (r, c)
    
    # Check for opponent's immediate win and block it
    opp_stones = set(opp)
    for r in range(11):
        for c in range(11):
            if (r, c) in occupied:
                continue
            if is_winning_move(r, c, opp_stones, start_edge, end_edge, get_neighbors, 'w' if color == 'b' else 'b'):
                return (r, c)
    
    # If no immediate win/block, use A* to find best move for our connection
    
    # Build a graph of our current component(s) and find shortest path to target
    # We'll use a modified BFS/A* over empty and own stones to find a path
    
    # If we have no stones yet, play in the center or near the edge strategically
    if len(my_stones) == 0:
        # For black: center or top/bottom edge
        # For white: center or left/right edge
        center = (5, 5)
        if color == 'b':
            # Black prefers top or bottom row center
            if (5, 0) not in occupied:
                return (5, 0)
            elif (5, 10) not in occupied:
                return (5, 10)
            else:
                return center
        else:
            # White prefers left or right edge center
            if (0, 5) not in occupied:
                return (0, 5)
            elif (10, 5) not in occupied:
                return (10, 5)
            else:
                return center
    
    # Use A* to find a path from our stones to target edge
    best_move = None
    best_score = float('inf')
    
    # We'll compute the shortest path from any of our stones to the target edge
    # considering only empty and own stones as traversable
    traversable = my_stones | occupied  # We can traverse own stones and empty (but we can only place on empty)
    
    # Priority queue: (estimated_total_cost, current_r, current_c, path_cost)
    queue = []
    visited = set()
    
    # Add all our stones as starting points
    for r, c in my_stones:
        if (r, c) in start_edge:
            # Already touching target edge, we are close
            pass  # Will be handled in pathfinding below
        visited.add((r, c))
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in occupied:
                # This is an empty neighbor of our stone
                # Estimate cost to reach end edge
                heuristic = manhattan_to_edge(nr, nc, end_edge, color)
                # We use a slightly weighted A* to prefer moves closer to edge and center
                cost = 1 + heuristic  # base cost 1 + heuristic
                heapq.heappush(queue, (cost, nr, nc, 1))
    
    # If no adjacent empty cells, this shouldn't happen, but fallback
    if not queue:
        # Just pick any empty cell
        for r in range(11):
            for c in range(11):
                if (r, c) not in occupied:
                    return (r, c)
    
    # Try to find path to target edge using A*
    target_reached = False
    best_path_length = float('inf')
    best_candidate = None
    
    # We explore up to 10 steps deep
    while queue and len(queue) < 1000:
        total_est, r, c, path_cost = heapq.heappop(queue)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        
        # Check if we reached target edge
        if (r, c) in end_edge:
            # We found a path!
            if path_cost < best_path_length:
                best_path_length = path_cost
                best_candidate = (r, c)
                target_reached = True
            continue
        
        if path_cost >= 10:  # Limit depth
            continue
            
        # Explore neighbors
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in visited or (nr, nc) in opp:
                continue
            # Heuristic: distance to target edge
            h = manhattan_to_edge(nr, nc, end_edge, color)
            estimated_total = path_cost + 1 + h
            heapq.heappush(queue, (estimated_total, nr, nc, path_cost + 1))
            
    # If we found a path to edge, then the best candidate is the last move we'd make
    # But we want the first move: the empty neighbor that starts the path
    if best_candidate is not None:
        # Reconstruct: look for an empty cell adjacent to our group that is on a good path
        # Instead, we use a simpler heuristic: for all empty neighbors of our stones, evaluate the score
        candidates = []
        for r, c in my_stones:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in occupied:
                    # Evaluate this candidate using multiple metrics
                    score = evaluate_move(nr, nc, my_stones, opp, start_edge, end_edge, color, get_neighbors)
                    candidates.append((score, nr, nc))
        
        candidates.sort(reverse=True)  # Highest score first
        if candidates:
            return candidates[0][1]
    
    # If no good candidate found by A*, try to find any move that connects stones or blocks opponent
    # Use a simple connectivity score
    candidates = []
    for r in range(11):
        for c in range(11):
            if (r, c) in occupied:
                continue
            score = evaluate_move(r, c, my_stones, opp, start_edge, end_edge, color, get_neighbors)
            candidates.append((score, r, c))
    
    # Sort by score descending
    candidates.sort(reverse=True)
    if candidates:
        return candidates[0][1]
    
    # Fallback: return any empty cell
    for r in range(11):
        for c in range(11):
            if (r, c) not in occupied:
                return (r, c)
    
    # This should never happen due to game rules
    raise RuntimeError("No legal move found!")

def is_winning_move(r, c, stone_set, start_edge, end_edge, get_neighbors, color):
    """Check if placing a stone at (r, c) wins the game for player with stone_set"""
    # Temporarily add the stone
    stone_set_temp = stone_set | {(r, c)}
    
    # Use BFS to see if there's a path from start edge to end edge
    visited = set()
    queue = deque()
    
    # Add all stones on the start edge
    for sr, sc in stone_set_temp:
        if (sr, sc) in start_edge:
            queue.append((sr, sc))
            visited.add((sr, sc))
    
    while queue:
        curr_r, curr_c = queue.popleft()
        if (curr_r, curr_c) in end_edge:
            return True
            
        for nr, nc in get_neighbors(curr_r, curr_c):
            if (nr, nc) in stone_set_temp and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    
    return False

def manhattan_to_edge(r, c, edge_set, color):
    """Heuristic: Manhattan-like distance to target edge"""
    if color == 'b':
        # Target: row 10 (bottom)
        return 10 - r
    else:
        # Target: col 10 (right)
        return 10 - c

def evaluate_move(r, c, my_stones, opp_stones, start_edge, end_edge, color, get_neighbors):
    """Evaluate a move's quality using multiple heuristics"""
    score = 0.0
    
    # Heuristic 1: Distance to target edge
    if color == 'b':
        score += (10 - r) * 10
    else:
        score += (10 - c) * 10
    
    # Heuristic 2: Proximity to existing stones (connectivity)
    connections = 0
    for nr, nc in get_neighbors(r, c):
        if (nr, nc) in my_stones:
            connections += 1
    
    score += connections * 5
    
    # Heuristic 3: Proximity to opponent stones (block potential)
    opp_adj = 0
    for nr, nc in get_neighbors(r, c):
        if (nr, nc) in opp_stones:
            opp_adj += 1
    # We don't want to block too close, but being adjacent is sometimes good
    # Penalize moves that are surrounded by opponents, favor moves adjacent to one or two
    if opp_adj == 0:
        score += 3
    elif opp_adj <= 2:
        score += 1
    else:
        score -= 2  # risk of being surrounded
    
    # Heuristic 4: Central location bonus
    center_dist = abs(r - 5) + abs(c - 5)
    score += (10 - center_dist) * 0.5
    
    # Heuristic 5: Bridges between components? Need graph analysis - simplified as adjacency to two groups
    # We do a simple check: if placing this stone connects two separate components, give bonus
    # We'll check how many of our components this point connects (via the 6 neighbors)
    component_count = 0
    comp_neighbors = []
    for nr, nc in get_neighbors(r, c):
        if (nr, nc) in my_stones:
            comp_neighbors.append((nr, nc))
    
    # For a simple version: if we have 2+ neighbors that are disconnected from each other, this is a bridge
    if len(comp_neighbors) >= 2:
        # Check if any of the neighbors are connected to each other
        # This is complex, so we just use count as proxy: more connections = better
        score += 8
    
    # Heuristic 6: Edge control
    if r == 0 and color == 'b':
        score += 10
    elif r == 10 and color == 'b':
        score += 10
    elif c == 0 and color == 'w':
        score += 10
    elif c == 10 and color == 'w':
        score += 10
    
    return score
