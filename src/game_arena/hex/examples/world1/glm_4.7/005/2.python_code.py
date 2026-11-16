
import heapq
import random

# Constants
BOARD_SIZE = 11

# Hexagonal neighbor offsets (row, col)
# Excluding (i-1, j-1) and (i+1, j+1) as per instructions
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

def get_neighbors(r: int, c: int):
    """Generator yielding valid neighbor coordinates for (r, c)."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def shortest_path(own_stones, opp_stones, color):
    """
    Calculates the shortest path cost to connect the two sides for 'color'.
    
    Args:
        own_stones: set of (r, c) tuples of the player calculating the path.
        opp_stones: set of (r, c) tuples of the opponent (blockers).
        color: 'b' for Black (Top-Bottom), 'w' for White (Left-Right).
        
    Returns:
        float: The cost of the shortest path. 0 if already connected.
               float('inf') if no path exists.
    """
    # Dijkstra's algorithm
    # Distance array initialized to infinity
    dist = [[float('inf')] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    pq = []
    
    # Initialize starting nodes based on color
    if color == 'b':
        # Black connects Top (row 0) to Bottom (row 10)
        # Source is row 0
        for c in range(BOARD_SIZE):
            if (0, c) in opp_stones:
                continue
            # Cost to enter a cell: 0 if own stone, 1 if empty
            entry_cost = 0 if (0, c) in own_stones else 1
            if entry_cost < dist[0][c]:
                dist[0][c] = entry_cost
                heapq.heappush(pq, (entry_cost, 0, c))
        target_check = lambda r, c: r == BOARD_SIZE - 1
    else:
        # White connects Left (col 0) to Right (col 10)
        # Source is col 0
        for r in range(BOARD_SIZE):
            if (r, 0) in opp_stones:
                continue
            entry_cost = 0 if (r, 0) in own_stones else 1
            if entry_cost < dist[r][0]:
                dist[r][0] = entry_cost
                heapq.heappush(pq, (entry_cost, r, 0))
        target_check = lambda r, c: c == BOARD_SIZE - 1

    while pq:
        d, r, c = heapq.heappop(pq)
        
        # If we reached the target edge, we can return immediately
        # because Dijkstra processes nodes in order of increasing distance.
        if target_check(r, c):
            return d
        
        if d > dist[r][c]:
            continue
            
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue # Cannot pass through opponent
            
            # Calculate cost to move to neighbor
            # If neighbor is our stone, cost is 0. If empty, cost is 1.
            nd = d + (0 if (nr, nc) in own_stones else 1)
            
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(pq, (nd, nr, nc))
                
    return float('inf')

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'
    
    # Opening strategy: Play center if empty
    if not me_set:
        return (5, 5)
        
    # Generate candidate moves
    # We only consider neighbors of existing stones to improve performance and
    # focus on relevant areas of the board.
    candidates = set()
    
    for r, c in me_set:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                candidates.add((nr, nc))
                
    for r, c in opp_set:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                candidates.add((nr, nc))
    
    # Fallback if candidates is empty (rare, e.g., very sparse board not triggering neighbors logic correctly)
    if not candidates:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in me_set and (r, c) not in opp_set:
                    candidates.add((r, c))

    best_move = None
    best_score = -float('inf')
    
    # Evaluate each candidate
    for move in candidates:
        r, c = move
        
        # Simulate my move
        new_me = me_set | {move}
        
        # 1. Calculate my shortest path if I play here
        my_path_len = shortest_path(new_me, opp_set, color)
        
        # 2. Calculate opponent's shortest path if I play here (I block this cell for them)
        opp_path_len = shortest_path(opp_set, new_me, opp_color)
        
        # If I can win immediately, take it
        if my_path_len == 0:
            return move
        
        # Score calculation:
        # We want to maximize (Opponent's Effort - My Effort)
        # High opponent path length is good (they are blocked).
        # Low my path length is good (I am close to winning).
        
        val_opp = opp_path_len if opp_path_len != float('inf') else 1000
        val_me = my_path_len if my_path_len != float('inf') else 1000
        
        score = val_opp - val_me
        
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Add randomness for tie-breaking to avoid being predictable
            if random.random() < 0.5:
                best_move = move

    return best_move
