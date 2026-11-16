
from __future__ import annotations

N = 19
EMPTY = 0
MY = 1
OPP = -1
BORDER = 2

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

_MASK = (1 << 64) - 1


def _splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & _MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
    return (z ^ (z >> 31)) & _MASK


def _idx(r: int, c: int) -> int:
    return (r - 1) * N + (c - 1)


_Z_MY = [_splitmix64(0x123456789ABCDEF0 + i * 2) for i in range(N * N)]
_Z_OPP = [_splitmix64(0x0FEDCBA987654321 + i * 2) for i in range(N * N)]

_RECENT_AFTER: list[int] = []
_RECENT_SET: set[int] = set()
_LAST_TOTAL: int | None = None


def _remember(h: int) -> None:
    _RECENT_AFTER.append(h)
    _RECENT_SET.add(h)
    if len(_RECENT_AFTER) > 10:
        old = _RECENT_AFTER.pop(0)
        if old not in _RECENT_AFTER:
            _RECENT_SET.discard(old)


def _jitter(h: int, r: int, c: int) -> float:
    x = h ^ ((_idx(r, c) + 1) * 0x9E3779B97F4A7C15)
    return ((_splitmix64(x) & 0xFFFF) / 65535.0) * 0.05


def _make_board(me, opponent):
    board = [[BORDER for _ in range(N + 2)] for _ in range(N + 2)]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            board[r][c] = EMPTY

    h = 0
    my_stones = []
    opp_stones = []

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N and board[r][c] == EMPTY:
            board[r][c] = MY
            my_stones.append((r, c))
            h ^= _Z_MY[_idx(r, c)]

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r][c] == EMPTY:
            board[r][c] = OPP
            opp_stones.append((r, c))
            h ^= _Z_OPP[_idx(r, c)]

    return board, h, len(my_stones) + len(opp_stones), my_stones, opp_stones


def _build_groups(board):
    gid = [[-1 for _ in range(N + 2)] for _ in range(N + 2)]
    groups = []

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            color = board[r][c]
            if color not in (MY, OPP) or gid[r][c] != -1:
                continue

            group_id = len(groups)
            stack = [(r, c)]
            gid[r][c] = group_id
            stones = []
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))
                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    v = board[nr][nc]
                    if v == EMPTY:
                        libs.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = group_id
                        stack.append((nr, nc))

            groups.append(
                {
                    "color": color,
                    "stones": stones,
                    "libs": libs,
                    "size": len(stones),
                }
            )

    return groups, gid


def _compute_influence(my_stones, opp_stones):
    weights = (0, 9, 5, 3, 1)
    my_inf = [[0 for _ in range(N + 2)] for _ in range(N + 2)]
    opp_inf = [[0 for _ in range(N + 2)] for _ in range(N + 2)]

    for stones, arr in ((my_stones, my_inf), (opp_stones, opp_inf)):
        for r, c in stones:
            for dr in range(-4, 5):
                nr = r + dr
                if nr < 1 or nr > N:
                    continue
                rem = 4 - abs(dr)
                for dc in range(-rem, rem + 1):
                    dist = abs(dr) + abs(dc)
                    if dist == 0:
                        continue
                    nc = c + dc
                    if 1 <= nc <= N:
                        arr[nr][nc] += weights[dist]

    return my_inf, opp_inf


def _empty_regions(board):
    region_id = [[-1 for _ in range(N + 2)] for _ in range(N + 2)]
    regions = []

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] != EMPTY or region_id[r][c] != -1:
                continue

            rid = len(regions)
            stack = [(r, c)]
            region_id[r][c] = rid
            size = 0
            borders = set()

            while stack:
                sr, sc = stack.pop()
                size += 1
                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    v = board[nr][nc]
                    if v == EMPTY and region_id[nr][nc] == -1:
                        region_id[nr][nc] = rid
                        stack.append((nr, nc))
                    elif v == MY or v == OPP:
                        borders.add(v)

            if borders == {MY}:
                owner = MY
            elif borders == {OPP}:
                owner = OPP
            else:
                owner = EMPTY

            regions.append({"size": size, "owner": owner})

    return region_id, regions


def _corner_summary(board):
    data = []
    for top in (True, False):
        for left in (True, False):
            rows = range(1, 8) if top else range(N - 6, N + 1)
            cols = range(1, 8) if left else range(N - 6, N + 1)
            myc = 0
            oppc = 0
            for r in rows:
                for c in cols:
                    if board[r][c] == MY:
                        myc += 1
                    elif board[r][c] == OPP:
                        oppc += 1
            data.append((top, left, myc, oppc))
    return data


def _group_value(size: int) -> float:
    if size <= 6:
        return float(size)
    return 6.0 + 0.55 * (size - 6)


def _orth_surrounded(board, r: int, c: int, color: int) -> bool:
    for dr, dc in DIRS:
        v = board[r + dr][c + dc]
        if v != color and v != BORDER:
            return False
    return True


def _is_eye(board, r: int, c: int, color: int) -> bool:
    if board[r][c] != EMPTY:
        return False

    for dr, dc in DIRS:
        v = board[r + dr][c + dc]
        if v != color and v != BORDER:
            return False

    bad_diags = 0
    for dr, dc in DIAGS:
        v = board[r + dr][c + dc]
        if v != color and v != BORDER:
            bad_diags += 1

    on_edge = r == 1 or r == N or c == 1 or c == N
    if on_edge:
        return bad_diags == 0
    return bad_diags <= 1


def _line_bonus(r: int, c: int, total: int) -> float:
    edge = min(r, c, N + 1 - r, N + 1 - c)

    if total < 90:
        if edge == 1:
            return -170.0
        if edge == 2:
            return -35.0
        if edge == 3:
            return 24.0
        if edge == 4:
            return 34.0
        if edge == 5:
            return 14.0
        return 2.0
    elif total < 240:
        if edge == 1:
            return -80.0
        if edge == 2:
            return 4.0
        if edge == 3:
            return 18.0
        if edge == 4:
            return 18.0
        if edge == 5:
            return 8.0
        return 1.0
    else:
        if edge == 1:
            return -8.0
        if edge == 2:
            return 10.0
        if edge == 3:
            return 8.0
        if edge == 4:
            return 4.0
        return 0.0


def _standard_point_bonus(r: int, c: int, total: int) -> float:
    if total >= 130:
        return 0.0
    phase = max(0.0, (130.0 - total) / 130.0)
    s = 0.0
    if r in (4, 10, 16) and c in (4, 10, 16):
        s += 24.0 * phase
    if r in (4, 16) and c in (4, 16):
        s += 55.0 * phase
    if r == 10 and c == 10:
        s += 12.0 * phase
    return s


def _corner_bonus(r: int, c: int, total: int, corner_data) -> float:
    phase = max(0.0, (120.0 - total) / 120.0)
    mid = max(0.0, (220.0 - total) / 220.0)
    score = 0.0

    for top, left, myc, oppc in corner_data:
        rr = r if top else N + 1 - r
        cc = c if left else N + 1 - c
        if rr > 7 or cc > 7:
            continue

        point = (rr, cc)
        if myc + oppc == 0:
            if point == (4, 4):
                score += 260.0 * phase + (30.0 if total < 80 else 0.0)
            elif point in ((3, 4), (4, 3)):
                score += 225.0 * phase + (25.0 if total < 80 else 0.0)
            elif point == (3, 3):
                score += 150.0 * phase
            elif point in ((4, 5), (5, 4), (3, 5), (5, 3)):
                score += 105.0 * phase
        elif myc == 0 and oppc > 0:
            if point in ((4, 6), (6, 4), (3, 6), (6, 3), (5, 5), (5, 4), (4, 5)):
                score += 90.0 * phase + 15.0
            elif point == (3, 3):
                score += 80.0 * mid + 20.0
        elif myc > 0 and oppc == 0:
            if point == (3, 3) and total > 25:
                score += 48.0 * mid
            elif 3 <= rr <= 6 and 3 <= cc <= 6:
                score += 28.0 * phase
        else:
            if rr <= 5 and cc <= 5:
                score += 20.0

    return score


def _side_extension_bonus(r: int, c: int, total: int, my_stones, opp_stones) -> float:
    if total > 140:
        return 0.0

    score = 0.0

    if r in (3, 4) and 3 <= c <= 17:
        for sr, sc in my_stones:
            if sr <= 5 and 3 <= abs(c - sc) <= 7:
                score += 30.0
                break
        for sr, sc in opp_stones:
            if sr <= 5 and 2 <= abs(c - sc) <= 6:
                score += 14.0
                break

    if r in (N - 3, N - 2) and 3 <= c <= 17:
        for sr, sc in my_stones:
            if sr >= N - 4 and 3 <= abs(c - sc) <= 7:
                score += 30.0
                break
        for sr, sc in opp_stones:
            if sr >= N - 4 and 2 <= abs(c - sc) <= 6:
                score += 14.0
                break

    if c in (3, 4) and 3 <= r <= 17:
        for sr, sc in my_stones:
            if sc <= 5 and 3 <= abs(r - sr) <= 7:
                score += 30.0
                break
        for sr, sc in opp_stones:
            if sc <= 5 and 2 <= abs(r - sr) <= 6:
                score += 14.0
                break

    if c in (N - 3, N - 2) and 3 <= r <= 17:
        for sr, sc in my_stones:
            if sc >= N - 4 and 3 <= abs(r - sr) <= 7:
                score += 30.0
                break
        for sr, sc in opp_stones:
            if sc >= N - 4 and 2 <= abs(r - sr) <= 6:
                score += 14.0
                break

    return score


def _local_shape_bonus(board, r: int, c: int, tactical: bool) -> float:
    score = 0.0

    for dr, dc in DIAGS:
        v = board[r + dr][c + dc]
        if v == MY:
            score += 8.0
        elif v == OPP:
            score += 6.0

    if not tactical:
        pairs = (
            ((1, 0), (0, 1)),
            ((1, 0), (0, -1)),
            ((-1, 0), (0, 1)),
            ((-1, 0), (0, -1)),
        )
        for a, b in pairs:
            ar, ac = r + a[0], c + a[1]
            br, bc = r + b[0], c + b[1]
            cr, cc = r + a[0] + b[0], c + a[1] + b[1]
            if board[ar][ac] == MY and board[br][bc] == MY and board[cr][cc] == MY:
                score -= 45.0
                break

    return score


def _analyze_move(board, groups, gid, current_hash: int, r: int, c: int):
    if board[r][c] != EMPTY:
        return None

    adj_own = set()
    adj_opp = set()
    adj_empty = 0
    adj_my_count = 0
    adj_opp_count = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        v = board[nr][nc]
        if v == EMPTY:
            adj_empty += 1
        elif v == MY:
            adj_my_count += 1
            adj_own.add(gid[nr][nc])
        elif v == OPP:
            adj_opp_count += 1
            adj_opp.add(gid[nr][nc])

    captured = []
    for g in adj_opp:
        libs = groups[g]["libs"]
        if len(libs) == 1 and (r, c) in libs:
            captured.append(g)

    if not captured and adj_empty == 0:
        possible = False
        for g in adj_own:
            if len(groups[g]["libs"]) > 1:
                possible = True
                break
        if not possible:
            return None

    captured_stones = set()
    for g in captured:
        captured_stones.update(groups[g]["stones"])

    libs = set()

    def add_lib(nr: int, nc: int) -> None:
        if nr == r and nc == c:
            return
        v = board[nr][nc]
        if v == EMPTY:
            libs.add((nr, nc))
        elif v == OPP and (nr, nc) in captured_stones:
            libs.add((nr, nc))

    for dr, dc in DIRS:
        add_lib(r + dr, c + dc)

    own_size = 1
    for g in adj_own:
        own_size += groups[g]["size"]
        for sr, sc in groups[g]["stones"]:
            for dr, dc in DIRS:
                add_lib(sr + dr, sc + dc)

    if not libs:
        return None

    saved = set()
    for g in adj_own:
        if len(groups[g]["libs"]) == 1 and (r, c) in groups[g]["libs"]:
            saved.add(g)

    if captured_stones:
        for sr, sc in captured_stones:
            for dr, dc in DIRS:
                nr, nc = sr + dr, sc + dc
                if board[nr][nc] == MY:
                    og = gid[nr][nc]
                    if og >= 0 and len(groups[og]["libs"]) == 1:
                        saved.add(og)

    mh = current_hash ^ _Z_MY[_idx(r, c)]
    for sr, sc in captured_stones:
        mh ^= _Z_OPP[_idx(sr, sc)]

    return {
        "adj_own": adj_own,
        "adj_opp": adj_opp,
        "adj_empty": adj_empty,
        "adj_my_count": adj_my_count,
        "adj_opp_count": adj_opp_count,
        "captured": captured,
        "cap_size": len(captured_stones),
        "new_libs": len(libs),
        "own_size": own_size,
        "saved": saved,
        "hash": mh,
    }


def _score_move(board, groups, info, ctx, r: int, c: int) -> float:
    total = ctx["total"]
    my_inf = ctx["my_inf"][r][c]
    opp_inf = ctx["opp_inf"][r][c]
    cap_size = info["cap_size"]
    new_libs = info["new_libs"]
    saved = info["saved"]

    score = 0.0
    tactical = False
    captured_ids = set(info["captured"])

    if cap_size:
        tactical = True
        cap_val = 0.0
        for g in info["captured"]:
            sz = groups[g]["size"]
            cap_val += _group_value(sz)
            if sz >= 3:
                score += 40.0 * sz
        score += 650.0 + 620.0 * cap_val + 65.0 * cap_size
        if len(info["captured"]) >= 2:
            score += 120.0 * len(info["captured"])

    if saved:
        tactical = True
        save_val = 0.0
        raw = 0
        for g in saved:
            sz = groups[g]["size"]
            raw += sz
            save_val += _group_value(sz)
        score += 550.0 * len(saved) + 700.0 * save_val + 45.0 * raw
        if new_libs >= 3:
            score += 70.0 * new_libs
        elif new_libs <= 1:
            score -= 250.0

    for g in info["adj_opp"]:
        if g in captured_ids:
            continue
        libs = groups[g]["libs"]
        if (r, c) not in libs:
            continue
        lc = len(libs)
        sz = groups[g]["size"]
        gv = _group_value(sz)
        if lc == 2:
            tactical = True
            score += 150.0 + 170.0 * gv
            if sz >= 4:
                score += 120.0
            if new_libs <= 1 and not cap_size:
                score -= 520.0
        elif lc == 3:
            score += 35.0 + 34.0 * gv

    for g in info["adj_own"]:
        libs = groups[g]["libs"]
        if (r, c) not in libs:
            continue
        lc = len(libs)
        sz = groups[g]["size"]
        gv = _group_value(sz)
        if lc == 2:
            tactical = True
            score += 130.0 + 120.0 * gv + 20.0 * new_libs
        elif lc == 3:
            score += 35.0 + 30.0 * gv

    if len(info["adj_own"]) >= 2:
        join_val = 0.0
        weak_join = False
        for g in info["adj_own"]:
            join_val += _group_value(groups[g]["size"])
            if len(groups[g]["libs"]) <= 3:
                weak_join = True
        score += 95.0 + 36.0 * join_val
        if weak_join:
            tactical = True
            score += 130.0

    opp_neighbors = [g for g in info["adj_opp"] if g not in captured_ids]
    if len(opp_neighbors) >= 2:
        cut_val = 0.0
        cut_weak = False
        for g in opp_neighbors:
            cut_val += _group_value(groups[g]["size"])
            if len(groups[g]["libs"]) <= 3:
                cut_weak = True
        score += 90.0 + 32.0 * cut_val
        if cut_weak:
            tactical = True
            score += 120.0
        if new_libs <= 2:
            score -= 80.0

    score += 18.0 * min(new_libs, 6)
    if new_libs >= 5:
        score += 18.0

    if new_libs <= 1:
        penalty = 1150.0 + 45.0 * info["own_size"]
        if cap_size >= 3:
            penalty *= 0.45
        if saved:
            penalty *= 0.75
        score -= penalty
        if cap_size == 1:
            score -= 550.0
    elif new_libs == 2:
        penalty = 110.0
        if opp_inf > my_inf:
            penalty += min(160.0, 4.0 * (opp_inf - my_inf))
        if cap_size or saved:
            penalty *= 0.6
        score -= penalty
    elif new_libs == 3:
        score -= 10.0

    score += _line_bonus(r, c, total)
    score += _standard_point_bonus(r, c, total)
    score += _corner_bonus(r, c, total, ctx["corner_data"])
    score += _side_extension_bonus(r, c, total, ctx["my_stones"], ctx["opp_stones"])
    score += _local_shape_bonus(board, r, c, tactical)

    own_eye = _is_eye(board, r, c, MY)
    own_surrounded = True if own_eye else _orth_surrounded(board, r, c, MY)
    opp_eye = _is_eye(board, r, c, OPP)

    if own_eye and not cap_size:
        score -= 2300.0 if not saved else 900.0
    elif own_surrounded and not cap_size:
        score -= 520.0 if not tactical else 180.0

    if opp_eye:
        if cap_size:
            score += 380.0
        else:
            score -= 350.0

    rid = ctx["region_id"][r][c]
    if rid >= 0:
        reg = ctx["regions"][rid]
        owner = reg["owner"]
        size = reg["size"]
        if owner == MY:
            if not tactical and not cap_size and not saved:
                score -= min(520.0, 25.0 + 5.0 * size)
            else:
                score -= min(120.0, 2.0 * size)
        elif owner == OPP:
            if new_libs >= 3 or tactical:
                score += min(220.0, 20.0 + 4.0 * size)
            else:
                score += min(70.0, 2.0 * size) - 70.0
        else:
            score += min(55.0, 1.2 * size)

    frontier = min(my_inf, opp_inf)
    score += 1.35 * frontier + 0.22 * my_inf + 0.38 * opp_inf

    if total < 45 and info["adj_opp_count"] and not info["adj_my_count"] and not cap_size:
        score -= 35.0

    if not tactical and not cap_size and not saved:
        if my_inf > opp_inf + 22:
            score -= 3.0 * (my_inf - opp_inf - 22)
        if opp_inf > my_inf + 30 and new_libs <= 2:
            score -= 3.5 * (opp_inf - my_inf - 30)

    if opp_inf > my_inf + 9 and new_libs >= 3 and not own_surrounded:
        score += 0.65 * min(28.0, opp_inf - my_inf)

    if ctx["largest_own_atari"] and not saved and cap_size == 0:
        score -= 55.0 * min(ctx["largest_own_atari"], 8) + 12.0 * min(ctx["total_own_atari"], 25)

    if ctx["largest_opp_atari"] >= 2 and cap_size == 0:
        score -= 35.0 * min(ctx["largest_opp_atari"], 10)

    return score


def _policy_impl(me, opponent) -> tuple[int, int]:
    global _LAST_TOTAL

    board, current_hash, total, my_stones, opp_stones = _make_board(me, opponent)

    if total <= 1 or (_LAST_TOTAL is not None and total <= 2 and _LAST_TOTAL > 20):
        _RECENT_AFTER.clear()
        _RECENT_SET.clear()

    groups, gid = _build_groups(board)
    my_inf, opp_inf = _compute_influence(my_stones, opp_stones)
    region_id, regions = _empty_regions(board)
    corner_data = _corner_summary(board)

    largest_own_atari = 0
    total_own_atari = 0
    largest_opp_atari = 0

    for g in groups:
        if len(g["libs"]) == 1:
            sz = g["size"]
            if g["color"] == MY:
                largest_own_atari = max(largest_own_atari, sz)
                total_own_atari += min(sz, 15)
            else:
                largest_opp_atari = max(largest_opp_atari, sz)

    ctx = {
        "total": total,
        "my_inf": my_inf,
        "opp_inf": opp_inf,
        "my_stones": my_stones,
        "opp_stones": opp_stones,
        "region_id": region_id,
        "regions": regions,
        "corner_data": corner_data,
        "largest_own_atari": largest_own_atari,
        "total_own_atari": total_own_atari,
        "largest_opp_atari": largest_opp_atari,
    }

    best_move = (0, 0)
    best_hash = None
    best_score = -10**100

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] != EMPTY:
                continue

            info = _analyze_move(board, groups, gid, current_hash, r, c)
            if info is None:
                continue

            score = _score_move(board, groups, info, ctx, r, c)

            # Avoid simple ko/superko-like repeats when sequential calls share process memory.
            if info["hash"] in _RECENT_SET:
                score -= 100000.0

            score += _jitter(current_hash, r, c)

            if score > best_score:
                best_score = score
                best_move = (r, c)
                best_hash = info["hash"]

    _LAST_TOTAL = total

    if best_hash is None:
        return (0, 0)

    if total < 180:
        threshold = -300.0
    elif total < 280:
        threshold = -120.0
    else:
        threshold = 5.0

    if largest_own_atari or largest_opp_atari:
        threshold = min(threshold, -700.0)

    if best_score < threshold:
        return (0, 0)

    _remember(best_hash)
    return best_move


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        move = _policy_impl(me, opponent)
        r, c = move
        if (r == 0 and c == 0) or (1 <= r <= N and 1 <= c <= N):
            return (int(r), int(c))
        return (0, 0)
    except Exception:
        return (0, 0)
