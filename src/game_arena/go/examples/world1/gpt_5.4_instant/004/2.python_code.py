
from collections import deque

BOARD_SIZE = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 2

    legal_moves = []
    best_move = None
    best_score = -10**18

    center = 9

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue
            legal, info = simulate_move(board, r, c, 1)
            if not legal:
                continue
            legal_moves.append((r + 1, c + 1))

            score = evaluate_move(board, r, c, info, center)

            if score > best_score:
                best_score = score
                best_move = (r + 1, c + 1)

    if best_move is not None:
        return best_move
    return (0, 0)


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def get_group_and_liberties(board, r, c):
    color = board[r][c]
    group = []
    liberties = set()
    q = deque([(r, c)])
    seen = {(r, c)}

    while q:
        cr, cc = q.popleft()
        group.append((cr, cc))
        for nr, nc in neighbors(cr, cc):
            v = board[nr][nc]
            if v == 0:
                liberties.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return group, liberties


def simulate_move(board, r, c, color):
    if not in_bounds(r, c) or board[r][c] != 0:
        return False, None

    opp = 3 - color
    b = [row[:] for row in board]
    b[r][c] = color

    captured = []
    checked = set()
    for nr, nc in neighbors(r, c):
        if b[nr][nc] == opp and (nr, nc) not in checked:
            grp, libs = get_group_and_liberties(b, nr, nc)
            for p in grp:
                checked.add(p)
            if len(libs) == 0:
                captured.extend(grp)

    if captured:
        for cr, cc in captured:
            b[cr][cc] = 0

    my_group, my_libs = get_group_and_liberties(b, r, c)
    if len(my_libs) == 0:
        return False, None

    info = {
        "board_after": b,
        "captured": captured,
        "my_group": my_group,
        "my_libs": my_libs,
    }
    return True, info


def evaluate_move(board, r, c, info, center):
    b = info["board_after"]
    captured = info["captured"]
    my_group = info["my_group"]
    my_libs = info["my_libs"]

    score = 0.0

    # Strong priority: captures
    if captured:
        score += 10000 + 120 * len(captured)

    # Save own neighboring groups in atari / strengthen weak groups
    adjacent_friendly_groups = []
    seen_friendly = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 1 and (nr, nc) not in seen_friendly:
            grp, libs = get_group_and_liberties(board, nr, nc)
            for p in grp:
                seen_friendly.add(p)
            adjacent_friendly_groups.append((grp, libs))

    for grp, libs in adjacent_friendly_groups:
        if len(libs) == 1 and (r, c) in libs:
            score += 6000 + 80 * len(grp)
        elif len(libs) == 2 and (r, c) in libs:
            score += 800 + 20 * len(grp)

    # Putting opponent neighboring groups into atari / pressure
    adjacent_enemy_groups = []
    seen_enemy = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 2 and (nr, nc) not in seen_enemy:
            grp, libs = get_group_and_liberties(board, nr, nc)
            for p in grp:
                seen_enemy.add(p)
            adjacent_enemy_groups.append((grp, libs))

    for grp, libs in adjacent_enemy_groups:
        libs_after = count_group_liberties_after(b, grp[0][0], grp[0][1], 2)
        if libs_after == 1:
            score += 2500 + 40 * len(grp)
        elif libs_after == 2:
            score += 300 + 10 * len(grp)

    # Prefer connections
    friendly_neighbor_groups_count = len(adjacent_friendly_groups)
    if friendly_neighbor_groups_count >= 2:
        score += 700 * friendly_neighbor_groups_count

    # Prefer stronger resulting shape
    score += 35 * len(my_libs)
    score += 8 * len(my_group)

    # Avoid filling own eyes unless tactically useful
    empties_around = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 0)
    friendly_around = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 1)
    enemy_around = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 2)
    if friendly_around >= 3 and enemy_around == 0 and not captured:
        score -= 1500

    # Locality: favor moves near existing stones, especially contact/nearby tactical play
    nearby = 0
    enemy_nearby = 0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc) or (dr == 0 and dc == 0):
                continue
            if board[nr][nc] == 1:
                nearby += 1
            elif board[nr][nc] == 2:
                nearby += 1
                enemy_nearby += 1
    score += 6 * nearby + 4 * enemy_nearby

    # Opening preference: center-ish when board is sparse
    stones = sum(1 for rr in range(BOARD_SIZE) for cc in range(BOARD_SIZE) if board[rr][cc] != 0)
    dist_center = abs(r - center) + abs(c - center)
    if stones < 12:
        score += 80 - 5 * dist_center
    else:
        score += 20 - 1.2 * dist_center

    # Mild edge/corner penalty unless tactical
    edge_dist = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    if not captured and enemy_around == 0 and stones < 20:
        if edge_dist == 0:
            score -= 40
        elif edge_dist == 1:
            score -= 15

    return score


def count_group_liberties_after(board, r, c, color):
    if not in_bounds(r, c) or board[r][c] != color:
        return 0
    _, libs = get_group_and_liberties(board, r, c)
    return len(libs)
