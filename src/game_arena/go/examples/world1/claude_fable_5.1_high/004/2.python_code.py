
import time
import numpy as np

N = 19
W = N + 2
EMPTY, ME, OPP, BORDER = 0, 1, 2, 3
NBR_OFF = (-W, -1, 1, W)
DIAG_OFF = (-W - 1, -W + 1, W - 1, W + 1)
R = 4
KT = 1.2
TERR_SCALE = 0.8


def _make_kernel():
    K = np.zeros((2 * R + 1, 2 * R + 1))
    wts = {0: 3.0, 1: 1.0, 2: 0.5, 3: 0.25, 4: 0.12}
    for dr in range(-R, R + 1):
        for dc in range(-R, R + 1):
            d = abs(dr) + abs(dc)
            if d in wts:
                K[dr + R, dc + R] = wts[d]
    return K


KERNEL = _make_kernel()


def make_board(me, opp):
    b = [BORDER] * (W * W)
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            b[r * W + c] = EMPTY
    for (r, c) in me:
        if 1 <= r <= N and 1 <= c <= N:
            b[r * W + c] = ME
    for (r, c) in opp:
        if 1 <= r <= N and 1 <= c <= N:
            b[r * W + c] = OPP
    return b


def flood(b, start):
    color = b[start]
    stones = {start}
    stack = [start]
    libs = set()
    while stack:
        s = stack.pop()
        for d in NBR_OFF:
            n = s + d
            v = b[n]
            if v == EMPTY:
                libs.add(n)
            elif v == color and n not in stones:
                stones.add(n)
                stack.append(n)
    return stones, libs


def all_groups(b):
    gid = [-1] * (W * W)
    groups = []
    for i in range(W * W):
        if (b[i] == ME or b[i] == OPP) and gid[i] == -1:
            stones, libs = flood(b, i)
            g = len(groups)
            for s in stones:
                gid[s] = g
            groups.append((b[i], stones, libs))
    return gid, groups


def place(b, p, color):
    b2 = b[:]
    b2[p] = color
    other = 3 - color
    captured = set()
    for d in NBR_OFF:
        n = p + d
        if b2[n] == other and n not in captured:
            st, lb = flood(b2, n)
            if not lb:
                captured |= st
    for s in captured:
        b2[s] = EMPTY
    return b2, captured


def ladder_captured(b, stones, defender, deadline, depth=0):
    """Defender group (1 liberty) to move. True if attacker captures via ladder."""
    if depth > 50 or time.time() > deadline:
        return False
    attacker = 3 - defender
    libs = set()
    adj_att = set()
    for s in stones:
        for d in NBR_OFF:
            n = s + d
            v = b[n]
            if v == EMPTY:
                libs.add(n)
            elif v == attacker:
                adj_att.add(n)
    if len(libs) != 1:
        return len(libs) == 0
    seen = set()
    for a in adj_att:
        if a in seen:
            continue
        st, lb = flood(b, a)
        seen |= st
        if len(lb) <= 1:
            return False
    lib = next(iter(libs))
    b2, cap = place(b, lib, defender)
    if cap:
        return False
    grp, glibs = flood(b2, lib)
    if len(glibs) >= 3:
        return False
    if len(glibs) <= 1:
        return True
    for a in glibs:
        b3, cap3 = place(b2, a, attacker)
        ag, alibs = flood(b3, a)
        if len(alibs) <= 1:
            continue
        if ladder_captured(b3, grp, defender, deadline, depth + 1):
            return True
    return False


def own_2lib_dead(b, stones, libs, deadline):
    for a in libs:
        if time.time() > deadline:
            return False
        b2, cap = place(b, a, OPP)
        ag, alibs = flood(b2, a)
        if len(alibs) <= 1:
            continue
        if ladder_captured(b2, stones, ME, deadline):
            return True
    return False


def f_me(n):
    if n >= 4:
        return 1.0
    if n == 3:
        return 0.9
    if n == 2:
        return 0.75
    if n == 1:
        return 0.3
    return 0.0


def f_opp(n):
    if n >= 4:
        return 1.0
    if n == 3:
        return 0.92
    if n == 2:
        return 0.8
    if n == 1:
        return 0.35
    return 0.0


def is_true_eye(b, p):
    for d in NBR_OFF:
        v = b[p + d]
        if v != ME and v != BORDER:
            return False
    opp_diag = 0
    border_diag = 0
    for d in DIAG_OFF:
        v = b[p + d]
        if v == OPP:
            opp_diag += 1
        elif v == BORDER:
            border_diag += 1
    if border_diag > 0:
        return opp_diag == 0
    return opp_diag <= 1


def _fallback(me, opp):
    occ = set(me) | set(opp)
    best = None
    bestd = 1e9
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if (r, c) in occ:
                continue
            ok = False
            for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 1 <= rr <= N and 1 <= cc <= N and (rr, cc) not in occ:
                    ok = True
                    break
            if ok:
                d = abs(r - 10) + abs(c - 10)
                if d < bestd:
                    bestd = d
                    best = (r, c)
    return best if best is not None else (0, 0)


def _policy(me, opp):
    t0 = time.time()
    deadline = t0 + 0.70
    b = make_board(me, opp)
    gid, groups = all_groups(b)
    stones_total = len(me) + len(opp)
    opening = max(0.0, 1.0 - stones_total / 80.0)

    # influence maps
    size_p = N + 2 * R
    im = np.zeros((size_p, size_p))
    io = np.zeros((size_p, size_p))
    for color, stones, libs in groups:
        if len(libs) <= 1:
            continue
        arr = im if color == ME else io
        for s in stones:
            r, c = divmod(s, W)
            arr[r - 1:r + 2 * R, c - 1:c + 2 * R] += KERNEL
    diff = im - io
    o_before = np.tanh(KT * diff)
    emp = np.zeros((size_p, size_p))
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if b[r * W + c] == EMPTY:
                emp[r - 1 + R, c - 1 + R] = 1.0

    def corner_empty(r, c):
        rows = range(1, 8) if r <= 7 else range(13, 20)
        cols = range(1, 8) if c <= 7 else range(13, 20)
        for rr in rows:
            for cc in cols:
                if b[rr * W + cc] != EMPTY:
                    return False
        return True

    cands = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            p = r * W + c
            if b[p] != EMPTY:
                continue
            if is_true_eye(b, p):
                continue
            own_g = set()
            opp_g = set()
            empty_n = []
            for d in NBR_OFF:
                n = p + d
                v = b[n]
                if v == EMPTY:
                    empty_n.append(n)
                elif v == ME:
                    own_g.add(gid[n])
                elif v == OPP:
                    opp_g.add(gid[n])
            cap_groups = [g for g in opp_g if len(groups[g][2]) == 1]
            cap_stones = set()
            for g in cap_groups:
                cap_stones |= groups[g][1]
            S = 1 + sum(len(groups[g][1]) for g in own_g)
            new_libs = set(empty_n)
            for g in own_g:
                new_libs |= groups[g][2]
            new_libs.discard(p)
            saved_gain = 0.0
            if cap_stones:
                other_own = {}
                for s in cap_stones:
                    for d in NBR_OFF:
                        n = s + d
                        if n == p:
                            new_libs.add(s)
                        elif b[n] == ME:
                            g = gid[n]
                            if g in own_g:
                                new_libs.add(s)
                            else:
                                other_own.setdefault(g, set()).add(s)
                for g, extra in other_own.items():
                    color, st, lb = groups[g]
                    nb = len(lb)
                    na = len(lb | extra)
                    saved_gain += 10.0 * len(st) * (f_me(na) - f_me(nb))
            L = len(new_libs)
            if L == 0:
                continue
            if L == 1 and not cap_stones:
                continue
            if L == 1 and len(cap_stones) == 1 and not own_g:
                continue  # possible ko recapture, avoid
            f_after = 0.0 if L == 1 else f_me(L)
            own_before = sum(len(groups[g][1]) * f_me(len(groups[g][2])) for g in own_g)
            own_delta = 10.0 * (S * f_after - own_before - 1.0)
            gain = saved_gain
            for g in opp_g:
                color, st, lb = groups[g]
                sz = len(st)
                if len(lb) == 1:
                    gain += 10.0 * sz * f_opp(1) + 3.0 * sz + 1.0
                else:
                    gain += 10.0 * sz * (f_opp(len(lb)) - f_opp(len(lb) - 1))
            # territory
            sl = (slice(r - 1, r + 2 * R), slice(c - 1, c + 2 * R))
            after = np.tanh(KT * (diff[sl] + KERNEL))
            terr = float(((after - o_before[sl]) * emp[sl]).sum()) * TERR_SCALE
            pr, pc = r - 1 + R, c - 1 + R
            if im[pr, pc] < 0.3 and io[pr, pc] > 2.0:
                terr *= 0.35
            terr *= (0.3 + 0.7 * f_after)
            # line / corner bonuses
            line = min(r, N + 1 - r, c, N + 1 - c)
            if line == 1:
                bonus = -3.0 - 2.0 * opening
            elif line == 2:
                bonus = -1.0 - 2.0 * opening
            elif line == 3:
                bonus = 2.0 * opening
            elif line == 4:
                bonus = 2.5 * opening
            elif line == 5:
                bonus = 0.5 * opening
            else:
                bonus = -0.5 * (line - 5) * opening
            if opening > 0 and (r in (3, 4, 16, 17)) and (c in (3, 4, 16, 17)):
                if corner_empty(r, c):
                    bonus += (5.5 if (r in (4, 16) and c in (4, 16)) else 5.0) * opening
            score = own_delta + gain + terr + bonus
            cands.append([score, p, own_g, opp_g, L, cap_stones, S, terr, bonus, saved_gain])

    if not cands:
        return (0, 0)
    cands.sort(key=lambda x: -x[0])

    # refinement with ladder reading
    own_cache = {}
    opp_cache = {}

    def fb_own(g):
        if g in own_cache:
            return own_cache[g]
        color, st, lb = groups[g]
        n = len(lb)
        if n == 1:
            v = 0.0 if ladder_captured(b, st, ME, deadline) else 0.3
        elif n == 2:
            v = 0.15 if own_2lib_dead(b, st, lb, deadline) else 0.75
        else:
            v = f_me(n)
        own_cache[g] = v
        return v

    def fb_opp(g):
        if g in opp_cache:
            return opp_cache[g]
        color, st, lb = groups[g]
        n = len(lb)
        if n == 1:
            v = 0.0 if ladder_captured(b, st, OPP, deadline) else 0.35
        else:
            v = f_opp(n)
        opp_cache[g] = v
        return v

    K_REFINE = 40
    for i in range(min(K_REFINE, len(cands))):
        if time.time() > deadline:
            break
        cd = cands[i]
        score, p, own_g, opp_g, L, cap_stones, S, terr, bonus, saved_gain = cd
        b2, cap = place(b, p, ME)
        mystones, mylibs = flood(b2, p)
        L2 = len(mylibs)
        if L2 <= 1:
            f_after = 0.0
        elif L2 == 2:
            f_after = 0.15 if own_2lib_dead(b2, mystones, mylibs, deadline) else 0.75
        else:
            f_after = f_me(L2)
        own_before = sum(len(groups[g][1]) * fb_own(g) for g in own_g)
        own_delta = 10.0 * (len(mystones) * f_after - own_before - 1.0)
        gain = saved_gain
        for g in opp_g:
            color, st, lb = groups[g]
            sz = len(st)
            if len(lb) == 1:
                gain += 10.0 * sz * fb_opp(g) + 3.0 * sz + 1.0
            else:
                nl = len(lb) - 1
                if nl == 1:
                    fo_a = 0.0 if ladder_captured(b2, st, OPP, deadline) else 0.35
                else:
                    fo_a = f_opp(nl)
                gain += 10.0 * sz * (f_opp(len(lb)) - fo_a)
        terr2 = terr / max(0.3 + 0.7 * (0.0 if L == 1 else f_me(L)), 1e-6) * (0.3 + 0.7 * f_after)
        cd[0] = own_delta + gain + terr2 + bonus

    best = max(cands, key=lambda x: x[0])
    if best[0] < 0.25:
        return (0, 0)
    r, c = divmod(best[1], W)
    return (r, c)


def policy(me, opponent):
    try:
        me = [(int(r), int(c)) for (r, c) in me]
        opponent = [(int(r), int(c)) for (r, c) in opponent]
        mv = _policy(me, opponent)
        if mv == (0, 0):
            return (0, 0)
        r, c = mv
        occ = set(me) | set(opponent)
        if 1 <= r <= N and 1 <= c <= N and (r, c) not in occ:
            return (r, c)
        return _fallback(me, opponent)
    except Exception:
        try:
            return _fallback(me, opponent)
        except Exception:
            return (0, 0)
