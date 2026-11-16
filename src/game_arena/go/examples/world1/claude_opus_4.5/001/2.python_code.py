
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                yield nr, nc
    
    def get_group_and_liberties(start, stones_set):
        group = set()
        liberties = set()
        stack = [start]
        while stack:
            pos = stack.pop()
            if pos in group:
                continue
            group.add(pos)
            for n in neighbors(*pos):
                if n in stones_set and n not in group:
                    stack.append(n)
                elif n not in occupied:
                    liberties.add(n)
        return group, liberties
    
    def would_capture(move, my_stones, opp_stones):
        captured = set()
        for n in neighbors(*move):
            if n in opp_stones:
                grp, libs = get_group_and_liberties(n, opp_stones)
                libs.discard(move)
                if len(libs) == 0:
                    captured |= grp
        return captured
    
    def is_legal(move):
        if move in occupied:
            return False
        r, c = move
        if not (1 <= r <= 19 and 1 <= c <= 19):
            return False
        
        new_me = me_set | {move}
        new_opp = opp_set - would_capture(move, new_me, opp_set)
        new_occupied_after = new_me | new_opp
        
        # Check if our new stone/group has liberties
        my_group, my_libs = set(), set()
        stack = [move]
        while stack:
            pos = stack.pop()
            if pos in my_group:
                continue
            my_group.add(pos)
            for n in neighbors(*pos):
                if n in new_me and n not in my_group:
                    stack.append(n)
                elif n not in new_occupied_after:
                    my_libs.add(n)
        return len(my_libs) > 0
    
    # Find opponent groups in atari
    for stone in opp_set:
        grp, libs = get_group_and_liberties(stone, opp_set)
        if len(libs) == 1:
            move = list(libs)[0]
            if is_legal(move):
                return move
    
    # Protect own groups in atari
    for stone in me_set:
        grp, libs = get_group_and_liberties(stone, me_set)
        if len(libs) == 1:
            escape = list(libs)[0]
            if is_legal(escape):
                return escape
    
    # Opening: star points
    star_points = [(4,4), (4,10), (4,16), (10,4), (10,10), (10,16), (16,4), (16,10), (16,16)]
    if len(me) + len(opponent) < 12:
        for sp in star_points:
            if sp not in occupied and is_legal(sp):
                return sp
    
    # Evaluate moves
    best_score = -float('inf')
    best_move = None
    
    candidates = set()
    for stone in me_set | opp_set:
        for n in neighbors(*stone):
            if n not in occupied:
                candidates.add(n)
        for n in neighbors(*stone):
            for n2 in neighbors(*n):
                if n2 not in occupied:
                    candidates.add(n2)
    
    if not candidates:
        candidates = {(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in occupied}
    
    for move in candidates:
        if not is_legal(move):
            continue
        
        score = 0
        captures = would_capture(move, me_set | {move}, opp_set)
        score += len(captures) * 10
        
        for n in neighbors(*move):
            if n in opp_set:
                grp, libs = get_group_and_liberties(n, opp_set)
                libs.discard(move)
                score += max(0, 4 - len(libs))
            if n in me_set:
                score += 2
        
        # Prefer center-ish moves
        dist_center = abs(move[0] - 10) + abs(move[1] - 10)
        score += (18 - dist_center) * 0.1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        return best_move
    
    # Fallback
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in occupied and is_legal((r, c)):
                return (r, c)
    
    return (0, 0)
