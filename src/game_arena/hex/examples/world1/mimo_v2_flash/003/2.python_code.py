
import collections
import heapq

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    A competitive Hex policy using a heuristic based on shortest path calculations.
    
    Strategy:
    1. Evaluate the 'distance' to victory for both players using BFS on a graph 
       where virtual nodes represent the board sides.
    2. Generate candidate moves only around existing stones (local search) to 
       maintain computational efficiency.
    3. Score moves based on reducing my path length while increasing the opponent's.
    """
    
    # Board constants
    BOARD_SIZE = 11
    ROWS, COLS = BOARD_SIZE, BOARD_SIZE
    
    # Define side pairs based on color
    # Black connects Top (0, col) to Bottom (10, col)
    # White connects Left (row, 0) to Right (row, 10)
    if color == 'b':
        my_start_side = lambda r, c: r == 0
        my_end_side = lambda r, c: r == ROWS - 1
        opp_start_side = lambda r, c: c == 0
        opp_end_side = lambda r, c: c == COLS - 1
    else: # 'w'
        my_start_side = lambda r, c: c == 0
        my_end_side = lambda r, c: c == COLS - 1
        opp_start_side = lambda r, c: r == 0
        opp_end_side = lambda r, c: r == ROWS - 1

    # Helper to get neighbors (Hexagonal grid logic)
    # The prompt's description "except for (i-1, j-1) and (i+1, j+1)" corresponds to 
    # an axial coordinate system or a specific flattened grid layout.
    # For a standard 2D array representation of Hex (often "odd-r" or "even-r" offset),
    # standard neighbors are:
    # (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c-1) [for even rows]
    # (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r+1, c+1) [for odd rows]
    # However, given the prompt's specific adjacency example:
    # (4,1) touches (4,0), (4,2), (5,1), (5,0), (3,1), (3,2).
    # This implies a coordinate system where:
    # Horizontal neighbors are (r, c-1), (r, c+1).
    # Vertical neighbors are (r+1, c), (r-1, c).
    # Diagonal neighbors are (r+1, c-1), (r-1, c+1).
    # This matches the "except (i-1, j-1) and (i+1, j+1)" rule for standard 2D arrays 
    # if we consider valid neighbors to be: 
    # (r, c-1), (r, c+1), (r-1, c), (r+1, c), (r-1, c+1), (r+1, c-1).
    def get_neighbors(r, c):
        candidates = [
            (r, c - 1), (r, c + 1),  # Left, Right
            (r - 1, c), (r + 1, c),  # Up, Down
            (r - 1, c + 1), (r + 1, c - 1) # Diagonals based on prompt logic
        ]
        valid = []
        for nr, nc in candidates:
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                valid.append((nr, nc))
        return valid

    # Set up lookup for fast empty checks
    me_set = set(me)
    opp_set = set(opp)
    all_stones = me_set.union(opp_set)
    
    # --- 1. Shortest Path Calculation (BFS) ---
    def get_shortest_path_length(stones, is_me):
        # If no stones, distance is effectively infinite (or max board dimension)
        if not stones:
            return ROWS + COLS + 10
        
        # We want the minimum number of jumps to reach the target side.
        # We treat the start side as the current stones (distance 0).
        # We treat the target side as the goal (virtual nodes).
        # Since we can only place one stone per turn, the "path length" represents
        # the number of additional stones needed to connect.
        
        visited = set(stones)
        queue = collections.deque([(s, 0) for s in stones])
        
        while queue:
            (r, c), dist = queue.popleft()
            
            # Check if we hit the target side
            if is_me and my_end_side(r, c):
                return dist
            if not is_me and opp_end_side(r, c):
                return dist
            
            # Explore neighbors
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and (nr, nc) not in all_stones:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist + 1))
                
                # If neighbor is occupied by us, we can extend through it
                # (Effectively 0 cost extension in this BFS model)
                if (nr, nc) in stones and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist)) # 0 cost step
        
        return ROWS + COLS + 10 # Fallback for disconnected

    # --- 2. Candidate Generation ---
    # Generate moves only near existing stones to save time and play locally
    candidates = set()
    
    # Always consider the immediate center if the board is very empty
    # and if it's a valid move
    if len(all_stones) < 2:
        center = (5, 5)
        if center not in all_stones:
            return center
    
    # Add neighbors of all stones
    for stone in all_stones:
        for n in get_neighbors(stone[0], stone[1]):
            if n not in all_stones:
                candidates.add(n)
                
    # If for some reason candidates is empty (start of game or isolated blocks),
    # scan for any empty spot (fallback)
    if not candidates:
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) not in all_stones:
                    candidates.add((r, c))

    # --- 3. Evaluation & Selection ---
    best_move = None
    best_score = -float('inf')
    
    # Pre-calculate base distances for context (optional, but helps heuristic)
    # Note: In a full implementation, we would update the stones set for each candidate
    # to see the actual impact. However, to keep it fast for 1 second:
    # We use a proxy: "How close is this move to bridging the gap?"
    
    for move in candidates:
        # Simulate move
        temp_me = me_set.union({move})
        
        # Calculate new path length for Me
        my_dist = get_shortest_path_length(temp_me, is_me=True)
        
        # Calculate new path length for Opponent (using actual opp stones)
        # Note: We don't simulate opponent blocking, as we assume we want to maximize our path
        # and minimize opponent's current potential.
        opp_dist = get_shortest_path_length(opp_set, is_me=False)
        
        # Heuristic Score:
        # We want to minimize our distance (shorter path to win).
        # We want to maximize opponent distance (harder for them to win).
        # Score = (Opponent_Distance - My_Distance)
        # We add a small bonus for moves closer to the center to resolve ties 
        # and favor central control in early game.
        
        score = (opp_dist - my_dist)
        
        # Center bias (optional tie-breaker)
        dist_to_center = abs(move[0] - 5) + abs(move[1] - 5)
        score += (5 - dist_to_center) * 0.1
        
        if score > best_score:
            best_score = score
            best_move = move
            
    # Fallback if no move found (should not happen given candidates logic)
    if best_move is None:
        for r in range(ROWS):
            for c in range(COLS):
                if (r, c) not in all_stones:
                    return (r, c)
                    
    return best_move
