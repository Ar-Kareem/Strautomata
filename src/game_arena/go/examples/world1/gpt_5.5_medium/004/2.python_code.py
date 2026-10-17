
from collections import deque

N = 19


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0 for _ in range(N)] for _ in range(N)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2

    total_stones = len(me) + len(opponent)

    def on_board(r, c):
        return 0 <= r < N and 0 <= c < N

    def neigh(r, c):
        if r > 0:
            yield r - 1, c
        if r < N - 1:
            yield r + 1, c
        if c > 0:
            yield r, c - 1
        if c < N - 1:
            yield r, c + 1

    def build_groups(color):
        visited = set()
        groups = []
        stone_to_gid = {}

        for r in range(N):
            for c in range(N):
                if board[r][c] != color or (r, c) in visited:
                    continue

                q = deque([(r, c)])
                visited.add((r, c))
                stones = set()
                libs = set()

                while q:
                    x, y = q.popleft()
                    stones.add((x, y))

                    for nx, ny in neigh(x, y):
                        v = board[nx][ny]
                        if v == 0:
                            libs.add((nx, ny))
                        elif v == color and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            q.append((nx, ny))

                gid = len(groups)
                groups.append((stones, libs))
                for s in stones:
                    stone_to_gid[s] = gid

        return groups, stone_to_gid

    my_groups, my_gid = build_groups(1)
    opp_groups, opp_gid = build_groups(2)

    def analyze_move(r, c):
        if not on_board(r, c) or board[r][c] != 0:
            return None

        adj_my = set()
        adj_opp = set()

        for nr, nc in neigh(r, c):
            if board[nr][nc] == 1:
                adj_my.add(my_gid[(nr, nc)])
            elif board[nr][nc] == 2:
                adj_opp.add(opp_gid[(nr, nc)])

        captured = set()
        for gid in adj_opp:
            stones, libs = opp_groups[gid]
            if len(libs) == 1 and (r, c) in libs:
                captured.update(stones)

        result_stones = {(r, c)}
        for gid in adj_my:
            result_stones.update(my_groups[gid][0])

        result_libs = set()
        for sx, sy in result_stones:
            for nx, ny in neigh(sx, sy):
                if (nx, ny) == (r, c):
                    continue

                v = board[nx][ny]
                if v == 0:
                    result_libs.add((nx, ny))
                elif v == 2 and (nx, ny) in captured:
                    result_libs.add((nx, ny))

        legal = bool(captured) or bool(result_libs)
        if not legal:
            return None

        # With no game history available, the only uncertain legality is ko.
        # A one-stone capture that leaves the played group with one liberty is
        # the classic possible ko-recapture shape, so avoid it for safety.
        ko_risky = len(captured) == 1 and len(result_libs) == 1

        return {
            "adj_my": adj_my,
            "adj_opp": adj_opp,
            "captured": captured,
            "libs": result_libs,
            "ko_risky": ko_risky,
        }

    def own_eye_penalty(r, c, info):
        if info["captured"]:
            return 0

        orth_good = 0
        opp_adjacent = False

        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not on_board(nr, nc):
                orth_good += 1
            elif board[nr][nc] == 1:
                orth_good += 1
            elif board[nr][nc] == 2:
                opp_adjacent = True

        if opp_adjacent:
            return 0

        diag_good = 0
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr, nc = r + dr, c + dc
            if not on_board(nr, nc):
                diag_good += 1
            elif board[nr][nc] == 1:
                diag_good += 1

        if orth_good == 4 and diag_good >= 3:
            return -700
        if orth_good >= 3 and diag_good >= 2:
            return -320
        if orth_good >= 3:
            return -160
        return 0

    star_points = {
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
    }

    corner_stars = [(3, 3), (3, 15), (15, 3), (15, 15)]

    def positional_score(r, c):
        score = 0.0

        line = min(r + 1, c + 1, N - r, N - c)

        if total_stones < 80:
            if line == 4:
                score += 24
            elif line == 3:
                score += 16
            elif line == 5:
                score += 8
            elif line <= 2:
                score -= 22
        else:
            if line == 1:
                score -= 12
            elif line == 2:
                score += 2
            elif line in (3, 4):
                score += 7

        if (r, c) in star_points:
            score += 42 if total_stones < 60 else 10

        if (r, c) == (9, 9):
            score += 10 if total_stones < 80 else 3

        # Prefer open corners early.
        if total_stones < 60:
            for sr, sc in corner_stars:
                near_this_corner = (
                    (sr == 3 and r <= 7 or sr == 15 and r >= 11) and
                    (sc == 3 and c <= 7 or sc == 15 and c >= 11)
                )
                if not near_this_corner:
                    continue

                occupied_near = 0
                for x in range(max(0, sr - 4), min(N, sr + 5)):
                    for y in range(max(0, sc - 4), min(N, sc + 5)):
                        if board[x][y] != 0:
                            occupied_near += 1

                if occupied_near == 0:
                    score += max(0, 55 - 7 * (abs(r - sr) + abs(c - sc)))
                elif occupied_near <= 2:
                    score += max(0, 24 - 5 * (abs(r - sr) + abs(c - sc)))

        # Slight centrality without overvaluing the middle.
        dist_center = abs(r - 9) + abs(c - 9)
        score += max(0, 9 - dist_center) * 0.8

        return score

    def influence_score(r, c):
        score = 0.0
        friendly_close = 0
        enemy_close = 0

        for sr, sc in me:
            x, y = sr - 1, sc - 1
            d = abs(r - x) + abs(c - y)
            if d == 1:
                score += 20
                friendly_close += 1
            elif d == 2:
                score += 12
            elif d == 3:
                score += 6
            elif d == 4:
                score += 2

        for sr, sc in opponent:
            x, y = sr - 1, sc - 1
            d = abs(r - x) + abs(c - y)
            if d == 1:
                score += 7
                enemy_close += 1
            elif d == 2:
                score += 16
            elif d == 3:
                score += 8
            elif d == 4:
                score += 3

        # Contact against enemy stones is better with friendly support.
        if enemy_close and not friendly_close:
            score -= 10 * enemy_close

        # Avoid excessive clumping.
        if friendly_close >= 3 and enemy_close == 0:
            score -= 20

        return score

    def score_move(r, c, info):
        score = 0.0
        libs_after = len(info["libs"])
        cap_count = len(info["captured"])

        score += positional_score(r, c)
        score += influence_score(r, c)

        # Capturing and attacking.
        for gid in info["adj_opp"]:
            stones, libs = opp_groups[gid]
            size = len(stones)
            l = len(libs)

            if (r, c) not in libs:
                continue

            if l == 1:
                score += 1250 + 105 * size
            elif l == 2:
                score += 190 + 18 * size
            elif l == 3:
                score += 48 + 6 * size
            else:
                score += 8 + size

        if cap_count:
            score += 120 * cap_count

        # Saving and connecting.
        adjacent_my_groups = len(info["adj_my"])
        if adjacent_my_groups >= 2:
            score += 95 * (adjacent_my_groups - 1)

        for gid in info["adj_my"]:
            stones, libs = my_groups[gid]
            size = len(stones)
            l = len(libs)

            if (r, c) not in libs:
                continue

            if l == 1:
                score += 1150 + 95 * size + 18 * libs_after
            elif l == 2:
                score += 175 + 14 * size
            elif l == 3:
                score += 50 + 5 * size
            else:
                score += 8

        # Liberties of the resulting group.
        score += min(libs_after, 8) * 13

        if libs_after == 1:
            score -= 190 if not cap_count else 45
        elif libs_after == 2:
            score -= 45 if not cap_count else 5

        # Cutting shape: adjacent to multiple enemy groups.
        if len(info["adj_opp"]) >= 2:
            score += 70 * (len(info["adj_opp"]) - 1)

        # Avoid filling real or likely own eyes.
        score += own_eye_penalty(r, c, info)

        # Prefer moves with some local relevance after the opening.
        if total_stones > 35:
            local = False
            for nr in range(max(0, r - 2), min(N, r + 3)):
                for nc in range(max(0, c - 2), min(N, c + 3)):
                    if board[nr][nc] != 0:
                        local = True
                        break
                if local:
                    break
            if not local:
                score -= 35

        # Tiny deterministic tie-breaker, stable and harmless.
        score += ((r + 1) * 37 + (c + 1) * 17) * 0.0001

        return score

    best_move = None
    best_score = -10**18

    # First, examine every point. 361 points is tiny under the time limit and
    # avoids missing global opening moves or distant endgame plays.
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            info = analyze_move(r, c)
            if info is None:
                continue

            if info["ko_risky"]:
                continue

            s = score_move(r, c, info)

            if s > best_score:
                best_score = s
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # In the late game, do not fill obvious own territory or play very bad
    # self-damaging moves merely because they are legal.
    if total_stones > 180 and best_score < -30:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)
