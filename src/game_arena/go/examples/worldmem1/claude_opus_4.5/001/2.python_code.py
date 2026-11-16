
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                yield nr, nc
    
    def get_group(r, c, stones_set):
        group = set()
        stack = [(r, c)]
        while stack:
            pos = stack.pop()
            if pos in group:
                continue
            if pos in stones_set:
                group.add(pos)
                for n in neighbors(*pos):
                    if n not in group and n in stones_set:
                        stack.append(n)
        return group
    
    def get_liberties(group, my_stones, opp_stones):
        libs = set()
        for r, c in group:
            for n in neighbors(r, c):
                if n not in my_stones and n not in opp_stones:
                    libs.add(n)
        return libs
    
    def would_capture(r, c, my_stones, opp_stones):
        new_my = my_stones | {(r, c)}
        for n in neighbors(r, c):
            if n in opp_stones:
                opp_group = get_group(*n, opp_stones)
                libs = get_liberties(opp_group, new_my, opp_stones)
                if len(libs) == 0:
                    return True
        return False
    
    def is_legal(r, c):
        if (r, c) in occupied:
            return False
        new_me = me_set | {(r, c)}
        # Check if we capture something
        if would_capture(r, c, new_me, opp_set):
            return True
        # Check if our new stone/group has liberties
        my_group = get_group(r, c, new_me)
        libs = get_liberties(my_group, new_me, opp_set)
        return len(libs) > 0
    
    def score_move(r, c):
        score = 0
        # Capture opponent stones
        if would_capture(r, c, me_set | {(r, c)}, opp_set):
            score += 1000
        # Proximity to own stones
        for mr, mc in me:
            dist = abs(r - mr) + abs(c - mc)
            if dist <= 3:
                score += (4 - dist) * 10
        # Territory value (corners and sides)
        edge_dist = min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
        if edge_dist <= 4:
            score += (5 - edge_dist) * 5
        # Star points bonus
        star_points = [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]
        if (r, c) in star_points:
            score += 30
        # Avoid self-atari
        new_me = me_set | {(r, c)}
        my_group = get_group(r, c, new_me)
        libs = get_liberties(my_group, new_me, opp_set)
        if len(libs) == 1:
            score -= 500
        return score
    
    legal_moves = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) if is_legal(r, c)]
    
    if not legal_moves:
        return ((0, 0), memory)
    
    best_move = max(legal_moves, key=lambda m: score_move(*m))
    return (best_move, memory)
