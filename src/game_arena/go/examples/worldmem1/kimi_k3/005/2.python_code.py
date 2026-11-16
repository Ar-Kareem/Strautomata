
import time
import random

N = 19
NN = N * N
ME = 1
OP = 2


def _build_tables():
    NB, DG, LINE, NEAR, KEYB = [], [], [], [], []
    for i in range(NN):
        r, c = divmod(i, N)
        ns = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        NB.append(tuple(ns))
        ds = []
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ds.append(rr * N + cc)
        DG.append(tuple(ds))
        LINE.append(min(r, c, N - 1 - r, N - 1 - c))
        lst = []
        for dr in (-2, -1, 0, 1, 2):
            for dc in (-2, -1, 0, 1, 2):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    lst.append(rr * N + cc)
        NEAR.append(tuple(lst))
        d1 = min(r, N - 1 - r)
        d2 = min(c, N - 1 - c)
        p = (d1, d2) if d1 <= d2 else (d2, d1)
        kb = 0.0
        if p == (3, 3):
            kb = 3.0          # 4-4
        elif p == (2, 3):
            kb = 2.6          # 3-4
        elif p == (2, 4) or p == (3, 4):
            kb = 2.0          # 3-5 / 4-5
        elif p == (2, 2):
            kb = 1.8          # 3-3
        elif (d1 == 3 and c == 9) or (d2 == 3 and r == 9):
            kb = 1.6          # side star points
        elif r == 9 and c == 9:
            kb = 0.9          # tengen
        KEYB.append(kb)
    return NB, DG, LINE, NEAR, KEYB


NB, DG, LINE, NEAR, KEYB = _build_tables()
KEY_PTS = tuple(i for i in range(NN) if KEYB[i] > 0.0)


def group_libs(bd, s, col):
    stack = [s]
    seen = {s}
    stones = [s]
    libs = set()
    nbg = NB
    b = bd
    while stack:
        x = stack.pop()
        for n in nbg[x]:
            v = b[n]
            if v == 0:
                libs.add(n)
            elif v == col and n not in seen:
                seen.add(n)
                stones.append(n)
                stack.append(n)
    return stones, libs


def eval_move(bd, m, my, op, past, stage):
    if bd[m] != 0:
        return None
    nbm = NB[m]
    own_pre = []
    seen_rep = set()
    opp_adj = 0
    all_own = True
    all_opp = True
    for n in nbm:
        v = bd[n]
        if v == my:
            all_opp = False
            st, lb = group_libs(bd, n, my)
            rep = min(st)
            if rep not in seen_rep:
                seen_rep.add(rep)
                own_pre.append((len(st), len(lb)))
        elif v == op:
            all_own = False
            opp_adj += 1
        else:
            all_own = False
            all_opp = False

    # Skip filling a solid true eye of our own unless it saves/connects.
    if all_own:
        solid = True
        for d in DG[m]:
            if bd[d] != my:
                solid = False
                break
        if solid and len(own_pre) <= 1:
            ok_skip = True
            for _, nlb in own_pre:
                if nlb == 1:
                    ok_skip = False
                    break
            if ok_skip:
                return None

    bd[m] = my
    captured = []
    checked = set()
    for n in nbm:
        if bd[n] == op and n not in checked:
            st, lb = group_libs(bd, n, op)
            checked.update(st)
            if not lb:
                for x in st:
                    bd[x] = 0
                captured.extend(st)
    ost, olb = group_libs(bd, m, my)
    ol = len(olb)
    osz = len(ost)
    if ol == 0:  # suicide
        for x in captured:
            bd[x] = op
        bd[m] = 0
        return None
    if bytes(bd) in past:  # ko / superko
        for x in captured:
            bd[x] = op
        bd[m] = 0
        return None

    capn = len(captured)
    score = 0.0
    if capn:
        score += 15.0 * capn
    if ol == 1:
        if osz == 1 and capn >= 1:
            score += 1.0          # safe ko capture (recapture would be illegal ko)
        else:
            score -= 16.0 * osz   # self-atari / snapback risk
    elif ol == 2:
        pen = 0.5 * osz
        score -= 4.0 if pen > 4.0 else pen

    # Opponent groups we just attacked.
    checked2 = set()
    for n in nbm:
        if bd[n] == op and n not in checked2:
            st, lb = group_libs(bd, n, op)
            checked2.update(st)
            nl = len(lb)
            if nl == 1:
                L = next(iter(lb))
                bd[L] = op
                cap2 = []
                checked3 = set()
                for nn in NB[L]:
                    if bd[nn] == my and nn not in checked3:
                        st2, lb2 = group_libs(bd, nn, my)
                        checked3.update(st2)
                        if not lb2:
                            for x in st2:
                                bd[x] = 0
                            cap2.extend(st2)
                st3, lb3 = group_libs(bd, L, op)
                after = len(lb3)
                for x in cap2:
                    bd[x] = my
                bd[L] = 0
                if cap2:
                    score -= 15.0 * len(cap2)   # opponent captures in reply
                if after >= 3:
                    score += 0.5 * len(st)      # failed ladder
                else:
                    score += 3.0 + 3.0 * len(st)  # working capture
            elif nl == 2:
                score += 0.4 * len(st)

    if ol >= 2:
        for size, nlb in own_pre:
            if nlb == 1:
                score += 12.0 * size + 4.0      # saving a group in atari
    if len(own_pre) >= 2:
        score += 2.0 * (len(own_pre) - 1)       # connection
    if opp_adj >= 2:
        score += 1.0 * (opp_adj - 1)            # cut
    if capn == 0 and all_own:
        score -= 10.0                           # filling own territory/eye
    if capn == 0 and all_opp:
        score -= 6.0                            # deep invasion of solid area
    if opp_adj >= 3 and capn == 0:
        score -= 3.0
    if opp_adj:
        score += 0.5                            # contact fight
    score += 0.05 * (ol if ol < 8 else 8)
    if stage > 0.0:
        score += KEYB[m] * stage
        ln = LINE[m]
        if ln == 2 or ln == 3:
            score += 0.8 * stage
        elif ln <= 1:
            score -= 1.2 * stage
    score += 0.4
    score += random.random() * 0.15

    for x in captured:
        bd[x] = op
    bd[m] = 0
    return score


def policy(me, opponent, memory):
    t0 = time.time()
    bd = [0] * NN
    cnt_me = 0
    for rc in me:
        r, c = rc
        if 1 <= r <= N and 1 <= c <= N:
            bd[(r - 1) * N + (c - 1)] = ME
            cnt_me += 1
    cnt_op = 0
    for rc in opponent:
        r, c = rc
        if 1 <= r <= N and 1 <= c <= N:
            bd[(r - 1) * N + (c - 1)] = OP
            cnt_op += 1
    total = cnt_me + cnt_op
    stage = 1.0 - total / 55.0
    if stage < 0.0:
        stage = 0.0

    if memory is None:
        memory = {}
    past = memory.get('h')
    prev_n = memory.get('n', -1)
    if past is None or total <= 1 or total + 20 < prev_n:
        past = set()          # new game: reset position history
    past.add(bytes(bd))

    cand = set(KEY_PTS)
    for idx in range(NN):
        if bd[idx]:
            for j in NEAR[idx]:
                if bd[j] == 0:
                    cand.add(j)

    best = -1
    bs = -1e18
    cnt = 0
    for m in cand:
        if bd[m]:
            continue
        sc = eval_move(bd, m, ME, OP, past, stage)
        if sc is not None and sc > bs:
            bs = sc
            best = m
        cnt += 1
        if (cnt & 31) == 0 and time.time() - t0 > 0.75:
            break

    memory = {'h': past, 'n': total}
    if best < 0 or bs <= 0.25:
        return (0, 0), memory

    bd[best] = ME
    checked = set()
    for n in NB[best]:
        if bd[n] == OP and n not in checked:
            st, lb = group_libs(bd, n, OP)
            checked.update(st)
            if not lb:
                for x in st:
                    bd[x] = 0
    past.add(bytes(bd))
    return (best // N + 1, best % N + 1), memory
