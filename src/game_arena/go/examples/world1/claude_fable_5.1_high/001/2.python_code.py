
import random

N = 19
W = N + 2
EMPTY, ME, OPP, OFF = 0, 1, 2, 3
NBR = (-W, -1, 1, W)
T_OWN = 0.55

_POINTS = [r * W + c for r in range(1, N + 1) for c in range(1, N + 1)]


def _build_kernel():
    ks = {}
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            p = r * W + c
            lst = []
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    d = abs(dr) + abs(dc)
                    if d == 0 or d > 3:
                        continue
                    rr, cc = r + dr, c + dc
                    if 1 <= rr <= N and 1 <= cc <= N:
                        w = 1.0 if d == 1 else (0.6 if d == 2 else 0.3)
                        lst.append((rr * W + cc, w))
            ks[p] = lst
    return ks


_KERNEL = _build_kernel()

_PRIOR = {}
for _r in range(1, N + 1):
    for _c in range(1, N + 1):
        _line = min(_r, _c, N + 1 - _r, N + 1 - _c)
        _PRIOR[_r * W + _c] = {1: -5.0, 2: -2.5, 3: 2.0, 4: 2.5, 5: 0.5}.get(_line, -0.5)

_CORNERS = [((1, 6), (1, 6), (4, 4), [(3, 4), (4, 3)]),
            ((1, 6), (14, 19), (4, 16), [(3, 16), (4, 17)]),
            ((14, 19), (1, 6), (16, 4), [(16, 3), (17, 4)]),
            ((14, 19), (14, 19), (16, 16), [(16, 17), (17, 16)])]


class _BudgetExceeded(Exception):
    pass


_BUD = [0, 3000]


def _floodl(b, p):
    _BUD[0] += 1
    if _BUD[0] > _BUD[1]:
        raise _BudgetExceeded()
    color = b[p]
    stones = [p]
    seen = {p}
    libs = set()
    stack = [p]
    while stack:
        s = stack.pop()
        for d in NBR:
            n = s + d
            v = b[n]
            if v == EMPTY:
                libs.add(n)
            elif v == color and n not in seen:
                seen.add(n)
                stones.append(n)
                stack.append(n)
    return stones, libs


def _place(b, p, color):
    b[p] = color
    opp = 3 - color
    captured = 0
    for d in NBR:
        n = p + d
        if b[n] == opp:
            st, libs = _floodl(b, n)
            if not libs:
                for s in st:
                    b[s] = EMPTY
                captured += len(st)
    if captured == 0:
        st, libs = _floodl(b, p)
        if not libs:
            b[p] = EMPTY
            return -1
    return captured


def _ladder_attack(b, tp, attacker, depth):
    if depth > 80:
        return False
    stones, libs = _floodl(b, tp)
    n = len(libs)
    if n == 0:
        return True
    if n >= 3:
        return False
    if n == 1:
        return True
    for q in libs:
        b2 = b[:]
        if _place(b2, q, attacker) < 0:
            continue
        if _ladder_defend(b2, tp, attacker, depth + 1):
            return True
    return False


def _ladder_defend(b, tp, attacker, depth):
    if depth > 80:
        return False
    defender = 3 - attacker
    stones, libs = _floodl(b, tp)
    if len(libs) == 0:
        return True
    if len(libs) >= 2:
        return False
    q = next(iter(libs))
    seen = set()
    for s in stones:
        for d in NBR:
            n = s + d
            if b[n] == attacker and n not in seen:
                st2, l2 = _floodl(b, n)
                seen.update(st2)
                if len(l2) == 1:
                    b2 = b[:]
                    lib = next(iter(l2))
                    if _place(b2, lib, defender) >= 0:
                        st3, l3 = _floodl(b2, tp)
                        if len(l3) >= 3:
                            return False
                        if len(l3) == 2:
                            if not _ladder_attack(b2, tp, attacker, depth + 1):
                                return False
    b2 = b[:]
    if _place(b2, q, defender) < 0:
        return True
    st, l = _floodl(b2, tp)
    if len(l) >= 3:
        return False
    if len(l) <= 1:
        return True
    return _ladder_attack(b2, tp, attacker, depth + 1)


def ladder_attack(b, tp, attacker):
    try:
        return _ladder_attack(b, tp, attacker, 0)
    except _BudgetExceeded:
        return False


def ladder_defend(b, tp, attacker):
    try:
        return _ladder_defend(b, tp, attacker, 0)
    except _BudgetExceeded:
        return False


def _make_board(me, opponent):
    b = [OFF] * (W * W)
    for p in _POINTS:
        b[p] = EMPTY
    for (r, c) in me:
        if 1 <= r <= N and 1 <= c <= N:
            b[r * W + c] = ME
    for (r, c) in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            b[r * W + c] = OPP
    return b


def _owner(v):
    if v > T_OWN:
        return 1
    if v < -T_OWN:
        return -1
    return 0


def _policy(me, opponent):
    _BUD[0] = 0
    _BUD[1] = 3000
    b = _make_board(me, opponent)
    nstones = 0
    for p in _POINTS:
        if b[p] != EMPTY:
            nstones += 1
    s_open = max(0.0, 1.0 - nstones / 100.0)

    # groups
    gid = [-1] * (W * W)
    groups = []
    for p in _POINTS:
        if b[p] in (ME, OPP) and gid[p] == -1:
            stones, libs = _floodl(b, p)
            g = len(groups)
            for st in stones:
                gid[st] = g
            groups.append((b[p], stones, libs))
    _BUD[0] = 0

    # regions
    region_id = [-1] * (W * W)
    regions = []
    for p in _POINTS:
        if b[p] == EMPTY and region_id[p] == -1:
            rid = len(regions)
            region_id[p] = rid
            stack = [p]
            size = 0
            borders = set()
            while stack:
                s = stack.pop()
                size += 1
                for d in NBR:
                    n = s + d
                    v = b[n]
                    if v == EMPTY:
                        if region_id[n] == -1:
                            region_id[n] = rid
                            stack.append(n)
                    elif v == ME or v == OPP:
                        borders.add(v)
            regions.append((size, borders))

    # influence
    infl = [0.0] * (W * W)
    for p in _POINTS:
        v = b[p]
        if v == ME:
            for q, w in _KERNEL[p]:
                infl[q] += w
        elif v == OPP:
            for q, w in _KERNEL[p]:
                infl[q] -= w

    # corner bonuses
    corner_bonus = {}
    if s_open > 0:
        for (r0, r1), (c0, c1), star, others in _CORNERS:
            empty_box = True
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if b[r * W + c] != EMPTY:
                        empty_box = False
                        break
                if not empty_box:
                    break
            if empty_box:
                corner_bonus[star[0] * W + star[1]] = 4.0 * s_open
                for (r, c) in others:
                    corner_bonus[r * W + c] = 3.0 * s_open

    ladder_danger_cache = {}

    def own_ladder_danger(g):
        if g in ladder_danger_cache:
            return ladder_danger_cache[g]
        res = ladder_attack(b, groups[g][1][0], OPP)
        ladder_danger_cache[g] = res
        return res

    best_score = None
    best_p = None

    for p in _POINTS:
        if b[p] != EMPTY:
            continue
        own_adj = set()
        opp_adj = set()
        emp = []
        for d in NBR:
            n = p + d
            v = b[n]
            if v == EMPTY:
                emp.append(n)
            elif v == ME:
                own_adj.add(gid[n])
            elif v == OPP:
                opp_adj.add(gid[n])
        captured = [g for g in opp_adj if len(groups[g][2]) == 1]
        ncap = 0
        for g in captured:
            ncap += len(groups[g][1])
        newlibs = set(emp)
        for g in own_adj:
            newlibs |= groups[g][2]
        newlibs.discard(p)
        if captured:
            for g in captured:
                for st in groups[g][1]:
                    for d in NBR:
                        n = st + d
                        if n == p or (b[n] == ME and gid[n] in own_adj):
                            newlibs.add(st)
                            break
        nl = len(newlibs)
        if nl == 0:
            continue  # suicide
        new_size = 1
        for g in own_adj:
            new_size += len(groups[g][1])
        if ncap == 1 and not own_adj and nl == 1:
            continue  # possible ko shape - avoid
        rsize, rborders = regions[region_id[p]]
        if ME in rborders and OPP not in rborders and rsize < 25:
            continue  # own territory / eye
        if OPP in rborders and ME not in rborders and rsize < 8 and ncap == 0:
            continue  # hopeless tiny invasion

        score = 0.0
        if ncap > 0:
            score += 10.0 * ncap + 3.0
        if nl == 1:
            score -= 8.0 * new_size + 4.0
        elif nl == 2 and ncap == 0:
            score -= 2.5
        elif nl == 3 and ncap == 0:
            score -= 0.5

        # saving / strengthening own groups
        for g in own_adj:
            lg = len(groups[g][2])
            sz = len(groups[g][1])
            if lg == 1:
                if nl >= 3:
                    score += 10.0 * sz + 3.0
                elif nl == 2:
                    b2 = b[:]
                    if _place(b2, p, ME) >= 0:
                        if ladder_attack(b2, p, OPP):
                            score += 0.5
                        else:
                            score += 10.0 * sz + 1.0
            elif lg == 2:
                if nl >= 3:
                    if own_ladder_danger(g):
                        score += 8.0 * sz
                    else:
                        score += 0.5 * sz
            elif lg == 3 and nl >= 4:
                score += 0.2 * sz

        # pressure on opponent groups
        for g in opp_adj:
            if g in captured:
                continue
            lg = len(groups[g][2])
            sz = len(groups[g][1])
            if lg == 2:
                if nl >= 2:
                    b2 = b[:]
                    if _place(b2, p, ME) >= 0:
                        if ladder_defend(b2, groups[g][1][0], ME):
                            score += 9.0 * sz + 2.0
                        else:
                            score += 1.0
                else:
                    score -= 1.0
            elif lg == 3:
                score += 1.5 + 0.3 * sz
            elif lg == 4:
                score += 0.4
            else:
                score += 0.2

        # connection / cutting
        if len(own_adj) >= 2:
            score += 1.5 * (len(own_adj) - 1)
            for g in own_adj:
                if len(groups[g][2]) <= 2:
                    score += 2.0
        if len(opp_adj) >= 2:
            score += 1.0 * (len(opp_adj) - 1)

        score += 0.3 * min(nl, 5)

        # territory delta
        td = 1 - _owner(infl[p])
        for q, w in _KERNEL[p]:
            if b[q] == EMPTY:
                v = infl[q]
                td += _owner(v + w) - _owner(v)
        score += td

        # opening prior
        score += _PRIOR[p] * s_open
        score += corner_bonus.get(p, 0.0)

        # isolation penalty
        if infl[p] < -0.8:
            has_own = False
            for q, w in _KERNEL[p]:
                if w >= 0.6 and b[q] == ME:
                    has_own = True
                    break
            if not has_own:
                score += 2.0 * infl[p]

        score += random.random() * 0.05

        if best_score is None or score > best_score:
            best_score = score
            best_p = p

    if best_p is None:
        return (0, 0)
    return (best_p // W, best_p % W)


def _fallback(me, opponent):
    try:
        _BUD[0] = 0
        _BUD[1] = 10 ** 9
        b = _make_board(me, opponent)
        pts = _POINTS[:]
        random.shuffle(pts)
        for p in pts:
            if b[p] != EMPTY:
                continue
            b2 = b[:]
            cap = _place(b2, p, ME)
            if cap < 0:
                continue
            if cap == 1:
                st, libs = _floodl(b2, p)
                if len(st) == 1 and len(libs) == 1:
                    continue
            return (p // W, p % W)
    except Exception:
        pass
    return (0, 0)


def policy(me, opponent):
    try:
        mv = _policy(me, opponent)
        if mv == (0, 0):
            return mv
        r, c = mv
        if 1 <= r <= N and 1 <= c <= N:
            return (r, c)
        return _fallback(me, opponent)
    except Exception:
        return _fallback(me, opponent)
