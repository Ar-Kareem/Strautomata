
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy using a Probability Density Function (PDF) approach
    with a 'Hunt' and 'Target' mode.
    
    1. Analyzes the board to detect probable sunk ships and remove them from the fleet/board 
       logic to prevent ghost hunting.
    2. Calculates a probability map for where remaining ships could be placed.
    3. Prioritizes placements that overlap existing hits (Target Mode).
    4. Falls back to finding the best spot for remaining ships in open water (Hunt Mode) 
       using a parity filter for efficiency.
    """
    
    # Constants
    ROWS = 10
    COLS = 10
    EMPTY = 0
    MISS = -1
    HIT = 1
    
    # Determine initial fleet
    initial_fleet = [5, 4, 3, 3, 2]
    
    # Convert to numpy for easier handling
    grid = np.array(board, dtype=int)
    
    # -------------------------------------------------------------------------
    # Step 1: Heuristic Sunk Ship Detection
    # -------------------------------------------------------------------------
    
    remaining_fleet = initial_fleet[:]
    # We use a calculation board where suspected sunk ships are marked as MISS (obstacles)
    calc_grid = grid.copy()
    
    visited_hits = np.zeros((ROWS, COLS), dtype=bool)
    
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r, c] == HIT and not visited_hits[r, c]:
                # Explore component
                stack = [(r, c)]
                component = []
                while stack:
                    curr_r, curr_c = stack.pop()
                    if visited_hits[curr_r, curr_c]:
                        continue
                    visited_hits[curr_r, curr_c] = True
                    component.append((curr_r, curr_c))
                    
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            if grid[nr, nc] == HIT and not visited_hits[nr, nc]:
                                stack.append((nr, nc))
                
                # Analyze component
                comp_len = len(component)
                rs = [p[0] for p in component]
                cs = [p[1] for p in component]
                min_r, max_r = min(rs), max(rs)
                min_c, max_c = min(cs), max(cs)
                
                # Check property: Linear
                is_horizontal = (min_r == max_r) and (max_c - min_c + 1 == comp_len)
                is_vertical = (min_c == max_c) and (max_r - min_r + 1 == comp_len)
                is_linear = is_horizontal or is_vertical
                
                # Only assume sunk if linear, length matches a ship, and bounded
                if is_linear and (comp_len in remaining_fleet):
                    bounded = True
                    if is_horizontal:
                        if min_c > 0 and grid[min_r, min_c - 1] != MISS: bounded = False
                        if max_c < COLS - 1 and grid[min_r, max_c + 1] != MISS: bounded = False
                    else: # Vertical
                        if min_r > 0 and grid[min_r - 1, min_c] != MISS: bounded = False
                        if max_r < ROWS - 1 and grid[max_r + 1, min_c] != MISS: bounded = False
                            
                    if bounded:
                        remaining_fleet.remove(comp_len)
                        for (cr, cc) in component:
                            calc_grid[cr, cc] = MISS

    # -------------------------------------------------------------------------
    # Step 2: Probability Density Calculation
    # -------------------------------------------------------------------------
    
    target_pdf = np.zeros((ROWS, COLS), dtype=float)
    hunt_pdf = np.zeros((ROWS, COLS), dtype=float)
    
    sim_fleet = remaining_fleet if remaining_fleet else [2] # Fallback
    
    for ship_len in sim_fleet:
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - ship_len + 1):
                segment_vals = calc_grid[r, c : c + ship_len]
                if np.any(segment_vals == MISS): continue
                
                hits = np.sum(segment_vals == HIT)
                unknowns = np.sum(segment_vals == EMPTY)
                
                if unknowns > 0:
                    weight = 1
                    if hits > 0:
                        # Target Score: prioritize explaining existing hits
                        weight = 1000 + (100 * hits)
                        target_pdf[r, c : c + ship_len] += (segment_vals == EMPTY) * weight
                    else:
                        # Hunt Score
                        hunt_pdf[r, c : c + ship_len] += (segment_vals == EMPTY) * weight
                        
        # Vertical
        for r in range(ROWS - ship_len + 1):
            for c in range(COLS):
                segment_vals = calc_grid[r : r + ship_len, c]
                if np.any(segment_vals == MISS): continue
                
                hits = np.sum(segment_vals == HIT)
                unknowns = np.sum(segment_vals == EMPTY)
                
                if unknowns > 0:
                    weight = 1
                    if hits > 0:
                        weight = 1000 + (100 * hits)
                        target_pdf[r : r + ship_len, c] += (segment_vals == EMPTY) * weight
                    else:
                        hunt_pdf[r : r + ship_len, c] += (segment_vals == EMPTY) * weight

    # -------------------------------------------------------------------------
    # Step 3: Selection
    # -------------------------------------------------------------------------
    
    valid_mask = (grid == EMPTY)
    
    if np.max(target_pdf) > 0:
        final_map = target_pdf
    else:
        final_map = hunt_pdf
        # Apply parity (Checkerboard)
        indices = np.indices((ROWS, COLS))
        p0 = (indices[0] + indices[1]) % 2 == 0
        p1 = ~p0
        s0 = np.sum(final_map[p0 & valid_mask])
        s1 = np.sum(final_map[p1 & valid_mask])
        
        # Only search on the parity that has higher probability mass
        if s0 + s1 > 0:
            if s0 >= s1: final_map[p1] = 0
            else: final_map[p0] = 0

    final_map[~valid_mask] = -1.0
    
    best_idx = np.argmax(final_map)
    best_loc = np.unravel_index(best_idx, final_map.shape)
    
    # Fallback if map is empty (shouldn't happen unless board full)
    if final_map[best_loc] < 0:
        coords = np.argwhere(grid == EMPTY)
        if len(coords) > 0:
            return int(coords[0][0]), int(coords[0][1])
            
    return int(best_loc[0]), int(best_loc[1])
