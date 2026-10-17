
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go policy that prioritizes:
    1. Saving own groups in Atari.
    2. Capturing opponent groups in Atari.
    3. Taking Star points / Territory.
    4. Maximizing local liberties and influence.
    Includes suicide prevention.
    """
    # Constants
    SIZE = 19
    EMPTY = 0
    ME = 1
    OPP = 2
    
    # 1. Initialize Board
    # 0: Empty, 1: Me, 2: Opponent
    board = [[EMPTY] * SIZE for _ in range(SIZE)]
    
    # Store stone locations for fast iteration if needed
    stones_me = set()
    stones_opp = set()
    
    # Parsing input (Input is 1-based, internal board is 0-based)
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r-1][c-1] = ME
            stones_me.add((r-1, c-1))
            
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r-1][c-1] = OPP
            stones_opp.add((r-1, c-1))

    # 2. Group Analysis Helpers
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def get_neighbors(r, c):
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield nr, nc

    # Build Group Data using Flood Fill
    # groups maps (r,c) -> group_id
    # group_data maps group_id -> {color, liberties (set), stones (list)}
    groups = {} 
    group_data = {}
    group_id_counter = 0
    
    visited = set()
    
    for r in range(SIZE):
        for c in range(SIZE):
            color = board[r][c]
            if color != EMPTY and (r,c) not in visited:
                # Start new group
                stack = [(r, c)]
                visited.add((r, c))
                
                current_stones = []
                current_libs = set()
                
                while stack:
                    curr_r, curr_c = stack.pop()
                    current_stones.append((curr_r, curr_c))
                    groups[(curr_r, curr_c)] = group_id_counter
                    
                    for nr, nc in get_neighbors(curr_r, curr_c):
                        n_color = board[nr][nc]
                        if n_color == EMPTY:
                            current_libs.add((nr, nc))
                        elif n_color == color and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            stack.append((nr, nc))
                
                group_data[group_id_counter] = {
                    'color': color,
                    'stones': current_stones,
                    'libs': current_libs
                }
                group_id_counter += 1

    # 3. Legality Checker (Suicide Prevention)
    def is_legal(r, c):
        # Must be empty
        if board[r][c] != EMPTY:
            return False
        
        # Check 1: Does it have immediate liberties?
        has_liberty = False
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == EMPTY:
                has_liberty = True
                break
        if has_liberty:
            return True
            
        # Check 2: Does it capture an opponent?
        # (Opponent neighbor with 1 liberty which is (r,c))
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == OPP:
                g_id = groups.get((nr, nc))
                if g_id is not None:
                    # Logic: The group has 1 lib, and that lib is (r,c).
                    # Since (r,c) is currently empty (verified above), it IS the lib.
                    if len(group_data[g_id]['libs']) == 1:
                        return True
                        
        # Check 3: Does it connect to a friendly group that is alive?
        # (Friendly neighbor with >= 2 liberties)
        # Why >= 2? Because (r,c) is currently one of its liberties. 
        # Filling (r,c) consumes that liberty. It needs another one to survive.
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == ME:
                g_id = groups.get((nr, nc))
                if g_id is not None:
                    if len(group_data[g_id]['libs']) >= 2:
                        return True
        
        # If none of the above, it's suicide (0 liberties, no capture)
        return False

    # 4. Strategy Execution
    
    # 4a. Emergency: Save own stones in Atari (1 liberty)
    my_atari_moves = []
    for g_id, data in group_data.items():
        if data['color'] == ME and len(data['libs']) == 1:
            # Get the single liberty
            lib = list(data['libs'])[0]
            my_atari_moves.append(lib)
    
    # Shuffle to avoid directional bias
    random.shuffle(my_atari_moves)
    for r, c in my_atari_moves:
        if is_legal(r, c):
            return (r + 1, c + 1), memory

    # 4b. Aggression: Capture opponent stones in Atari
    opp_atari_moves = []
    for g_id, data in group_data.items():
        if data['color'] == OPP and len(data['libs']) == 1:
            lib = list(data['libs'])[0]
            opp_atari_moves.append(lib)
            
    random.shuffle(opp_atari_moves)
    for r, c in opp_atari_moves:
        if is_legal(r, c):
            return (r + 1, c + 1), memory
            
    # 4c. General Move Selection (Heuristic Scoring)
    best_move = None
    best_score = -float('inf')
    
    # Identify candidates: Star points + Empty spots near existing stones
    candidates = set()
    
    # Star points (Standard Openings)
    stars = [
        (3,3), (3,15), (15,3), (15,15), # 4-4
        (2,3), (3,2), (2,15), (15,2), (16,3), (3,16), (16,15), (15,16), # 3-4
        (9,9), (9,3), (3,9), (15,9), (9,15) # Center/Sides
    ]
    for r, c in stars:
        if board[r][c] == EMPTY:
            candidates.add((r, c))
    
    # Neighbors of all stones
    # Iterate all cells to find empty neighbors of occupied cells
    # (Faster than iterating valid moves if board is sparse, safer if dense)
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != EMPTY:
                for nr, nc in get_neighbors(r, c):
                    if board[nr][nc] == EMPTY:
                        candidates.add((nr, nc))
    
    # If board is empty (first move), ensure candidates has something
    if not candidates:
        candidates.add((3, 15)) # Default opener
        candidates.add((15, 3))
    
    candidate_list = list(candidates)
    random.shuffle(candidate_list)
    
    for r, c in candidate_list:
        if not is_legal(r, c):
            continue
            
        score = 0.0
        
        # Heuristic 1: Star point bonus
        if (r, c) in stars:
            score += 5.0
            
        # Heuristic 2: Local Liberty/Connection analysis
        opp_libs_reduced = 0
        friendly_libs_added = 0
        
        for nr, nc in get_neighbors(r, c):
            n_color = board[nr][nc]
            if n_color == OPP:
                # Pushing opponent is good
                score += 1.0
                # Putting opponent in Atari (reducing to 1 lib) is very good
                g_id = groups.get((nr, nc))
                if g_id is not None:
                    # Current libs (before my move). 
                    # If they have 2, I reduce to 1.
                    if len(group_data[g_id]['libs']) == 2:
                        score += 8.0
            elif n_color == ME:
                # Connecting is good for stability
                score += 1.0
                # Saving a weak group (low libs) is crucial
                g_id = groups.get((nr, nc))
                if g_id is not None:
                     if len(group_data[g_id]['libs']) <= 2:
                         score += 4.0
            else:
                # Empty neighbor = liberty for new stone
                friendly_libs_added += 1
        
        score += friendly_libs_added * 0.5
        
        # Heuristic 3: Avoid 1st/2nd line early in game
        # Distance to nearest edge
        dist_to_edge = min(r, SIZE - 1 - r, c, SIZE - 1 - c)
        if dist_to_edge == 0:
            score -= 5.0 # Death line
        elif dist_to_edge == 1:
            score -= 1.0 # Low value
            
        # Add slight noise to prevent loops in similar positions
        score += random.random() * 0.5
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    # Fallback: If no candidate was legal (e.g. board full of eyes), try everything
    if best_move is None:
        all_spots = [(r, c) for r in range(SIZE) for c in range(SIZE)]
        random.shuffle(all_spots)
        for r, c in all_spots:
            if is_legal(r, c):
                best_move = (r, c)
                break
    
    # Return result
    if best_move:
        return (best_move[0] + 1, best_move[1] + 1), memory
    
    # Pass if no moves possible
    return (0, 0), memory
