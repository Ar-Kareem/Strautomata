
from __future__ import annotations

import math


SIZE = 19
POINTS = SIZE * SIZE


def _index(row: int, col: int) -> int:
    return row * SIZE + col


NEIGHBORS: list[tuple[int, ...]] = []
DIAGONALS: list[tuple[int, ...]] = []

for _r in range(SIZE):
    for _c in range(SIZE):
        ns = []
        ds = []

        if _r > 0:
            ns.append(_index(_r - 1, _c))
        if _r + 1 < SIZE:
            ns.append(_index(_r + 1, _c))
        if _c > 0:
            ns.append(_index(_r, _c - 1))
        if _c + 1 < SIZE:
            ns.append(_index(_r, _c + 1))

        for _dr, _dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            _rr = _r + _dr
            _cc = _c + _dc
            if 0 <= _rr < SIZE and 0 <= _cc < SIZE:
                ds.append(_index(_rr, _cc))

        NEIGHBORS.append(tuple(ns))
        DIAGONALS.append(tuple(ds))


INFLUENCE_OFFSETS: list[tuple[int, int, float]] = []
_INFLUENCE_WEIGHTS = {
    1: 11.0,
    2: 7.0,
    3: 4.5,
    4: 2.5,
    5: 1.3,
    6: 0.6,
}

for _dr in range(-6, 7):
    for _dc in range(-6, 7):
        _distance = abs(_dr) + abs(_dc)
        if 1 <= _distance <= 6:
            INFLUENCE_OFFSETS.append(
                (_dr, _dc, _INFLUENCE_WEIGHTS[_distance])
            )


# A group is represented as:
# (color, tuple_of_stones, frozenset_of_liberties)
def _analyse_groups(board: bytearray):
    group_id = [-1] * POINTS
    groups = []

    for start in range(POINTS):
        color = board[start]
        if color == 0 or group_id[start] != -1:
            continue

        gid = len(groups)
        queue = [start]
        group_id[start] = gid
        stones = []
        liberties = set()
        qpos = 0

        while qpos < len(queue):
            point = queue[qpos]
            qpos += 1
            stones.append(point)

            for neighbor in NEIGHBORS[point]:
                value = board[neighbor]
                if value == 0:
                    liberties.add(neighbor)
                elif value == color and group_id[neighbor] == -1:
                    group_id[neighbor] = gid
                    queue.append(neighbor)

        groups.append((color, tuple(stones), frozenset(liberties)))

    return group_id, groups


def _play_move(
    board: bytearray,
    point: int,
    group_id: list[int],
    groups,
):
    """Play a move for color 1. Return None if it is suicide."""
    if board[point] != 0:
        return None

    captured_group_ids = set()

    for neighbor in NEIGHBORS[point]:
        if board[neighbor] != 2:
            continue

        gid = group_id[neighbor]
        if gid < 0 or gid in captured_group_ids:
            continue

        liberties = groups[gid][2]
        if len(liberties) == 1 and point in liberties:
            captured_group_ids.add(gid)

    result = bytearray(board)
    result[point] = 1
    captured = 0

    for gid in captured_group_ids:
        for stone in groups[gid][1]:
            result[stone] = 0
            captured += 1

    # Determine the complete new friendly group and its liberties.
    queue = [point]
    visited = {point}
    liberties = set()
    qpos = 0

    while qpos < len(queue):
        current = queue[qpos]
        qpos += 1

        for neighbor in NEIGHBORS[current]:
            value = result[neighbor]
            if value == 0:
                liberties.add(neighbor)
            elif value == 1 and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    if not liberties:
        return None

    return (
        result,
        captured,
        len(visited),
        liberties,
        captured_group_ids,
    )


def _territory_region_penalties(board: bytearray) -> list[float]:
    """
    Identify small or medium empty regions surrounded by one side.

    This is deliberately conservative: very large regions are treated as open
    board rather than established territory.
    """
    penalties = [0.0] * POINTS
    visited = [False] * POINTS

    for start in range(POINTS):
        if board[start] != 0 or visited[start]:
            continue

        queue = [start]
        visited[start] = True
        region = []
        boundary_colors = set()
        qpos = 0

        while qpos < len(queue):
            point = queue[qpos]
            qpos += 1
            region.append(point)

            for neighbor in NEIGHBORS[point]:
                value = board[neighbor]
                if value == 0:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
                else:
                    boundary_colors.add(value)

        region_size = len(region)
        penalty = 0.0

        # Huge connected regions are normally still open board.
        if region_size <= 70:
            if boundary_colors == {1}:
                if region_size <= 2:
                    penalty = -90.0
                elif region_size <= 6:
                    penalty = -55.0
                elif region_size <= 16:
                    penalty = -34.0
                else:
                    penalty = -22.0
            elif boundary_colors == {2}:
                if region_size <= 4:
                    penalty = -70.0
                elif region_size <= 10:
                    penalty = -22.0
                elif region_size <= 24:
                    penalty = -5.0
                else:
                    penalty = 1.0
            elif boundary_colors == {1, 2}:
                penalty = 3.0

        for point in region:
            penalties[point] = penalty

    return penalties


def _influence_maps(board: bytearray):
    own = [0.0] * POINTS
    enemy = [0.0] * POINTS

    for point, color in enumerate(board):
        if color == 0:
            continue

        row, col = divmod(point, SIZE)
        target = own if color == 1 else enemy

        for dr, dc, weight in INFLUENCE_OFFSETS:
            rr = row + dr
            cc = col + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                target[_index(rr, cc)] += weight

    return own, enemy


def _corner_information(board: bytearray):
    """
    Return local stone coordinates for each of the four 7x7 corner areas.

    Local coordinates count from the corresponding pair of board edges.
    """
    corners = [[], [], [], []]

    for point, color in enumerate(board):
        if color == 0:
            continue

        row, col = divmod(point, SIZE)
        coordinates = (
            (row + 1, col + 1),
            (row + 1, SIZE - col),
            (SIZE - row, col + 1),
            (SIZE - row, SIZE - col),
        )

        for corner_id, (a, b) in enumerate(coordinates):
            if a <= 7 and b <= 7:
                corners[corner_id].append((a, b, color))

    return corners


def _corner_bonus(
    point: int,
    corner_info,
    occupied_count: int,
) -> float:
    if occupied_count >= 65:
        return 0.0

    row, col = divmod(point, SIZE)
    coordinates = (
        (row + 1, col + 1),
        (row + 1, SIZE - col),
        (SIZE - row, col + 1),
        (SIZE - row, SIZE - col),
    )

    bonus = 0.0

    for corner_id, (a, b) in enumerate(coordinates):
        if a > 8 or b > 8:
            continue

        stones = corner_info[corner_id]
        own_stones = [(x, y) for x, y, color in stones if color == 1]
        enemy_stones = [(x, y) for x, y, color in stones if color == 2]

        if not stones:
            if (a, b) == (4, 4):
                bonus += 43.0
            elif sorted((a, b)) == [3, 4]:
                bonus += 34.0
            elif (a, b) == (3, 3):
                bonus += 19.0
            elif sorted((a, b)) == [4, 5]:
                bonus += 9.0

        elif enemy_stones and not own_stones:
            nearest = min(
                abs(a - x) + abs(b - y) for x, y in enemy_stones
            )
            if 3 <= nearest <= 4 and 2 <= a <= 8 and 2 <= b <= 8:
                bonus += 14.0
            elif nearest == 2:
                bonus += 5.0

        elif own_stones and not enemy_stones:
            # Encourage a light corner extension after claiming the corner.
            if (a == 4 and 6 <= b <= 8) or (b == 4 and 6 <= a <= 8):
                bonus += 7.0

    return bonus


def _edge_bonus(point: int) -> float:
    row, col = divmod(point, SIZE)
    edge_distance = min(row, col, SIZE - 1 - row, SIZE - 1 - col)

    values = (
        -18.0,  # first line
        -8.0,   # second line
        8.0,    # third line
        13.0,   # fourth line
        10.0,
        8.0,
        7.0,
        6.0,
        5.0,
        4.0,
    )
    return values[min(edge_distance, len(values) - 1)]


def _policy_impl(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    board = bytearray(POINTS)

    for row, col in me:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[_index(row - 1, col - 1)] = 1

    for row, col in opponent:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[_index(row - 1, col - 1)] = 2

    current_position = bytes(board)
    occupied_count = len(me) + len(opponent)

    old_history = memory.get("_history", set())
    if isinstance(old_history, set):
        history = set(old_history)
    elif isinstance(old_history, (list, tuple)):
        history = set(old_history)
    else:
        history = set()

    history.add(current_position)

    last_after = memory.get("_last_after")
    opponent_passed = (
        isinstance(last_after, (bytes, bytearray))
        and bytes(last_after) == current_position
    )

    group_id, groups = _analyse_groups(board)

    save_at = [[] for _ in range(POINTS)]
    defend_at = [[] for _ in range(POINTS)]
    attack_at = [[] for _ in range(POINTS)]

    for gid, (color, stones, liberties) in enumerate(groups):
        liberty_count = len(liberties)

        if color == 1:
            if liberty_count == 1:
                liberty = next(iter(liberties))
                save_at[liberty].append(gid)
            elif liberty_count == 2:
                for liberty in liberties:
                    defend_at[liberty].append(gid)
        else:
            if liberty_count == 2:
                for liberty in liberties:
                    attack_at[liberty].append(gid)

    region_penalty = _territory_region_penalties(board)
    own_influence, enemy_influence = _influence_maps(board)
    corner_info = _corner_information(board)

    # A stable, position-dependent tie breaker.
    seed = 0
    for point, value in enumerate(board):
        if value:
            seed = (seed * 131 + (point + 1) * (value + 3)) % 1000003

    best_point = None
    best_result = None
    best_score = -float("inf")
    best_tactical = False

    side_points = {
        _index(3, 9),
        _index(9, 3),
        _index(9, 15),
        _index(15, 9),
    }
    center_point = _index(9, 9)

    for point in range(POINTS):
        if board[point] != 0:
            continue

        played = _play_move(board, point, group_id, groups)
        if played is None:
            continue

        result, captured, new_group_size, liberties, captured_gids = played
        result_bytes = bytes(result)

        # Avoid all known repetitions. This includes ordinary ko.
        if result_bytes in history:
            continue

        liberty_count = len(liberties)
        score = 0.0
        tactical = False

        # Broad positional considerations.
        score += _edge_bonus(point)
        score += region_penalty[point]
        score += _corner_bonus(point, corner_info, occupied_count)

        if occupied_count < 36:
            if point in side_points:
                score += 11.0
            elif point == center_point:
                score += 7.0

        own_inf = own_influence[point]
        enemy_inf = enemy_influence[point]
        total_inf = own_inf + enemy_inf

        if own_inf > 0.0 and enemy_inf > 0.0:
            score += min(17.0, 0.48 * min(own_inf, enemy_inf))
            score += min(5.0, 0.07 * max(own_inf, enemy_inf))
        elif own_inf > 0.0:
            score += min(8.0, 0.30 * own_inf)
        elif enemy_inf > 0.0:
            score += min(7.0, 0.25 * enemy_inf)
        elif occupied_count > 22:
            score -= 5.0

        if total_inf > 34.0:
            score -= 0.38 * (total_inf - 34.0)

        # Captures are the most concrete tactical gain.
        if captured_gids:
            tactical = True
            for gid in captured_gids:
                group_size = len(groups[gid][1])
                score += (
                    75.0
                    + 32.0 * group_size
                    + 6.0 * math.sqrt(group_size)
                )

        # Saving friendly groups in atari.
        for gid in save_at[point]:
            group_size = len(groups[gid][1])
            if liberty_count >= 2:
                tactical = True
                score += 70.0 + 27.0 * group_size
            else:
                score += 8.0 * group_size

        # Extending endangered two-liberty groups into better shape.
        for gid in defend_at[point]:
            group_size = len(groups[gid][1])
            if liberty_count >= 3:
                score += 9.0 + min(42.0, 2.2 * group_size)
            elif liberty_count <= 2:
                score -= min(18.0, 1.2 * group_size)

        # Putting enemy groups into atari.
        for gid in attack_at[point]:
            if gid not in captured_gids:
                group_size = len(groups[gid][1])
                score += 13.0 + min(58.0, 4.3 * group_size)
                tactical = True

        adjacent_own_groups = set()
        adjacent_enemy_groups = set()
        adjacent_empty = 0

        for neighbor in NEIGHBORS[point]:
            value = board[neighbor]
            if value == 0:
                adjacent_empty += 1
            elif value == 1:
                adjacent_own_groups.add(group_id[neighbor])
            else:
                adjacent_enemy_groups.add(group_id[neighbor])

        # Connections and cuts.
        if len(adjacent_own_groups) >= 2:
            sizes = [len(groups[gid][1]) for gid in adjacent_own_groups]
            score += 10.0 * (len(adjacent_own_groups) - 1)
            score += min(30.0, 1.5 * sum(sizes))
            tactical = True
        elif len(adjacent_own_groups) == 1:
            score += 2.0

        if len(adjacent_enemy_groups) >= 2:
            score += 8.0 * (len(adjacent_enemy_groups) - 1)

        # Pressure groups with three liberties without overvaluing contact.
        for gid in adjacent_enemy_groups:
            if gid in captured_gids:
                continue
            enemy_liberties = len(groups[gid][2])
            if enemy_liberties == 3:
                score += 4.0 + min(15.0, 0.8 * len(groups[gid][1]))

        if adjacent_own_groups and adjacent_enemy_groups:
            score += 4.0

        # General shape and liberty quality.
        score += 2.1 * min(liberty_count, 6)

        if adjacent_empty >= 3 and new_group_size <= 3:
            score += 3.0

        # Penalize redundant filling into the side of one existing group.
        if len(adjacent_own_groups) == 1 and len(adjacent_enemy_groups) == 0:
            own_neighbors = sum(
                1 for neighbor in NEIGHBORS[point] if board[neighbor] == 1
            )
            if own_neighbors >= 2:
                score -= 6.0 * (own_neighbors - 1)

        # Self-atari and low-liberty large groups are dangerous.
        if liberty_count == 1:
            penalty = (
                120.0
                + min(190.0, 7.5 * new_group_size)
                - min(105.0, 30.0 * captured)
            )
            score -= max(18.0, penalty)
        elif liberty_count == 2:
            score -= min(62.0, 2.6 * new_group_size)

        # Small deterministic noise only resolves otherwise close choices.
        score += ((point * 73 + seed) % 101) * 0.0001

        if score > best_score:
            best_score = score
            best_point = point
            best_result = result_bytes
            best_tactical = tactical

    new_memory = {
        "_history": history,
        "_turns": int(memory.get("_turns", 0)) + 1,
    }

    if best_point is None:
        new_memory["_last_after"] = current_position
        return (0, 0), new_memory

    # Stop filling settled positions. Passing is especially attractive after
    # an opponent pass because it ends a likely completed game.
    should_pass = False

    if occupied_count > 100 and best_score < -14.0 and not best_tactical:
        should_pass = True
    if occupied_count > 280 and best_score < 0.0 and not best_tactical:
        should_pass = True
    if opponent_passed and occupied_count > 90:
        if best_score < 4.0 and not best_tactical:
            should_pass = True

    if should_pass:
        new_memory["_last_after"] = current_position
        return (0, 0), new_memory

    history.add(best_result)
    new_memory["_history"] = history
    new_memory["_last_after"] = best_result

    row, col = divmod(best_point, SIZE)
    return (row + 1, col + 1), new_memory


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    """
    Select a legal Go move.

    Passing is used as a fail-safe because it is always legal.
    """
    try:
        if not isinstance(memory, dict):
            memory = {}
        return _policy_impl(me, opponent, memory)
    except Exception:
        # A pass guarantees a legal action even if unexpected malformed state
        # or memory is supplied by the environment.
        return (0, 0), memory if isinstance(memory, dict) else {}
