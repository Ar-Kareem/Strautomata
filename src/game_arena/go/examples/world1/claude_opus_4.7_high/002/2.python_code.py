
def policy(me, opponent):
    N = 19
    board = {}
    for r, c in me:
        board[(r, c)] = 1
    for r, c in opponent:
        board[(r, c)] = 2

    def neighbors(r, c):
        out = []
        if r > 1: out.append((r-1, c))
        if r < 19: out.append((r+1, c))
        if c > 1: out.append((r, c-1))
        if c < 19: out.append((r, c+1))
        return out

    def get_group(bd, r, c):
        color = bd.get((r, c))
        if color is None:
            return set(), set()
        group = set()
        libs = set()
        stack = [(r, c)]
        while stack:
            p = stack.pop()
            if p in group:
                continue
            group.add(p)
            for n in neighbors(*p):
                v = bd.get(n)
                if v is None:
                    libs.add(n)
                elif v == color and n not in group:
                    stack.append(n)
        return group, libs

    def simulate(bd, move, color):
        r, c = move
        if (r, c) in bd:
            return None
        new_bd = dict(bd)
        new_bd[(r, c)] = color
        opp = 3 - color
        captured = set()
        for n in neighbors(r, c):
            if new_bd.get(n) == opp:
                g, libs = get_group(new_bd, *n)
                if not libs:
                    captured |= g
        for p in captured:
            del new_bd[p]
        g, libs = get_group(new_bd, r, c)
        if not libs:
            return None
        return new_bd, len(captured)

    def is_eye(bd, r, c, color):
        if (r, c) in bd:
            return False
        for n in neighbors(r, c):
            if bd.get(n) != color:
                return False
        friendly_diag = 0
        enemy_diag = 0
        total_diag = 0
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                total_diag += 1
                v = bd.get((nr, nc))
                if v == color:
                    friendly_diag += 1
                elif v == 3 - color:
                    enemy_diag += 1
        if total_diag < 4:
            return enemy_diag == 0
        return enemy_diag <= 1

    all_stones = list(me) + list(opponent)

    # Opening
    if len(all_stones) == 0:
        return (16, 4)
    if len(me) == 0 and len(opponent) <= 2:
        for sp in [(4, 16), (16, 4), (4, 4), (16, 16), (10, 10)]:
            if sp not in board:
                return sp

    candidates = set()
    for r, c in all_stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r+dr, c+dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in board:
                    candidates.add((nr, nc))

    if len(all_stones) < 12:
        for sp in [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]:
            if sp not in board:
                candidates.add(sp)

    best_score = -float('inf')
    best_move = (0, 0)
    fallback = None

    # Pre-compute my groups in atari
    my_atari_groups = []
    visited = set()
    for stone in me:
        if stone in visited:
            continue
        g, libs = get_group(board, *stone)
        visited |= g
        if len(libs) == 1:
            my_atari_groups.append((g, next(iter(libs))))

    for move in candidates:
        r, c = move
        if is_eye(board, r, c, 1):
            continue
        result = simulate(board, move, 1)
        if result is None:
            continue
        new_bd, captures = result
        if fallback is None:
            fallback = move

        score = 0.0
        score += captures * 150

        _, my_libs_set = get_group(new_bd, r, c)
        my_libs = len(my_libs_set)
        if my_libs == 1:
            score -= 80
        elif my_libs == 2:
            score += 4
        else:
            score += min(my_libs, 6) * 3

        # Adjacent opponent pressure
        checked_opp = set()
        for n in neighbors(r, c):
            if new_bd.get(n) == 2 and n not in checked_opp:
                g, libs = get_group(new_bd, *n)
                checked_opp |= g
                ol = len(libs)
                if ol == 1:
                    score += 40 + len(g) * 5
                elif ol == 2:
                    score += 12

        # Connection / saving
        for g, lib in my_atari_groups:
            if (r, c) == lib:
                score += 60 + len(g) * 3

        # Adjacent friendly
        friendly_adj = 0
        for n in neighbors(r, c):
            if board.get(n) == 1:
                friendly_adj += 1
        score += friendly_adj * 2

        # Positional
        dist_edge = min(r-1, 19-r, c-1, 19-c)
        if dist_edge == 2 or dist_edge == 3:
            score += 4
        elif dist_edge == 0:
            score -= 8
        elif dist_edge == 1:
            score -= 3

        # Don't play too close if opening
        if len(all_stones) < 15:
            min_dist = min(abs(r-sr) + abs(c-sc) for sr, sc in all_stones)
            if min_dist >= 3:
                score += 2

        if score > best_score:
            best_score = score
            best_move = move

    if best_score == -float('inf'):
        if fallback is not None:
            return fallback
        # Try any legal move
        for r in range(1, 20):
            for c in range(1, 20):
                if (r, c) in board:
                    continue
                if is_eye(board, r, c, 1):
                    continue
                if simulate(board, (r, c), 1) is not None:
                    return (r, c)
        return (0, 0)

    return best_move
