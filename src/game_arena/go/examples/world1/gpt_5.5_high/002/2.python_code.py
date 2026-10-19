
from __future__ import annotations

N = 19

NEIGHBORS = [[[] for _ in range(N)] for _ in range(N)]
for _r in range(N):
    for _c in range(N):
        _ns = []
        if _r > 0:
            _ns.append((_r - 1, _c))
        if _r + 1 < N:
            _ns.append((_r + 1, _c))
        if _c > 0:
            _ns.append((_r, _c - 1))
        if _c + 1 < N:
            _ns.append((_r, _c + 1))
        NEIGHBORS[_r][_c] = _ns

_DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

_RADIUS4 = []
for _dr in range(-4, 5):
    for _dc in range(-4, 5):
        _d = abs(_dr) + abs(_dc)
        if 1 <= _d <= 4:
            _RADIUS4.append((_dr, _dc, _d))

_STAR_POINTS = {
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
}

_EDGE_VALUE = {
    1: -24,
    2: -7,
    3: 7,
    4: 13,
    5: 10,
    6: 6,
    7: 3,
    8: 1,
    9: 0,
    10: 0,
}

# Keyed by sorted distances from nearest two board edges.
_SHAPE_BONUS = {
    (3, 3): 3,
    (3, 4): 14,
    (3, 5): 8,
    (3, 6): 3,
    (4, 4): 18,
    (4, 5): 9,
    (4, 6): 4,
    (4, 10): 8,
    (5, 5): 5,
    (10, 10): 2,
}

_EMPTY_CORNER_BONUS = {
    (4, 4): 44,
    (3, 4): 38,
    (4, 3): 38,
    (3, 5): 24,
    (5, 3): 24,
    (4, 5): 24,
    (5, 4): 24,
    (5, 5): 15,
    (3, 3): 6,
}

_APPROACH_BONUS = {
    (4, 6): 36,
    (6, 4): 36,
    (3, 6): 28,
    (6, 3): 28,
    (5, 6): 22,
    (6, 5): 22,
    (4, 7): 16,
    (7, 4): 16,
}

_EXTENSION_BONUS = {
    (4, 6): 15,
    (6, 4): 15,
    (3, 6): 10,
    (6, 3): 10,
    (4, 7): 10,
    (7, 4): 10,
}


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        return _policy_impl(me, opponent)
    except Exception:
        # Pass is always legal in Go and prevents accidental disqualification.
        return (0, 0)


def _policy_impl(me, opponent):
    board = [[0] * N for _ in range(N)]
    me_stones = []
    opp_stones = []

    for row, col in me:
        r, c = row - 1, col - 1
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            board[r][c] = 1
            me_stones.append((r, c))

    for row, col in opponent:
        r, c = row - 1, col - 1
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            board[r][c] = -1
            opp_stones.append((r, c))

    gid, groups = _analyze(board)
    stage = len(me_stones) + len(opp_stones)
    corner_infos = _corner_infos(board)

    best_score = -10**18
    best_move = None
    best_koish = False

    best_safe_score = -10**18
    best_safe_move = None

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            if not _legal(board, gid, groups, r, c):
                continue

            score, koish = _score_move(
                r, c, board, gid, groups,
                me_stones, opp_stones, stage, corner_infos
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)
                best_koish = koish

            if not koish and score > best_safe_score:
                best_safe_score = score
                best_safe_move = (r, c)

    if best_move is None:
        return (0, 0)

    # Avoid ko-shaped single-stone captures when possible, because the API
    # provides no history for checking an immediate ko ban.
    if best_koish:
        if best_safe_move is None:
            return (0, 0)
        chosen = best_safe_move
        chosen_score = best_safe_score
    else:
        chosen = best_move
        chosen_score = best_score

    # Very late, if the only moves are severe eye-fills/self-damaging moves,
    # pass instead.
    if stage > 250 and chosen_score < -550:
        return (0, 0)

    r, c = chosen
    if _legal(board, gid, groups, r, c):
        return (r + 1, c + 1)

    if best_safe_move is not None:
        r, c = best_safe_move
        if _legal(board, gid, groups, r, c):
            return (r + 1, c + 1)

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 and _legal(board, gid, groups, r, c):
                return (r + 1, c + 1)

    return (0, 0)


def _analyze(board):
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == 0 or gid[r][c] != -1:
                continue

            idx = len(groups)
            stack = [(r, c)]
            gid[r][c] = idx
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))

                for nr, nc in NEIGHBORS[sr][sc]:
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append((color, stones, libs))

    return gid, groups


def _legal(board, gid, groups, r, c):
    if not (0 <= r < N and 0 <= c < N):
        return False
    if board[r][c] != 0:
        return False

    # Any adjacent empty point gives the placed stone a liberty.
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 0:
            return True

    # Capturing adjacent opponent groups is legal.
    seen = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == -1:
            g = gid[nr][nc]
            if g not in seen:
                seen.add(g)
                if len(groups[g][2]) == 1:
                    return True

    # Connecting to a friendly group that has another liberty is legal.
    seen.clear()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 1:
            g = gid[nr][nc]
            if g not in seen:
                seen.add(g)
                if len(groups[g][2]) > 1:
                    return True

    return False


def _score_move(r, c, board, gid, groups, me_stones, opp_stones, stage, corner_infos):
    s = 0.0
    s += _positional_score(r, c)
    s += _corner_bonus(r, c, stage, corner_infos)

    adj_own = set()
    adj_opp = set()
    empty_adj = 0

    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 0:
            empty_adj += 1
        elif v == 1:
            adj_own.add(gid[nr][nc])
        elif v == -1:
            adj_opp.add(gid[nr][nc])

    captured = set()
    cap_size = 0

    # Captures and attacks.
    for og in adj_opp:
        libs = groups[og][2]
        osize = len(groups[og][1])
        llen = len(libs)

        if llen == 1:
            captured.add(og)
            cap_size += osize
            s += 1050 + 230 * osize
        elif llen == 2:
            s += 310 + 70 * min(osize, 12)   # Put in atari.
        elif llen == 3:
            s += 60 + 16 * min(osize, 12)    # Reduce liberties.

    own_atari_save = 0

    # Directly saving or strengthening friendly groups.
    for mg in adj_own:
        libs = groups[mg][2]
        msize = len(groups[mg][1])
        llen = len(libs)

        if llen == 1:
            s += 980 + 220 * msize
            own_atari_save += msize
        elif llen == 2:
            s += 120 + 30 * min(msize, 10)
        elif llen == 3:
            s += 25 + 8 * min(msize, 10)

    # Capturing stones can also save adjacent friendly groups.
    saved_by_capture = set()
    for og in captured:
        for sr, sc in groups[og][1]:
            for nr, nc in NEIGHBORS[sr][sc]:
                if board[nr][nc] == 1:
                    mg = gid[nr][nc]
                    if mg in saved_by_capture:
                        continue
                    saved_by_capture.add(mg)
                    libs = groups[mg][2]
                    msize = len(groups[mg][1])
                    if len(libs) == 1:
                        s += 930 + 210 * msize
                        own_atari_save += msize
                    elif len(libs) == 2:
                        s += 120 + 24 * min(msize, 10)

    # Approximate liberties of the resulting friendly group.
    new_libs = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 0:
            new_libs.add((nr, nc))

    new_size = 1
    for mg in adj_own:
        new_size += len(groups[mg][1])
        new_libs.update(groups[mg][2])

    new_libs.discard((r, c))

    for og in captured:
        # For single-stone captures this is exact; for larger captures it is a
        # good optimistic liberty estimate.
        new_libs.update(groups[og][1])

    libn = len(new_libs)

    # Shape, connection, and cutting.
    s += 14 * len(adj_own) + 10 * len(adj_opp) + 3 * empty_adj

    if len(adj_own) >= 2:
        total = sum(len(groups[g][1]) for g in adj_own)
        s += 90 + 32 * (len(adj_own) - 1) + 8 * min(total, 20)
        for g in adj_own:
            if len(groups[g][2]) <= 2:
                s += 45

    if len(adj_opp) >= 2:
        s += 70 + 22 * (len(adj_opp) - 1)
        for g in adj_opp:
            if len(groups[g][2]) <= 3:
                s += 34

    if stage < 45 and cap_size == 0 and own_atari_save == 0:
        # Avoid unnecessary early contact and over-concentration.
        s -= 8 * (len(adj_own) + len(adj_opp))

    # Liberty safety.
    s += 10 * min(libn, 6)

    if libn <= 1:
        penalty = 760 + 60 * min(new_size, 15)
        if cap_size >= 2:
            penalty *= 0.35
        elif cap_size == 1:
            penalty *= 0.65
        if own_atari_save >= 2:
            penalty *= 0.45
        s -= penalty
    elif libn == 2:
        penalty = 95 + 18 * min(new_size, 12)
        if cap_size:
            penalty *= 0.55
        if own_atari_save:
            penalty *= 0.60
        s -= penalty
    elif libn >= 4:
        s += 18

    koish = (cap_size == 1 and libn == 1)
    if koish:
        s -= 800

    # Eye-filling is usually bad unless tactical.
    if _is_eye_like(board, r, c, 1) and cap_size == 0 and own_atari_save == 0:
        s -= 900
        if len(adj_own) >= 2:
            s += 250

    if _is_eye_like(board, r, c, -1) and cap_size == 0:
        s -= 250

    # Local influence: play near relevant stones, but do not over-concentrate.
    own_inf = 0
    opp_inf = 0
    for dr, dc, dist in _RADIUS4:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            w = 5 - dist
            if board[nr][nc] == 1:
                own_inf += w
            elif board[nr][nc] == -1:
                opp_inf += w

    if stage < 45:
        s += 0.65 * own_inf + 0.85 * opp_inf
        if own_inf > 18 and opp_inf < 5 and cap_size == 0:
            s -= 1.8 * (own_inf - 18)
    else:
        s += 1.00 * own_inf + 1.25 * opp_inf
        if own_inf + opp_inf == 0:
            s -= 15

    if opp_inf > own_inf + 15 and libn <= 2 and cap_size == 0:
        s -= 35

    if own_inf > opp_inf + 24 and stage > 80 and cap_size == 0 and own_atari_save == 0:
        s -= 25

    # Development distance.
    d_own = _nearest_dist(r, c, me_stones)
    d_opp = _nearest_dist(r, c, opp_stones)

    if stage < 60:
        if me_stones:
            if d_own == 1:
                s -= 28
            elif d_own == 2:
                s -= 10
            elif 3 <= d_own <= 6:
                s += 10
            elif d_own >= 12:
                s -= 3

        if opp_stones:
            if d_opp == 1:
                s -= 14
            elif 2 <= d_opp <= 5:
                s += 7
            elif d_opp >= 12:
                s += 1
    else:
        d_any = min(d_own, d_opp)
        if d_any >= 10:
            s -= 22
        elif d_any >= 7:
            s -= 8

        if d_own == 1:
            s += 8
        elif d_own == 2:
            s += 5

        if d_opp == 1:
            s += 10
        elif 2 <= d_opp <= 3:
            s += 6

    # Extra aversion to non-tactical first-line plays.
    line = min(r + 1, c + 1, N - r, N - c)
    if line == 1 and cap_size == 0 and own_atari_save == 0:
        s -= 35
    elif line == 2 and cap_size == 0 and own_atari_save == 0:
        s -= 8

    # Deterministic tiny tie-breaker.
    s += ((((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ (stage * 83492791)) & 1023) / 10000.0

    return s, koish


def _positional_score(r, c):
    line = min(r + 1, c + 1, N - r, N - c)
    s = _EDGE_VALUE.get(line, 0)

    a = min(r + 1, N - r)
    b = min(c + 1, N - c)
    key = tuple(sorted((a, b)))
    s += _SHAPE_BONUS.get(key, 0)

    p = (r + 1, c + 1)
    if p in _STAR_POINTS:
        if p[0] in (4, 16) and p[1] in (4, 16):
            s += 10
        elif p == (10, 10):
            s += 2
        else:
            s += 6

    return s


def _corner_infos(board):
    infos = []
    for top, left in ((True, True), (True, False), (False, True), (False, False)):
        own = 0
        opp = 0
        rr = range(0, 7) if top else range(N - 7, N)
        cc = range(0, 7) if left else range(N - 7, N)

        for r in rr:
            for c in cc:
                if board[r][c] == 1:
                    own += 1
                elif board[r][c] == -1:
                    opp += 1

        infos.append((top, left, own, opp, own + opp))

    return infos


def _corner_bonus(r, c, stage, infos):
    if stage < 60:
        factor = 1.0
    elif stage < 120:
        factor = 0.50
    else:
        factor = 0.15

    s = 0.0
    for top, left, own, opp, total in infos:
        rr = r + 1 if top else N - r
        cc = c + 1 if left else N - c

        if rr > 7 or cc > 7:
            continue

        if total == 0:
            s += factor * _EMPTY_CORNER_BONUS.get((rr, cc), 0)
        elif own == 0 and opp > 0:
            s += factor * _APPROACH_BONUS.get((rr, cc), 0)
            if stage > 45 and (rr, cc) == (3, 3):
                s += 24
        elif own > 0 and opp == 0:
            s += factor * _EXTENSION_BONUS.get((rr, cc), 0)
        else:
            if stage > 70 and (rr, cc) == (3, 3):
                s += 10

    return s


def _is_eye_like(board, r, c, color):
    if board[r][c] != 0:
        return False

    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] != color:
            return False

    bad_diags = 0
    for dr, dc in _DIAGS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            if board[nr][nc] == -color:
                bad_diags += 1

    if r == 0 or r == N - 1 or c == 0 or c == N - 1:
        return bad_diags == 0

    return bad_diags <= 1


def _nearest_dist(r, c, stones):
    if not stones:
        return 99

    best = 99
    for sr, sc in stones:
        d = abs(r - sr) + abs(c - sc)
        if d < best:
            best = d
            if best == 1:
                break

    return best
