
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    size = 19
    my = set(me)
    opp = set(opponent)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def group_and_libs(board, stone, other):
        """Return (group_set, liberty_set) for the connected group containing stone."""
        if stone not in board:
            return (set(), set())
        group = set()
        libs = set()
        stack = [stone]
        seen = {stone}
        while stack:
            r, c = stack.pop()
            group.add((r, c))
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= size and 1 <= nc <= size:
                    npos = (nr, nc)
                    if npos in board and npos not in seen:
                        seen.add(npos)
                        stack.append(npos)
                    elif npos not in board and npos not in other:
                        libs.add(npos)
        return (group, libs)
    
    def is_legal(move):
        """Check if placing a stone at move is legal (not suicide)."""
        r, c = move
        if move in my or move in opp:
            return False
        
        new_my = my | {move}
        captures = False
        
        # Check if this move captures any opponent groups
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp:
                _, opp_libs = group_and_libs(opp, (nr, nc), new_my)
                if len(opp_libs) == 0:
                    captures = True
                    break
        
        if captures:
            return True
        
        # Check if the new stone has liberties (not suicide)
        _, new_libs = group_and_libs(new_my, move, opp)
        return len(new_libs) > 0
    
    # ----- Tactical Phase: Captures and Defense -----
    captures = []  # (size, move)
    defenses = []  # (size, move)
    
    # Find opponent groups in atari (capturable)
    seen_opp = set()
    for stone in opp:
        if stone in seen_opp:
            continue
        grp, libs = group_and_libs(opp, stone, my)
        seen_opp.update(grp)
        if len(libs) == 1:
            move = next(iter(libs))
            if move not in my and move not in opp and is_legal(move):
                captures.append((len(grp), move))
    
    # Find own groups in atari (need saving)
    seen_my = set()
    for stone in my:
        if stone in seen_my:
            continue
        grp, libs = group_and_libs(my, stone, opp)
        seen_my.update(grp)
        if len(libs) == 1:
            move = next(iter(libs))
            if move not in my and move not in opp and is_legal(move):
                defenses.append((len(grp), move))
    
    # Prioritize: capture if bigger or equal, else defend
    captures.sort(reverse=True)
    defenses.sort(reverse=True)
    
    if captures and defenses:
        if captures[0][0] >= defenses[0][0]:
            return captures[0][1]
        return defenses[0][1]
    if captures:
        return captures[0][1]
    if defenses:
        return defenses[0][1]
    
    # ----- Positional Phase: Heuristic Search -----
    # Generate candidates near existing stones, or all empty if sparse
    candidates = set()
    for r, c in list(my) + list(opp):
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= size and 1 <= nc <= size:
                if (nr, nc) not in my and (nr, nc) not in opp:
                    candidates.add((nr, nc))
    
    empty = [(r, c) for r in range(1, size+1) for c in range(1, size+1) 
             if (r, c) not in my and (r, c) not in opp]
    
    if not candidates:
        candidates = set(empty)
    
    best_move = None
    best_score = -float('inf')
    import random
    random.seed(hash(tuple(my)) % 10000)  # Deterministic based on position
    
    for move in candidates:
        if not is_legal(move):
            continue
        r, c = move
        score = random.random() * 0.1  # Tie-breaker
        
        # Line preference: 3rd line (edge_dist=2) and 4th line (edge_dist=3) are best
        edge_dist = min(r-1, size-r, c-1, size-c)
        if edge_dist == 0:
            score -= 100  # 1st line
        elif edge_dist == 1:
            score -= 20   # 2nd line
        elif edge_dist == 2:
            score += 15   # 3rd line (star point area)
        elif edge_dist == 3:
            score += 10   # 4th line
        else:
            score += 5    # Center
        
        # Connection bonus
        for dr, dc in dirs:
            if (r+dr, c+dc) in my:
                score += 3
        
        # Attack bonus (adjacent to opponent)
        for dr, dc in dirs:
            if (r+dr, c+dc) in opp:
                score += 2
        
        # Slight center bias for influence
        score -= 0.05 * (abs(r - 10) + abs(c - 10))
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        return best_move
    
    # Last resort: any legal move
    for move in empty:
        if is_legal(move):
            return move
            
    return (0, 0)
