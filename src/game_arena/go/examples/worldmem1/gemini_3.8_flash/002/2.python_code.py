
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import collections

    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    # 1. Neighbor helper
    def get_neighbors(r, c):
        res = []
        if r > 1: res.append((r - 1, c))
        if r < BOARD_SIZE: res.append((r + 1, c))
        if c > 1: res.append((r, c - 1))
        if c < BOARD_SIZE: res.append((r, c + 1))
        return res

    # 2. Find groups and liberties
    def find_groups(stones_set):
        visited = set()
        groups = []  # list of (set_of_stones, set_of_liberties)
        for stone in stones_set:
            if stone in visited:
                continue
            group = set()
            liberties = set()
            queue = collections.deque([stone])
            visited.add(stone)
            while queue:
                curr = queue.popleft()
                group.add(curr)
                for nbr in get_neighbors(curr[0], curr[1]):
                    if nbr in stones_set:
                        if nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)
                    elif nbr not in occupied:
                        liberties.add(nbr)
            groups.append((group, liberties))
        return groups

    my_groups = find_groups(me_set)
    opp_groups = find_groups(opp_set)

    # 3. Ko point from memory
    ko_point = memory.get('ko_point', None)

    # 4. Legality and simulation test
    def is_legal(move, is_me=True):
        r, c = move
        if not (1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE):
            return False, 0
        if move in occupied:
            return False, 0
        if move == ko_point:
            return False, 0

        my_s = me_set if is_me else opp_set
        opp_s = opp_set if is_me else me_set

        # Check if any neighbor is empty
        nbrs = get_neighbors(r, c)
        empty_nbrs = [n for n in nbrs if n not in occupied]
        
        # Check captures
        captured_stones = 0
        for og, olibs in (opp_groups if is_me else my_groups):
            if len(olibs) == 1 and move in olibs:
                captured_stones += len(og)

        if empty_nbrs or captured_stones > 0:
            return True, captured_stones

        # If no empty neighbor and no captures, check if connecting to a group with >1 liberty
        for mg, mlibs in (my_groups if is_me else opp_groups):
            if any(n in mg for n in nbrs):
                if len(mlibs) > 1:
                    return True, 0

        return False, 0

    # 5. Tactical detection
    # A. Capture opponent in atari
    captures = []
    for og, olibs in opp_groups:
        if len(olibs) == 1:
            pt = next(iter(olibs))
            legal, count = is_legal(pt, is_me=True)
            if legal:
                captures.append((pt, len(og)))

    if captures:
        captures.sort(key=lambda x: x[1], reverse=True)
        # Return best capture
        best_pt = captures[0][0]
        new_memory = {'ko_point': best_pt if captures[0][1] == 1 else None}
        return best_pt, new_memory

    # B. Save friendly group in atari
    saves = []
    for mg, mlibs in my_groups:
        if len(mlibs) == 1:
            pt = next(iter(mlibs))
            legal, count = is_legal(pt, is_me=True)
            if legal:
                # Check if moving here gives more than 1 liberty (not self-atari)
                nbrs = get_neighbors(pt[0], pt[1])
                free_nbrs = sum(1 for n in nbrs if n not in occupied and n != pt)
                if free_nbrs > 0 or count > 0:
                    saves.append((pt, len(mg) + count))

    if saves:
        saves.sort(key=lambda x: x[1], reverse=True)
        return saves[0][0], {'ko_point': None}

    # 6. Opening book moves
    star_points = [
        (4, 4), (4, 16), (16, 4), (16, 16),
        (4, 10), (16, 10), (10, 4), (10, 16),
        (3, 4), (4, 3), (16, 3), (17, 4),
        (3, 16), (4, 17), (16, 17), (17, 16),
        (10, 10)
    ]
    if len(occupied) < 12:
        for sp in star_points:
            if sp not in occupied:
                legal, _ = is_legal(sp, is_me=True)
                if legal:
                    return sp, {'ko_point': None}

    # 7. Candidate evaluation
    candidate_moves = set()

    # Generate moves near existing stones
    if occupied:
        for r, c in occupied:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and (nr, nc) not in occupied:
                        candidate_moves.add((nr, nc))
    else:
        return (10, 10), {'ko_point': None}

    best_move = None
    best_score = -float('inf')

    for move in candidate_moves:
        legal, caps = is_legal(move, is_me=True)
        if not legal:
            continue

        r, c = move
        nbrs = get_neighbors(r, c)

        # Immediate self-atari avoidance
        free_nbrs = [n for n in nbrs if n not in occupied]
        adjacent_my_groups = [g for g, libs in my_groups if any(n in g for n in nbrs)]
        total_libs_rough = len(free_nbrs)
        for g in adjacent_my_groups:
            total_libs_rough += len([lib for lib in g if lib not in occupied and lib != move])
        if total_libs_rough <= 1 and caps == 0:
            continue  # avoid suicide-like self atari

        # Score components
        score = 0.0

        # Edge distance preference: line 3 and 4 are ideal
        dist_r = min(r, BOARD_SIZE - r + 1)
        dist_c = min(c, BOARD_SIZE - c + 1)
        line = min(dist_r, dist_c)

        if line == 3:
            score += 18.0
        elif line == 4:
            score += 20.0
        elif line == 2:
            score += 4.0
        elif line == 1:
            score -= 10.0
        else:
            score += 12.0

        # Connectivity / Attack
        for n in nbrs:
            if n in me_set:
                score += 12.0
            elif n in opp_set:
                score += 8.0

        # Hane / diagonal influence
        diagonals = [(r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)]
        for dr, dc in diagonals:
            if 1 <= dr <= BOARD_SIZE and 1 <= dc <= BOARD_SIZE:
                if (dr, dc) in me_set:
                    score += 6.0
                elif (dr, dc) in opp_set:
                    score += 5.0

        # Captures
        score += caps * 35.0

        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        return best_move, {'ko_point': None}

    # 8. Fallback to any legal move
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            move = (r, c)
            legal, _ = is_legal(move, is_me=True)
            if legal:
                return move, {'ko_point': None}

    # Pass if completely no legal move
    return (0, 0), {}
