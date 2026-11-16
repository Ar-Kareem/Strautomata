
import heapq
import math

BOARD_SIZE = 11

# Precompute neighbors for all cells (0..10, 0..10)
# Neighbors are the 8 surrounding cells except top-left (i-1, j-1) and bottom-right (i+1, j+1)
_NEIGHBORS = {}
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        # Standard Hex neighbors
        potential = [
            (r - 1, c), (r - 1, c + 1),
            (r, c - 1), (r, c + 1),
            (r + 1, c - 1), (r + 1, c)
        ]
        valid_ns = []
        for nr, nc in potential:
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                valid_ns.append((nr, nc))
        _NEIGHBORS[(r, c)] = valid_ns

def _shortest_path_cost(my_stones, opp_stones, is_black):
    """
    Computes the shortest path cost to connect the two opposing sides.
    
    Args:
        my_stones: Set of (r, c) tuples representing the player's stones.
        opp_stones: Set of (r, c) tuples representing the opponent's stones.
        is_black: Boolean, True if player is Black (Top-Bottom), False if White (Left-Right).
        
    Returns:
        Integer cost of the shortest path. Lower is better.
        0 means already connected.
    """
    # Define source and target nodes based on color
    if is_black:
        # Black connects Top (row 0) to Bottom (row 10)
        sources = [(0, c) for c in range(BOARD_SIZE)]
        targets = {(10, c) for c in range(BOARD_SIZE)}
    else:
        # White connects Left (col 0) to Right (col 10)
        sources = [(r, 0) for r in range(BOARD_SIZE)]
        targets = {(r, 10) for r in range(BOARD_SIZE)}

    # Priority Queue for Dijkstra: (cost, row, col)
    pq = []
    # Distance dictionary
    dist = {}

    # Initialize all source nodes
    for s in sources:
        # If a source cell is occupied by opponent, it is not traversable
        if s in opp_stones:
            continue
        
        # Cost to enter a source cell: 0 if I have a stone there, 1 if empty
        entry_cost = 0 if s in my_stones else 1
        heapq.heappush(pq, (entry_cost, s))
        dist[s] = entry_cost

    min_cost = math.inf

    while pq:
        curr_cost, r, c = heapq.heappop(pq)

        # Early exit if we reached a target node
        if (r, c) in targets:
            return curr_cost

        # Explore neighbors
        for nr, nc in _NEIGHBORS[(r, c)]:
            # Cannot pass through opponent stones
            if (nr, nc) in opp_stones:
                continue

            # Cost to enter neighbor: 0 if mine, 1 if empty
            edge_cost = 0 if (nr, nc) in my_stones else 1
            new_cost = curr_cost + edge_cost

            if (nr, nc) not in dist or new_cost < dist[(nr, nc)]:
                dist[(nr, nc)] = new_cost
                heapq.heappush(pq, (new_cost, nr, nc))

    return min_cost if min_cost != math.inf else 1000 # Return large penalty if no path exists

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Selects the best move for the current player.
    """
    # Convert lists to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)
    is_black = (color == 'b')

    # 1. Candidate Generation
    # To optimize, we don't check every empty cell. We check:
    # - The center (5,5) - most important
    # - Empty cells adjacent to existing stones (my or opponent's)
    
    candidates = set()
    candidates.add((5, 5))

    for r, c in me_set:
        for n in _NEIGHBORS[(r, c)]:
            candidates.add(n)
            
    for r, c in opp_set:
        for n in _NEIGHBORS[(r, c)]:
            candidates.add(n)

    # Filter candidates: must be empty and on board
    valid_moves = []
    for r, c in candidates:
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            if (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    
    # Fallback: If no neighbors found (e.g. very start of game and center ignored logic?), 
    # just take center or first empty.
    if not valid_moves:
        if (5, 5) not in me_set and (5, 5) not in opp_set:
            return (5, 5)
        # If center is taken, try neighbors or random
        valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                       if (r, c) not in me_set and (r, c) not in opp_set]
        if not valid_moves:
            # Should not happen unless board is full
            return (0, 0)

    best_score = -math.inf
    best_move = valid_moves[0]

    # 2. Evaluate Candidates
    for move in valid_moves:
        # Simulate placing the stone
        me_set.add(move)

        # Calculate shortest path for me
        my_cost = _shortest_path_cost(me_set, opp_set, is_black)
        
        # If I can connect immediately (cost 0), this is the best move
        if my_cost == 0:
            me_set.remove(move)
            return move

        # Calculate shortest path for opponent (assuming I just played)
        # We want to maximize the opponent's cost
        opp_cost = _shortest_path_cost(opp_set, me_set, not is_black)

        # Score = (Opponent's difficulty) - (My difficulty)
        # Higher score is better.
        score = opp_cost - my_cost

        if score > best_score:
            best_score = score
            best_move = move

        # Revert simulation
        me_set.remove(move)

    return best_move
