
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Board constants
    SIZE = 19
    # 0 = empty, 1 = me, 2 = opponent
    grid = [[0] * SIZE for _ in range(SIZE)]
    
    # Internal 0-based coordinates, inputs are 1-based
    for r, c in me:
        grid[r-1][c-1] = 1
    for r, c in opponent:
        grid[r-1][c-1] = 2
        
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # --- Group Analysis (Flood Fill) ---
    # map: (r,c) -> group_id
    group_map = [[-1] * SIZE for _ in range(SIZE)]
    # map: group_id -> set of liberties (tuples)
    group_libs = {}
    # map: group_id -> count of stones
    group_size = {}
    
    group_counter = 0
    
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] != 0 and group_map[r][c] == -1:
                gid = group_counter
                group_counter += 1
                color = grid[r][c]
                
                # BFS to find component
                q = [(r, c)]
                group_map[r][c] = gid
                current_stones = 0
                current_libs = set()
                
                head = 0
                while head < len(q):
                    curr_r, curr_c = q[head]
                    head += 1
                    current_stones += 1
                    
                    for dr, dc in DIRECTIONS:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < SIZE and 0 <= nc < SIZE:
                            n_val = grid[nr][nc]
                            if n_val == 0:
                                current_libs.add((nr, nc))
                            elif n_val == color and group_map[nr][nc] == -1:
                                group_map[nr][nc] = gid
                                q.append((nr, nc))
                
                group_libs[gid] = current_libs
                group_size[gid] = current_stones

    # --- Move Selection ---
    best_move = (0, 0)
    best_score = -float('inf')
    
    # Standard opening star points (0-indexed)
    star_points = {
        (3,3), (3,15), (15,3), (15,15), # 4-4
        (2,3), (3,2), (16,3), (15,2),   # 3-4 / 4-3
        (9,9),                          # Tengen
        (3,9), (9,3), (15,9), (9,15)    # Sides
    }
    
    # Generate all empty spots
    moves = []
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == 0:
                moves.append((r, c))
                
    random.shuffle(moves) # Randomize checks to break ties arbitrarily
    
    has_legal_move = False
    
    for r, c in moves:
        # Context for the move
        friendly_adj_ids = set()
        enemy_adj_ids = set()
        empty_neighbors_count = 0
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                val = grid[nr][nc]
                if val == 0:
                    empty_neighbors_count += 1
                elif val == 1:
                    friendly_adj_ids.add(group_map[nr][nc])
                elif val == 2:
                    enemy_adj_ids.add(group_map[nr][nc])
        
        # 1. Check Captures
        captures_count = 0
        capture_occurred = False
        
        for egid in enemy_adj_ids:
            # If this enemy group has this move (r,c) as its ONLY liberty, it dies.
            libs = group_libs[egid]
            if len(libs) == 1 and (r, c) in libs:
                capture_occurred = True
                captures_count += group_size[egid]
        
        # 2. Check Suicide (Legality)
        # Suicide: No empty neighbors AND No captures AND All friendly connections have 0 remaining liberties.
        legal = True
        if empty_neighbors_count == 0 and not capture_occurred:
            can_breathe = False
            for fgid in friendly_adj_ids:
                # If friendly group has > 1 liberty, it survives joining (r,c) (which consumes 1 lib)
                if len(group_libs[fgid]) > 1:
                    can_breathe = True
                    break
            if not can_breathe:
                legal = False # Suicide
        
        if not legal:
            continue
            
        has_legal_move = True
        
        # --- Scoring ---
        score = 0.0
        
        # A. Capture Priority
        if capture_occurred:
            score += 10000.0 + (captures_count * 100)
            
        # B. Atari Defense (Saving own stones)
        is_saving = False
        saved_stones_count = 0
        for fgid in friendly_adj_ids:
            if len(group_libs[fgid]) == 1:
                # Helping a group in Atari.
                # Valid save if we captured something OR have empty neighbors OR connect to a rich group
                if capture_occurred or empty_neighbors_count > 0:
                    is_saving = True
                    saved_stones_count += group_size[fgid]
                else:
                    # Check if we connected to a safe group
                    for other_fgid in friendly_adj_ids:
                        if len(group_libs[other_fgid]) > 1:
                            is_saving = True
                            saved_stones_count += group_size[fgid]
                            break
                            
        if is_saving:
            score += 5000.0 + (saved_stones_count * 50)
            
        # C. Atari Attack (Threatening enemy)
        for egid in enemy_adj_ids:
            libs = group_libs[egid]
            # If enemy has exactly 2 liberties and one is (r,c), filling it puts them in Atari
            if len(libs) == 2 and (r, c) in libs:
                score += 500.0
                
        # D. Eye Protection
        # Avoid filling single eyes unless forced or capturing
        if empty_neighbors_count == 0 and len(enemy_adj_ids) == 0:
             if not capture_occurred:
                 score -= 2000.0
                 
        # E. Positional Heuristics
        # Preference for 3rd/4th line
        dist_edge = min(r, SIZE-1-r, c, SIZE-1-c)
        if dist_edge == 0: score -= 25.0
        elif dist_edge == 1: score -= 5.0
        elif dist_edge == 2: score += 10.0
        elif dist_edge == 3: score += 12.0
        
        # Opening points
        stone_count = len(me) + len(opponent)
        if stone_count < 40:
            if (r, c) in star_points:
                score += 50.0
                
        # Proximity to stones (fighting spirit/shape)
        actual_stone_neighbors = 0
        for dr, dc in DIRECTIONS:
            nr, nc = r+dr, c+dc
            if 0<=nr<SIZE and 0<=nc<SIZE and grid[nr][nc] != 0:
                actual_stone_neighbors += 1
        
        if actual_stone_neighbors > 0:
            score += 5.0
            
        # Random noise to prevent loops
        score += random.random()
        
        if score > best_score:
            best_score = score
            best_move = (r + 1, c + 1) # Return to 1-based indexing
            
    if not has_legal_move:
        return (0, 0) # Pass
    
    return best_move
