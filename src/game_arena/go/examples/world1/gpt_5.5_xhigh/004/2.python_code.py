
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

STAR_POINTS = {(r, c) for r in (4, 10, 16) for c in (4, 10, 16)}

BIG_POINTS = (
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (3, 3), (3, 17), (17, 3), (17, 17),
    (3, 10), (10, 3), (10, 17), (17, 10),
)
BIG_POINT_RANK = {p: k for k, p in enumerate(BIG_POINTS)}

INF_WEIGHTS = (0.0, 6.0, 4.0, 2.6, 1.7, 1.1, 0.7, 0.4, 0.2)


def build_groups(board):
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for i in range(N):
        for j in range(N):
            color = board[i][j]
            if color == 0 or gid[i][j] != -1:
                continue

            idx = len(groups)
            stack = [(i, j)]
            gid[i][j] = idx
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))

                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < N and 0 <= ny < N:
                        v = board[nx][ny]
                        if v == 0:
                            libs.add((nx, ny))
                        elif v == color and gid[nx][ny] == -1:
                            gid[nx][ny] = idx
                            stack.append((nx, ny))

            groups.append({
                "color": color,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
            })

    return gid, groups


def build_empty_regions(board):
    rid = [[-1] * N for _ in range(N)]
    regions = []

    for i in range(N):
        for j in range(N):
            if board[i][j] != 0 or rid[i][j] != -1:
                continue

            idx = len(regions)
            stack = [(i, j)]
            rid[i][j] = idx
            border = set()
            count = 0

            while stack:
                x, y = stack.pop()
                count += 1

                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < N and 0 <= ny < N:
                        v = board[nx][ny]
                        if v == 0:
                            if rid[nx][ny] == -1:
                                rid[nx][ny] = idx
                                stack.append((nx, ny))
                        else:
                            border.add(v)

            regions.append({"size": count, "border": border})

    return rid, regions


def positional_score(i, j, total):
    r, c = i + 1, j + 1
    edge = min(r, c, N + 1 - r, N + 1 - c)
    open_phase = max(0.0, min(1.0, (90.0 - total) / 90.0))

    line_values = (
        0.0,
        -34.0,  # first line
        -9.0,   # second line
        8.0,    # third line
        12.0,   # fourth line
        7.0,
        4.0,
        2.0,
        1.0,
        0.5,
        0.0,
    )
    val = line_values[edge]

    a = min(r, N + 1 - r)
    b = min(c, N + 1 - c)
    x, y = (a, b) if a <= b else (b, a)

    if x <= 6 and y <= 6:
        if (x, y) == (4, 4):
            val += 14.0 + 38.0 * open_phase
        elif (x, y) == (3, 4):
            val += 12.0 + 30.0 * open_phase
        elif (x, y) == (3, 3):
            val += 8.0 + 24.0 * open_phase
        elif (x, y) in ((4, 5), (3, 5), (4, 6)):
            val += 5.0 + 12.0 * open_phase

    if (r, c) in STAR_POINTS:
        val += 7.0 + 28.0 * open_phase

    if (r, c) == (10, 10):
        val += 4.0 + 12.0 * open_phase

    if edge == 1:
        val -= 10.0 * open_phase
    elif edge == 2:
        val -= 4.0 * open_phase

    return val


def influence_stats(i, j, my_stones, opp_stones):
    own_inf = 0.0
    opp_inf = 0.0
    min_own = 99
    min_opp = 99

    for x, y in my_stones:
        d = abs(i - x) + abs(j - y)
        if d < min_own:
            min_own = d
        if 0 < d < len(INF_WEIGHTS):
            own_inf += INF_WEIGHTS[d]

    for x, y in opp_stones:
        d = abs(i - x) + abs(j - y)
        if d < min_opp:
            min_opp = d
        if 0 < d < len(INF_WEIGHTS):
            opp_inf += INF_WEIGHTS[d]

    return own_inf, opp_inf, min_own, min_opp


def is_eye_like(board, i, j, color):
    if board[i][j] != 0:
        return False

    for dx, dy in DIRS:
        nx, ny = i + dx, j + dy
        if 0 <= nx < N and 0 <= ny < N:
            if board[nx][ny] != color:
                return False

    bad_diag = 0
    off_board = 0
    for dx, dy in DIAGS:
        nx, ny = i + dx, j + dy
        if not (0 <= nx < N and 0 <= ny < N):
            off_board += 1
        elif board[nx][ny] == -color:
            bad_diag += 1

    if off_board >= 2:
        return bad_diag == 0
    if off_board == 1:
        return bad_diag == 0
    return bad_diag <= 1


def move_features(board, gid, groups, i, j):
    own_adj = set()
    opp_adj = set()
    captured = set()
    empty_neighbors = 0
    libs = set()

    for dx, dy in DIRS:
        nx, ny = i + dx, j + dy
        if 0 <= nx < N and 0 <= ny < N:
            v = board[nx][ny]
            if v == 0:
                empty_neighbors += 1
                libs.add((nx, ny))
            elif v == 1:
                own_adj.add(gid[nx][ny])
            elif v == -1:
                og = gid[nx][ny]
                opp_adj.add(og)
                if len(groups[og]["libs"]) == 1:
                    captured.add(og)

    for og in own_adj:
        libs.update(groups[og]["libs"])

    # Captured stones become liberties only if they touch the new connected group.
    for cg in captured:
        for sx, sy in groups[cg]["stones"]:
            touches_new_group = False
            for dx, dy in DIRS:
                tx, ty = sx + dx, sy + dy
                if tx == i and ty == j:
                    touches_new_group = True
                    break
                if 0 <= tx < N and 0 <= ty < N:
                    if board[tx][ty] == 1 and gid[tx][ty] in own_adj:
                        touches_new_group = True
                        break
            if touches_new_group:
                libs.add((sx, sy))

    libs.discard((i, j))

    new_size = 1
    for og in own_adj:
        new_size += groups[og]["size"]

    return own_adj, opp_adj, captured, empty_neighbors, len(libs), new_size


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0] * N for _ in range(N)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1

    my_stones = []
    opp_stones = []
    for i in range(N):
        for j in range(N):
            if board[i][j] == 1:
                my_stones.append((i, j))
            elif board[i][j] == -1:
                opp_stones.append((i, j))

    total = len(my_stones) + len(opp_stones)

    gid, groups = build_groups(board)
    rid, regions = build_empty_regions(board)

    own_atari = {}
    largest_own_atari = 0
    largest_opp_atari = 0

    for idx, g in enumerate(groups):
        if len(g["libs"]) == 1:
            p = next(iter(g["libs"]))
            if g["color"] == 1:
                own_atari.setdefault(p, []).append(idx)
                if g["size"] > largest_own_atari:
                    largest_own_atari = g["size"]
            else:
                if g["size"] > largest_opp_atari:
                    largest_opp_atari = g["size"]

    seed = len(my_stones) * 1009 + len(opp_stones) * 917
    for x, y in my_stones:
        seed = (seed + (x + 1) * 37 + (y + 1) * 101) & 0xFFFFFFFF
    for x, y in opp_stones:
        seed = (seed + (x + 1) * 131 + (y + 1) * 17) & 0xFFFFFFFF

    open_phase = max(0.0, min(1.0, (90.0 - total) / 90.0))
    late_phase = max(0.0, min(1.0, (total - 220.0) / 100.0))

    best = None
    best_score = -10**18
    best_forcing = False

    for i in range(N):
        for j in range(N):
            if board[i][j] != 0:
                continue

            own_adj, opp_adj_all, captured, adj_empty, new_libs, new_size = move_features(
                board, gid, groups, i, j
            )

            # Standard Go suicide check.
            if new_libs <= 0:
                continue

            point = (i, j)
            noncap_opp = opp_adj_all - captured

            capture_size = sum(groups[g]["size"] for g in captured)
            save_gids = own_atari.get(point, ())
            save_size = sum(groups[g]["size"] for g in save_gids)
            max_saved_size = 0
            for g in save_gids:
                if groups[g]["size"] > max_saved_size:
                    max_saved_size = groups[g]["size"]

            score = 0.0

            # Board-location and opening book features.
            score += positional_score(i, j, total)

            rank = BIG_POINT_RANK.get((i + 1, j + 1))
            if rank is not None and open_phase > 0.0:
                score += open_phase * (90.0 - 2.5 * rank)

            own_inf, opp_inf, min_own, min_opp = influence_stats(i, j, my_stones, opp_stones)

            # Captures are the highest priority.
            if captured:
                score += 120.0 * (len(captured) - 1)
                for gidx in captured:
                    s = groups[gidx]["size"]
                    score += 520.0 + 260.0 * s
                    if s >= 2:
                        score += 50.0 * s
                    if s >= 5:
                        score += 80.0

            # Save own groups in atari.
            if save_gids:
                for gidx in save_gids:
                    s = groups[gidx]["size"]
                    score += 360.0 + 210.0 * s
                    if s >= 3:
                        score += 60.0 * s
                if new_libs >= 3:
                    score += 80.0
                elif new_libs == 2:
                    score += 20.0

            # Do not casually abandon sizable groups in atari.
            if largest_own_atari >= 2:
                if max(capture_size, max_saved_size) < largest_own_atari:
                    if largest_own_atari >= 5:
                        score -= 500.0 + 120.0 * largest_own_atari
                    else:
                        score -= 150.0 + 70.0 * largest_own_atari

            # Attack adjacent opponent groups.
            attack_score = 0.0
            for gidx in noncap_opp:
                g = groups[gidx]
                before = len(g["libs"])
                after = before - 1
                s = g["size"]

                if after == 1:
                    attack_score += 260.0 + 120.0 * s
                    if s >= 4:
                        attack_score += 80.0
                elif after == 2:
                    attack_score += 70.0 + 24.0 * s
                elif after == 3:
                    attack_score += 20.0 + 7.0 * s

            score += attack_score

            # Reinforce weak adjacent friendly groups.
            for gidx in own_adj:
                g = groups[gidx]
                before = len(g["libs"])
                s = g["size"]
                if before == 2:
                    score += 75.0 + 24.0 * s
                elif before == 3:
                    score += 24.0 + 8.0 * s
                elif before >= 4:
                    score += 4.0

            # Connections and cuts.
            if len(own_adj) >= 2:
                conn = 110.0 * (len(own_adj) - 1)
                for gidx in own_adj:
                    g = groups[gidx]
                    conn += min(80.0, max(0, 5 - len(g["libs"])) * 18.0 + min(g["size"], 6) * 4.0)
                score += conn

            if len(noncap_opp) >= 2:
                cut = 120.0 * (len(noncap_opp) - 1)
                for gidx in noncap_opp:
                    g = groups[gidx]
                    cut += min(90.0, max(0, 5 - len(g["libs"])) * 22.0 + min(g["size"], 6) * 5.0)
                score += cut

            # Shape and liberties.
            score += 4.0 * adj_empty
            if adj_empty >= 3:
                score += 8.0

            if new_libs == 1:
                if capture_size > 0:
                    score -= 280.0
                    # Very likely ko/snapback; avoid when alternatives exist.
                    if capture_size == 1 and len(captured) == 1 and new_size <= 2:
                        score -= 700.0
                elif save_size > 0:
                    score -= 260.0 + 35.0 * new_size
                else:
                    score -= 1150.0 + 110.0 * new_size
            elif new_libs == 2:
                if capture_size == 0:
                    score -= 70.0 + 12.0 * max(0, new_size - 2)
                else:
                    score -= 20.0
            else:
                score += min(45.0, 9.0 * new_libs)

            if new_libs <= 2 and noncap_opp and capture_size == 0:
                score -= 40.0 * len(noncap_opp)

            forcing = (capture_size > 0 or save_size > 0 or attack_score >= 180.0)

            # Avoid filling real eyes or secure own territory.
            if is_eye_like(board, i, j, 1) and not forcing:
                if len(own_adj) <= 1:
                    score -= 900.0
                else:
                    score -= 350.0

            if is_eye_like(board, i, j, -1) and capture_size == 0:
                score -= 250.0

            # Opening spacing.
            if open_phase > 0.0 and not forcing:
                if min_own == 1:
                    score -= 28.0 * open_phase
                elif min_own == 2:
                    score -= 10.0 * open_phase
                elif 3 <= min_own <= 7:
                    score += (8.0 + 2.0 * min_own) * open_phase

                if min_opp == 1:
                    score -= 18.0 * open_phase
                elif 2 <= min_opp <= 5:
                    score += (10.0 + 2.0 * min_opp) * open_phase
                elif 8 <= min_opp < 99:
                    score += 4.0 * open_phase

                if min_own == 99 and 8 <= min_opp < 99:
                    score += 10.0 * open_phase

            # Influence/frontier evaluation.
            frontier = min(own_inf, opp_inf)
            if frontier > 0.0:
                score += min(35.0, 5.0 * frontier)

            diff = own_inf - opp_inf
            if not forcing:
                if diff > 5.0 and len(noncap_opp) == 0:
                    score -= min(35.0, 3.0 * (diff - 5.0)) * (0.7 + late_phase)
                elif diff < -5.0 and len(own_adj) == 0:
                    if new_libs >= 3 and (min_own <= 5 or total < 120):
                        score += min(22.0, 1.8 * (-diff - 5.0))
                    else:
                        score -= min(45.0, 2.5 * (-diff - 5.0))
                else:
                    score += 0.8 * (own_inf + opp_inf)
            else:
                score += 0.4 * own_inf

            # Local contact shape.
            if len(noncap_opp) > 0 and len(own_adj) > 0:
                score += 30.0
            elif len(noncap_opp) > 0 and len(own_adj) == 0 and capture_size == 0:
                if min_own <= 3:
                    score += 10.0
                elif adj_empty <= 2:
                    score -= 25.0

            if len(own_adj) > 0 and len(noncap_opp) == 0 and adj_empty <= 1 and not forcing:
                score -= 25.0

            # Empty-region ownership/endgame logic.
            reg = regions[rid[i][j]]
            border = reg["border"]
            rsize = reg["size"]

            if not forcing:
                if border == {1}:
                    if rsize <= 20 or late_phase > 0.25:
                        score -= (45.0 + min(100.0, 4.0 * rsize)) * (0.7 + late_phase)
                elif border == {-1}:
                    if rsize <= 8 and min_own > 4:
                        score -= 60.0 + 60.0 * late_phase
                    elif rsize >= 20 and new_libs >= 3:
                        score += 18.0 if total < 260 else 8.0
                elif len(border) == 2:
                    score += 18.0 + min(18.0, 0.3 * rsize)
                else:
                    score += 10.0 * open_phase

            # Tiny deterministic tie-breaker.
            tie = (((i + 1) * 73856093) ^ ((j + 1) * 19349663) ^ seed) & 1023
            score += tie * 1.0e-6

            if score > best_score:
                best_score = score
                best = (i, j)
                best_forcing = forcing

    if best is None:
        return (0, 0)

    urgent = largest_own_atari >= 2 or largest_opp_atari >= 2

    # In late game, pass instead of filling only bad/self-damaging points.
    if total > 180 and not best_forcing and not urgent and best_score < -80.0:
        return (0, 0)
    if total > 260 and not best_forcing and not urgent and best_score < 10.0:
        return (0, 0)
    if total > 335 and not best_forcing and not urgent and best_score < 100.0:
        return (0, 0)

    return (best[0] + 1, best[1] + 1)
