
from math import sqrt

SIZE = 19
AREA = SIZE * SIZE

ROWS = [i // SIZE + 1 for i in range(AREA)]
COLS = [i % SIZE + 1 for i in range(AREA)]

NEIGHBORS = []
DIAGONALS = []

for i in range(AREA):
    r, c = ROWS[i], COLS[i]
    neighbors = []
    diagonals = []

    if r > 1:
        neighbors.append(i - SIZE)
    if r < SIZE:
        neighbors.append(i + SIZE)
    if c > 1:
        neighbors.append(i - 1)
    if c < SIZE:
        neighbors.append(i + 1)

    if r > 1 and c > 1:
        diagonals.append(i - SIZE - 1)
    if r > 1 and c < SIZE:
        diagonals.append(i - SIZE + 1)
    if r < SIZE and c > 1:
        diagonals.append(i + SIZE - 1)
    if r < SIZE and c < SIZE:
        diagonals.append(i + SIZE + 1)

    NEIGHBORS.append(tuple(neighbors))
    DIAGONALS.append(tuple(diagonals))


STAR_POINTS = {
    (4, 4), (4, 16), (16, 4), (16, 16)
}

THREE_FOUR_POINTS = {
    (3, 4), (4, 3),
    (3, 16), (4, 17),
    (17, 4), (16, 3),
    (17, 16), (16, 17),
}

SIDE_STAR_POINTS = {
    (4, 10), (10, 4), (10, 16), (16, 10)
}


def _analyze(board):
    """Return group id per point and (color, stones, liberties) per group."""
    group_ids = [-1] * AREA
    groups = []

    for start in range(AREA):
        color = board[start]
        if color == 0 or group_ids[start] != -1:
            continue

        gid = len(groups)
        group_ids[start] = gid
        stack = [start]
        stones = []
        liberties = set()

        while stack:
            point = stack.pop()
            stones.append(point)

            for neighbor in NEIGHBORS[point]:
                value = board[neighbor]
                if value == 0:
                    liberties.add(neighbor)
                elif value == color and group_ids[neighbor] == -1:
                    group_ids[neighbor] = gid
                    stack.append(neighbor)

        groups.append((color, tuple(stones), frozenset(liberties)))

    return group_ids, groups


def _signature(board):
    value = 2166136261
    for i, stone in enumerate(board):
        if stone:
            value ^= (i + 1) * (stone * 16777619)
            value = (value * 16777619) & 0xFFFFFFFF
    return value


def _corner_zone_count(board, row, col):
    if row <= 7 and col <= 7:
        return sum(
            1 for i, stone in enumerate(board)
            if stone and ROWS[i] <= 7 and COLS[i] <= 7
        )
    if row <= 7 and col >= 13:
        return sum(
            1 for i, stone in enumerate(board)
            if stone and ROWS[i] <= 7 and COLS[i] >= 13
        )
    if row >= 13 and col <= 7:
        return sum(
            1 for i, stone in enumerate(board)
            if stone and ROWS[i] >= 13 and COLS[i] <= 7
        )
    if row >= 13 and col >= 13:
        return sum(
            1 for i, stone in enumerate(board)
            if stone and ROWS[i] >= 13 and COLS[i] >= 13
        )
    return -1


def _positional_score(board, point, color, total_stones):
    row, col = ROWS[point], COLS[point]
    line = min(row, col, 20 - row, 20 - col)

    if line == 1:
        score = -34.0
    elif line == 2:
        score = -11.0
    elif line == 3:
        score = 8.0
    elif line == 4:
        score = 12.0
    elif line == 5:
        score = 7.0
    else:
        score = 2.0

    coordinate = (row, col)
    zone_count = _corner_zone_count(board, row, col)

    if coordinate in STAR_POINTS and zone_count == 0:
        score += 58.0 if total_stones < 16 else 28.0
    elif coordinate in THREE_FOUR_POINTS and zone_count == 0:
        score += 45.0 if total_stones < 16 else 22.0

    if coordinate in SIDE_STAR_POINTS and total_stones < 24:
        score += 19.0
    elif coordinate == (10, 10) and total_stones < 20:
        score += 9.0

    minimum_distance = 99
    friendly_influence = 0.0
    enemy_influence = 0.0

    for other, stone in enumerate(board):
        if stone == 0:
            continue

        distance = max(
            abs(row - ROWS[other]),
            abs(col - COLS[other])
        )

        if distance < minimum_distance:
            minimum_distance = distance

        if distance <= 5:
            influence = 6 - distance
            if stone == color:
                friendly_influence += influence
            else:
                enemy_influence += influence

    if minimum_distance != 99:
        if total_stones < 30:
            score += 2.2 * min(minimum_distance, 8)
        elif total_stones < 100:
            score += 0.8 * min(minimum_distance, 6)

        if minimum_distance == 1:
            score -= 8.0

    score += 0.75 * min(friendly_influence, 12.0)
    score += 0.40 * min(enemy_influence, 10.0)

    if enemy_influence > friendly_influence + 9.0:
        score -= 0.65 * (enemy_influence - friendly_influence - 9.0)

    return score


def _inspect_move(board, point, color, group_ids, groups,
                  total_stones, state_signature):
    """
    Return (heuristic score, captured points), or None if the move is unsafe
    or illegal from the supplied board.
    """
    if point < 0 or point >= AREA or board[point] != 0:
        return None

    enemy = 3 - color
    friendly_ids = set()
    enemy_ids = set()

    for neighbor in NEIGHBORS[point]:
        value = board[neighbor]
        if value == color:
            friendly_ids.add(group_ids[neighbor])
        elif value == enemy:
            enemy_ids.add(group_ids[neighbor])

    captured_ids = {
        gid for gid in enemy_ids
        if len(groups[gid][2]) == 1
    }

    captured = set()
    for gid in captured_ids:
        captured.update(groups[gid][1])

    resulting_stones = {point}
    for gid in friendly_ids:
        resulting_stones.update(groups[gid][1])

    resulting_liberties = set()
    for stone in resulting_stones:
        for neighbor in NEIGHBORS[stone]:
            if neighbor == point:
                continue
            if board[neighbor] == 0 or neighbor in captured:
                resulting_liberties.add(neighbor)

    if not resulting_liberties:
        return None

    # With no history supplied, this exact shape could be an illegal immediate
    # ko recapture. Avoid it rather than risk returning an illegal move.
    if (
        len(captured) == 1
        and len(resulting_stones) == 1
        and len(resulting_liberties) == 1
    ):
        return None

    score = _positional_score(board, point, color, total_stones)

    capture_count = len(captured)
    if capture_count:
        score += 155.0 + 48.0 * capture_count
        score += 10.0 * len(captured_ids)

    result_liberty_count = len(resulting_liberties)
    result_size = len(resulting_stones)

    if result_liberty_count == 1:
        score -= 140.0 + 12.0 * sqrt(result_size)
    elif result_liberty_count == 2:
        score -= 10.0 + 2.5 * sqrt(result_size)
    else:
        score += min(14.0, 2.2 * result_liberty_count)

    # Saving friendly groups whose last liberty is this move.
    for gid in friendly_ids:
        _, stones, liberties = groups[gid]
        if len(liberties) == 1:
            if result_liberty_count >= 2:
                score += 120.0 + 23.0 * len(stones)
            else:
                score += 12.0

    # Connecting separate groups is generally valuable, especially weak ones.
    if len(friendly_ids) >= 2:
        score += 14.0 * (len(friendly_ids) - 1)
        weak_connections = sum(
            1 for gid in friendly_ids if len(groups[gid][2]) <= 3
        )
        score += 7.0 * weak_connections

    # Pressure enemy groups and reward forcing ataris.
    active_enemy_groups = 0
    for gid in enemy_ids:
        if gid in captured_ids:
            continue

        _, stones, liberties = groups[gid]
        old_liberties = len(liberties)
        new_liberties = old_liberties - 1

        if new_liberties == 1:
            score += 34.0 + 12.0 * len(stones)
            active_enemy_groups += 1
        elif new_liberties == 2:
            score += 5.0 + 2.0 * sqrt(len(stones))

    if len(enemy_ids - captured_ids) >= 2:
        score += 9.0 * (len(enemy_ids - captured_ids) - 1)

    adjacent_friendly = sum(
        1 for neighbor in NEIGHBORS[point] if board[neighbor] == color
    )
    adjacent_enemy = sum(
        1 for neighbor in NEIGHBORS[point] if board[neighbor] == enemy
    )
    adjacent_empty = sum(
        1 for neighbor in NEIGHBORS[point] if board[neighbor] == 0
    )

    score += 2.0 * adjacent_enemy
    score += 0.7 * adjacent_friendly
    score += 0.8 * adjacent_empty

    # Avoid filling a surrounded friendly point, normally an eye.
    if NEIGHBORS[point] and all(
        board[neighbor] == color for neighbor in NEIGHBORS[point]
    ):
        score -= 165.0

    # Mild empty-triangle penalty.
    friendly_diagonals = sum(
        1 for diagonal in DIAGONALS[point] if board[diagonal] == color
    )
    if adjacent_friendly >= 2 and friendly_diagonals:
        score -= 7.0

    # Stable deterministic tie-breaking.
    jitter = (
        ((point + 1) * 1103515245 + state_signature * 12345) & 1023
    ) / 100000.0
    score += jitter

    return score, captured


def _play(board, point, color, captured):
    new_board = board[:]
    new_board[point] = color
    for stone in captured:
        new_board[stone] = 0
    return new_board


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [0] * AREA

    for row, col in me:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            board[(row - 1) * SIZE + (col - 1)] = 1

    for row, col in opponent:
        if 1 <= row <= SIZE and 1 <= col <= SIZE:
            point = (row - 1) * SIZE + (col - 1)
            if board[point] == 0:
                board[point] = 2

    total_stones = sum(1 for stone in board if stone)
    group_ids, groups = _analyze(board)
    state_signature = _signature(board)

    candidates = []

    for point in range(AREA):
        if board[point] != 0:
            continue

        result = _inspect_move(
            board,
            point,
            1,
            group_ids,
            groups,
            total_stones,
            state_signature,
        )

        if result is not None:
            score, captured = result
            candidates.append((score, point, captured))

    if not candidates:
        return (0, 0)

    candidates.sort(key=lambda item: item[0], reverse=True)

    # If every remaining move is severely destructive, pass.
    if candidates[0][0] < -75.0:
        return (0, 0)

    # Search opponent responses for the strongest static candidates.
    search_width = min(16, len(candidates))
    best_value = float("-inf")
    best_point = candidates[0][1]

    for base_score, point, captured in candidates[:search_width]:
        next_board = _play(board, point, 1, captured)
        next_total = total_stones + 1 - len(captured)
        next_group_ids, next_groups = _analyze(next_board)
        next_signature = _signature(next_board)

        opponent_best = 0.0  # Passing is always available.

        for reply in range(AREA):
            if next_board[reply] != 0:
                continue

            reply_result = _inspect_move(
                next_board,
                reply,
                2,
                next_group_ids,
                next_groups,
                next_total,
                next_signature,
            )

            if reply_result is not None:
                reply_score = reply_result[0]
                if reply_score > opponent_best:
                    opponent_best = reply_score

        value = base_score - 0.72 * opponent_best

        if value > best_value:
            best_value = value
            best_point = point

    return (ROWS[best_point], COLS[best_point])
