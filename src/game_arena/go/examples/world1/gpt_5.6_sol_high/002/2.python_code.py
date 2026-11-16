
import math


BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPPONENT = -1
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]]
) -> tuple[int, int]:
    board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    for row, col in me:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[row - 1][col - 1] = ME

    for row, col in opponent:
        if 1 <= row <= BOARD_SIZE and 1 <= col <= BOARD_SIZE:
            board[row - 1][col - 1] = OPPONENT

    stone_count = sum(
        1
        for row in board
        for value in row
        if value != EMPTY
    )

    def neighbors(row, col):
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                yield nr, nc

    def analyze_groups(color):
        group_id = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        groups = []

        for start_row in range(BOARD_SIZE):
            for start_col in range(BOARD_SIZE):
                if (
                    board[start_row][start_col] != color
                    or group_id[start_row][start_col] != -1
                ):
                    continue

                gid = len(groups)
                stack = [(start_row, start_col)]
                group_id[start_row][start_col] = gid
                members = []
                liberties = set()

                while stack:
                    row, col = stack.pop()
                    members.append((row, col))

                    for nr, nc in neighbors(row, col):
                        value = board[nr][nc]
                        if value == EMPTY:
                            liberties.add((nr, nc))
                        elif value == color and group_id[nr][nc] == -1:
                            group_id[nr][nc] = gid
                            stack.append((nr, nc))

                groups.append({
                    "members": members,
                    "liberties": liberties,
                    "size": len(members),
                })

        return group_id, groups

    my_group_id, my_groups = analyze_groups(ME)
    enemy_group_id, enemy_groups = analyze_groups(OPPONENT)

    # Map empty regions to their size and bordering colors. This helps avoid
    # filling settled friendly territory while rewarding useful endgame plays.
    region_id = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    regions = []

    for start_row in range(BOARD_SIZE):
        for start_col in range(BOARD_SIZE):
            if (
                board[start_row][start_col] != EMPTY
                or region_id[start_row][start_col] != -1
            ):
                continue

            rid = len(regions)
            stack = [(start_row, start_col)]
            region_id[start_row][start_col] = rid
            points = []
            borders = set()

            while stack:
                row, col = stack.pop()
                points.append((row, col))

                for nr, nc in neighbors(row, col):
                    value = board[nr][nc]
                    if value == EMPTY:
                        if region_id[nr][nc] == -1:
                            region_id[nr][nc] = rid
                            stack.append((nr, nc))
                    else:
                        borders.add(value)

            regions.append({
                "size": len(points),
                "borders": borders,
            })

    # Short-range influence fields.
    my_influence = [[0.0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    enemy_influence = [[0.0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    influence_weight = {
        1: 6.0,
        2: 3.0,
        3: 1.4,
        4: 0.6,
        5: 0.25,
    }

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = board[row][col]
            if color == EMPTY:
                continue

            target = my_influence if color == ME else enemy_influence

            for dr in range(-5, 6):
                nr = row + dr
                if not (0 <= nr < BOARD_SIZE):
                    continue
                for dc in range(-5, 6):
                    nc = col + dc
                    if not (0 <= nc < BOARD_SIZE):
                        continue
                    distance = max(abs(dr), abs(dc))
                    if distance in influence_weight:
                        target[nr][nc] += influence_weight[distance]

    def simulate_move(row, col):
        if board[row][col] != EMPTY:
            return None

        adjacent_enemy_groups = set()
        for nr, nc in neighbors(row, col):
            if board[nr][nc] == OPPONENT:
                adjacent_enemy_groups.add(enemy_group_id[nr][nc])

        captured_group_ids = set()
        for gid in adjacent_enemy_groups:
            group = enemy_groups[gid]
            if len(group["liberties"]) == 1 and (row, col) in group["liberties"]:
                captured_group_ids.add(gid)

        new_board = [line[:] for line in board]
        new_board[row][col] = ME
        captured = []

        for gid in captured_group_ids:
            for point in enemy_groups[gid]["members"]:
                pr, pc = point
                new_board[pr][pc] = EMPTY
                captured.append(point)

        stack = [(row, col)]
        seen = {(row, col)}
        own_members = []
        own_liberties = set()

        while stack:
            pr, pc = stack.pop()
            own_members.append((pr, pc))

            for nr, nc in neighbors(pr, pc):
                value = new_board[nr][nc]
                if value == EMPTY:
                    own_liberties.add((nr, nc))
                elif value == ME and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))

        if not own_liberties:
            return None

        # This exact shape is the only possible immediate simple-ko recapture:
        # one stone captures one stone and has only the captured point as a
        # liberty. Since history is unavailable, skip such moves.
        possible_ko_recapture = (
            len(captured) == 1
            and len(own_members) == 1
            and len(own_liberties) == 1
            and next(iter(own_liberties)) == captured[0]
        )

        return {
            "board": new_board,
            "captured": captured,
            "captured_groups": captured_group_ids,
            "own_members": own_members,
            "own_liberties": own_liberties,
            "possible_ko": possible_ko_recapture,
        }

    star_points = {
        (3, 3), (3, 15), (15, 3), (15, 15)
    }
    three_four_points = {
        (2, 3), (3, 2),
        (2, 15), (3, 16),
        (15, 2), (16, 3),
        (15, 16), (16, 15),
    }
    side_points = {
        (3, 9), (9, 3), (9, 15), (15, 9)
    }

    corners = (
        (3, 3, 1, 1, range(0, 7), range(0, 7)),
        (3, 15, 1, -1, range(0, 7), range(12, 19)),
        (15, 3, -1, 1, range(12, 19), range(0, 7)),
        (15, 15, -1, -1, range(12, 19), range(12, 19)),
    )

    def corner_is_empty(row_range, col_range):
        for rr in row_range:
            for cc in col_range:
                if board[rr][cc] != EMPTY:
                    return False
        return True

    best_move = None
    best_score = -float("inf")

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != EMPTY:
                continue

            result = simulate_move(row, col)
            if result is None or result["possible_ko"]:
                continue

            score = 0.0
            own_members = result["own_members"]
            own_liberties = result["own_liberties"]
            own_size = len(own_members)
            liberty_count = len(own_liberties)
            captured_count = len(result["captured"])

            adjacent_my_groups = set()
            adjacent_enemy_groups = set()
            empty_neighbors = 0
            adjacent_my_stones = 0
            adjacent_enemy_stones = 0

            for nr, nc in neighbors(row, col):
                value = board[nr][nc]
                if value == EMPTY:
                    empty_neighbors += 1
                elif value == ME:
                    adjacent_my_stones += 1
                    adjacent_my_groups.add(my_group_id[nr][nc])
                else:
                    adjacent_enemy_stones += 1
                    adjacent_enemy_groups.add(enemy_group_id[nr][nc])

            # Captures are the strongest immediate tactical gain.
            if captured_count:
                score += 115.0 * captured_count
                score += 25.0 * math.sqrt(captured_count)
                score += 12.0 * len(result["captured_groups"])
                if liberty_count >= 3:
                    score += 12.0

            # Save friendly groups currently in atari.
            for gid in adjacent_my_groups:
                group = my_groups[gid]
                liberties = group["liberties"]

                if len(liberties) == 1 and (row, col) in liberties:
                    if liberty_count >= 2:
                        score += 110.0 + 75.0 * group["size"]
                        score += 8.0 * min(liberty_count, 6)
                    else:
                        score -= 80.0 * group["size"]

                elif len(liberties) == 2 and (row, col) in liberties:
                    if liberty_count >= 3:
                        score += 22.0 + 10.0 * min(group["size"], 10)
                    else:
                        score += 4.0

                elif len(liberties) == 3 and (row, col) in liberties:
                    if liberty_count >= 4:
                        score += 4.0 + min(group["size"], 8)

            # Attack enemy groups, especially double-atari and large targets.
            for gid in adjacent_enemy_groups:
                if gid in result["captured_groups"]:
                    continue

                group = enemy_groups[gid]
                liberties = len(group["liberties"])

                if liberties == 2:
                    score += 45.0 + 18.0 * min(group["size"], 20)
                elif liberties == 3:
                    score += 8.0 + 3.0 * min(group["size"], 12)
                elif liberties == 4:
                    score += min(5.0, 0.8 * group["size"])

            # Connect separate friendly groups and cut separate enemy groups.
            if len(adjacent_my_groups) >= 2:
                score += 28.0 * (len(adjacent_my_groups) - 1)
                for gid in adjacent_my_groups:
                    group = my_groups[gid]
                    if len(group["liberties"]) <= 3:
                        score += 6.0 * min(group["size"], 8)

            if len(adjacent_enemy_groups) >= 2:
                score += 18.0 * (len(adjacent_enemy_groups) - 1)

            # Self-atari is usually disastrous.
            if liberty_count == 1:
                score -= 430.0 + 85.0 * own_size
            elif liberty_count == 2:
                score -= 15.0 + 3.0 * min(own_size, 15)
            elif liberty_count >= 4:
                score += min(12.0, 2.0 * liberty_count)

            # Basic local shape.
            score += 2.0 * empty_neighbors
            score -= 1.2 * adjacent_my_stones
            score += 1.8 * adjacent_enemy_stones

            if adjacent_my_stones == 3 and not captured_count:
                score -= 18.0
            elif adjacent_my_stones == 4 and not captured_count:
                score -= 55.0

            # Penalize filling a recognizable friendly eye.
            all_orthogonal_friendly = True
            for dr, dc in DIRECTIONS:
                nr, nc = row + dr, col + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board[nr][nc] != ME:
                        all_orthogonal_friendly = False
                        break

            if all_orthogonal_friendly and not captured_count:
                enemy_diagonals = 0
                edge_count = 0
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                    nr, nc = row + dr, col + dc
                    if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                        edge_count += 1
                    elif board[nr][nc] == OPPONENT:
                        enemy_diagonals += 1

                allowed_bad_diagonals = 1 if edge_count == 0 else 0
                if enemy_diagonals <= allowed_bad_diagonals:
                    score -= 95.0

            # Prefer useful board lines and avoid premature edge plays.
            line = min(row + 1, col + 1, BOARD_SIZE - row, BOARD_SIZE - col)
            line_values = {
                1: -30.0,
                2: -8.0,
                3: 8.0,
                4: 13.0,
                5: 8.0,
                6: 5.0,
            }
            score += line_values.get(line, 3.0)

            # Influence balance: favor extensions and contested boundaries,
            # while discouraging needless plays deep inside friendly influence.
            own_inf = my_influence[row][col]
            enemy_inf = enemy_influence[row][col]

            if own_inf > 0.0 and enemy_inf > 0.0:
                score += min(18.0, 1.2 * min(own_inf, enemy_inf))
                score += min(6.0, 0.15 * max(own_inf, enemy_inf))
            elif enemy_inf > 0.0:
                score += min(12.0, 0.5 * enemy_inf)
            elif own_inf > 0.0:
                score += min(8.0, 0.35 * own_inf)

            if own_inf > 18.0 and enemy_inf < 3.0 and not captured_count:
                score -= 18.0
            if enemy_inf > 24.0 and own_inf < 2.0 and liberty_count <= 2:
                score -= 15.0

            # Empty-region assessment.
            rid = region_id[row][col]
            region = regions[rid]
            region_size = region["size"]
            borders = region["borders"]

            if borders == {ME} and not captured_count:
                if region_size <= 2:
                    score -= 105.0
                elif region_size <= 8:
                    score -= 75.0
                elif region_size <= 25:
                    score -= 45.0
                else:
                    score -= 10.0
            elif borders == {OPPONENT}:
                if region_size <= 2:
                    score -= 12.0
                elif region_size <= 8:
                    score += 4.0
                else:
                    score += 12.0
            elif ME in borders and OPPONENT in borders:
                score += 12.0

            # Opening corner priorities.
            if stone_count < 50:
                for (
                    star_row, star_col, inward_row, inward_col,
                    row_range, col_range
                ) in corners:
                    empty_corner = corner_is_empty(row_range, col_range)

                    if empty_corner:
                        if (row, col) == (star_row, star_col):
                            score += 68.0 if stone_count < 24 else 38.0
                        elif (row, col) in three_four_points:
                            if row in row_range and col in col_range:
                                score += 58.0 if stone_count < 24 else 31.0

                    corner_stone = board[star_row][star_col]
                    approach_points = {
                        (star_row, star_col + 2 * inward_col),
                        (star_row - inward_row, star_col + 2 * inward_col),
                        (star_row + 2 * inward_row, star_col),
                        (star_row + 2 * inward_row, star_col - inward_col),
                    }

                    if (row, col) in approach_points:
                        if corner_stone == OPPONENT:
                            score += 30.0
                        elif corner_stone == ME:
                            score += 15.0

                if (row, col) in side_points:
                    score += 20.0 if stone_count >= 8 else 8.0
                if (row, col) == (9, 9):
                    score += 7.0

            # Small deterministic tie breaker.
            score += (
                ((row + 1) * 37 + (col + 1) * 17 + stone_count * 13) % 101
            ) / 1000.0

            if score > best_score:
                best_score = score
                best_move = (row + 1, col + 1)

    if best_move is None:
        return (0, 0)

    # In settled late positions, do not fill territory merely because a move
    # is technically legal.
    if stone_count >= 80 and best_score < -25.0:
        return (0, 0)

    return best_move
