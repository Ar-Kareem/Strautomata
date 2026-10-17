
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
_INF_WEIGHTS = (0, 12, 7, 4, 2)


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _tf_corner(r, c, corner):
    if corner == 0:      # top-left
        return r, c
    if corner == 1:      # top-right
        return r, N - 1 - c
    if corner == 2:      # bottom-left
        return N - 1 - r, c
    return N - 1 - r, N - 1 - c  # bottom-right


def _make_corner_maps():
    # 0-indexed patterns relative to top-left corner.
    base_open = [
        (3, 3, 900),   # 4-4
        (2, 3, 720),   # 3-4
        (3, 2, 720),   # 4-3
        (2, 2, 560),   # 3-3
        (4, 3, 430),
        (3, 4, 430),
    ]
    base_approach = [
        (2, 5, 440),
        (5, 2, 440),
        (3, 5, 390),
        (5, 3, 390),
        (4, 5, 330),
        (5, 4, 330),
        (2, 6, 260),
        (6, 2, 260),
    ]

    open_maps = []
    approach_maps = []
    for k in range(4):
        od = {}
        ad = {}
        for r, c, s in base_open:
            od[_tf_corner(r, c, k)] = s
        for r, c, s in base_approach:
            ad[_tf_corner(r, c, k)] = s
        open_maps.append(od)
        approach_maps.append(ad)
    return open_maps, approach_maps


_CORNER_OPEN_MAPS, _CORNER_APPROACH_MAPS = _make_corner_maps()


def _make_opening_bonus():
    d = {}

    def add(p, v):
        if v > d.get(p, -10**9):
            d[p] = v

    # Star points and major side points.
    for p in ((3, 3), (3, 15), (15, 3), (15, 15)):
        add(p, 360)
    for p in ((3, 9), (9, 3), (9, 15), (15, 9)):
        add(p, 250)
    add((9, 9), 170)

    # 3-4 / 4-3 corner alternatives.
    for p in (
        (2, 3), (3, 2), (2, 15), (3, 16),
        (15, 2), (16, 3), (15, 16), (16, 15),
    ):
        add(p, 230)

    # 3-3 points are playable, but usually not first choice.
    for p in ((2, 2), (2, 16), (16, 2), (16, 16)):
        add(p, 150)

    return d


_OPENING_BONUS = _make_opening_bonus()


def _make_board(me, opponent):
    board = [[0] * N for _ in range(N)]

    for p in me:
        try:
            r, c = p
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1

    for p in opponent:
        try:
            r, c = p
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1

    return board


def _board_hash(board):
    # Compact immutable whole-board position.
    return bytes((cell + 1) for row in board for cell in row)


def _analyze(board):
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 or gid[r][c] != -1:
                continue

            color = board[r][c]
            idx = len(groups)
            stack = [(r, c)]
            gid[r][c] = idx
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))

                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    if not _inside(nr, nc):
                        continue
                    val = board[nr][nc]
                    if val == 0:
                        libs.add((nr, nc))
                    elif val == color and gid[nr][nc] == -1:
                        gid[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append({
                "color": color,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
            })

    return groups, gid


def _group_stats(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    libs = set()
    size = 0

    while stack:
        sr, sc = stack.pop()
        size += 1

        for dr, dc in DIRS:
            nr, nc = sr + dr, sc + dc
            if not _inside(nr, nc):
                continue
            val = board[nr][nc]
            if val == 0:
                libs.add((nr, nc))
            elif val == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return size, len(libs)


def _build_tactical_maps(groups):
    own_atari = {}
    opp_atari = {}
    own_two = {}
    opp_two = {}
    own_three = {}
    opp_three = {}

    def add(d, key, value):
        d.setdefault(key, []).append(value)

    for i, g in enumerate(groups):
        libs = g["libs"]
        l = len(libs)
        color = g["color"]

        if l == 1:
            lib = next(iter(libs))
            add(own_atari if color == 1 else opp_atari, lib, i)
        elif l == 2:
            target = own_two if color == 1 else opp_two
            for lib in libs:
                add(target, lib, i)
        elif l == 3:
            target = own_three if color == 1 else opp_three
            for lib in libs:
                add(target, lib, i)

    return own_atari, opp_atari, own_two, opp_two, own_three, opp_three


def _try_play(board, groups, gid, r, c, color=1, ko_hash=None):
    if board[r][c] != 0:
        return None

    captured = []
    seen_enemy = set()

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc) or board[nr][nc] != -color:
            continue

        gi = gid[nr][nc]
        if gi in seen_enemy:
            continue
        seen_enemy.add(gi)

        g = groups[gi]
        if len(g["libs"]) == 1 and (r, c) in g["libs"]:
            captured.append(gi)

    # Suicide check before copying board, unless we capture something.
    if not captured:
        libs = set()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not _inside(nr, nc):
                continue
            val = board[nr][nc]
            if val == 0:
                libs.add((nr, nc))
            elif val == color:
                libs.update(groups[gid[nr][nc]]["libs"])

        libs.discard((r, c))
        if not libs:
            return None

    nb = [row[:] for row in board]
    nb[r][c] = color

    cap_count = 0
    for gi in captured:
        g = groups[gi]
        cap_count += g["size"]
        for sr, sc in g["stones"]:
            nb[sr][sc] = 0

    self_size, self_libs = _group_stats(nb, r, c)
    if self_libs <= 0:
        return None

    h = _board_hash(nb)
    if ko_hash is not None and h == ko_hash:
        return None

    return cap_count, tuple(captured), self_size, self_libs, h


def _is_eye_like(board, r, c, color):
    if board[r][c] != 0:
        return False

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc) and board[nr][nc] != color:
            return False

    bad_diag = 0
    off_board = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc):
            off_board += 1
        elif board[nr][nc] == -color:
            bad_diag += 1

    if off_board:
        return bad_diag == 0
    return bad_diag <= 1


def _local_influence(board, r, c):
    own = 0
    opp = 0
    empty_close = 0

    for dr in range(-4, 5):
        nr = r + dr
        if nr < 0 or nr >= N:
            continue
        for dc in range(-4, 5):
            nc = c + dc
            if nc < 0 or nc >= N:
                continue

            dist = abs(dr) + abs(dc)
            if dist == 0 or dist > 4:
                continue

            val = board[nr][nc]
            w = _INF_WEIGHTS[dist]
            if val == 1:
                own += w
            elif val == -1:
                opp += w
            elif dist <= 2:
                empty_close += 1

    return own, opp, empty_close


def _corner_counts(board):
    out = []
    for k in range(4):
        rows = range(0, 6) if k in (0, 1) else range(N - 6, N)
        cols = range(0, 6) if k in (0, 2) else range(N - 6, N)

        own = 0
        opp = 0
        for r in rows:
            for c in cols:
                if board[r][c] == 1:
                    own += 1
                elif board[r][c] == -1:
                    opp += 1
        out.append((own, opp))
    return out


def _score_move(board, groups, gid, r, c, res, total_stones, maps, corner_counts):
    cap_count, captured_gids, self_size, self_libs, _h = res
    own_atari, opp_atari, own_two, opp_two, own_three, opp_three = maps
    pos = (r, c)

    score = 0.0
    tactical = cap_count > 0

    # Captures and atari tactics.
    if cap_count:
        score += 3000 + 500 * cap_count + 250 * len(captured_gids)
        if cap_count >= 3:
            score += 250 * cap_count

    for gi in opp_atari.get(pos, ()):
        tactical = True
        sz = groups[gi]["size"]
        score += 7000 + 900 * sz

    for gi in own_atari.get(pos, ()):
        tactical = True
        sz = groups[gi]["size"]
        score += 10000 + 1800 * sz + 80 * self_libs

    for gi in opp_two.get(pos, ()):
        tactical = True
        sz = groups[gi]["size"]
        score += 1600 + 170 * min(sz, 30)

    for gi in own_two.get(pos, ()):
        tactical = True
        sz = groups[gi]["size"]
        score += 1300 + 190 * min(sz, 30)

    for gi in opp_three.get(pos, ()):
        sz = groups[gi]["size"]
        score += 330 + 55 * min(sz, 25)

    for gi in own_three.get(pos, ()):
        sz = groups[gi]["size"]
        score += 300 + 60 * min(sz, 25)

    # Adjacency and shape.
    adj_own = set()
    adj_opp = set()
    empty_n = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc):
            continue
        val = board[nr][nc]
        if val == 0:
            empty_n += 1
        elif val == 1:
            adj_own.add(gid[nr][nc])
        elif val == -1:
            adj_opp.add(gid[nr][nc])

    score += 25 * empty_n + 16 * min(self_libs, 14) + 3 * min(self_size, 20)

    if self_libs >= 4:
        score += 45
    if self_libs >= 6:
        score += 45

    if adj_own:
        score += 65 * len(adj_own)
        if len(adj_own) >= 2:
            score += 320 * (len(adj_own) - 1)

        for gi in adj_own:
            g = groups[gi]
            l = len(g["libs"])
            sz = g["size"]
            score += 8 * min(sz, 14)
            if l <= 2:
                score += (3 - l) * 430 + 38 * min(sz, 18)
            elif l == 3:
                score += 120

    if adj_opp:
        if len(adj_opp) >= 2:
            score += 210 * (len(adj_opp) - 1)

        for gi in adj_opp:
            g = groups[gi]
            l = len(g["libs"])
            sz = g["size"]
            if l == 1:
                score += 500 + 45 * min(sz, 20)
            elif l == 2:
                score += 440 + 55 * min(sz, 20)
            elif l == 3:
                score += 190 + 25 * min(sz, 20)
            elif l >= 5 and cap_count == 0:
                score -= 75

        if not adj_own and self_libs <= 3 and cap_count == 0:
            score -= 260

    # Diagonal shape and cutting potential.
    diag_own = 0
    diag_opp = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc):
            continue
        if board[nr][nc] == 1:
            diag_own += 1
        elif board[nr][nc] == -1:
            diag_opp += 1

    score += 22 * diag_own + 13 * diag_opp
    if diag_own >= 2 and not adj_own:
        score += 120
    if diag_opp >= 2 and adj_own:
        score += 90

    # Avoid filling our own real eyes and very safe territory.
    if cap_count == 0 and _is_eye_like(board, r, c, 1):
        score -= 7000

    if cap_count == 0 and _is_eye_like(board, r, c, -1):
        score -= 1800

    # Opening/fuseki preferences.
    open_factor = max(0.0, (100.0 - total_stones) / 100.0)
    if open_factor > 0:
        score += _OPENING_BONUS.get(pos, 0) * open_factor

        for k in range(4):
            ownc, oppc = corner_counts[k]

            ob = _CORNER_OPEN_MAPS[k].get(pos, 0)
            if ob:
                if ownc == 0 and oppc == 0:
                    score += ob * open_factor
                elif ownc > 0 and oppc == 0 and total_stones < 50:
                    score -= 120 * open_factor

            ab = _CORNER_APPROACH_MAPS[k].get(pos, 0)
            if ab:
                if ownc == 0 and oppc > 0:
                    score += ab * open_factor
                elif ownc > 0 and oppc > 0:
                    score += 0.35 * ab * open_factor

    # Board geometry: favor 3rd/4th line, avoid first line unless tactical.
    edge = min(r, c, N - 1 - r, N - 1 - c)
    if total_stones < 80:
        if edge == 3:
            score += 180
        elif edge == 2:
            score += 145
        elif edge == 4:
            score += 75
        elif edge == 1:
            score -= 80
        elif edge == 0:
            score -= 230
        elif edge >= 7:
            score -= 35
    else:
        if edge == 0:
            score -= 145
        elif edge == 1:
            score += 8
        elif edge == 2:
            score += 68
        elif edge == 3:
            score += 58

    # Local influence: play near relevant stones but avoid hopeless contact.
    own_inf, opp_inf, empty_close = _local_influence(board, r, c)
    score += 4.0 * own_inf + 3.2 * opp_inf + 4 * min(empty_close, 10)

    if own_inf == 0 and opp_inf == 0 and total_stones > 40:
        score -= 120

    if opp_inf > own_inf + 18 and not adj_own and cap_count == 0:
        score -= 180

    if own_inf > opp_inf + 35 and not adj_opp and cap_count == 0 and total_stones > 70:
        score -= 420

    if total_stones < 40 and adj_opp and not tactical:
        score -= 110

    # Self-atari / shortage-of-liberties avoidance.
    if self_libs <= 1:
        if cap_count == 0:
            score -= 8000
        else:
            score -= max(500.0, 3600.0 - 650.0 * cap_count)
    elif self_libs == 2:
        score -= 150 if tactical else 450

    if self_size > 6 and self_libs <= 2:
        score -= 80 * min(self_size, 20)

    # Deterministic tiny tie-breaker.
    score += ((r * 37 + c * 101 + total_stones * 17) % 997) / 10000.0

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    board = _make_board(me, opponent)
    groups, gid = _analyze(board)
    maps = _build_tactical_maps(groups)
    corner_info = _corner_counts(board)

    total_stones = 0
    for row in board:
        for v in row:
            if v != 0:
                total_stones += 1

    current_hash = _board_hash(board)

    # Avoid immediate repetition/ko if our previous post-move board is known.
    ko_hash = memory.get("last_my_hash")
    if total_stones <= 1 or ko_hash == current_hash:
        ko_hash = None

    best_move = None
    best_res = None
    best_score = -10**100

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            res = _try_play(board, groups, gid, r, c, 1, ko_hash)
            if res is None:
                continue

            s = _score_move(board, groups, gid, r, c, res, total_stones, maps, corner_info)
            if s > best_score:
                best_score = s
                best_move = (r, c)
                best_res = res

    try:
        memory["turn"] = int(memory.get("turn", 0)) + 1
    except Exception:
        memory["turn"] = 1

    # Pass only when every legal move looks actively harmful, usually late.
    if best_move is None:
        action = (0, 0)
        memory["last_my_hash"] = current_hash
    else:
        should_pass = False
        if best_score < -5000:
            should_pass = True
        elif total_stones > 260 and best_score < -1200:
            should_pass = True
        elif total_stones > 330 and best_score < 0:
            should_pass = True

        if should_pass:
            action = (0, 0)
            memory["last_my_hash"] = current_hash
        else:
            action = (best_move[0] + 1, best_move[1] + 1)
            memory["last_my_hash"] = best_res[4]

    # Final safety check: if anything unexpected happened, pass.
    if action != (0, 0):
        rr, cc = action
        if not (1 <= rr <= N and 1 <= cc <= N and board[rr - 1][cc - 1] == 0):
            action = (0, 0)
            memory["last_my_hash"] = current_hash

    return action, memory
