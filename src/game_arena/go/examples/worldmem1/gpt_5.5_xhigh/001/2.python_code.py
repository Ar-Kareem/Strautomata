
N = 19
NN = N * N

# ---------- Board geometry precomputation ----------

NEIGHBORS = []
DIAGONALS = []
LINE = []

for r in range(N):
    for c in range(N):
        ns = []
        if r > 0:
            ns.append((r - 1) * N + c)
        if r + 1 < N:
            ns.append((r + 1) * N + c)
        if c > 0:
            ns.append(r * N + c - 1)
        if c + 1 < N:
            ns.append(r * N + c + 1)
        NEIGHBORS.append(tuple(ns))

        ds = []
        for dr in (-1, 1):
            for dc in (-1, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    ds.append(rr * N + cc)
        DIAGONALS.append(tuple(ds))

        LINE.append(min(r, c, N - 1 - r, N - 1 - c) + 1)

LOCAL = []
for r in range(N):
    for c in range(N):
        pts = []
        for dr in range(-4, 5):
            for dc in range(-4, 5):
                d = abs(dr) + abs(dc)
                if d == 0 or d > 4:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    pts.append((rr * N + cc, d))
        LOCAL.append(tuple(pts))

CORNERS = ((0, 0), (0, N - 1), (N - 1, 0), (N - 1, N - 1))
CORNER_REGIONS = []
for cr, cc0 in CORNERS:
    rows = range(0, 6) if cr == 0 else range(N - 6, N)
    cols = range(0, 6) if cc0 == 0 else range(N - 6, N)
    pts = []
    for rr in rows:
        for col in cols:
            pts.append(rr * N + col)
    CORNER_REGIONS.append(tuple(pts))


# ---------- Basic board utilities ----------

def _build_board(me, opponent):
    board = [0] * NN
    for stone in me:
        try:
            r, c = stone
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 1

    for stone in opponent:
        try:
            r, c = stone
        except Exception:
            continue
        if 1 <= r <= N and 1 <= c <= N:
            idx = (r - 1) * N + (c - 1)
            if board[idx] == 0:
                board[idx] = -1
    return board


def _analyze_groups(board):
    gid = [-1] * NN
    groups = []

    for i, v in enumerate(board):
        if v != 0 and gid[i] == -1:
            gidx = len(groups)
            gid[i] = gidx
            stack = [i]
            stones = []
            libs = set()

            while stack:
                x = stack.pop()
                stones.append(x)
                for nb in NEIGHBORS[x]:
                    bv = board[nb]
                    if bv == 0:
                        libs.add(nb)
                    elif bv == v and gid[nb] == -1:
                        gid[nb] = gidx
                        stack.append(nb)

            groups.append({
                "color": v,
                "stones": tuple(stones),
                "libs": libs,
                "size": len(stones),
            })

    return groups, gid


def _analyze_regions(board):
    owner = [0] * NN
    size = [0] * NN
    seen = [False] * NN

    for i, v in enumerate(board):
        if v == 0 and not seen[i]:
            stack = [i]
            seen[i] = True
            pts = []
            touch_me = False
            touch_opp = False

            while stack:
                x = stack.pop()
                pts.append(x)
                for nb in NEIGHBORS[x]:
                    bv = board[nb]
                    if bv == 0:
                        if not seen[nb]:
                            seen[nb] = True
                            stack.append(nb)
                    elif bv == 1:
                        touch_me = True
                    else:
                        touch_opp = True

            if touch_me and not touch_opp:
                own = 1
            elif touch_opp and not touch_me:
                own = -1
            else:
                own = 0

            ln = len(pts)
            for p in pts:
                owner[p] = own
                size[p] = ln

    return owner, size


def _area_score(board):
    score = 0
    for v in board:
        if v == 1:
            score += 1
        elif v == -1:
            score -= 1

    seen = [False] * NN
    for i, v in enumerate(board):
        if v == 0 and not seen[i]:
            stack = [i]
            seen[i] = True
            count = 0
            touch_me = False
            touch_opp = False

            while stack:
                x = stack.pop()
                count += 1
                for nb in NEIGHBORS[x]:
                    bv = board[nb]
                    if bv == 0:
                        if not seen[nb]:
                            seen[nb] = True
                            stack.append(nb)
                    elif bv == 1:
                        touch_me = True
                    else:
                        touch_opp = True

            if touch_me and not touch_opp:
                score += count
            elif touch_opp and not touch_me:
                score -= count

    return score


def _is_eye(board, p, color):
    for nb in NEIGHBORS[p]:
        if board[nb] != color:
            return False

    r, c = divmod(p, N)
    bad_diag = 0
    off = 0
    for dr in (-1, 1):
        for dc in (-1, 1):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < N and 0 <= cc < N):
                off += 1
            elif board[rr * N + cc] == -color:
                bad_diag += 1

    if off:
        return bad_diag == 0
    return bad_diag <= 1


# ---------- Move simulation / legality ----------

def _move_features(p, board, groups, gid):
    if board[p] != 0:
        return None

    friend = set()
    enemy = set()
    adj_empty = []
    adj_own_stones = 0
    adj_opp_stones = 0

    for nb in NEIGHBORS[p]:
        v = board[nb]
        if v == 1:
            friend.add(gid[nb])
            adj_own_stones += 1
        elif v == -1:
            enemy.add(gid[nb])
            adj_opp_stones += 1
        else:
            adj_empty.append(nb)

    captured = []
    for eg in enemy:
        if len(groups[eg]["libs"]) == 1:
            captured.append(eg)

    new_libs = set(adj_empty)
    for fg in friend:
        new_libs.update(groups[fg]["libs"])
    new_libs.discard(p)

    cap_size = 0
    for cg in captured:
        stones = groups[cg]["stones"]
        cap_size += len(stones)

        # Only captured stones adjacent to the newly connected friendly group
        # are liberties of the new move's group.
        for s in stones:
            for nb in NEIGHBORS[s]:
                if nb == p or (board[nb] == 1 and gid[nb] in friend):
                    new_libs.add(s)
                    break

    if not captured and not new_libs:
        return None

    cap_set = set(captured)
    enemy_after = []
    for eg in enemy:
        if eg not in cap_set:
            enemy_after.append((eg, len(groups[eg]["libs"]) - 1))

    new_size = 1
    for fg in friend:
        new_size += groups[fg]["size"]

    return {
        "friend": tuple(friend),
        "enemy": tuple(enemy),
        "captured": tuple(captured),
        "cap_size": cap_size,
        "new_libs": len(new_libs),
        "new_size": new_size,
        "enemy_after": tuple(enemy_after),
        "adj_empty": len(adj_empty),
        "adj_own": adj_own_stones,
        "adj_opp": adj_opp_stones,
    }


def _state_after(board, p, groups, captured):
    nb = list(board)
    nb[p] = 1
    for cg in captured:
        for s in groups[cg]["stones"]:
            nb[s] = 0
    return tuple(nb)


# ---------- Heuristic scoring ----------

def _local_counts(board, p):
    own2 = opp2 = own4 = opp4 = 0
    for q, d in LOCAL[p]:
        v = board[q]
        if v == 1:
            own4 += 1
            if d <= 2:
                own2 += 1
        elif v == -1:
            opp4 += 1
            if d <= 2:
                opp2 += 1
    return own2, opp2, own4, opp4


def _corner_value(x, y):
    a, b = (x, y) if x <= y else (y, x)
    if (a, b) == (4, 4):
        return 115.0
    if (a, b) == (3, 4):
        return 108.0
    if (a, b) == (3, 3):
        return 92.0
    if (a, b) == (4, 5):
        return 68.0
    if (a, b) == (3, 5):
        return 62.0
    if (a, b) == (4, 6):
        return 58.0
    if (a, b) == (3, 6):
        return 55.0
    if (a, b) == (5, 5):
        return 48.0
    if a == 4 and b <= 7:
        return 42.0
    if a == 3 and b <= 7:
        return 35.0
    return 0.0


def _positional_score(p, total, board):
    r, c = divmod(p, N)
    line = LINE[p]
    s = 0.0

    if line == 1:
        s -= 105.0 if total < 240 else 30.0
    elif line == 2:
        s -= 40.0 if total < 180 else 8.0
    elif line == 3:
        s += 16.0 if total < 260 else 6.0
    elif line == 4:
        s += 24.0 if total < 220 else 8.0
    elif line == 5:
        s += 9.0 if total < 180 else 3.0
    elif line >= 8 and total < 60:
        s += 2.0

    if total < 140:
        early = (140.0 - total) / 140.0
        best_corner = 0.0

        for k, (cr, cc0) in enumerate(CORNERS):
            x = abs(r - cr) + 1
            y = abs(c - cc0) + 1
            if x <= 7 and y <= 7:
                val = _corner_value(x, y)
                if val:
                    own = opp = 0
                    for q in CORNER_REGIONS[k]:
                        if board[q] == 1:
                            own += 1
                        elif board[q] == -1:
                            opp += 1

                    if own + opp == 0:
                        mult = 1.0
                    elif opp and not own:
                        mult = 0.62
                    elif own and not opp:
                        mult = 0.38
                    else:
                        mult = 0.18

                    cv = val * mult
                    if cv > best_corner:
                        best_corner = cv

        s += early * best_corner

        row, col = r + 1, c + 1
        if (row in (4, 16) and col == 10) or (col in (4, 16) and row == 10):
            s += 50.0 * early
        if row == 10 and col == 10:
            s += 18.0 * early

    return s


def _jitter(p, seed):
    x = (p * 1103515245 + seed * 12345 + 0x9E3779B9) & 0xFFFFFFFF
    x ^= (x >> 16)
    return (((x & 1023) / 1023.0) - 0.5) * 0.5


def _score_move(p, feat, board, groups, gid, total,
                region_owner, region_size, area_delta, current_area, seed):
    score = 0.0
    tactical = 0.0

    cap_size = feat["cap_size"]
    new_libs = feat["new_libs"]

    # Approximate area swing. Capped so doomed invasions do not dominate everything.
    if area_delta > 0:
        score += min(area_delta, 10) * 8.0 + max(0, area_delta - 10) * 1.5
    elif area_delta < 0:
        score += area_delta * 6.0

    # Captures are urgent.
    if cap_size:
        v = 950.0 + 155.0 * cap_size + 16.0 * min(cap_size * cap_size, 100)
        score += v
        tactical += v

    # Defend adjacent friendly groups.
    saved_size = 0
    for fg in feat["friend"]:
        g = groups[fg]
        libs = len(g["libs"])
        sz = g["size"]
        if libs == 1:
            v = 850.0 + 105.0 * sz + 35.0 * min(new_libs, 6)
            score += v
            tactical += v
            saved_size += sz
        elif libs == 2:
            v = 115.0 + 16.0 * min(sz, 12)
            score += v
            tactical += 0.45 * v
        elif libs == 3:
            score += 28.0 + 4.0 * min(sz, 10)

    # Attack adjacent enemy groups.
    for eg, nl in feat["enemy_after"]:
        g = groups[eg]
        sz = g["size"]
        if nl == 1:
            v = 500.0 + 70.0 * sz
            score += v
            tactical += v
        elif nl == 2:
            v = 105.0 + 16.0 * min(sz, 12)
            score += v
            tactical += 0.35 * v
        elif nl == 3:
            score += 30.0 + 4.0 * min(sz, 10)

    # Connections and cuts.
    nf = len(feat["friend"])
    ne = len(feat["enemy"])

    if nf >= 2:
        szsum = sum(min(groups[fg]["size"], 8) for fg in feat["friend"])
        low = sum(1 for fg in feat["friend"] if len(groups[fg]["libs"]) <= 2)
        score += 120.0 * (nf - 1) + 12.0 * szsum + 55.0 * low

    if ne >= 2:
        esum = sum(min(groups[eg]["size"], 8) for eg in feat["enemy"])
        score += 95.0 * (ne - 1) + 9.0 * esum
        if new_libs <= 2 and cap_size == 0:
            score -= 80.0

    if nf and ne:
        score += 28.0

    # Shape / self-atari control.
    if new_libs <= 1:
        if cap_size == 0 and saved_size == 0:
            score -= 900.0
        elif cap_size <= 1:
            score -= 520.0
        else:
            score -= 220.0
    elif new_libs == 2:
        if cap_size == 0 and saved_size == 0:
            score -= 125.0
        else:
            score -= 45.0
    elif new_libs == 3:
        score += 18.0
    else:
        score += 13.0 * min(new_libs, 8)

    # Ko-like / snapback-like single-stone captures are often dangerous.
    if cap_size == 1 and new_libs == 1:
        score -= 420.0

    own2, opp2, own4, opp4 = _local_counts(board, p)

    if feat["adj_opp"] and not feat["adj_own"] and cap_size == 0:
        if new_libs <= 2:
            score -= 230.0
        else:
            score -= 70.0

    if total > 45 and own4 + opp4 == 0:
        score -= 45.0
    elif total > 150 and own4 + opp4 <= 1:
        score -= 25.0

    score += 6.0 * own2 + 5.0 * opp2 + 1.8 * own4 + 1.5 * opp4

    if tactical < 250.0 and own4 >= 8 and opp4 == 0:
        score -= 65.0
    if tactical < 250.0 and opp4 >= 8 and own2 == 0 and cap_size == 0:
        score -= 70.0

    diag_own = diag_opp = 0
    for q in DIAGONALS[p]:
        if board[q] == 1:
            diag_own += 1
        elif board[q] == -1:
            diag_opp += 1

    if diag_own:
        score += (18.0 if feat["adj_own"] == 0 else 7.0) * diag_own
    if diag_opp and feat["adj_opp"] == 0:
        score += 8.0 * diag_opp

    # Do not fill solid own eyes or safe own territory unless tactical.
    if _is_eye(board, p, 1):
        score -= 850.0 if tactical < 500.0 else 180.0

    if _is_eye(board, p, -1) and cap_size == 0:
        score -= 350.0 if tactical < 500.0 else 80.0

    owner = region_owner[p]
    rsz = region_size[p]

    if owner == 1 and cap_size == 0:
        pen = 170.0 + 6.0 * min(rsz, 20)
        if tactical < 350.0:
            score -= pen
        else:
            score -= 0.25 * pen
    elif owner == -1 and cap_size == 0:
        support = own2 + 0.5 * own4
        if rsz <= 4 and tactical < 500.0:
            score -= 330.0
        elif rsz <= 8 and support < 2 and tactical < 500.0:
            score -= 190.0
        elif support < 1 and new_libs <= 2 and tactical < 500.0:
            score -= 150.0
        else:
            score += min(rsz, 25) * 2.5
    else:
        if total > 180:
            score += 10.0

    if total > 220:
        if current_area < -20 and owner == -1 and cap_size == 0:
            score += 35.0
        elif current_area > 25 and owner == -1 and tactical < 350.0:
            score -= 35.0

    score += _positional_score(p, total, board)
    score += _jitter(p, seed)
    return score


def _pass_threshold(total, current_area):
    if total < 80:
        th = -500.0
    elif total < 180:
        th = -220.0
    elif total < 280:
        th = -90.0
    elif total < 340:
        th = -15.0
    else:
        th = 8.0

    if total > 240:
        if current_area > 25:
            th += 18.0
        elif current_area < -20:
            th -= 45.0

    return th


# ---------- Memory helpers ----------

def _seed_from_board(board, total):
    x = (0xA5A5A5A5 ^ ((total * 2654435761) & 0xFFFFFFFF)) & 0xFFFFFFFF
    for i, v in enumerate(board):
        if v:
            mul = 0x9E3779B1 if v == 1 else 0x85EBCA77
            x ^= ((i + 1) * mul) & 0xFFFFFFFF
            x = ((x << 13) | (x >> 19)) & 0xFFFFFFFF
    return x


def _prepare_memory(memory, current_state, total, board):
    if not isinstance(memory, dict):
        memory = {}

    last_total = memory.get("last_total", 0)
    if isinstance(last_total, int) and total <= 1 and last_total > 5:
        old_seed = memory.get("seed")
        memory = {}
        if isinstance(old_seed, int):
            memory["seed"] = old_seed

    hist_obj = memory.get("history")
    if isinstance(hist_obj, set):
        hist = hist_obj
    else:
        try:
            hist = set(hist_obj) if hist_obj is not None else set()
        except Exception:
            hist = set()

    hist.add(current_state)
    memory["history"] = hist

    seed = memory.get("seed")
    if not isinstance(seed, int):
        seed = _seed_from_board(board, total)
        memory["seed"] = seed

    return memory, hist, seed


def _finish_memory(memory, hist, after_state, seed):
    hist.add(after_state)
    memory["history"] = hist
    memory["last_after"] = after_state
    memory["last_total"] = sum(1 for v in after_state if v)
    memory["seed"] = seed

    mv = memory.get("moves", 0)
    memory["moves"] = (mv if isinstance(mv, int) else 0) + 1
    return memory


# ---------- Required API ----------

def policy(me, opponent, memory):
    board = _build_board(me, opponent)
    total = sum(1 for v in board if v)
    current_state = tuple(board)

    memory, hist, seed = _prepare_memory(memory, current_state, total, board)

    last_after = memory.get("last_after")
    if last_after is not None and not isinstance(last_after, tuple):
        try:
            last_after = tuple(last_after)
        except Exception:
            last_after = None

    groups, gid = _analyze_groups(board)
    region_owner, region_size = _analyze_regions(board)
    current_area = _area_score(board)

    best_p = None
    best_score = -10**18
    best_state = None

    for p in range(NN):
        if board[p] != 0:
            continue

        feat = _move_features(p, board, groups, gid)
        if feat is None:
            continue

        # If memory is missing, avoid unknown ko-like single-stone recaptures.
        if last_after is None and feat["cap_size"] == 1 and feat["new_libs"] == 1 and total > 1:
            continue

        post = _state_after(board, p, groups, feat["captured"])

        # Avoid simple ko / positional repetition.
        if last_after is not None and post == last_after:
            continue
        if post in hist:
            continue

        area_delta = _area_score(post) - current_area
        sc = _score_move(
            p, feat, board, groups, gid, total,
            region_owner, region_size, area_delta, current_area, seed
        )

        if sc > best_score:
            best_score = sc
            best_p = p
            best_state = post

    if best_p is None or best_score < _pass_threshold(total, current_area):
        memory = _finish_memory(memory, hist, current_state, seed)
        return (0, 0), memory

    memory = _finish_memory(memory, hist, best_state, seed)
    return (best_p // N + 1, best_p % N + 1), memory
