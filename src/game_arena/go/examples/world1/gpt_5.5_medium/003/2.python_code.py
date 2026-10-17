
BOARD_SIZE = 19

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

_STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
}

_CORNER_STARS = ((4, 4), (4, 16), (16, 4), (16, 16))


def _in_bounds(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def _neighbors(p):
    r, c = p
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            yield (nr, nc)


def _build_groups(me_set, opp_set):
    occupied = me_set | opp_set
    visited = set()
    groups = []
    stone_group = {}

    for color, stones in ((1, me_set), (-1, opp_set)):
        for start in stones:
            if start in visited:
                continue

            stack = [start]
            visited.add(start)
            group_stones = set()
            libs = set()

            while stack:
                s = stack.pop()
                group_stones.add(s)

                for nb in _neighbors(s):
                    if nb in stones and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
                    elif nb not in occupied:
                        libs.add(nb)

            gid = len(groups)
            groups.append({
                "color": color,
                "stones": group_stones,
                "libs": libs,
            })
            for s in group_stones:
                stone_group[s] = gid

    return groups, stone_group


def _legal(move, me_set, opp_set, occupied, groups, stone_group):
    if move == (0, 0):
        return True

    r, c = move
    if not _in_bounds(r, c) or move in occupied:
        return False

    # Capturing any adjacent opponent group is legal.
    seen_opp = set()
    for nb in _neighbors(move):
        if nb in opp_set:
            gid = stone_group[nb]
            if gid not in seen_opp:
                seen_opp.add(gid)
                libs = groups[gid]["libs"]
                if len(libs) == 1 and move in libs:
                    return True

    # Otherwise the move must have an immediate liberty or connect to
    # a friendly group with another liberty.
    for nb in _neighbors(move):
        if nb not in occupied:
            return True

    seen_own = set()
    for nb in _neighbors(move):
        if nb in me_set:
            gid = stone_group[nb]
            if gid not in seen_own:
                seen_own.add(gid)
                if len(groups[gid]["libs"] - {move}) > 0:
                    return True

    return False


def _after_info(move, me_set, opp_set, occupied, groups, stone_group):
    adj_own = set()
    adj_opp = set()

    for nb in _neighbors(move):
        if nb in me_set:
            adj_own.add(stone_group[nb])
        elif nb in opp_set:
            adj_opp.add(stone_group[nb])

    cap_gids = []
    captured_stones = set()
    for gid in adj_opp:
        libs = groups[gid]["libs"]
        if len(libs) == 1 and move in libs:
            cap_gids.append(gid)
            captured_stones.update(groups[gid]["stones"])

    new_group = {move}
    for gid in adj_own:
        new_group.update(groups[gid]["stones"])

    new_libs = set()
    for s in new_group:
        for nb in _neighbors(s):
            if nb in captured_stones:
                new_libs.add(nb)
            elif nb != move and nb not in occupied:
                new_libs.add(nb)

    captured_sizes = [len(groups[gid]["stones"]) for gid in cap_gids]
    return len(new_libs), sum(captured_sizes), captured_sizes, adj_own, adj_opp


def _is_eye(move, stone_set):
    # Conservative eye detector: all orthogonal points are own stones or edge.
    r, c = move
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and (nr, nc) not in stone_set:
            return False

    bad_diags = 0
    off_board_diags = 0
    for dr, dc in _DIAGS:
        nr, nc = r + dr, c + dc
        if not _in_bounds(nr, nc):
            off_board_diags += 1
        elif (nr, nc) not in stone_set:
            bad_diags += 1

    if off_board_diags >= 2:
        return bad_diags == 0
    return bad_diags <= 1


def _static_position_score(move, total_stones):
    r, c = move
    edge_dist = min(r - 1, c - 1, BOARD_SIZE - r, BOARD_SIZE - c)

    if total_stones < 120:
        table = [-120, -45, 40, 55, 25, 12, 5, 0]
    else:
        table = [-40, 5, 25, 20, 10, 5, 0, 0]

    score = table[edge_dist] if edge_dist < len(table) else 0

    if move in _STAR_POINTS:
        score += 230 if total_stones < 50 else 55

    # Prefer normal corner-opening zones early.
    if total_stones < 80:
        best_corner_dist = min((r - sr) * (r - sr) + (c - sc) * (c - sc)
                               for sr, sc in _CORNER_STARS)
        if best_corner_dist <= 2:
            score += 70
        elif best_corner_dist <= 8:
            score += 35

    return score


def _evaluate(move, me, opponent, me_set, opp_set, occupied, groups, stone_group):
    total_stones = len(occupied)
    r, c = move

    libs_after, captured_count, captured_sizes, adj_own, adj_opp = _after_info(
        move, me_set, opp_set, occupied, groups, stone_group
    )

    score = 0.0
    score += _static_position_score(move, total_stones)

    # Captures are valuable, especially large captures.
    if captured_count:
        score += 1200 * captured_count
        score += 200 * sum(s * s for s in captured_sizes)

    # Save own groups in atari.
    saved_size = 0
    saved_groups = 0
    for gid in adj_own:
        g = groups[gid]
        if len(g["libs"]) == 1 and move in g["libs"]:
            saved_size += len(g["stones"])
            saved_groups += 1

    if saved_size:
        score += 1300 * saved_size + 250 * saved_groups

    # Avoid ko-like or snapback-like one-stone captures unless they also save a lot.
    if captured_count == 1 and libs_after == 1 and saved_size == 0:
        score -= 4000

    # Self-atari and liberty quality.
    if libs_after <= 1:
        score -= 2500 if captured_count == 0 else 700
    elif libs_after == 2:
        score -= 120
    else:
        score += min(libs_after, 8) * 35

    # Connecting friendly groups.
    if len(adj_own) >= 2:
        connected_size = sum(min(len(groups[gid]["stones"]), 5) for gid in adj_own)
        score += 180 * (len(adj_own) - 1) + 40 * connected_size

    for gid in adj_own:
        old_libs = len(groups[gid]["libs"])
        size = len(groups[gid]["stones"])
        if old_libs == 2 and move in groups[gid]["libs"]:
            score += 450 + 80 * size
        elif old_libs == 3 and move in groups[gid]["libs"]:
            score += 120 + 20 * size

    # Attack adjacent opponent groups by reducing liberties.
    for gid in adj_opp:
        g = groups[gid]
        old_libs = len(g["libs"])
        size = len(g["stones"])
        if move in g["libs"]:
            if old_libs == 2:
                score += 700 + 120 * size
            elif old_libs == 3:
                score += 180 + 30 * size
            elif old_libs == 4:
                score += 50 + 10 * size

    # Cutting potential.
    if len(adj_opp) >= 2 and libs_after >= 3:
        score += 170 * (len(adj_opp) - 1)

    adj_friend_count = 0
    adj_enemy_count = 0
    diag_friend_count = 0

    for nb in _neighbors(move):
        if nb in me_set:
            adj_friend_count += 1
        elif nb in opp_set:
            adj_enemy_count += 1

    for dr, dc in _DIAGS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and (nr, nc) in me_set:
            diag_friend_count += 1

    score += 25 * adj_friend_count + 10 * diag_friend_count

    if adj_enemy_count and adj_friend_count == 0 and captured_count == 0 and libs_after < 4:
        score -= 250

    # Do not fill solid own eyes unless tactically necessary.
    if captured_count == 0 and saved_size == 0 and _is_eye(move, me_set):
        score -= 8000

    # Playing inside a solid opponent eye is usually bad unless capturing.
    if captured_count == 0 and _is_eye(move, opp_set):
        score -= 1200

    # Local influence and spacing.
    friendly_influence = 0
    enemy_influence = 0

    for sr, sc in me:
        d = abs(r - sr) + abs(c - sc)
        if d <= 6:
            friendly_influence += 7 - d

    for sr, sc in opponent:
        d = abs(r - sr) + abs(c - sc)
        if d <= 6:
            enemy_influence += 7 - d

    score += 5 * friendly_influence + 2 * enemy_influence

    if enemy_influence > friendly_influence + 8 and adj_friend_count == 0 and captured_count == 0:
        score -= 4 * (enemy_influence - friendly_influence)

    if friendly_influence > 20 and enemy_influence == 0:
        score -= 2 * (friendly_influence - 20)

    # Opening: prefer well-spaced development rather than immediate contact.
    if total_stones < 50 and occupied:
        nearest = min(abs(r - sr) + abs(c - sc) for sr, sc in occupied)
        if nearest >= 4:
            score += min(70, 8 * nearest)
        elif nearest <= 1 and captured_count == 0 and saved_size == 0:
            score -= 180
        elif nearest == 2 and captured_count == 0 and saved_size == 0:
            score -= 80

    # Tiny deterministic tie breaker.
    score += ((r * 37 + c * 17) % 19) * 0.001

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    groups, stone_group = _build_groups(me_set, opp_set)

    best_move = None
    best_score = -10**18

    # Evaluate every legal board move. 361 points is small enough for 1 second.
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            move = (r, c)
            if move in occupied:
                continue
            if not _legal(move, me_set, opp_set, occupied, groups, stone_group):
                continue

            score = _evaluate(move, me, opponent, me_set, opp_set, occupied, groups, stone_group)

            if score > best_score:
                best_score = score
                best_move = move

    if best_move is None:
        return (0, 0)

    # If every remaining legal move is just filling our own eyes, pass.
    if best_score < -6000:
        return (0, 0)

    return best_move
