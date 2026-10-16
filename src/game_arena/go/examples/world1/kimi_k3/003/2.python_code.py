
from collections import deque

N = 19
NN = N * N

# Orthogonal and diagonal neighbors.
NEI = []
DIAG = []
for r in range(N):
    for c in range(N):
        ns = []
        if r > 0:
            ns.append((r - 1) * N + c)
        if r < N - 1:
            ns.append((r + 1) * N + c)
        if c > 0:
            ns.append(r * N + c - 1)
        if c < N - 1:
            ns.append(r * N + c + 1)
        NEI.append(tuple(ns))
        ds = []
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ds.append(rr * N + cc)
        DIAG.append(tuple(ds))

# Influence weights by distance to nearest stone.
INF_W = (0, 6, 5, 4, 3, 2, 1)

# Positional table: corners first, then sides, center low unless fighting.
SIDE_VAL = (-10, -6, 4, 6, 5, 4, 3, 2, 1, 0)
CORNER = (
    (-10, -7, -3, -1, -2, -3),
    (-7, -5, 0, 3, 2, 0),
    (-3, 0, 7, 10, 8, 4),
    (-1, 3, 10, 12, 10, 6),
    (-2, 2, 8, 10, 8, 5),
    (-3, 0, 4, 6, 5, 3),
)
HOSHI = ((4, 4), (4, 10), (4, 16),
         (10, 4), (10, 10), (10, 16),
         (16, 4), (16, 10), (16, 16))
HOSHI_IDX = set((r - 1) * N + (c - 1) for r, c in HOSHI)

BASE = [0.0] * NN
for r in range(N):
    for c in range(N):
        idx = r * N + c
        a = min(r, N - 1 - r)
        b = min(c, N - 1 - c)
        e = a if a < b else b
        val = float(SIDE_VAL[e])
        if a <= 5 and b <= 5:
            cv = CORNER[a][b]
            if cv > val:
                val = float(cv)
        if idx in HOSHI_IDX:
            val += 2.0
        BASE[idx] = val
OPEN_POINTS = tuple(i for i, v in enumerate(BASE) if v >= 8.0)

MAX_CANDIDATES = 88
LAST_AFTER_BOARD = None  # board tuple after our previous move, with opponent to move


def get_groups(board):
    seen = [False] * NN
    groups = []
    for i, v in enumerate(board):
        if v == 0 or seen[i]:
            continue
        stack = [i]
        seen[i] = True
        stones = []
        libs = set()
        while stack:
            p = stack.pop()
            stones.append(p)
            for q in NEI[p]:
                bq = board[q]
                if bq == 0:
                    libs.add(q)
                elif bq == v and not seen[q]:
                    seen[q] = True
                    stack.append(q)
        groups.append((v, stones, libs))
    return groups


def dist_to_color(board, color):
    dist = [-1] * NN
    dq = deque()
    for i, v in enumerate(board):
        if v == color:
            dist[i] = 0
            dq.append(i)
    if not dq:
        return dist
    nei = NEI
    while dq:
        p = dq.popleft()
        nd = dist[p] + 1
        for q in nei[p]:
            if dist[q] < 0:
                dist[q] = nd
                dq.append(q)
    return dist


def evaluate_board(board, need_map=False):
    my = 0
    opp = 0
    for v in board:
        if v == 1:
            my += 1
        elif v == -1:
            opp += 1

    dm = dist_to_color(board, 1)
    do = dist_to_color(board, -1)
    influence = 0
    for i, v in enumerate(board):
        if v != 0:
            continue
        a = dm[i]
        b = do[i]
        if a < 0:
            a = 99
        if b < 0:
            b = 99
        if a < b:
            if a <= 6:
                influence += INF_W[a]
        elif b < a:
            if b <= 6:
                influence -= INF_W[b]

    groups = get_groups(board)
    gsum = 0
    my_atari = my_two = opp_atari = opp_two = 0
    max_my_atari = 0
    for color, stones, libs in groups:
        s = len(stones)
        l = len(libs)
        if l <= 1:
            f = -12
        elif l == 2:
            f = -3
        elif l == 3:
            f = 0
        elif l == 4:
            f = 2
        elif l == 5:
            f = 3
        else:
            f = 4
        if color == 1:
            gsum += s * f
            if l == 1:
                my_atari += s
                if s > max_my_atari:
                    max_my_atari = s
            elif l == 2:
                my_two += s
        else:
            gsum -= s * f
            if l == 1:
                opp_atari += s
            elif l == 2:
                opp_two += s

    stone_group = None
    if need_map:
        stone_group = [-1] * NN
        for gi, (_, stones, _) in enumerate(groups):
            for p in stones:
                stone_group[p] = gi

    score = 3 * (my - opp) + influence + gsum
    return score, {
        "groups": groups,
        "stone_group": stone_group,
        "my_atari": my_atari,
        "my_two": my_two,
        "opp_atari": opp_atari,
        "opp_two": opp_two,
        "max_my_atari": max_my_atari,
    }


def try_move(board, idx, color=1, ko_board=None):
    if board[idx] != 0:
        return None
    b = board[:]
    b[idx] = color
    oc = -color

    # Capture adjacent enemy groups with no liberties.
    checked = set()
    captured = []
    for nb in NEI[idx]:
        if b[nb] == oc and nb not in checked:
            stack = [nb]
            checked.add(nb)
            stones = []
            has_lib = False
            while stack:
                p = stack.pop()
                stones.append(p)
                for q in NEI[p]:
                    bq = b[q]
                    if bq == 0:
                        has_lib = True
                    elif bq == oc and q not in checked:
                        checked.add(q)
                        stack.append(q)
            if not has_lib:
                for p in stones:
                    b[p] = 0
                captured.extend(stones)

    # The resulting own group must have a liberty.
    stack = [idx]
    seen = {idx}
    stones = [idx]
    libs = set()
    while stack:
        p = stack.pop()
        for q in NEI[p]:
            bq = b[q]
            if bq == 0:
                libs.add(q)
            elif bq == color and q not in seen:
                seen.add(q)
                stack.append(q)
                stones.append(q)
    if not libs:
        return None
    if ko_board is not None and tuple(b) == ko_board:
        return None
    return b, captured, stones, libs


def is_true_eye(board, idx, color):
    for q in NEI[idx]:
        if board[q] != color:
            return False
    ds = DIAG[idx]
    edge_count = 4 - len(NEI[idx])
    if edge_count >= 1:
        return all(board[d] == color for d in ds)
    good = 0
    for d in ds:
        if board[d] == color:
            good += 1
    return good >= 3


def one_opponent_move_reachable(prev, cur):
    if prev is None or len(prev) != NN:
        return False
    added_opp = 0
    for a, b in zip(prev, cur):
        if a == b:
            continue
        if a == 0:
            if b == -1:
                added_opp += 1
                if added_opp > 1:
                    return False
            else:
                return False
        elif a == 1:
            if b != 0:
                return False
        else:
            return False
    return True


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global LAST_AFTER_BOARD

    board = [0] * NN
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = -1

    total = 0
    for v in board:
        if v != 0:
            total += 1

    if total == 0:
        LAST_AFTER_BOARD = None
    if LAST_AFTER_BOARD is not None and not one_opponent_move_reachable(LAST_AFTER_BOARD, board):
        LAST_AFTER_BOARD = None
    ko_board = LAST_AFTER_BOARD

    before_score, bm = evaluate_board(board, need_map=True)
    groups = bm["groups"]
    stone_group = bm["stone_group"]

    if total < 12:
        pos_w = 4.0
    elif total < 30:
        pos_w = 3.0
    elif total < 80:
        pos_w = 1.5
    else:
        pos_w = 0.4

    cand = set()
    quick = [0.0] * NN

    def add_point(p, inc=0.0):
        if board[p] == 0:
            cand.add(p)
            quick[p] += inc

    # Moves near existing stones; wider radius early for fuseki approaches.
    rad = 3 if total < 30 else 2
    for idx, v in enumerate(board):
        if v == 0:
            continue
        r, c = divmod(idx, N)
        for dr in range(-rad, rad + 1):
            rr = r + dr
            if rr < 0 or rr >= N:
                continue
            rem = rad - abs(dr)
            adr = abs(dr)
            for dc in range(-rem, rem + 1):
                cc = c + dc
                if cc < 0 or cc >= N:
                    continue
                p = rr * N + cc
                if board[p] != 0:
                    continue
                man = adr + abs(dc)
                inc = 0.35 * (rad + 1 - man)
                if man == 1:
                    inc += 1.0 if v == -1 else 0.6
                add_point(p, inc)

    # Urgent liberties: captures, ataris, and saving our own unstable groups.
    for color, stones, libs in groups:
        l = len(libs)
        s = len(stones)
        if color == -1:
            if l == 1:
                bonus = 1000.0 + 40.0 * s
                for p in libs:
                    add_point(p, bonus)
            elif l == 2:
                bonus = 250.0 + 15.0 * s
                for p in libs:
                    add_point(p, bonus)
            elif l == 3:
                bonus = 60.0 + 4.0 * s
                for p in libs:
                    add_point(p, bonus)
        else:
            if l == 1:
                bonus = 950.0 + 45.0 * s
                for p in libs:
                    add_point(p, bonus)
            elif l == 2:
                bonus = 220.0 + 14.0 * s
                for p in libs:
                    add_point(p, bonus)

    if total < 60:
        for p in OPEN_POINTS:
            add_point(p, 0.0)
    if len(cand) < 25:
        for p, v in enumerate(board):
            if v == 0 and BASE[p] >= 5.0:
                add_point(p, 0.0)
    if not cand:
        for p, v in enumerate(board):
            if v == 0:
                add_point(p, 0.0)

    for p in cand:
        quick[p] += BASE[p] * pos_w

    cand_list = list(cand)
    cand_list.sort(key=quick.__getitem__, reverse=True)
    if len(cand_list) > MAX_CANDIDATES:
        cand_list = cand_list[:MAX_CANDIDATES]

    best_score = -1.0e100
    best_idx = None
    best_after = None

    for p in cand_list:
        res = try_move(board, p, 1, ko_board)
        if res is None:
            continue
        b2, captured, _, _ = res
        after_score, am = evaluate_board(b2, need_map=False)
        cnum = len(captured)

        score = after_score - before_score
        if cnum:
            score += 34.0 * cnum + 4.0 * cnum * cnum

        # Extra urgency for fixing our shortage of liberties and creating enemy ataris.
        score += 12.0 * (bm["my_atari"] - am["my_atari"])
        score += 4.0 * (bm["my_two"] - am["my_two"])
        score += 5.0 * (am["opp_atari"] - bm["opp_atari"])
        score += 2.0 * (am["opp_two"] - bm["opp_two"])

        # Immediate recapture / snapback risk.
        risk = am["max_my_atari"]
        if risk:
            score -= 30.0 * risk
            if cnum == 0:
                score -= 12.0

        # Shape: connections and contact fights.
        adj_f = set()
        adj_e = set()
        for q in NEI[p]:
            v = board[q]
            if v == 1:
                adj_f.add(stone_group[q])
            elif v == -1:
                adj_e.add(stone_group[q])
        if len(adj_f) >= 2:
            score += 9.0 * (len(adj_f) - 1)
            for gi in adj_f:
                if len(groups[gi][2]) <= 2:
                    score += 6.0
        if adj_f and adj_e:
            score += 3.0

        # Do not fill true eyes unless it is clearly a saving/capturing necessity.
        if cnum == 0 and is_true_eye(board, p, 1):
            penalty = 85.0
            if bm["my_atari"] > am["my_atari"]:
                penalty = 30.0
            score -= penalty

        if score > best_score:
            best_score = score
            best_idx = p
            best_after = b2

    if best_idx is None or board[best_idx] != 0:
        LAST_AFTER_BOARD = tuple(board)
        return (0, 0)

    # Pass only in obviously harmful or finished positions.
    if best_score < -60.0 or (best_score < -25.0 and total > 230):
        LAST_AFTER_BOARD = tuple(board)
        return (0, 0)

    LAST_AFTER_BOARD = tuple(best_after)
    return (best_idx // N + 1, best_idx % N + 1)
