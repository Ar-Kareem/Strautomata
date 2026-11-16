
from collections import defaultdict

SIZE = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

# 0-based points with rough opening weights.
OPENING_SITES = [
    ((3, 3), 350), ((3, 15), 350), ((15, 3), 350), ((15, 15), 350),   # 4-4
    ((3, 9), 220), ((9, 3), 220), ((9, 15), 220), ((15, 9), 220),     # side stars
    ((9, 9), 180),                                                      # tengen
    ((6, 6), 140), ((6, 12), 140), ((12, 6), 140), ((12, 12), 140),   # 7-7 style
]


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < SIZE and 0 <= c < SIZE


def neighbors(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r + 1 < SIZE:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < SIZE:
        yield r, c + 1


def diagonals(r: int, c: int):
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            yield nr, nc


def build_board(me, opponent):
    board = [[0] * SIZE for _ in range(SIZE)]
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[r - 1][c - 1] = -1
    return board


def group_and_liberties(board, r: int, c: int):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return stones, libs


def analyze_groups(board):
    visited = set()
    groups = []
    pos_to_group = [[-1] * SIZE for _ in range(SIZE)]

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0 and (r, c) not in visited:
                stones, libs = group_and_liberties(board, r, c)
                gid = len(groups)
                for x, y in stones:
                    visited.add((x, y))
                    pos_to_group[x][y] = gid
                groups.append(
                    {
                        "color": board[r][c],
                        "stones": stones,
                        "libs": libs,
                        "size": len(stones),
                    }
                )
    return groups, pos_to_group


def simulate_move(board, move, color: int):
    r, c = move
    if not in_bounds(r, c) or board[r][c] != 0:
        return None

    nb = [row[:] for row in board]
    nb[r][c] = color

    captured = 0
    checked = set()
    to_remove = []

    for nx, ny in neighbors(r, c):
        if nb[nx][ny] == -color and (nx, ny) not in checked:
            stones, libs = group_and_liberties(nb, nx, ny)
            for s in stones:
                checked.add(s)
            if len(libs) == 0:
                captured += len(stones)
                to_remove.extend(stones)

    for x, y in to_remove:
        nb[x][y] = 0

    stones, libs = group_and_liberties(nb, r, c)
    if len(libs) == 0:
        return None

    return {
        "board": nb,
        "captures": captured,
        "group_stones": stones,
        "group_libs": libs,
    }


def is_eye_like(board, r: int, c: int, color: int) -> bool:
    if board[r][c] != 0:
        return False
    for nx, ny in neighbors(r, c):
        if board[nx][ny] != color:
            return False
    for nx, ny in diagonals(r, c):
        if board[nx][ny] == -color:
            return False
    return True


def opening_bonus(r: int, c: int, total_stones: int) -> int:
    if total_stones > 20:
        return 25 - 2 * (abs(r - 9) + abs(c - 9))

    factor = 2 if total_stones == 0 else 1
    penalty = 50 if total_stones == 0 else (18 if total_stones <= 8 else 10)

    best = -10**9
    for (pr, pc), w in OPENING_SITES:
        val = factor * w - penalty * (abs(r - pr) + abs(c - pc))
        if val > best:
            best = val

    if total_stones < 12:
        edge = min(r, c, SIZE - 1 - r, SIZE - 1 - c)
        if edge == 0:
            best -= 180
        elif edge == 1:
            best -= 90
    return best


def generate_tactical_maps(groups):
    kill = defaultdict(int)    # moves that capture opponent atari groups
    save = defaultdict(int)    # moves that save my atari groups
    attack = defaultdict(int)  # moves that pressure opponent weak groups
    defend = defaultdict(int)  # moves that help my weak groups

    for g in groups:
        libs = g["libs"]
        n = len(libs)
        if n == 0:
            continue

        if g["color"] == -1:
            if n == 1:
                lib = next(iter(libs))
                kill[lib] += g["size"]
            elif n == 2:
                for lib in libs:
                    attack[lib] += g["size"]
            elif n == 3 and g["size"] >= 4:
                for lib in libs:
                    attack[lib] += max(1, g["size"] // 2)
        else:
            if n == 1:
                lib = next(iter(libs))
                save[lib] += g["size"]
            elif n == 2:
                for lib in libs:
                    defend[lib] += g["size"]

    return kill, save, attack, defend


def generate_candidates(board, groups, total_stones: int):
    cand = set()

    # Tactical liberties first.
    for g in groups:
        n = len(g["libs"])
        if n <= 2:
            cand.update(g["libs"])
        elif g["color"] == -1 and n == 3 and g["size"] >= 4:
            cand.update(g["libs"])

    # Locality: play near stones.
    if total_stones > 0:
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] != 0:
                    for nx, ny in neighbors(r, c):
                        if board[nx][ny] == 0:
                            cand.add((nx, ny))
                    if total_stones < 12:
                        for nx, ny in diagonals(r, c):
                            if board[nx][ny] == 0:
                                cand.add((nx, ny))
                        for dr, dc in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                            nr, nc = r + dr, c + dc
                            if in_bounds(nr, nc) and board[nr][nc] == 0:
                                cand.add((nr, nc))

    # Opening structure points.
    for p, _ in OPENING_SITES:
        if board[p[0]][p[1]] == 0:
            cand.add(p)

    return cand


def evaluate_move(board, groups, pos_to_group, move, total_stones: int, tactical_maps):
    r, c = move
    if board[r][c] != 0:
        return None

    kill, save, attack, defend = tactical_maps

    score = opening_bonus(r, c, total_stones)

    adj_me = 0
    adj_opp = 0
    diag_me = 0
    diag_opp = 0
    friendly_gids = set()
    enemy_gids = set()

    for nx, ny in neighbors(r, c):
        v = board[nx][ny]
        if v == 1:
            adj_me += 1
            friendly_gids.add(pos_to_group[nx][ny])
        elif v == -1:
            adj_opp += 1
            enemy_gids.add(pos_to_group[nx][ny])

    for nx, ny in diagonals(r, c):
        if board[nx][ny] == 1:
            diag_me += 1
        elif board[nx][ny] == -1:
            diag_opp += 1

    score += 90 * adj_me + 55 * adj_opp + 12 * diag_me + 4 * diag_opp

    if adj_me == 0 and adj_opp == 0 and total_stones > 6:
        score -= 180

    if total_stones > 25 and min(r, c, SIZE - 1 - r, SIZE - 1 - c) == 0 and adj_me + adj_opp == 0:
        score -= 120

    score += 6000 * kill.get(move, 0)
    score += 5000 * save.get(move, 0)
    score += 220 * attack.get(move, 0)
    score += 180 * defend.get(move, 0)

    for gid in enemy_gids:
        g = groups[gid]
        libs = len(g["libs"])
        sz = g["size"]
        if libs == 1:
            score += 1200 * sz
        elif libs == 2:
            score += 260 * sz
        elif libs == 3:
            score += 70 * sz

    for gid in friendly_gids:
        g = groups[gid]
        libs = len(g["libs"])
        sz = g["size"]
        if libs == 1:
            score += 1100 * sz
        elif libs == 2:
            score += 220 * sz
        elif libs == 3:
            score += 60 * sz

    if len(friendly_gids) >= 2:
        score += 160 * (len(friendly_gids) - 1)
        score += 15 * sum(min(groups[gid]["size"], 10) for gid in friendly_gids)

    if len(enemy_gids) >= 2:
        score += (120 if adj_me else 70) * (len(enemy_gids) - 1)

    if is_eye_like(board, r, c, 1) and kill.get(move, 0) == 0 and save.get(move, 0) == 0:
        score -= 2500

    sim = simulate_move(board, move, 1)
    if sim is None:
        return None

    nb = sim["board"]
    caps = sim["captures"]
    libs_after = len(sim["group_libs"])
    new_group_size = len(sim["group_stones"])

    score += 15000 * caps
    score += 60 * libs_after + 15 * new_group_size

    if save.get(move, 0):
        if libs_after >= 2:
            score += 6000 * save.get(move, 0)
        else:
            score -= 3000 * save.get(move, 0)

    if libs_after == 1 and caps == 0:
        score -= 7000 + 180 * new_group_size
    elif libs_after == 2 and caps == 0:
        score -= 350

    if adj_opp >= 3 and adj_me == 0 and caps == 0 and libs_after <= 2:
        score -= 700

    checked = set()
    for nx, ny in neighbors(r, c):
        if nb[nx][ny] == -1 and (nx, ny) not in checked:
            stones, libs = group_and_liberties(nb, nx, ny)
            for s in stones:
                checked.add(s)
            l = len(libs)
            sz = len(stones)
            if l == 1:
                score += 350 * sz
            elif l == 2:
                score += 80 * sz

    checked = set()
    for nx, ny in neighbors(r, c):
        if nb[nx][ny] == 1 and (nx, ny) not in checked:
            stones, libs = group_and_liberties(nb, nx, ny)
            for s in stones:
                checked.add(s)
            l = len(libs)
            sz = len(stones)
            if l == 1:
                score -= 450 * sz
            elif l == 2:
                score -= 40 * sz

    return score, sim


def best_opponent_reply(board_after, last_move):
    groups, _ = analyze_groups(board_after)

    kill = defaultdict(int)    # opponent can kill my groups
    save = defaultdict(int)    # opponent can save own groups
    attack = defaultdict(int)
    defend = defaultdict(int)

    cand = set()

    for g in groups:
        libs = g["libs"]
        n = len(libs)
        if n == 0:
            continue

        if g["color"] == 1:
            if n == 1:
                lib = next(iter(libs))
                kill[lib] += g["size"]
                cand.add(lib)
            elif n == 2:
                for lib in libs:
                    attack[lib] += g["size"]
                    cand.add(lib)
        else:
            if n == 1:
                lib = next(iter(libs))
                save[lib] += g["size"]
                cand.add(lib)
            elif n == 2:
                for lib in libs:
                    defend[lib] += g["size"]
                    cand.add(lib)

    lr, lc = last_move
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            nr, nc = lr + dr, lc + dc
            if in_bounds(nr, nc) and board_after[nr][nc] == 0:
                cand.add((nr, nc))

    scored = []
    for mv in cand:
        r, c = mv
        if board_after[r][c] != 0:
            continue
        s = 7000 * kill.get(mv, 0) + 5000 * save.get(mv, 0) + 220 * attack.get(mv, 0) + 180 * defend.get(mv, 0)
        adj_me = 0
        adj_opp = 0
        for nx, ny in neighbors(r, c):
            if board_after[nx][ny] == 1:
                adj_me += 1
            elif board_after[nx][ny] == -1:
                adj_opp += 1
        s += 80 * adj_me + 60 * adj_opp
        scored.append((s, mv))

    if not scored:
        return 0

    scored.sort(key=lambda x: x[0], reverse=True)

    best = 0
    for _, mv in scored[:30]:
        sim = simulate_move(board_after, mv, -1)
        if sim is None:
            continue

        score = 15000 * sim["captures"]

        if save.get(mv, 0):
            if len(sim["group_libs"]) >= 2:
                score += 5000 * save[mv]
            else:
                score -= 2000 * save[mv]

        if len(sim["group_libs"]) == 1 and sim["captures"] == 0:
            score -= 6000

        checked = set()
        r, c = mv
        for nx, ny in neighbors(r, c):
            if sim["board"][nx][ny] == 1 and (nx, ny) not in checked:
                stones, libs = group_and_liberties(sim["board"], nx, ny)
                for s in stones:
                    checked.add(s)
                if len(libs) == 1:
                    score += 300 * len(stones)

        if score > best:
            best = score

    return best


def first_legal(board):
    for p, _ in OPENING_SITES:
        if board[p[0]][p[1]] == 0 and simulate_move(board, p, 1) is not None:
            return p

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0 and simulate_move(board, (r, c), 1) is not None:
                return r, c
    return None


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = build_board(me, opponent)
    total_stones = len(me) + len(opponent)

    groups, pos_to_group = analyze_groups(board)
    tactical_maps = generate_tactical_maps(groups)
    candidates = generate_candidates(board, groups, total_stones)

    scored = []
    for mv in candidates:
        result = evaluate_move(board, groups, pos_to_group, mv, total_stones, tactical_maps)
        if result is not None:
            sc, sim = result
            scored.append((sc, mv, sim))

    if not scored:
        fallback = first_legal(board)
        if fallback is None:
            return (0, 0)
        return (fallback[0] + 1, fallback[1] + 1)

    scored.sort(key=lambda x: x[0], reverse=True)

    best_move = scored[0][1]
    best_score = -10**18
    best_base = -10**18

    for base_score, mv, sim in scored[:6]:
        reply = best_opponent_reply(sim["board"], mv)
        final_score = base_score - 0.85 * reply
        if final_score > best_score or (final_score == best_score and base_score > best_base):
            best_score = final_score
            best_base = base_score
            best_move = mv

    return (best_move[0] + 1, best_move[1] + 1)
