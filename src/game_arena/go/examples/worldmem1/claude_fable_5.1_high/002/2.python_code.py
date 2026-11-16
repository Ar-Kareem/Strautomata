
import random

N = 19

_rng = random.Random(987654321)
Z = [[[0] * (N + 2) for _ in range(N + 2)] for _ in range(3)]
for _col in (1, 2):
    for _r in range(1, N + 1):
        for _c in range(1, N + 1):
            Z[_col][_r][_c] = _rng.getrandbits(64)

OFFS = []
for _dr in range(-3, 4):
    for _dc in range(-3, 4):
        _d = abs(_dr) + abs(_dc)
        if 0 < _d <= 3:
            OFFS.append((_dr, _dc, {1: 4, 2: 2, 3: 1}[_d]))

OPENING = {(4, 4): 12, (4, 16): 12, (16, 4): 12, (16, 16): 12,
           (3, 4): 10, (4, 3): 10, (3, 16): 10, (4, 17): 10,
           (16, 3): 10, (17, 4): 10, (16, 17): 10, (17, 16): 10,
           (4, 10): 7, (10, 4): 7, (16, 10): 7, (10, 16): 7,
           (10, 10): 4, (3, 10): 5, (10, 3): 5, (17, 10): 5, (10, 17): 5}


def neighbors(r, c):
    if r > 1:
        yield (r - 1, c)
    if r < N:
        yield (r + 1, c)
    if c > 1:
        yield (r, c - 1)
    if c < N:
        yield (r, c + 1)


def _policy(me, opponent, memory):
    board = [[0] * (N + 2) for _ in range(N + 2)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 2
    total = len(me) + len(opponent)
    if not isinstance(memory, dict) or total <= 1 or 'hist' not in memory:
        memory = {'hist': [], 'prev_opp': []}
    hist = set(memory.get('hist', []))
    prev_opp = set(tuple(p) for p in memory.get('prev_opp', []))
    new_opp = [tuple(p) for p in opponent if tuple(p) not in prev_opp]
    last_opp = new_opp[0] if len(new_opp) == 1 else None

    # groups
    gid = [[0] * (N + 2) for _ in range(N + 2)]
    groups = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] and gid[r][c] == 0:
                color = board[r][c]
                idx = len(groups) + 1
                gid[r][c] = idx
                stack = [(r, c)]
                stones = []
                libs = set()
                while stack:
                    p = stack.pop()
                    stones.append(p)
                    for n in neighbors(p[0], p[1]):
                        v = board[n[0]][n[1]]
                        if v == 0:
                            libs.add(n)
                        elif v == color and gid[n[0]][n[1]] == 0:
                            gid[n[0]][n[1]] = idx
                            stack.append(n)
                groups.append({'color': color, 'stones': stones, 'libs': libs})

    def libs_if_play(r, c, color):
        libs = set()
        mygs = set()
        caps = set()
        for (nr, nc) in neighbors(r, c):
            v = board[nr][nc]
            if v == 0:
                libs.add((nr, nc))
            elif v == color:
                mygs.add(gid[nr][nc])
            else:
                g = gid[nr][nc]
                if len(groups[g - 1]['libs']) == 1:
                    caps.add(g)
        for g in mygs:
            libs |= groups[g - 1]['libs']
        libs.discard((r, c))
        for g in caps:
            for s in groups[g - 1]['stones']:
                for n in neighbors(s[0], s[1]):
                    if n == (r, c) or (board[n[0]][n[1]] == color and gid[n[0]][n[1]] in mygs):
                        libs.add(s)
                        break
        return libs, mygs, caps

    # regions
    region_id = [[0] * (N + 2) for _ in range(N + 2)]
    regions = []
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0 and region_id[r][c] == 0:
                idx = len(regions) + 1
                region_id[r][c] = idx
                stack = [(r, c)]
                size = 0
                has_my = False
                has_opp = False
                while stack:
                    p = stack.pop()
                    size += 1
                    for n in neighbors(p[0], p[1]):
                        v = board[n[0]][n[1]]
                        if v == 0:
                            if region_id[n[0]][n[1]] == 0:
                                region_id[n[0]][n[1]] = idx
                                stack.append(n)
                        elif v == 1:
                            has_my = True
                        else:
                            has_opp = True
                regions.append((size, has_my, has_opp))

    # influence
    myinf = [[0] * (N + 2) for _ in range(N + 2)]
    opinf = [[0] * (N + 2) for _ in range(N + 2)]
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            v = board[r][c]
            if v:
                tgt = myinf if v == 1 else opinf
                for dr, dc, w in OFFS:
                    rr, cc = r + dr, c + dc
                    if 1 <= rr <= N and 1 <= cc <= N:
                        tgt[rr][cc] += w

    # urgent own groups (2 libs, opponent can kill)
    urgent = set()
    for gi, grp in enumerate(groups):
        if grp['color'] == 1 and len(grp['libs']) == 2:
            A, B = list(grp['libs'])
            for L1, L2 in ((A, B), (B, A)):
                ol, _, oc = libs_if_play(L1[0], L1[1], 2)
                if len(ol) <= 1 and not oc:
                    continue
                el, _, ec = libs_if_play(L2[0], L2[1], 1)
                el.discard(L1)
                if len(el) <= 1 and not ec:
                    urgent.add(gi + 1)
                    break

    cur_hash = 0
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c]:
                cur_hash ^= Z[board[r][c]][r][c]
    hist.add(cur_hash)
    early = total < 80

    best = None
    best_score = -1e9
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] != 0:
                continue
            libs, mygs, caps = libs_if_play(r, c, 1)
            nl = len(libs)
            if nl == 0:
                continue
            h = cur_hash ^ Z[1][r][c]
            ncap = 0
            for g in caps:
                for s in groups[g - 1]['stones']:
                    h ^= Z[2][s[0]][s[1]]
                    ncap += 1
            if h in hist:
                continue
            size_after = 1 + sum(len(groups[g - 1]['stones']) for g in mygs)
            s = 0.0
            if ncap:
                s += 10 * ncap + 12
            for g in mygs:
                grp = groups[g - 1]
                gl = len(grp['libs'])
                gs = len(grp['stones'])
                if gl == 1:
                    if nl >= 3 or ncap:
                        s += 8 * gs + 8
                    elif nl == 2:
                        s += 4 * gs + 2
                elif gl == 2:
                    if g in urgent:
                        if nl >= 3 or ncap:
                            s += 6 * gs + 6
                        elif nl == 2:
                            s += gs
                    else:
                        if nl >= 3:
                            s += min(12, 1.5 * gs + 1.5)
            if nl == 1:
                if ncap == 0:
                    s -= 30 + 3 * size_after
                elif ncap == 1:
                    s -= 6
            elif nl == 2 and ncap == 0:
                s -= 3 + 0.5 * size_after
            elif nl == 3:
                s -= 0.5
            oppgs = set()
            nmy = 0
            nopp = 0
            for (nr, nc) in neighbors(r, c):
                v = board[nr][nc]
                if v == 1:
                    nmy += 1
                elif v == 2:
                    nopp += 1
                    g = gid[nr][nc]
                    if g not in caps:
                        oppgs.add(g)
            for g in oppgs:
                grp = groups[g - 1]
                gl = len(grp['libs'])
                gs = len(grp['stones'])
                if gl == 2:
                    L = None
                    for x in grp['libs']:
                        if x != (r, c):
                            L = x
                    if L is None:
                        continue
                    if nl == 1:
                        e = 99
                    else:
                        el, _, ecaps = libs_if_play(L[0], L[1], 2)
                        el.discard((r, c))
                        e = len(el)
                    if e <= 1:
                        s += 8 * gs + 10
                    elif e == 2:
                        s += 1.5 * gs + 3
                    else:
                        s += 0.5 * gs + 1.5
                elif gl == 3:
                    s += min(6, 0.7 * gs + 0.5)
                else:
                    s += min(3, 0.2 * gs)
            # positional
            line = min(r, c, N + 1 - r, N + 1 - c)
            if early:
                lv = {1: -7, 2: -2, 3: 3, 4: 3, 5: 2}.get(line, 1)
            else:
                lv = {1: -2, 2: 0, 3: 1, 4: 1}.get(line, 0.5)
            mi = myinf[r][c]
            oi = opinf[r][c]
            if mi == 0 and oi == 0:
                s += lv + (2 if early else 0)
            else:
                s += lv * 0.5
                if mi > 0 and oi > 0:
                    s += 2.5 + min(3, 0.3 * min(mi, oi))
                d = mi - oi
                if d >= 8:
                    s -= 5
                elif d >= 4:
                    s -= 2
                if d <= -8:
                    s -= 4
                elif d <= -4:
                    s -= 1.5
            size, has_my, has_opp = regions[region_id[r][c] - 1]
            if has_my and not has_opp:
                if size <= 2:
                    s -= 30
                elif size <= 6:
                    s -= 14
                elif size <= 12:
                    s -= 5
                else:
                    s -= 1
            elif has_opp and not has_my:
                if size <= 4:
                    s -= 20
                elif size <= 8:
                    s -= 10
                elif size <= 14:
                    s -= 4
            if total < 100 and (r, c) in OPENING:
                empty_area = True
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        rr, cc = r + dr, c + dc
                        if 1 <= rr <= N and 1 <= cc <= N and board[rr][cc]:
                            empty_area = False
                            break
                    if not empty_area:
                        break
                if empty_area:
                    s += OPENING[(r, c)]
            if nmy >= 3 and ncap == 0:
                s -= 3
            elif nmy >= 1:
                s += 1
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r + dr, c + dc
                if 1 <= rr <= N and 1 <= cc <= N and board[rr][cc] == 1:
                    s += 0.4
            if last_opp is not None:
                dist = max(abs(last_opp[0] - r), abs(last_opp[1] - c))
                if dist <= 1:
                    s += 3
                elif dist <= 2:
                    s += 2
                elif dist <= 4:
                    s += 1
            s += random.random() * 0.3
            if s > best_score:
                best_score = s
                best = (r, c, h)

    memory['prev_opp'] = [tuple(p) for p in opponent]
    if best is None or best_score < -1:
        memory['hist'] = list(hist)
        return (0, 0), memory
    hist.add(best[2])
    memory['hist'] = list(hist)
    return (best[0], best[1]), memory


def _fallback(me, opponent, memory):
    board = [[0] * (N + 2) for _ in range(N + 2)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r][c] = 2
    best = None
    best_e = -1
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            if board[r][c] == 0:
                e = 0
                for n in neighbors(r, c):
                    if board[n[0]][n[1]] == 0:
                        e += 1
                if e > best_e:
                    best_e = e
                    best = (r, c)
    if best is None or best_e == 0:
        return (0, 0), {}
    return best, {}


def policy(me, opponent, memory):
    try:
        return _policy(me, opponent, memory if isinstance(memory, dict) else {})
    except Exception:
        try:
            return _fallback(me, opponent, memory)
        except Exception:
            return (0, 0), {}
