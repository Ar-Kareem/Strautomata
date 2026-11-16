
from __future__ import annotations

N = 19


def _build_geometry():
    neighbors = [[[] for _ in range(N)] for _ in range(N)]
    diagonals = [[[] for _ in range(N)] for _ in range(N)]
    knights = [[[] for _ in range(N)] for _ in range(N)]

    for r in range(N):
        for c in range(N):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    neighbors[r][c].append((rr, cc))

            for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    diagonals[r][c].append((rr, cc))

            for dr, dc in (
                (1, 2), (1, -2), (-1, 2), (-1, -2),
                (2, 1), (2, -1), (-2, 1), (-2, -1),
            ):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    knights[r][c].append((rr, cc))

    return neighbors, diagonals, knights


NEIGHBORS, DIAGONALS, KNIGHTS = _build_geometry()

STAR_LINES = (3, 9, 15)
STAR_POINTS = {(r, c) for r in STAR_LINES for c in STAR_LINES}
CORNER_STARS = {(3, 3), (3, 15), (15, 3), (15, 15)}

INFLUENCE_RADIUS = 6
INFLUENCE_W = [10.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.5]


def _analyze_groups(board):
    visited = [[False] * N for _ in range(N)]
    own_gid = [[-1] * N for _ in range(N)]
    opp_gid = [[-1] * N for _ in range(N)]
    own_groups = []
    opp_groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or visited[r][c]:
                continue

            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))
                for nr, nc in NEIGHBORS[sr][sc]:
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            group = {"stones": stones, "libs": libs}
            if color == 1:
                gid = len(own_groups)
                own_groups.append(group)
                for sr, sc in stones:
                    own_gid[sr][sc] = gid
            else:
                gid = len(opp_groups)
                opp_groups.append(group)
                for sr, sc in stones:
                    opp_gid[sr][sc] = gid

    return own_groups, opp_groups, own_gid, opp_gid


def _is_legal(board, r, c, own_gid, opp_gid, own_groups, opp_groups):
    if board[r][c] != 0:
        return False

    p = (r, c)

    # Capturing any adjacent opponent group makes the move legal.
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == -1:
            gid = opp_gid[nr][nc]
            if gid >= 0:
                libs = opp_groups[gid]["libs"]
                if len(libs) == 1 and p in libs:
                    return True

    # Otherwise the newly connected own group must have at least one liberty.
    libs = set()
    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 0:
            libs.add((nr, nc))
        elif v == 1:
            gid = own_gid[nr][nc]
            if gid >= 0:
                libs.update(own_groups[gid]["libs"])

    libs.discard(p)
    return bool(libs)


def _simulate_result(board, r, c, opp_gid, opp_groups):
    new_board = [row[:] for row in board]
    new_board[r][c] = 1
    p = (r, c)

    captured_gids = []
    seen = set()
    captured_count = 0

    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == -1:
            gid = opp_gid[nr][nc]
            if gid >= 0 and gid not in seen:
                g = opp_groups[gid]
                if len(g["libs"]) == 1 and p in g["libs"]:
                    seen.add(gid)
                    captured_gids.append(gid)
                    for sr, sc in g["stones"]:
                        new_board[sr][sc] = 0
                        captured_count += 1

    # Count liberties of the resulting own group.
    stack = [(r, c)]
    seen_stones = {(r, c)}
    libs = set()
    size = 0

    while stack:
        sr, sc = stack.pop()
        size += 1
        for nr, nc in NEIGHBORS[sr][sc]:
            v = new_board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == 1 and (nr, nc) not in seen_stones:
                seen_stones.add((nr, nc))
                stack.append((nr, nc))

    return captured_count, captured_gids, size, len(libs)


def _is_eyeish(board, r, c, color):
    # Orthogonal neighbors must all be friendly stones; board edge is acceptable.
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] != color:
            return False

    bad_diag = 0
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            if board[rr][cc] == -color:
                bad_diag += 1

    on_edge = r == 0 or r == N - 1 or c == 0 or c == N - 1
    if on_edge:
        return bad_diag <= 1
    return bad_diag == 0


def _influence_arrays(board):
    own_inf = [[0.0] * N for _ in range(N)]
    opp_inf = [[0.0] * N for _ in range(N)]

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0:
                continue
            arr = own_inf if color == 1 else opp_inf

            for dr in range(-INFLUENCE_RADIUS, INFLUENCE_RADIUS + 1):
                rem = INFLUENCE_RADIUS - abs(dr)
                rr = r + dr
                if rr < 0 or rr >= N:
                    continue
                for dc in range(-rem, rem + 1):
                    cc = c + dc
                    if cc < 0 or cc >= N:
                        continue
                    d = abs(dr) + abs(dc)
                    arr[rr][cc] += INFLUENCE_W[d]

    return own_inf, opp_inf


def _influence_gain(board, r, c, own_inf, opp_inf):
    gain = 0.0

    for dr in range(-INFLUENCE_RADIUS, INFLUENCE_RADIUS + 1):
        rem = INFLUENCE_RADIUS - abs(dr)
        rr = r + dr
        if rr < 0 or rr >= N:
            continue
        for dc in range(-rem, rem + 1):
            cc = c + dc
            if cc < 0 or cc >= N:
                continue
            if board[rr][cc] != 0 and not (rr == r and cc == c):
                continue

            d = abs(dr) + abs(dc)
            w = INFLUENCE_W[d]
            diff = own_inf[rr][cc] - opp_inf[rr][cc]

            if diff < -8:
                mult = 2.0
            elif diff < -2:
                mult = 1.6
            elif diff < 4:
                mult = 1.0
            elif diff < 10:
                mult = 0.55
            else:
                mult = 0.22

            gain += w * mult

    return gain


def _line_score(r, c, move_no):
    line = min(r, c, N - 1 - r, N - 1 - c) + 1

    if move_no < 80:
        table = {1: -420, 2: -90, 3: 90, 4: 135, 5: 60, 6: 25}
        return table.get(line, 0)
    if move_no < 200:
        table = {1: -180, 2: 20, 3: 80, 4: 80, 5: 35, 6: 10}
        return table.get(line, 0)

    table = {1: 20, 2: 45, 3: 55, 4: 35, 5: 10}
    return table.get(line, 0)


def _corner_score(board, r, c, move_no):
    score = 0.0

    empty_corner_pref = {
        (3, 3): 1400,
        (2, 2): 1080,
        (2, 3): 1020,
        (3, 2): 1020,
        (2, 4): 760,
        (4, 2): 760,
        (3, 4): 680,
        (4, 3): 680,
        (4, 4): 520,
    }

    approach_points = {
        (2, 5), (5, 2), (3, 5), (5, 3),
        (4, 5), (5, 4), (1, 5), (5, 1),
    }

    phase = 1.0 if move_no < 80 else 0.55 if move_no < 170 else 0.25

    for top in (True, False):
        for left in (True, False):
            a = r if top else N - 1 - r
            b = c if left else N - 1 - c

            if a > 7 or b > 7:
                continue

            own = 0
            opp = 0
            own_locs = []
            opp_locs = []

            for i in range(6):
                rr = i if top else N - 1 - i
                for j in range(6):
                    cc = j if left else N - 1 - j
                    v = board[rr][cc]
                    if v == 1:
                        own += 1
                        own_locs.append((i, j))
                    elif v == -1:
                        opp += 1
                        opp_locs.append((i, j))

            if own + opp == 0:
                if (a, b) in empty_corner_pref:
                    score += empty_corner_pref[(a, b)] * phase
                elif 2 <= a <= 5 and 2 <= b <= 5:
                    score += 230 * phase

            elif opp > 0 and own == 0:
                md = min(abs(a - x) + abs(b - y) for x, y in opp_locs)

                # Approaches and 3-3 invasions against an opponent corner.
                if 2 <= md <= 5 and 1 <= min(a, b) <= 5:
                    score += 360 + 45 * (5 - md)
                if (a, b) in approach_points:
                    score += 520
                if (a, b) == (2, 2) and move_no > 18:
                    score += 560

            elif own > 0 and opp == 0:
                # Modest reward for useful extensions from our own corner.
                if 2 <= min(a, b) <= 4 and 4 <= max(a, b) <= 7:
                    score += 140
                elif 3 <= a <= 6 and 3 <= b <= 6:
                    score += 60

            else:
                # Both players present: local fighting value.
                if a <= 5 and b <= 5:
                    score += 90

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[0] * N for _ in range(N)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1

    move_no = len(me) + len(opponent)

    own_groups, opp_groups, own_gid, opp_gid = _analyze_groups(board)

    legal_moves = []
    for r in range(N):
        for c in range(N):
            if _is_legal(board, r, c, own_gid, opp_gid, own_groups, opp_groups):
                legal_moves.append((r, c))

    if not legal_moves:
        return (0, 0)

    own_inf, opp_inf = _influence_arrays(board)

    own_atari_groups = [i for i, g in enumerate(own_groups) if len(g["libs"]) == 1]
    max_own_atari = 0
    if own_atari_groups:
        max_own_atari = max(len(own_groups[i]["stones"]) for i in own_atari_groups)

    # Small deterministic tie-breaker depending on board state.
    state_hash = 1469598103934665603
    for r, c in me:
        state_hash ^= (r * 37 + c * 131 + 1)
        state_hash *= 1099511628211
    for r, c in opponent:
        state_hash ^= (r * 97 + c * 53 + 7)
        state_hash *= 1099511628211
    state_hash &= 0xFFFFFFFF

    best_move = legal_moves[0]
    best_score = -10**18

    for r, c in legal_moves:
        captured_count, captured_gids, new_size, new_libs = _simulate_result(
            board, r, c, opp_gid, opp_groups
        )
        captured_gid_set = set(captured_gids)

        score = 0.0

        adj_own_ids = set()
        adj_opp_ids = set()
        own_adj = 0
        opp_adj = 0
        empty_adj = 0

        for nr, nc in NEIGHBORS[r][c]:
            v = board[nr][nc]
            if v == 1:
                own_adj += 1
                gid = own_gid[nr][nc]
                if gid >= 0:
                    adj_own_ids.add(gid)
            elif v == -1:
                opp_adj += 1
                gid = opp_gid[nr][nc]
                if gid >= 0:
                    adj_opp_ids.add(gid)
            else:
                empty_adj += 1

        own_diag = sum(1 for nr, nc in DIAGONALS[r][c] if board[nr][nc] == 1)
        opp_diag = sum(1 for nr, nc in DIAGONALS[r][c] if board[nr][nc] == -1)
        own_knight = sum(1 for nr, nc in KNIGHTS[r][c] if board[nr][nc] == 1)
        opp_knight = sum(1 for nr, nc in KNIGHTS[r][c] if board[nr][nc] == -1)

        # Captures are the most urgent positive tactical feature.
        if captured_gids:
            for gid in captured_gids:
                g = opp_groups[gid]
                sz = len(g["stones"])
                score += 4600 + 1150 * sz

                # Capturing stones next to our weak groups is especially valuable.
                touched_own = set()
                for sr, sc in g["stones"]:
                    for ar, ac in NEIGHBORS[sr][sc]:
                        if board[ar][ac] == 1:
                            og = own_gid[ar][ac]
                            if og >= 0:
                                touched_own.add(og)
                for og in touched_own:
                    libs = len(own_groups[og]["libs"])
                    if libs <= 2:
                        score += 350 + 120 * len(own_groups[og]["stones"])

        # Save own groups in atari or low liberties.
        save_value = 0.0
        saves_atari = False
        for gid in adj_own_ids:
            g = own_groups[gid]
            libs_n = len(g["libs"])
            sz = len(g["stones"])
            if (r, c) in g["libs"]:
                if libs_n == 1:
                    saves_atari = True
                    val = 4500 + 900 * sz
                elif libs_n == 2:
                    val = 650 + 90 * sz
                elif libs_n == 3:
                    val = 120 + 25 * sz
                else:
                    val = 25
                save_value += val

        score += save_value

        # If we have a group in atari, ignoring it is usually terrible unless we capture.
        if max_own_atari and not saves_atari and not captured_gids:
            score -= 2200 + 650 * max_own_atari + 250 * len(own_atari_groups)

        # Attack adjacent opponent groups.
        for gid in adj_opp_ids:
            if gid in captured_gid_set:
                continue
            g = opp_groups[gid]
            libs_n = len(g["libs"])
            sz = len(g["stones"])
            if (r, c) in g["libs"]:
                after = libs_n - 1
                if after == 1:
                    score += 1350 + 260 * sz
                elif after == 2:
                    score += 310 + 55 * sz
                elif after == 3:
                    score += 70 + 15 * sz

        # Connections and cuts.
        if len(adj_own_ids) >= 2:
            score += 360 * (len(adj_own_ids) - 1)
            for gid in adj_own_ids:
                if len(own_groups[gid]["libs"]) <= 3:
                    score += 90 + 35 * len(own_groups[gid]["stones"])

        if len(adj_opp_ids) >= 2:
            score += 210 * (len(adj_opp_ids) - 1)
            for gid in adj_opp_ids:
                if gid not in captured_gid_set and len(opp_groups[gid]["libs"]) <= 3:
                    score += 90 + 35 * len(opp_groups[gid]["stones"])

        # Avoid self-atari and cramped moves.
        if new_libs <= 1:
            score -= 3900
            if captured_count:
                score += min(1800, 420 * captured_count)
        elif new_libs == 2:
            score -= 650 if opp_adj else 260
        else:
            score += 35 * min(new_libs, 8)

        if new_size >= 5 and new_libs <= 2 and not captured_gids:
            score -= 700

        # Local shape and contact.
        score += 35 * empty_adj
        score += 42 * own_adj
        score += 56 * own_diag
        score += 23 * own_knight
        score += 27 * opp_diag
        score += 12 * opp_knight

        if opp_adj:
            if own_adj or own_diag or captured_gids or save_value > 0:
                score += 48 * opp_adj
            else:
                score -= 145 * opp_adj

        if opp_adj and own_adj:
            score += 80

        if opp_adj == 0 and own_adj >= 3 and not captured_gids and save_value < 500:
            score -= 360

        # Do not fill our own real eyes unless tactically necessary.
        if _is_eyeish(board, r, c, 1) and not captured_gids and save_value < 1000:
            score -= 6500

        # Playing into an opponent eye without capture is almost never useful.
        if _is_eyeish(board, r, c, -1) and not captured_gids:
            score -= 1800

        # Opening, corner, side, and line heuristics.
        score += _line_score(r, c, move_no)
        score += _corner_score(board, r, c, move_no)

        if (r, c) in STAR_POINTS:
            if (r, c) in CORNER_STARS:
                score += 260 if move_no < 90 else 80
            elif r == 9 and c == 9:
                score += 90 if move_no < 70 else 20
            else:
                score += 360 if move_no < 110 else 120

        # Influence / territory expansion.
        inf_gain = _influence_gain(board, r, c, own_inf, opp_inf)
        score += inf_gain * (1.65 if move_no < 200 else 0.95)

        opp_strength = opp_inf[r][c] - own_inf[r][c]
        own_strength = own_inf[r][c] - opp_inf[r][c]

        tactical = bool(captured_gids) or save_value > 500 or opp_adj >= 2

        if opp_strength > 18 and not tactical and own_adj == 0 and own_diag == 0:
            score -= min(900, opp_strength * 18)

        if own_strength > 28 and opp_adj == 0 and move_no < 260 and not saves_atari:
            score -= min(430, own_strength * 6)

        # Prefer not to play totally isolated late opening moves.
        nearby = own_adj + opp_adj + own_diag + opp_diag + own_knight + opp_knight
        if move_no > 35 and nearby == 0 and (r, c) not in STAR_POINTS:
            score -= 170

        # Tiny deterministic tie-breaker.
        score += (((r + 1) * 1009 + (c + 1) * 9176 + state_hash) % 1000) / 100000.0

        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If only awful own-eye-filling moves remain, pass.
    if best_score < -5000:
        return (0, 0)
    if move_no > 330 and best_score < -1200:
        return (0, 0)
    if move_no > 350 and best_score < -100:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)
