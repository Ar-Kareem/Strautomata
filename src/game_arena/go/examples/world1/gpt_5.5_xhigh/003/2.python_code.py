
from __future__ import annotations

N = 19
ME = 1
OPP = -1

# Precomputed board geometry.
NEIGHBORS = [[() for _ in range(N)] for _ in range(N)]
DIAGONALS = [[() for _ in range(N)] for _ in range(N)]
BIT = [[0 for _ in range(N)] for _ in range(N)]

for _i in range(N):
    for _j in range(N):
        ns = []
        if _i > 0:
            ns.append((_i - 1, _j))
        if _i + 1 < N:
            ns.append((_i + 1, _j))
        if _j > 0:
            ns.append((_i, _j - 1))
        if _j + 1 < N:
            ns.append((_i, _j + 1))
        NEIGHBORS[_i][_j] = tuple(ns)

        ds = []
        for _di in (-1, 1):
            for _dj in (-1, 1):
                ni, nj = _i + _di, _j + _dj
                if 0 <= ni < N and 0 <= nj < N:
                    ds.append((ni, nj))
        DIAGONALS[_i][_j] = tuple(ds)

        BIT[_i][_j] = 1 << (_i * N + _j)

# Small state memory to avoid immediate simple-ko recapture and some superko repeats.
_last_after_key = None
_seen_keys = set()
_last_total = None

_INF_WEIGHTS = (0.0, 7.0, 4.5, 3.0, 2.0, 1.2, 0.7, 0.4)


def _analyze(board):
    """Return group list and group-id grid."""
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for i in range(N):
        for j in range(N):
            color = board[i][j]
            if color == 0 or gid[i][j] != -1:
                continue

            g_id = len(groups)
            stack = [(i, j)]
            gid[i][j] = g_id
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in NEIGHBORS[x][y]:
                    v = board[nx][ny]
                    if v == 0:
                        libs.add((nx, ny))
                    elif v == color and gid[nx][ny] == -1:
                        gid[nx][ny] = g_id
                        stack.append((nx, ny))

            groups.append(
                {
                    "color": color,
                    "stones": stones,
                    "libs": libs,
                    "size": len(stones),
                }
            )

    return groups, gid


def _line(coord: int, low_side: bool) -> int:
    """1-based distance from a chosen edge."""
    return coord + 1 if low_side else N - coord


def _make_corner_stats(me0, opp0):
    stats = []
    for top in (True, False):
        for left in (True, False):
            own = []
            opp = []
            for x, y in me0:
                if _line(x, top) <= 6 and _line(y, left) <= 6:
                    own.append((x, y))
            for x, y in opp0:
                if _line(x, top) <= 6 and _line(y, left) <= 6:
                    opp.append((x, y))
            stats.append((top, left, own, opp))
    return stats


def _point_value(i: int, j: int, total: int) -> float:
    r, c = i + 1, j + 1
    line = min(r, c, N + 1 - r, N + 1 - c)
    open_phase = max(0.0, min(1.0, (120.0 - total) / 120.0))

    v = 0.0
    if line == 1:
        v -= 10.0 * open_phase + 3.0
    elif line == 2:
        v -= 4.0 * open_phase + 0.5
    elif line == 3:
        v += 4.0 * open_phase + 1.0
    elif line == 4:
        v += 7.0 * open_phase + 1.2
    elif line == 5:
        v += 3.0 * open_phase + 0.5

    # Star points and broad opening development.
    if r in (4, 10, 16) and c in (4, 10, 16):
        v += 7.0 * open_phase
    if (r == 10 and c in (4, 16)) or (c == 10 and r in (4, 16)):
        v += 4.0 * open_phase

    dist_center = abs(r - 10) + abs(c - 10)
    v += max(0.0, 4.0 - 0.35 * dist_center) * (0.5 * open_phase)
    return v


def _corner_bonus(i: int, j: int, total: int, corner_stats) -> float:
    if total >= 100:
        return 0.0

    phase = (100.0 - total) / 100.0
    b = 0.0

    for top, left, own, opp in corner_stats:
        lr = _line(i, top)
        lc = _line(j, left)
        if lr > 6 or lc > 6:
            continue

        occ = len(own) + len(opp)

        base = 0.0
        if (lr, lc) == (4, 4):
            base = 55.0
        elif (lr, lc) in ((3, 4), (4, 3)):
            base = 48.0
        elif (lr, lc) == (3, 3):
            base = 38.0
        elif (lr, lc) in ((4, 5), (5, 4), (3, 5), (5, 3)):
            base = 25.0
        elif 3 <= lr <= 5 and 3 <= lc <= 5:
            base = 16.0

        if occ == 0:
            b += base * phase
        elif len(own) == 0 and len(opp) > 0:
            mind = min(abs(i - x) + abs(j - y) for x, y in opp)
            if mind == 1:
                b -= 16.0 * phase
            elif 2 <= mind <= 6 and lr >= 3 and lc >= 3:
                b += max(0.0, 18.0 - 2.0 * abs(mind - 3.5)) * phase
        elif len(own) > 0 and len(opp) == 0:
            mind = min(abs(i - x) + abs(j - y) for x, y in own)
            if mind == 1:
                b -= 12.0 * phase
            elif 2 <= mind <= 6 and len(own) <= 2 and lr >= 3 and lc >= 3:
                b += max(0.0, 8.0 - abs(mind - 4.0)) * phase
            elif len(own) > 2 and mind <= 2:
                b -= 8.0 * phase
        else:
            mind_opp = min(abs(i - x) + abs(j - y) for x, y in opp)
            if 1 <= mind_opp <= 3 and lr >= 2 and lc >= 2:
                b += 4.0 * phase

    return b


def _influence(i: int, j: int, me0, opp0):
    own = 0.0
    opp = 0.0

    for x, y in me0:
        d = abs(i - x) + abs(j - y)
        if 0 < d <= 7:
            own += _INF_WEIGHTS[d]

    for x, y in opp0:
        d = abs(i - x) + abs(j - y)
        if 0 < d <= 7:
            opp += _INF_WEIGHTS[d]

    return own, opp


def _orth_eye(board, i: int, j: int, color: int) -> bool:
    # Off-board edges count as friendly boundaries.
    for nx, ny in NEIGHBORS[i][j]:
        if board[nx][ny] != color:
            return False
    return True


def _noise(i: int, j: int, total: int, my_count: int, opp_count: int) -> float:
    h = (
        ((i + 1) * 73856093)
        ^ ((j + 1) * 19349663)
        ^ ((total + 1) * 83492791)
        ^ ((my_count + 3) * 2654435761)
        ^ ((opp_count + 7) * 97531)
    ) & 0xFFFF
    return (h / 65536.0) * 0.05


def _move_info(board, gid, groups, i: int, j: int):
    if board[i][j] != 0:
        return None

    adj_own = set()
    adj_opp = set()

    for nx, ny in NEIGHBORS[i][j]:
        v = board[nx][ny]
        if v == ME:
            adj_own.add(gid[nx][ny])
        elif v == OPP:
            adj_opp.add(gid[nx][ny])

    captures = []
    cap_bits = 0
    capture_count = 0

    for og in adj_opp:
        if len(groups[og]["libs"]) == 1:
            captures.append(og)
            capture_count += groups[og]["size"]
            for sx, sy in groups[og]["stones"]:
                cap_bits |= BIT[sx][sy]

    cap_set = set(captures)
    new_libs = set()

    # Liberties adjacent to the placed stone.
    for nx, ny in NEIGHBORS[i][j]:
        v = board[nx][ny]
        if v == 0:
            new_libs.add((nx, ny))
        elif v == OPP and gid[nx][ny] in cap_set:
            new_libs.add((nx, ny))

    # Liberties inherited by connected friendly groups.
    for g in adj_own:
        for lib in groups[g]["libs"]:
            if lib != (i, j):
                new_libs.add(lib)

    # Friendly atari groups saved by this move, directly or by capture.
    rescued = set()
    for g in adj_own:
        if len(groups[g]["libs"]) == 1:
            rescued.add(g)

    if cap_set:
        for cg in cap_set:
            for sx, sy in groups[cg]["stones"]:
                touches_new_group = False
                for nx, ny in NEIGHBORS[sx][sy]:
                    if nx == i and ny == j:
                        touches_new_group = True
                    elif board[nx][ny] == ME:
                        mg = gid[nx][ny]
                        if mg in adj_own:
                            touches_new_group = True
                        if len(groups[mg]["libs"]) == 1:
                            rescued.add(mg)
                if touches_new_group:
                    new_libs.add((sx, sy))

    new_libs.discard((i, j))

    # Suicide check.
    if capture_count == 0 and not new_libs:
        return None

    new_size = 1 + sum(groups[g]["size"] for g in adj_own)
    ko_risk = (
        capture_count == 1
        and len(captures) == 1
        and groups[captures[0]]["size"] == 1
        and len(new_libs) == 1
        and new_size == 1
    )

    return {
        "adj_own": adj_own,
        "adj_opp": adj_opp,
        "captures": captures,
        "capture_count": capture_count,
        "cap_bits": cap_bits,
        "new_libs": new_libs,
        "new_size": new_size,
        "rescued": rescued,
        "ko_risk": ko_risk,
    }


def _evaluate(
    board,
    groups,
    gid,
    i: int,
    j: int,
    info,
    total: int,
    me0,
    opp0,
    corner_stats,
    own_atari_size: int,
    opp_atari_size: int,
) -> float:
    score = 0.0

    captures = info["captures"]
    capture_set = set(captures)
    cap_count = info["capture_count"]
    new_l = len(info["new_libs"])
    adj_own = info["adj_own"]
    adj_opp = info["adj_opp"]
    rescued = info["rescued"]

    rescued_size = sum(groups[g]["size"] for g in rescued)

    # Global urgency: do not ignore groups currently in atari.
    if own_atari_size:
        unsaved = own_atari_size - rescued_size
        if unsaved > 0:
            score -= 85.0 * unsaved

    if opp_atari_size:
        missed = opp_atari_size - cap_count
        if missed > 0:
            score -= 45.0 * missed

    # Captures.
    if cap_count:
        max_cap = max(groups[g]["size"] for g in captures)
        score += 110.0 * cap_count + 35.0 * len(captures) + 12.0 * max_cap

    # Save own groups in atari.
    for g in rescued:
        size = groups[g]["size"]
        score += 100.0 * size + 20.0
        if g in adj_own:
            if new_l <= 1:
                score -= 75.0 * size
            elif new_l >= 3:
                score += 15.0 * size

    # Defend nearby weak groups.
    for g in adj_own:
        libs = len(groups[g]["libs"])
        size = groups[g]["size"]
        if libs == 1:
            continue
        if libs == 2:
            score += 18.0 * min(size, 12)
            if new_l >= 3:
                score += 8.0
            elif new_l <= 1:
                score -= 15.0
        elif libs == 3:
            score += 5.0 * min(size, 10)

    # Attack adjacent opponent groups.
    for g in adj_opp:
        if g in capture_set:
            continue
        old_l = len(groups[g]["libs"])
        after_l = old_l - 1 if (i, j) in groups[g]["libs"] else old_l
        size = groups[g]["size"]

        if after_l == 1:
            score += 55.0 * size + 18.0
            if size >= 3:
                score += 10.0
        elif after_l == 2:
            score += 13.0 * min(size, 12)
        elif after_l == 3:
            score += 3.0 * min(size, 12)

    # Connections and cuts.
    if len(adj_own) >= 2:
        conn_size = sum(groups[g]["size"] for g in adj_own)
        score += 22.0 * (len(adj_own) - 1) + 3.0 * min(conn_size, 30)
        if min(len(groups[g]["libs"]) for g in adj_own) <= 3:
            score += 20.0

    if len(adj_opp) >= 2:
        score += 13.0 * (len(adj_opp) - 1)
        if adj_own or cap_count or new_l >= 3:
            score += 8.0
        else:
            score -= 10.0

    # Safety / self-atari.
    if new_l <= 1:
        score -= 95.0
        if cap_count >= 2 or rescued_size >= 2:
            score += 35.0
    elif new_l == 2:
        score -= 18.0
    elif new_l == 3:
        score += 4.0
    else:
        score += 3.0 * min(new_l, 8)

    if info["new_size"] > 1 and new_l >= 3:
        score += 1.2 * min(info["new_size"], 15)

    if info["ko_risk"]:
        score -= 65.0

    # Avoid filling own eyes unless it captures/saves tactically.
    if cap_count == 0:
        if _orth_eye(board, i, j, ME):
            score -= 260.0
        if _orth_eye(board, i, j, OPP):
            score -= 80.0

    # Local shape.
    adj_my_count = 0
    adj_opp_count = 0
    empty_adj = 0

    for nx, ny in NEIGHBORS[i][j]:
        v = board[nx][ny]
        if v == ME:
            adj_my_count += 1
        elif v == OPP:
            adj_opp_count += 1
        else:
            empty_adj += 1

    diag_my = 0
    diag_opp = 0
    for nx, ny in DIAGONALS[i][j]:
        v = board[nx][ny]
        if v == ME:
            diag_my += 1
        elif v == OPP:
            diag_opp += 1

    score += 1.2 * empty_adj
    score += 2.5 * adj_my_count
    score += 1.0 * diag_my

    if adj_opp_count:
        if adj_my_count or cap_count or rescued_size or new_l >= 3:
            score += 2.0 * adj_opp_count
        else:
            score -= 5.5 * adj_opp_count

    if adj_my_count and adj_opp_count:
        score += 9.0

    if adj_my_count == 0 and diag_my > 0 and new_l >= 3:
        score += 1.5 * diag_my

    if diag_opp > diag_my and adj_my_count == 0 and cap_count == 0:
        score -= 0.8 * (diag_opp - diag_my)

    if adj_my_count >= 3 and adj_opp_count == 0 and cap_count == 0:
        score -= 14.0

    if empty_adj == 0 and cap_count == 0 and new_l <= 2:
        score -= 25.0

    # Opening, influence, and whole-board development.
    score += _point_value(i, j, total)
    score += _corner_bonus(i, j, total, corner_stats)

    own_inf, opp_inf = _influence(i, j, me0, opp0)
    open_phase = max(0.0, min(1.0, (140.0 - total) / 140.0))
    late_phase = min(1.0, total / 240.0)

    score += (0.50 + 0.35 * open_phase) * own_inf
    score += (0.65 + 0.55 * late_phase) * opp_inf
    score += 1.15 * min(own_inf, opp_inf)

    # Avoid unsupported deep invasions into strong opposing influence.
    if opp_inf > own_inf + 7.0 and adj_my_count == 0 and cap_count == 0 and rescued_size == 0:
        if new_l < 4 or total < 100:
            score -= min(35.0, (opp_inf - own_inf) * 2.0)

    # Avoid unnecessary self-filling in very friendly areas.
    if own_inf > opp_inf + 10.0 and opp_inf < 1.0 and total > 70 and cap_count == 0:
        score -= min(18.0, (own_inf - opp_inf) * 0.9)

    score += _noise(i, j, total, len(me0), len(opp0))
    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global _last_after_key, _last_total, _seen_keys

    board = [[0] * N for _ in range(N)]
    me0 = []
    opp0 = []
    my_bits = 0
    opp_bits = 0

    # Build board defensively.
    for p in me:
        try:
            r, c = p
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N:
            i, j = r - 1, c - 1
            if board[i][j] == 0:
                board[i][j] = ME
                me0.append((i, j))
                my_bits |= BIT[i][j]

    for p in opponent:
        try:
            r, c = p
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N:
            i, j = r - 1, c - 1
            if board[i][j] == 0:
                board[i][j] = OPP
                opp0.append((i, j))
                opp_bits |= BIT[i][j]

    total = len(me0) + len(opp0)

    # Reset memory at likely game starts or after implausibly large discontinuities.
    if total <= 2:
        _seen_keys.clear()
        _last_after_key = None
    elif _last_total is not None and total + 20 < _last_total:
        _seen_keys.clear()
        _last_after_key = None

    current_key = (my_bits, opp_bits)
    _seen_keys.add(current_key)

    groups, gid = _analyze(board)

    own_atari_size = 0
    opp_atari_size = 0
    for g in groups:
        if len(g["libs"]) == 1:
            if g["color"] == ME:
                own_atari_size += g["size"]
            else:
                opp_atari_size += g["size"]

    corner_stats = _make_corner_stats(me0, opp0)

    best_move = None
    best_score = -10**100
    best_key = current_key
    legal_exists = False

    for i in range(N):
        for j in range(N):
            info = _move_info(board, gid, groups, i, j)
            if info is None:
                continue

            legal_exists = True
            result_key = (my_bits | BIT[i][j], opp_bits & ~info["cap_bits"])

            # Conservative ko/superko avoidance. If all moves are forbidden this way,
            # passing is still legal.
            if result_key == _last_after_key or result_key in _seen_keys:
                continue

            score = _evaluate(
                board,
                groups,
                gid,
                i,
                j,
                info,
                total,
                me0,
                opp0,
                corner_stats,
                own_atari_size,
                opp_atari_size,
            )

            if score > best_score:
                best_score = score
                best_move = (i, j)
                best_key = result_key

    if not legal_exists or best_move is None:
        chosen = (0, 0)
        final_key = current_key
    else:
        # Passing threshold: early we strongly prefer playing; late we pass instead
        # of filling our own eyes or making clearly harmful moves.
        if own_atari_size or opp_atari_size:
            threshold = -10**99
        elif total < 80:
            threshold = -200.0
        elif total < 160:
            threshold = -80.0
        elif total < 240:
            threshold = -25.0
        elif total < 320:
            threshold = -8.0
        else:
            threshold = 0.0

        if best_score < threshold:
            chosen = (0, 0)
            final_key = current_key
        else:
            chosen = (best_move[0] + 1, best_move[1] + 1)
            final_key = best_key

    # Last-resort validation.
    if chosen != (0, 0):
        rr, cc = chosen
        if not (1 <= rr <= N and 1 <= cc <= N and board[rr - 1][cc - 1] == 0):
            chosen = (0, 0)
            final_key = current_key

    _last_after_key = final_key
    _seen_keys.add(final_key)
    if len(_seen_keys) > 5000:
        _seen_keys.clear()
        _seen_keys.add(final_key)

    _last_total = total
    return chosen
