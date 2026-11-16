
import time

N = 19
NN = N * N
ME = 1
OPP = 2


def _build_neighbors():
    neigh = []
    for i in range(NN):
        r, c = divmod(i, N)
        lst = []
        if r > 0:
            lst.append(i - N)
        if r + 1 < N:
            lst.append(i + N)
        if c > 0:
            lst.append(i - 1)
        if c + 1 < N:
            lst.append(i + 1)
        neigh.append(tuple(lst))
    return neigh


NEIGH = _build_neighbors()

CHEB2 = []
EDGE_D = [0] * NN
POS_BASE = [0.0] * NN
for i in range(NN):
    r, c = divmod(i, N)
    pts = []
    for dr in (-2, -1, 0, 1, 2):
        rr = r + dr
        if 0 <= rr < N:
            base = rr * N
            for dc in (-2, -1, 0, 1, 2):
                cc = c + dc
                if 0 <= cc < N:
                    pts.append(base + cc)
    CHEB2.append(tuple(pts))
    d = min(r, N - 1 - r, c, N - 1 - c)
    EDGE_D[i] = d
    if d == 0:
        POS_BASE[i] = -9.0
    elif d == 1:
        POS_BASE[i] = -3.0
    elif d == 2:
        POS_BASE[i] = 5.0
    elif d == 3:
        POS_BASE[i] = 7.0
    elif d == 4:
        POS_BASE[i] = 3.0
    else:
        POS_BASE[i] = 1.5


def _build_open_bonus():
    arr = [0.0] * NN
    vals = {
        (3, 3): 24.0,
        (2, 3): 21.0, (3, 2): 21.0,
        (2, 2): 17.0,
        (2, 4): 11.0, (4, 2): 11.0,
        (3, 4): 8.0, (4, 3): 8.0,
        (2, 5): 6.0, (5, 2): 6.0,
        (3, 5): 3.0, (5, 3): 3.0,
        (1, 3): 3.0, (3, 1): 3.0,
        (4, 5): 2.0, (5, 4): 2.0,
        (1, 2): 1.5, (2, 1): 1.5,
    }
    for cr in (1, N):
        for cc in (1, N):
            dr = 1 if cr == 1 else -1
            dc = 1 if cc == 1 else -1
            for (x, y), v in vals.items():
                r = cr + dr * x
                c = cc + dc * y
                if 1 <= r <= N and 1 <= c <= N:
                    i = (r - 1) * N + (c - 1)
                    if v > arr[i]:
                        arr[i] = v
    for r, c in ((4, 10), (10, 4), (10, 16), (16, 10)):
        i = (r - 1) * N + (c - 1)
        arr[i] = max(arr[i], 9.0)
    i = (10 - 1) * N + (10 - 1)
    arr[i] = max(arr[i], 5.0)
    return arr


OPEN_BONUS = _build_open_bonus()


def _group_from(board, start, color):
    stack = [start]
    seen = {start}
    stones = []
    libs = set()
    while stack:
        i = stack.pop()
        stones.append(i)
        for nb in NEIGH[i]:
            v = board[nb]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return stones, libs


def _apply_move(board, idx, color):
    if board[idx] != 0:
        return None
    opp = 3 - color
    b = board[:]
    b[idx] = color
    captured = []
    seen_groups = set()
    for nb in NEIGH[idx]:
        if b[nb] == opp and nb not in seen_groups:
            stones, libs = _group_from(b, nb, opp)
            seen_groups.update(stones)
            if not libs:
                for s in stones:
                    b[s] = 0
                captured.extend(stones)
    stones, libs = _group_from(b, idx, color)
    if not captured and not libs:
        return None
    return b, captured, stones, libs


def _scan_groups(board):
    visited = bytearray(NN)
    gid = [-1] * NN
    groups = []
    for i, v in enumerate(board):
        if v and not visited[i]:
            color = v
            gi = len(groups)
            stack = [i]
            visited[i] = 1
            stones = []
            libs = set()
            while stack:
                a = stack.pop()
                stones.append(a)
                gid[a] = gi
                for nb in NEIGH[a]:
                    bv = board[nb]
                    if bv == 0:
                        libs.add(nb)
                    elif bv == color and not visited[nb]:
                        visited[nb] = 1
                        stack.append(nb)
            groups.append((color, stones, libs))
    return groups, gid


def _danger(groups, color):
    d = 0.0
    for col, stones, libs in groups:
        if col != color:
            continue
        l = len(libs)
        s = len(stones)
        if l == 1:
            d += 16.0 + 7.0 * s
        elif l == 2:
            d += 4.0 + 1.6 * s
        elif l == 3 and s >= 6:
            d += 0.35 * s
    return d


def _ordered_candidates(board, groups, gid, total_stones):
    cand = set()
    if total_stones == 0:
        for i, v in enumerate(OPEN_BONUS):
            if v > 0.0 and board[i] == 0:
                cand.add(i)
        if not cand:
            cand.add((10 - 1) * N + (10 - 1))
    else:
        rad = 3 if total_stones < 10 else 2
        for i, v in enumerate(board):
            if v:
                r, c = divmod(i, N)
                for dr in range(-rad, rad + 1):
                    rr = r + dr
                    if 0 <= rr < N:
                        base = rr * N
                        for dc in range(-rad, rad + 1):
                            cc = c + dc
                            if 0 <= cc < N:
                                j = base + cc
                                if board[j] == 0:
                                    cand.add(j)
        for col, stones, libs in groups:
            l = len(libs)
            if l <= 3:
                cand.update(libs)
                if l <= 2:
                    for lib in libs:
                        for nb in NEIGH[lib]:
                            if board[nb] == 0:
                                cand.add(nb)
        if total_stones < 60:
            for i, v in enumerate(OPEN_BONUS):
                if v > 0.0 and board[i] == 0:
                    cand.add(i)

    def key(i):
        k = POS_BASE[i] * 10.0 + OPEN_BONUS[i] * 8.0
        fr = en = 0
        adj_fr = set()
        adj_en = set()
        for nb in NEIGH[i]:
            v = board[nb]
            if v == ME:
                fr += 1
                adj_fr.add(gid[nb])
            elif v == OPP:
                en += 1
                adj_en.add(gid[nb])
        k += fr * 6.0 + en * 2.0
        for g in adj_en:
            col, stones, libs = groups[g]
            l = len(libs)
            s = len(stones)
            if l == 1:
                k += 200000.0 + 3000.0 * s
            elif l == 2:
                k += 6000.0 + 250.0 * s
            elif l == 3:
                k += 500.0 + 40.0 * s
        for g in adj_fr:
            col, stones, libs = groups[g]
            l = len(libs)
            s = len(stones)
            if l == 1:
                k += 150000.0 + 2500.0 * s
            elif l == 2:
                k += 3000.0 + 120.0 * s
        return k

    return sorted(cand, key=key, reverse=True)


def _eval_move(board, idx, groups, gid, my_d_before, op_d_before, total_stones, near_enemy):
    res = _apply_move(board, idx, ME)
    if res is None:
        return -1e100, None
    b2, captured, mstones, mlibs = res
    gain = len(captured)

    groups2, gid2 = _scan_groups(b2)
    my_d_after = _danger(groups2, ME)
    op_d_after = _danger(groups2, OPP)

    save_term = (my_d_before - my_d_after) * 9.0
    pressure = max(0.0, op_d_after - op_d_before) * 7.0
    cap_bonus = 0.0
    if gain:
        cap_bonus = 35.0 * gain + 12.0 * gain * gain

    if total_stones < 18:
        pw, ow = 4.0, 1.0
    elif total_stones < 70:
        pw, ow = 2.2, 0.35
    elif total_stones < 170:
        pw, ow = 1.0, 0.0
    else:
        pw, ow = 0.55, 0.0

    score = pw * POS_BASE[idx] + ow * OPEN_BONUS[idx] + save_term + pressure + cap_bonus

    libs_n = len(mlibs)
    size_n = len(mstones)
    adj_fr = set()
    adj_en = set()
    fr_nb = en_nb = empty_nb = 0
    for nb in NEIGH[idx]:
        v = board[nb]
        if v == ME:
            fr_nb += 1
            adj_fr.add(gid[nb])
        elif v == OPP:
            en_nb += 1
            adj_en.add(gid[nb])
        else:
            empty_nb += 1

    if len(adj_fr) >= 2:
        tot = sum(len(groups[g][1]) for g in adj_fr)
        score += 12.0 * (len(adj_fr) - 1) + 1.5 * min(20, tot)
    if len(adj_en) >= 2 and (libs_n >= 3 or gain):
        score += 8.0 * (len(adj_en) - 1) + 2.0 * sum(min(5, len(groups[g][1])) for g in adj_en)

    for g in adj_en:
        col, stones, libs = groups[g]
        before_l = len(libs)
        after_l = None
        for s in stones:
            if b2[s] == OPP:
                after_l = len(groups2[gid2[s]][2])
                break
        if after_l is None:
            continue
        if after_l < before_l:
            score += (before_l - after_l) * (4.0 + 2.0 * len(stones))
            if after_l == 1:
                score += 10.0 + 3.0 * len(stones)

    if libs_n >= 3:
        score += min(7, libs_n) * 1.7 + min(9, size_n) * 1.3
    elif libs_n == 2 and gain == 0:
        score -= 9.0

    if libs_n == 1 and gain:
        sole = next(iter(mlibs))
        res3 = _apply_move(b2, sole, OPP)
        if res3 is not None:
            lost = len(res3[1])
            if gain == 1 and lost == 1:
                return -1e90, None
            if lost >= gain:
                score -= 220.0 + 80.0 * (lost - gain + 1)
            else:
                score += 35.0 * (gain - lost)
        else:
            score += 15.0

    if gain == 0 and en_nb == 0 and not near_enemy[idx]:
        offboard = 4 - len(NEIGH[idx])
        if empty_nb == 0 and fr_nb + offboard >= 3 and len(adj_fr) <= 1 and save_term <= 0.0 and pressure <= 0.0:
            score -= 20.0 if total_stones < 150 else 45.0
        elif len(adj_fr) <= 1 and save_term <= 0.0 and pressure <= 0.0:
            score -= 4.0

    return score, (gain, libs_n, save_term, pressure)


def _fallback(board):
    empt = [i for i, v in enumerate(board) if v == 0]
    if not empt:
        return None
    empt.sort(key=lambda i: POS_BASE[i] + OPEN_BONUS[i], reverse=True)
    last_resort = None
    for i in empt:
        res = _apply_move(board, i, ME)
        if res is None:
            continue
        b2, cap, st, libs = res
        if len(libs) == 1 and cap:
            sole = next(iter(libs))
            res3 = _apply_move(b2, sole, OPP)
            if res3 is not None:
                lost = len(res3[1])
                gain = len(cap)
                if gain == 1 and lost == 1:
                    continue
                if lost > gain:
                    if last_resort is None:
                        last_resort = i
                    continue
        return i
    return last_resort


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start = time.time()
    board = [0] * NN
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = ME
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            i = (r - 1) * N + (c - 1)
            if board[i] == 0:
                board[i] = OPP

    total_stones = sum(1 for v in board if v)
    if total_stones == NN:
        return (0, 0)

    groups, gid = _scan_groups(board)
    my_d_before = _danger(groups, ME)
    op_d_before = _danger(groups, OPP)

    near_enemy = [False] * NN
    for i, v in enumerate(board):
        if v == OPP:
            for j in CHEB2[i]:
                if board[j] == 0:
                    near_enemy[j] = True

    best_i = -1
    best_score = -1e100
    for i in _ordered_candidates(board, groups, gid, total_stones):
        if time.time() - start > 0.88 and best_i != -1:
            break
        sc, info = _eval_move(board, i, groups, gid, my_d_before, op_d_before, total_stones, near_enemy)
        if sc > best_score:
            best_score = sc
            best_i = i

    if best_i == -1:
        best_i = _fallback(board)
    if best_i is None:
        return (0, 0)

    if best_score < -45.0 and total_stones > 90:
        return (0, 0)
    return (best_i // N + 1, best_i % N + 1)
