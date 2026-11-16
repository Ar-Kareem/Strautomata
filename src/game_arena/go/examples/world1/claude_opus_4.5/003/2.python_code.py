
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                yield nr, nc
    
    def get_group_and_liberties(r, c, stones_set):
        group = set()
        liberties = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in stones_set and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in occupied:
                    liberties.add((nr, nc))
        return group, liberties
    
    def would_capture(r, c, my_stones, opp_stones):
        captures = []
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_stones:
                new_occ = occupied | {(r, c)}
                group, libs = set(), set()
                stack = [(nr, nc)]
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in group:
                        continue
                    group.add((cr, cc))
                    for nnr, nnc in neighbors(cr, cc):
                        if (nnr, nnc) in opp_stones and (nnr, nnc) not in group:
                            stack.append((nnr, nnc))
                        elif (nnr, nnc) not in new_occ:
                            libs.add((nnr, nnc))
                if len(libs) == 0:
                    captures.extend(group)
        return captures
    
    def is_legal(r, c):
        if (r, c) in occupied:
            return False
        caps = would_capture(r, c, me_set, opp_set)
        if caps:
            return True
        new_occ = occupied | {(r, c)}
        new_me = me_set | {(r, c)}
        group, libs = set(), set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in new_me and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in new_occ:
                    libs.add((nr, nc))
        return len(libs) > 0
    
    # Check for captures
    for r, c in opp_set:
        grp, libs = get_group_and_liberties(r, c, opp_set)
        if len(libs) == 1:
            lib = list(libs)[0]
            if is_legal(*lib):
                return lib
    
    # Save own groups in atari
    for r, c in me_set:
        grp, libs = get_group_and_liberties(r, c, me_set)
        if len(libs) == 1:
            lib = list(libs)[0]
            for nr, nc in neighbors(*lib):
                if (nr, nc) not in occupied and is_legal(nr, nc):
                    return (nr, nc)
    
    # Opening moves
    star_points = [(4,4), (4,10), (4,16), (10,4), (10,10), (10,16), (16,4), (16,10), (16,16)]
    if len(me) < 5:
        for pt in star_points:
            if pt not in occupied and is_legal(*pt):
                return pt
    
    # Score-based move selection
    best_move, best_score = None, -float('inf')
    candidates = set()
    for r, c in me_set | opp_set:
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in occupied:
                    candidates.add((nr, nc))
    
    if not candidates:
        candidates = {(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in occupied}
    
    for r, c in candidates:
        if not is_legal(r, c):
            continue
        score = 0
        caps = would_capture(r, c, me_set, opp_set)
        score += len(caps) * 10
        
        my_neighbors = sum(1 for nr, nc in neighbors(r, c) if (nr, nc) in me_set)
        opp_neighbors = sum(1 for nr, nc in neighbors(r, c) if (nr, nc) in opp_set)
        score += my_neighbors * 2 + opp_neighbors * 1.5
        
        edge_dist = min(r - 1, 19 - r, c - 1, 19 - c)
        if edge_dist <= 4:
            score += (5 - edge_dist) * 0.5
        
        if (r, c) in [(4,4), (4,10), (4,16), (10,4), (10,10), (10,16), (16,4), (16,10), (16,16)]:
            score += 3
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        return best_move
    
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal(r, c):
                return (r, c)
    
    return (0, 0)
