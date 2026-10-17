
BOARD_SIZE = 19
ME_COLOR = 1
OPP_COLOR = -1

# Precompute board geometry.
NEIGHBORS = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
DIAGONALS = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
EDGE_DISTANCE = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        n = []
        if r > 0:
            n.append((r - 1, c))
        if r + 1 < BOARD_SIZE:
            n.append((r + 1, c))
        if c > 0:
            n.append((r, c - 1))
        if c + 1 < BOARD_SIZE:
            n.append((r, c + 1))
        NEIGHBORS[r][c] = tuple(n)

        d = []
        if r > 0 and c > 0:
            d.append((r - 1, c - 1))
        if r > 0 and c + 1 < BOARD_SIZE:
            d.append((r - 1, c + 1))
        if r + 1 < BOARD_SIZE and c > 0:
            d.append((r + 1, c - 1))
        if r + 1 < BOARD_SIZE and c + 1 < BOARD_SIZE:
            d.append((r + 1, c + 1))
        DIAGONALS[r][c] = tuple(d)

        EDGE_DISTANCE[r][c] = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)

# Opening points, 0-based.
CORNER_44 = {(3, 3), (3, 15), (15, 3), (15, 15)}
CORNER_34 = {
    (2, 3), (3, 2),
    (2, 15), (3, 16),
    (15, 2), (16, 3),
    (15, 16), (16, 15),
}
SIDE_STARS = {(3, 9), (9, 3), (9, 15), (15, 9)}
CENTER_STAR = (9, 9)


def board_hash(board):
    """Compact board serialization for ko/history checking."""
    out = bytearray(BOARD_SIZE * BOARD_SIZE)
    k = 0
    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            v = row[c]
            out[k] = 1 if v == ME_COLOR else 2 if v == OPP_COLOR else 0
            k += 1
    return bytes(out)


def get_group_and_liberties(board, r, c):
    """Return (stones_list, liberties_set) for the group at (r,c)."""
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    liberties = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in NEIGHBORS[x][y]:
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))

    return stones, liberties


def analyze_groups(board):
    """Find all groups and a stone->group-id map."""
    visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    gid_at = [[-1 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    groups = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = board[r][c]
            if color == 0 or visited[r][c]:
                continue

            stack = [(r, c)]
            visited[r][c] = True
            stones = []
            liberties = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in NEIGHBORS[x][y]:
                    v = board[nx][ny]
                    if v == 0:
                        liberties.add((nx, ny))
                    elif v == color and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))

            gid = len(groups)
            for x, y in stones:
                gid_at[x][y] = gid
            groups.append({
                "color": color,
                "stones": stones,
                "libs": liberties,
            })

    return groups, gid_at


def is_eye_like(board, r, c, color):
    """Heuristic eye check: avoid filling our own real eyes."""
    if board[r][c] != 0:
        return False

    opp = -color

    # All orthogonal neighbors must be friendly (edges are implicitly okay).
    for nx, ny in NEIGHBORS[r][c]:
        if board[nx][ny] != color:
            return False

    # Diagonal false-eye test.
    bad_diagonals = 0
    total_diagonals = 0
    for nx, ny in DIAGONALS[r][c]:
        total_diagonals += 1
        if board[nx][ny] == opp:
            bad_diagonals += 1

    # Interior eye: at most one bad diagonal.
    # Edge/corner eye: no bad diagonals.
    if total_diagonals == 4:
        return bad_diagonals <= 1
    return bad_diagonals == 0


def play_move(board, r, c, color, forbidden_hashes=None):
    """
    Simulate a move.
    Returns (legal, new_board, captured_count, info_dict).
    """
    if board[r][c] != 0:
        return False, None, 0, None

    opp = -color
    new_board = [row[:] for row in board]
    new_board[r][c] = color

    # Determine all adjacent opponent groups with 0 liberties BEFORE removing any.
    to_capture = []
    checked = set()
    for nx, ny in NEIGHBORS[r][c]:
        if new_board[nx][ny] == opp and (nx, ny) not in checked:
            stones, libs = get_group_and_liberties(new_board, nx, ny)
            checked.update(stones)
            if len(libs) == 0:
                to_capture.append(stones)

    captured = 0
    for stones in to_capture:
        captured += len(stones)
        for sx, sy in stones:
            new_board[sx][sy] = 0

    my_stones, my_libs = get_group_and_liberties(new_board, r, c)
    if len(my_libs) == 0:
        return False, None, 0, None  # suicide

    h = board_hash(new_board)
    if forbidden_hashes is not None and h in forbidden_hashes:
        return False, None, 0, None  # ko / repetition avoidance

    info = {
        "group_stones": my_stones,
        "group_libs": my_libs,
        "hash": h,
    }
    return True, new_board, captured, info


def opening_bonus(r, c, total_stones, all_stones):
    """Opening preference for good global points."""
    pos = (r, c)
    bonus = 0.0

    if total_stones < 10:
        if pos in CORNER_44:
            bonus += 260.0
        elif pos in CORNER_34:
            bonus += 200.0
        elif pos in SIDE_STARS:
            bonus += 100.0
        elif pos == CENTER_STAR:
            bonus += 40.0

        if all_stones:
            md = min(abs(r - sr) + abs(c - sc) for sr, sc in all_stones)
            bonus += 8.0 * min(md, 10)
            if md <= 2:
                bonus -= 80.0

    elif total_stones < 30:
        if pos in CORNER_44:
            bonus += 70.0
        elif pos in CORNER_34:
            bonus += 50.0
        elif pos in SIDE_STARS:
            bonus += 25.0

        if all_stones:
            md = min(abs(r - sr) + abs(c - sc) for sr, sc in all_stones)
            bonus += 2.0 * min(md, 8)

    return bonus


def local_density_score(board, r, c):
    """Prefer moves near existing activity, but with short radius only."""
    score = 0.0
    for dr in (-2, -1, 0, 1, 2):
        nr = r + dr
        if nr < 0 or nr >= BOARD_SIZE:
            continue
        for dc in (-2, -1, 0, 1, 2):
            if dr == 0 and dc == 0:
                continue
            nc = c + dc
            if nc < 0 or nc >= BOARD_SIZE:
                continue

            dist = abs(dr) + abs(dc)
            if dist > 3:
                continue

            v = board[nr][nc]
            if v == ME_COLOR:
                if dist == 1:
                    score += 6.0
                elif dist == 2:
                    score += 3.0
                else:
                    score += 1.0
            elif v == OPP_COLOR:
                if dist == 1:
                    score += 5.0
                elif dist == 2:
                    score += 2.0
                else:
                    score += 1.0
    return score


def stones_from_board(board):
    my_stones = []
    opp_stones = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = board[r][c]
            if v == ME_COLOR:
                my_stones.append((r, c))
            elif v == OPP_COLOR:
                opp_stones.append((r, c))
    return my_stones, opp_stones


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    # Build current board, deduplicating any accidental repeated coordinates.
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    my_stones = []
    opp_stones = []

    for rr, cc in me:
        r = rr - 1
        c = cc - 1
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
            board[r][c] = ME_COLOR
            my_stones.append((r, c))

    for rr, cc in opponent:
        r = rr - 1
        c = cc - 1
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
            board[r][c] = OPP_COLOR
            opp_stones.append((r, c))

    total_stones = len(my_stones) + len(opp_stones)
    all_stones = my_stones + opp_stones

    # History for ko / repetition avoidance.
    raw_history = memory.get("history", [])
    if isinstance(raw_history, list):
        history = raw_history[:]
    else:
        try:
            history = list(raw_history)
        except Exception:
            history = []

    try:
        history_set = set(history)
    except Exception:
        history = []
        history_set = set()

    current_h = board_hash(board)
    if current_h not in history_set:
        history.append(current_h)
        history_set.add(current_h)

    # Infer last opponent move (if memory is available) for a mild local preference.
    last_opp_move = None
    prev_opp_raw = memory.get("opp_after")
    if prev_opp_raw is not None:
        try:
            prev_opp_set = set(tuple(p) for p in prev_opp_raw)
            added = [p for p in opp_stones if p not in prev_opp_set]
            if len(added) == 1:
                last_opp_move = added[0]
        except Exception:
            last_opp_move = None

    # Analyze current groups.
    groups, gid_at = analyze_groups(board)

    save_map = {}
    pressure_map = {}
    defend_map = {}

    for g in groups:
        color = g["color"]
        size = len(g["stones"])
        libs = g["libs"]
        lib_count = len(libs)

        if lib_count == 1:
            lib = next(iter(libs))
            if color == ME_COLOR:
                save_map[lib] = save_map.get(lib, 0) + size
        elif lib_count == 2:
            if color == ME_COLOR:
                for lib in libs:
                    defend_map[lib] = defend_map.get(lib, 0) + size
            else:
                for lib in libs:
                    pressure_map[lib] = pressure_map.get(lib, 0) + size

    best_move = None
    best_score = float("-inf")
    best_board = None
    best_hash = None

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue

            legal, new_board, captured, info = play_move(board, r, c, ME_COLOR, history_set)
            if not legal:
                continue

            adj_my = 0
            adj_opp = 0
            adj_empty = 0
            adj_my_ids = set()
            adj_opp_ids = set()

            for nx, ny in NEIGHBORS[r][c]:
                v = board[nx][ny]
                if v == ME_COLOR:
                    adj_my += 1
                    adj_my_ids.add(gid_at[nx][ny])
                elif v == OPP_COLOR:
                    adj_opp += 1
                    adj_opp_ids.add(gid_at[nx][ny])
                else:
                    adj_empty += 1

            new_group_libs = len(info["group_libs"])
            new_group_size = len(info["group_stones"])
            saved = save_map.get((r, c), 0)

            score = 0.0

            # Tactical priorities.
            score += 1400.0 * captured

            if saved:
                if new_group_libs > 1 or captured > 0:
                    score += 850.0 * saved
                else:
                    score += 40.0 * saved

            score += 55.0 * pressure_map.get((r, c), 0)
            score += 35.0 * defend_map.get((r, c), 0)

            # Shape and connectivity.
            score += 60.0 * max(0, len(adj_my_ids) - 1)
            score += 30.0 * max(0, len(adj_opp_ids) - 1)
            score += 14.0 * adj_my + 10.0 * adj_opp + 4.0 * adj_empty
            score += 32.0 * min(new_group_libs, 5)
            score += 4.0 * min(new_group_size, 15)

            # Avoid self-atari unless it is tactical.
            if new_group_libs == 1:
                if captured == 0 and saved == 0:
                    score -= 950.0
                else:
                    score -= 250.0
            elif new_group_libs == 2:
                score -= 80.0

            # Avoid filling our own eyes.
            if is_eye_like(board, r, c, ME_COLOR):
                score -= 280.0
                if captured or saved:
                    score += 250.0

            # Avoid isolated moves after opening.
            if adj_my + adj_opp == 0:
                if total_stones >= 8:
                    score -= 120.0
                else:
                    score -= 20.0

            # Avoid pointless early contact fights.
            if total_stones < 8 and adj_opp > 0 and adj_my == 0 and captured == 0 and saved == 0:
                score -= 60.0

            # Post-move pressure: do we put nearby enemy groups into atari?
            seen_enemy = set()
            for nx, ny in NEIGHBORS[r][c]:
                if new_board[nx][ny] == OPP_COLOR and (nx, ny) not in seen_enemy:
                    stones, libs = get_group_and_liberties(new_board, nx, ny)
                    seen_enemy.update(stones)
                    sz = len(stones)
                    ll = len(libs)
                    if ll == 1:
                        score += 170.0 + 30.0 * sz
                    elif ll == 2:
                        score += 45.0 + 10.0 * sz

            # Diagonal shape.
            diag_my = 0
            diag_opp = 0
            for nx, ny in DIAGONALS[r][c]:
                v = board[nx][ny]
                if v == ME_COLOR:
                    diag_my += 1
                elif v == OPP_COLOR:
                    diag_opp += 1
            score += 4.0 * diag_my + 2.0 * diag_opp

            # Line preference.
            d = EDGE_DISTANCE[r][c]
            if total_stones < 20:
                if d == 0:
                    score -= 120.0
                elif d == 1:
                    score -= 25.0
                elif d in (2, 3):
                    score += 30.0
            else:
                if d == 0:
                    score -= 40.0
                elif d in (2, 3):
                    score += 8.0

            # Opening and locality.
            score += opening_bonus(r, c, total_stones, all_stones)
            score += local_density_score(board, r, c)

            # Mild local response to the opponent's latest move.
            if last_opp_move is not None:
                dist = abs(r - last_opp_move[0]) + abs(c - last_opp_move[1])
                if dist <= 2:
                    score += 15.0 * (3 - dist)

            if (
                best_move is None
                or score > best_score + 1e-9
                or (abs(score - best_score) <= 1e-9 and (r, c) < best_move)
            ):
                best_move = (r, c)
                best_score = score
                best_board = new_board
                best_hash = info["hash"]

    # Safe pass policy: only if no legal move, or extremely poor late-game options.
    if best_move is None or best_score < -700.0 or (total_stones > 320 and best_score < 25.0):
        new_memory = {
            "history": history,
            "me_after": list(my_stones),
            "opp_after": list(opp_stones),
        }
        return (0, 0), new_memory

    if best_hash not in history_set:
        history.append(best_hash)
        history_set.add(best_hash)

    my_after, opp_after = stones_from_board(best_board)
    new_memory = {
        "history": history,
        "me_after": my_after,
        "opp_after": opp_after,
    }
    return (best_move[0] + 1, best_move[1] + 1), new_memory
