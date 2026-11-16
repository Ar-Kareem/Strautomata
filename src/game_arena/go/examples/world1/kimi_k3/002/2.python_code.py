
from collections import deque

N = 19
NN = N * N
INF = 10 ** 9
EVAL_LIMIT = 160
# value of being on line (distance to nearest edge) 0..9 ; 3rd/4th line are best early
EV = (-7.0, -3.0, 2.0, 4.0, 1.0, 0.0, 0.0, -1.0, -1.0, -1.0)

NBR = []
for _r in range(N):
    for _c in range(N):
        _l = []
        if _r > 0:
            _l.append((_r - 1) * N + _c)
        if _r + 1 < N:
            _l.append((_r + 1) * N + _c)
        if _c > 0:
            _l.append(_r * N + _c - 1)
        if _c + 1 < N:
            _l.append(_r * N + _c + 1)
        NBR.append(_l)


def _build_prior():
    P = [0.0] * NN
    for r in range(N):
        er = min(r, N - 1 - r)
        vr = EV[er]
        for c in range(N):
            ec = min(c, N - 1 - c)
            v = vr + EV[ec]
            lo = er if er < ec else ec
            hi = ec if er < ec else er
            if lo >= 2 and hi <= 4:  # corner 3x3 block (3-3 .. 5-5 points)
                v += 6 - (abs(er - 3) + abs(ec - 3))
            if (er == 3 and ec == 9) or (er == 9 and ec == 3):  # side star points
                v += 4.0
            P[r * N + c] = v
    return P


PRIOR = _build_prior()


def _analyze(b):
    gid = [-1] * NN
    groups = []  # (color, stones[list idx], liberties[set idx])
    for i, v in enumerate(b):
        if v and gid[i] < 0:
            g = len(groups)
            gid[i] = g
            stack = [i]
            stones = []
            libs = set()
            while stack:
                u = stack.pop()
                stones.append(u)
                for w in NBR[u]:
                    vw = b[w]
                    if vw == 0:
                        libs.add(w)
                    elif vw == v and gid[w] < 0:
                        gid[w] = g
                        stack.append(w)
            groups.append((v, stones, libs))
    return groups, gid


def _dists(b, color):
    """Multi-source BFS distance to nearest `color` stone, not crossing opponent."""
    block = 3 - color
    dist = [-1] * NN
    dq = deque()
    for i, v in enumerate(b):
        if v == color:
            dist[i] = 0
            dq.append(i)
    while dq:
        u = dq.popleft()
        d = dist[u] + 1
        for w in NBR[u]:
            if dist[w] < 0 and b[w] != block:
                dist[w] = d
                dq.append(w)
    return dist


def _evaluate(b):
    groups, _ = _analyze(b)
    my_st = opp_st = 0
    safe = 0.0
    for col, stones, libs in groups:
        sz = len(stones)
        l = len(libs)
        if col == 1:
            my_st += sz
            if l == 1:
                safe -= 5.0 * sz + 3.0
            elif l == 2:
                safe -= 0.7 * sz
        else:
            opp_st += sz
            if l == 1:
                safe += 0.9 * sz + 0.5   # only a threat: opponent moves next
            elif l == 2:
                safe += 0.4 * sz
    d1 = _dists(b, 1)
    d2 = _dists(b, 2)
    my_t = opp_t = 0
    for i, v in enumerate(b):
        if v == 0:
            x = d1[i] if d1[i] >= 0 else INF
            y = d2[i] if d2[i] >= 0 else INF
            if x < y:
                my_t += 1
            elif y < x:
                opp_t += 1
    return float((my_st - opp_st) + (my_t - opp_t)) + safe


def _features(b, gid, groups):
    feats = [None] * NN
    for i, v in enumerate(b):
        if v != 0:
            continue
        my = set()
        op = set()
        emp = 0
        for j in NBR[i]:
            w = b[j]
            if w == 0:
                emp += 1
            elif w == 1:
                my.add(gid[j])
            else:
                op.add(gid[j])
        cap = 0
        two = 0
        for g in op:
            l = len(groups[g][2])
            sz = len(groups[g][1])
            if l == 1:
                cap += sz
            elif l == 2:
                two += sz
        save = 0
        my2 = 0
        libs_count = emp
        for g in my:
            l = len(groups[g][2])
            sz = len(groups[g][1])
            libs_count += l - 1
            if l == 1:
                save += sz
            elif l == 2:
                my2 += sz
        legal = (cap > 0) or (libs_count > 0)
        feats[i] = {
            'legal': legal, 'cap': cap, 'two': two, 'save': save, 'my2': my2,
            'nmy': len(my), 'nopp': len(op), 'est': libs_count + cap,
            'op': op, 'my': my,
        }
    return feats


def _prior_weight(n):
    if n < 6:
        return 1.0
    if n < 20:
        return 0.8
    if n < 50:
        return 0.5
    if n < 120:
        return 0.28
    return 0.15


def _policy(me, opponent):
    b = [0] * NN
    for r, c in me:
        r = int(r); c = int(c)
        if 1 <= r <= N and 1 <= c <= N:
            b[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        r = int(r); c = int(c)
        if 1 <= r <= N and 1 <= c <= N:
            b[(r - 1) * N + (c - 1)] = 2

    groups, gid = _analyze(b)
    feats = _features(b, gid, groups)
    legal_idx = [i for i in range(NN) if feats[i] is not None and feats[i]['legal']]
    if not legal_idx:
        return (0, 0)

    nstones = len(me) + len(opponent)
    pw = _prior_weight(nstones)

    if len(legal_idx) > EVAL_LIMIT:
        d1 = _dists(b, 1)
        d2 = _dists(b, 2)

        def cheap(i):
            f = feats[i]
            s = 50.0 * f['cap'] + 60.0 * f['save'] + 14.0 * f['two'] + 3.0 * f['my2']
            if f['nmy'] > 1:
                s += 12.0 * (f['nmy'] - 1)
            if f['nopp'] > 1:
                s += 8.0 * (f['nopp'] - 1)
            s += 2.0 * min(f['est'], 6)
            if f['cap'] == 0 and f['nmy'] >= 1 and f['est'] <= 1:
                s -= 25.0
            s += PRIOR[i]
            do = d2[i]
            if do >= 0:
                if do <= 1:
                    s += 7.0
                elif do == 2:
                    s += 5.0
                elif do == 3:
                    s += 2.0
            dm = d1[i]
            if dm >= 0:
                if dm <= 2:
                    s += 2.0
                elif dm > 4 and (do < 0 or do > 4):
                    s -= 4.0
            return s

        scored = sorted(legal_idx, key=cheap, reverse=True)
        sel = set(scored[:EVAL_LIMIT])
        for i in legal_idx:  # never drop a forcing move
            f = feats[i]
            if f['cap'] > 0 or f['save'] > 0:
                sel.add(i)
        selected = list(sel)
    else:
        selected = legal_idx

    best = -1
    best_sc = -1e18
    for i in selected:
        f = feats[i]
        # simulate
        b[i] = 1
        removed = []
        for g in f['op']:
            if len(groups[g][2]) == 1:
                for sidx in groups[g][1]:
                    if b[sidx] == 2:
                        b[sidx] = 0
                        removed.append(sidx)
        base = _evaluate(b)
        for sidx in removed:
            b[sidx] = 2
        b[i] = 0

        sc = base + PRIOR[i] * pw
        if f['cap']:
            sc += 2.0 * f['cap']
        if f['save']:
            sc += 0.5 * f['save']
        if f['two']:
            sc += 0.8 * f['two']
        if f['my2']:
            sc += 0.5 * f['my2']
        if f['nmy'] > 1:
            sc += 1.0 * (f['nmy'] - 1)
        if f['nopp'] > 1:
            sc += 0.6 * (f['nopp'] - 1)
        if f['cap'] == 0 and f['nmy'] >= 1 and f['est'] <= 1:
            sc -= 25.0

        if sc > best_sc:
            best_sc = sc
            best = i

    if best < 0:
        return (0, 0)
    return (best // N + 1, best % N + 1)


def policy(me, opponent):
    try:
        return _policy(me, opponent)
    except Exception:
        try:
            b = [0] * NN
            for r, c in me:
                r = int(r); c = int(c)
                if 1 <= r <= N and 1 <= c <= N:
                    b[(r - 1) * N + (c - 1)] = 1
            for r, c in opponent:
                r = int(r); c = int(c)
                if 1 <= r <= N and 1 <= c <= N:
                    b[(r - 1) * N + (c - 1)] = 2
            order = [3 * N + 3, 3 * N + 15, 15 * N + 3, 15 * N + 15, 9 * N + 9]
            order.extend(range(NN))
            seen = set()
            for i in order:
                if i in seen:
                    continue
                seen.add(i)
                if b[i] == 0:
                    for j in NBR[i]:
                        if b[j] == 0:  # has a liberty -> definitely legal
                            return (i // N + 1, i % N + 1)
        except Exception:
            pass
        return (0, 0)
