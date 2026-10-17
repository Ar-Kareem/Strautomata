
BOARD_SIZE = 19
BOARD_AREA = BOARD_SIZE * BOARD_SIZE

_NEIGHBORS = []
for _r in range(BOARD_SIZE):
    for _c in range(BOARD_SIZE):
        _ns = []
        if _r > 0:
            _ns.append((_r - 1) * BOARD_SIZE + _c)
        if _r + 1 < BOARD_SIZE:
            _ns.append((_r + 1) * BOARD_SIZE + _c)
        if _c > 0:
            _ns.append(_r * BOARD_SIZE + _c - 1)
        if _c + 1 < BOARD_SIZE:
            _ns.append(_r * BOARD_SIZE + _c + 1)
        _NEIGHBORS.append(tuple(_ns))


def _build_groups(board):
    group_id = [-1] * BOARD_AREA
    groups = []

    for start in range(BOARD_AREA):
        color = board[start]
        if color < 0 or group_id[start] >= 0:
            continue

        gid = len(groups)
        group_id[start] = gid
        stack = [start]
        stones = []
        liberties = set()

        while stack:
            point = stack.pop()
            stones.append(point)

            for neighbor in _NEIGHBORS[point]:
                value = board[neighbor]
                if value < 0:
                    liberties.add(neighbor)
                elif value == color and group_id[neighbor] < 0:
                    group_id[neighbor] = gid
                    stack.append(neighbor)

        groups.append({
            "color": color,
            "stones": tuple(stones),
            "libs": liberties,
        })

    return group_id, groups


def _empty_components(board):
    component_id = [-1] * BOARD_AREA
    components = []

    for start in range(BOARD_AREA):
        if board[start] >= 0 or component_id[start] >= 0:
            continue

        cid = len(components)
        component_id[start] = cid
        stack = [start]
        points = []
        borders = set()

        while stack:
            point = stack.pop()
            points.append(point)

            for neighbor in _NEIGHBORS[point]:
                value = board[neighbor]
                if value < 0:
                    if component_id[neighbor] < 0:
                        component_id[neighbor] = cid
                        stack.append(neighbor)
                else:
                    borders.add(value)

        components.append({
            "size": len(points),
            "borders": frozenset(borders),
        })

    return component_id, components


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
) -> tuple[int, int]:
    # -1 is empty, 0 is the player to move, and 1 is the opponent.
    board = [-1] * BOARD_AREA

    for row, col in me:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[(row - 1) * BOARD_SIZE + col - 1] = 0

    for row, col in opponent:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[(row - 1) * BOARD_SIZE + col - 1] = 1

    total_stones = sum(1 for value in board if value >= 0)
    group_id, groups = _build_groups(board)
    component_id, components = _empty_components(board)

    # A deterministic position hash supplies tiny tie-breaking variations.
    position_hash = 0x9E3779B97F4A7C15
    for point, value in enumerate(board):
        if value >= 0:
            x = (point + 1) * (0xBF58476D1CE4E5B9 if value == 0
                               else 0x94D049BB133111EB)
            position_hash ^= x & 0xFFFFFFFFFFFFFFFF
            position_hash = (
                (position_hash << 9) | (position_hash >> 55)
            ) & 0xFFFFFFFFFFFFFFFF

    corner_stars = ((3, 3), (3, 15), (15, 3), (15, 15))
    side_stars = ((3, 9), (9, 3), (9, 15), (15, 9), (9, 9))

    corner_data = []
    for star_row, star_col in corner_stars:
        claimed = False
        own_region = 0
        enemy_region = 0

        for point, value in enumerate(board):
            if value < 0:
                continue
            row, col = divmod(point, BOARD_SIZE)
            distance = max(abs(row - star_row), abs(col - star_col))

            if distance <= 3:
                claimed = True
            if distance <= 5:
                if value == 0:
                    own_region += 1
                else:
                    enemy_region += 1

        corner_data.append(
            (star_row, star_col, claimed, own_region, enemy_region)
        )

    best_point = None
    best_score = float("-inf")

    for point in range(BOARD_AREA):
        if board[point] >= 0:
            continue

        row, col = divmod(point, BOARD_SIZE)

        friendly_ids = set()
        enemy_ids = set()
        adjacent_empty = []

        for neighbor in _NEIGHBORS[point]:
            value = board[neighbor]
            if value < 0:
                adjacent_empty.append(neighbor)
            elif value == 0:
                friendly_ids.add(group_id[neighbor])
            else:
                enemy_ids.add(group_id[neighbor])

        captured_ids = []
        captured_stones = []

        for gid in enemy_ids:
            group = groups[gid]
            if len(group["libs"]) == 1 and point in group["libs"]:
                captured_ids.append(gid)
                captured_stones.extend(group["stones"])

        # Compute the liberties of the newly placed stone and every friendly
        # group it joins, after adjacent captures are removed.
        resulting_liberties = set(adjacent_empty)

        for gid in friendly_ids:
            resulting_liberties.update(groups[gid]["libs"])

        resulting_liberties.discard(point)

        captured_set = set(captured_stones)
        if captured_set:
            for captured_point in captured_set:
                for neighbor in _NEIGHBORS[captured_point]:
                    if neighbor == point:
                        resulting_liberties.add(captured_point)
                        break
                    if (
                        board[neighbor] == 0
                        and group_id[neighbor] in friendly_ids
                    ):
                        resulting_liberties.add(captured_point)
                        break

        # Any captured points not adjacent to the resulting friendly group
        # cannot be liberties of that group.
        resulting_liberties.discard(point)

        if not captured_stones and not resulting_liberties:
            # Suicide is illegal.
            continue

        merged_size = 1
        for gid in friendly_ids:
            merged_size += len(groups[gid]["stones"])

        capture_count = len(captured_stones)

        # With no history, an actual simple-ko recapture cannot be identified
        # uniquely. Every forbidden recapture has this characteristic, so
        # conservatively avoid all such moves to guarantee legality.
        possible_ko_recapture = (
            capture_count == 1
            and merged_size == 1
            and len(resulting_liberties) == 1
            and next(iter(resulting_liberties)) == captured_stones[0]
        )
        if possible_ko_recapture:
            continue

        score = 12.0
        liberty_count = len(resulting_liberties)

        # Tactical captures.
        if capture_count:
            score += 100.0 + 190.0 * capture_count
            score += min(300.0, 12.0 * capture_count * capture_count)

            opened_weak_groups = set()
            for captured_point in captured_stones:
                for neighbor in _NEIGHBORS[captured_point]:
                    if board[neighbor] == 0:
                        gid = group_id[neighbor]
                        if len(groups[gid]["libs"]) == 1:
                            opened_weak_groups.add(gid)

            for gid in opened_weak_groups:
                size = len(groups[gid]["stones"])
                score += 120.0 + min(260.0, 42.0 * size)

        # Rescue friendly groups whose last liberty is this move.
        saved_ids = set()
        for gid in friendly_ids:
            group = groups[gid]
            size = len(group["stones"])
            liberties = len(group["libs"])

            if liberties == 1 and point in group["libs"]:
                saved_ids.add(gid)
                score += 220.0 + min(600.0, 120.0 * size)
            elif liberties == 2:
                score += 28.0 + min(70.0, 5.0 * size)
            elif liberties == 3:
                score += 8.0 + min(25.0, 2.0 * size)

        # Create ataris and pressure low-liberty enemy groups.
        atari_count = 0
        for gid in enemy_ids:
            if gid in captured_ids:
                continue

            group = groups[gid]
            liberties = len(group["libs"])
            size = len(group["stones"])

            if point in group["libs"] and liberties == 2:
                atari_count += 1
                score += 78.0 + min(430.0, 30.0 * size)
            elif point in group["libs"] and liberties == 3:
                score += 13.0 + min(60.0, 3.0 * size)

        if atari_count >= 2:
            score += 35.0 * (atari_count - 1)

        # Connections and cuts.
        if len(friendly_ids) >= 2:
            score += 27.0 * (len(friendly_ids) - 1)
            weak_connection = sum(
                1 for gid in friendly_ids if len(groups[gid]["libs"]) <= 3
            )
            score += 16.0 * weak_connection

        if len(enemy_ids) >= 2:
            score += 25.0 * (len(enemy_ids) - 1)

        # Resulting group safety. Self-atari is strongly discouraged.
        if liberty_count == 1:
            score -= 260.0 + min(520.0, 45.0 * merged_size)
            if capture_count:
                score += min(100.0, 20.0 * capture_count)
        elif liberty_count == 2:
            score -= 18.0 + min(90.0, 4.0 * merged_size)
        elif liberty_count >= 4:
            score += min(24.0, 4.0 * (liberty_count - 3))

        # Board-line preferences.
        edge_distance = min(row, col, 18 - row, 18 - col)
        if edge_distance == 0:
            score -= 38.0
        elif edge_distance == 1:
            score -= 10.0
        elif edge_distance == 2:
            score += 11.0
        elif edge_distance == 3:
            score += 18.0
        elif edge_distance == 4:
            score += 8.0

        # Immediate contact and shape.
        own_adjacent = sum(1 for n in _NEIGHBORS[point] if board[n] == 0)
        enemy_adjacent = sum(1 for n in _NEIGHBORS[point] if board[n] == 1)
        score += 4.0 * own_adjacent + 7.0 * enemy_adjacent
        score += 1.5 * len(adjacent_empty)

        # Penalize completing solid 2x2 blocks (empty-triangle-like shape).
        triangle_count = 0
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            r1, c1 = row + dr, col
            r2, c2 = row, col + dc
            rd, cd = row + dr, col + dc
            if (
                0 <= r1 < BOARD_SIZE
                and 0 <= c1 < BOARD_SIZE
                and 0 <= r2 < BOARD_SIZE
                and 0 <= c2 < BOARD_SIZE
                and 0 <= rd < BOARD_SIZE
                and 0 <= cd < BOARD_SIZE
            ):
                p1 = r1 * BOARD_SIZE + c1
                p2 = r2 * BOARD_SIZE + c2
                pd = rd * BOARD_SIZE + cd
                if board[p1] == 0 and board[p2] == 0 and board[pd] == 0:
                    triangle_count += 1
        score -= 19.0 * triangle_count

        # Estimate nearby influence and useful spacing.
        own_influence = 0
        enemy_influence = 0
        nearest_own = 99
        nearest_enemy = 99

        r0 = max(0, row - 5)
        r1 = min(BOARD_SIZE - 1, row + 5)
        c0 = max(0, col - 5)
        c1 = min(BOARD_SIZE - 1, col + 5)

        influence_weights = (0, 12, 7, 4, 2, 1)

        for rr in range(r0, r1 + 1):
            base = rr * BOARD_SIZE
            for cc in range(c0, c1 + 1):
                value = board[base + cc]
                if value < 0:
                    continue

                distance = max(abs(rr - row), abs(cc - col))
                if distance == 0 or distance > 5:
                    continue

                weight = influence_weights[distance]
                if value == 0:
                    own_influence += weight
                    if distance < nearest_own:
                        nearest_own = distance
                else:
                    enemy_influence += weight
                    if distance < nearest_enemy:
                        nearest_enemy = distance

        score += 0.8 * min(15, own_influence, enemy_influence)

        if own_influence > enemy_influence:
            score -= 0.42 * max(
                0, own_influence - enemy_influence - 16
            )
        else:
            score -= 0.42 * max(
                0, enemy_influence - own_influence - 23
            )
            score += 0.30 * min(12, enemy_influence - own_influence)

        if total_stones < 70:
            if 3 <= nearest_own <= 5:
                score += 17.0
            elif nearest_own == 2:
                score += 8.0
            elif nearest_own == 1:
                score += 2.0

            if nearest_enemy == 2:
                score += 22.0
            elif nearest_enemy in (3, 4):
                score += 18.0
            elif nearest_enemy == 5:
                score += 8.0
            elif nearest_enemy == 1:
                score += 8.0

            if nearest_own == 99 and nearest_enemy == 99:
                score += 8.0

        # Fuseki: claim open corners, then make approaches and extensions.
        if total_stones < 55:
            opening_scale = 1.0 if total_stones < 25 else 0.62

            for star_row, star_col, claimed, own_region, enemy_region in corner_data:
                manhattan = abs(row - star_row) + abs(col - star_col)

                if not claimed and manhattan <= 3:
                    score += opening_scale * max(
                        0.0, 105.0 - 25.0 * manhattan
                    )
                elif (
                    enemy_region > 0
                    and own_region == 0
                    and max(abs(row - star_row), abs(col - star_col)) <= 6
                    and nearest_enemy in (3, 4, 5)
                ):
                    score += 22.0
                elif (
                    own_region > 0
                    and enemy_region == 0
                    and max(abs(row - star_row), abs(col - star_col)) <= 7
                    and nearest_own in (3, 4, 5)
                ):
                    score += 13.0

            if (row, col) in side_stars:
                if total_stones >= 6:
                    score += 25.0
                else:
                    score += 8.0

        # Empty-region ownership discourages filling secure territory and
        # hopeless plays inside tiny opposing enclosures.
        cid = component_id[point]
        if cid >= 0:
            component = components[cid]
            region_size = component["size"]
            borders = component["borders"]

            if borders == frozenset((0,)):
                if region_size < 80 or total_stones > 120:
                    score -= 90.0
                    if region_size <= 6:
                        score -= 70.0
            elif borders == frozenset((1,)):
                if region_size <= 4:
                    score -= 105.0
                elif region_size <= 8:
                    score -= 25.0
                elif region_size >= 16:
                    score += 12.0
            elif borders == frozenset((0, 1)) and total_stones > 55:
                score += 7.0

        # Detect likely true eyes of our own color.
        if all(board[n] == 0 for n in _NEIGHBORS[point]):
            enemy_diagonals = 0
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = row + dr, col + dc
                if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                    if board[rr * BOARD_SIZE + cc] == 1:
                        enemy_diagonals += 1

            on_edge = (
                row == 0 or row == 18 or col == 0 or col == 18
            )
            true_eye = (
                enemy_diagonals == 0 if on_edge
                else enemy_diagonals <= 1
            )

            if true_eye:
                score -= 500.0
            else:
                score -= 80.0

        # Small deterministic jitter prevents rigid tie behavior.
        jitter_bits = (
            position_hash
            ^ ((point + 1) * 0xD6E8FEB86659FD93)
        ) & 1023
        score += (jitter_bits / 1023.0 - 0.5) * 2.4

        if score > best_score:
            best_score = score
            best_point = point

    if best_point is None:
        return (0, 0)

    # Pass when only damaging moves remain in a settled position.
    if best_score < -180.0:
        return (0, 0)
    if total_stones > 100 and best_score < -45.0:
        return (0, 0)

    best_row, best_col = divmod(best_point, BOARD_SIZE)
    return (best_row + 1, best_col + 1)
