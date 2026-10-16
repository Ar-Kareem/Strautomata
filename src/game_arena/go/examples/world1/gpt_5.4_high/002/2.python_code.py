
from collections import defaultdict

BOARD_SIZE = 19

NEIGHBORS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
DIAGONALS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        if r > 0:
            NEIGHBORS[r][c].append((r - 1, c))
        if r + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r + 1, c))
        if c > 0:
            NEIGHBORS[r][c].append((r, c - 1))
        if c + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r, c + 1))

        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                DIAGONALS[r][c].append((nr, nc))

CORNER_4_4 = {(3, 3), (3, 15), (15, 3), (15, 15)}
SIDE_STAR = {(3, 9), (9, 3), (9, 15), (15, 9)}
CENTER = (9, 9)


def add_to_map(mapping, point, value):
    mapping[point] = mapping.get(point, 0) + value


def build_board(me, opponent):
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    for r, c in me:
        r -= 1
        c -= 1
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            board[r][c] = 1

    for r, c in opponent:
        r -= 1
        c -= 1
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
            board[r][c] = -1

    return board


def analyze_board(board):
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    group_map = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    groups = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = board[r][c]
            if color == 0 or visited[r][c]:
                continue

            gid = len(groups)
            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                group_map[x][y] = gid

                for nx, ny in NEIGHBORS[x][y]:
                    v = board[nx][ny]
                    if v == 0:
                        libs.add((nx, ny))
                    elif v == color and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            groups.append((color, stones, libs))

    return group_map, groups


def collect_group(board, r, c):
    color = board[r][c]
    stones = {(r, c)}
    libs = set()
    stack = [(r, c)]

    while stack:
        x, y = stack.pop()
        for nx, ny in NEIGHBORS[x][y]:
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in stones:
                stones.add((nx, ny))
                stack.append((nx, ny))

    return stones, libs


def simulate_move(board, r, c, color=1):
    if board[r][c] != 0:
        return None

    new_board = [row[:] for row in board]
    new_board[r][c] = color

    checked = set()
    captured = 0

    for nx, ny in NEIGHBORS[r][c]:
        if new_board[nx][ny] == -color and (nx, ny) not in checked:
            stones, libs = collect_group(new_board, nx, ny)
            checked |= stones
            if not libs:
                captured += len(stones)
                for x, y in stones:
                    new_board[x][y] = 0

    own_stones, own_libs = collect_group(new_board, r, c)
    if not own_libs:
        return None

    return new_board, captured, len(own_stones), len(own_libs), own_stones, own_libs


def is_eye_like(board, r, c, color):
    if board[r][c] != 0:
        return False

    for nx, ny in NEIGHBORS[r][c]:
        if board[nx][ny] != color:
            return False

    for nx, ny in DIAGONALS[r][c]:
        if board[nx][ny] == -color:
            return False

    return True


def position_bonus(r, c, total_stones, occupied):
    line = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    score = 0

    if total_stones < 10:
        if (r, c) in CORNER_4_4:
            score += 700
        elif (r, c) == CENTER:
            score += 450
        elif (r, c) in SIDE_STAR:
            score += 260

        if line == 0:
            score -= 140
        elif line == 1:
            score -= 40

        if occupied:
            md = 999
            for x, y in occupied:
                d = abs(r - x) + abs(c - y)
                if d < md:
                    md = d
                    if md <= 2:
                        break
            score += min(md, 10) * 14

    elif total_stones < 40:
        if (r, c) in CORNER_4_4:
            score += 60
        elif (r, c) == CENTER:
            score += 30

        if line == 0:
            score -= 60
        elif line == 1:
            score -= 20

    else:
        if line == 0:
            score -= 20

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)

    occupied = []
    has_empty = False
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                has_empty = True
            else:
                occupied.append((r, c))

    if not has_empty:
        return (0, 0)

    total_stones = len(occupied)
    group_map, groups = analyze_board(board)
    group_sizes = [len(stones) for _, stones, _ in groups]

    capture_map = {}
    save_map = {}
    attack_map = {}
    defend_map = {}
    squeeze_map = {}
    expand_map = {}

    for color, stones, libs in groups:
        size = len(stones)
        nlibs = len(libs)

        if nlibs == 1:
            p = next(iter(libs))
            if color == -1:
                add_to_map(capture_map, p, size)
            else:
                add_to_map(save_map, p, size)

        elif nlibs == 2:
            if color == -1:
                for p in libs:
                    add_to_map(attack_map, p, size)
            else:
                for p in libs:
                    add_to_map(defend_map, p, size)

        elif nlibs == 3:
            if color == -1:
                for p in libs:
                    add_to_map(squeeze_map, p, size)
            else:
                for p in libs:
                    add_to_map(expand_map, p, size)

    empties = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue

            p = (r, c)
            prior = 0

            prior += 4000 * capture_map.get(p, 0)
            prior += 3000 * save_map.get(p, 0)
            prior += 220 * attack_map.get(p, 0)
            prior += 120 * defend_map.get(p, 0)
            prior += 45 * squeeze_map.get(p, 0)
            prior += 20 * expand_map.get(p, 0)

            adj_own = 0
            adj_opp = 0
            own_groups = set()
            opp_groups = set()

            for nx, ny in NEIGHBORS[r][c]:
                v = board[nx][ny]
                if v == 1:
                    adj_own += 1
                    own_groups.add(group_map[nx][ny])
                elif v == -1:
                    adj_opp += 1
                    opp_groups.add(group_map[nx][ny])

            prior += 26 * adj_own + 34 * adj_opp

            if len(own_groups) > 1:
                prior += 120 * (len(own_groups) - 1)
                prior += 8 * sum(group_sizes[gid] for gid in own_groups)

            if len(opp_groups) > 1:
                prior += 60 * (len(opp_groups) - 1)
                prior += 4 * sum(group_sizes[gid] for gid in opp_groups)

            if total_stones > 20 and adj_own + adj_opp == 0:
                prior -= 100
            if total_stones > 80 and adj_own + adj_opp == 0:
                prior -= 80

            tactical_here = (
                capture_map.get(p, 0)
                + save_map.get(p, 0)
                + attack_map.get(p, 0)
                + defend_map.get(p, 0)
            )

            if tactical_here == 0 and is_eye_like(board, r, c, 1):
                prior -= 900

            prior += position_bonus(r, c, total_stones, occupied)

            empties.append((prior, r, c, adj_own, adj_opp))

    empties.sort(key=lambda x: x[0], reverse=True)

    best_move = None
    best_score = -10**18

    for prior, r, c, adj_own, adj_opp in empties:
        sim = simulate_move(board, r, c, 1)
        if sim is None:
            continue

        new_board, captured, own_size, own_lib_count, own_stones, own_libs = sim

        score = prior
        score += 4500 * captured
        score += 18 * own_size + 24 * own_lib_count

        if own_lib_count == 1:
            score -= 1600 + 120 * own_size
        elif own_lib_count == 2:
            score -= 70 * own_size

        seen_opp = set()
        atari_opp = 0
        weak_opp = 0

        for nx, ny in NEIGHBORS[r][c]:
            if new_board[nx][ny] == -1 and (nx, ny) not in seen_opp:
                stones2, libs2 = collect_group(new_board, nx, ny)
                seen_opp |= stones2
                s2 = len(stones2)
                l2 = len(libs2)
                if l2 == 1:
                    atari_opp += s2
                elif l2 == 2:
                    weak_opp += s2

        score += 230 * atari_opp + 45 * weak_opp

        seen_me = set()
        atari_me = 0
        weak_me = 0

        to_check = [(r, c)] + NEIGHBORS[r][c]
        for x, y in to_check:
            if new_board[x][y] == 1 and (x, y) not in seen_me:
                stones2, libs2 = collect_group(new_board, x, y)
                seen_me |= stones2
                s2 = len(stones2)
                l2 = len(libs2)
                if l2 == 1:
                    atari_me += s2
                elif l2 == 2:
                    weak_me += s2

        score -= 260 * atari_me + 35 * weak_me

        if captured == 0 and is_eye_like(board, r, c, 1):
            score -= 1500

        if adj_own == 0 and adj_opp == 0 and total_stones > 0:
            score -= 50

        # Conservative ko safety:
        # without history, an immediate ko recapture can be illegal.
        # This pattern is the usual "capture one stone, new stone has one liberty".
        ko_like = (captured == 1 and own_size == 1 and own_lib_count == 1)
        if ko_like:
            continue

        if score > best_score:
            best_score = score
            best_move = (r + 1, c + 1)

    if best_move is not None:
        return best_move

    # Fallback: return any non-ko-like legal move if one exists.
    for _, r, c, _, _ in empties:
        sim = simulate_move(board, r, c, 1)
        if sim is None:
            continue
        _, captured, own_size, own_lib_count, _, _ = sim
        if not (captured == 1 and own_size == 1 and own_lib_count == 1):
            return (r + 1, c + 1)

    # Passing is always legal.
    return (0, 0)
