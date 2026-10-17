
import time
import random
import numpy as np

N = 19
SIZE = N * N
NEIGH = []
for _i in range(SIZE):
    _r, _c = divmod(_i, N)
    _lst = []
    if _r > 0:
        _lst.append(_i - N)
    if _r < N - 1:
        _lst.append(_i + N)
    if _c > 0:
        _lst.append(_i - 1)
    if _c < N - 1:
        _lst.append(_i + 1)
    NEIGH.append(_lst)

_idx = np.arange(SIZE)
ROWS = _idx // N
COLS = _idx % N
_D = np.abs(ROWS[:, None] - ROWS[None, :]) + np.abs(COLS[:, None] - COLS[None, :])
K = np.where(_D <= 5, 0.55 ** _D, 0.0)
LINE = np.minimum(np.minimum(ROWS, COLS), np.minimum(N - 1 - ROWS, N - 1 - COLS)).tolist()
CR = np.minimum(ROWS, N - 1 - ROWS).tolist()
CC = np.minimum(COLS, N - 1 - COLS).tolist()
LINEB = [-4.0, -1.5, 1.0, 1.0, 0.0, -1.0, -1.0, -1.0, -1.0, -1.0]
DEPTH = 7

_deadline = 0.0


def group(board, start):
    color = board[start]
    stones = [start]
    seen = {start}
    libs = set()
    stack = [start]
    while stack:
        x = stack.pop()
        for n in NEIGH[x]:
            v = board[n]
            if v == 0:
                libs.add(n)
            elif v == color and n not in seen:
                seen.add(n)
                stones.append(n)
                stack.append(n)
    return stones, libs


def play(board, p, color):
    b = board[:]
    b[p] = color
    opp = 3 - color
    captured = []
    for n in NEIGH[p]:
        if b[n] == opp:
            st, lb = group(b, n)
            if not lb:
                for s in st:
                    b[s] = 0
                captured.extend(st)
    st, lb = group(b, p)
    if not lb:
        return None
    return b, captured, st, lb


def compute_groups(board):
    gid = [-1] * SIZE
    groups = []
    for i in range(SIZE):
        if board[i] and gid[i] < 0:
            color = board[i]
            g = len(groups)
            gid[i] = g
            stones = []
            libs = set()
            stack = [i]
            while stack:
                x = stack.pop()
                stones.append(x)
                for n in NEIGH[x]:
                    v = board[n]
                    if v == 0:
                        libs.add(n)
                    elif v == color and gid[n] < 0:
                        gid[n] = g
                        stack.append(n)
            groups.append((color, stones, libs))
    return gid, groups


def weights(groups):
    w = np.zeros(SIZE)
    for color, stones, libs in groups:
        l = len(libs)
        wt = 1.0 if l >= 3 else (0.65 if l == 2 else 0.25)
        if color == 2:
            wt = -wt
        for s in stones:
            w[s] = wt
    return w


def attacker_kills(board, gstone, attacker, depth):
    if time.time() > _deadline:
        return False
    defender = 3 - attacker
    stones, libs = group(board, gstone)
    if len(libs) != 2:
        return len(libs) <= 1
    if depth <= 0:
        return False
    for L in list(libs):
        res = play(board, L, attacker)
        if res is None:
            continue
        b2, cap, ast, alibs = res
        if len(alibs) < 2:
            continue
        if not defender_escapes(b2, gstone, defender, depth - 1):
            return True
    return False


def defender_escapes(board, gstone, defender, depth):
    if time.time() > _deadline:
        return True
    attacker = 3 - defender
    stones, libs = group(board, gstone)
    if len(libs) >= 2:
        return True
    if len(libs) == 0:
        return False
    if depth <= 0:
        return True
    L = next(iter(libs))
    options = [L]
    seen = set()
    for s in stones:
        for n in NEIGH[s]:
            if board[n] == attacker and n not in seen:
                st, lb = group(board, n)
                seen.update(st)
                if len(lb) == 1:
                    options.append(next(iter(lb)))
    for m in options:
        res = play(board, m, defender)
        if res is None:
            continue
        b2 = res[0]
        if b2[gstone] != defender:
            continue
        st2, libs2 = group(b2, gstone)
        if len(libs2) >= 3:
            return True
        if len(libs2) <= 1:
            continue
        if not attacker_kills(b2, gstone, attacker, depth - 1):
            return True
    return False


def corner_empty(board, p):
    r, c = divmod(p, N)
    r0 = 0 if r < 9 else N - 7
    c0 = 0 if c < 9 else N - 7
    for rr in range(r0, r0 + 7):
        base = rr * N
        for cc in range(c0, c0 + 7):
            if board[base + cc]:
                return False
    return True


def _build_board(me, opponent):
    board = [0] * SIZE
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + (c - 1)] = 2
    return board


def _fallback(me, opponent):
    board = _build_board(me, opponent)
    for p in range(SIZE):
        if board[p] == 0:
            # avoid filling own eyes if possible
            if all(board[n] == 1 for n in NEIGH[p]):
                continue
            if play(board, p, 1) is not None:
                r, c = divmod(p, N)
                return (r + 1, c + 1)
    for p in range(SIZE):
        if board[p] == 0 and play(board, p, 1) is not None:
            r, c = divmod(p, N)
            return (r + 1, c + 1)
    return (0, 0)


def _policy(me, opponent, memory, start):
    board = _build_board(me, opponent)
    mem = memory if isinstance(memory, dict) else {}
    hist = mem.get('hist')
    if not isinstance(hist, list):
        hist = []
    cur_key = hash(bytes(board))
    last = mem.get('last')
    opp_passed = (last == cur_key)
    histset = set(hist)
    histset.add(cur_key)

    gid, groups = compute_groups(board)
    total = len(me) + len(opponent)
    empties = [i for i in range(SIZE) if board[i] == 0]
    if not empties:
        mem['hist'] = hist + [cur_key]
        mem['last'] = cur_key
        return (0, 0), mem

    w = weights(groups)
    I = K @ w
    T0 = float(np.tanh(I).sum())
    G = (np.tanh(I[None, :] + K).sum(axis=1) - T0).tolist()
    Il = I.tolist()

    # own 2-liberty groups that opponent can kill
    threatened = set()
    for gi, g in enumerate(groups):
        if g[0] == 1 and len(g[2]) == 2 and time.time() < _deadline:
            contact = False
            for s in g[1]:
                for n in NEIGH[s]:
                    if board[n] == 2:
                        contact = True
                        break
                if contact:
                    break
            if contact and attacker_kills(board, g[1][0], 2, DEPTH):
                threatened.add(gi)

    op = max(0.0, 1.0 - total / 90.0)
    best = None
    best_s = -1e9

    for p in empties:
        if time.time() - start > 0.85:
            break
        adj_own = set()
        adj_opp = set()
        empty_n = 0
        for n in NEIGH[p]:
            v = board[n]
            if v == 0:
                empty_n += 1
            elif v == 1:
                adj_own.add(gid[n])
            else:
                adj_opp.add(gid[n])
        caps = [gi for gi in adj_opp if len(groups[gi][2]) == 1]
        s = 0.0
        b2 = None
        if caps:
            res = play(board, p, 1)
            if res is None:
                continue
            b2, cap, stones, libs = res
            if hash(bytes(b2)) in histset:
                continue
            ncap = len(cap)
            gid2, groups2 = compute_groups(b2)
            w2 = weights(groups2)
            s += float(np.tanh(K @ w2).sum() - T0)
            s += 2.0 * ncap + 2.0
            nl = len(libs)
            size = len(stones)
            if nl == 1:
                s -= 2.0 * size + 1.0
            elif nl == 2:
                s -= 1.0
            for gi in adj_own:
                g = groups[gi]
                if len(g[2]) == 1 and nl >= 2:
                    s += 2.0 * len(g[1]) + 1.0
        else:
            libs = set()
            size = 1
            minlib_own = 99
            for gi in adj_own:
                libs |= groups[gi][2]
                size += len(groups[gi][1])
                if len(groups[gi][2]) < minlib_own:
                    minlib_own = len(groups[gi][2])
            for n in NEIGH[p]:
                if board[n] == 0:
                    libs.add(n)
            libs.discard(p)
            if not libs:
                continue
            nl = len(libs)
            s += G[p]
            killed = False
            if nl == 1:
                s -= 10.0 + 2.0 * size
            elif nl == 2:
                s -= 2.0
                if (adj_opp or size >= 2) and time.time() < _deadline:
                    b2 = board[:]
                    b2[p] = 1
                    if attacker_kills(b2, p, 2, DEPTH):
                        killed = True
                        s -= 2.0 * size + 3.0
            elif nl == 3:
                s -= 0.3
            if empty_n == 0 and not adj_opp:
                if not (len(adj_own) >= 2 and minlib_own <= 2):
                    s -= 12.0
            for gi in adj_own:
                g = groups[gi]
                if len(g[2]) == 1:
                    if nl >= 3 or (nl == 2 and not killed):
                        s += 2.0 * len(g[1]) + 1.5
                elif gi in threatened:
                    if nl >= 3 or (nl == 2 and not killed):
                        s += 1.5 * len(g[1]) + 1.0
            for gi in adj_opp:
                g = groups[gi]
                ol = len(g[2])
                if ol == 2 and nl >= 2 and not killed:
                    if b2 is None:
                        b2 = board[:]
                        b2[p] = 1
                    if time.time() < _deadline and not defender_escapes(b2, g[1][0], 2, DEPTH):
                        s += 2.0 * len(g[1]) + 3.0
                    else:
                        s += 0.3
                elif ol == 3 and nl >= 3:
                    s += 0.4
                elif ol == 4 and nl >= 3:
                    s += 0.15
            ip = Il[p]
            if ip < -1.0:
                s -= 3.0 * (-ip - 1.0)
        line = LINE[p]
        if op > 0:
            s += LINEB[line] * op
            if 2 <= CR[p] <= 3 and 2 <= CC[p] <= 3 and corner_empty(board, p):
                s += 6.0 * op
        else:
            if line == 0:
                s -= 0.3
        s += random.random() * 0.01
        if s > best_s:
            best_s = s
            best = p

    threshold = 0.9 if opp_passed else 0.3
    if best is None or best_s < threshold:
        hist.append(cur_key)
        mem['hist'] = hist[-600:]
        mem['last'] = cur_key
        return (0, 0), mem

    res = play(board, best, 1)
    if res is None:
        raise ValueError("illegal best move")
    b2 = res[0]
    new_key = hash(bytes(b2))
    hist.append(cur_key)
    hist.append(new_key)
    mem['hist'] = hist[-600:]
    mem['last'] = new_key
    r, c = divmod(best, N)
    return (r + 1, c + 1), mem


def policy(me, opponent, memory):
    global _deadline
    start = time.time()
    _deadline = start + 0.6
    try:
        move, mem = _policy(me, opponent, memory, start)
        if move != (0, 0):
            board = _build_board(me, opponent)
            p = (move[0] - 1) * N + (move[1] - 1)
            if board[p] != 0 or play(board, p, 1) is None:
                move = _fallback(me, opponent)
    except Exception:
        try:
            move = _fallback(me, opponent)
        except Exception:
            move = (0, 0)
        mem = memory if isinstance(memory, dict) else {}
    if not isinstance(mem, dict):
        mem = {}
    return move, mem
