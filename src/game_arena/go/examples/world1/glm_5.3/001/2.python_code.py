
# Go policy: tactical reading + 2-ply search with liberty/eye/influence evaluation.
# Fully self-contained; always returns a legal move (verified) or (0,0) to pass.
import time
from collections import deque

S = 21
NS = S * S
D4 = (-21, 21, -1, 1)
DD = (-22, -20, 20, 22)
INTERIOR = tuple(r * S + c for r in range(1, 20) for c in range(1, 20))
CENTER_ORDER = tuple(sorted(INTERIOR, key=lambda i: abs(i // S - 10) + abs(i % S - 10)))

STAR = ((10, 10), (4, 4), (4, 10), (4, 16), (10, 4), (10, 16), (16, 4), (16, 10), (16, 16))
OPEN_EXTRA = ((3, 4), (4, 3), (17, 4), (4, 17), (16, 3), (3, 16), (17, 16), (16, 17),
              (10, 3), (3, 10), (10, 17), (17, 10))
OPEN_PTS = tuple(r * S + c for (r, c) in (STAR + OPEN_EXTRA))

INF_W = 0.38

_GID = [0] * NS
_GIDG = [0] * NS
_gen = 0
LBUDGET = [0]


def analyze(board):
    """All groups as (color, stones, liberties-set)."""
    global _gen
    _gen += 1
    g = _gen
    groups = []
    gidg = _GIDG
    gid = _GID
    for i in INTERIOR:
        c = board[i]
        if c and gidg[i] != g:
            gi = len(groups)
            stones = [i]
            libs = set()
            stack = [i]
            gidg[i] = g
            gid[i] = gi
            while stack:
                p = stack.pop()
                for d in D4:
                    n = p + d
                    v = board[n]
                    if v == 0:
                        libs.add(n)
                    elif v == c and gidg[n] != g:
                        gidg[n] = g
                        gid[n] = gi
                        stones.append(n)
                        stack.append(n)
            groups.append((c, stones, libs))
    return groups


def _libs_of(board, start):
    c = board[start]
    seen = set()
    libs = set()
    stack = [start]
    seen.add(start)
    while stack:
        p = stack.pop()
        for d in D4:
            n = p + d
            v = board[n]
            if v == 0:
                libs.add(n)
            elif v == c and n not in seen:
                seen.add(n)
                stack.append(n)
    return libs


def _remove_group(board, start):
    c = board[start]
    stones = [start]
    stack = [start]
    board[start] = 0
    while stack:
        p = stack.pop()
        for d in D4:
            n = p + d
            if board[n] == c:
                board[n] = 0
                stones.append(n)
                stack.append(n)
    return stones


def apply_move(board, idx, color):
    """Play move; return captured points, or None if illegal (suicide)."""
    opp = 3 - color
    board[idx] = color
    captured = []
    for d in D4:
        n = idx + d
        if board[n] == opp:
            if len(_libs_of(board, n)) == 0:
                captured.extend(_remove_group(board, n))
    if len(_libs_of(board, idx)) == 0:
        board[idx] = 0
        for s in captured:
            board[s] = opp
        return None
    return captured


def undo_move(board, idx, color, captured):
    board[idx] = 0
    opp = 3 - color
    for s in captured:
        board[s] = opp


def ko_bad(board, idx, captured):
    """Conservative ko filter: reject single-stone captures that leave a lone
    capturing stone with exactly one liberty (the ko-recapture shape)."""
    if len(captured) != 1:
        return False
    c = board[idx]
    lone = True
    libs = 0
    for d in D4:
        v = board[idx + d]
        if v == c:
            lone = False
            break
        if v == 0:
            libs += 1
    return lone and libs == 1


def _lad2(board, stone, att, depth):
    """Defender group at 'stone' has 2 libs; attacker to move. True = capturable."""
    LBUDGET[0] -= 1
    if LBUDGET[0] < 0 or depth > 24:
        return False
    libs = _libs_of(board, stone)
    n = len(libs)
    if n == 0:
        return True
    if n == 1:
        return _lad1(board, stone, att, depth + 1)
    if n > 2:
        return False
    for lib in libs:
        caps = apply_move(board, lib, att)
        if caps is None:
            continue
        if ko_bad(board, lib, caps):
            undo_move(board, lib, att, caps)
            continue
        res = _lad1(board, stone, att, depth + 1)
        undo_move(board, lib, att, caps)
        if res:
            return True
    return False


def _lad1(board, stone, att, depth):
    """Defender group at 'stone' has 1 lib; defender to move. True = dies anyway."""
    LBUDGET[0] -= 1
    if LBUDGET[0] < 0 or depth > 24:
        return False
    libs = _libs_of(board, stone)
    n = len(libs)
    if n == 0:
        return True
    if n > 1:
        return _lad2(board, stone, att, depth + 1)
    lib = next(iter(libs))
    dfd = 3 - att
    col = board[stone]
    stones_set = set()
    stones_set.add(stone)
    stack = [stone]
    while stack:
        p = stack.pop()
        for d in D4:
            q = p + d
            if board[q] == col and q not in stones_set:
                stones_set.add(q)
                stack.append(q)
    if LBUDGET[0] > 20:
        LBUDGET[0] -= 5
        esc = False
        for p in stones_set:
            for d in D4:
                q = p + d
                if board[q] == att:
                    l2 = _libs_of(board, q)
                    if len(l2) == 1:
                        alib = next(iter(l2))
                        caps = apply_move(board, alib, dfd)
                        if caps is None:
                            continue
                        if ko_bad(board, alib, caps):
                            undo_move(board, alib, dfd, caps)
                            continue
                        l3 = _libs_of(board, stone)
                        undo_move(board, alib, dfd, caps)
                        if len(l3) >= 2:
                            esc = True
                            break
            if esc:
                break
        if esc:
            return False
    caps = apply_move(board, lib, dfd)
    if caps is None:
        return True
    res = True
    if ko_bad(board, lib, caps):
        res = True
    else:
        l3 = _libs_of(board, lib)
        m = len(l3)
        if m >= 3:
            res = False
        elif m == 1:
            res = True
        else:
            res = _lad2(board, lib, att, depth + 1)
    undo_move(board, lib, dfd, caps)
    return res


def _bfs(board, color, trans):
    dist = [999] * NS
    dq = deque()
    for i in INTERIOR:
        if board[i] == color:
            dist[i] = 0
            dq.append(i)
    if not dq:
        return dist
    pop = dq.popleft
    push = dq.append
    while dq:
        p = pop()
        nd = dist[p] + 1
        for d in D4:
            n = p + d
            v = board[n]
            if v == 0 or v == color or n in trans:
                if dist[n] > nd:
                    dist[n] = nd
                    push(n)
    return dist


def eval_board(board, mover):
    """Static eval from color-1 perspective; 'mover' = side to play next."""
    groups = analyze(board)
    g = _gen
    trans = set()
    for gs in groups:
        if len(gs[2]) == 1:
            trans.update(gs[1])
    alive = set()
    gidg = _GIDG
    gid = _GID
    for i in INTERIOR:
        if board[i] == 0:
            if board[i - 21] == 0:
                continue
            o1 = 0
            o2 = 0
            bord = 0
            for d in D4:
                v = board[i + d]
                if v == 1:
                    o1 += 1
                elif v == 2:
                    o2 += 1
                else:
                    bord += 1
            col = 0
            if o2 == 0 and o1 + bord == 4:
                col = 1
            elif o1 == 0 and o2 + bord == 4:
                col = 2
            if col:
                do = 0
                for dd in DD:
                    if board[i + dd] == 3 - col:
                        do += 1
                if do <= 1:
                    for d in D4:
                        n = i + d
                        if gidg[n] == g:
                            alive.add(gid[n])
    mat = 0.0
    for gi in range(len(groups)):
        c, stones, libs = groups[gi]
        nl = len(libs)
        sz = len(stones)
        if nl >= 4:
            sf = 1.0
        elif nl == 3:
            sf = 0.92
        elif nl == 2:
            sf = 0.9 if gi in alive else 0.72
        elif nl == 1:
            if c == mover:
                if sz == 1:
                    lib = next(iter(libs))
                    e = 0
                    for d in D4:
                        if board[lib + d] == 0:
                            e += 1
                    if e >= 2:
                        sf = 0.4
                    elif e == 1:
                        sf = 0.2
                    else:
                        sf = 0.06
                else:
                    lib = next(iter(libs))
                    caps = apply_move(board, lib, c)
                    if caps is None:
                        sf = 0.06
                    else:
                        if ko_bad(board, lib, caps):
                            sf = 0.12
                        else:
                            l3 = _libs_of(board, lib)
                            m = len(l3)
                            if m >= 3:
                                sf = 0.45
                            elif m == 2:
                                if LBUDGET[0] > 60:
                                    if _lad2(board, lib, 3 - c, 0):
                                        sf = 0.15
                                    else:
                                        sf = 0.38
                                else:
                                    sf = 0.28
                            else:
                                sf = 0.12
                        undo_move(board, lib, c, caps)
            else:
                sf = 0.08
        else:
            sf = 0.0
        mat += sz * sf * (1.0 if c == 1 else -1.0)
    d1 = _bfs(board, 1, trans)
    d2 = _bfs(board, 2, trans)
    inf = 0
    for i in INTERIOR:
        if board[i] == 0:
            a = d1[i]
            b = d2[i]
            if a < b:
                inf += 1
            elif b < a:
                inf -= 1
    return mat + INF_W * inf


def gen_cands(board, color, groups, bonus, limit):
    opp = 3 - color
    cand = {}
    b = board
    for i in INTERIOR:
        if b[i]:
            r = i // S
            c = i - r * S
            for dr in (-2, -1, 0, 1, 2):
                rr = r + dr
                if rr < 1 or rr > 19:
                    continue
                base = rr * S
                for dc in (-2, -1, 0, 1, 2):
                    cc = c + dc
                    if cc < 1 or cc > 19:
                        continue
                    n = base + cc
                    if b[n] == 0:
                        ad = dr if dr > 0 else -dr
                        ac = dc if dc > 0 else -dc
                        ch = ad if ad > ac else ac
                        w = 1.2 if ch == 1 else 0.5
                        cand[n] = cand.get(n, 0.0) + w
    tot = 0
    for gs in groups:
        tot += len(gs[1])
    openf = 1.0 if tot < 25 else max(0.0, 1.0 - (tot - 25) / 130.0)
    for gs in groups:
        c2, stones, libs = gs
        sz = len(stones)
        nl = len(libs)
        if c2 == opp:
            if nl == 1:
                lib = next(iter(libs))
                cand[lib] = cand.get(lib, 0.0) + 12.0 + 2.2 * sz
            elif nl == 2:
                for lib in libs:
                    cand[lib] = cand.get(lib, 0.0) + 1.6 + 0.5 * sz
            elif nl == 3:
                for lib in libs:
                    cand[lib] = cand.get(lib, 0.0) + 0.7
        else:
            if nl == 1:
                lib = next(iter(libs))
                cand[lib] = cand.get(lib, 0.0) + 9.0 + 1.8 * sz
            elif nl == 2:
                for lib in libs:
                    cand[lib] = cand.get(lib, 0.0) + 1.3
    if tot <= 8:
        for idx in OPEN_PTS:
            if b[idx] == 0:
                cand[idx] = cand.get(idx, 0.0) + 2.5
    out = []
    for idx, sc in cand.items():
        if bonus:
            sc += bonus.get(idx, 0.0)
        r = idx // S
        c = idx - r * S
        e = 0
        myn = 0
        opn = 0
        for d in D4:
            v = b[idx + d]
            if v == 0:
                e += 1
            elif v == color:
                myn += 1
            elif v == opp:
                opn += 1
        if e == 0 and opn == 0:
            sc -= 14.0
        de = r
        if 20 - r < de:
            de = 20 - r
        if c < de:
            de = c
        if 20 - c < de:
            de = 20 - c
        if de == 1:
            sc -= 1.1 * openf
        elif de == 2:
            sc -= 0.45 * openf
        elif de <= 4:
            sc += 0.5 * openf
        else:
            sc += 0.12 * openf
        sc += 0.2 * e + 0.12 * myn + 0.08 * opn
        out.append((sc, idx))
    out.sort(reverse=True)
    return out[:limit]


def _legal_on(board, idx, color):
    caps = apply_move(board, idx, color)
    if caps is None:
        return False
    ok = not ko_bad(board, idx, caps)
    undo_move(board, idx, color, caps)
    return ok


def _fallback(board0, cands):
    order = []
    if cands:
        for sc, idx in cands:
            order.append(idx)
    order.extend(CENTER_ORDER)
    seen = set()
    for idx in order:
        if idx in seen or board0[idx] != 0:
            continue
        seen.add(idx)
        fill = True
        for d in D4:
            v = board0[idx + d]
            if v != 1 and v != 3:
                fill = False
                break
        if fill:
            continue
        if _legal_on(board0, idx, 1):
            return idx
    return None


def _final(board0, idx, cands):
    if idx is not None and board0[idx] == 0 and _legal_on(board0, idx, 1):
        return (idx // S, idx % S)
    fb = _fallback(board0, cands)
    if fb is not None:
        return (fb // S, fb % S)
    return (0, 0)


def _policy(me_list, opp_list, t0):
    board = [0] * NS
    for r in range(S):
        board[r * S] = 3
        board[r * S + S - 1] = 3
    for c in range(S):
        board[c] = 3
        board[(S - 1) * S + c] = 3
    mine = 0
    for it in me_list:
        try:
            r, c = it
            r = int(r)
            c = int(c)
        except Exception:
            continue
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * S + c] = 1
            mine += 1
    theirs = 0
    for it in opp_list:
        try:
            r, c = it
            r = int(r)
            c = int(c)
        except Exception:
            continue
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * S + c] = 2
            theirs += 1
    tot = mine + theirs
    if tot == 0:
        return (10, 10)
    board0 = board[:]

    groups = analyze(board)

    # root ladder reads: opponent two-liberty groups that are ladder-dead
    bonus = {}
    opp2 = [gs for gs in groups if gs[0] == 2 and len(gs[2]) == 2]
    opp2.sort(key=lambda gs: -len(gs[1]))
    reads = 0
    for gs in opp2:
        if reads >= 4:
            break
        LBUDGET[0] = 150
        if _lad2(board, gs[1][0], 1, 0):
            for lib in gs[2]:
                bonus[lib] = bonus.get(lib, 0.0) + 2.0 + 0.8 * len(gs[1])
        reads += 1
    board[:] = board0

    LBUDGET[0] = 900
    cands = gen_cands(board, 1, groups, bonus, 42)

    # Phase A: one-ply evaluation of candidates
    scored = []
    for sc, idx in cands:
        board[:] = board0
        caps = apply_move(board, idx, 1)
        if caps is None:
            continue
        if ko_bad(board, idx, caps):
            continue
        v = eval_board(board, 2)
        scored.append((v + 0.02 * sc, idx))
        if scored and time.perf_counter() - t0 > 0.50:
            break
    board[:] = board0

    if not scored:
        return _final(board0, None, cands)

    scored.sort(reverse=True)
    pass_v = eval_board(board, 2) - 0.5

    vals = {}
    for v, idx in scored:
        vals[idx] = v
    expanded = set()
    dsum = 0.0
    dcnt = 0

    # Phase B: opponent best-reply minimax on top moves
    tA = time.perf_counter() - t0
    if tA < 0.55 and (0.78 - tA) > 0.08:
        K1 = min(10, len(scored))
        perA = tA / max(1, len(scored))
        K2 = int((0.75 - tA) / (K1 * (perA * 2.5 + 0.0005)))
        if K2 < 3:
            K2 = 3
        if K2 > 14:
            K2 = 14
        stop = False
        for vA, idx in scored[:K1]:
            board[:] = board0
            caps = apply_move(board, idx, 1)
            if caps is None:
                continue
            base = board[:]
            groups2 = analyze(board)
            replies = gen_cands(board, 2, groups2, None, K2)
            worst = eval_board(board, 1) + 0.25
            for rsc, ridx in replies:
                board[:] = base
                rcaps = apply_move(board, ridx, 2)
                if rcaps is None:
                    continue
                if ko_bad(board, ridx, rcaps):
                    continue
                lv = eval_board(board, 1)
                if lv < worst:
                    worst = lv
                if time.perf_counter() - t0 > 0.80:
                    stop = True
                    break
            vals[idx] = 0.75 * worst + 0.25 * vA
            expanded.add(idx)
            dsum += vA - vals[idx]
            dcnt += 1
            if stop:
                break

    drop = 0.3
    if dcnt > 0:
        d = dsum / dcnt
        if d > 0.3:
            drop = d
    best_v = pass_v
    best_idx = 0
    for v, idx in scored:
        vv = vals[idx] if idx in expanded else v - drop
        if vv > best_v:
            best_v = vv
            best_idx = idx
    if best_idx == 0:
        return (0, 0)
    return _final(board0, best_idx, cands)


def _emergency(me, opponent):
    """Standalone fallback: return any legal, non-eye-filling move."""
    board = [0] * NS
    for r in range(S):
        board[r * S] = 3
        board[r * S + S - 1] = 3
    for c in range(S):
        board[c] = 3
        board[(S - 1) * S + c] = 3

    def parse(lst, val):
        if not lst:
            return
        for it in lst:
            try:
                r, c = it
                r = int(r)
                c = int(c)
                if 1 <= r <= 19 and 1 <= c <= 19:
                    board[r * S + c] = val
            except Exception:
                pass

    parse(me, 1)
    parse(opponent, 2)

    def libs_at(bd, st):
        col = bd[st]
        seen = set([st])
        stk = [st]
        lb = set()
        while stk:
            p = stk.pop()
            for d in (-21, 21, -1, 1):
                n = p + d
                v = bd[n]
                if v == 0:
                    lb.add(n)
                elif v == col and n not in seen:
                    seen.add(n)
                    stk.append(n)
        return lb

    def legal(idx):
        if board[idx] != 0:
            return False
        board[idx] = 1
        caps = []
        for d in (-21, 21, -1, 1):
            n = idx + d
            if board[n] == 2 and len(libs_at(board, n)) == 0:
                stk = [n]
                seen2 = set([n])
                while stk:
                    p = stk.pop()
                    board[p] = 0
                    caps.append(p)
                    for d2 in (-21, 21, -1, 1):
                        q = p + d2
                        if board[q] == 2 and q not in seen2:
                            seen2.add(q)
                            stk.append(q)
        ok = len(libs_at(board, idx)) > 0
        if ok and len(caps) == 1:
            lone = True
            lb2 = 0
            for d in (-21, 21, -1, 1):
                v = board[idx + d]
                if v == 1:
                    lone = False
                elif v == 0:
                    lb2 += 1
            if lone and lb2 == 1:
                ok = False
        board[idx] = 0
        for p in caps:
            board[p] = 2
        return ok

    for idx in CENTER_ORDER:
        if legal(idx):
            return (idx // S, idx % S)
    return (0, 0)


def policy(me, opponent):
    t0 = time.perf_counter()
    try:
        mv = _policy(me, opponent, t0)
        if mv is None:
            mv = (0, 0)
        return mv
    except Exception:
        try:
            return _emergency(me, opponent)
        except Exception:
            return (0, 0)
