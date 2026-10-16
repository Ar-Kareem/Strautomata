
import random

N = 19

_NEIGHBORS = [[() for _ in range(N + 1)] for __ in range(N + 1)]
_DIAGONALS = [[() for _ in range(N + 1)] for __ in range(N + 1)]

for _r in range(1, N + 1):
    for _c in range(1, N + 1):
        ns = []
        if _r > 1:
            ns.append((_r - 1, _c))
        if _r < N:
            ns.append((_r + 1, _c))
        if _c > 1:
            ns.append((_r, _c - 1))
        if _c < N:
            ns.append((_r, _c + 1))
        _NEIGHBORS[_r][_c] = tuple(ns)

        ds = []
        for dr in (-1, 1):
            for dc in (-1, 1):
                rr, cc = _r + dr, _c + dc
                if 1 <= rr <= N and 1 <= cc <= N:
                    ds.append((rr, cc))
        _DIAGONALS[_r][_c] = tuple(ds)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        return _policy_impl(me, opponent)
    except Exception:
        # Passing is always legal and prevents disqualification on unexpected input.
        return (0, 0)


def _policy_impl(me, opponent):
    board = [[0] * (N + 1) for _ in range(N + 1)]

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 1

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r][c] == 0:
            board[r][c] = 2

    my_stones = []
    opp_stones = []
    all_stones = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 1:
                my_stones.append((r, c))
                all_stones.append((r, c))
            elif board[r][c] == 2:
                opp_stones.append((r, c))
                all_stones.append((r, c))

    total = len(all_stones)

    groups, gid = _analyze_groups(board)
    own_inf, opp_inf = _compute_influence(board)

    best_move = None
    best_score = -10**18

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] != 0:
                continue

            info = _move_info(board, groups, gid, r, c)
            if info is None:
                continue

            score = _score_move(
                board, groups, info, total,
                own_inf, opp_inf,
                my_stones, opp_stones, all_stones
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # Do not play only terrible self-atari / eye-filling / likely-ko moves.
    if best_score < -1000:
        return (0, 0)

    # Late in the game, avoid pointless dame/territory filling unless tactical.
    if total > 330 and best_score < 150:
        return (0, 0)
    if total > 260 and best_score < -150:
        return (0, 0)

    return best_move


def _analyze_groups(board):
    gid = [[-1] * (N + 1) for _ in range(N + 1)]
    groups = []

    for r in range(1, N + 1):
        for c in range(1, N + 1):
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

                for nr, nc in _NEIGHBORS[sr][sc]:
                    v = board[nr][nc]
                    if v == 0:
                        libs.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append({
                "color": color,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
            })

    return groups, gid


def _move_info(board, groups, gid, r, c):
    if board[r][c] != 0:
        return None

    p = (r, c)
    adj_own = set()
    adj_opp = set()

    for nr, nc in _NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 1:
            adj_own.add(gid[nr][nc])
        elif v == 2:
            adj_opp.add(gid[nr][nc])

    cap_gids = []
    for g in adj_opp:
        libs = groups[g]["libs"]
        if len(libs) == 1 and p in libs:
            cap_gids.append(g)

    captured_stones = set()
    for g in cap_gids:
        captured_stones.update(groups[g]["stones"])

    merged_stones = [p]
    for g in adj_own:
        merged_stones.extend(groups[g]["stones"])

    result_libs = set()
    for sr, sc in merged_stones:
        for nr, nc in _NEIGHBORS[sr][sc]:
            if (nr, nc) == p:
                continue
            if (nr, nc) in captured_stones:
                result_libs.add((nr, nc))
            elif board[nr][nc] == 0:
                result_libs.add((nr, nc))

    result_libs.discard(p)

    # Suicide is illegal.
    if not result_libs:
        return None

    captured_count = len(captured_stones)
    result_size = len(merged_stones)

    # A move that captures exactly one stone, leaves a single isolated stone,
    # and has exactly one liberty is the classic immediate-ko shape.  Since
    # the API gives no history, avoid it to reduce illegal ko recaptures.
    koish = (captured_count == 1 and result_size == 1 and len(result_libs) == 1)

    return {
        "r": r,
        "c": c,
        "adj_own": adj_own,
        "adj_opp": adj_opp,
        "cap_gids": tuple(cap_gids),
        "captured": captured_count,
        "libs_after": result_libs,
        "result_size": result_size,
        "koish": koish,
    }


def _score_move(board, groups, info, total, own_inf, opp_inf,
                my_stones, opp_stones, all_stones):
    r = info["r"]
    c = info["c"]
    p = (r, c)
    score = float(_positional_value(r, c, total))
    score += random.random() * 0.01

    libs_after = len(info["libs_after"])
    captured = info["captured"]
    cap_gids = set(info["cap_gids"])

    tactical = False
    own_atari_save = False

    # Capturing opponent stones is the strongest tactical feature.
    if captured:
        tactical = True
        cap_sizes = [groups[g]["size"] for g in cap_gids]
        largest = max(cap_sizes) if cap_sizes else 0
        score += 4800 + 650 * captured + 90 * captured * captured
        score += 180 * sum(cap_sizes)
        score += 90 * largest * largest

    # Avoid likely ko recaptures; pass or play elsewhere instead.
    if info["koish"]:
        score -= 100000

    # Save friendly groups in atari or low-liberty situations.
    for g in info["adj_own"]:
        gr = groups[g]
        libs = gr["libs"]
        if p not in libs:
            continue

        lcnt = len(libs)
        size = gr["size"]

        if lcnt == 1:
            tactical = True
            own_atari_save = True
            score += 4300 + 380 * min(size, 30) + 60 * size
            if libs_after >= 3:
                score += 900
            elif libs_after == 2:
                score += 350
            else:
                score -= 2500
        elif lcnt == 2:
            score += 700 + 90 * min(size, 25) + 45 * libs_after
        elif lcnt == 3:
            score += 150 + 25 * min(size, 20)

    # Attack opponent groups by reducing liberties, especially putting them
    # into atari.
    for g in info["adj_opp"]:
        if g in cap_gids:
            continue
        gr = groups[g]
        libs = gr["libs"]
        if p not in libs:
            continue

        lcnt = len(libs)
        size = gr["size"]

        if lcnt == 2:
            tactical = True
            score += 1650 + 220 * min(size, 25) + 35 * size
            if libs_after <= 1:
                score -= 1200
        elif lcnt == 3:
            score += 360 + 55 * min(size, 25)
        elif lcnt == 4:
            score += 90 + 15 * min(size, 20)

    # Connect friendly groups.
    if len(info["adj_own"]) >= 2:
        tactical = True
        sizes = [groups[g]["size"] for g in info["adj_own"]]
        low = sum(1 for g in info["adj_own"] if len(groups[g]["libs"]) <= 2)
        score += 300 + 70 * sum(min(s, 12) for s in sizes) + 300 * low

    # Cut or separate opponent groups.
    if len(info["adj_opp"]) >= 2:
        sizes = [groups[g]["size"] for g in info["adj_opp"]]
        score += 220 + 55 * sum(min(s, 12) for s in sizes)
        if info["adj_own"]:
            score += 120

    # Liberties and self-atari handling.
    score += 35 * min(libs_after, 10)
    if libs_after == 1:
        if not captured and not own_atari_save:
            score -= 5200
        else:
            score -= 1800
    elif libs_after == 2:
        score -= 350
    elif libs_after >= 4:
        score += 80

    # Eye-filling is usually awful unless it captures or saves a group.
    if _is_eye(board, r, c, 1) and not captured:
        if own_atari_save:
            score -= 1500
        else:
            score -= 12000

    # Playing in an opponent eye is usually illegal or bad unless capturing.
    if _is_eye(board, r, c, 2) and not captured:
        score -= 900

    # Local shape: friendly adjacency, diagonal shape, and contact penalties.
    adj_own_count = 0
    adj_opp_count = 0
    empty_adj = 0

    for nr, nc in _NEIGHBORS[r][c]:
        if board[nr][nc] == 1:
            adj_own_count += 1
        elif board[nr][nc] == 2:
            adj_opp_count += 1
        else:
            empty_adj += 1

    diag_own = 0
    diag_opp = 0
    for nr, nc in _DIAGONALS[r][c]:
        if board[nr][nc] == 1:
            diag_own += 1
        elif board[nr][nc] == 2:
            diag_opp += 1

    score += 22 * adj_own_count - 18 * adj_opp_count
    score += 12 * diag_own + 6 * diag_opp
    score += 10 * empty_adj

    if adj_opp_count and not adj_own_count and not tactical:
        score -= 90
    if adj_opp_count >= 2 and libs_after <= 2 and not captured:
        score -= 220

    # Influence: prefer important contested areas, but do not let this outweigh
    # life-and-death tactics.
    oi = own_inf[r][c]
    pi = opp_inf[r][c]

    if total < 80:
        score += 0.45 * oi + 0.65 * pi
    else:
        score += 0.35 * oi + 0.85 * pi

    if total > 100 and oi + pi < 8:
        score -= 35

    # Opening spacing: good extensions and approaches, not random contact.
    if all_stones:
        md_all = _min_dist(p, all_stones)
        if total < 80:
            if md_all == 1 and not tactical:
                score -= 120
            elif 3 <= md_all <= 6:
                score += 45
            elif 7 <= md_all <= 11:
                score += 25
    if my_stones:
        md_me = _min_dist(p, my_stones)
        if total < 90:
            if md_me <= 2 and not tactical:
                score -= 60
            elif md_me >= 7:
                score += 25
    if opp_stones:
        md_opp = _min_dist(p, opp_stones)
        if total < 100:
            if md_opp == 1 and not tactical:
                score -= 70
            elif 3 <= md_opp <= 6:
                score += 30

    return score


def _compute_influence(board):
    own = [[0] * (N + 1) for _ in range(N + 1)]
    opp = [[0] * (N + 1) for _ in range(N + 1)]
    weights = (0, 24, 14, 8, 4)

    for r in range(1, N + 1):
        for c in range(1, N + 1):
            color = board[r][c]
            if color == 0:
                continue

            grid = own if color == 1 else opp

            for dr in range(-4, 5):
                for dc in range(-4, 5):
                    d = abs(dr) + abs(dc)
                    if d == 0 or d > 4:
                        continue
                    rr, cc = r + dr, c + dc
                    if 1 <= rr <= N and 1 <= cc <= N:
                        grid[rr][cc] += weights[d]

    return own, opp


def _positional_value(r, c, total):
    edge = min(r, c, N + 1 - r, N + 1 - c)
    line_values = {
        1: -150,
        2: -25,
        3: 95,
        4: 125,
        5: 90,
        6: 65,
        7: 45,
        8: 30,
        9: 22,
        10: 18,
    }
    val = line_values.get(edge, 15)

    corners = ((4, 4), (4, 16), (16, 4), (16, 16))
    corner_dist = min(abs(r - a) + abs(c - b) for a, b in corners)
    corner_bonus = max(0, 95 - 18 * corner_dist)

    side_stars = ((4, 10), (10, 4), (10, 16), (16, 10), (10, 10))
    side_dist = min(abs(r - a) + abs(c - b) for a, b in side_stars)
    side_bonus = max(0, 50 - 10 * side_dist)

    if total < 80:
        val += corner_bonus + side_bonus
    elif total < 180:
        val += 0.55 * corner_bonus + 0.45 * side_bonus
    else:
        val += 0.20 * corner_bonus + 0.20 * side_bonus

    return val


def _is_eye(board, r, c, color):
    if board[r][c] != 0:
        return False

    for nr, nc in _NEIGHBORS[r][c]:
        if board[nr][nc] != color:
            return False

    opp = 3 - color
    bad_diag = 0
    diag_count = 0

    for nr, nc in _DIAGONALS[r][c]:
        diag_count += 1
        if board[nr][nc] == opp:
            bad_diag += 1

    if diag_count < 4:
        return bad_diag == 0
    return bad_diag <= 1


def _min_dist(p, stones):
    r, c = p
    best = 100
    for sr, sc in stones:
        d = abs(r - sr) + abs(c - sc)
        if d < best:
            best = d
            if best == 1:
                return 1
    return best
