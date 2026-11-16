
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go policy that determines the next move based on capturing/saving stones in Atari
    and simple positional heuristics.
    """
    
    # -------------------------------------------------------------------------
    # 1. State Parsing & Constants
    # -------------------------------------------------------------------------
    BOARD_SIZE = 19
    EMPTY = 0
    ME = 1
    OPP = 2
    
    # 1-based to 0-based conversion
    my_stones = set((r-1, c-1) for r, c in me)
    opp_stones = set((r-1, c-1) for r, c in opponent)
    
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in my_stones:
        board[r][c] = ME
    for r, c in opp_stones:
        board[r][c] = OPP
        
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # -------------------------------------------------------------------------
    # 2. Group Analysis (Flood Fill)
    # -------------------------------------------------------------------------
    # Determine liberties for all groups to identify Atari situations.
    
    group_map = {} # (r,c) -> group_id
    groups = {}    # group_id -> info
    
    visited = set()
    group_counter = 0
    
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY and (r, c) not in visited:
                color = board[r][c]
                group_id = group_counter
                group_counter += 1
                
                stack = [(r, c)]
                visited.add((r, c))
                group_stones = []
                group_libs = set()
                
                while stack:
                    curr_r, curr_c = stack.pop()
                    group_stones.append((curr_r, curr_c))
                    group_map[(curr_r, curr_c)] = group_id
                    
                    for dr, dc in DIRECTIONS:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            if board[nr][nc] == EMPTY:
                                group_libs.add((nr, nc))
                            elif board[nr][nc] == color and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                stack.append((nr, nc))
                
                groups[group_id] = {
                    'color': color,
                    'stones': group_stones,
                    'liberties': list(group_libs),
                    'lib_count': len(group_libs)
                }

    # -------------------------------------------------------------------------
    # 3. Helpers: Hashing & Logic
    # -------------------------------------------------------------------------
    
    def get_board_hash(b):
        # A tuple of tuples is hashable
        return tuple(tuple(row) for row in b)
    
    # Retrieve the state we left the board in after our LAST move.
    # We use this to check for Simple Ko (recreating the immediate past state).
    prev_state_hash = memory.get('prev_board_hash', None)

    def get_next_board_state(move_r, move_c):
        """Simulate placing a stone and resolving captures."""
        new_b = [row[:] for row in board]
        new_b[move_r][move_c] = ME
        
        # Check neighbors for capture
        captured_any = False
        opp_neighbors = set()
        for dr, dc in DIRECTIONS:
            nr, nc = move_r + dr, move_c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == OPP:
                opp_neighbors.add((nr, nc))
                
        for nr, nc in opp_neighbors:
            g_id = group_map.get((nr, nc))
            if g_id is not None:
                g = groups[g_id]
                # If this group has 1 liberty and it is the point we played
                if g['lib_count'] == 1 and (move_r, move_c) in g['liberties']:
                    # Remove stones
                    captured_any = True
                    for sr, sc in g['stones']:
                        new_b[sr][sc] = EMPTY
        return new_b, captured_any

    def is_legal(r, c):
        if board[r][c] != EMPTY:
            return False, None
        
        # 1. Suicide Check
        # A move is suicide if it has 0 liberties AND captures nothing AND connects to no living group.
        # Check simple liberties of the point
        libs = 0
        friendly_adj = []
        opp_adj = []
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                val = board[nr][nc]
                if val == EMPTY:
                    libs += 1
                elif val == ME:
                    friendly_adj.append((nr, nc))
                else:
                    opp_adj.append((nr, nc))
        
        # Determine if we capture opponent
        captures = False
        for nr, nc in opp_adj:
            g_id = group_map[(nr, nc)]
            # If we fill their last liberty
            if groups[g_id]['lib_count'] == 1:
                captures = True
                break
        
        # Determine if we connect to a living group
        # (A group that has at least one liberty OTHER than (r,c))
        connects_to_life = False
        if not captures and libs == 0:
            for nr, nc in friendly_adj:
                g_id = group_map[(nr, nc)]
                if groups[g_id]['lib_count'] > 1:
                    connects_to_life = True
                    break
        
        is_suicide = (libs == 0 and not captures and not connects_to_life)
        if is_suicide:
            return False, None

        # 2. Ko Check
        # If we have a hash history, simple ko check
        if prev_state_hash is not None:
            # Only simulate full board if there's a risk (e.g. captures)
            # or simply do it for all strong candidates.
            # To be safe and correct:
            new_b, _ = get_next_board_state(r, c)
            h = get_board_hash(new_b)
            if h == prev_state_hash:
                return False, None
            return True, h
        
        return True, "PENDING"

    # -------------------------------------------------------------------------
    # 4. Candidate Identification
    # -------------------------------------------------------------------------
    candidates = set()
    
    # urgent points (Atari)
    urgent_save = []
    urgent_kill = []
    
    for g in groups.values():
        if g['lib_count'] == 1:
            if g['color'] == ME:
                urgent_save.extend(g['liberties'])
            else:
                urgent_kill.extend(g['liberties'])
    
    candidates.update(urgent_save)
    candidates.update(urgent_kill)
    
    # Star points
    stars = [(3,3), (3,15), (15,3), (15,15), (9,9), (9,3), (9,15), (3,9), (15,9)]
    for pt in stars:
        if board[pt[0]][pt[1]] == EMPTY:
            candidates.add(pt)
            
    # Neighbors of existing stones (Action zone)
    existing_stones = my_stones | opp_stones
    if not existing_stones:
        # Empty board -> Star point
        candidates.add((3, 15))
    else:
        for r, c in existing_stones:
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                    candidates.add((nr, nc))

    # -------------------------------------------------------------------------
    # 5. Scoring & Selection
    # -------------------------------------------------------------------------
    best_score = -float('inf')
    best_move = (0, 0) # Default Pass
    
    candidate_list = list(candidates)
    random.shuffle(candidate_list) # Add randomness

    for r, c in candidate_list:
        legal, pot_hash = is_legal(r, c)
        if not legal:
            continue
            
        score = 0
        
        # -- Objective 1: Save self from Atari --
        # If playing here fills the last liberty of a friendly group,
        # does it actually save it (increase libs or capture attacker)?
        saved_group = False
        is_atari_fill = False
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == ME:
                gid = group_map[(nr, nc)]
                if groups[gid]['lib_count'] == 1:
                    is_atari_fill = True
                    # Check if this move gains new liberties
                    # Count liberties of (r,c) itself
                    new_libs = 0
                    for ddr, ddc in DIRECTIONS:
                        nnr, nnc = r + ddr, c + ddc
                        if 0 <= nnr < BOARD_SIZE and 0 <= nnc < BOARD_SIZE and board[nnr][nnc] == EMPTY:
                            new_libs += 1
                    
                    # Check if it captures (which implies infinite life usually)
                    _, caps = get_next_board_state(r, c) # Slight redundant calc but safe
                    
                    if new_libs > 0 or caps:
                        score += 5000 # Massive Priority
                        saved_group = True
        
        # -- Objective 2: Capture Opponent --
        if (r, c) in urgent_kill:
            score += 4000
            
        # -- Objective 3: Attack (Put opponent in Atari) --
        # If opponent has 2 libs, and we take 1.
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == OPP:
                gid = group_map[(nr, nc)]
                if groups[gid]['lib_count'] == 2:
                    score += 200     

        # -- Objective 4: Shape / Positioning --
        # Star points good
        if (r, c) in stars:
            score += 20
        
        # Avoid edge early game
        if len(existing_stones) < 50:
            if r == 0 or r == 18 or c == 0 or c == 18:
                score -= 50
            elif r == 1 or r == 17 or c == 1 or c == 17:
                score -= 10
        
        # Self-Atari Penalties (Don't play into death)
        # If we are NOT saving a group, and the move has 0 liberties, it's bad shape
        # (Even if legal because connects to life, it reduces total liberties usually)
        if not saved_group and not is_atari_fill:
            # Check liberties of placed stone
            libs_here = 0
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                    libs_here += 1
            if libs_here == 0:
                 # Unless we capture
                 _, caps = get_next_board_state(r, c)
                 if not caps:
                     score -= 500
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # -------------------------------------------------------------------------
    # 6. Finalize
    # -------------------------------------------------------------------------
    if best_move == (0, 0):
        # Pass
        return (0, 0), memory
        
    br, bc = best_move
    
    # Update Memory with new board hash for next turn's Ko check
    final_board, _ = get_next_board_state(br, bc)
    memory['prev_board_hash'] = get_board_hash(final_board)
    
    # Return 1-based index
    return (br + 1, bc + 1), memory
