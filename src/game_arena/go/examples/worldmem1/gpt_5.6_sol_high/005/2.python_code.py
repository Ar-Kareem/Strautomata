
BOARD_SIZE = 19
BOARD_AREA = BOARD_SIZE * BOARD_SIZE

_NEIGHBORS = []
_DIAGONALS = []

for _p in range(BOARD_AREA):
    _r, _c = divmod(_p, BOARD_SIZE)

    _ns = []
    if _r > 0:
        _ns.append(_p - BOARD_SIZE)
    if _r + 1 < BOARD_SIZE:
        _ns.append(_p + BOARD_SIZE)
    if _c > 0:
        _ns.append(_p - 1)
    if _c + 1 < BOARD_SIZE:
        _ns.append(_p + 1)
    _NEIGHBORS.append(tuple(_ns))

    _ds = []
    if _r > 0 and _c > 0:
        _ds.append(_p - BOARD_SIZE - 1)
    if _r > 0 and _c + 1 < BOARD_SIZE:
        _ds.append(_p - BOARD_SIZE + 1)
    if _r + 1 < BOARD_SIZE and _c > 0:
        _ds.append(_p + BOARD_SIZE - 1)
    if _r + 1 < BOARD_SIZE and _c + 1 < BOARD_SIZE:
        _ds.append(_p + BOARD_SIZE + 1)
    _DIAGONALS.append(tuple(_ds))


def _position_key(board):
    """Compact positional-superko key from the fixed player's perspective."""
    mine = 0
    theirs = 0
    for p, value in enumerate(board):
        if value == 1:
            mine |= 1 << p
        elif value == -1:
            theirs |= 1 << p
    return mine, theirs


def _analyse(board):
    """
    Return all groups and a point-to-group map.

    A group is represented as:
        (color, tuple_of_stones, frozenset_of_liberties)
    """
    group_map = [-1] * BOARD_AREA
    groups = []

    for start in range(BOARD_AREA):
        color = board[start]
        if color == 0 or group_map[start] != -1:
            continue

        gid = len(groups)
        group_map[start] = gid
        stack = [start]
        stones = []
        liberties = set()

        while stack:
            p = stack.pop()
            stones.append(p)

            for q in _NEIGHBORS[p]:
                value = board[q]
                if value == 0:
                    liberties.add(q)
                elif value == color and group_map[q] == -1:
                    group_map[q] = gid
                    stack.append(q)

        groups.append((color, tuple(stones), frozenset(liberties)))

    return groups, group_map


def _simulate_move(board, point, groups, group_map):
    """
    Play a move for color 1. Returns:
        (new_board, captured_count, new_group_stones, new_group_liberties)
    or None if the move is occupied or suicidal.
    """
    if point < 0 or point >= BOARD_AREA or board[point] != 0:
        return None

    new_board = board[:]
    new_board[point] = 1

    enemy_groups = set()
    for q in _NEIGHBORS[point]:
        if board[q] == -1:
            enemy_groups.add(group_map[q])

    captured = 0
    for gid in enemy_groups:
        color, stones, liberties = groups[gid]
        if color == -1 and len(liberties) == 1 and point in liberties:
            captured += len(stones)
            for stone in stones:
                new_board[stone] = 0

    stack = [point]
    seen = {point}
    own_stones = []
    own_liberties = set()

    while stack:
        p = stack.pop()
        own_stones.append(p)

        for q in _NEIGHBORS[p]:
            value = new_board[q]
            if value == 0:
                own_liberties.add(q)
            elif value == 1 and q not in seen:
                seen.add(q)
                stack.append(q)

    if not own_liberties:
        return None

    return new_board, captured, own_stones, own_liberties


def _tension_value(groups):
    """
    Evaluate tactical pressure in a position. Positive values favor us.
    Only low-liberty groups are included so settled groups do not dominate.
    """
    value = 0.0

    for color, stones, liberties in groups:
        size = len(stones)
        liberty_count = len(liberties)

        if liberty_count == 1:
            amount = 14.0 + 7.5 * size
            value += amount if color == -1 else -amount
        elif liberty_count == 2:
            amount = 1.2 * min(size, 12)
            value += amount if color == -1 else -amount

    return value


def _opening_shape_value(row, col, occupied):
    """Opening preference for useful lines and standard corner points."""
    phase = max(0.0, min(1.0, (75.0 - occupied) / 75.0))
    if phase <= 0.0:
        return 0.0

    edge_distance = min(row, col, 18 - row, 18 - col)
    line_values = {
        0: -11.0,
        1: -5.0,
        2: 2.0,
        3: 6.5,
        4: 4.0,
    }
    value = line_values.get(edge_distance, 1.5) * phase

    # 4-4 points.
    if row in (3, 15) and col in (3, 15):
        value += 13.0 * phase

    # Detect coordinates relative to the nearest corner.
    vertical_corner_distance = min(row, 18 - row)
    horizontal_corner_distance = min(col, 18 - col)
    corner_shape = sorted(
        (vertical_corner_distance, horizontal_corner_distance)
    )

    # 3-4 and 4-3 points.
    if corner_shape == [2, 3]:
        value += 8.5 * phase
    # 3-3 points are useful, but normally less urgent than 4-4.
    elif corner_shape == [2, 2]:
        value += 5.5 * phase

    return value


def _influence_at(point, stones):
    """
    Approximate local influence. Positive is friendly, negative is opposing.
    """
    row, col = divmod(point, BOARD_SIZE)
    influence = 0.0
    nearest = 99

    weights = {
        1: 7.0,
        2: 3.8,
        3: 2.1,
        4: 1.2,
        5: 0.7,
        6: 0.35,
    }

    for q, color in stones:
        qr, qc = divmod(q, BOARD_SIZE)
        distance = abs(row - qr) + abs(col - qc)
        if distance < nearest:
            nearest = distance
        if distance <= 6:
            influence += color * weights.get(distance, 0.0)

    return influence, nearest


def _score_move(
    board,
    point,
    new_board,
    captured,
    own_stones,
    own_liberties,
    groups,
    group_map,
    before_tension,
    occupied,
    all_stones,
    seed,
):
    """Heuristic evaluation of one already-verified legal move."""
    score = 0.0
    tactical = False
    saves = 0
    attacks = 0

    own_liberty_count = len(own_liberties)
    own_size = len(own_stones)

    friendly_groups = set()
    enemy_groups = set()
    friendly_neighbors = 0
    enemy_neighbors = 0
    empty_neighbors = 0

    for q in _NEIGHBORS[point]:
        if board[q] == 1:
            friendly_neighbors += 1
            friendly_groups.add(group_map[q])
        elif board[q] == -1:
            enemy_neighbors += 1
            enemy_groups.add(group_map[q])
        else:
            empty_neighbors += 1

    # Captures receive the strongest immediate reward.
    if captured:
        tactical = True
        score += 39.0 * captured + 8.0

    # Saving adjacent friendly groups that were in atari.
    for gid in friendly_groups:
        color, stones, liberties = groups[gid]
        if color == 1 and len(liberties) == 1 and point in liberties:
            if own_liberty_count >= 2:
                saves += len(stones)
                tactical = True
                score += 25.0 + 7.0 * len(stones)

    # Attack enemy groups by removing liberties.
    for gid in enemy_groups:
        color, stones, liberties = groups[gid]
        if color != -1 or point not in liberties:
            continue

        if len(liberties) == 2:
            attacks += len(stones)
            tactical = True
            score += 11.0 + 3.5 * len(stones)
        elif len(liberties) == 3:
            score += 2.5 + min(5.0, 0.7 * len(stones))

    # Connecting independent friendly groups and splitting enemy groups.
    if len(friendly_groups) >= 2:
        score += 6.0 * (len(friendly_groups) - 1)
    if len(enemy_groups) >= 2:
        score += 3.5 * (len(enemy_groups) - 1)

    # Immediate quality of the newly formed group.
    score += 1.2 * min(own_liberty_count, 6)

    if own_liberty_count == 1:
        # Usually reject self-atari, even when technically legal.
        score -= 50.0 + 7.0 * min(own_size, 15)
        if not captured:
            score -= 15.0
    elif own_liberty_count == 2:
        score -= 3.0 + 0.8 * min(own_size, 12)
    elif own_liberty_count >= 4:
        score += 1.5

    after_groups, _ = _analyse(new_board)
    score += _tension_value(after_groups) - before_tension

    row, col = divmod(point, BOARD_SIZE)

    # Avoid filling a friendly eye.
    if _NEIGHBORS[point] and all(board[q] == 1 for q in _NEIGHBORS[point]):
        opposing_diagonals = sum(
            1 for q in _DIAGONALS[point] if board[q] == -1
        )
        on_edge = row in (0, 18) or col in (0, 18)

        true_eye = (
            opposing_diagonals == 0
            if on_edge
            else opposing_diagonals <= 1
        )
        score -= 95.0 if true_eye else 25.0

    # Diagonal friendly stones provide useful shape support.
    friendly_diagonals = sum(
        1 for q in _DIAGONALS[point] if board[q] == 1
    )
    score += 0.55 * friendly_diagonals

    # Opening line and corner preferences.
    score += _opening_shape_value(row, col, occupied)

    opening_phase = max(0.0, min(1.0, (65.0 - occupied) / 65.0))

    # Local influence and spacing.
    influence, nearest = _influence_at(point, all_stones)

    if nearest == 99:
        nearest = 10

    if opening_phase > 0.0:
        score += 0.65 * min(nearest, 10) * opening_phase

        # Increase the preference for an unoccupied corner area.
        if row in (3, 15) and col in (3, 15):
            nearby = 0
            for q, _color in all_stones:
                qr, qc = divmod(q, BOARD_SIZE)
                if max(abs(row - qr), abs(col - qc)) <= 5:
                    nearby += 1
            score += max(0.0, 8.0 - 1.6 * nearby) * opening_phase

    # Filling strongly controlled friendly territory is usually wasteful.
    if influence > 10.0 and enemy_neighbors == 0 and not tactical:
        score -= 0.7 * (influence - 9.0)

    # Discourage unsupported, excessively deep invasions.
    if influence < -13.0 and own_liberty_count <= 2 and not captured:
        score -= 0.8 * (-influence - 12.0)

    # Slightly prefer boundaries between the two spheres of influence.
    score += max(0.0, 4.5 - abs(influence)) * 0.23

    # A tiny deterministic perturbation prevents excessive fixed tie patterns.
    noise_value = (
        ((point + 1) * 1103515245)
        ^ (seed & 0xFFFFFFFF)
        ^ ((seed >> 32) & 0xFFFFFFFF)
    ) & 1023
    score += noise_value / 4096.0

    metadata = {
        "captured": captured,
        "saves": saves,
        "attacks": attacks,
        "tactical": tactical,
        "liberties": own_liberty_count,
    }
    return score, metadata


def _normalize_history(raw_history):
    history = []
    if not isinstance(raw_history, (list, tuple)):
        return history

    for item in raw_history:
        if (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and isinstance(item[0], int)
            and isinstance(item[1], int)
        ):
            history.append((item[0], item[1]))

    return history[-600:]


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict,
) -> tuple[tuple[int, int], dict]:
    board = [0] * BOARD_AREA

    for row, col in me:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[(row - 1) * BOARD_SIZE + (col - 1)] = 1

    for row, col in opponent:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[(row - 1) * BOARD_SIZE + (col - 1)] = -1

    occupied = len(me) + len(opponent)
    current_key = _position_key(board)

    if not isinstance(memory, dict):
        memory = {}

    history = _normalize_history(memory.get("history", []))

    last_result_raw = memory.get("last_result")
    last_result = None
    if (
        isinstance(last_result_raw, (list, tuple))
        and len(last_result_raw) == 2
        and isinstance(last_result_raw[0], int)
        and isinstance(last_result_raw[1], int)
    ):
        last_result = (last_result_raw[0], last_result_raw[1])

    # An empty board normally indicates the start of a new game.
    if occupied == 0:
        history = []
        last_result = None

    opponent_passed = last_result is not None and last_result == current_key

    history_set = set(history)
    if current_key not in history_set:
        history.append(current_key)
        history_set.add(current_key)

    groups, group_map = _analyse(board)
    before_tension = _tension_value(groups)

    all_stones = [
        (point, color)
        for point, color in enumerate(board)
        if color != 0
    ]

    seed = current_key[0] ^ (current_key[1] << 1)

    best_point = None
    best_board = None
    best_key = None
    best_score = float("-inf")
    best_metadata = None

    for point in range(BOARD_AREA):
        if board[point] != 0:
            continue

        result = _simulate_move(board, point, groups, group_map)
        if result is None:
            continue

        new_board, captured, own_stones, own_liberties = result
        result_key = _position_key(new_board)

        # Positional-superko avoidance also handles ordinary ko.
        if result_key in history_set:
            continue

        score, metadata = _score_move(
            board=board,
            point=point,
            new_board=new_board,
            captured=captured,
            own_stones=own_stones,
            own_liberties=own_liberties,
            groups=groups,
            group_map=group_map,
            before_tension=before_tension,
            occupied=occupied,
            all_stones=all_stones,
            seed=seed,
        )

        if score > best_score:
            best_score = score
            best_point = point
            best_board = new_board
            best_key = result_key
            best_metadata = metadata

    # Passing is always the safe fallback if no legal board move remains.
    should_pass = best_point is None

    # If the opponent has passed in a mature position, pass when there is no
    # meaningful capture, rescue, attack, or worthwhile neutral move.
    if (
        not should_pass
        and opponent_passed
        and occupied >= 190
        and best_metadata is not None
        and best_metadata["captured"] == 0
        and best_metadata["saves"] == 0
        and best_metadata["attacks"] == 0
        and best_score < 5.5
    ):
        should_pass = True

    if should_pass:
        new_memory = {
            "history": history[-600:],
            "last_result": current_key,
            "last_action_pass": True,
        }
        return (0, 0), new_memory

    if best_key not in history_set:
        history.append(best_key)

    row, col = divmod(best_point, BOARD_SIZE)
    action = (row + 1, col + 1)

    new_memory = {
        "history": history[-600:],
        "last_result": best_key,
        "last_action_pass": False,
    }
    return action, new_memory
