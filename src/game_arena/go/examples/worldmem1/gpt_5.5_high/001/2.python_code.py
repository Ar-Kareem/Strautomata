
N = 19
EMPTY = 0
ME = 1
OPP = -1

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _board_key(board):
    chars = {EMPTY: ".", ME: "X", OPP: "O"}
    return tuple("".join(chars[v] for v in row) for row in board)


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

                for dr, dc in DIRS:
                    nr, nc = sr + dr, sc + dc
                    if not _inside(nr, nc):
                        continue
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

    return groups, gid


def _flood_group(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    libs = set()

    while stack:
        sr, sc = stack.pop()
        for dr, dc in DIRS:
            nr, nc = sr + dr, sc + dc
            if not _inside(nr, nc):
                continue
            v = board[nr][nc]
            if v == EMPTY:
                libs.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return len(seen), libs


def _legal_result(board, groups, gid, r, c, history=None):
    if not _inside(r, c) or board[r][c] != EMPTY:
        return None

    move = (r, c)
    captured = []
    captured_gids = []
    seen_opp = set()

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc) or board[nr][nc] != OPP:
            continue
        g = gid[nr][nc]
        if g in seen_opp:
            continue
        seen_opp.add(g)
        grp = groups[g]
        if len(grp["libs"]) == 1 and move in grp["libs"]:
            captured_gids.append(g)
            captured.extend(grp["stones"])

    new_board = [row[:] for row in board]
    new_board[r][c] = ME

    for sr, sc in captured:
        new_board[sr][sc] = EMPTY

    new_size, new_libs = _flood_group(new_board, r, c)
    if len(new_libs) == 0:
        return None

    key = None
    if history:
        key = _board_key(new_board)
        if key in history:
            return None

    return {
        "board": new_board,
        "captured_count": len(captured),
        "captured_gids": captured_gids,
        "new_size": new_size,
        "new_lib_count": len(new_libs),
        "key": key,
    }


def _eye_like(board, r, c, color):
    if board[r][c] != EMPTY:
        return False

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc) and board[nr][nc] != color:
            return False

    bad_diags = 0
    inside_diags = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            inside_diags += 1
            if board[nr][nc] != color:
                bad_diags += 1

    if inside_diags < 4:
        return bad_diags == 0
    return bad_diags <= 1


def _corner_index(r, c):
    if r <= 8 and c <= 8:
        return 0
    if r <= 8 and c >= 10:
        return 1
    if r >= 10 and c <= 8:
        return 2
    if r >= 10 and c >= 10:
        return 3
    return None


CORNER_HOSHI = {(3, 3), (3, 15), (15, 3), (15, 15)}
SIDE_HOSHI = {(3, 9), (9, 3), (9, 15), (15, 9)}
CENTER_POINT = {(9, 9)}

KOMOKU = set()
for rr, cc in ((2, 3), (3, 2)):
    KOMOKU.add((rr, cc))
    KOMOKU.add((rr, N - 1 - cc))
    KOMOKU.add((N - 1 - rr, cc))
    KOMOKU.add((N - 1 - rr, N - 1 - cc))

SAN_SAN = {(2, 2), (2, 16), (16, 2), (16, 16)}
ALL_OPENING_POINTS = CORNER_HOSHI | SIDE_HOSHI | CENTER_POINT | KOMOKU | SAN_SAN


def _score_move(r, c, board, groups, gid, res, my_stones, opp_stones,
                total, corner_own, corner_opp):
    move = (r, c)
    score = 0.0

    cap_count = res["captured_count"]
    cap_gids = set(res["captured_gids"])
    cap_max = 0
    for g in cap_gids:
        cap_max = max(cap_max, groups[g]["size"])

    adj_own = set()
    adj_opp = set()
    empty_adj = 0

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not _inside(nr, nc):
            continue
        v = board[nr][nc]
        if v == ME:
            adj_own.add(gid[nr][nc])
        elif v == OPP:
            adj_opp.add(gid[nr][nc])
        else:
            empty_adj += 1

    # Capturing opponent stones is usually urgent.
    if cap_count:
        score += 700.0 + 240.0 * cap_count + 120.0 * cap_max + 70.0 * len(cap_gids)

    # Save our groups that are in atari.
    save_gids = []
    for g in adj_own:
        grp = groups[g]
        if len(grp["libs"]) == 1 and move in grp["libs"]:
            save_gids.append(g)

    save_size = sum(groups[g]["size"] for g in save_gids)
    if save_size:
        score += 650.0 + 230.0 * save_size + 60.0 * len(save_gids)

    # Extend or strengthen weak friendly groups.
    for g in adj_own:
        grp = groups[g]
        if move not in grp["libs"]:
            continue
        libs = len(grp["libs"])
        sz = grp["size"]
        if libs == 2:
            score += 180.0 + 45.0 * min(sz, 12)
        elif libs == 3:
            score += 60.0 + 12.0 * min(sz, 12)
        elif libs == 4:
            score += 20.0 + 4.0 * min(sz, 8)

    # Attack opponent groups by reducing liberties, especially putting them in atari.
    threat_count = 0
    threat_size = 0
    for g in adj_opp:
        if g in cap_gids:
            continue
        grp = groups[g]
        if move not in grp["libs"]:
            continue
        libs = len(grp["libs"])
        sz = grp["size"]
        if libs == 2:
            threat_count += 1
            threat_size += sz
            score += 260.0 + 90.0 * min(sz, 12)
        elif libs == 3:
            score += 55.0 + 18.0 * min(sz, 10)
        elif libs == 4:
            score += 15.0 + 5.0 * min(sz, 8)

    tactical = cap_count > 0 or save_size > 0 or threat_count > 0

    # Connecting friendly groups has lasting value.
    if len(adj_own) >= 2:
        connected_size = sum(min(groups[g]["size"], 10) for g in adj_own)
        weak_bonus = sum(1 for g in adj_own if len(groups[g]["libs"]) <= 3)
        score += 100.0 * (len(adj_own) - 1) + 18.0 * connected_size + 45.0 * weak_bonus
    elif len(adj_own) == 1:
        only = next(iter(adj_own))
        score += 8.0 + min(groups[only]["size"], 10)

    # Cutting or separating multiple opposing groups.
    if len(adj_opp) >= 2:
        cut_size = sum(min(groups[g]["size"], 8) for g in adj_opp)
        score += 45.0 * (len(adj_opp) - 1) + 10.0 * cut_size

    # Liberties of the resulting friendly group.
    new_libs = res["new_lib_count"]
    new_size = res["new_size"]
    score += 10.0 * min(new_libs, 10)

    if new_libs == 1:
        if cap_count == 0 and save_size == 0:
            score -= 1200.0 + 90.0 * min(new_size, 15)
        else:
            score -= 550.0 + 70.0 * min(new_size, 15)
            if cap_count <= 1 and new_size <= 2:
                score -= 300.0
    elif new_libs == 2:
        if not tactical:
            score -= 90.0
        else:
            score -= 25.0
    elif new_libs >= 4:
        score += 22.0

    # Basic local shape.
    diag_own = 0
    diag_opp = 0
    for dr, dc in DIAGS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            if board[nr][nc] == ME:
                diag_own += 1
            elif board[nr][nc] == OPP:
                diag_opp += 1

    score += 8.0 * len(adj_own) + 5.0 * diag_own + 6.0 * len(adj_opp)
    if diag_own and adj_opp:
        score += 12.0 * min(diag_own, len(adj_opp))

    phase = max(0.0, min(1.0, (90.0 - total) / 90.0))
    line = min(r, c, N - 1 - r, N - 1 - c) + 1

    # Avoid low-value edge plays unless tactical.
    if not tactical:
        if line == 1:
            score -= 90.0 if total < 280 else 25.0
        elif line == 2 and total < 250:
            score -= 28.0

    # Opening theory: corners, 4th line, 3-4, side hoshi, spacing.
    nearest_own = 99
    nearest_opp = 99
    own_inf = 0
    opp_inf = 0

    for sr, sc in my_stones:
        d = abs(sr - r) + abs(sc - c)
        if d < nearest_own:
            nearest_own = d
        if d <= 8:
            own_inf += 9 - d

    for sr, sc in opp_stones:
        d = abs(sr - r) + abs(sc - c)
        if d < nearest_opp:
            nearest_opp = d
        if d <= 8:
            opp_inf += 9 - d

    if phase > 0.0:
        os = 0.0

        if line == 4:
            os += 38.0
        elif line == 3:
            os += 30.0
        elif line == 5:
            os += 15.0
        elif line == 2:
            os -= 50.0
        elif line == 1:
            os -= 130.0

        if move in CORNER_HOSHI:
            os += 190.0
        elif move in KOMOKU:
            os += 155.0
        elif move in SAN_SAN:
            os += 45.0
        elif move in SIDE_HOSHI:
            os += 90.0
        elif move in CENTER_POINT:
            os += 35.0

        idx = _corner_index(r, c)
        if idx is not None:
            if not corner_own[idx]:
                os += 45.0
            if not corner_own[idx] and not corner_opp[idx]:
                os += 30.0
            if corner_opp[idx] and not corner_own[idx] and line in (3, 4):
                os += 25.0
            if corner_own[idx] and move in ALL_OPENING_POINTS:
                os -= 100.0

        if total > 0 and not tactical:
            nall = min(nearest_own, nearest_opp)
            if nall < 3:
                os -= 30.0 * (3 - nall)
            elif nall <= 14:
                os += 5.0 * nall
            else:
                os += 70.0

        score += os * phase

    # Middle-game influence and proximity.
    if total > 0:
        score += (1.15 * own_inf + 0.95 * opp_inf) * (0.35 + 0.65 * (1.0 - phase))

    if total > 25:
        if 2 <= nearest_own <= 5:
            score += 22.0
        elif nearest_own == 1:
            score += 8.0
        elif nearest_own > 11 and total > 100:
            score -= 30.0

        if 2 <= nearest_opp <= 6:
            score += 20.0
        elif nearest_opp == 1 and not tactical and phase > 0.2:
            score -= 20.0

    # Avoid filling our own eyes or very safe territory unless necessary.
    if not tactical:
        if _eye_like(board, r, c, ME):
            score -= 950.0
        if total > 100 and nearest_opp > 8 and nearest_own <= 4:
            score -= 75.0
        if total > 160 and nearest_own > 9 and nearest_opp <= 4 and new_libs <= 2:
            score -= 130.0

    # Prefer not to start unsupported contact fights early.
    if len(adj_own) == 0 and len(adj_opp) > 0 and not tactical and total < 90:
        score -= 35.0 * len(adj_opp)

    if len(adj_own) == 0 and len(adj_opp) == 0 and total > 130:
        score -= 35.0

    # Tiny deterministic tie-breaker.
    score += (((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ (total * 83492791)) % 997 / 100000.0

    return score


def policy(me, opponent, memory):
    if not isinstance(memory, dict):
        memory = {}

    # Reset stale memory if a new game appears to have started.
    current_total_input = len(me) + len(opponent)
    if current_total_input <= 1 and memory.get("last_total", 0) > 1:
        memory = {}

    board = [[EMPTY] * N for _ in range(N)]

    for r, c in opponent:
        rr, cc = r - 1, c - 1
        if _inside(rr, cc):
            board[rr][cc] = OPP

    for r, c in me:
        rr, cc = r - 1, c - 1
        if _inside(rr, cc):
            board[rr][cc] = ME

    my_stones = []
    opp_stones = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == ME:
                my_stones.append((r, c))
            elif board[r][c] == OPP:
                opp_stones.append((r, c))

    total = len(my_stones) + len(opp_stones)

    hist_obj = memory.get("history", set())
    try:
        history = set(hist_obj)
    except Exception:
        history = set()

    current_key = _board_key(board)
    history.add(current_key)

    groups, gid = _analyze(board)

    corner_own = [False, False, False, False]
    corner_opp = [False, False, False, False]

    for r, c in my_stones:
        idx = _corner_index(r, c)
        if idx is not None:
            corner_own[idx] = True

    for r, c in opp_stones:
        idx = _corner_index(r, c)
        if idx is not None:
            corner_opp[idx] = True

    best_move = None
    best_res = None
    best_score = -10 ** 18

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue

            res = _legal_result(board, groups, gid, r, c, history)
            if res is None:
                continue

            sc = _score_move(
                r, c, board, groups, gid, res,
                my_stones, opp_stones, total,
                corner_own, corner_opp
            )

            if sc > best_score:
                best_score = sc
                best_move = (r, c)
                best_res = res

    # If there is no legal non-ko move, pass.
    if best_move is None:
        memory["history"] = history
        memory["last_total"] = total
        memory["calls"] = memory.get("calls", 0) + 1
        return (0, 0), memory

    # Late game: avoid playing moves that are probably self-damaging territory fills.
    if (
        (total > 180 and best_score < -650.0) or
        (total > 260 and best_score < -250.0) or
        (total > 320 and best_score < 0.0)
    ):
        memory["history"] = history
        memory["last_total"] = total
        memory["calls"] = memory.get("calls", 0) + 1
        return (0, 0), memory

    key = best_res.get("key")
    if key is None:
        key = _board_key(best_res["board"])
    history.add(key)

    memory["history"] = history
    memory["last_total"] = total
    memory["calls"] = memory.get("calls", 0) + 1

    return (best_move[0] + 1, best_move[1] + 1), memory
