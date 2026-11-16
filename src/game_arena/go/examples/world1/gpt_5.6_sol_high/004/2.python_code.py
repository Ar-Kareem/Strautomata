
from collections import deque
from math import sqrt


SIZE = 19
AREA = SIZE * SIZE
EMPTY = 0
ME = 1
OPPONENT = -1

NEIGHBORS = [[] for _ in range(AREA)]
DIAGONALS = [[] for _ in range(AREA)]

for _p in range(AREA):
    _r, _c = divmod(_p, SIZE)
    if _r > 0:
        NEIGHBORS[_p].append(_p - SIZE)
    if _r + 1 < SIZE:
        NEIGHBORS[_p].append(_p + SIZE)
    if _c > 0:
        NEIGHBORS[_p].append(_p - 1)
    if _c + 1 < SIZE:
        NEIGHBORS[_p].append(_p + 1)

    if _r > 0 and _c > 0:
        DIAGONALS[_p].append(_p - SIZE - 1)
    if _r > 0 and _c + 1 < SIZE:
        DIAGONALS[_p].append(_p - SIZE + 1)
    if _r + 1 < SIZE and _c > 0:
        DIAGONALS[_p].append(_p + SIZE - 1)
    if _r + 1 < SIZE and _c + 1 < SIZE:
        DIAGONALS[_p].append(_p + SIZE + 1)


OPENING_POINTS = [
    (3, 3), (15, 15), (3, 15), (15, 3),
    (3, 9), (15, 9), (9, 3), (9, 15),
    (9, 9),
]

KOMOKU_POINTS = [
    (2, 3), (3, 2), (2, 15), (3, 16),
    (15, 2), (16, 3), (15, 16), (16, 15),
]

OPENING_RANK = {
    r * SIZE + c: i for i, (r, c) in enumerate(OPENING_POINTS)
}
KOMOKU_SET = {
    r * SIZE + c for r, c in KOMOKU_POINTS
}


def _analyze_groups(board, color):
    """Return point-to-group IDs and dictionaries containing stones/liberties."""
    group_id = [-1] * AREA
    groups = []

    for start in range(AREA):
        if board[start] != color or group_id[start] != -1:
            continue

        gid = len(groups)
        stack = [start]
        group_id[start] = gid
        stones = []
        liberties = set()

        while stack:
            p = stack.pop()
            stones.append(p)

            for q in NEIGHBORS[p]:
                value = board[q]
                if value == EMPTY:
                    liberties.add(q)
                elif value == color and group_id[q] == -1:
                    group_id[q] = gid
                    stack.append(q)

        groups.append({
            "stones": stones,
            "libs": liberties,
            "size": len(stones),
        })

    return group_id, groups


def _distance_map(board, color):
    """Manhattan distance to the nearest stone of color."""
    distance = [99] * AREA
    queue = deque()

    for p, value in enumerate(board):
        if value == color:
            distance[p] = 0
            queue.append(p)

    while queue:
        p = queue.popleft()
        next_distance = distance[p] + 1
        for q in NEIGHBORS[p]:
            if next_distance < distance[q]:
                distance[q] = next_distance
                queue.append(q)

    return distance


def _empty_regions(board):
    """Classify connected empty regions by bordering colors and size."""
    region_id = [-1] * AREA
    region_owner = []
    region_size = []

    for start in range(AREA):
        if board[start] != EMPTY or region_id[start] != -1:
            continue

        rid = len(region_owner)
        region_id[start] = rid
        stack = [start]
        points = []
        borders = set()

        while stack:
            p = stack.pop()
            points.append(p)

            for q in NEIGHBORS[p]:
                if board[q] == EMPTY:
                    if region_id[q] == -1:
                        region_id[q] = rid
                        stack.append(q)
                else:
                    borders.add(board[q])

        if borders == {ME}:
            owner = ME
        elif borders == {OPPONENT}:
            owner = OPPONENT
        else:
            owner = EMPTY

        region_owner.append(owner)
        region_size.append(len(points))

    return region_id, region_owner, region_size


def _corner_approach_bonus(board, p, total_stones):
    if total_stones > 90:
        return 0.0

    r, c = divmod(p, SIZE)
    bonus = 0.0

    corner_data = (
        (
            range(0, 7), range(0, 7),
            {(2, 5), (5, 2), (3, 6), (6, 3)}
        ),
        (
            range(0, 7), range(12, 19),
            {(2, 13), (5, 16), (3, 12), (6, 15)}
        ),
        (
            range(12, 19), range(0, 7),
            {(13, 2), (16, 5), (12, 3), (15, 6)}
        ),
        (
            range(12, 19), range(12, 19),
            {(13, 16), (16, 13), (12, 15), (15, 12)}
        ),
    )

    for rows, cols, approaches in corner_data:
        if (r, c) not in approaches:
            continue

        own = 0
        enemy = 0
        for rr in rows:
            base = rr * SIZE
            for cc in cols:
                value = board[base + cc]
                if value == ME:
                    own += 1
                elif value == OPPONENT:
                    enemy += 1

        if enemy > 0 and own == 0:
            bonus += 27.0
        elif enemy > own and own <= 1:
            bonus += 13.0

    return bonus


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]]
) -> tuple[int, int]:
    board = [EMPTY] * AREA

    for row, col in me:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[(row - 1) * SIZE + (col - 1)] = ME

    for row, col in opponent:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[(row - 1) * SIZE + (col - 1)] = OPPONENT

    total_stones = sum(1 for value in board if value != EMPTY)
    if total_stones == AREA:
        return (0, 0)

    my_gid, my_groups = _analyze_groups(board, ME)
    opp_gid, opp_groups = _analyze_groups(board, OPPONENT)

    my_distance = _distance_map(board, ME)
    opp_distance = _distance_map(board, OPPONENT)

    region_id, region_owner, region_size = _empty_regions(board)

    opening_weight = max(0.0, min(1.0, (75.0 - total_stones) / 75.0))
    late_weight = max(0.0, min(1.0, (total_stones - 110.0) / 170.0))

    candidates = []

    for p in range(AREA):
        if board[p] != EMPTY:
            continue

        adjacent_my_ids = {
            my_gid[q] for q in NEIGHBORS[p] if board[q] == ME
        }
        adjacent_opp_ids = {
            opp_gid[q] for q in NEIGHBORS[p] if board[q] == OPPONENT
        }

        captured_ids = {
            gid for gid in adjacent_opp_ids
            if len(opp_groups[gid]["libs"]) == 1
            and p in opp_groups[gid]["libs"]
        }

        captured_stones = []
        for gid in captured_ids:
            captured_stones.extend(opp_groups[gid]["stones"])

        captured_set = set(captured_stones)
        capture_count = len(captured_stones)

        # Compute the exact liberties of the newly played/merged group.
        new_liberties = set()
        for q in NEIGHBORS[p]:
            if board[q] == EMPTY:
                new_liberties.add(q)

        new_group_size = 1
        for gid in adjacent_my_ids:
            group = my_groups[gid]
            new_group_size += group["size"]
            new_liberties.update(group["libs"])

        new_liberties.discard(p)

        # Captured stones become liberties only where they touch the new group.
        for q in captured_stones:
            touches_new_group = p in NEIGHBORS[q]
            if not touches_new_group:
                for n in NEIGHBORS[q]:
                    if board[n] == ME and my_gid[n] in adjacent_my_ids:
                        touches_new_group = True
                        break
            if touches_new_group:
                new_liberties.add(q)

        # Suicide is illegal.
        if not new_liberties:
            continue

        # With no history available, conservatively avoid the only local shape
        # that can be an immediate simple-ko recapture.
        possible_ko_recapture = (
            capture_count == 1
            and new_group_size == 1
            and len(new_liberties) == 1
        )
        if possible_ko_recapture:
            continue

        score = 0.0
        row, col = divmod(p, SIZE)
        edge_distance = min(row, col, SIZE - 1 - row, SIZE - 1 - col)

        # Tactical captures.
        if capture_count:
            score += 112.0 * capture_count
            score += 28.0 * len(captured_ids)
            score += 7.0 * sqrt(capture_count)

        # Determine which endangered friendly groups this move saves.
        saved_groups = set()

        if len(new_liberties) >= 2:
            for gid in adjacent_my_ids:
                if len(my_groups[gid]["libs"]) == 1:
                    saved_groups.add(gid)

        # Capturing can save a non-connected friendly chain by opening liberties.
        for q in captured_stones:
            for n in NEIGHBORS[q]:
                if board[n] == ME:
                    gid = my_gid[n]
                    if (
                        gid not in adjacent_my_ids
                        and len(my_groups[gid]["libs"]) == 1
                    ):
                        saved_groups.add(gid)

        for gid in saved_groups:
            size = my_groups[gid]["size"]
            score += 45.0 + 105.0 * size

        # Reward healthy extensions of groups that currently have two liberties.
        for gid in adjacent_my_ids:
            group = my_groups[gid]
            if len(group["libs"]) == 2 and len(new_liberties) >= 3:
                score += 8.0 + 4.0 * min(group["size"], 8)

        # Attacks, ataris, and liberty reduction.
        for gid in adjacent_opp_ids:
            if gid in captured_ids:
                continue

            group = opp_groups[gid]
            old_liberty_count = len(group["libs"])
            resulting_liberties = old_liberty_count - 1
            size = group["size"]

            if resulting_liberties == 1:
                attack_value = 22.0 + 10.0 * min(size, 14)
                attack_value += 3.0 * sqrt(size)

                remaining = next(
                    (liberty for liberty in group["libs"] if liberty != p),
                    None
                )
                if remaining is not None:
                    escape_options = sum(
                        1 for q in NEIGHBORS[remaining]
                        if board[q] == EMPTY and q != p
                    )
                    if escape_options >= 3:
                        attack_value -= 8.0
                    elif escape_options <= 1:
                        attack_value += 8.0

                score += attack_value
            elif resulting_liberties == 2:
                score += 5.0 + 2.5 * min(size, 10)
            elif resulting_liberties == 3 and size >= 4:
                score += 2.0

        # New-group safety.
        liberty_count = len(new_liberties)
        if liberty_count == 1:
            score -= 90.0 + 28.0 * new_group_size
        elif liberty_count == 2:
            score -= 10.0 + min(12.0, new_group_size * 0.8)
        elif liberty_count == 3:
            score += 7.0
        elif liberty_count == 4:
            score += 12.0
        else:
            score += 14.0 + min(8.0, liberty_count - 4)

        # Connection and cutting value.
        if len(adjacent_my_ids) >= 2:
            connected_size = sum(
                my_groups[gid]["size"] for gid in adjacent_my_ids
            )
            score += 16.0 + min(22.0, connected_size * 1.5)
        elif len(adjacent_my_ids) == 1:
            score += 3.0

        if len(adjacent_opp_ids - captured_ids) >= 2:
            score += 9.0 * (len(adjacent_opp_ids - captured_ids) - 1)

        direct_friends = sum(1 for q in NEIGHBORS[p] if board[q] == ME)
        direct_enemies = sum(1 for q in NEIGHBORS[p] if board[q] == OPPONENT)
        diagonal_friends = sum(1 for q in DIAGONALS[p] if board[q] == ME)
        diagonal_enemies = sum(1 for q in DIAGONALS[p] if board[q] == OPPONENT)

        score += 2.0 * direct_enemies
        score += 1.5 * diagonal_friends
        score += 0.5 * diagonal_enemies

        # Avoid needlessly filling a liberty of one already-connected chain.
        if len(adjacent_my_ids) == 1 and direct_friends >= 2 and not capture_count:
            score -= 7.0

        # Strong penalty for filling a simple friendly eye.
        simple_friendly_eye = (
            len(NEIGHBORS[p]) > 0
            and all(board[q] == ME for q in NEIGHBORS[p])
            and capture_count == 0
        )
        if simple_friendly_eye:
            score -= 145.0

        # Edge-aware positional value.
        if edge_distance == 0:
            score -= 31.0 * opening_weight
            score += 2.0 * late_weight
        elif edge_distance == 1:
            score -= 14.0 * opening_weight
            score += 2.0 * late_weight
        elif edge_distance == 2:
            score += 5.0 * opening_weight
        elif edge_distance == 3:
            score += 14.0 * opening_weight
        elif edge_distance == 4:
            score += 8.0 * opening_weight
        else:
            score += 3.0 * opening_weight

        # Standard opening points and corner approaches.
        if p in OPENING_RANK and total_stones < 45:
            rank = OPENING_RANK[p]
            score += opening_weight * max(32.0, 67.0 - 2.5 * rank)

        if p in KOMOKU_SET and total_stones < 38:
            score += 47.0 * opening_weight

        score += _corner_approach_bonus(board, p, total_stones) * opening_weight

        # Influence and frontier play.
        dm = my_distance[p]
        do = opp_distance[p]

        if dm < 99 and do < 99:
            if abs(dm - do) <= 2:
                score += 7.0 + 4.0 * late_weight
            elif dm + 2 < do:
                score -= 4.0 + 11.0 * late_weight
            elif do + 2 < dm:
                score += 5.0
        elif do < 99:
            score += 3.0

        # Region ownership: avoid filling small secure friendly regions.
        rid = region_id[p]
        owner = region_owner[rid]
        rsize = region_size[rid]

        if owner == ME and rsize <= 25 and capture_count == 0:
            score -= 24.0 + 23.0 * late_weight
            if rsize <= 3:
                score -= 30.0
        elif owner == OPPONENT:
            if rsize >= 9:
                score += 7.0
            elif rsize <= 3 and capture_count == 0:
                score -= 18.0

        # Prefer shape with some surrounding room.
        nearby_empty = sum(1 for q in NEIGHBORS[p] if board[q] == EMPTY)
        score += 1.1 * nearby_empty

        # Stable deterministic tie breaker.
        score += ((p * 73 + total_stones * 37 + len(me) * 19) % 997) * 1e-6

        candidates.append((score, p))

    if not candidates:
        return (0, 0)

    candidates.sort(reverse=True)
    best_score, best_point = candidates[0]

    # Pass when only destructive moves remain in a sufficiently advanced game.
    if total_stones > 220 and best_score < -12.0:
        return (0, 0)
    if total_stones > 110 and best_score < -75.0:
        return (0, 0)

    row, col = divmod(best_point, SIZE)
    return (row + 1, col + 1)
