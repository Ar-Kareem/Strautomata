
from collections import deque


SIZE = 19
AREA = SIZE * SIZE

NEIGHBORS = []
DIAGONALS = []
for r in range(SIZE):
    for c in range(SIZE):
        ns = []
        ds = []
        if r > 0:
            ns.append((r - 1) * SIZE + c)
        if r + 1 < SIZE:
            ns.append((r + 1) * SIZE + c)
        if c > 0:
            ns.append(r * SIZE + c - 1)
        if c + 1 < SIZE:
            ns.append(r * SIZE + c + 1)

        if r > 0 and c > 0:
            ds.append((r - 1) * SIZE + c - 1)
        if r > 0 and c + 1 < SIZE:
            ds.append((r - 1) * SIZE + c + 1)
        if r + 1 < SIZE and c > 0:
            ds.append((r + 1) * SIZE + c - 1)
        if r + 1 < SIZE and c + 1 < SIZE:
            ds.append((r + 1) * SIZE + c + 1)

        NEIGHBORS.append(tuple(ns))
        DIAGONALS.append(tuple(ds))


def board_key(board):
    # Values -1, 0, 1 become bytes 0, 1, 2.
    return bytes(v + 1 for v in board)


def analyze(board):
    """Return group id per point and [color, stones, liberties] records."""
    gids = [-1] * AREA
    groups = []

    for start in range(AREA):
        color = board[start]
        if color == 0 or gids[start] != -1:
            continue

        gid = len(groups)
        stack = [start]
        gids[start] = gid
        stones = []
        liberties = set()

        while stack:
            q = stack.pop()
            stones.append(q)
            for n in NEIGHBORS[q]:
                value = board[n]
                if value == 0:
                    liberties.add(n)
                elif value == color and gids[n] == -1:
                    gids[n] = gid
                    stack.append(n)

        groups.append((color, tuple(stones), liberties))

    return gids, groups


def simulate(board, point, color, gids=None, groups=None, forbidden=None):
    """
    Play color at point.

    Returns:
      (new_board, captured_stones, liberties_of_played_group,
       stones_of_played_group, new_key)
    or None if occupied, suicide, or repetition.
    """
    if point < 0 or point >= AREA or board[point] != 0:
        return None

    if gids is None or groups is None:
        gids, groups = analyze(board)

    result = board[:]
    result[point] = color

    captured = []
    handled = set()
    for n in NEIGHBORS[point]:
        if board[n] == -color:
            gid = gids[n]
            if gid in handled:
                continue
            handled.add(gid)
            group = groups[gid]
            if len(group[2]) == 1 and point in group[2]:
                captured.extend(group[1])

    for q in captured:
        result[q] = 0

    stack = [point]
    seen = {point}
    own_stones = []
    liberties = set()

    while stack:
        q = stack.pop()
        own_stones.append(q)
        for n in NEIGHBORS[q]:
            value = result[n]
            if value == 0:
                liberties.add(n)
            elif value == color and n not in seen:
                seen.add(n)
                stack.append(n)

    if not liberties:
        return None

    key = board_key(result)
    if forbidden is not None and key in forbidden:
        return None

    return result, captured, liberties, own_stones, key


def territory_regions(board):
    """
    Classify reasonably bounded empty regions.

    owner[p] is:
       1 for a region bordered only by us,
      -1 for a region bordered only by the opponent,
       0 otherwise.

    Very large regions are treated as unsettled.
    """
    owner = [0] * AREA
    region_size = [0] * AREA
    visited = [False] * AREA

    for start in range(AREA):
        if board[start] != 0 or visited[start]:
            continue

        stack = [start]
        visited[start] = True
        region = []
        borders = set()

        while stack:
            q = stack.pop()
            region.append(q)
            for n in NEIGHBORS[q]:
                value = board[n]
                if value == 0:
                    if not visited[n]:
                        visited[n] = True
                        stack.append(n)
                else:
                    borders.add(value)

        classification = 0
        if len(region) <= 45 and borders == {1}:
            classification = 1
        elif len(region) <= 35 and borders == {-1}:
            classification = -1

        count = len(region)
        for q in region:
            owner[q] = classification
            region_size[q] = count

    return owner, region_size


def opening_bonus_map(board, stone_count):
    bonus = [0.0] * AREA
    if stone_count >= 45:
        return bonus

    corners = [
        (range(0, 7), range(0, 7), 3, 3),
        (range(0, 7), range(12, 19), 3, 15),
        (range(12, 19), range(0, 7), 15, 3),
        (range(12, 19), range(12, 19), 15, 15),
    ]

    for rr, cc, sr, sc in corners:
        contents = []
        for r in rr:
            for c in cc:
                if board[r * SIZE + c] != 0:
                    contents.append(board[r * SIZE + c])

        star = sr * SIZE + sc
        inward_r = 1 if sr < 9 else -1
        inward_c = 1 if sc < 9 else -1

        three_four = [
            (sr - inward_r) * SIZE + sc,
            sr * SIZE + (sc - inward_c),
        ]

        if not contents:
            if board[star] == 0:
                bonus[star] += 285.0
            for p in three_four:
                if board[p] == 0:
                    bonus[p] += 255.0
        else:
            friendly = contents.count(1)
            enemy = contents.count(-1)

            # Approach an opponent corner or develop a friendly corner.
            approach_points = [
                (sr - inward_r) * SIZE + (sc + 2 * inward_c),
                (sr + 2 * inward_r) * SIZE + (sc - inward_c),
                sr * SIZE + (sc + 3 * inward_c),
                (sr + 3 * inward_r) * SIZE + sc,
            ]
            for p in approach_points:
                if 0 <= p < AREA and board[p] == 0:
                    if enemy > friendly:
                        bonus[p] += 95.0
                    elif friendly > enemy:
                        bonus[p] += 65.0

    # Side star points are useful after corners begin to fill.
    side_stars = [
        3 * SIZE + 9,
        9 * SIZE + 3,
        15 * SIZE + 9,
        9 * SIZE + 15,
    ]
    for p in side_stars:
        if board[p] == 0:
            bonus[p] += 45.0 if stone_count < 28 else 15.0

    return bonus


def positional_values(board, stone_count):
    values = [0.0] * AREA
    occupied = [p for p, value in enumerate(board) if value != 0]

    for p in range(AREA):
        if board[p] != 0:
            continue

        r, c = divmod(p, SIZE)
        edge = min(r, c, SIZE - 1 - r, SIZE - 1 - c)

        if edge == 0:
            score = -175.0
        elif edge == 1:
            score = -65.0
        elif edge == 2:
            score = 28.0
        elif edge == 3:
            score = 42.0
        elif edge == 4:
            score = 22.0
        else:
            score = 10.0

        nearest = 99
        influence = 0.0
        friendly_near = 0
        enemy_near = 0

        for q in occupied:
            qr, qc = divmod(q, SIZE)
            dr = abs(r - qr)
            dc = abs(c - qc)
            d = max(dr, dc)
            if d < nearest:
                nearest = d

            if d <= 6:
                weights = (0.0, 12.0, 7.0, 4.0, 2.2, 1.2, 0.6)
                contribution = weights[d]
                if board[q] == 1:
                    influence += contribution
                    if d <= 3:
                        friendly_near += 1
                else:
                    influence -= contribution
                    if d <= 3:
                        enemy_near += 1

        if occupied:
            if stone_count < 24:
                if nearest >= 8:
                    score += 38.0
                elif nearest >= 5:
                    score += 47.0
                elif nearest >= 3:
                    score += 24.0
                elif nearest == 2:
                    score += 5.0
                else:
                    score -= 20.0
            else:
                if 2 <= nearest <= 4:
                    score += 17.0
                elif nearest >= 8:
                    score += 5.0

        # Prefer disputed zones over filling strongly friendly influence.
        if influence > 14:
            score -= (influence - 14) * 2.5
        elif -18 <= influence < -4:
            score += min(24.0, -influence * 1.3)
        elif influence < -25:
            score -= (-influence - 25) * 1.6

        if friendly_near and enemy_near:
            score += 18.0

        # Mild deterministic tie breaker.
        score += ((p * 37 + 11) % 17) * 0.01
        values[p] = score

    return values


def reply_tactical_value(board, last_point, historical_positions):
    """
    Estimate the opponent's strongest immediate tactical response.
    The board still uses 1 for us and -1 for the opponent.
    """
    gids, groups = analyze(board)
    candidates = set(NEIGHBORS[last_point])

    for color, stones, liberties in groups:
        if len(liberties) <= 2:
            candidates.update(liberties)

    if len(candidates) > 90:
        candidates = set(list(candidates)[:90])

    forbidden = set(historical_positions)
    forbidden.add(board_key(board))
    best = 0.0

    for p in candidates:
        if board[p] != 0:
            continue

        result = simulate(
            board, p, -1, gids=gids, groups=groups, forbidden=forbidden
        )
        if result is None:
            continue

        new_board, captured, liberties, own_stones, _ = result
        score = 0.0

        if captured:
            score += 650.0 + 225.0 * (len(captured) - 1)

        # Saving an opponent group that was in atari.
        saved = 0
        adjacent_enemy_groups = set()
        for n in NEIGHBORS[p]:
            if board[n] == -1:
                adjacent_enemy_groups.add(gids[n])

        for gid in adjacent_enemy_groups:
            color, stones, libs = groups[gid]
            if len(libs) == 1 and p in libs:
                saved += len(stones)

        if saved:
            score += 470.0 + 165.0 * (saved - 1)

        # Atari created against one of our groups.
        touched = set()
        for n in NEIGHBORS[p]:
            if board[n] == 1:
                gid = gids[n]
                if gid in touched:
                    continue
                touched.add(gid)
                color, stones, libs = groups[gid]
                if p in libs and len(libs) == 2:
                    score += 175.0 + 55.0 * min(5, len(stones))

        if len(liberties) == 1 and not captured:
            score -= 410.0 + 80.0 * min(5, len(own_stones))
        elif len(liberties) >= 4:
            score += 12.0

        if score > best:
            best = score

    return best


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        board = [0] * AREA

        for row, col in me:
            if 1 <= row <= SIZE and 1 <= col <= SIZE:
                board[(row - 1) * SIZE + (col - 1)] = 1

        for row, col in opponent:
            if 1 <= row <= SIZE and 1 <= col <= SIZE:
                p = (row - 1) * SIZE + (col - 1)
                if board[p] == 0:
                    board[p] = -1

        current_key = board_key(board)

        old_seen = memory.get("_seen", []) if isinstance(memory, dict) else []
        seen = set()
        if isinstance(old_seen, (list, tuple, set)):
            for item in old_seen:
                if isinstance(item, bytes) and len(item) == AREA:
                    seen.add(item)
        seen.add(current_key)

        gids, groups = analyze(board)
        stone_count = len(me) + len(opponent)

        region_owner, region_size = territory_regions(board)
        opening_bonus = opening_bonus_map(board, stone_count)
        positional = positional_values(board, stone_count)

        scored = []
        legal_results = {}

        for p in range(AREA):
            if board[p] != 0:
                continue

            result = simulate(
                board, p, 1, gids=gids, groups=groups, forbidden=seen
            )
            if result is None:
                continue

            new_board, captured, liberties, own_stones, new_key = result
            legal_results[p] = result

            score = 10.0 + positional[p] + opening_bonus[p]
            tactical = False

            captured_count = len(captured)
            if captured_count:
                tactical = True
                score += 700.0 + 230.0 * (captured_count - 1)

            adjacent_own = set()
            adjacent_enemy = set()
            for n in NEIGHBORS[p]:
                if board[n] == 1:
                    adjacent_own.add(gids[n])
                elif board[n] == -1:
                    adjacent_enemy.add(gids[n])

            # Rescue groups whose sole liberty is this move.
            saved_stones = 0
            saved_groups = 0
            for gid in adjacent_own:
                color, stones, libs = groups[gid]
                if len(libs) == 1 and p in libs:
                    saved_stones += len(stones)
                    saved_groups += 1

            if saved_stones:
                tactical = True
                score += 620.0 + 180.0 * (saved_stones - 1)
                if saved_groups > 1:
                    score += 130.0 * (saved_groups - 1)

            # Atari or pressure against neighboring opponent groups.
            for gid in adjacent_enemy:
                color, stones, libs = groups[gid]
                if p not in libs:
                    continue
                remaining = len(libs) - 1
                if remaining == 1:
                    tactical = True
                    score += 205.0 + 72.0 * min(8, len(stones))
                elif remaining == 2:
                    score += 24.0 + 6.0 * min(6, len(stones))

            # Connections are valuable, especially between several groups.
            if len(adjacent_own) >= 2:
                connected_size = sum(len(groups[g][1]) for g in adjacent_own)
                score += 72.0 * (len(adjacent_own) - 1)
                score += 8.0 * min(12, connected_size)

            # Splitting neighboring enemy groups has modest shape value.
            if len(adjacent_enemy) >= 2 and not captured_count:
                score += 34.0 * (len(adjacent_enemy) - 1)

            # Exact self-atari test, including whether recapture is prohibited.
            if len(liberties) == 1:
                reply_point = next(iter(liberties))
                enemy_forbidden = set(seen)
                enemy_forbidden.add(new_key)
                rgids, rgroups = analyze(new_board)
                punishment = simulate(
                    new_board,
                    reply_point,
                    -1,
                    gids=rgids,
                    groups=rgroups,
                    forbidden=enemy_forbidden,
                )
                if punishment is not None:
                    lost = len(punishment[1])
                    score -= 690.0 + 235.0 * max(0, lost - 1)
                else:
                    # Usually a protected ko capture.
                    score += 90.0
            elif len(liberties) == 2 and not tactical:
                score -= 28.0
            elif len(liberties) >= 5:
                score += 18.0

            # Avoid filling simple eyes unless tactically necessary.
            existing_neighbors = NEIGHBORS[p]
            if existing_neighbors and all(board[n] == 1 for n in existing_neighbors):
                if not tactical:
                    score -= 980.0
                else:
                    score -= 90.0

            # Diagonal shape: friendly diagonals aid connection; opposing
            # diagonals can indicate a useful cut.
            friendly_diagonal = 0
            enemy_diagonal = 0
            for d in DIAGONALS[p]:
                if board[d] == 1:
                    friendly_diagonal += 1
                elif board[d] == -1:
                    enemy_diagonal += 1
            score += 7.0 * friendly_diagonal
            if enemy_diagonal >= 2:
                score += 13.0

            # Do not casually spend points inside settled territory.
            if region_owner[p] == 1 and not tactical:
                score -= 130.0 + min(70.0, region_size[p] * 3.0)
            elif region_owner[p] == -1 and not tactical:
                if region_size[p] <= 8:
                    score -= 85.0
                elif region_size[p] <= 18:
                    score -= 30.0

            scored.append([score, p])

        if not scored:
            new_memory = dict(memory) if isinstance(memory, dict) else {}
            new_memory["_seen"] = list(seen)
            return (0, 0), new_memory

        scored.sort(reverse=True)

        # Examine tactical opponent replies for the most promising candidates.
        examine = min(16, len(scored))
        for i in range(examine):
            base_score, p = scored[i]
            new_board = legal_results[p][0]
            danger = reply_tactical_value(new_board, p, seen)
            scored[i][0] = base_score - 0.52 * danger

        scored[:examine] = sorted(scored[:examine], reverse=True)
        best_score, best_point = max(scored, key=lambda item: item[0])

        # In a mature position, passing is preferable to filling an eye or
        # making an obviously destructive invasion.
        if stone_count > 85 and best_score < -15.0:
            new_memory = dict(memory) if isinstance(memory, dict) else {}
            new_memory["_seen"] = list(seen)
            new_memory["_last_pass"] = True
            return (0, 0), new_memory

        chosen_result = legal_results[best_point]
        chosen_key = chosen_result[4]
        seen.add(chosen_key)

        new_memory = dict(memory) if isinstance(memory, dict) else {}
        new_memory["_seen"] = list(seen)
        new_memory["_last_pass"] = False
        new_memory["_after_my_move"] = chosen_key

        row, col = divmod(best_point, SIZE)
        return (row + 1, col + 1), new_memory

    except Exception:
        # Passing is always the safe legal fallback.
        safe_memory = dict(memory) if isinstance(memory, dict) else {}
        return (0, 0), safe_memory
