
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import random
    
    SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                yield nr, nc
    
    def get_group_and_liberties(r, c, player_set):
        group = set()
        liberties = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if (nr, nc) in player_set and (nr, nc) not in group:
                    stack.append((nr, nc))
                elif (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return group, liberties
    
    def is_legal(r, c, my_set, opp_s):
        if (r, c) in all_stones:
            return False
        temp_all = all_stones | {(r, c)}
        temp_my = my_set | {(r, c)}
        
        # Check if captures opponent
        captures = False
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_s:
                grp, libs = get_group_and_liberties(nr, nc, opp_s)
                libs.discard((r, c))
                if len(libs) == 0:
                    captures = True
        
        # Check own liberties
        _, my_libs = get_group_and_liberties(r, c, temp_my)
        if len(my_libs) == 0 and not captures:
            return False
        return True
    
    def score_move(r, c):
        score = 0.0
        # Star points and strategic positions
        star_points = [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]
        if (r, c) in star_points:
            score += 15
        
        # Prefer 3rd/4th line in opening
        for coord in [r, c]:
            if coord in [3, 4, 16, 17]:
                score += 5
        
        # Proximity to own stones (extensions)
        for mr, mc in me_set:
            dist = abs(r - mr) + abs(c - mc)
            if 2 <= dist <= 4:
                score += 8
            elif dist == 1:
                score += 3
        
        # Attack opponent (close to opponent stones)
        for opr, opc in opp_set:
            dist = abs(r - opr) + abs(c - opc)
            if dist <= 2:
                score += 6
        
        # Check for captures
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                grp, libs = get_group_and_liberties(nr, nc, opp_set)
                libs.discard((r, c))
                if len(libs) == 0:
                    score += 50 + len(grp) * 10
                elif len(libs) == 1:
                    score += 20
        
        # Add small randomness
        score += random.random() * 2
        return score
    
    # Generate candidate moves
    candidates = []
    if len(all_stones) < 20:
        # Opening: focus on strategic points
        priority = [(4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10),
                    (3, 4), (4, 3), (3, 16), (4, 17), (16, 3), (17, 4), (16, 17), (17, 16)]
        for pos in priority:
            if pos not in all_stones and is_legal(pos[0], pos[1], me_set, opp_set):
                candidates.append(pos)
    
    # Add moves near existing stones
    for sr, sc in list(me_set) + list(opp_set):
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = sr + dr, sc + dc
                if 1 <= nr <= SIZE and 1 <= nc <= SIZE:
                    if (nr, nc) not in all_stones and is_legal(nr, nc, me_set, opp_set):
                        candidates.append((nr, nc))
    
    # If no candidates, try all empty points
    if not candidates:
        for r in range(1, SIZE + 1):
            for c in range(1, SIZE + 1):
                if (r, c) not in all_stones and is_legal(r, c, me_set, opp_set):
                    candidates.append((r, c))
    
    # Remove duplicates
    candidates = list(set(candidates))
    
    if not candidates:
        return ((0, 0), memory)
    
    # Score and select best move
    best_move = None
    best_score = -float('inf')
    for move in candidates:
        s = score_move(move[0], move[1])
        if s > best_score:
            best_score = s
            best_move = move
    
    if best_move is None:
        best_move = (0, 0)
    
    return (best_move, memory)
