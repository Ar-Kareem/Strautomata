
import time
from collections import deque

N = 19
NN = N * N
INF = 10 ** 9

NEI = []
DIAG = []
for i in range(NN):
    r = i // N
    c = i % N
    ns = []
    if r > 0:
        ns.append(i - N)
    if r < N - 1:
        ns.append(i + N)
    if c > 0:
        ns.append(i - 1)
    if c < N - 1:
        ns.append(i + 1)
    NEI.append(tuple(ns))
    ds = []
    if r > 0 and c > 0:
        ds.append(i - N - 1)
    if r > 0 and c < N - 1:
        ds.append(i - N + 1)
    if r < N - 1 and c > 0:
        ds.append(i + N - 1)
    if r < N - 1 and c < N - 1:
        ds.append(i + N + 1)
    DIAG.append(tuple(ds))

P3 = [1] * NN
for i in range(1, NN):
    P3[i] = P3[i - 1] * 3


def _key_points():
    pts = set()
    offs = [(3, 3), (2, 3), (3, 2), (2, 2), (4, 3), (3, 4),
            (2, 4), (4, 2), (5, 3), (3, 5), (5, 2), (2, 5)]
    for top in (True, False):
        for left in (True, False):
            for a, b in offs:
                r = a if top else 18 - a
                c = b if left else 18 - b
                pts.add(r * N + c)
    for r, c in ((3, 9), (9, 3), (9, 15), (15, 9), (9, 9)):
        pts.add(r * N + c)
    return pts


KEY_POINTS = _key_points()


def _hash_board(board):
    h = 0
    for i, v in enumerate(board):
        if v:
            h += v * P3[i]
    return h


def _distances(sources):
    dist = [INF] * NN
    if not sources:
        return dist
    dq = deque()
    for s in sources:
        dist[s] = 0
        dq.append(s)
    while dq:
        x = dq.popleft()
        nd = dist[x] + 1
        for n in NEI[x]:
            if dist[n] > nd:
                dist[n] = nd
                dq.append(n)
    return dist


def _compute_groups(board):
    gid = [-1] * NN
    groups = []
    for i, v in enumerate(board):
        if v and gid[i] < 0:
            color = v
            gidx = len(groups)
            stones = []
            libs = set()
            stack = [i]
            gid[i] = gidx
            while stack:
                x = stack.pop()
                stones.append(x)
                for n in NEI[x]:
                    vn = board[n]
                    if vn == 0:
                        libs.add(n)
                    elif vn == color and gid[n] < 0:
                        gid[n] = gidx
                        stack.append(n)
            groups.append({"c": color, "stones": stones, "libs": libs, "n": len(stones)})
    return gid, groups


def _corner_counts(board):
    out = []
    for r0, c0 in ((0, 0), (0, 13), (13, 0), (13, 13)):
        my = op = 0
        for r in range(r0, r0 + 6):
            base = r * N
            for c in range(c0, c0 + 6):
                v = board[base + c]
                if v == 1:
                    my += 1
                elif v == 2:
                    op += 1
        out.append((my, op))
    return out


def _add_square(cand, board, idx, rad):
    r = idx // N
    c = idx % N
    r0 = max(0, r - rad)
    r1 = min(N - 1, r + rad)
    c0 = max(0, c - rad)
    c1 = min(N - 1, c + rad)
    for rr in range(r0, r1 + 1):
        base = rr * N
        for cc in range(c0, c1 + 1):
            j = base + cc
            if board[j] == 0:
                cand.add(j)


def _candidate_indices(board, me_idx, opp_idx, groups, total, last_opp, captured_from_me):
    cand = set()
    for idx in me_idx:
        _add_square(cand, board, idx, 2)
    for idx in opp_idx:
        _add_square(cand, board, idx, 2)
    for g in groups:
        if len(g["libs"]) <= 3:
            cand.update(g["libs"])
    for idx in last_opp:
        _add_square(cand, board, idx, 3)
    for idx in captured_from_me:
        _add_square(cand, board, idx, 3)
    if total < 30:
        for idx in KEY_POINTS:
            if board[idx] == 0:
                cand.add(idx)
    if len(cand) < 10:
        for i, v in enumerate(board):
            if v == 0:
                cand.add(i)
    return cand


def _positional_bonus(idx, total, dist_my, dist_opp, corner_counts):
    r = idx // N
    c = idx % N
    a = r if r < 9 else 18 - r
    b = c if c < 9 else 18 - c
    edge = a if a < b else b
    bonus = 0.0
    if total < 60:
        if edge == 0:
            bonus -= 150
        elif edge == 1:
            bonus -= 60
        elif edge == 2:
            bonus += 4
        elif edge == 3:
            bonus += 16
        elif edge == 4:
            bonus += 7
        if a <= 5 and b <= 5:
            ab = (a, b)
            if ab == (3, 3):
                bonus += 118
            elif ab == (2, 3) or ab == (3, 2):
                bonus += 96
            elif ab == (2, 2):
                bonus += 64
            elif ab in ((4, 3), (3, 4), (2, 4), (4, 2)):
                bonus += 44
            elif ab in ((5, 3), (3, 5), (5, 2), (2, 5)):
                bonus += 18
            ci = 0 if (r < 9 and c < 9) else (1 if r < 9 else (2 if c < 9 else 3))
            cm, co = corner_counts[ci]
            if co > 0 and cm == 0 and ab in ((2, 4), (4, 2), (3, 4), (4, 3), (2, 3), (3, 2), (5, 3), (3, 5)):
                bonus += 26
            elif cm > 0 and co == 0 and ab in ((2, 3), (3, 2), (2, 4), (4, 2)):
                bonus += 16
        if (a == 3 and b == 9) or (b == 3 and a == 9):
            bonus += 34
        elif a == 9 and b == 9:
            bonus += 4
    else:
        if edge == 0:
            bonus -= 5
        elif edge == 1:
            bonus -= 2
    dm = dist_my[idx]
    do = dist_opp[idx]
    if dm < INF and do < INF:
        d = do - dm
        if d > 3:
            d = 3
        elif d < -3:
            d = -3
        bonus += 3.0 * d
        if dm <= 3 and do >= 4:
            bonus += 7
        if do <= 2 and dm > do:
            bonus -= 7
    return bonus


def _score_candidate(board, gid, groups, idx, dist_my, dist_opp, corner_counts, total,
                     cur_hash, last_hash, last_opp_set, captured_from_me,
                     my_atari, opp_atari_max):
    if board[idx] != 0:
        return None
    adj_own = set()
    adj_opp = set()
    empty_ns = []
    for n in NEI[idx]:
        v = board[n]
        if v == 1:
            g = gid[n]
            if g >= 0:
                adj_own.add(g)
        elif v == 2:
            g = gid[n]
            if g >= 0:
                adj_opp.add(g)
        else:
            empty_ns.append(n)

    captured_stones = []
    capt = 0
    atari_groups = []
    reduced_groups = []
    for og in adj_opp:
        g = groups[og]
        L = len(g["libs"])
        if L == 1:
            captured_stones.extend(g["stones"])
            capt += g["n"]
        elif L == 2:
            atari_groups.append(g)
        elif L == 3:
            reduced_groups.append(g)

    if capt == 1:
        s = captured_stones[0]
        if idx in captured_from_me and s in last_opp_set:
            return None
        if last_hash is not None:
            rh = cur_hash + P3[idx] - 2 * P3[s]
            if rh == last_hash:
                return None

    new_libs = set(empty_ns)
    for og in adj_own:
        new_libs.update(groups[og]["libs"])
    new_libs.discard(idx)
    new_size = 1
    for og in adj_own:
        new_size += groups[og]["n"]
    if captured_stones:
        for s in captured_stones:
            for n in NEI[s]:
                if n == idx or (board[n] == 1 and gid[n] in adj_own):
                    new_libs.add(s)
                    break
    nl = len(new_libs)
    if nl == 0:
        return None

    score = 0.0
    if capt:
        score += 55 + 42 * capt + (12 * capt if capt > 1 else 0)

    saved_ids = set()
    for og in adj_own:
        g = groups[og]
        L = len(g["libs"])
        if L == 1 and nl > 1:
            saved_ids.add(og)
            score += 48 + 35 * g["n"]
        elif L == 2 and nl >= 3:
            score += 8 + 5 * g["n"]

    for g in atari_groups:
        score += 24 + 18 * g["n"]
    for g in reduced_groups:
        score += 3 * g["n"]

    no = len(adj_own)
    ne = len(adj_opp)
    if no >= 2:
        score += 20 * (no - 1) + 3 * new_size
    if ne >= 2:
        score += 14 * (ne - 1) + (8 if no else 0)

    if nl == 1:
        if capt == 1 and new_size == 1:
            score += 6
        else:
            score -= 90 + 50 * new_size
    elif nl == 2:
        score -= 7 * new_size
    elif nl == 3:
        score -= new_size

    unresolved = set()
    if my_atari:
        unresolved = my_atari - saved_ids
        if unresolved:
            bad = max(groups[g]["n"] for g in unresolved)
            if capt < bad:
                score -= 80 + 50 * bad
            else:
                score -= 8 * bad

    if opp_atari_max and capt < opp_atari_max and not unresolved:
        diff = opp_atari_max - capt
        score -= 10 + 7 * diff

    if ne and not capt and not atari_groups and not reduced_groups:
        score -= 3

    if capt == 0:
        orth_all_own = True
        for n in NEI[idx]:
            if board[n] != 1:
                orth_all_own = False
                break
        if orth_all_own:
            diag_opp = 0
            diag_empty = 0
            for d in DIAG[idx]:
                v = board[d]
                if v == 2:
                    diag_opp += 1
                elif v == 0:
                    diag_empty += 1
            allowed = 1 if len(NEI[idx]) < 4 else 0
            if diag_empty == 0 and diag_opp <= allowed:
                score -= 135

    score += _positional_bonus(idx, total, dist_my, dist_opp, corner_counts)
    sim = {
        "capt": capt,
        "captured_stones": captured_stones,
        "new_lib": nl,
        "new_size": new_size,
        "adj_own": adj_own,
        "adj_opp": adj_opp,
    }
    return score, sim


def _make_board_after(board, idx, captured_stones):
    nb = board.copy()
    nb[idx] = 1
    for s in captured_stones:
        nb[s] = 0
    return nb


def _area_score(board, my_count, opp_count):
    seen = bytearray(NN)
    my_ter = 0
    opp_ter = 0
    for i, v in enumerate(board):
        if v == 0 and not seen[i]:
            stack = [i]
            seen[i] = 1
            size = 0
            mask = 0
            while stack:
                x = stack.pop()
                size += 1
                for n in NEI[x]:
                    vn = board[n]
                    if vn == 0:
                        if not seen[n]:
                            seen[n] = 1
                            stack.append(n)
                    elif vn == 1:
                        mask |= 1
                    else:
                        mask |= 2
            if mask == 1:
                my_ter += size
            elif mask == 2:
                opp_ter += size
    return (my_count + my_ter) - (opp_count + opp_ter)


def _fallback_policy(me, opponent, memory):
    if not isinstance(memory, dict):
        memory = {}
    board = [0] * NN
    for r, c in me:
        board[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        board[(r - 1) * N + (c - 1)] = 2
    for i, v in enumerate(board):
        if v == 0:
            ok = False
            for n in NEI[i]:
                if board[n] == 0:
                    ok = True
                    break
            if ok:
                return (i // N + 1, i % N + 1), memory
    return (0, 0), memory


def _policy_impl(me, opponent, memory):
    start = time.perf_counter()
    if not isinstance(memory, dict):
        memory = {}

    me_idx = [(r - 1) * N + (c - 1) for r, c in me]
    opp_idx = [(r - 1) * N + (c - 1) for r, c in opponent]
    me_set = set(me_idx)
    opp_set = set(opp_idx)
    board = [0] * NN
    for i in me_idx:
        board[i] = 1
    for i in opp_idx:
        board[i] = 2
    total = len(me_idx) + len(opp_idx)
    cur_hash = _hash_board(board)

    last_hash = memory.get("last_hash")
    last_opp_set = set()
    captured_from_me = set()
    if "prev_me" in memory and "prev_opp" in memory:
        prev_me = set(memory.get("prev_me", []))
        prev_opp = set(memory.get("prev_opp", []))
        if me_set.issubset(prev_me) and prev_opp.issubset(opp_set):
            last_opp_set = opp_set - prev_opp
            captured_from_me = prev_me - me_set
        else:
            last_hash = None

    gid, groups = _compute_groups(board)
    dist_my = _distances(me_idx)
    dist_opp = _distances(opp_idx)
    corner_counts = _corner_counts(board)
    my_atari = {i for i, g in enumerate(groups) if g["c"] == 1 and len(g["libs"]) == 1}
    opp_atari_max = 0
    for g in groups:
        if g["c"] == 2 and len(g["libs"]) == 1 and g["n"] > opp_atari_max:
            opp_atari_max = g["n"]

    def finish(idx, sim):
        if idx is None:
            memory["prev_me"] = list(me_idx)
            memory["prev_opp"] = list(opp_idx)
            memory["last_hash"] = cur_hash
            memory["move_no"] = int(memory.get("move_no", 0)) + 1
            return (0, 0), memory
        after_me = set(me_idx)
        after_me.add(idx)
        after_opp = set(opp_idx)
        after_opp.difference_update(sim["captured_stones"])
        memory["prev_me"] = list(after_me)
        memory["prev_opp"] = list(after_opp)
        h = cur_hash + P3[idx]
        for s in sim["captured_stones"]:
            h -= 2 * P3[s]
        memory["last_hash"] = h
        memory["move_no"] = int(memory.get("move_no", 0)) + 1
        return (idx // N + 1, idx % N + 1), memory

    cand = _candidate_indices(board, me_idx, opp_idx, groups, total, last_opp_set, captured_from_me)
    scored = []
    for idx in cand:
        res = _score_candidate(board, gid, groups, idx, dist_my, dist_opp, corner_counts, total,
                               cur_hash, last_hash, last_opp_set, captured_from_me,
                               my_atari, opp_atari_max)
        if res is not None:
            scored.append((res[0], idx, res[1]))

    if not scored:
        for idx in range(NN):
            if board[idx] == 0:
                res = _score_candidate(board, gid, groups, idx, dist_my, dist_opp, corner_counts, total,
                                       cur_hash, last_hash, last_opp_set, captured_from_me,
                                       my_atari, opp_atari_max)
                if res is not None:
                    return finish(idx, res[1])
        return finish(None, None)

    scored.sort(key=lambda x: x[0], reverse=True)
    elapsed = time.perf_counter() - start
    if elapsed > 0.86:
        return finish(scored[0][1], scored[0][2])

    if total < 60:
        area_w = 2.0
    elif total < 140:
        area_w = 4.5
    else:
        area_w = 7.5
    K = 14 if total < 150 else 10
    if elapsed > 0.58:
        K = min(K, 7)
    if elapsed > 0.74:
        K = min(K, 4)

    best = None
    my_count_after = len(me_idx) + 1
    for base, idx, sim in scored[:K]:
        nb = _make_board_after(board, idx, sim["captured_stones"])
        ar = _area_score(nb, my_count_after, len(opp_idx) - sim["capt"])
        final = base + area_w * ar
        if best is None or final > best[0]:
            best = (final, idx, sim)
    if best is None:
        return finish(scored[0][1], scored[0][2])
    return finish(best[1], best[2])


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        return _policy_impl(me, opponent, memory)
    except Exception:
        return _fallback_policy(me, opponent, memory)
