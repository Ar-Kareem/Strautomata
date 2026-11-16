
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import random

    # Board size is 19x19
    MAX_ROW = 19
    MAX_COL = 19
    
    # Convert lists to sets for O(1) lookup
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set.union(opp_set)
    
    # Helper: Get neighbors
    def get_neighbors(r, c):
        n = []
        if r > 1: n.append((r-1, c))
        if r < MAX_ROW: n.append((r+1, c))
        if c > 1: n.append((r, c-1))
        if c < MAX_COL: n.append((r, c+1))
        return n

    # Helper: Find group and its liberties
    def get_group_and_liberties(start_stone, player_set):
        group = set()
        liberties = set()
        stack = [start_stone]
        group.add(start_stone)
        
        while stack:
            r, c = stack.pop()
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in player_set and (nr, nc) not in group:
                    group.add((nr, nc))
                    stack.append((nr, nc))
                elif (nr, nc) not in player_set and (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return group, liberties

    # Helper: Check if a move is a capture
    def is_capture(r, c, player_set, opponent_set):
        # Simulate the move
        temp_player = player_set.union({(r, c)})
        # Check all adjacent opponent groups
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opponent_set:
                group, liberties = get_group_and_liberties((nr, nc), opponent_set)
                # If the opponent group has 0 liberties after move, it is captured
                # Note: get_group_and_liberties calculates liberties based on current board.
                # We need to check if the specific move reduces liberties to 0.
                # But since (r, c) is added to player, we must ensure we don't count (r,c) as liberty.
                # Actually, get_group_and_liberties uses all_stones which includes (r,c) if we add it?
                # Let's refine: check liberties of opponent group on the NEW board.
                # The opponent group's liberties are effectively (current liberties - 1 if (r,c) was a liberty).
                # If (r,c) was a liberty of that group, its liberties reduce by 1.
                if is_adjacent_to_group((r,c), (nr,nc)) and (r,c) in get_liberties_of_group(group, opponent_set):
                    return True
        return False
    
    # Refined capture check using simple liberty subtraction
    def check_capture_simple(r, c, opponent_set):
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opponent_set:
                group, liberties = get_group_and_liberties((nr, nc), opponent_set)
                if (r, c) in liberties and len(liberties) == 1:
                    return True
        return False

    def get_liberties_of_group(group, player_set):
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in player_set and (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return liberties

    def is_adjacent_to_group(point, group_start):
        # Simple adjacency check
        r, c = point
        return (r-1, c) == group_start or (r+1, c) == group_start or \
               (r, c-1) == group_start or (r, c+1) == group_start

    # 1. Identify Candidate Moves
    # Only check moves adjacent to existing stones (Tenuki is rarely best for tactical bots)
    # And moves near own stones
    candidates = set()
    occupied = all_stones
    
    # Expand from existing stones
    for r, c in occupied:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in occupied and 1 <= nr <= 19 and 1 <= nc <= 19:
                candidates.add((nr, nc))

    # If board is empty, start in center or corner
    if not candidates and not occupied:
        # Start at 4-4 or 16-16
        candidates.add((4, 4))
        candidates.add((16, 16))

    if not candidates:
        return (0, 0), memory

    # Evaluate candidates
    best_moves = []
    max_score = -1000

    # Prioritize centers
    center_priority = {
        (10, 10): 10,
        (9, 9): 9, (9, 10): 9, (9, 11): 9,
        (10, 9): 9, (10, 11): 9,
        (11, 9): 9, (11, 10): 9, (11, 11): 9,
        (4, 4): 5, (4, 16): 5, (16, 4): 5, (16, 16): 5
    }

    for move in candidates:
        r, c = move
        
        # Check legality (suicide check)
        # If it's not a capture, check if my group dies
        is_cap = check_capture_simple(r, c, opp_set)
        
        # Check suicide
        is_suicide = False
        if not is_cap:
            # Temporarily add to me_set
            temp_me = me_set.union({move})
            group, liberties = get_group_and_liberties(move, temp_me)
            if len(liberties) == 0:
                is_suicide = True
        
        if is_suicide:
            continue # Illegal or bad move

        # Scoring
        score = 0
        
        # 1. Capture (Highest Value)
        if is_cap:
            score += 1000
            # Bonus for capturing larger groups (approximate by liberties count before capture)
            max_group_liberties = 0
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_set:
                    _, libs = get_group_and_liberties((nr, nc), opp_set)
                    if len(libs) > max_group_liberties:
                        max_group_liberties = len(libs)
            score += max_group_liberties * 10

        # 2. Saving my groups (increasing liberties of endangered groups)
        else:
            # Check how this move affects adjacent friendly groups
            my_group_libs_before = 0
            my_group_libs_after = 0
            
            affected_groups = set()
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in me_set:
                    g, l = get_group_and_liberties((nr, nc), me_set)
                    my_group_libs_before += len(l)
                    affected_groups.add(tuple(sorted(list(g)))) # Hashable ID for set
            
            # Calculate after adding move
            new_me = me_set.union({move})
            for g_tuple in affected_groups:
                # Recover group from tuple
                g = set(g_tuple)
                l = get_liberties_of_group(g, new_me)
                my_group_libs_after += len(l)
            
            # Also check the new group created by the move (if not connected to others)
            if not affected_groups:
                g, l = get_group_and_liberties(move, new_me)
                my_group_libs_after += len(l)
                # If isolated, let's value it slightly less unless it's a corner
                if len(l) >= 3: score += 5
                elif len(l) == 2: score += 2
            
            # Score difference
            diff = my_group_libs_after - my_group_libs_before
            if diff > 0:
                score += diff * 10

        # 3. Center / Shape Bias
        if move in center_priority:
            score += center_priority[move]
        else:
            # Encourage playing near own stones
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in me_set:
                    score += 2
                    break
            
            # Encourage playing near opponent stones (contact play)
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_set:
                    score += 1
                    break

        # 4. Randomness to break ties
        score += random.random() * 0.5

        if score > max_score:
            max_score = score
            best_moves = [move]
        elif abs(score - max_score) < 1.0:
            best_moves.append(move)

    if not best_moves:
        return (0, 0), memory

    chosen_move = random.choice(best_moves)
    return chosen_move, memory
