
import time, math, random

N = 19
NN = N * N

NEIGH = [None] * NN
for i in range(NN):
    r, c = divmod(i, N)
    lst = []
    if r > 0: lst.append(i - N)
    if r < N - 1: lst.append(i + N)
    if c > 0: lst.append(i - 1)
    if c < N - 1: lst.append(i + 1)
    NEIGH[i] = lst

LINE = [0] * NN
for i in range(NN):
    r, c = divmod(i, N)
    LINE[i] = min(r + 1, N - r, c + 1, N - c)

NEAR = [None] * NN
for i in range(NN):
    r, c = divmod(i, N)
    lst = []
    for dr in range(-4, 5):
        rr = r + dr
        if rr < 0 or rr >= N:
            continue
        for dc in range(-4, 5):
            d = abs(dr) + abs(dc)
            if d == 0 or d > 4:
                continue
            cc = c + dc
            if cc < 0 or cc >= N:
                continue
            lst.append((rr * N + cc, d))
    NEAR[i] = lst

WD = [0.0, 8.0, 4.0, 2.0, 1.0]
LINEPRIOR = {1: -3.0, 2: -1.0, 3: 2.0, 4: 2.5, 5: 1.0}


def _idx(r, c):
    return (r - 1) * N + (c - 1)


CORNER_REGIONS = []
for (r0, c0, sr, sc) in [(1, 1, 1, 1), (1, 19, 1, -1), (19, 1, -1, 1), (19, 19, -1, -1)]:
    region = set()
    for dr in range(9):
        for dc in range(9):
            region.add(_idx(r0 + sr * dr, c0 + sc * dc))
    pts = {_idx(r0 + sr * 3, c0 + sc * 3): 6.0,
           _idx(r0 + sr * 2, c0 + sc * 3): 5.5,
           _idx(r0 + sr * 3, c0 + sc * 2): 5.5}
    CORNER_REGIONS.append((region, pts))

LAST = None


def flood(board, start):
    color = board[start]
    seen = {start}
    stack = [start]
    libs = set()
    while stack:
        s = stack.pop()
        for n in NEIGH[s]:
            b = board[n]
            if b == 0:
                libs.add(n)
            elif b == color and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen, libs


def sim_play(board, p, color):
    board[p] = color
    opp = 3 - color
    captured = []
    for n in NEIGH[p]:
        if board[n] == opp:
            stones, libs = flood(board, n)
            if not libs:
                for s in stones:
                    board[s] = 0
                captured.extend(stones)
    return captured


def analyze(board):
    gid = [-1] * NN
    groups = []
    for i in range(NN):
        if board[i] and gid[i] < 0:
            color = board[i]
            g = len(groups)
            gid[i] = g
            stack = [i]
            stones = []
            libs = set()
            while stack:
                s = stack.pop()
                stones.append(s)
                for n in NEIGH[s]:
                    b = board[n]
                    if b == 0:
                        libs.add(n)
                    elif b == color and gid[n] < 0:
                        gid[n] = g
                        stack.append(n)
            groups.append((color, stones, libs))
    return gid, groups


def escapes(board, t, budget, depth=0):
    # target group at t has (expected) 1 liberty; defender (its color) to move.
    if budget[0] <= 0 or depth > 50:
        return True
    budget[0] -= 1
    color = board[t]
    if color == 0:
        return False
    opp = 3 - color
    stones, libs = flood(board, t)
    if len(libs) >= 2:
        return True
    if len(libs) == 0:
        return False
    seen = set()
    for s in stones:
        for n in NEIGH[s]:
            if board[n] == opp and n not in seen:
                st, lb = flood(board, n)
                seen |= st
                if len(lb) == 1:
                    return True
    lib = next(iter(libs))
    return extension_works(board, t, lib, color, budget, depth)


def extension_works(board, t, lib, color, budget, depth):
    opp = 3 - color
    b2 = board[:]
    sim_play(b2, lib, color)
    st2, lb2 = flood(b2, lib)
    if len(lb2) >= 3:
        return True
    if len(lb2) <= 1:
        return False
    for a in list(lb2):
        b3 = b2[:]
        sim_play(b3, a, opp)
        sa, la = flood(b3, a)
        if len(la) <= 1:
            continue
        if not escapes(b3, t, budget, depth + 1):
            return False
    return True


def fallback(board):
    for p in range(NN):
        if board[p] == 0:
            for n in NEIGH[p]:
                if board[n] == 0:
                    return p
    return None


def choose(board, start, ko_point, ko_stone, strict_ko, last_opp):
    gid, groups = analyze(board)
    total = 0
    for x in board:
        if x:
            total += 1

    # influence map
    inf = [0.0] * NN
    for color, stones, libs in groups:
        nl = len(libs)
        w = 1.0 if nl >= 3 else (0.6 if nl == 2 else 0.25)
        sgn = w if color == 1 else -w
        for s in stones:
            for q, d in NEAR[s]:
                if board[q] == 0:
                    inf[q] += sgn * WD[d]

    # ladder reading on opponent groups with 2 liberties
    ladder_kill = {}
    ladder_done = set()
    opp2 = [i for i, g in enumerate(groups) if g[0] == 2 and len(g[2]) == 2]
    opp2.sort(key=lambda i: -len(groups[i][1]))
    for i in opp2:
        if time.time() - start > 0.30:
            break
        color, stones, libs = groups[i]
        ladder_done.add(i)
        for lib in libs:
            b2 = board[:]
            sim_play(b2, lib, 1)
            s, l = flood(b2, lib)
            if len(l) <= 1:
                continue
            if not escapes(b2, stones[0], [80]):
                ladder_kill[(i, lib)] = True

    # own groups: atari extension viability, and 2-lib ladder threats
    save_ext = {}
    threatened = set()
    own_groups = [i for i, g in enumerate(groups) if g[0] == 1 and len(g[2]) <= 2]
    own_groups.sort(key=lambda i: -len(groups[i][1]))
    for i in own_groups:
        if time.time() - start > 0.42:
            break
        color, stones, libs = groups[i]
        if len(libs) == 1:
            lib = next(iter(libs))
            save_ext[i] = extension_works(board, stones[0], lib, 1, [80], 0)
        else:
            for a in libs:
                b2 = board[:]
                sim_play(b2, a, 2)
                s, l = flood(b2, a)
                if len(l) <= 1:
                    continue
                if not escapes(b2, stones[0], [80]):
                    threatened.add(i)
                    break

    corner_bonus = {}
    if total < 40:
        for region, pts in CORNER_REGIONS:
            empty = True
            for q in region:
                if board[q]:
                    empty = False
                    break
            if empty:
                corner_bonus.update(pts)

    local_bonus = {}
    if last_opp is not None:
        for q, d in NEAR[last_opp]:
            local_bonus[q] = 1.2 if d <= 2 else 0.5

    best = None
    best_score = -1e9
    for p in range(NN):
        if board[p] != 0:
            continue
        own_g = set()
        opp_g = set()
        empties = []
        for n in NEIGH[p]:
            b = board[n]
            if b == 0:
                empties.append(n)
            elif b == 1:
                own_g.add(gid[n])
            else:
                opp_g.add(gid[n])
        captured_groups = [g for g in opp_g if len(groups[g][2]) == 1]
        new_libs = set(empties)
        merged_size = 1
        for g in own_g:
            new_libs |= groups[g][2]
            merged_size += len(groups[g][1])
        new_libs.discard(p)
        ncap = 0
        if captured_groups:
            merged = set([p])
            for g in own_g:
                merged.update(groups[g][1])
            for g in captured_groups:
                for s in groups[g][1]:
                    ncap += 1
                    for n in NEIGH[s]:
                        if n in merged:
                            new_libs.add(s)
                            break
        nl = len(new_libs)
        if nl == 0:
            continue
        # ko handling
        if strict_ko:
            if ncap == 1 and merged_size == 1 and nl == 1:
                continue
        else:
            if ko_point is not None and p == ko_point and ncap == 1:
                cg = captured_groups[0]
                if groups[cg][1][0] == ko_stone:
                    continue

        score = 0.0
        if not empties and not opp_g:
            score -= 50.0

        cap_set = set(captured_groups)
        for g in captured_groups:
            sz = len(groups[g][1])
            score += 20.0 + 10.0 * sz
            rescued = set()
            for s in groups[g][1]:
                for n in NEIGH[s]:
                    if board[n] == 1:
                        rescued.add(gid[n])
            for h in rescued:
                if len(groups[h][2]) == 1 and h not in own_g:
                    score += 8.0 + 5.0 * len(groups[h][1])

        if nl == 1:
            if ncap == 0:
                score -= 30.0 + 5.0 * merged_size
            elif merged_size > 1:
                score -= 5.0 + 4.0 * merged_size
        elif nl == 2 and ncap == 0:
            score -= 3.0

        for g in own_g:
            glibs = len(groups[g][2])
            sz = len(groups[g][1])
            if glibs == 1:
                if nl >= 3 or ncap > 0:
                    score += 10.0 + 6.0 * sz
                elif nl == 2:
                    if save_ext.get(g, False):
                        score += 10.0 + 6.0 * sz
                    else:
                        score += 1.0
            elif glibs == 2:
                if g in threatened and nl >= 3:
                    score += 6.0 + 3.0 * sz
                elif nl >= 3:
                    score += 1.0 + 0.3 * sz
            if nl < glibs and ncap == 0:
                score -= 2.0
        if len(own_g) >= 2:
            score += 2.5
        if len(opp_g) >= 2:
            score += 1.5

        atari_count = 0
        for g in opp_g:
            if g in cap_set:
                continue
            olibs = len(groups[g][2])
            sz = len(groups[g][1])
            after = olibs - 1
            if after == 1:
                atari_count += 1
                if ladder_kill.get((g, p)):
                    score += 14.0 + 6.0 * sz
                elif g in ladder_done:
                    score += 2.0 + 0.5 * sz
                else:
                    if time.time() - start < 0.7:
                        b2 = board[:]
                        sim_play(b2, p, 1)
                        rem = [q for q in groups[g][2] if q != p]
                        if rem and b2[groups[g][1][0]] == 2:
                            sim_play(b2, rem[0], 2)
                            s2, l2 = flood(b2, rem[0])
                            if len(l2) <= 1:
                                score += 14.0 + 6.0 * sz
                            elif len(l2) == 2:
                                score += 4.0 + 1.0 * sz
                            else:
                                score += 2.0 + 0.5 * sz
                        else:
                            score += 2.0 + 0.5 * sz
                    else:
                        score += 2.0 + 0.5 * sz
            elif after == 2:
                score += 1.5 + 0.3 * sz
            elif after == 3:
                score += 0.5
        if atari_count >= 2 and nl >= 2:
            score += 8.0

        own_p = math.tanh(inf[p] / 10.0)
        contest = 1.0 - abs(own_p)
        if own_p < -0.75 and ncap == 0:
            score -= 3.0

        gain = 0.0
        near = NEAR[p]
        empt = 0
        for q, d in near:
            if board[q] == 0:
                empt += 1
                v = inf[q]
                gain += math.tanh((v + WD[d]) / 6.0) - math.tanh(v / 6.0)
        score += gain * 0.9
        openness = empt / float(len(near)) if near else 0.0

        lp = LINEPRIOR.get(LINE[p], 0.0)
        if total < 30 and LINE[p] >= 6:
            lp -= 1.5
        score += lp * contest * openness
        score += min(nl, 4) * 0.5 * contest
        score += corner_bonus.get(p, 0.0)
        score += local_bonus.get(p, 0.0) * contest
        score += random.random() * 0.01

        if score > best_score:
            best_score = score
            best = p

    if best is None or best_score < 0.3:
        return None
    return best


def policy(me, opponent):
    global LAST
    start = time.time()
    board = [0] * NN
    for rc in me:
        r, c = rc[0], rc[1]
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + c - 1] = 1
    for rc in opponent:
        r, c = rc[0], rc[1]
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + c - 1] = 2

    ko_point = None
    ko_stone = None
    strict_ko = True
    last_opp = None
    try:
        if LAST is not None:
            added_opp = []
            removed_own = []
            other = False
            for i in range(NN):
                a = LAST[i]
                b = board[i]
                if a != b:
                    if a == 0 and b == 2:
                        added_opp.append(i)
                    elif a == 1 and b == 0:
                        removed_own.append(i)
                    else:
                        other = True
                        break
            if not other:
                if len(added_opp) == 1:
                    strict_ko = False
                    last_opp = added_opp[0]
                    if len(removed_own) == 1:
                        ko_point = removed_own[0]
                        ko_stone = added_opp[0]
                elif len(added_opp) == 0 and len(removed_own) == 0:
                    strict_ko = False
    except Exception:
        strict_ko = True

    move = None
    try:
        move = choose(board, start, ko_point, ko_stone, strict_ko, last_opp)
    except Exception:
        move = fallback(board)

    nb = board[:]
    if move is None:
        LAST = nb
        return (0, 0)
    try:
        sim_play(nb, move, 1)
    except Exception:
        pass
    LAST = nb
    return (move // N + 1, move % N + 1)
