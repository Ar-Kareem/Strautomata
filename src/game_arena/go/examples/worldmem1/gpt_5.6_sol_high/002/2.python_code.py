
from __future__ import annotations

import time
from typing import Optional


SIZE = 19
AREA = SIZE * SIZE

NEIGHBORS: list[tuple[int, ...]] = []
DIAGONALS: list[tuple[int, ...]] = []

for _r in range(SIZE):
    for _c in range(SIZE):
        ns = []
        ds = []

        if _r > 0:
            ns.append((_r - 1) * SIZE + _c)
        if _r + 1 < SIZE:
            ns.append((_r + 1) * SIZE + _c)
        if _c > 0:
            ns.append(_r * SIZE + _c - 1)
        if _c + 1 < SIZE:
            ns.append(_r * SIZE + _c + 1)

        if _r > 0 and _c > 0:
            ds.append((_r - 1) * SIZE + _c - 1)
        if _r > 0 and _c + 1 < SIZE:
            ds.append((_r - 1) * SIZE + _c + 1)
        if _r + 1 < SIZE and _c > 0:
            ds.append((_r + 1) * SIZE + _c - 1)
        if _r + 1 < SIZE and _c + 1 < SIZE:
            ds.append((_r + 1) * SIZE + _c + 1)

        NEIGHBORS.append(tuple(ns))
        DIAGONALS.append(tuple(ds))


def _group_and_liberties(
    board: list[int], start: int
) -> tuple[list[int], set[int]]:
    color = board[start]
    stones = [start]
    liberties: set[int] = set()
    seen = {start}
    pos = 0

    while pos < len(stones):
        point = stones[pos]
        pos += 1

        for neighbor in NEIGHBORS[point]:
            value = board[neighbor]
            if value == 0:
                liberties.add(neighbor)
            elif value == color and neighbor not in seen:
                seen.add(neighbor)
                stones.append(neighbor)

    return stones, liberties


def _all_groups(
    board: list[int], color: int
) -> list[tuple[list[int], set[int]]]:
    visited = [False] * AREA
    result: list[tuple[list[int], set[int]]] = []

    for point in range(AREA):
        if board[point] != color or visited[point]:
            continue

        stones, liberties = _group_and_liberties(board, point)
        for stone in stones:
            visited[stone] = True
        result.append((stones, liberties))

    return result


def _groups_with_map(
    board: list[int], color: int
) -> tuple[list[tuple[list[int], set[int]]], list[int]]:
    groups = _all_groups(board, color)
    group_map = [-1] * AREA

    for group_id, (stones, _) in enumerate(groups):
        for stone in stones:
            group_map[stone] = group_id

    return groups, group_map


def _play(
    board: list[int],
    point: int,
    color: int,
    forbidden: Optional[set[bytes]] = None,
) -> Optional[tuple[list[int], int, list[int], set[int], bytes]]:
    if point < 0 or point >= AREA or board[point] != 0:
        return None

    result = board.copy()
    result[point] = color
    enemy = 3 - color
    captured = 0
    checked: set[int] = set()

    for neighbor in NEIGHBORS[point]:
        if result[neighbor] != enemy or neighbor in checked:
            continue

        stones, liberties = _group_and_liberties(result, neighbor)
        checked.update(stones)

        if not liberties:
            captured += len(stones)
            for stone in stones:
                result[stone] = 0

    own_stones, own_liberties = _group_and_liberties(result, point)
    if not own_liberties:
        return None

    key = bytes(result)
    if forbidden is not None and key in forbidden:
        return None

    return result, captured, own_stones, own_liberties, key


def _empty_regions(
    board: list[int],
) -> tuple[list[int], list[tuple[int, frozenset[int], bool]]]:
    labels = [-1] * AREA
    regions: list[tuple[int, frozenset[int], bool]] = []

    for start in range(AREA):
        if board[start] != 0 or labels[start] != -1:
            continue

        region_id = len(regions)
        points = [start]
        labels[start] = region_id
        borders: set[int] = set()
        touches_edge = False
        pos = 0

        while pos < len(points):
            point = points[pos]
            pos += 1
            row, col = divmod(point, SIZE)

            if row == 0 or row == SIZE - 1 or col == 0 or col == SIZE - 1:
                touches_edge = True

            for neighbor in NEIGHBORS[point]:
                value = board[neighbor]
                if value == 0:
                    if labels[neighbor] == -1:
                        labels[neighbor] = region_id
                        points.append(neighbor)
                else:
                    borders.add(value)

        regions.append((len(points), frozenset(borders), touches_edge))

    return labels, regions


def _opening_bonus(
    point: int,
    board: list[int],
    total_stones: int,
) -> float:
    if total_stones >= 45:
        return 0.0

    row, col = divmod(point, SIZE)
    bonus = 0.0

    # Star points, side star points, and tengen.
    major_points = {
        (3, 3),
        (3, 15),
        (15, 3),
        (15, 15),
    }
    side_points = {
        (3, 9),
        (9, 3),
        (9, 9),
        (9, 15),
        (15, 9),
    }

    if (row, col) in side_points:
        bonus += 8.0 if total_stones < 18 else 2.0

    top = row < 9
    left = col < 9
    row_range = range(0, 9) if top else range(10, 19)
    col_range = range(0, 9) if left else range(10, 19)

    corner_stones: list[tuple[int, int, int]] = []
    for rr in row_range:
        base = rr * SIZE
        for cc in col_range:
            value = board[base + cc]
            if value:
                corner_stones.append((rr, cc, value))

    distance_row = row if top else SIZE - 1 - row
    distance_col = col if left else SIZE - 1 - col

    if not corner_stones:
        if distance_row == 3 and distance_col == 3:
            bonus += 40.0
        elif sorted((distance_row, distance_col)) == [2, 3]:
            bonus += 30.0
        elif distance_row == 2 and distance_col == 2:
            bonus += 20.0
    else:
        opponent_corner_stones = [
            (rr, cc) for rr, cc, value in corner_stones if value == 2
        ]
        own_corner_stones = [
            (rr, cc) for rr, cc, value in corner_stones if value == 1
        ]

        if opponent_corner_stones and not own_corner_stones:
            nearest = min(
                abs(row - rr) + abs(col - cc)
                for rr, cc in opponent_corner_stones
            )
            if (
                2 <= nearest <= 4
                and 2 <= distance_row <= 6
                and 2 <= distance_col <= 6
            ):
                bonus += 10.0

    if (row, col) in major_points and total_stones < 12:
        bonus += 4.0

    return bonus


def _strategic_score(
    board: list[int],
    point: int,
    total_stones: int,
    region_labels: list[int],
    regions: list[tuple[int, frozenset[int], bool]],
) -> float:
    row, col = divmod(point, SIZE)
    edge_distance = min(row, col, SIZE - 1 - row, SIZE - 1 - col)
    line = edge_distance + 1
    score = 0.0

    if line == 1:
        score -= 34.0
    elif line == 2:
        score -= 9.0
    elif line == 3:
        score += 5.0
    elif line == 4:
        score += 8.0
    elif line == 5:
        score += 3.0

    score += _opening_bonus(point, board, total_stones)

    own_influence = 0.0
    opponent_influence = 0.0
    nearest = 100
    nearest_own = 100
    nearest_opponent = 100

    for other, value in enumerate(board):
        if value == 0:
            continue

        rr, cc = divmod(other, SIZE)
        distance = abs(row - rr) + abs(col - cc)

        if distance < nearest:
            nearest = distance

        if value == 1:
            if distance < nearest_own:
                nearest_own = distance
            if distance <= 4:
                own_influence += 5 - distance
        else:
            if distance < nearest_opponent:
                nearest_opponent = distance
            if distance <= 4:
                opponent_influence += 5 - distance

    if total_stones < 50:
        if nearest >= 5:
            score += 7.0
        elif nearest == 2:
            score += 4.0
        elif nearest == 3:
            score += 5.0
    else:
        if nearest > 6:
            score -= 6.0
        elif nearest in (2, 3):
            score += 2.5

    if own_influence > 0 and opponent_influence > 0:
        score += min(own_influence, opponent_influence) * 0.6
    elif own_influence > opponent_influence * 2 + 3:
        score -= min(6.0, (own_influence - opponent_influence) * 0.35)
    elif opponent_influence > own_influence * 2 + 3:
        score += min(4.0, (opponent_influence - own_influence) * 0.2)

    region_id = region_labels[point]
    if region_id >= 0:
        region_size, borders, _ = regions[region_id]

        # Only treat reasonably bounded regions as settled. This avoids
        # considering the entire open board territory in the opening.
        if region_size <= 45:
            if borders == frozenset((1,)):
                score -= 48.0
                if region_size <= 4:
                    score -= 20.0
            elif borders == frozenset((2,)):
                if region_size <= 2:
                    score -= 52.0
                elif region_size <= 5:
                    score -= 22.0
                elif region_size <= 10:
                    score -= 5.0
                else:
                    score += 3.0
            elif borders == frozenset((1, 2)):
                score += 4.0 if total_stones > 80 else 1.0

    return score


def _score_move(
    board: list[int],
    point: int,
    total_stones: int,
    forbidden: set[bytes],
    uncertain_history: bool,
    own_groups: list[tuple[list[int], set[int]]],
    own_map: list[int],
    opponent_groups: list[tuple[list[int], set[int]]],
    opponent_map: list[int],
    region_labels: list[int],
    regions: list[tuple[int, frozenset[int], bool]],
) -> Optional[tuple[float, bytes]]:
    played = _play(board, point, 1, forbidden)
    if played is None:
        return None

    new_board, captured, played_group, played_liberties, key = played

    # If invoked in the middle of a game without history, conservatively
    # reject the characteristic shape of an immediate ko recapture.
    if (
        uncertain_history
        and captured == 1
        and len(played_group) == 1
        and len(played_liberties) == 1
    ):
        return None

    score = _strategic_score(
        board, point, total_stones, region_labels, regions
    )

    score += captured * 50.0
    if captured >= 3:
        score += min(30.0, captured * 2.5)

    adjacent_own_ids = {
        own_map[n]
        for n in NEIGHBORS[point]
        if board[n] == 1 and own_map[n] >= 0
    }
    adjacent_opponent_ids = {
        opponent_map[n]
        for n in NEIGHBORS[point]
        if board[n] == 2 and opponent_map[n] >= 0
    }

    if len(adjacent_own_ids) >= 2:
        score += 9.0 * (len(adjacent_own_ids) - 1)

        connected_size = sum(
            len(own_groups[group_id][0])
            for group_id in adjacent_own_ids
        )
        score += min(14.0, connected_size * 0.8)

    adjacent_own_count = sum(
        1 for neighbor in NEIGHBORS[point] if board[neighbor] == 1
    )
    if adjacent_own_count >= 2 and len(adjacent_own_ids) == 1:
        score -= 5.0

    if len(adjacent_opponent_ids) >= 2:
        score += 6.0 * (len(adjacent_opponent_ids) - 1)

    diagonal_own = sum(
        1 for neighbor in DIAGONALS[point] if board[neighbor] == 1
    )
    score += min(3.0, diagonal_own * 0.8)

    saved_stones = 0
    for group_id, (stones, liberties) in enumerate(own_groups):
        if len(liberties) == 1 and point in liberties:
            saved_stones += len(stones)

    score += min(100.0, saved_stones * 18.0)

    if len(played_liberties) == 2:
        score -= 8.0
    elif len(played_liberties) == 3:
        score += 1.0
    elif len(played_liberties) >= 4:
        score += min(9.0, len(played_liberties) * 1.4)

    # Filling a point entirely surrounded by our stones is generally bad.
    if NEIGHBORS[point] and all(
        board[neighbor] == 1 for neighbor in NEIGHBORS[point]
    ):
        score -= 82.0
        if saved_stones:
            score += 35.0

    new_own_groups = _all_groups(new_board, 1)
    new_opponent_groups = _all_groups(new_board, 2)

    # Determine whether the opponent can immediately capture any group.
    reply_forbidden = set(forbidden)
    reply_forbidden.add(key)
    danger_values: dict[int, float] = {}

    for stones, liberties in new_own_groups:
        if len(liberties) != 1:
            if len(liberties) == 2 and len(stones) >= 4:
                score -= min(10.0, len(stones) * 0.6)
            continue

        liberty = next(iter(liberties))
        reply = _play(new_board, liberty, 2, reply_forbidden)
        if reply is not None:
            reply_captured = reply[1]
            danger = 34.0 + 24.0 * reply_captured
            previous = danger_values.get(liberty, 0.0)
            if danger > previous:
                danger_values[liberty] = danger
        else:
            # Usually a ko-protected atari.
            score -= 2.0

    if danger_values:
        ordered_dangers = sorted(danger_values.values(), reverse=True)
        score -= ordered_dangers[0]
        if len(ordered_dangers) > 1:
            score -= 0.15 * sum(ordered_dangers[1:])

    # Reward newly created ataris, but discount ataris with easy escapes.
    for stones, liberties in new_opponent_groups:
        old_id = opponent_map[stones[0]]
        old_liberty_count = (
            len(opponent_groups[old_id][1]) if old_id >= 0 else 0
        )

        if len(liberties) == 1:
            liberty = next(iter(liberties))
            newly_created = old_liberty_count > 1
            if newly_created:
                atari_value = 13.0 + 8.0 * min(len(stones), 10)
            else:
                atari_value = 2.0 + min(5.0, len(stones))

            escape = _play(new_board, liberty, 2, reply_forbidden)
            if escape is None:
                atari_value += 14.0 + 8.0 * min(len(stones), 8)
            else:
                _, escape_captures, _, escape_liberties, _ = escape
                if escape_captures:
                    atari_value *= 0.35
                elif len(escape_liberties) >= 4:
                    atari_value *= 0.5
                elif len(escape_liberties) >= 3:
                    atari_value *= 0.7

            score += atari_value

        elif len(liberties) == 2 and old_liberty_count >= 3:
            score += 3.0 + min(8.0, len(stones) * 1.2)

    # Small deterministic tie-breaker to avoid repetitive equal choices.
    noise = (
        (point * 1103515245 + total_stones * 12345 + captured * 7919)
        & 1023
    )
    score += noise / 4096.0

    return score, key


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    board = [0] * AREA

    for row, col in me:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[(row - 1) * SIZE + (col - 1)] = 1

    for row, col in opponent:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            point = (row - 1) * SIZE + (col - 1)
            if board[point] == 0:
                board[point] = 2

    total_stones = len(me) + len(opponent)
    current_key = bytes(board)

    output_memory = dict(memory) if isinstance(memory, dict) else {}
    raw_history = output_memory.get("_go_position_history_v3", [])

    history: list[bytes] = []
    if isinstance(raw_history, (list, tuple)):
        for item in raw_history:
            if isinstance(item, bytes) and len(item) == AREA:
                history.append(item)
            elif isinstance(item, bytearray) and len(item) == AREA:
                history.append(bytes(item))

    # A completely empty board indicates a new game.
    if total_stones == 0 and history:
        history = []

    had_valid_history = bool(history)

    if current_key not in history:
        history.append(current_key)

    if len(history) > 1000:
        history = history[-1000:]

    forbidden = set(history)
    uncertain_history = not had_valid_history and total_stones > 2

    own_groups, own_map = _groups_with_map(board, 1)
    opponent_groups, opponent_map = _groups_with_map(board, 2)
    region_labels, regions = _empty_regions(board)

    tactical_priority: set[int] = set()
    secondary_priority: set[int] = set()

    for stones, liberties in own_groups:
        if len(liberties) == 1:
            tactical_priority.update(liberties)
        elif len(liberties) == 2:
            secondary_priority.update(liberties)

    for stones, liberties in opponent_groups:
        if len(liberties) == 1:
            tactical_priority.update(liberties)
        elif len(liberties) == 2:
            secondary_priority.update(liberties)

    standard_points = {
        3 * SIZE + 3,
        3 * SIZE + 15,
        15 * SIZE + 3,
        15 * SIZE + 15,
        3 * SIZE + 9,
        9 * SIZE + 3,
        9 * SIZE + 9,
        9 * SIZE + 15,
        15 * SIZE + 9,
    }

    candidates = [point for point in range(AREA) if board[point] == 0]

    def candidate_priority(point: int) -> tuple[int, int, int]:
        priority = 0

        if point in tactical_priority:
            priority += 10000
        if point in secondary_priority:
            priority += 3000
        if point in standard_points:
            priority += 1500

        occupied_neighbors = sum(
            1 for neighbor in NEIGHBORS[point] if board[neighbor] != 0
        )
        priority += occupied_neighbors * 300

        row, col = divmod(point, SIZE)
        edge_distance = min(row, col, SIZE - 1 - row, SIZE - 1 - col)
        if edge_distance in (2, 3):
            priority += 100

        return priority, -abs(row - 9) - abs(col - 9), -point

    candidates.sort(key=candidate_priority, reverse=True)

    best_point: Optional[int] = None
    best_key: Optional[bytes] = None
    best_score = float("-inf")

    for examined, point in enumerate(candidates):
        if examined > 0 and time.perf_counter() >= deadline:
            break

        evaluated = _score_move(
            board=board,
            point=point,
            total_stones=total_stones,
            forbidden=forbidden,
            uncertain_history=uncertain_history,
            own_groups=own_groups,
            own_map=own_map,
            opponent_groups=opponent_groups,
            opponent_map=opponent_map,
            region_labels=region_labels,
            regions=regions,
        )

        if evaluated is None:
            continue

        score, resulting_key = evaluated

        if score > best_score:
            best_score = score
            best_point = point
            best_key = resulting_key

    should_pass = best_point is None

    # In a developed position, pass rather than fill territory, play a dead
    # invasion, or make another severely damaging move.
    if (
        best_point is not None
        and total_stones > 50
        and best_score < -32.0
    ):
        should_pass = True

    if should_pass:
        action = (0, 0)
        resulting_key = current_key
    else:
        row, col = divmod(best_point, SIZE)
        action = (row + 1, col + 1)
        resulting_key = best_key if best_key is not None else current_key

    if resulting_key not in history:
        history.append(resulting_key)

    if len(history) > 1000:
        history = history[-1000:]

    output_memory["_go_position_history_v3"] = history
    output_memory["_go_last_stone_count_v3"] = total_stones
    output_memory["_go_last_action_v3"] = action

    return action, output_memory
