
from math import sqrt

SIZE = 19
AREA = SIZE * SIZE


def _make_neighbors():
    result = []
    for r in range(SIZE):
        for c in range(SIZE):
            ns = []
            if r > 0:
                ns.append((r - 1) * SIZE + c)
            if r + 1 < SIZE:
                ns.append((r + 1) * SIZE + c)
            if c > 0:
                ns.append(r * SIZE + c - 1)
            if c + 1 < SIZE:
                ns.append(r * SIZE + c + 1)
            result.append(tuple(ns))
    return tuple(result)


def _make_diagonals():
    result = []
    for r in range(SIZE):
        for c in range(SIZE):
            ds = []
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < SIZE and 0 <= cc < SIZE:
                    ds.append(rr * SIZE + cc)
            result.append(tuple(ds))
    return tuple(result)


NEIGHBORS = _make_neighbors()
DIAGONALS = _make_diagonals()


def _board_key(board):
    return bytes(v + 1 for v in board)


def _flood(board, start):
    color = board[start]
    stones = []
    liberties = set()
    seen = {start}
    stack = [start]

    while stack:
        p = stack.pop()
        stones.append(p)
        for q in NEIGHBORS[p]:
            value = board[q]
            if value == 0:
                liberties.add(q)
            elif value == color and q not in seen:
                seen.add(q)
                stack.append(q)

    return stones, liberties


def _analyse(board):
    group_at = [-1] * AREA
    groups = []
    seen = [False] * AREA

    for start in range(AREA):
        if board[start] == 0 or seen[start]:
            continue

        color = board[start]
        stones = []
        liberties = set()
        stack = [start]
        seen[start] = True
        gid = len(groups)

        while stack:
            p = stack.pop()
            stones.append(p)
            group_at[p] = gid

            for q in NEIGHBORS[p]:
                value = board[q]
                if value == 0:
                    liberties.add(q)
                elif value == color and not seen[q]:
                    seen[q] = True
                    stack.append(q)

        groups.append((color, tuple(stones), frozenset(liberties)))

    return group_at, groups


def _play(board, point, color):
    if point < 0 or point >= AREA or board[point] != 0:
        return None

    new_board = board.copy()
    new_board[point] = color
    captured = []
    checked = set()

    for q in NEIGHBORS[point]:
        if new_board[q] != -color or q in checked:
            continue

        stones, liberties = _flood(new_board, q)
        checked.update(stones)

        if not liberties:
            captured.extend(stones)
            for stone in stones:
                new_board[stone] = 0

    own_stones, own_liberties = _flood(new_board, point)
    if not own_liberties:
        return None

    return new_board, captured, own_stones, own_liberties


def _true_eye(board, point, color):
    for q in NEIGHBORS[point]:
        if board[q] != color:
            return False

    diagonals = DIAGONALS[point]
    bad = sum(1 for q in diagonals if board[q] != color)

    if len(diagonals) == 4:
        return bad <= 1
    return bad == 0


def _empty_regions(board):
    owner = [9] * AREA
    region_size = [0] * AREA
    border_mask = [0] * AREA
    seen = [False] * AREA

    for start in range(AREA):
        if board[start] != 0 or seen[start]:
            continue

        points = []
        stack = [start]
        seen[start] = True
        mask = 0

        while stack:
            p = stack.pop()
            points.append(p)

            for q in NEIGHBORS[p]:
                value = board[q]
                if value == 0:
                    if not seen[q]:
                        seen[q] = True
                        stack.append(q)
                elif value == 1:
                    mask |= 1
                else:
                    mask |= 2

        if mask == 1:
            region_owner = 1
        elif mask == 2:
            region_owner = -1
        else:
            region_owner = 0

        size = len(points)
        for p in points:
            owner[p] = region_owner
            region_size[p] = size
            border_mask[p] = mask

    return owner, region_size, border_mask


def _immediate_capture_risk(board, forbidden_positions):
    _, groups = _analyse(board)
    candidate_liberties = set()

    for color, stones, liberties in groups:
        if color == 1 and len(liberties) == 1:
            candidate_liberties.add(next(iter(liberties)))

    largest = 0

    for point in candidate_liberties:
        result = _play(board, point, -1)
        if result is None:
            continue

        next_board, captured, _, _ = result
        if _board_key(next_board) in forbidden_positions:
            continue

        if len(captured) > largest:
            largest = len(captured)

    return largest


def _corner_information(board):
    zones = (
        (range(0, 7), range(0, 7)),
        (range(0, 7), range(12, 19)),
        (range(12, 19), range(0, 7)),
        (range(12, 19), range(12, 19)),
    )

    counts = []
    for rows, cols in zones:
        count = 0
        for r in rows:
            base = r * SIZE
            for c in cols:
                if board[base + c] != 0:
                    count += 1
        counts.append(count)

    return counts


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict
) -> tuple[tuple[int, int], dict]:
    board = [0] * AREA

    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + (c - 1)] = 1

    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + (c - 1)] = -1

    if not isinstance(memory, dict):
        memory = {}

    old_history = memory.get("_history", [])
    history_list = []
    history_set = set()

    if isinstance(old_history, (list, tuple)):
        for item in old_history:
            if isinstance(item, bytes) and len(item) == AREA:
                if item not in history_set:
                    history_set.add(item)
                    history_list.append(item)

    had_history = bool(history_list)
    current_key = _board_key(board)

    last_after = memory.get("_last_after")
    opponent_passed = (
        isinstance(last_after, bytes)
        and len(last_after) == AREA
        and last_after == current_key
    )

    if current_key not in history_set:
        history_set.add(current_key)
        history_list.append(current_key)

    group_at, groups = _analyse(board)
    region_owner, region_size, border_mask = _empty_regions(board)
    corner_counts = _corner_information(board)

    total_stones = len(me) + len(opponent)
    all_stones = [i for i, value in enumerate(board) if value != 0]
    own_points = [i for i, value in enumerate(board) if value == 1]
    enemy_points = [i for i, value in enumerate(board) if value == -1]

    stars = {(3, 3), (3, 15), (15, 3), (15, 15)}
    corner_specials = (
        ((3, 3), {(2, 3), (3, 2)}),
        ((3, 15), {(2, 15), (3, 16)}),
        ((15, 3), {(15, 2), (16, 3)}),
        ((15, 15), {(15, 16), (16, 15)}),
    )

    candidates = []

    for point in range(AREA):
        if board[point] != 0:
            continue

        result = _play(board, point, 1)
        if result is None:
            continue

        next_board, captured, new_group, new_liberties = result
        next_key = _board_key(next_board)

        if next_key in history_set:
            continue

        # With no prior history, conservatively avoid a structurally possible
        # immediate ko recapture.
        if (
            not had_history
            and len(captured) == 1
            and len(new_group) == 1
            and len(new_liberties) == 1
        ):
            continue

        r, c = divmod(point, SIZE)
        adjacent_own = set()
        adjacent_enemy = set()

        for q in NEIGHBORS[point]:
            gid = group_at[q]
            if gid < 0:
                continue
            if groups[gid][0] == 1:
                adjacent_own.add(gid)
            else:
                adjacent_enemy.add(gid)

        capture_count = len(captured)
        score = 0.0

        if capture_count:
            score += 125.0 * capture_count
            score += 25.0 * sqrt(capture_count)
            score += 8.0 * len(
                [gid for gid in adjacent_enemy if len(groups[gid][2]) == 1]
            )

        saved_value = 0.0
        for gid in adjacent_own:
            _, stones, liberties = groups[gid]
            size = len(stones)

            if len(liberties) == 1 and point in liberties:
                saved_value += 105.0 + 18.0 * size
            elif len(liberties) == 2 and point in liberties:
                score += 10.0 + 2.5 * min(size, 12)

        if saved_value:
            if len(new_liberties) >= 2:
                score += saved_value
            else:
                score += 0.15 * saved_value

        for gid in adjacent_enemy:
            _, stones, liberties = groups[gid]
            size = len(stones)

            if point not in liberties:
                continue

            if len(liberties) == 2:
                score += 35.0 + 11.0 * min(size, 10)
            elif len(liberties) == 3:
                score += 5.0 + 2.0 * min(size, 8)

        if len(adjacent_own) >= 2:
            score += 13.0 * (len(adjacent_own) - 1)
            weak_connections = sum(
                1 for gid in adjacent_own if len(groups[gid][2]) <= 2
            )
            score += 8.0 * weak_connections

        if len(adjacent_enemy) >= 2:
            score += 8.0 * (len(adjacent_enemy) - 1)

        liberty_count = len(new_liberties)
        new_group_size = len(new_group)

        if liberty_count == 1:
            is_simple_ko_take = (
                capture_count == 1
                and new_group_size == 1
            )
            if is_simple_ko_take:
                score -= 22.0
            else:
                score -= 150.0 + 15.0 * min(new_group_size, 15)
        elif liberty_count == 2:
            score -= 12.0
        else:
            score += 2.5 * min(liberty_count, 6)

        own_neighbors = sum(1 for q in NEIGHBORS[point] if board[q] == 1)
        enemy_neighbors = sum(1 for q in NEIGHBORS[point] if board[q] == -1)
        own_diagonals = sum(1 for q in DIAGONALS[point] if board[q] == 1)
        enemy_diagonals = sum(1 for q in DIAGONALS[point] if board[q] == -1)

        score += 3.5 * own_neighbors
        score += 4.0 * enemy_neighbors
        score += 1.7 * own_diagonals
        score += 0.7 * enemy_diagonals

        if own_neighbors and enemy_neighbors:
            score += 7.0

        edge = min(r, c, SIZE - 1 - r, SIZE - 1 - c)
        if edge == 0:
            score -= 45.0
        elif edge == 1:
            score -= 11.0
        elif edge == 2:
            score += 8.0
        elif edge == 3:
            score += 12.0
        else:
            score += 5.0

        if _true_eye(board, point, 1):
            score -= 240.0

        owner = region_owner[point]
        component_size = region_size[point]
        mask = border_mask[point]

        if owner == 1:
            score -= 170.0
            if component_size <= 2:
                score -= 60.0
        elif owner == -1:
            if component_size <= 3:
                score -= 180.0
            elif component_size <= 6:
                score -= 85.0
            elif component_size <= 12:
                score -= 25.0
            elif liberty_count >= 4:
                score += 8.0
        elif total_stones > 100:
            if mask == 3:
                score += 28.0
            else:
                score += 8.0

        if total_stones < 45:
            if (r, c) in stars:
                score += 24.0

            for index, (star, three_four_points) in enumerate(corner_specials):
                if corner_counts[index] == 0:
                    if (r, c) == star:
                        score += 82.0
                    elif (r, c) in three_four_points:
                        score += 58.0

        if all_stones:
            nearest = min(
                max(abs(r - (q // SIZE)), abs(c - (q % SIZE)))
                for q in all_stones
            )

            if total_stones < 15:
                score += 2.2 * min(nearest, 10)
            elif total_stones >= 40 and nearest > 5:
                score -= 3.0 * (nearest - 5)

        if own_points:
            nearest_own = min(
                max(abs(r - (q // SIZE)), abs(c - (q % SIZE)))
                for q in own_points
            )
            if 2 <= nearest_own <= 4:
                score += 3.0

        if enemy_points:
            nearest_enemy = min(
                max(abs(r - (q // SIZE)), abs(c - (q % SIZE)))
                for q in enemy_points
            )
            if 2 <= nearest_enemy <= 4:
                score += 7.0

        own_influence = 0
        enemy_influence = 0
        for rr in range(max(0, r - 4), min(SIZE, r + 5)):
            for cc in range(max(0, c - 4), min(SIZE, c + 5)):
                q = rr * SIZE + cc
                value = board[q]
                if value == 0:
                    continue

                distance = max(abs(rr - r), abs(cc - c))
                weight = 5 - distance
                if value == 1:
                    own_influence += weight
                else:
                    enemy_influence += weight

        if total_stones > 50:
            difference = own_influence - enemy_influence
            if difference > 7 and enemy_neighbors == 0:
                score -= 0.8 * difference
            elif abs(difference) <= 4 and own_influence + enemy_influence > 3:
                score += 4.0

        # Stable, board-dependent tie breaker.
        jitter_seed = (
            point * 1103515245
            + total_stones * 12345
            + len(me) * 2654435761
        )
        score += (jitter_seed & 255) / 10000.0

        candidates.append(
            [
                score,
                point,
                next_board,
                next_key,
                capture_count,
            ]
        )

    if not candidates:
        output_memory = dict(memory)
        output_memory["_history"] = history_list
        output_memory["_last_after"] = current_key
        return (0, 0), output_memory

    candidates.sort(key=lambda item: item[0], reverse=True)

    # Refine the strongest candidates by checking the opponent's largest
    # immediately available capture.
    refinement_count = min(28, len(candidates))
    forbidden_for_reply = set(history_set)

    for i in range(refinement_count):
        item = candidates[i]
        forbidden_for_reply.add(item[3])
        risk = _immediate_capture_risk(item[2], forbidden_for_reply)
        forbidden_for_reply.discard(item[3])

        if risk:
            item[0] -= 70.0 * risk + 12.0 * sqrt(risk)

    candidates[:refinement_count] = sorted(
        candidates[:refinement_count],
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_point, best_board, best_key, _ = candidates[0]

    should_pass = False
    if opponent_passed and total_stones > 60 and best_score < 5.0:
        should_pass = True
    elif total_stones > 140 and best_score < -18.0:
        should_pass = True
    elif total_stones > 250 and best_score < 0.0:
        should_pass = True

    output_memory = dict(memory)

    if should_pass:
        output_memory["_history"] = history_list
        output_memory["_last_after"] = current_key
        return (0, 0), output_memory

    if best_key not in history_set:
        history_set.add(best_key)
        history_list.append(best_key)

    output_memory["_history"] = history_list
    output_memory["_last_after"] = best_key

    row, col = divmod(best_point, SIZE)
    return (row + 1, col + 1), output_memory
