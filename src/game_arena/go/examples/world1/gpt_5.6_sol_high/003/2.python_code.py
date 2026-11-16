
from typing import Dict, List, Set, Tuple

Point = Tuple[int, int]

SIZE = 19
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _neighbors(p: Point):
    r, c = p
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            yield nr, nc


def _build_groups(
    stones: Set[Point], occupied: Set[Point]
) -> Tuple[List[Tuple[Set[Point], Set[Point]]], Dict[Point, int]]:
    groups: List[Tuple[Set[Point], Set[Point]]] = []
    group_map: Dict[Point, int] = {}
    unseen = set(stones)

    while unseen:
        start = unseen.pop()
        stack = [start]
        group = {start}
        liberties: Set[Point] = set()

        while stack:
            p = stack.pop()
            for q in _neighbors(p):
                if q not in occupied:
                    liberties.add(q)
                elif q in stones and q not in group:
                    group.add(q)
                    unseen.discard(q)
                    stack.append(q)

        index = len(groups)
        groups.append((group, liberties))
        for p in group:
            group_map[p] = index

    return groups, group_map


def _empty_regions(
    me: Set[Point], opponent: Set[Point]
) -> Dict[Point, Tuple[int, bool, bool]]:
    occupied = me | opponent
    unseen = {
        (r, c)
        for r in range(SIZE)
        for c in range(SIZE)
        if (r, c) not in occupied
    }
    result: Dict[Point, Tuple[int, bool, bool]] = {}

    while unseen:
        start = unseen.pop()
        stack = [start]
        region = {start}
        borders_me = False
        borders_opponent = False

        while stack:
            p = stack.pop()
            for q in _neighbors(p):
                if q in me:
                    borders_me = True
                elif q in opponent:
                    borders_opponent = True
                elif q not in region:
                    region.add(q)
                    unseen.discard(q)
                    stack.append(q)

        description = (len(region), borders_me, borders_opponent)
        for p in region:
            result[p] = description

    return result


def _analyze_move(
    p: Point,
    me: Set[Point],
    opponent: Set[Point],
    my_groups: List[Tuple[Set[Point], Set[Point]]],
    my_map: Dict[Point, int],
    opponent_groups: List[Tuple[Set[Point], Set[Point]]],
    opponent_map: Dict[Point, int],
):
    if p in me or p in opponent:
        return None

    adjacent_my_ids: Set[int] = set()
    adjacent_opponent_ids: Set[int] = set()

    for q in _neighbors(p):
        if q in me:
            adjacent_my_ids.add(my_map[q])
        elif q in opponent:
            adjacent_opponent_ids.add(opponent_map[q])

    captured_ids: Set[int] = set()
    captured: Set[Point] = set()

    for index in adjacent_opponent_ids:
        stones, liberties = opponent_groups[index]
        if len(liberties) == 1 and p in liberties:
            captured_ids.add(index)
            captured.update(stones)

    new_group = {p}
    for index in adjacent_my_ids:
        new_group.update(my_groups[index][0])

    final_opponent = opponent - captured
    new_liberties: Set[Point] = set()

    for stone in new_group:
        for q in _neighbors(stone):
            if q not in me and q != p and q not in final_opponent:
                new_liberties.add(q)

    if not new_liberties:
        return None

    # Any illegal immediate simple-ko recapture must have this shape.
    # Since history is unavailable, these ambiguous moves are conservatively
    # avoided in favor of an unquestionably legal alternative.
    possible_ko_recapture = (
        len(captured) == 1
        and len(new_group) == 1
        and len(new_liberties) == 1
    )

    return (
        captured,
        captured_ids,
        new_group,
        new_liberties,
        adjacent_my_ids,
        adjacent_opponent_ids,
        possible_ko_recapture,
    )


def _is_own_eye(
    p: Point,
    me: Set[Point],
    opponent: Set[Point],
) -> bool:
    orthogonal = list(_neighbors(p))
    if not orthogonal or any(q not in me for q in orthogonal):
        return False

    r, c = p
    opponent_diagonals = 0
    off_board_diagonals = 0

    for dr, dc in DIAGONALS:
        q = (r + dr, c + dc)
        if not (0 <= q[0] < SIZE and 0 <= q[1] < SIZE):
            off_board_diagonals += 1
        elif q in opponent:
            opponent_diagonals += 1

    if off_board_diagonals:
        return opponent_diagonals == 0
    return opponent_diagonals <= 1


def _opening_score(
    p: Point,
    occupied: Set[Point],
    stone_count: int,
) -> float:
    if stone_count >= 70:
        return 0.0

    r, c = p
    score = 0.0
    edge_distance = min(r, c, SIZE - 1 - r, SIZE - 1 - c)

    if edge_distance == 3:
        score += 75.0
    elif edge_distance == 2:
        score += 52.0
    elif edge_distance == 4:
        score += 28.0
    elif edge_distance == 1:
        score -= 38.0
    elif edge_distance == 0:
        score -= 130.0

    corner_specs = (
        (range(0, 7), range(0, 7), (3, 3), {(2, 3), (3, 2)}, (2, 2)),
        (range(0, 7), range(12, 19), (3, 15), {(2, 15), (3, 16)}, (2, 16)),
        (range(12, 19), range(0, 7), (15, 3), {(16, 3), (15, 2)}, (16, 2)),
        (
            range(12, 19),
            range(12, 19),
            (15, 15),
            {(16, 15), (15, 16)},
            (16, 16),
        ),
    )

    for rows, cols, star, komoku, san_san in corner_specs:
        if r not in rows or c not in cols:
            continue

        corner_occupied = any(
            q[0] in rows and q[1] in cols for q in occupied
        )

        if not corner_occupied:
            if p == star:
                score += 330.0
            elif p in komoku:
                score += 270.0
            elif p == san_san:
                score += 155.0
            elif edge_distance in (2, 3):
                score += 35.0
        break

    if occupied:
        nearest = min(
            max(abs(r - q[0]), abs(c - q[1])) for q in occupied
        )
        if stone_count < 45:
            if nearest >= 7:
                score += 65.0
            elif nearest >= 5:
                score += 42.0
            elif nearest == 1:
                score -= 55.0

    return score


def _positional_score(
    p: Point,
    me: Set[Point],
    opponent: Set[Point],
    stone_count: int,
) -> float:
    r, c = p
    score = 0.0
    occupied = me | opponent

    edge_distance = min(r, c, SIZE - 1 - r, SIZE - 1 - c)
    if stone_count >= 70:
        if edge_distance == 0:
            score -= 24.0
        elif edge_distance == 2:
            score += 9.0
        elif edge_distance == 3:
            score += 7.0

    friendly_influence = 0.0
    enemy_influence = 0.0
    friendly_near = 0
    enemy_near = 0
    nearest = 30

    for q in occupied:
        distance = max(abs(r - q[0]), abs(c - q[1]))
        nearest = min(nearest, distance)
        if distance <= 5:
            weight = 6 - distance
            if q in me:
                friendly_influence += weight
                friendly_near += 1
            else:
                enemy_influence += weight
                enemy_near += 1

    if friendly_near and enemy_near:
        score += 18.0
        score += min(20.0, 2.0 * min(friendly_influence, enemy_influence))
    elif enemy_near:
        score += min(18.0, enemy_influence * 1.5)
    elif friendly_near:
        if friendly_influence > 16:
            score -= (friendly_influence - 16) * 2.0
        else:
            score += min(10.0, friendly_influence)

    if stone_count >= 45:
        if nearest >= 7:
            score += 18.0
        elif nearest in (3, 4, 5):
            score += 12.0
        elif nearest == 1:
            score -= 5.0

    # Empty-triangle shape penalty.
    adjacent_directions = []
    for dr, dc in DIRECTIONS:
        if (r + dr, c + dc) in me:
            adjacent_directions.append((dr, dc))

    for i in range(len(adjacent_directions)):
        dr1, dc1 = adjacent_directions[i]
        for j in range(i + 1, len(adjacent_directions)):
            dr2, dc2 = adjacent_directions[j]
            if dr1 * dr2 + dc1 * dc2 == 0:
                diagonal = (r + dr1 + dr2, c + dc1 + dc2)
                if diagonal in me:
                    score -= 24.0

    return score


def _score_move(
    p: Point,
    analysis,
    me: Set[Point],
    opponent: Set[Point],
    my_groups: List[Tuple[Set[Point], Set[Point]]],
    opponent_groups: List[Tuple[Set[Point], Set[Point]]],
    regions: Dict[Point, Tuple[int, bool, bool]],
    stone_count: int,
    fingerprint: int,
) -> float:
    (
        captured,
        captured_ids,
        new_group,
        new_liberties,
        adjacent_my_ids,
        adjacent_opponent_ids,
        _,
    ) = analysis

    capture_count = len(captured)
    score = 0.0
    tactical = False

    # Captures.
    if capture_count:
        tactical = True
        score += 1280.0 + 175.0 * capture_count
        score += 14.0 * min(capture_count * capture_count, 100)

    # Save friendly groups currently in atari.
    rescued_stones = 0
    for index in adjacent_my_ids:
        stones, liberties = my_groups[index]
        if len(liberties) == 1 and p in liberties:
            rescued_stones += len(stones)
            score += 1020.0 + 135.0 * len(stones)
            tactical = True
        elif len(liberties) == 2 and p in liberties and len(new_liberties) >= 3:
            score += 82.0 + 13.0 * min(len(stones), 12)

    # Attack adjacent enemy groups.
    attacked_groups = 0
    for index in adjacent_opponent_ids:
        if index in captured_ids:
            continue

        stones, liberties = opponent_groups[index]
        remaining = liberties - {p}

        if len(remaining) == 1:
            attacked_groups += 1
            score += 255.0 + 43.0 * min(len(stones), 20)
            tactical = True
        elif len(remaining) == 2:
            score += 32.0 + 5.0 * min(len(stones), 10)
        elif p in liberties:
            score += 8.0

    if len(adjacent_opponent_ids - captured_ids) >= 2:
        score += 52.0 * (len(adjacent_opponent_ids - captured_ids) - 1)

    # Connections, especially connections between weak groups.
    if len(adjacent_my_ids) >= 2:
        score += 38.0 * (len(adjacent_my_ids) - 1)
        for index in adjacent_my_ids:
            stones, liberties = my_groups[index]
            if len(liberties) <= 2:
                score += 35.0 + 6.0 * min(len(stones), 10)

    # Safety of the newly formed group.
    liberty_count = len(new_liberties)
    if liberty_count == 1:
        score -= 1750.0 + 85.0 * min(len(new_group), 20)
        if capture_count >= 3:
            score += 280.0
    elif liberty_count == 2:
        score -= 105.0 + 9.0 * min(len(new_group), 15)
        if attacked_groups:
            score += 35.0
    elif liberty_count == 3:
        score += 20.0
    else:
        score += min(55.0, 10.0 * liberty_count)

    occupied = me | opponent
    score += _opening_score(p, occupied, stone_count)
    score += _positional_score(p, me, opponent, stone_count)

    # Avoid wasting moves inside established territory.
    region_size, borders_me, borders_opponent = regions[p]
    if not tactical and region_size <= 45:
        if borders_me and not borders_opponent:
            score -= 900.0 + max(0, 18 - region_size) * 12.0
        elif borders_opponent and not borders_me:
            if region_size <= 5:
                score -= 610.0
            elif region_size <= 10:
                score -= 130.0
            else:
                score += min(95.0, 3.0 * region_size)

    if not capture_count and _is_own_eye(p, me, opponent):
        score -= 4300.0

    # Penalize filling a completely surrounded friendly point even if diagonal
    # defects prevent it from being classified as a full eye.
    if not capture_count:
        orthogonal = list(_neighbors(p))
        if orthogonal and all(q in me for q in orthogonal):
            score -= 720.0

    # Small deterministic tie breaker, dependent on the board position.
    z = (
        fingerprint
        ^ ((p[0] + 1) * 0x9E3779B1)
        ^ ((p[1] + 1) * 0x85EBCA77)
    ) & 0xFFFFFFFF
    z ^= z >> 16
    z = (z * 0x7FEB352D) & 0xFFFFFFFF
    z ^= z >> 15
    score += (z & 1023) / 4096.0

    return score


def _policy_impl(
    me_list: List[Tuple[int, int]],
    opponent_list: List[Tuple[int, int]],
) -> Tuple[int, int]:
    me: Set[Point] = {(r - 1, c - 1) for r, c in me_list}
    opponent: Set[Point] = {
        (r - 1, c - 1) for r, c in opponent_list
    }

    occupied = me | opponent
    if len(occupied) >= SIZE * SIZE:
        return (0, 0)

    my_groups, my_map = _build_groups(me, occupied)
    opponent_groups, opponent_map = _build_groups(opponent, occupied)
    regions = _empty_regions(me, opponent)

    fingerprint = 0xA5B35705
    for r, c in me:
        fingerprint ^= (
            ((r + 1) * 0x9E3779B1) + ((c + 1) * 0x85EBCA77)
        ) & 0xFFFFFFFF
    for r, c in opponent:
        fingerprint ^= (
            ((r + 1) * 0xC2B2AE3D) + ((c + 1) * 0x27D4EB2F)
        ) & 0xFFFFFFFF

    best_move = None
    best_score = float("-inf")
    stone_count = len(occupied)

    for r in range(SIZE):
        for c in range(SIZE):
            p = (r, c)
            if p in occupied:
                continue

            analysis = _analyze_move(
                p,
                me,
                opponent,
                my_groups,
                my_map,
                opponent_groups,
                opponent_map,
            )
            if analysis is None:
                continue

            # Avoid a move that could be an illegal immediate ko recapture.
            if analysis[6]:
                continue

            score = _score_move(
                p,
                analysis,
                me,
                opponent,
                my_groups,
                opponent_groups,
                regions,
                stone_count,
                fingerprint,
            )

            if score > best_score:
                best_score = score
                best_move = p

    if best_move is None:
        return (0, 0)

    # Pass rather than fill eyes, make severe self-atari, or play inside
    # settled territory. A lower threshold is used once the board is mature.
    if best_score < -900.0:
        return (0, 0)
    if stone_count > 150 and best_score < -120.0:
        return (0, 0)

    return best_move[0] + 1, best_move[1] + 1


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
) -> tuple[int, int]:
    try:
        return _policy_impl(me, opponent)
    except Exception:
        # Passing is always the safest legal fallback.
        return (0, 0)
