
import sys
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Go policy function.
    Args:
        me: List of (row, col) tuples for player's stones (1-based).
        opponent: List of (row, col) tuples for opponent's stones (1-based).
    Returns:
        (row, col) tuple for the next move (1-based). (0, 0) for pass.
    """
    
    # --- Constants & Setup ---
    BOARD_SIZE = 19
    EMPTY = 0
    ME = 1
    OPP = 2
    
    # Directions for neighbor checks
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Internal 0-indexed board
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, c in me:
        board[r-1][c-1] = ME
    for r, c in opponent:
        board[r-1][c-1] = OPP

    # --- Group Analysis ---
    # We will identify all groups (chains) and calculate their liberties.
    # group_map: (r,c) -> group_id
    # groups: group_id -> {color, stones (set), liberties (set)}
    
    group_map = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    groups = {}
    group_counter = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY and group_map[r][c] == -1:
                # Start flood fill
                color = board[r][c]
                gid = group_counter
                group_counter += 1
                
                stack = [(r, c)]
                group_map[r][c] = gid
                stones = {(r, c)}
                liberties = set()
                
                while stack:
                    curr_r, curr_c = stack.pop()
                    for dr, dc in DIRS:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if board[nr][nc] == EMPTY:
                                liberties.add((nr, nc))
                            elif board[nr][nc] == color and group_map[nr][nc] == -1:
                                group_map[nr][nc] = gid
                                stones.add((nr, nc))
                                stack.append((nr, nc))
                
                groups[gid] = {
                    'color': color,
                    'stones': list(stones),
                    'liberties': list(liberties),
                    'id': gid
                }

    # --- Heuristic Scoring ---
    
    # We will score every legal move (empty spot).
    # To optimize, we focus on:
    # 1. Liberties of all groups (critical points).
    # 2. Neighbors of existing stones.
    # 3. Star points (if board is open).
    
    candidates = set()
    
    # Add all liberties of all groups to candidates
    for g in groups.values():
        for lib in g['liberties']:
            candidates.add(lib)
            
    # Add neighbors of all stones to candidates (Local fighting shapes)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                        candidates.add((nr, nc))

    # Add star points (4-4, 3-4, 3-3, etc)
    stars = [
        (3, 3), (3, 15), (15, 3), (15, 15), # 4-4 points
        (2, 3), (3, 2), (2, 15), (3, 16), (15, 2), (16, 3), (15, 16), (16, 15), # 3-4 points
        (2, 2), (2, 16), (16, 2), (16, 16), # 3-3 points
        (9, 9), (3, 9), (9, 3), (15, 9), (9, 15) # Tengen and sides
    ]
    for sr, sc in stars:
        if board[sr][sc] == EMPTY:
            candidates.add((sr, sc))
            
    # If candidates is empty (empty board start), add star points
    if not candidates:
        for sr, sc in stars:
            candidates.add((sr, sc))

    best_move = None
    best_score = -float('inf')
    
    # Helper to check if a spot is a "true eye" (surrounded by own stones)
    # Simple heuristic: if all 4 neighbors are ME (or wall), and no enemy in corners (ignoring precise eye logic for speed)
    def is_likely_eye(r, c):
        my_neighbors = 0
        total_neighbors = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                total_neighbors += 1
                if board[nr][nc] == ME:
                    my_neighbors += 1
        # If surrounded by edges + my stones, it's likely an eye
        return my_neighbors == total_neighbors

    for (r, c) in candidates:
        score = random.random() # Small noise to break ties
        
        # --- Simulate Move ---
        # We need to know:
        # 1. Did we capture anything?
        # 2. What are the liberties of the new group formed?
        
        captured_stones_count = 0
        captured_groups_ids = set()
        
        neighbor_my_groups_ids = set()
        neighbor_opp_groups_ids = set()
        
        liberties_of_neighbors = {} # map gid -> liberty_count
        
        # Check neighbors
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                nid = group_map[nr][nc]
                if nid != -1:
                    if groups[nid]['color'] == OPP:
                        neighbor_opp_groups_ids.add(nid)
                    else:
                        neighbor_my_groups_ids.add(nid)
        
        # Check Captures
        for gid in neighbor_opp_groups_ids:
            libs = groups[gid]['liberties']
            # If the only liberty of this opponent group is the point we play (r,c)
            if len(libs) == 1 and (r, c) in libs:
                captured_groups_ids.add(gid)
                captured_stones_count += len(groups[gid]['stones'])
        
        # Move legality check: Suicide?
        # A move is suicide if it captures nothing AND creates a group with 0 liberties.
        
        # Calculate new liberties
        # Start with empty neighbors of (r,c)
        new_liberties_set = set()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr][nc] == EMPTY:
                    new_liberties_set.add((nr, nc))
        
        # Merge liberties from friendly neighbor groups
        for gid in neighbor_my_groups_ids:
            for l in groups[gid]['liberties']:
                if l != (r, c): # Remove the spot we just filled
                    new_liberties_set.add(l)
        
        # Add liberties created by capturing opponent stones
        # The stones of captured groups become liberties
        if captured_stones_count > 0:
            for gid in captured_groups_ids:
                for stone_r, stone_c in groups[gid]['stones']:
                    new_liberties_set.add((stone_r, stone_c))
        
        final_liberties_count = len(new_liberties_set)
        
        # --- Penalties and Rules ---
        
        # Rule: Suicide is illegal (usually). 
        # If no liberties and no captures, strictly forbid.
        if final_liberties_count == 0:
            continue
            
        # Rule: Eye Protection
        # If it looks like an eye, heavily penalize filling it unless it captures something significant
        if is_likely_eye(r, c) and captured_stones_count == 0:
            score -= 50000

        # Rule: Self-Atari
        # If move results in a group with 1 liberty: dangerous.
        if final_liberties_count == 1:
            # Exception: Snapback (we capture, but remain with 1 lib).
            # This is risky due to Ko or immediate recapture.
            # Only do it if we capture a lot.
            if captured_stones_count > 0:
                score += (captured_stones_count * 50) - 300 # Capture is good, but fragile state is bad
            else:
                score -= 2000 # Pure self-atari is very bad
        
        # --- Bounties ---
        
        # 1. Capturing Opponent
        if captured_stones_count > 0:
            score += 10000 + (captured_stones_count * 100)
            
        # 2. Saving Own Groups (Defending against Atari)
        # Check if we are merging with a friendly group that was in Atari
        saved_from_atari = False
        for gid in neighbor_my_groups_ids:
            if len(groups[gid]['liberties']) == 1:
                # We are connecting to a group in Atari.
                # Did we gain liberties?
                if final_liberties_count > 1:
                    score += 5000 + (len(groups[gid]['stones']) * 100)
                    saved_from_atari = True
                elif captured_stones_count > 0:
                     # We are in Atari, but we captured, so we live (at least temporarily)
                     score += 4000
        
        # 3. Attacking (Putting opponent in Atari)
        # Note: This is computationally expensive to check perfectly, 
        # so we approximate: if we fill a liberty of an opponent group with 2 liberties.
        for gid in neighbor_opp_groups_ids:
            # We already handled capture (lib=1). What if libs=2?
            # If we play on one liberty, they go to 1 (Atari).
            if len(groups[gid]['liberties']) == 2:
                # But ensure we are not putting ourselves in Atari doing it (ladder check approx)
                if final_liberties_count > 1:
                     score += 500
        
        # 4. Positional / Opening
        # Edge penalty (Line 1 is usually bad early game)
        dist_to_edge = min(r, BOARD_SIZE - 1 - r, c, BOARD_SIZE - 1 - c)
        if dist_to_edge == 0: # Line 1
            score -= 50
        elif dist_to_edge == 1: # Line 2
            score -= 10
        elif dist_to_edge == 2 or dist_to_edge == 3: # Line 3 and 4 (Golden)
            score += 15
        elif dist_to_edge == 9: # Tengen / Center
            score += 10
            
        # Star point bonus (Early game)
        if len(me) + len(opponent) < 30:
            if (r, c) in stars:
                score += 100
                
        # Proximity to friendly stones (Connect/Support)
        # But not too close (efficiency).
        # We checked direct neighbors (connection). What about jumps?
        # Simple proximity boost
        for sr in range(max(0, r-2), min(BOARD_SIZE, r+3)):
            for sc in range(max(0, c-2), min(BOARD_SIZE, c+3)):
                if board[sr][sc] == ME:
                    score += 5

        # Update Best
        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move:
        return (best_move[0] + 1, best_move[1] + 1)
    
    # Pass if no moves found
    return (0, 0)
