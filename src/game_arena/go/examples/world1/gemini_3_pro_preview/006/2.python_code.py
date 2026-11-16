
import numpy as np
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A smart Go policy using heuristic analysis of groups, liberties, and local shape.
    """
    BOARD_SIZE = 19
    
    # Pre-defined star points for opening strategy
    STAR_POINTS = [
        (4, 4), (4, 16), (16, 4), (16, 16),
        (10, 10), (10, 4), (10, 16), (4, 10), (16, 10)
    ]

    # Convert 1-based coordinates to 0-based for internal processing
    flattened_me = set((r-1, c-1) for r, c in me)
    flattened_opp = set((r-1, c-1) for r, c in opponent)
    
    # Initialize board: 0 = empty, 1 = me, -1 = opponent
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    for r, c in flattened_me:
        board[r, c] = 1
    for r, c in flattened_opp:
        board[r, c] = -1

    # --- Helper Functions ---

    def get_neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                yield nr, nc

    def get_groups_and_liberties(current_board):
        """
        Scans board to find all groups.
        Returns:
            group_map: 2D array where value is group_id (or -1 if empty)
            groups: dict {group_id: {'color': int, 'stones': set, 'liberties': set}}
        """
        visited = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=bool)
        group_map = np.full((BOARD_SIZE, BOARD_SIZE), -1, dtype=int)
        groups = {}
        group_id_counter = 0

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = current_board[r, c]
                if color != 0 and not visited[r, c]:
                    # Flood fill for new group
                    gid = group_id_counter
                    group_id_counter += 1
                    
                    stones = set()
                    liberties = set()
                    stack = [(r, c)]
                    visited[r, c] = True
                    
                    while stack:
                        curr_r, curr_c = stack.pop()
                        stones.add((curr_r, curr_c))
                        group_map[curr_r, curr_c] = gid
                        
                        for nr, nc in get_neighbors(curr_r, curr_c):
                            if current_board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif current_board[nr, nc] == color and not visited[nr, nc]:
                                visited[nr, nc] = True
                                stack.append((nr, nc))
                    
                    groups[gid] = {
                        'color': color,
                        'stones': stones,
                        'liberties': liberties
                    }
        return group_map, groups

    # --- Analysis ---

    initial_group_map, initial_groups = get_groups_and_liberties(board)
    
    my_groups = [g for g in initial_groups.values() if g['color'] == 1]
    opp_groups = [g for g in initial_groups.values() if g['color'] == -1]

    # 1. Urgent: Check for winning Captures (Enemy in Atari)
    capturing_moves = []
    for g in opp_groups:
        if len(g['liberties']) == 1:
            kill_spot = list(g['liberties'])[0]
            # Verify legality (not suicide) by checking if we have liberties after move
            # Simple check: does this move also put us in 0 liberties?
            # We assume killing allows us to live (stone replaces liberty).
            capturing_moves.append(kill_spot)
    
    # Prioritize capturing moves
    if capturing_moves:
        # Pick one that might also save our stones or is centrally located
        best_kill = max(capturing_moves, key=lambda p: (1 if p in [l for mg in my_groups for l in mg['liberties']] else 0))
        return (best_kill[0] + 1, best_kill[1] + 1)

    # 2. Urgent: Check for Saving Moves (Self in Atari)
    saving_moves = []
    for g in my_groups:
        if len(g['liberties']) == 1:
            # Try to extend or capture
            liberty = list(g['liberties'])[0]
            
            # Simulation: Does playing here increase liberties?
            # A quick heuristic: look at neighbors of the liberty
            # If neighbor is empty, we gain liberties.
            # If neighbor is enemy in atari, we capture and gain liberties.
            
            # We must verify we don't just fill the last liberty and die (unless capturing).
            # check if the liberty spot connects to another friendly group with liberties
            
            # Simple simulation for accuracy
            test_board = board.copy()
            test_board[liberty] = 1
            _, test_groups = get_groups_and_liberties(test_board)
            
            # Find the group at the liberty position
            # Since we rebuilt groups, we have to find which group maps to our coordinate
            # Just iterating test_groups is fast enough for one point
            survived = False
            for tg in test_groups.values():
                if liberty in tg['stones'] and tg['color'] == 1:
                    if len(tg['liberties']) > 1:
                        survived = True
                    break
            
            if survived:
                saving_moves.append(liberty)
            
            # Also check if we can capture an adjacent enemy to save ourselves
            # (Already covered by step 1, but step 1 is general. This is specific context).
            
    if saving_moves:
        # Pick the one closest to center
        best_save = min(saving_moves, key=lambda p: (abs(p[0]-9) + abs(p[1]-9)))
        return (best_save[0] + 1, best_save[1] + 1)

    # 3. Candidate Generation for General Play
    candidates = set()
    
    # A. Star Points (if opening)
    stones_count = len(flattened_me) + len(flattened_opp)
    if stones_count < 20:
        for sp in STAR_POINTS:
            r, c = sp[0]-1, sp[1]-1 # adjust to 0-based
            if board[r, c] == 0:
                candidates.add((r, c))

    # B. Neighbors of existing stones (Local battles/Shape)
    # Reducing search space to adjacent to occupied stones
    occupied = flattened_me.union(flattened_opp)
    for r, c in occupied:
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 0:
                candidates.add((nr, nc))
    
    # If board is empty (first move), add center
    if not candidates:
        candidates.add((3, 3)) # 4-4 point
        candidates.add((15, 3))
        candidates.add((3, 15))
        candidates.add((15, 15))

    # 4. Scoring Candidates
    best_score = -float('inf')
    best_move = None
    
    candidate_list = list(candidates)
    random.shuffle(candidate_list) # Add randomness for equal scores

    for r, c in candidate_list:
        score = 0
        
        # --- Filters ---
        
        # 1. Don't fill own eye
        # Heuristic: if all 4 neighbors are me, it's likely an eye.
        neighbors = list(get_neighbors(r, c))
        my_neighbors = sum(1 for nr, nc in neighbors if board[nr, nc] == 1)
        opp_neighbors = sum(1 for nr, nc in neighbors if board[nr, nc] == -1)
        
        if my_neighbors == len(neighbors):
            continue # Don't fill logic eye
            
        # 2. Suicide Check & Self-Atari Check
        # Fast local check: effective liberties = empty neighbors + sum(liberties of friendly neighbor groups) - 1 (the spot itself)
        # This is complex due to merging. We do a quick simulation.
        # However, to save time, we approximate.
        
        # Count direct empty neighbors (immediate liberties)
        empty_neighbors = 0
        friendly_groups_ids = set()
        enemy_groups_ids = set()
        
        for nr, nc in neighbors:
            if board[nr, nc] == 0:
                empty_neighbors += 1
            elif board[nr, nc] == 1:
                gid = initial_group_map[nr, nc]
                if gid != -1: friendly_groups_ids.add(gid)
            elif board[nr, nc] == -1:
                gid = initial_group_map[nr, nc]
                if gid != -1: enemy_groups_ids.add(gid)

        # Check for capture (does this move kill an adjacent enemy?)
        captures_count = 0
        for gid in enemy_groups_ids:
            if len(initial_groups[gid]['liberties']) == 1:
                # We are filling the last liberty
                captures_count += len(initial_groups[gid]['stones'])
        
        # Check estimated liberties of resulting group
        # This is a lower bound estimate.
        estimated_liberties = empty_neighbors
        for gid in friendly_groups_ids:
            # Add liberties of merged group, minus 1 (the current spot used to be a liberty)
            estimated_liberties += (len(initial_groups[gid]['liberties']) - 1)
        
        # Handle Suicide: No liberties and no captures
        if estimated_liberties == 0 and captures_count == 0:
            continue # Illegal suicide
            
        # Penalty for Self-Atari (unless capturing)
        if estimated_liberties <= 1 and captures_count == 0:
            score -= 50
        
        # --- Heuristics ---
        
        # Reward Captures
        score += captures_count * 100
        
        # Reward reducing enemy liberties (Pressure)
        # If we touch an enemy group, we likely reduced its liberties
        score += len(enemy_groups_ids) * 5
        
        # Influence / Territory
        # Prefer lines 3 and 4 (indices 2, 3, 15, 16)
        dist_to_edge = min(r, 18-r, c, 18-c)
        if dist_to_edge == 2 or dist_to_edge == 3: # 3rd or 4th line
            score += 10
        elif dist_to_edge == 0: # 1st line (edge) usually bad early game
            score -= 5
            
        # Shape: Avoid Empty Triangle
        # (Too expensive to check perfectly, but avoiding moves with 2 friendly neighbors and 0 empty intervals is good)
        
        # Connection
        score += len(friendly_groups_ids) * 2
        
        # Central bias in opening
        if stones_count < 60:
            dist_center = abs(r - 9) + abs(c - 9)
            score -= dist_center * 0.5

        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    if best_move:
        return (best_move[0] + 1, best_move[1] + 1)
    
    # Fallback: Pass
    return (0, 0)
