
# Go policy for a 19x19 board.
# Required API:
#   policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = 2

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = ME

    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = OPP

    occupied = len(me) + len(opponent)

    # Strong deterministic opening: occupy important corner/star points.
    opening_points = [
        (4, 4), (16, 16), (4, 16), (16, 4),
        (10, 10),
        (4, 10), (16, 10), (10, 4), (10, 16),
        (3, 3), (17, 17), (3, 17), (17, 3),
        (5, 4), (4, 5), (15, 16), (16, 15),
        (5, 16), (4, 15), (15, 4), (16, 5),
    ]

    if occupied < 12:
        for move in opening_points:
            rr, cc = move[0] - 1, move[1] - 1
            if board[rr][cc] == EMPTY and is_legal(board, rr, cc):
                return move

    candidates = generate_candidates(board)

    best_move = None
    best_score = -10**18

    for r, c in candidates:
        if board[r][c] != EMPTY:
            continue
        if not is_legal(board, r, c):
            continue

        score = evaluate_move(board, r, c)

        if score > best_score:
            best_score = score
            best_move = (r + 1, c + 1)

    if best_move is not None:
        return best_move

    # Absolute safety fallback: return the first legal empty point.
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY and is_legal(board, r, c):
                return (r + 1, c + 1)

    # No legal move exists.
    return (0, 0)


def inside(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc):
            yield nr, nc


def get_group_and_liberties(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    group = []
    liberties = set()

    while stack:
        x, y = stack.pop()
        group.append((x, y))

        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == EMPTY:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))

    return group, liberties


def is_legal(board, r, c):
    if not inside(r, c) or board[r][c] != EMPTY:
        return False

    # Legal if it captures at least one adjacent opponent group in atari.
    captures = False
    checked = set()

    for nr, nc in neighbors(r, c):
        if board[nr][nc] == OPP and (nr, nc) not in checked:
            group, libs = get_group_and_liberties(board, nr, nc)
            checked.update(group)
            if len(libs) == 1 and (r, c) in libs:
                captures = True
                break

    if captures:
        return True

    # Otherwise legal if the placed stone/group has at least one liberty.
    board[r][c] = ME
    _, libs = get_group_and_liberties(board, r, c)
    board[r][c] = EMPTY

    return len(libs) > 0


def simulate_move(board, r, c):
    new_board = [row[:] for row in board]
    new_board[r][c] = ME

    captured = 0
    checked = set()

    for nr, nc in neighbors(r, c):
        if new_board[nr][nc] == OPP and (nr, nc) not in checked:
            group, libs = get_group_and_liberties(new_board, nr, nc)
            checked.update(group)
            if len(libs) == 0:
                captured += len(group)
                for gx, gy in group:
                    new_board[gx][gy] = EMPTY

    return new_board, captured


def generate_candidates(board):
    candidates = set()

    # Tactical/local candidates around existing stones.
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if abs(dr) + abs(dc) <= 3:
                            nr, nc = r + dr, c + dc
                            if inside(nr, nc) and board[nr][nc] == EMPTY:
                                candidates.add((nr, nc))

    # Always include important strategic points.
    strategic = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
        (2, 2), (2, 16), (16, 2), (16, 16),
        (3, 2), (2, 3), (3, 16), (2, 15),
        (16, 3), (15, 2), (16, 15), (15, 16),
    ]

    for r, c in strategic:
        if board[r][c] == EMPTY:
            candidates.add((r, c))

    # Empty board fallback.
    if not candidates:
        candidates.add((3, 3))

    return candidates


def evaluate_move(board, r, c):
    score = 0

    # Avoid filling a solid own eye unless tactically valuable.
    own_eye = is_own_eye(board, r, c)

    adjacent_own = 0
    adjacent_opp = 0

    opp_groups_seen = set()
    own_groups_seen = set()

    capture_potential = 0
    attack_potential = 0
    save_potential = 0
    connection_potential = 0

    for nr, nc in neighbors(r, c):
        if board[nr][nc] == ME:
            adjacent_own += 1
            if (nr, nc) not in own_groups_seen:
                group, libs = get_group_and_liberties(board, nr, nc)
                own_groups_seen.update(group)

                if len(libs) == 1 and (r, c) in libs:
                    save_potential += 90 + 14 * len(group)
                elif len(libs) == 2 and (r, c) in libs:
                    save_potential += 25 + 5 * len(group)

                connection_potential += min(30, 4 * len(group))

        elif board[nr][nc] == OPP:
            adjacent_opp += 1
            if (nr, nc) not in opp_groups_seen:
                group, libs = get_group_and_liberties(board, nr, nc)
                opp_groups_seen.update(group)

                if len(libs) == 1 and (r, c) in libs:
                    capture_potential += 160 + 45 * len(group)
                elif len(libs) == 2 and (r, c) in libs:
                    attack_potential += 55 + 10 * len(group)
                elif len(libs) == 3 and (r, c) in libs:
                    attack_potential += 18 + 3 * len(group)

    new_board, captured = simulate_move(board, r, c)
    _, new_libs = get_group_and_liberties(new_board, r, c)
    liberties = len(new_libs)

    score += capture_potential
    score += captured * 120
    score += save_potential
    score += attack_potential
    score += connection_potential

    # Liberty/shape value.
    score += 14 * liberties
    score += 18 * adjacent_own
    score += 8 * adjacent_opp

    # Penalize self-atari unless capturing or saving something important.
    if liberties <= 1 and captured == 0:
        score -= 180
    elif liberties == 2:
        score -= 25

    if own_eye and captured == 0:
        score -= 250

    # Positional heuristic.
    rr = r + 1
    cc = c + 1

    edge_dist = min(rr, cc, BOARD_SIZE + 1 - rr, BOARD_SIZE + 1 - cc)

    if edge_dist == 1:
        score -= 35
    elif edge_dist == 2:
        score += 2
    elif edge_dist == 3:
        score += 20
    elif edge_dist == 4:
        score += 24
    elif edge_dist == 5:
        score += 10
    else:
        score += 2

    # Corners are valuable early/midgame.
    corner_distance = min(
        abs(rr - 4) + abs(cc - 4),
        abs(rr - 4) + abs(cc - 16),
        abs(rr - 16) + abs(cc - 4),
        abs(rr - 16) + abs(cc - 16),
    )
    score += max(0, 26 - 5 * corner_distance)

    # Star/extension points.
    if rr in (4, 10, 16) and cc in (4, 10, 16):
        score += 16

    # Avoid cramped overconcentration.
    if adjacent_own >= 3 and captured == 0:
        score -= 35

    # Slight preference for sente-like contact against weak enemy.
    if adjacent_opp and attack_potential:
        score += 20

    # Deterministic tie breaker toward center-ish useful points.
    score -= abs(rr - 10) * 0.05 + abs(cc - 10) * 0.05

    return score


def is_own_eye(board, r, c):
    # Orthogonal neighbors must be own stones or board edge.
    for nr, nc in neighbors(r, c):
        if board[nr][nc] != ME:
            return False

    # Check diagonals. True eye if opponent has too much diagonal presence.
    opponent_diagonals = 0
    offboard_diagonals = 0

    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nr, nc = r + dr, c + dc
        if not inside(nr, nc):
            offboard_diagonals += 1
        elif board[nr][nc] == OPP:
            opponent_diagonals += 1

    if offboard_diagonals > 0:
        return opponent_diagonals == 0

    return opponent_diagonals <= 1
