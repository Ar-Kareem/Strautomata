
N = 19
ALL_POINTS = [(r, c) for r in range(1, N + 1) for c in range(1, N + 1)]

NEIGHBORS = {}
DIAGONALS = {}
for r, c in ALL_POINTS:
    ns = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 1 <= rr <= N and 1 <= cc <= N:
            ns.append((rr, cc))
    NEIGHBORS[(r, c)] = tuple(ns)

    ds = []
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        rr, cc = r + dr, c + dc
        if 1 <= rr <= N and 1 <= cc <= N:
            ds.append((rr, cc))
    DIAGONALS[(r, c)] = tuple(ds)

STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
}

CORNER_OF_POINT = {}
CORNER_LOCAL = {}
CORNER_POINTS = [set(), set(), set(), set()]

for p in ALL_POINTS:
    r, c = p
    cid = None
    local = None
    if r <= 6 and c <= 6:
        cid = 0
        local = (r, c)
    elif r <= 6 and c >= 14:
        cid = 1
        local = (r, N + 1 - c)
    elif r >= 14 and c <= 6:
        cid = 2
        local = (N + 1 - r, c)
    elif r >= 14 and c >= 14:
        cid = 3
        local = (N + 1 - r, N + 1 - c)

    if cid is not None:
        CORNER_OF_POINT[p] = cid
        CORNER_LOCAL[p] = local
        CORNER_POINTS[cid].add(p)


def board_key(me_set, opp_set):
    return (tuple(sorted(me_set)), tuple(sorted(opp_set)))


def build_groups(stones, occupied):
    visited = set()
    groups = []
    gid_map = {}

    for s in stones:
        if s in visited:
            continue

        gid = len(groups)
        stack = [s]
        visited.add(s)
        group_stones = []
        libs = set()

        while stack:
            p = stack.pop()
            group_stones.append(p)

            for nb in NEIGHBORS[p]:
                if nb in stones:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
                elif nb not in occupied:
                    libs.add(nb)

        for p in group_stones:
            gid_map[p] = gid

        groups.append({
            "stones": tuple(group_stones),
            "libs": libs,
            "size": len(group_stones),
        })

    return groups, gid_map


def make_liberty_map(groups):
    out = {}
    for gid, g in enumerate(groups):
        for lib in g["libs"]:
            out.setdefault(lib, []).append(gid)
    return out


def try_play(move, me_set, opp_set, my_groups, my_gid, opp_groups, opp_gid, forbidden_key):
    if move in me_set or move in opp_set:
        return None

    adj_opp_gids = set()
    for nb in NEIGHBORS[move]:
        gid = opp_gid.get(nb)
        if gid is not None:
            adj_opp_gids.add(gid)

    captured = set()
    captured_gids = set()
    for gid in adj_opp_gids:
        g = opp_groups[gid]
        if len(g["libs"]) == 1 and move in g["libs"]:
            captured_gids.add(gid)
            captured.update(g["stones"])

    adj_my_gids = set()
    for nb in NEIGHBORS[move]:
        gid = my_gid.get(nb)
        if gid is not None:
            adj_my_gids.add(gid)

    own_stones = [move]
    for gid in adj_my_gids:
        own_stones.extend(my_groups[gid]["stones"])

    occupied_after = (me_set | {move}) | (opp_set - captured)

    libs = set()
    for s in own_stones:
        for nb in NEIGHBORS[s]:
            if nb not in occupied_after:
                libs.add(nb)

    if not libs:
        return None

    if forbidden_key is not None:
        if len(me_set) + 1 == len(forbidden_key[0]) and len(opp_set) - len(captured) == len(forbidden_key[1]):
            if board_key(me_set | {move}, opp_set - captured) == forbidden_key:
                return None

    return {
        "captured": captured,
        "captured_count": len(captured),
        "captured_gids": captured_gids,
        "adj_my_gids": adj_my_gids,
        "adj_opp_gids": adj_opp_gids,
        "libs": len(libs),
        "lib_set": libs,
        "own_size": len(own_stones),
    }


def eye_quality(p, me_set, opp_set):
    # Returns 0 for not an eye, 1 for eye-like, 2 for solid own eye.
    for nb in NEIGHBORS[p]:
        if nb not in me_set:
            return 0

    opp_diag = 0
    empty_diag = 0
    for d in DIAGONALS[p]:
        if d in opp_set:
            opp_diag += 1
        elif d not in me_set:
            empty_diag += 1

    if opp_diag == 0 and empty_diag == 0:
        return 2
    return 1


def local_influence(p, me_set, opp_set):
    r, c = p
    own = 0.0
    opp = 0.0

    for dr in range(-4, 5):
        rem = 4 - abs(dr)
        rr = r + dr
        if rr < 1 or rr > N:
            continue
        for dc in range(-rem, rem + 1):
            if dr == 0 and dc == 0:
                continue
            cc = c + dc
            if cc < 1 or cc > N:
                continue
            q = (rr, cc)
            dist = abs(dr) + abs(dc)
            weight = 5 - dist
            if q in me_set:
                own += weight
            elif q in opp_set:
                opp += weight

    return own, opp


def estimate_area(me_set, opp_set):
    occupied = me_set | opp_set
    visited = set()
    my_terr = 0
    opp_terr = 0

    for p in ALL_POINTS:
        if p in occupied or p in visited:
            continue

        stack = [p]
        visited.add(p)
        region_size = 0
        touches_me = False
        touches_opp = False

        while stack:
            q = stack.pop()
            region_size += 1

            for nb in NEIGHBORS[q]:
                if nb in me_set:
                    touches_me = True
                elif nb in opp_set:
                    touches_opp = True
                elif nb not in visited:
                    visited.add(nb)
                    stack.append(nb)

        if touches_me and not touches_opp:
            my_terr += region_size
        elif touches_opp and not touches_me:
            opp_terr += region_size

    return (len(me_set) + my_terr) - (len(opp_set) + opp_terr)


def positional_score(p, corner_counts, occupied_count):
    r, c = p
    stage = occupied_count / 361.0
    edge = min(r - 1, c - 1, N - r, N - c)
    score = 0.0

    if edge == 0:
        score -= 24.0 if occupied_count < 280 else 7.0
    elif edge == 1:
        score += -5.0 + 10.0 * stage
    elif edge == 2:
        score += 12.0 - 3.0 * stage
    elif edge == 3:
        score += 14.0 - 6.0 * stage
    elif edge == 4:
        score += 6.0 - 2.0 * stage
    else:
        score += 1.5

    if p in STAR_POINTS:
        score += 18.0 * (1.0 - stage)

    cid = CORNER_OF_POINT.get(p)
    if cid is not None:
        ownc, oppc = corner_counts[cid]
        total = ownc + oppc
        a, b = CORNER_LOCAL[p]

        if total == 0:
            if (a, b) == (4, 4):
                score += 50.0 * (1.0 - stage)
            elif (a, b) in ((3, 4), (4, 3)):
                score += 42.0 * (1.0 - stage)
            elif (a, b) in ((3, 3), (4, 5), (5, 4)):
                score += 25.0 * (1.0 - stage)
        elif ownc == 0 and oppc > 0 and total <= 4:
            mn, mx = min(a, b), max(a, b)
            if 3 <= mn <= 5 and 5 <= mx <= 6:
                score += 20.0 * (1.0 - stage) + 8.0
        elif ownc > 0 and oppc == 0 and occupied_count < 80:
            score -= 6.0 * (1.0 - stage)

    return score


def evaluate_move(move, data, me_set, opp_set, my_groups, opp_groups,
                  my_lib_map, opp_lib_map, corner_counts, area_diff, occupied_count):
    score = 0.0
    score += positional_score(move, corner_counts, occupied_count)

    captured_gids = data["captured_gids"]
    cap_count = data["captured_count"]
    libs = data["libs"]

    capture_bonus = 0.0
    for gid in captured_gids:
        sz = opp_groups[gid]["size"]
        capture_bonus += 170.0 + 90.0 * sz
    capture_bonus += 18.0 * cap_count
    score += capture_bonus

    save_bonus = 0.0
    for gid in my_lib_map.get(move, ()):
        g = my_groups[gid]
        l = len(g["libs"])
        sz = g["size"]

        if l == 1:
            save_bonus += 230.0 + 95.0 * sz
        elif l == 2:
            save_bonus += 42.0 + 9.0 * sz
        elif l == 3:
            save_bonus += 10.0 + 2.5 * sz

    score += save_bonus

    attack_bonus = 0.0
    for gid in opp_lib_map.get(move, ()):
        if gid in captured_gids:
            continue

        g = opp_groups[gid]
        l = len(g["libs"])
        sz = g["size"]

        if l == 2:
            attack_bonus += 85.0 + 32.0 * sz
        elif l == 3:
            attack_bonus += 18.0 + 6.0 * sz
        elif l == 4:
            attack_bonus += 5.0 + 2.0 * sz

    score += attack_bonus

    adj_my = data["adj_my_gids"]
    if adj_my:
        total_adj_size = sum(my_groups[gid]["size"] for gid in adj_my)
        score += 5.0 * len(adj_my) + 1.2 * min(total_adj_size, 22)

        if len(adj_my) >= 2:
            score += 42.0 * (len(adj_my) - 1)
            for gid in adj_my:
                glibs = len(my_groups[gid]["libs"])
                if glibs <= 3:
                    score += 18.0 * (4 - glibs)

    surviving_adj_opp = [gid for gid in data["adj_opp_gids"] if gid not in captured_gids]
    if surviving_adj_opp:
        score += 4.0 * len(surviving_adj_opp)
        if len(surviving_adj_opp) >= 2:
            score += 26.0 * (len(surviving_adj_opp) - 1)

    if libs >= 6:
        score += 20.0
    elif libs == 5:
        score += 15.0
    elif libs == 4:
        score += 10.0
    elif libs == 3:
        score += 3.0
    elif libs == 2:
        score -= 26.0
    else:
        if cap_count:
            score -= 70.0
        else:
            score -= 260.0 + 22.0 * data["own_size"]

    if libs <= 2 and cap_count == 0 and save_bonus == 0:
        score -= 35.0 * len(surviving_adj_opp)

    eq = eye_quality(move, me_set, opp_set)
    if eq and cap_count == 0:
        penalty = 360.0 if eq == 2 else 150.0
        if save_bonus > 0:
            penalty *= 0.45
        score -= penalty

    diag_own = 0
    diag_opp = 0
    for d in DIAGONALS[move]:
        if d in me_set:
            diag_own += 1
        elif d in opp_set:
            diag_opp += 1

    score += 3.0 * diag_own + 1.5 * diag_opp

    own_inf, opp_inf = local_influence(move, me_set, opp_set)
    if occupied_count > 8:
        score += 0.45 * own_inf + 0.35 * opp_inf
        if own_inf + opp_inf < 0.5:
            score -= min(30.0, occupied_count / 5.0)
    else:
        # In the very early opening, spread out instead of crowding.
        score -= 0.12 * (own_inf + opp_inf)

    if opp_inf > own_inf * 2.0 + 8.0 and libs <= 3 and cap_count == 0 and save_bonus == 0:
        invasion_penalty = 38.0
        if area_diff < -12:
            invasion_penalty *= 0.45
        score -= invasion_penalty

    if area_diff < -18 and opp_inf > own_inf:
        score += min(24.0, 0.45 * opp_inf)

    # Tiny deterministic tie-breaker.
    r, c = move
    score += ((r * 37 + c * 91 + occupied_count * 13) % 97) * 0.0001

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    me_set = {
        (int(r), int(c))
        for r, c in me
        if 1 <= int(r) <= N and 1 <= int(c) <= N
    }
    opp_set = {
        (int(r), int(c))
        for r, c in opponent
        if 1 <= int(r) <= N and 1 <= int(c) <= N
    }

    occupied = me_set | opp_set
    occupied_count = len(occupied)

    if occupied_count >= N * N:
        new_memory = {"last_after": board_key(me_set, opp_set), "turn": memory.get("turn", 0) + 1}
        return (0, 0), new_memory

    my_groups, my_gid = build_groups(me_set, occupied)
    opp_groups, opp_gid = build_groups(opp_set, occupied)

    my_lib_map = make_liberty_map(my_groups)
    opp_lib_map = make_liberty_map(opp_groups)

    forbidden_key = memory.get("last_after")
    current_key = board_key(me_set, opp_set)
    opponent_passed = (forbidden_key == current_key)

    corner_counts = []
    for pts in CORNER_POINTS:
        ownc = sum(1 for p in pts if p in me_set)
        oppc = sum(1 for p in pts if p in opp_set)
        corner_counts.append((ownc, oppc))

    area_diff = estimate_area(me_set, opp_set)

    best_move = None
    best_data = None
    best_score = -10**18

    for move in ALL_POINTS:
        if move in occupied:
            continue

        data = try_play(move, me_set, opp_set, my_groups, my_gid, opp_groups, opp_gid, forbidden_key)
        if data is None:
            continue

        score = evaluate_move(
            move, data, me_set, opp_set, my_groups, opp_groups,
            my_lib_map, opp_lib_map, corner_counts, area_diff, occupied_count
        )

        if score > best_score:
            best_score = score
            best_move = move
            best_data = data

    if best_move is None:
        new_memory = {"last_after": current_key, "turn": memory.get("turn", 0) + 1}
        return (0, 0), new_memory

    pass_threshold = -90.0
    if occupied_count > 300:
        pass_threshold = -10.0
    if opponent_passed:
        pass_threshold = 12.0 if area_diff >= -5 else -30.0

    if best_score < pass_threshold:
        new_memory = {"last_after": current_key, "turn": memory.get("turn", 0) + 1}
        return (0, 0), new_memory

    new_me = me_set | {best_move}
    new_opp = opp_set - best_data["captured"]
    new_memory = {
        "last_after": board_key(new_me, new_opp),
        "turn": memory.get("turn", 0) + 1,
    }

    return best_move, new_memory
