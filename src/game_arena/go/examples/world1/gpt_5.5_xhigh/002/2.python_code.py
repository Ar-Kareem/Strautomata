
N = 19

EMPTY = 0
ME = 1
OPP = 2

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

# Internal coordinates: 4-4, 10-10, 16-16 are 3, 9, 15.
_STAR_COORDS = (3, 9, 15)

_LINE_EARLY = (0, -220, -75, 70, 90, 35, 12, 4)
_LINE_MID = (0, -90, 5, 42, 48, 22, 8, 2)
_LINE_LATE = (0, -18, 18, 25, 16, 8, 2, 0)

_EMPTY_CORNER = {
    (4, 4): 520,
    (3, 4): 470,
    (4, 3): 470,
    (3, 3): 360,
    (4, 5): 180,
    (5, 4): 180,
    (3, 5): 145,
    (5, 3): 145,
}

_APPROACH_CORNER = {
    (3, 3): 270,
    (3, 4): 170,
    (4, 3): 170,
    (4, 4): 135,
    (3, 5): 310,
    (5, 3): 310,
    (4, 6): 270,
    (6, 4): 270,
    (5, 5): 120,
    (2, 4): 90,
    (4, 2): 90,
}

_OWN_CORNER_EXT = {
    (3, 5), (5, 3), (4, 5), (5, 4),
    (4, 6), (6, 4), (3, 6), (6, 3),
}

_STRAIGHT_TWO = ((2, 0), (-2, 0), (0, 2), (0, -2))
_KNIGHTS = (
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1),
)


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _build_board(me, opponent):
    board = [[EMPTY] * N for _ in range(N)]

    for rr, cc in me:
        r, c = rr - 1, cc - 1
        if _inside(r, c):
            board[r][c] = ME

    for rr, cc in opponent:
        r, c = rr - 1, cc - 1
        if _inside(r, c) and board[r][c] == EMPTY:
            board[r][c] = OPP

    return board


def _collect_group(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    libs = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))

        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not _inside(nx, ny):
                continue
            v = board[nx][ny]
            if v == EMPTY:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))

    return stones, libs


def _collect_groups(board, color):
    visited = [[False] * N for _ in range(N)]
    groups = []
    index = {}

    for r in range(N):
        for c in range(N):
            if board[r][c] == color and not visited[r][c]:
                stones, libs = _collect_group(board, r, c)
                gid = len(groups)
                for sr, sc in stones:
                    visited[sr][sc] = True
                    index[(sr, sc)] = gid
                groups.append({"stones": stones, "libs": libs, "size": len(stones)})

    return groups, index


def _make_lib_map(groups):
    lib_map = {}
    for gid, group in enumerate(groups):
        for p in group["libs"]:
            if p in lib_map:
                lib_map[p].append(gid)
            else:
                lib_map[p] = [gid]
    return lib_map


def _simulate(board, r, c):
    """Return resulting info if legal under normal no-suicide rules, else None."""
    if not _inside(r, c) or board[r][c] != EMPTY:
        return None

    b = [row[:] for row in board]
    b[r][c] = ME

    captured = []
    checked = set()

    for dx, dy in DIRS:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc) and b[nr][nc] == OPP and (nr, nc) not in checked:
            stones, libs = _collect_group(b, nr, nc)
            checked.update(stones)
            if not libs:
                captured.extend(stones)
                for sr, sc in stones:
                    b[sr][sc] = EMPTY

    new_stones, new_libs = _collect_group(b, r, c)
    if not new_libs:
        return None

    return b, captured, new_stones, new_libs


def _simple_ko_shape(info):
    # A one-stone capture by a single stone with one liberty is the common
    # immediate-ko-recapture shape. We heavily avoid it because history is not
    # provided by the API.
    return len(info[1]) == 1 and len(info[2]) == 1 and len(info[3]) == 1


def _is_eye_like(board, r, c, color):
    if board[r][c] != EMPTY:
        return False
    for dx, dy in DIRS:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc) and board[nr][nc] != color:
            return False
    return True


def _is_true_eye(board, r, c, color):
    if not _is_eye_like(board, r, c, color):
        return False

    enemy = OPP if color == ME else ME
    valid_diags = 0
    enemy_diags = 0

    for dx, dy in DIAGS:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc):
            valid_diags += 1
            if board[nr][nc] == enemy:
                enemy_diags += 1

    # On edge/corner, any enemy diagonal is suspicious. In the center, one bad
    # diagonal can still be a real eye.
    if valid_diags < 4:
        return enemy_diags == 0
    return enemy_diags <= 1


def _compute_heat(board):
    my_heat = [[0] * N for _ in range(N)]
    opp_heat = [[0] * N for _ in range(N)]
    weights = (0, 9, 6, 4, 2, 1)

    for r in range(N):
        for c in range(N):
            v = board[r][c]
            if v == EMPTY:
                continue
            target = my_heat if v == ME else opp_heat

            for dr in range(-5, 6):
                nr = r + dr
                if not (0 <= nr < N):
                    continue
                rem = 5 - abs(dr)
                for dc in range(-rem, rem + 1):
                    d = abs(dr) + abs(dc)
                    if d == 0:
                        continue
                    nc = c + dc
                    if 0 <= nc < N:
                        target[nr][nc] += weights[d]

    return my_heat, opp_heat


def _corner_score(board, r, c, total):
    if total < 80:
        scale = 100
    elif total < 160:
        scale = 65
    else:
        scale = 35

    score = 0

    for top, left in ((True, True), (True, False), (False, True), (False, False)):
        a = r + 1 if top else N - r
        b = c + 1 if left else N - c
        if a > 7 or b > 7:
            continue

        own = 0
        opp = 0

        for ia in range(7):
            rr = ia if top else N - 1 - ia
            row = board[rr]
            for ib in range(7):
                cc = ib if left else N - 1 - ib
                v = row[cc]
                if v == ME:
                    own += 1
                elif v == OPP:
                    opp += 1

        key = (a, b)

        if own + opp == 0:
            score += _EMPTY_CORNER.get(key, 0) * scale // 100
        elif opp > 0 and own == 0:
            local_scale = 100 if total < 120 else 70
            score += _APPROACH_CORNER.get(key, 0) * local_scale // 100
        elif own > 0 and opp == 0:
            if key in _OWN_CORNER_EXT:
                score += 100 * scale // 100
            if own >= 2 and a <= 5 and b <= 5:
                score -= 120
        else:
            if a <= 4 and b <= 4:
                score += 90
            elif a <= 6 and b <= 6:
                score += 45

    return score


def _positional_score(board, r, c, total):
    line = min(r, c, N - 1 - r, N - 1 - c) + 1

    if total < 80:
        vals = _LINE_EARLY
    elif total < 230:
        vals = _LINE_MID
    else:
        vals = _LINE_LATE

    score = vals[line] if line < len(vals) else 0

    if total < 140:
        if r in _STAR_COORDS:
            score += 18
        if c in _STAR_COORDS:
            score += 18
        if r in _STAR_COORDS and c in _STAR_COORDS:
            score += 20

    if total < 50:
        center_dist = abs(r - 9) + abs(c - 9)
        score += max(0, 10 - center_dist)

    score += _corner_score(board, r, c, total)
    return score


def _noise(r, c, total):
    # Small deterministic tie-breaker.
    x = ((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ ((total + 11) * 83492791)
    x &= 0xFFFFFFFF
    x ^= (x >> 16)
    return (x % 17) - 8


def _score_move(
    board,
    r,
    c,
    info,
    groups_me,
    groups_opp,
    idx_me,
    idx_opp,
    lib_me,
    lib_opp,
    heat_me,
    heat_opp,
    total,
    my_atari_ids,
):
    move = (r, c)
    _, captured, new_stones, new_libs = info

    cap_n = len(captured)
    new_size = len(new_stones)
    lib_n = len(new_libs)

    score = _positional_score(board, r, c, total)
    tactical = False

    my_ids = lib_me.get(move, ())
    opp_ids = lib_opp.get(move, ())
    saved_atari = set()

    # Captures.
    if cap_n:
        tactical = True
        score += 7600 + 2600 * cap_n
        if cap_n >= 3:
            score += 900 * (cap_n - 2)

    # Defend our weak groups by playing their liberties.
    for gid in my_ids:
        g = groups_me[gid]
        libs = len(g["libs"])
        size = g["size"]

        if libs == 1:
            tactical = True
            saved_atari.add(gid)
            score += 10500 + 1700 * size
            score += min(10, lib_n) * 180
        elif libs == 2:
            score += 1150 + 170 * size
            if size >= 4:
                score += 500
        elif libs == 3:
            score += 260 + 45 * size

    # Attack opponent groups by occupying liberties.
    for gid in opp_ids:
        g = groups_opp[gid]
        libs = len(g["libs"])
        size = g["size"]

        if libs == 1:
            tactical = True
            score += 9500 + 1700 * size
        elif libs == 2:
            tactical = True
            score += 1900 + 260 * size
        elif libs == 3:
            score += 430 + 80 * size
        elif libs == 4 and total < 180:
            score += 100 + 20 * min(size, 8)

    # If we have groups in atari, do not ignore them unless there is compensation.
    if my_atari_ids:
        unsaved_size = 0
        unsaved_count = 0
        biggest = 0
        for gid in my_atari_ids:
            if gid not in saved_atari:
                sz = groups_me[gid]["size"]
                unsaved_size += sz
                unsaved_count += 1
                if sz > biggest:
                    biggest = sz

        if unsaved_size:
            if biggest == 1 and unsaved_size == 1:
                score -= 1400
            else:
                score -= min(30000, 3600 + 1500 * unsaved_size + 1300 * unsaved_count)

    # Avoid likely ko recaptures.
    if _simple_ko_shape(info):
        score -= 100000

    # Liberties / self-atari safety.
    if lib_n == 1:
        if cap_n == 0:
            score -= 15500 + 900 * new_size
        else:
            score -= max(2500, 6500 + 800 * new_size - 700 * cap_n)
    elif lib_n == 2:
        score -= 250 if tactical else 850
        if new_size == 1 and cap_n == 0 and total < 180:
            score -= 350
    else:
        score += min(lib_n, 12) * 65
        if lib_n >= 6:
            score += 100

    # Do not fill our own real eyes unless capturing or tactically urgent.
    if cap_n == 0:
        if _is_true_eye(board, r, c, ME):
            score -= 5000 if tactical else 20000
        elif _is_eye_like(board, r, c, ME):
            score -= 1500 if tactical else 6000

        if _is_true_eye(board, r, c, OPP) and not tactical:
            score -= 8000
        elif _is_eye_like(board, r, c, OPP) and not tactical:
            score -= 3000

    # Local shape: connections, cuts, contact fights.
    adj_my = 0
    adj_opp = 0
    empty_adj = 0
    adj_my_groups = set()
    adj_opp_groups = set()

    for dx, dy in DIRS:
        nr, nc = r + dx, c + dy
        if not _inside(nr, nc):
            continue
        v = board[nr][nc]
        if v == EMPTY:
            empty_adj += 1
        elif v == ME:
            adj_my += 1
            gid = idx_me.get((nr, nc))
            if gid is not None:
                adj_my_groups.add(gid)
        elif v == OPP:
            adj_opp += 1
            gid = idx_opp.get((nr, nc))
            if gid is not None:
                adj_opp_groups.add(gid)

    diag_my = 0
    diag_opp = 0
    for dx, dy in DIAGS:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc):
            v = board[nr][nc]
            if v == ME:
                diag_my += 1
            elif v == OPP:
                diag_opp += 1

    score += empty_adj * 28
    score += adj_my * 60 + diag_my * 22
    score += adj_opp * 34 + diag_opp * 12

    if adj_my and adj_opp:
        score += 110 + 35 * min(adj_my, adj_opp)

    if len(adj_my_groups) >= 2:
        score += 500 * (len(adj_my_groups) - 1)
        for gid in adj_my_groups:
            libs = len(groups_me[gid]["libs"])
            if libs <= 3:
                score += 260
    elif len(adj_my_groups) == 1 and adj_my >= 2 and not tactical:
        score -= 90

    if len(adj_opp_groups) >= 2:
        cut_bonus = 380 * (len(adj_opp_groups) - 1)
        if adj_my + diag_my + empty_adj >= 2:
            cut_bonus += 120
        elif not tactical:
            cut_bonus -= 250
        score += cut_bonus

    if adj_my >= 3 and not tactical:
        score -= 220 * (adj_my - 2)

    if adj_opp > 0 and adj_my == 0 and diag_my == 0 and lib_n <= 2 and cap_n == 0:
        score -= 650
    elif adj_opp >= 2 and adj_my == 0 and diag_my == 0 and not tactical:
        score -= 250

    # Influence: prefer contested points, reductions, and supported invasions.
    mh = heat_me[r][c]
    oh = heat_opp[r][c]

    score += min(160, 5 * min(mh, oh))

    if total > 35 and mh + oh < 4:
        score -= 140

    if oh > mh:
        score += min(130, 3 * (oh - mh))
    else:
        score += min(90, 2 * (mh - oh))

    if oh > mh + 18 and adj_my == 0 and diag_my == 0 and lib_n <= 3 and not tactical:
        score -= 300

    if mh > oh + 25 and adj_opp == 0 and adj_my >= 2 and not tactical:
        score -= 100

    # Good extensions and approaches.
    for dx, dy in _STRAIGHT_TWO:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc):
            v = board[nr][nc]
            midr = r + dx // 2
            midc = c + dy // 2
            clear = board[midr][midc] == EMPTY
            if v == ME:
                score += 42 if clear else 15
            elif v == OPP:
                score += 32 if clear else 10

    for dx, dy in _KNIGHTS:
        nr, nc = r + dx, c + dy
        if _inside(nr, nc):
            v = board[nr][nc]
            if v == ME:
                score += 24
            elif v == OPP:
                score += 18

    score += _noise(r, c, total)
    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = _build_board(me, opponent)

    total = 0
    for row in board:
        for v in row:
            if v != EMPTY:
                total += 1

    groups_me, idx_me = _collect_groups(board, ME)
    groups_opp, idx_opp = _collect_groups(board, OPP)

    lib_me = _make_lib_map(groups_me)
    lib_opp = _make_lib_map(groups_opp)

    heat_me, heat_opp = _compute_heat(board)

    my_atari_ids = [gid for gid, g in enumerate(groups_me) if len(g["libs"]) == 1]

    best_move = None
    best_score = -10**18

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue

            info = _simulate(board, r, c)
            if info is None:
                continue

            score = _score_move(
                board,
                r,
                c,
                info,
                groups_me,
                groups_opp,
                idx_me,
                idx_opp,
                lib_me,
                lib_opp,
                heat_me,
                heat_opp,
                total,
                my_atari_ids,
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # If every non-pass move appears to be a ko recapture or very late self-harm,
    # pass is the safest legal move.
    if best_score < -50000:
        return (0, 0)
    if total > 300 and best_score < -12000:
        return (0, 0)

    # Final sanity check.
    if _simulate(board, best_move[0], best_move[1]) is None:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)
