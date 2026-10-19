
N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def on_board(r, c):
    return 0 <= r < N and 0 <= c < N


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def build_board(me, opponent):
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2
    return board


def board_key(board):
    return bytes([board[r][c] for r in range(N) for c in range(N)])


def collect_group(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    liberties = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))

    return stones, liberties


def all_groups(board, color):
    gid = [[-1] * N for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == color and gid[r][c] < 0:
                stones, libs = collect_group(board, r, c)
                idx = len(groups)
                for sr, sc in stones:
                    gid[sr][sc] = idx
                groups.append({
                    "stones": stones,
                    "libs": libs,
                    "size": len(stones),
                })

    return groups, gid


def simulate_move(board, r, c, last_after=None, forbidden=None):
    if board[r][c] != 0:
        return False, None, 0

    nb = [row[:] for row in board]
    nb[r][c] = 1
    captured = 0

    # Remove opponent groups with no liberties.
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == 2:
            stones, libs = collect_group(nb, nr, nc)
            if not libs:
                for sr, sc in stones:
                    nb[sr][sc] = 0
                captured += len(stones)

    # Suicide check.
    _, my_libs = collect_group(nb, r, c)
    if not my_libs:
        return False, None, 0

    # Ko / superko-style avoidance.
    if last_after is not None or forbidden:
        k = board_key(nb)
        if last_after is not None and k == last_after:
            return False, None, 0
        if forbidden is not None and k in forbidden:
            return False, None, 0

    return True, nb, captured


def is_eye_point(board, r, c, color):
    if board[r][c] != 0:
        return False

    for nr, nc in neighbors(r, c):
        if board[nr][nc] != color:
            return False

    bad_diags = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if on_board(nr, nc) and board[nr][nc] != color:
            bad_diags += 1

    # Edge and corner eyes need stricter diagonals.
    if r == 0 or r == N - 1 or c == 0 or c == N - 1:
        return bad_diags == 0
    return bad_diags <= 1


def positional_score(r, c, occupied):
    r1, c1 = r + 1, c + 1
    line = min(r1, N + 1 - r1, c1, N + 1 - c1)

    if line == 1:
        base = -18
    elif line == 2:
        base = -2
    elif line == 3:
        base = 8
    elif line == 4:
        base = 10
    elif line == 5:
        base = 6
    else:
        base = 2 if line <= 8 else 0

    # Hoshi/star points and good corner points.
    if r1 in (4, 10, 16) and c1 in (4, 10, 16):
        base += 5
    if r1 in (4, 16) and c1 in (4, 16):
        base += 8
    if r1 in (3, 17) and c1 in (3, 17):
        base += 3
    if r1 == 10 and c1 == 10:
        base += 4

    if occupied < 30:
        weight = 2.4
    elif occupied < 80:
        weight = 1.5
    elif occupied < 160:
        weight = 0.8
    else:
        weight = 0.25

    return base * weight


def build_corner_data(board):
    data = []
    for top in (True, False):
        for left in (True, False):
            rows = range(0, 6) if top else range(N - 6, N)
            cols = range(0, 6) if left else range(N - 6, N)
            my_count = 0
            opp_count = 0
            opp_stones = []

            for r in rows:
                for c in cols:
                    if board[r][c] == 1:
                        my_count += 1
                    elif board[r][c] == 2:
                        opp_count += 1
                        opp_stones.append((r, c))

            data.append((top, left, my_count, opp_count, opp_stones))
    return data


def opening_bonus(r, c, occupied, corner_data):
    if occupied > 80:
        return 0.0

    bonus = 0.0
    for top, left, my_count, opp_count, opp_stones in corner_data:
        # Local 1-indexed coordinates measured from this corner.
        lr = r + 1 if top else N - r
        lc = c + 1 if left else N - c

        if lr > 6 or lc > 6:
            continue

        ideal = lr in (3, 4) and lc in (3, 4)
        okay = lr in (3, 4, 5) and lc in (3, 4, 5)

        if my_count == 0 and opp_count == 0:
            if ideal:
                bonus += 42
            elif okay:
                bonus += 18

        elif my_count == 0 and opp_count > 0:
            if opp_stones:
                md = min(abs(r - rr) + abs(c - cc) for rr, cc in opp_stones)
            else:
                md = 99
            if okay and 3 <= md <= 6:
                bonus += 28
            if lr == 3 and lc == 3 and occupied > 20:
                bonus += 15

        elif my_count > 0 and opp_count == 0:
            # Avoid over-concentrating in an already-secured corner early.
            if occupied < 35:
                bonus -= 20 if max(lr, lc) <= 5 else 5

        else:
            if okay:
                bonus += 8

    return bonus


def local_influence_score(board, r, c, occupied):
    own = 0
    opp = 0
    nearest = 99

    for dr in range(-4, 5):
        for dc in range(-4, 5):
            d = abs(dr) + abs(dc)
            if d == 0 or d > 4:
                continue
            nr, nc = r + dr, c + dc
            if not on_board(nr, nc):
                continue

            v = board[nr][nc]
            if v:
                nearest = min(nearest, d)
                w = 5 - d
                if v == 1:
                    own += w
                else:
                    opp += w

    if occupied < 30:
        s = 0.4 * own + 0.8 * opp
        if own > 14 and opp == 0:
            s -= 0.5 * own
    elif occupied < 120:
        s = 0.8 * own + 1.0 * opp
    else:
        s = 1.1 * own + 1.2 * opp

    if occupied > 35 and nearest > 4:
        s -= 18

    return s


def score_move(board, r, c, new_board, captured, ctx):
    occupied = ctx["occupied"]
    my_groups = ctx["my_groups"]
    opp_groups = ctx["opp_groups"]
    my_id = ctx["my_id"]
    opp_id = ctx["opp_id"]
    own_atari = ctx["own_atari"]
    corner_data = ctx["corner_data"]

    score = 0.0
    score += positional_score(r, c, occupied)
    score += opening_bonus(r, c, occupied, corner_data)
    score += local_influence_score(board, r, c, occupied)

    adj_own = set()
    adj_opp = set()
    empty_adj = 0

    for nr, nc in neighbors(r, c):
        v = board[nr][nc]
        if v == 0:
            empty_adj += 1
        elif v == 1:
            gid = my_id[nr][nc]
            if gid >= 0:
                adj_own.add(gid)
        elif v == 2:
            gid = opp_id[nr][nc]
            if gid >= 0:
                adj_opp.add(gid)

    new_stones, new_libs = collect_group(new_board, r, c)
    new_lib_count = len(new_libs)
    new_size = len(new_stones)

    # Captures are very valuable, especially multi-stone captures.
    if captured:
        score += captured * 105 + captured * captured * 10

    # Attack adjacent opponent groups.
    weak_adjacent_opponents = 0
    for gid in adj_opp:
        g = opp_groups[gid]
        libs = len(g["libs"])
        size = g["size"]

        if libs == 1:
            score += 65 * size
        elif libs == 2:
            score += 34 * size + 18
            weak_adjacent_opponents += 1
        elif libs == 3:
            score += 8 * min(size, 6)

    # Cutting multiple opposing groups is usually good.
    if len(adj_opp) >= 2:
        score += 16 * (len(adj_opp) - 1) + 8 * weak_adjacent_opponents

    # Connect/save friendly groups.
    touched_atari_save = False
    for gid in adj_own:
        g = my_groups[gid]
        libs = len(g["libs"])
        size = g["size"]

        if libs == 1:
            score += 105 * size + 12 * new_lib_count
            touched_atari_save = True
        elif libs == 2:
            score += 18 * size + 5 * new_lib_count
        elif libs == 3:
            score += 5 * min(size, 6)

    if adj_own:
        score += 8 * len(adj_own)
        if len(adj_own) >= 2:
            score += 20 * (len(adj_own) - 1)
    else:
        if occupied > 45:
            score -= 4

    score += 4 * empty_adj

    # Global urgency: do not ignore friendly groups in atari unless compensation is large.
    for g in own_atari:
        size = g["size"]
        rep = g["stones"][0]
        if new_board[rep[0]][rep[1]] != 1:
            continue

        _, libs2 = collect_group(new_board, rep[0], rep[1])
        if len(libs2) <= 1:
            score -= 85 * size + 30
        else:
            if (r, c) in g["libs"] or captured > 0:
                score += 75 * size + 10 * min(len(libs2), 6)

    # Liberty safety.
    score += 7 * min(new_lib_count, 6)

    if new_lib_count == 1:
        score -= 130
        if captured <= 1:
            score -= 130
        if new_size <= 3:
            score -= 30
    elif new_lib_count == 2:
        score -= 18
        if captured == 0 and not touched_atari_save and new_size <= 3:
            score -= 14
    elif new_lib_count >= 4:
        score += 10

    if adj_opp and not adj_own and new_lib_count <= 2 and captured == 0:
        score -= 25

    # Avoid filling solid eyes unless tactically necessary.
    if is_eye_point(board, r, c, 1) and captured == 0 and not touched_atari_save:
        score -= 135

    if is_eye_point(board, r, c, 2) and captured == 0:
        score -= 55

    # First line is usually small unless it captures/saves.
    line = min(r + 1, N - r, c + 1, N - c)
    if line == 1:
        if captured == 0 and not touched_atari_save:
            score -= 35
        else:
            score -= 5
    elif line == 2 and occupied < 180 and captured == 0 and not touched_atari_save:
        score -= 6

    # Deterministic tiny tie-breaker.
    score += (((r + 1) * 13 + (c + 1) * 7 + occupied * 3) % 23) * 0.001

    return score


def policy(me, opponent, memory):
    if not isinstance(memory, dict):
        memory = {}

    board = build_board(me, opponent)
    occupied = len(me) + len(opponent)

    # Detect a likely new game or large reset.
    prev_occ = memory.get("_occ")
    if occupied <= 1 or (isinstance(prev_occ, int) and occupied < prev_occ - 10):
        memory = {}

    current_key = board_key(board)

    last_after = memory.get("last_after")
    if not isinstance(last_after, (bytes, bytearray)) or len(last_after) != N * N:
        last_after = None
    elif isinstance(last_after, bytearray):
        last_after = bytes(last_after)

    hist_obj = memory.get("history")
    if isinstance(hist_obj, set):
        history = hist_obj
    elif isinstance(hist_obj, (list, tuple)):
        try:
            history = set(hist_obj)
        except Exception:
            history = set()
    else:
        history = set()

    history.add(current_key)

    my_groups, my_id = all_groups(board, 1)
    opp_groups, opp_id = all_groups(board, 2)
    own_atari = [g for g in my_groups if len(g["libs"]) == 1]
    corner_data = build_corner_data(board)

    ctx = {
        "occupied": occupied,
        "my_groups": my_groups,
        "opp_groups": opp_groups,
        "my_id": my_id,
        "opp_id": opp_id,
        "own_atari": own_atari,
        "corner_data": corner_data,
    }

    best_score = -10**18
    best_move = None
    best_board = None
    best_captured = 0

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            legal, nb, captured = simulate_move(
                board,
                r,
                c,
                last_after=last_after,
                forbidden=history,
            )
            if not legal:
                continue

            sc = score_move(board, r, c, nb, captured, ctx)

            if sc > best_score:
                best_score = sc
                best_move = (r, c)
                best_board = nb
                best_captured = captured

    # No legal board move: pass.
    if best_move is None:
        memory["last_after"] = current_key
        memory["history"] = history
        memory["_occ"] = occupied
        return (0, 0), memory

    # In very late hopeless/self-damaging positions, passing is better than
    # filling solid eyes. Do not pass lightly when friendly groups are in atari.
    if (
        (occupied > 320 and best_score < 5)
        or (occupied > 220 and best_score < -90 and not own_atari)
        or (best_score < -160 and not own_atari)
    ):
        memory["last_after"] = current_key
        memory["history"] = history
        memory["_occ"] = occupied
        return (0, 0), memory

    br, bc = best_move
    after_key = board_key(best_board)
    history.add(after_key)

    memory["last_after"] = after_key
    memory["history"] = history
    memory["_occ"] = occupied + 1 - best_captured

    return (br + 1, bc + 1), memory
