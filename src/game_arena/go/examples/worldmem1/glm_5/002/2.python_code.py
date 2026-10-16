
import random

def policy(me, opponent, memory):
    SIZE = 19
    
    # Convert inputs to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones
    
    # Retrieve the previous board state to check for Ko
    prev_state = memory.get('prev_state')
    
    # Helper to get adjacent coordinates
    def get_neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                yield nr, nc
    
    # BFS to find a group and its liberties
    def get_group_and_liberties(start_r, start_c, player_stones, occupied):
        group = set()
        liberties = set()
        stack = [(start_r, start_c)]
        visited = set()
        
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group.add((r, c))
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in player_stones:
                    if (nr, nc) not in visited:
                        stack.append((nr, nc))
                elif (nr, nc) not in occupied:
                    liberties.add((nr, nc))
        return group, liberties

    # Check legality of a move including Suicide and Ko rules
    def is_legal_move(r, c):
        # 1. Check if occupied
        if (r, c) in all_stones:
            return False, None
        
        # Simulate move
        new_my = set(my_stones)
        new_my.add((r, c))
        new_opp = set(opp_stones)
        
        # Check for captures (opponent groups with 0 liberties)
        captured_stones = set()
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in new_opp:
                # We need to check the group status of this neighbor
                # Only check if we haven't already determined this stone is captured
                if (nr, nc) not in captured_stones:
                    grp, libs = get_group_and_liberties(nr, nc, new_opp, new_my | new_opp)
                    if not libs:
                        captured_stones.update(grp)
        
        # Remove captured stones
        new_opp -= captured_stones
        
        # Check for Suicide (own group has 0 liberties after move and captures)
        # We check the group of the placed stone
        # Note: occupied for liberty check is new_my | new_opp (after captures)
        my_group, my_libs = get_group_and_liberties(r, c, new_my, new_my | new_opp)
        if not my_libs:
            return False, None # Suicide
            
        # Check for Ko (simple: board state must not equal previous state)
        # We use frozensets for hashable state comparison
        current_state = (frozenset(new_my), frozenset(new_opp))
        if current_state == prev_state:
            return False, None # Ko
            
        return True, current_state

    # --- 1. Tactical Moves ---
    
    # Identify opponent groups in atari (can be captured immediately)
    opp_ataris = [] # List of (size, capture_point)
    checked_opp = set()
    for r, c in opp_stones:
        if (r, c) in checked_opp: continue
        grp, libs = get_group_and_liberties(r, c, opp_stones, all_stones)
        checked_opp.update(grp)
        if len(libs) == 1:
            opp_ataris.append((len(grp), list(libs)[0]))
    
    # Sort by size to capture larger groups first
    opp_ataris.sort(key=lambda x: -x[0])
    
    for size, move in opp_ataris:
        legal, state = is_legal_move(move[0], move[1])
        if legal:
            return move, {'prev_state': state}
            
    # Identify own groups in atari (need saving)
    # Strategy: Extend (play at the liberty) or Capture adjacent opponent
    my_ataris = [] # List of (size, liberty_point)
    checked_my = set()
    for r, c in my_stones:
        if (r, c) in checked_my: continue
        grp, libs = get_group_and_liberties(r, c, my_stones, all_stones)
        checked_my.update(grp)
        if len(libs) == 1:
            my_ataris.append((len(grp), list(libs)[0]))
            
    my_ataris.sort(key=lambda x: -x[0])
    
    for size, move in my_ataris:
        legal, state = is_legal_move(move[0], move[1])
        if legal:
            return move, {'prev_state': state}

    # --- 2. Heuristic Moves ---
    
    # Generate candidate moves based on proximity and board position
    candidates = set()
    
    # Prefer moves near existing stones
    for r, c in all_stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                    if (nr, nc) not in all_stones:
                        candidates.add((nr, nc))
    
    # If no neighbors (empty board), play center/star point
    if not candidates:
        candidates.add((SIZE//2 + 1, SIZE//2 + 1)) # Tengen
        
    # Score candidates
    scored_candidates = []
    for r, c in candidates:
        score = 0
        
        # Distance to edge (3rd/4th line preferred)
        edge_dist = min(r-1, SIZE-r, c-1, SIZE-c)
        if edge_dist in [2, 3]: # 3rd or 4th line (indices 2, 3)
            score += 10
        elif edge_dist == 1:
            score -= 5 # 1st line usually bad
            
        # Adjacency bonus
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in my_stones:
                score += 2
            if (nr, nc) in opp_stones:
                score += 1
                
        scored_candidates.append((score, (r, c)))
        
    scored_candidates.sort(key=lambda x: -x[0])
    
    # Try top candidates
    for score, move in scored_candidates[:20]:
        legal, state = is_legal_move(move[0], move[1])
        if legal:
            return move, {'prev_state': state}
            
    # --- 3. Random Legal Move ---
    # Fallback: scan board for any legal move
    all_points = [(r, c) for r in range(1, SIZE+1) for c in range(1, SIZE+1)]
    random.shuffle(all_points)
    
    for move in all_points:
        legal, state = is_legal_move(move[0], move[1])
        if legal:
            return move, {'prev_state': state}
            
    # --- 4. Pass ---
    return (0, 0), {}
