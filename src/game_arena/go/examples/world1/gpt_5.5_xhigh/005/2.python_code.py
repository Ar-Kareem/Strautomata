
from __future__ import annotations

N = 19
EMPTY = 0
ME = 1
OPP = 2

NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))

INFLUENCE_WEIGHTS = (0, 18, 12, 8, 5, 3, 2)

SHAPE_OFFSETS = (
    (-2, 0, 28), (2, 0, 28), (0, -2, 28), (0, 2, 28),
    (-1, -2, 38), (-1, 2, 38), (1, -2, 38), (1, 2, 38),
    (-2, -1, 38), (-2, 1, 38), (2, -1, 38), (2, 1, 38),
    (-3, 0, 18), (3, 0, 18), (0, -3, 18), (0, 3, 18),
    (-2, -2, 20), (-2, 2, 20), (2, -2, 20), (2, 2, 20),
    (-1, -1, 10), (-1, 1, 10), (1, -1, 10), (1, 1, 10),
)


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[EMPTY] * N for _ in range(N)]
    my_stones = []
    opp_stones = []

    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            rr, cc = r - 1, c - 1
            if board[rr][cc] == EMPTY:
                board[rr][cc] = ME
                my_stones.append((rr, cc))

    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            rr, cc = r - 1, c - 1
            if board[rr][cc] == EMPTY:
                board[rr][cc] = OPP
                opp_stones.append((rr, cc))

    gid, groups = _analyze(board)
    lib_count = [len(g["libs"]) for g in groups]

    own_lib_map = {}
    opp_lib_map = {}
    for i, g in enumerate(groups):
        target = own_lib_map if g["color"] == ME else opp_lib_map
        for p in g["libs"]:
            if p in target:
                target[p].append(i)
            else:
                target[p] = [i]

    own_inf, opp_inf = _influence(my_stones, opp_stones)
    total = len(my_stones) + len(opp_stones)
    empty_count = N * N - total
    seed = _seed(my_stones, opp_stones)

    best_move = None
    best_score = -10**18

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue
            if not _is_legal(board, gid, lib_count, r, c):
                continue

            stats = _move_stats(board, gid, groups, lib_count, r, c)

            # With no move history, a one-stone capture into a one-liberty isolated
            # stone may be an illegal immediate ko recapture. Prefer passing to
            # risking disqualification if every available move is like this.
            if stats["ko_like"]:
                continue

            score = _score_move(
                board, groups, lib_count, own_lib_map, opp_lib_map,
                own_inf, opp_inf, total, r, c, stats
            )
            score += _jitter(seed, r, c)

            if score > best_score:
                best_score = score
                best_move = (r, c)

    if best_move is None:
        return (0, 0)

    # Do not fill obvious eyes or play hopeless self-atari when passing is legal.
    if best_score < -5000:
        return (0, 0)

    # In very late board states, avoid damaging own territory for tiny value.
    if total > 300 and best_score < -250:
        return (0, 0)
    if empty_count <= 4 and best_score < 100:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)


def _iter_neighbors(r, c):
    if r > 0:
        yield r - 1, c
    if r + 1 < N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < N:
        yield r, c + 1


def _analyze(board):
    gid = [[-1] * N for _ in range(N)]
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
            libs = set()

            while stack:
                sr, sc = stack.pop()
                stones.append((sr, sc))

                for nr, nc in _iter_neighbors(sr, sc):
                    v = board[nr][nc]
                    if v == EMPTY:
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

    return gid, groups


def _is_legal(board, gid, lib_count, r, c):
    if board[r][c] != EMPTY:
        return False

    # Any adjacent empty point means the new stone has a liberty.
    for nr, nc in _iter_neighbors(r, c):
        if board[nr][nc] == EMPTY:
            return True

    # Capturing an adjacent opponent group is legal.
    for nr, nc in _iter_neighbors(r, c):
        if board[nr][nc] == OPP and lib_count[gid[nr][nc]] == 1:
            return True

    # Connecting to a friendly group that has another liberty is legal.
    for nr, nc in _iter_neighbors(r, c):
        if board[nr][nc] == ME and lib_count[gid[nr][nc]] > 1:
            return True

    return False


def _move_stats(board, gid, groups, lib_count, r, c):
    pos = (r, c)
    adj_own = set()
    adj_opp = set()
    empty_neighbors = []
    own_adj_count = 0
    opp_adj_count = 0

    for nr, nc in _iter_neighbors(r, c):
        v = board[nr][nc]
        if v == EMPTY:
            empty_neighbors.append((nr, nc))
        elif v == ME:
            own_adj_count += 1
            adj_own.add(gid[nr][nc])
        elif v == OPP:
            opp_adj_count += 1
            adj_opp.add(gid[nr][nc])

    captured = []
    capture_count = 0
    for g in adj_opp:
        if lib_count[g] == 1:
            captured.append(g)
            capture_count += groups[g]["size"]

    # Exact liberties of the newly formed friendly group, without fully copying board.
    libs = set(empty_neighbors)

    for g in adj_own:
        libs.update(groups[g]["libs"])
    libs.discard(pos)

    if captured:
        for g in captured:
            for sr, sc in groups[g]["stones"]:
                for nr, nc in _iter_neighbors(sr, sc):
                    if nr == r and nc == c:
                        libs.add((sr, sc))
                        break
                    if board[nr][nc] == ME and gid[nr][nc] in adj_own:
                        libs.add((sr, sc))
                        break

    new_size = 1
    for g in adj_own:
        new_size += groups[g]["size"]

    new_libs = len(libs)
    ko_like = (capture_count == 1 and new_size == 1 and new_libs == 1)

    return {
        "adj_own": adj_own,
        "adj_opp": adj_opp,
        "own_adj_count": own_adj_count,
        "opp_adj_count": opp_adj_count,
        "empty_adj": len(empty_neighbors),
        "captured_groups": captured,
        "capture_count": capture_count,
        "new_size": new_size,
        "new_libs": new_libs,
        "ko_like": ko_like,
    }


def _score_move(board, groups, lib_count, own_lib_map, opp_lib_map,
                own_inf, opp_inf, total, r, c, st):
    pos = (r, c)
    score = 0.0
    cap = st["capture_count"]
    new_libs = st["new_libs"]
    purposeful = cap > 0

    # Captures are urgent and usually sente.
    if cap:
        score += 12000 + 1500 * cap
        if cap >= 3:
            score += 800 * min(cap, 12)

    # Save friendly weak groups.
    for g in own_lib_map.get(pos, ()):
        lc = lib_count[g]
        sz = groups[g]["size"]
        if lc == 1:
            purposeful = True
            score += 11500 + 1400 * min(sz, 12) + 350 * max(0, sz - 12)
        elif lc == 2:
            purposeful = True
            score += 1500 + 180 * min(sz, 12)
        elif lc == 3:
            score += 300 + 35 * min(sz, 12)
        elif lc == 4:
            score += 80 + 12 * min(sz, 10)

    # Attack opponent weak groups.
    for g in opp_lib_map.get(pos, ()):
        lc = lib_count[g]
        sz = groups[g]["size"]
        if lc == 1:
            score += 500 * sz
        elif lc == 2:
            purposeful = True
            score += 2400 + 260 * min(sz, 12) + 70 * max(0, sz - 12)
        elif lc == 3:
            score += 450 + 60 * min(sz, 10)
        elif lc == 4:
            score += 100 + 15 * min(sz, 8)

    # Connections and cuts.
    adj_own = st["adj_own"]
    adj_opp = st["adj_opp"]

    if len(adj_own) >= 2:
        purposeful = True
        score += 750 * (len(adj_own) - 1)
        for g in adj_own:
            score += 45 * min(groups[g]["size"], 10)
            if lib_count[g] <= 3:
                score += 220 * (4 - lib_count[g])
    elif len(adj_own) == 1:
        g = next(iter(adj_own))
        if lib_count[g] <= 3:
            score += 120 * (4 - lib_count[g])

    if len(adj_opp) >= 2:
        purposeful = True
        score += 420 * (len(adj_opp) - 1)
        for g in adj_opp:
            score += 30 * min(groups[g]["size"], 10)

    # Avoid self-atari unless the tactical gain is substantial.
    if new_libs <= 1:
        if cap:
            score -= 7000
            if cap <= 2:
                score -= 3000
        else:
            score -= 10000
            if not purposeful:
                score -= 5000
    elif new_libs == 2:
        score -= 180 if purposeful else 650
    elif new_libs == 3:
        score += 60
    else:
        score += 70 * min(new_libs, 8)

    # Unsupported contact moves are often bad unless they are tactical.
    if st["opp_adj_count"] and cap == 0:
        if st["own_adj_count"] == 0 and not purposeful:
            score -= 350 + 180 * (st["opp_adj_count"] - 1)
            if new_libs <= 2:
                score -= 700
        elif st["own_adj_count"] > 0:
            score += 100 * min(st["own_adj_count"], 2)

    # Filling our own real-looking eye is almost always bad.
    if cap == 0 and _is_eye_like(board, r, c, ME):
        score -= 25000

    # Strategic whole-board heuristics.
    score += _positional_value(r, c, total)

    oi = own_inf[r][c]
    pi = opp_inf[r][c]

    if total < 30:
        score += 0.6 * min(oi, 50) + 0.8 * min(pi, 50) + 1.5 * min(oi, pi, 50)
        if not purposeful and oi + pi > 60:
            score -= (oi + pi - 60) * 2.5
    elif total < 170:
        score += 0.9 * min(oi, 80) + 1.15 * min(pi, 80) + 1.8 * min(oi, pi, 70)
    else:
        score += 0.65 * min(oi, 100) + 0.95 * min(pi, 100) + 1.35 * min(oi, pi, 80)

    # Do not play deep inside our own secure area without a reason.
    diff = oi - pi
    edge = _edge_line(r, c)
    if not purposeful:
        if diff > 38:
            score -= 90 + (diff - 38) * 4.0
        elif diff < -50:
            # Reductions/invasions can be valuable if the move has room.
            if new_libs >= 3 and edge >= 3:
                score += min(180.0, (-diff - 50) * 2.0)
            else:
                score -= (-diff - 50) * 2.5

    near_own, near_opp = _near_counts(board, r, c, 2)
    if not purposeful:
        if near_opp == 0 and near_own >= 6:
            score -= 180 + 30 * (near_own - 6)
        if near_own == 0 and near_opp >= 6 and new_libs < 4:
            score -= 220

    score += _shape_value(board, r, c)

    return score


def _is_eye_like(board, r, c, color):
    if board[r][c] != EMPTY:
        return False

    for nr, nc in _iter_neighbors(r, c):
        if board[nr][nc] != color:
            return False

    enemy = OPP if color == ME else ME
    bad_diag = 0
    off_board = 0

    for dr, dc in DIAGONALS:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < N and 0 <= nc < N):
            off_board += 1
        elif board[nr][nc] == enemy:
            bad_diag += 1

    if off_board == 0:
        return bad_diag <= 1
    return bad_diag == 0


def _edge_line(r, c):
    rr, cc = r + 1, c + 1
    return min(rr, cc, N + 1 - rr, N + 1 - cc)


def _positional_value(r, c, total):
    rr, cc = r + 1, c + 1
    edge = _edge_line(r, c)

    if total < 60:
        if edge == 1:
            val = -140
        elif edge == 2:
            val = -50
        elif edge == 3:
            val = 45
        elif edge == 4:
            val = 85
        elif edge == 5:
            val = 55
        elif edge == 6:
            val = 25
        else:
            val = 5
    elif total < 220:
        if edge == 1:
            val = -70
        elif edge == 2:
            val = 0
        elif edge == 3:
            val = 40
        elif edge == 4:
            val = 55
        elif edge == 5:
            val = 30
        elif edge == 6:
            val = 12
        else:
            val = 0
    else:
        if edge == 1:
            val = 15
        elif edge == 2:
            val = 30
        elif edge == 3:
            val = 25
        elif edge == 4:
            val = 15
        else:
            val = 0

    local = (min(rr, N + 1 - rr), min(cc, N + 1 - cc))

    if total < 80:
        corner_bonus = {
            (4, 4): 190,
            (3, 4): 125, (4, 3): 125,
            (3, 3): 85,
            (5, 4): 70, (4, 5): 70,
            (3, 5): 60, (5, 3): 60,
            (5, 5): 35,
            (2, 4): 15, (4, 2): 15,
        }
        val += corner_bonus.get(local, 0)

        if ((rr in (4, 16) and cc == 10) or
                (cc in (4, 16) and rr == 10)):
            val += 90
        elif rr == 10 and cc == 10:
            val += 70

        val += max(0, 12 - (abs(rr - 10) + abs(cc - 10))) * 1.2

    elif total < 220:
        corner_bonus = {
            (3, 3): 80,
            (4, 4): 55,
            (3, 4): 65, (4, 3): 65,
            (5, 4): 35, (4, 5): 35,
            (3, 5): 30, (5, 3): 30,
            (2, 3): 18, (3, 2): 18,
        }
        val += corner_bonus.get(local, 0)

        if ((rr in (4, 16) and cc == 10) or
                (cc in (4, 16) and rr == 10)):
            val += 25
        elif rr == 10 and cc == 10:
            val += 12

    return val


def _near_counts(board, r, c, radius):
    own = 0
    opp = 0
    r0 = max(0, r - radius)
    r1 = min(N, r + radius + 1)
    c0 = max(0, c - radius)
    c1 = min(N, c + radius + 1)

    for rr in range(r0, r1):
        for cc in range(c0, c1):
            if rr == r and cc == c:
                continue
            v = board[rr][cc]
            if v == ME:
                own += 1
            elif v == OPP:
                opp += 1

    return own, opp


def _shape_value(board, r, c):
    val = 0.0
    for dr, dc, w in SHAPE_OFFSETS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            v = board[nr][nc]
            if v == ME:
                val += w
            elif v == OPP:
                val += w * 0.55
    return val


def _influence(my_stones, opp_stones):
    own = [[0] * N for _ in range(N)]
    opp = [[0] * N for _ in range(N)]
    _add_influence(own, my_stones)
    _add_influence(opp, opp_stones)
    return own, opp


def _add_influence(arr, stones):
    weights = INFLUENCE_WEIGHTS
    for r, c in stones:
        for dr in range(-6, 7):
            nr = r + dr
            if not (0 <= nr < N):
                continue
            lim = 6 - abs(dr)
            for dc in range(-lim, lim + 1):
                if dr == 0 and dc == 0:
                    continue
                nc = c + dc
                if 0 <= nc < N:
                    d = abs(dr) + abs(dc)
                    arr[nr][nc] += weights[d]


def _seed(my_stones, opp_stones):
    s = 0xA511E9B3 ^ (len(my_stones) << 8) ^ len(opp_stones)

    for r, c in my_stones:
        s ^= ((r + 1) * 73856093) ^ ((c + 1) * 19349663)
        s = ((s << 7) | (s >> 25)) & 0xFFFFFFFF

    for r, c in opp_stones:
        s ^= ((r + 1) * 83492791) ^ ((c + 1) * 2654435761)
        s = ((s << 11) | (s >> 21)) & 0xFFFFFFFF

    return s & 0xFFFFFFFF


def _jitter(seed, r, c):
    x = (seed ^ ((r + 1) * 0x45D9F3B) ^ ((c + 1) * 0x119DE1F3)) & 0xFFFFFFFF
    x = ((x ^ (x >> 16)) * 0x45D9F3B) & 0xFFFFFFFF
    x = ((x ^ (x >> 16)) * 0x45D9F3B) & 0xFFFFFFFF
    x = (x ^ (x >> 16)) & 0xFFFFFFFF
    return (x & 1023) / 2048.0
