
import math

N = 19
EMPTY = 0
ME = 1
OPP = 2

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


# Opening preferences, in 0-indexed coordinates.
_OPENING_WEIGHTS = {}


def _add_opening(points, weight):
    for p in points:
        _OPENING_WEIGHTS[p] = max(_OPENING_WEIGHTS.get(p, 0.0), weight)


# 4-4 points
_add_opening([(3, 3), (3, 15), (15, 3), (15, 15)], 260.0)

# 3-4 / 4-3 points
_add_opening(
    [
        (2, 3), (3, 2), (2, 15), (3, 16),
        (15, 2), (16, 3), (15, 16), (16, 15),
    ],
    220.0,
)

# 3-3 points
_add_opening([(2, 2), (2, 16), (16, 2), (16, 16)], 95.0)

# Side star points and tengen
_add_opening([(3, 9), (9, 3), (9, 15), (15, 9)], 135.0)
_add_opening([(9, 9)], 85.0)

# Some 5-4 style points
_add_opening(
    [
        (3, 4), (4, 3), (3, 14), (4, 15),
        (14, 3), (15, 4), (14, 15), (15, 14),
    ],
    100.0,
)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[EMPTY for _ in range(N)] for _ in range(N)]

    my_stones = []
    opp_stones = []

    for rr, cc in me:
        if 1 <= rr <= N and 1 <= cc <= N:
            r, c = rr - 1, cc - 1
            board[r][c] = ME
            my_stones.append((r, c))

    for rr, cc in opponent:
        if 1 <= rr <= N and 1 <= cc <= N:
            r, c = rr - 1, cc - 1
            board[r][c] = OPP
            opp_stones.append((r, c))

    total = len(my_stones) + len(opp_stones)

    groups, gid = _find_groups(board)
    own_inf = _make_influence(my_stones)
    opp_inf = _make_influence(opp_stones)
    all_stones = my_stones + opp_stones

    best_move = None
    best_score = -10**18

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue

            info = _analyze_move(board, groups, gid, r, c)
            if not info["legal"]:
                continue

            # Without history, exact ko cannot be known.  This avoids the
            # classic simple-ko recapture shape, so returned moves are much
            # less likely to be rejected by a rules engine with ko.
            if info["ko_risk"]:
                continue

            score = _score_move(
                board, groups, r, c, info, total,
                own_inf, opp_inf, all_stones
            )

            if score > best_score:
                best_score = score
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # If all remaining moves look strongly self-damaging, pass rather than
    # filling our own eyes or playing pointless suicide-like endgame moves.
    if best_score < -700.0 or (total > 260 and best_score < -120.0):
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)


def _neighbors(r, c):
    if r > 0:
        yield r - 1, c
    if r + 1 < N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < N:
        yield r, c + 1


def _find_groups(board):
    gid = [[-1 for _ in range(N)] for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            color = board[r][c]
            if color == EMPTY or gid[r][c] != -1:
                continue

            idx = len(groups)
            stack = [(r, c)]
            gid[r][c] = idx
            stones = []
            liberties = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))

                for nr, nc in _neighbors(sr, sc):
                    v = board[nr][nc]
                    if v == EMPTY:
                        liberties.add((nr, nc))
                    elif v == color and gid[nr][nc] == -1:
                        gid[nr][nc] = idx
                        stack.append((nr, nc))

            groups.append(
                {
                    "color": color,
                    "stones": stones,
                    "libs": liberties,
                }
            )

    return groups, gid


def _flood_group(board, r, c):
    color = board[r][c]
    if color == EMPTY:
        return set(), set()

    seen = {(r, c)}
    stones = set()
    liberties = set()
    stack = [(r, c)]

    while stack:
        sr, sc = stack.pop()
        stones.add((sr, sc))

        for nr, nc in _neighbors(sr, sc):
            v = board[nr][nc]
            if v == EMPTY:
                liberties.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return stones, liberties


def _analyze_move(board, groups, gid, r, c):
    if board[r][c] != EMPTY:
        return {"legal": False}

    adj_own = set()
    adj_opp = set()

    for nr, nc in _neighbors(r, c):
        v = board[nr][nc]
        if v == ME:
            adj_own.add(gid[nr][nc])
        elif v == OPP:
            adj_opp.add(gid[nr][nc])

    captured = set()
    for g in adj_opp:
        if len(groups[g]["libs"]) == 1 and (r, c) in groups[g]["libs"]:
            captured.add(g)

    cap_count = 0
    new_board = [row[:] for row in board]
    new_board[r][c] = ME

    for g in captured:
        stones = groups[g]["stones"]
        cap_count += len(stones)
        for sr, sc in stones:
            new_board[sr][sc] = EMPTY

    new_stones, new_libs = _flood_group(new_board, r, c)

    if len(new_libs) == 0:
        return {"legal": False}

    ko_risk = cap_count == 1 and len(new_stones) == 1 and len(new_libs) == 1

    return {
        "legal": True,
        "adj_own": adj_own,
        "adj_opp": adj_opp,
        "captured": captured,
        "cap_count": cap_count,
        "new_stones": new_stones,
        "new_libs": new_libs,
        "ko_risk": ko_risk,
    }


def _score_move(board, groups, r, c, info, total, own_inf, opp_inf, all_stones):
    adj_own = info["adj_own"]
    adj_opp = info["adj_opp"]
    captured = info["captured"]
    cap_count = info["cap_count"]
    libn = len(info["new_libs"])
    new_size = len(info["new_stones"])

    score = 0.0

    # Captures: very important, especially larger groups.
    capture_value = 0.0
    if cap_count:
        capture_value += 650.0 + 950.0 * cap_count
        for g in captured:
            sz = len(groups[g]["stones"])
            capture_value += 80.0 * sz + 260.0 * math.sqrt(sz)
        if cap_count >= 3:
            capture_value += 250.0
        score += capture_value

    # Save our adjacent groups, especially groups in atari.
    save_value = 0.0
    for g in adj_own:
        libs = groups[g]["libs"]
        sz = len(groups[g]["stones"])
        l = len(libs)

        if l == 1:
            save_value += 700.0 + 1000.0 * sz + 120.0 * math.sqrt(sz)
        elif l == 2:
            save_value += 90.0 + 125.0 * sz
        elif l == 3:
            save_value += 20.0 + 28.0 * sz

    score += save_value

    # Attack opponent groups by putting them into atari or reducing liberties.
    attack_value = 0.0
    for g in adj_opp:
        if g in captured:
            continue

        old_libs = len(groups[g]["libs"])
        sz = len(groups[g]["stones"])
        new_libs = old_libs - 1

        if new_libs == 1:
            v = 330.0 + 155.0 * sz
            if libn >= 3:
                v += 90.0
            attack_value += v
        elif new_libs == 2:
            attack_value += 40.0 + 28.0 * sz
        elif new_libs == 3:
            attack_value += 10.0 + 8.0 * sz

    score += attack_value

    tactical_value = capture_value + save_value + attack_value

    # Connections and cuts.
    if adj_own:
        own_sizes = [len(groups[g]["stones"]) for g in adj_own]
        score += 45.0 * len(adj_own)
        score += sum(9.0 * min(12, sz) for sz in own_sizes)

        if len(adj_own) >= 2:
            score += 190.0 * (len(adj_own) - 1)
            weak_connections = sum(1 for g in adj_own if len(groups[g]["libs"]) <= 3)
            score += 55.0 * weak_connections

    if adj_opp:
        score += 24.0 * len(adj_opp)
        if len(adj_opp) >= 2:
            score += 150.0 * (len(adj_opp) - 1)
            if adj_own or own_inf[r][c] + 3.0 >= opp_inf[r][c]:
                score += 85.0

    # Liberties and general move health.
    score += 22.0 * min(libn, 8)
    if libn >= 4:
        score += 22.0
    score += 2.2 * min(new_size, 25)

    empty_adj = 0
    friendly_adj_count = 0
    enemy_adj_count = 0
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] == EMPTY:
            empty_adj += 1
        elif board[nr][nc] == ME:
            friendly_adj_count += 1
        elif board[nr][nc] == OPP:
            enemy_adj_count += 1

    score += 5.0 * empty_adj

    # Avoid self-atari unless it is tactically justified.
    if libn <= 1:
        if capture_value > 0.0 or save_value > 0.0:
            score -= 360.0
        else:
            score -= 2100.0
    elif libn == 2 and tactical_value < 250.0:
        score -= 120.0

    # Unsupported contact moves are often bad.
    if enemy_adj_count and not friendly_adj_count and cap_count == 0:
        if libn <= 2:
            score -= 280.0
        elif libn == 3:
            score -= 90.0

        if opp_inf[r][c] > own_inf[r][c] + 4.0:
            score -= 65.0

    if enemy_adj_count and friendly_adj_count:
        score += 75.0

    # Diagonal shape and light connection potential.
    diag_own = 0
    diag_opp = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            if board[nr][nc] == ME:
                diag_own += 1
            elif board[nr][nc] == OPP:
                diag_opp += 1

    score += 14.0 * diag_own + 6.0 * diag_opp
    if diag_own >= 2 and not adj_own:
        score += 45.0

    # Discourage heavy, overconcentrated non-tactical clumps.
    if friendly_adj_count >= 3 and tactical_value < 200.0:
        score -= 60.0 * (friendly_adj_count - 2)

    # Eye handling: do not fill our own real-looking eyes unless necessary.
    if cap_count == 0 and save_value == 0.0 and _is_eye_like(board, r, c, ME):
        score -= 1250.0 if total < 260 else 750.0

    # Playing in an opponent eye shape can be useful if it is legal.
    if _is_eye_like(board, r, c, OPP):
        score += 85.0 + 0.35 * total

    # Positional 19x19 values.
    score += _line_score(r, c, total)

    if total < 85:
        opening = _OPENING_WEIGHTS.get((r, c), 0.0)
        if opening:
            score += opening * ((85.0 - total) / 85.0)

    # Influence: prefer supported frontier points and relevant fights.
    oi = own_inf[r][c]
    pi = opp_inf[r][c]

    if total < 150:
        score += 3.5 * oi + 2.8 * pi
    else:
        score += 2.1 * oi + 3.3 * pi

    if pi > oi + 10.0 and not adj_own and cap_count == 0:
        score -= 110.0 + 8.0 * (pi - oi)

    if oi > pi + 18.0 and not adj_opp and cap_count == 0 and save_value == 0.0 and total < 260:
        score -= 45.0

    # Opening spacing: avoid crowding stones too early unless fighting.
    if total < 55 and tactical_value < 180.0 and all_stones:
        d2 = _nearest_d2(r, c, all_stones)
        if d2 <= 1:
            score -= 130.0
        elif d2 <= 2:
            score -= 70.0
        elif d2 >= 80:
            score += 18.0

    # Small deterministic tiebreaker.
    score += _tiebreak(r, c, total)

    return score


def _line_score(r, c, total):
    line = min(r, c, N - 1 - r, N - 1 - c) + 1

    if total < 80:
        table = {
            1: -220.0,
            2: -85.0,
            3: 22.0,
            4: 58.0,
            5: 26.0,
            6: 12.0,
        }
        return table.get(line, 5.0)

    if total < 220:
        table = {
            1: -90.0,
            2: -20.0,
            3: 32.0,
            4: 38.0,
            5: 18.0,
            6: 10.0,
        }
        return table.get(line, 4.0)

    table = {
        1: -20.0,
        2: 18.0,
        3: 24.0,
        4: 15.0,
        5: 8.0,
    }
    return table.get(line, 2.0)


def _make_influence(stones):
    grid = [[0.0 for _ in range(N)] for _ in range(N)]
    weights = [0.0, 6.0, 4.2, 2.8, 1.7, 1.0]

    for sr, sc in stones:
        for dr in range(-5, 6):
            rem = 5 - abs(dr)
            nr = sr + dr
            if not (0 <= nr < N):
                continue

            for dc in range(-rem, rem + 1):
                nc = sc + dc
                if not (0 <= nc < N):
                    continue

                d = abs(dr) + abs(dc)
                if 0 < d <= 5:
                    grid[nr][nc] += weights[d]

    return grid


def _is_eye_like(board, r, c, color):
    if board[r][c] != EMPTY:
        return False

    friendly_orth = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            if board[nr][nc] != color:
                return False
            friendly_orth += 1

    if friendly_orth == 0:
        return False

    bad_diag = 0
    diag_on_board = 0

    enemy_color = OPP if color == ME else ME

    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            diag_on_board += 1
            if board[nr][nc] == enemy_color:
                bad_diag += 1

    if diag_on_board <= 2:
        return bad_diag == 0

    return bad_diag <= 1


def _nearest_d2(r, c, stones):
    best = 10**9
    for sr, sc in stones:
        d = (r - sr) * (r - sr) + (c - sc) * (c - sc)
        if d < best:
            best = d
    return best


def _tiebreak(r, c, total):
    x = ((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ ((total + 1) * 83492791)
    return (x & 1023) / 100000.0
