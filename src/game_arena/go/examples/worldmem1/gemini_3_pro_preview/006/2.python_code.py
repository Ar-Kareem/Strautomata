
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A robust Go policy focusing on liberties, captures, and simple shape heuristics.
    """
    # ---------------- CONFIGURATION ---------------- #
    BOARD_SIZE = 19
    # Heuristic Weights
    W_CAPTURE = 2000          # High priority to capture
    W_ATARI_SAVE = 2200       # Highest priority to save self
    W_ATARI_THREAT = 100      # Put enemy in Atari
    W_CONNECT = 60            # Connect two groups
    W_LIBERTY = 10            # Gain individual liberties
    W_SIDE_3_4 = 15           # Prefer 3rd/4th line
    W_CENTER = 2              # Center minimal bonus
    W_EDGE = -20              # Avoid edge early
    W_LINE_2 = -5             # Avoid line 2 early
    W_FILL_EYE = -500         # Do not fill own eyes

    # ---------------- HELPERS ---------------- #
    
    # Convert 1-based (API) to 0-based (Internal)
    def to_int(r, c): return r - 1, c - 1
    def to_ext(r, c): return r + 1, c + 1

    # 1. RECONSTRUCT BOARD
    # 0 = Empty, 1 = Me, -1 = Opponent
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    me_set = set()
    opp_set = set()

    for r, c in me:
        rr, cc = to_int(r, c)
        if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
            board[rr][cc] = 1
            me_set.add((rr, cc))

    for r, c in opponent:
        rr, cc = to_int(r, c)
        if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
            board[rr][cc] = -1
            opp_set.add((rr, cc))

    # 2. GROUP ANALYSIS (LIBERTIES)
    # Returns list of dicts: {'color': int, 'stones': set, 'libs': set}
    groups = []
    visited = set()
    stone_to_group_idx = {}

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = board[r][c]
            if color != 0 and (r, c) not in visited:
                # Flood fill
                stack = [(r, c)]
                grp_stones = set()
                grp_libs = set()
                grp_stones.add((r, c))
                visited.add((r, c))
                
                while stack:
                    cur_r, cur_c = stack.pop()
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = cur_r + dr, cur_c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            n_color = board[nr][nc]
                            if n_color == color:
                                if (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    grp_stones.add((nr, nc))
                                    stack.append((nr, nc))
                            elif n_color == 0:
                                grp_libs.add((nr, nc))
                
                g_idx = len(groups)
                for s in grp_stones:
                    stone_to_group_idx[s] = g_idx
                groups.append({'color': color, 'stones': grp_stones, 'libs': grp_libs})

    # Separate groups
    my_groups = [g for g in groups if g['color'] == 1]
    opp_groups = [g for g in groups if g['color'] == -1]

    # 3. KO DETECTION
    # Identify if playing at specific spot is forbidden due to simple Ko.
    # Logic: If I lost exactly 1 stone since my last recorded state, and the opponent played 1 stone,
    # and the empty spot is where I lost the stone, I verify strict Ko conditions during simulation.
    forbidden_ko_point = None
    if 'prev_me' in memory:
        # prev_me stored as list of tuples
        prev_me_set = set(tuple(x) for x in memory['prev_me'])
        lost_stones = prev_me_set - me_set
        # Simple Ko usually involves losing 1 stone and the spot becoming empty
        if len(lost_stones) == 1:
            ko_candidate = list(lost_stones)[0]
            if board[ko_candidate[0]][ko_candidate[1]] == 0:
                forbidden_ko_point = ko_candidate

    # 4. CANDIDATE GENERATION
    candidates = set()
    
    # A. Liberties of all groups (Critical for attack/defend)
    for g in groups:
        for lib in g['libs']:
            candidates.add(lib)
            
    # B. Star Points (Opening strategy)
    star_points = [
        (3,3), (3,15), (15,3), (15,15), # 4-4
        (2,3), (16,3), (2,15), (16,15), # 3-4
        (3,2), (3,16), (15,2), (15,16),
        (9,9), (3,9), (15,9), (9,3), (9,15)
    ]
    for sp in star_points:
        if board[sp[0]][sp[1]] == 0:
            candidates.add(sp)
            
    # C. Random filler if candidates are sparse
    if len(candidates) < 10:
        for _ in range(20):
            rr = random.randint(0, BOARD_SIZE-1)
            cc = random.randint(0, BOARD_SIZE-1)
            if board[rr][cc] == 0:
                candidates.add((rr, cc))

    # 5. EVALUATION LOOP
    best_score = -float('inf')
    best_move = None # Default to Pass (0,0) if no moves found, but handled at end

    candidate_list = list(candidates)
    random.shuffle(candidate_list) # Jitter for equal moves

    for r, c in candidate_list:
        # Safety check: must be empty
        if board[r][c] != 0: continue
        
        # --- SIMULATION ---
        # 1. Identify neighbors
        neighbors = []
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        
        # 2. Check captures
        captured_stones = 0
        captured_groups_indices = set()
        
        for nr, nc in neighbors:
            if board[nr][nc] == -1:
                g_idx = stone_to_group_idx[(nr, nc)]
                if g_idx not in captured_groups_indices:
                    g = groups[g_idx]
                    # If the group has 1 liberty and it is (r,c), it's captured
                    if len(g['libs']) == 1 and (r, c) in g['libs']:
                        captured_stones += len(g['stones'])
                        captured_groups_indices.add(g_idx)

        # 3. Check Suicide / Self Liberties
        # We need to calculate the liberties of the NEW stone.
        # Libs = Sum(Empty Neighbors) + Sum(Libs of connected friendlies) - (r,c itself)
        # Note: If connected friendlies are in Atari, we must ensure the merge increases liberties.
        
        new_stone_libs = set()
        connected_friendly_indices = set()
        
        for nr, nc in neighbors:
            if board[nr][nc] == 0:
                new_stone_libs.add((nr, nc))
            elif board[nr][nc] == 1:
                g_idx = stone_to_group_idx[(nr, nc)]
                connected_friendly_indices.add(g_idx)
                # Add liberties of friendly group
                new_stone_libs.update(groups[g_idx]['libs'])
        
        # The spot (r,c) was a liberty for friends, now occupied
        if (r, c) in new_stone_libs:
            new_stone_libs.remove((r, c))
            
        is_suicide = (len(new_stone_libs) == 0)
        
        # --- LEGALITY CHECKS ---
        # Rule: Cannot commit suicide unless it captures opponent stones.
        if is_suicide and captured_stones == 0:
            continue
            
        # Rule: Ko
        if forbidden_ko_point and (r, c) == forbidden_ko_point:
            # Recreate scenario: if I capture exactly 1 stone, 
            # and the resulting board matches previous...
            # Simplification: If forbidden_point is set and I simply play there,
            # assume it's Ko if I capture 1 stone and have 1 liberty (snapback/ko shape).
            if captured_stones == 1 and len(new_stone_libs) <= 1:
                continue

        # --- SCORING ---
        score = 0.0
        
        # A. Captures
        if captured_stones > 0:
            score += W_CAPTURE
            score += captured_stones * 50
        
        # B. Saving Self (Atari Defense)
        saved_stones_count = 0
        was_in_atari = False
        
        for g_idx in connected_friendly_indices:
            g = groups[g_idx]
            if len(g['libs']) == 1:
                was_in_atari = True
                saved_stones_count += len(g['stones'])
        
        if was_in_atari:
            # If we gained liberties or captured, we saved them
            if len(new_stone_libs) > 1 or captured_stones > 0:
                score += W_ATARI_SAVE
                score += saved_stones_count * 20
            else:
                # Extending but still 1 liberty (bad usually, unless filling libs for capture race)
                score -= 50
        
        # C. Threatening Enemy (Atari Attack)
        for nr, nc in neighbors:
            if board[nr][nc] == -1:
                g_idx = stone_to_group_idx[(nr, nc)]
                # If enemy had 2 liberties, now has 1
                if len(groups[g_idx]['libs']) == 2:
                    score += W_ATARI_THREAT

        # D. Connecting Groups
        if len(connected_friendly_indices) > 1:
            score += W_CONNECT * len(connected_friendly_indices)

        # E. Positional / Shape
        # Liberties
        score += len(new_stone_libs) * W_LIBERTY
        
        # Location
        dist_edge_r = min(r, BOARD_SIZE - 1 - r)
        dist_edge_c = min(c, BOARD_SIZE - 1 - c)
        min_dist = min(dist_edge_r, dist_edge_c)
        
        if min_dist == 0: score += W_EDGE
        elif min_dist == 1: score += W_LINE_2
        elif min_dist == 2: score += W_SIDE_3_4
        elif min_dist == 3: score += W_SIDE_3_4
        else: score += W_CENTER
        
        # Eye Check
        # If all orthogonal neighbors are friendly, we might be filling an eye.
        friendly_orth = sum(1 for nr, nc in neighbors if board[nr][nc] == 1)
        if friendly_orth == 4:
            score += W_FILL_EYE

        # F. Random Jitter
        score += random.random() * 5

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # 6. RETURN
    # Prepare memory for next turn (store my stones to detect losses)
    # Simulate adding the best move to 'me'
    new_me = list(me)
    if best_move:
        # Note: We store the 'internal' tuple in a list, but memory needs to be serializable.
        # List of tuples is fine.
        new_me.append(to_int(*best_move)) 

    new_memory = {
        'prev_me': new_me
    }

    if best_move is None:
        return (0, 0), new_memory
    
    return to_ext(*best_move), new_memory
