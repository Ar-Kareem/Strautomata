
from typing import List, Tuple

N = 19

# Precompute neighbors / diagonals for speed.
NEIGHBORS = [[] for _ in range(N * N)]
DIAGONALS = [[] for _ in range(N * N)]

for r in range(N):
    for c in range(N):
        idx = r * N + c
        if r > 0:
            NEIGHBORS[idx].append((r - 1, c))
        if r + 1 < N:
            NEIGHBORS[idx].append((r + 1, c))
        if c > 0:
            NEIGHBORS[idx].append((r, c - 1))
        if c + 1 < N:
            NEIGHBORS[idx].append((r, c + 1))

        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                DIAGONALS[idx].append((rr, cc))

# Opening preferences, 0-based coordinates.
OPENING_BONUS = {
    # 4-4
    (3, 3): 220, (3, 15): 220, (15, 3): 220, (15, 15): 220,
    # 4-10 / 10-4
    (3, 9): 170, (9, 3): 170, (9, 15): 170, (15, 9): 170,
    # 3-4 / 4-3
    (2, 3): 150, (3, 2): 150, (2, 15): 150, (3, 16): 150,
    (15, 2): 150, (16, 3): 150, (15, 16): 150, (16, 15): 150,
    # 3-3
    (2, 2): 120, (2, 16): 120, (16, 2): 120, (16, 16): 120,
    # Tengen
    (9, 9): 140,
    # 7-7 style influence points
    (6, 6): 110, (6, 12): 110, (12, 6): 110, (12, 12): 110,
}


def analyze_groups(board):
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or gid[r][c] != -1:
                continue

            g = len(groups)
            stack = [(r, c)]
            gid[r][c] = g
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))
                for nr, nc in NEIGHBORS[sr * N + sc]:
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = g
                        stack.append((nr, nc))

            groups.append({
                "color": color,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
                "lib_count": len(libs),
            })

    return gid, groups


def is_own_eye(board, r, c, color):
    idx = r * N + c
    for nr, nc in NEIGHBORS[idx]:
        if board[nr][nc] != color:
            return False

    opp = 3 - color
    opp_diags = 0
    for nr, nc in DIAGONALS[idx]:
        if board[nr][nc] == opp:
            opp_diags += 1

    # On edge/corner, require no opposing diagonal stones.
    if len(DIAGONALS[idx]) < 4:
        return opp_diags == 0
    # In the center, allow at most one opposing diagonal.
    return opp_diags <= 1


def local_influence(board, r, c):
    score = 0
    r0 = max(0, r - 2)
    r1 = min(N, r + 3)
    c0 = max(0, c - 2)
    c1 = min(N, c + 3)

    for rr in range(r0, r1):
        for cc in range(c0, c1):
            stone = board[rr][cc]
            if stone == 0:
                continue
            d = abs(rr - r) + abs(cc - c)
            if d == 0 or d > 4:
                continue
            w = 5 - d
            if stone == 1:
                score += 3 * w
            else:
                score += 4 * w
    return score


def opening_score(r, c, total_stones, all_stones):
    edge = min(r, c, N - 1 - r, N - 1 - c)
    score = 0

    if total_stones < 14:
        score += OPENING_BONUS.get((r, c), 0)

        if edge == 0:
            score -= 140
        elif edge == 1:
            score -= 30
        elif edge == 2:
            score += 20
        elif edge == 3:
            score += 35

        if all_stones:
            mind = min(abs(r - sr) + abs(c - sc) for sr, sc in all_stones)
            score += 16 * min(mind, 10)
        else:
            score += 60

    elif total_stones < 50:
        if edge == 0:
            score -= 40
        elif edge == 1:
            score -= 10

    else:
        if edge == 0:
            score -= 15

    return score


def evaluate_move(board, gid, groups, r, c, total_stones, all_stones):
    if board[r][c] != 0:
        return None

    idx = r * N + c
    same = set()
    opp = set()
    captured_gids = set()
    saved_gids = set()
    attack_gids = set()

    libs = set()
    adj_me = 0
    adj_opp = 0
    adj_empty = 0

    for nr, nc in NEIGHBORS[idx]:
        val = board[nr][nc]
        if val == 0:
            libs.add((nr, nc))
            adj_empty += 1
        elif val == 1:
            adj_me += 1
            g = gid[nr][nc]
            same.add(g)
        else:
            adj_opp += 1
            g = gid[nr][nc]
            opp.add(g)

    captured_size = 0
    saved_size = 0
    attack_size = 0
    reinforce_size = 0
    light_attack_size = 0
    light_reinforce_size = 0

    for g in same:
        gr = groups[g]
        libs.update(gr["libs"])
        if (r, c) in gr["libs"]:
            if gr["lib_count"] == 1:
                saved_gids.add(g)
                saved_size += gr["size"]
            elif gr["lib_count"] == 2:
                reinforce_size += gr["size"]
            elif gr["lib_count"] == 3:
                light_reinforce_size += gr["size"]

    for g in opp:
        gr = groups[g]
        if (r, c) in gr["libs"]:
            if gr["lib_count"] == 1:
                captured_gids.add(g)
                captured_size += gr["size"]
            elif gr["lib_count"] == 2:
                attack_gids.add(g)
                attack_size += gr["size"]
            elif gr["lib_count"] == 3:
                light_attack_size += gr["size"]

    libs.discard((r, c))
    for g in captured_gids:
        libs.update(groups[g]["stones"])

    lib_count = len(libs)
    if lib_count == 0:
        return None  # suicide

    new_size = 1 + sum(groups[g]["size"] for g in same)

    score = 0

    # Big tactical priorities.
    score += 25000 * captured_size + 3500 * len(captured_gids)
    score += 17000 * saved_size + 2500 * len(saved_gids)

    # Pressure / reinforcement.
    score += 1100 * attack_size + 180 * len(attack_gids)
    score += 400 * reinforce_size
    score += 120 * light_attack_size
    score += 90 * light_reinforce_size

    # Connection / cutting.
    score += 160 * len(same)
    if len(same) >= 2:
        score += 320 * (len(same) - 1) * (len(same) - 1)

    score += 90 * len(opp)
    if len(opp) >= 2:
        score += 180 * (len(opp) - 1) * (len(opp) - 1)

    # Shape / liberties.
    score += 70 * lib_count + 10 * new_size
    score += 35 * adj_me + 30 * adj_opp

    # General locality / opening.
    score += local_influence(board, r, c)
    score += opening_score(r, c, total_stones, all_stones)

    # Penalties for bad shape.
    if lib_count == 1:
        if captured_size == 0:
            score -= 7000
        else:
            score -= 1200
    elif lib_count == 2:
        score -= 350

    if is_own_eye(board, r, c, 1) and captured_size == 0 and saved_size == 0 and attack_size == 0:
        score -= 2800

    if adj_me >= 3 and adj_opp == 0 and adj_empty == 0 and captured_size == 0 and saved_size == 0:
        score -= 900

    return score, lib_count


def collect_group_and_libs(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        sr, sc = stack.pop()
        stones.append((sr, sc))
        for nr, nc in NEIGHBORS[sr * N + sc]:
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return stones, libs


def is_legal_full(board, r, c, color):
    if not (0 <= r < N and 0 <= c < N):
        return False
    if board[r][c] != 0:
        return False

    opp = 3 - color
    new_board = [row[:] for row in board]
    new_board[r][c] = color

    for nr, nc in NEIGHBORS[r * N + c]:
        if new_board[nr][nc] == opp:
            stones, libs = collect_group_and_libs(new_board, nr, nc)
            if not libs:
                for sr, sc in stones:
                    new_board[sr][sc] = 0

    _, libs = collect_group_and_libs(new_board, r, c)
    return bool(libs)


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Robustify input a bit.
    me_set = set()
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            me_set.add((r - 1, c - 1))

    opp_set = set()
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and (r - 1, c - 1) not in me_set:
            opp_set.add((r - 1, c - 1))

    board = [[0] * N for _ in range(N)]
    for r, c in me_set:
        board[r][c] = 1
    for r, c in opp_set:
        board[r][c] = 2

    total_stones = len(me_set) + len(opp_set)
    all_stones = list(me_set | opp_set)

    gid, groups = analyze_groups(board)

    best_move = None
    best_key = None

    for r in range(N):
        for c in range(N):
            result = evaluate_move(board, gid, groups, r, c, total_stones, all_stones)
            if result is None:
                continue

            score, lib_count = result
            # Deterministic tie-breaks.
            center_pref = -(abs(r - 9) + abs(c - 9))
            inward_pref = -min(r, c, N - 1 - r, N - 1 - c)
            key = (score, lib_count, center_pref, inward_pref, -r, -c)

            if best_key is None or key > best_key:
                best_key = key
                best_move = (r, c)

    # Validate chosen move with a full legality check.
    if best_move is not None and is_legal_full(board, best_move[0], best_move[1], 1):
        return (best_move[0] + 1, best_move[1] + 1)

    # Safe fallback: first legal move found.
    for r in range(N):
        for c in range(N):
            if is_legal_full(board, r, c, 1):
                return (r + 1, c + 1)

    # No legal board move: pass.
    return (0, 0)
