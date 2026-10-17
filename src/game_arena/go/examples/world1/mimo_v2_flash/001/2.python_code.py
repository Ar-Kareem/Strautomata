
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Hybrid policy: Captures > Defends > Influence Maximization > Pass
    """
    SIZE = 19
    
    # Helper to check if a point is on board
    def on_board(r, c):
        return 1 <= r <= SIZE and 1 <= c <= SIZE

    # Helper to get neighbors
    def get_neighbors(r, c):
        return [(r-1, c), (r+1, c), (r-1, c-1), (r+1, c+1), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c-1)]
        # Using 8-connectivity for influence, but strict logic for liberties (4-connected usually, 
        # but Go is orthogonal. Let's stick to standard Go logic: orthogonal for liberties.
        # However, influence often considers diagonals. Let's define separate lists.
    
    def get_orthogonal_neighbors(r, c):
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

    # Convert lists to sets for fast lookups
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set.union(opp_set)

    # 1. Identify Candidate Moves
    candidates = set()
    
    # Expand around my stones (defense/capture opportunities)
    for r, c in me:
        for nr, nc in get_orthogonal_neighbors(r, c):
            if on_board(nr, nc) and (nr, nc) not in all_stones:
                candidates.add((nr, nc))
                
    # Expand around opponent stones (capture opportunities)
    for r, c in opponent:
        for nr, nc in get_orthogonal_neighbors(r, c):
            if on_board(nr, nc) and (nr, nc) not in all_stones:
                candidates.add((nr, nc))

    # If board is empty (first move), play center
    if not me and not opponent:
        return (10, 10)

    # 2. Evaluation Functions
    def count_group_liberties(start_r, start_c, group_set, stones_set):
        """ BFS to find a group and its liberties. """
        group = []
        queue = [(start_r, start_c)]
        visited = set([(start_r, start_c)])
        
        while queue:
            r, c = queue.pop(0)
            group.append((r, c))
            for nr, nc in get_orthogonal_neighbors(r, c):
                if on_board(nr, nc):
                    if (nr, nc) in stones_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        
        # Count liberties
        liberties = set()
        for r, c in group:
            for nr, nc in get_orthogonal_neighbors(r, c):
                if on_board(nr, nc) and (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        
        return group, liberties

    def is_capture_move(r, c, target_stones):
        """ Check if placing stone at (r,c) captures any enemy group. """
        # Temporarily add stone
        temp_all = all_stones.union({(r, c)})
        temp_target = set(target_stones) # Set of opponent stones
        
        # Check neighbors of (r, c) that are opponent stones
        for nr, nc in get_orthogonal_neighbors(r, c):
            if (nr, nc) in temp_target:
                # Find this group's liberties in the hypothetical board
                _, liberties = count_group_liberties(nr, nc, None, temp_target.union({(r,c)})) # pass set including new stone logic
                # Note: count_group_liberties uses all_stones logic implicitly, need to adapt
                # Let's rewrite a specific check for efficiency
                
                # BFS for opponent group
                opp_group = set()
                queue = [(nr, nc)]
                visited = set([(nr, nc)])
                while queue:
                    cr, cc = queue.pop(0)
                    opp_group.add((cr, cc))
                    for nnr, nnc in get_orthogonal_neighbors(cr, cc):
                        if on_board(nnr, nnc):
                            if (nnr, nnc) in temp_target and (nnr, nnc) not in visited:
                                visited.add((nnr, nnc))
                                queue.append((nnr, nnc))
                
                # Count liberties of this group
                lib_count = 0
                for gr, gc in opp_group:
                    for nnr, nnc in get_orthogonal_neighbors(gr, gc):
                        if on_board(nnr, nnc) and (nnr, nnc) not in temp_all and (nnr, nnc) not in opp_group:
                            lib_count += 1
                            
                if lib_count == 0:
                    return True
        return False

    # 3. Tactical Scoring
    capture_moves = []
    defend_moves = []
    influence_moves = []

    # Suicide check helper
    def is_suicide(r, c, my_set, opp_set):
        temp_all = my_set.union(opp_set).union({(r, c)})
        # Check liberties of the group formed by placing the stone
        # Find group of (r, c)
        group = set()
        queue = [(r, c)]
        visited = set([(r, c)])
        while queue:
            cr, cc = queue.pop(0)
            group.add((cr, cc))
            for nr, nc in get_orthogonal_neighbors(cr, cc):
                if on_board(nr, nc):
                    if (nr, nc) in my_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        
        # Count liberties
        liberties = set()
        for gr, gc in group:
            for nr, nc in get_orthogonal_neighbors(gr, gc):
                if on_board(nr, nc) and (nr, nc) not in temp_all:
                    liberties.add((nr, nc))
        
        return len(liberties) == 0

    # Evaluate candidates
    best_move = None
    best_score = -1

    for r, c in candidates:
        if is_suicide(r, c, me_set, opp_set):
            continue

        # Check Capture
        if is_capture_move(r, c, opponent):
            capture_moves.append((r, c))
            continue
            
        # Check Defense (Save my stones)
        # If I play here, does it save a 1-liberty group?
        # We check if any adjacent group of mine has only 1 liberty currently
        is_save = False
        for nr, nc in get_orthogonal_neighbors(r, c):
            if (nr, nc) in me_set:
                # Check liberties of this group excluding the move (r,c) yet, 
                # but including (r,c) increases liberties usually.
                # Actually, simpler: find a group with 1 liberty that includes (r,c) as the last liberty
                # Or check if playing (r,c) increases liberties of a neighbor group that is about to die.
                # For simplicity: if neighbor group has 1 liberty, and (r,c) is that liberty, it's a save.
                _, liberties = count_group_liberties(nr, nc, None, me_set)
                if len(liberties) == 1 and (r, c) in liberties:
                    is_save = True
                    break
        if is_save:
            defend_moves.append((r, c))
            continue

        # Influence Scoring
        # Score = (Distance from opponent stones) + (Distance from my stones - 2 to avoid clumping)
        # Normalize by board size
        min_opp_dist = 100
        for orow, ocol in opponent:
            d = abs(r - orow) + abs(c - ocol) # Manhattan distance
            if d < min_opp_dist:
                min_opp_dist = d
        
        min_me_dist = 100
        for mrow, mcol in me:
            d = abs(r - mrow) + abs(c - mcol)
            if d < min_me_dist:
                min_me_dist = d
        
        # Preference for distance from opponent (approaching) and not too close to self (clumping)
        # Ideally 3-5 points away from own stones, and closing in on opponent
        score = min_opp_dist + (5 - abs(min_me_dist - 3))
        influence_moves.append((r, c, score))

    # 4. Selection
    if capture_moves:
        # Prioritize capturing multiple groups or critical captures
        # Simplified: pick first capture (usually sufficient)
        return capture_moves[0]
    
    if defend_moves:
        # Pick any defense (usually urgent)
        return defend_moves[0]

    if influence_moves:
        # Pick move with highest influence score
        influence_moves.sort(key=lambda x: x[2], reverse=True)
        return (influence_moves[0][0], influence_moves[0][1])

    # 5. Pass
    return (0, 0)
