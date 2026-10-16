
import random
import time

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def _build_placements(board):
    plist = {}
    cover = {}
    for L in set(SHIP_LENGTHS):
        lst = []
        cov = [[] for _ in range(N * N)]
        for r in range(N):
            for c in range(N):
                if c + L <= N:
                    ok = True
                    m = 0
                    for k in range(L):
                        if board[r][c + k] == -1:
                            ok = False
                            break
                        m |= 1 << (r * N + c + k)
                    if ok:
                        lst.append(m)
                        for k in range(L):
                            cov[r * N + c + k].append(m)
                if r + L <= N:
                    ok = True
                    m = 0
                    for k in range(L):
                        if board[r + k][c] == -1:
                            ok = False
                            break
                        m |= 1 << ((r + k) * N + c)
                    if ok:
                        lst.append(m)
                        for k in range(L):
                            cov[(r + k) * N + c].append(m)
        plist[L] = lst
        cover[L] = cov
    return plist, cover


def _sample(rem, occ, hitmask, cover, plist, budget):
    budget[0] -= 1
    if budget[0] < 0:
        return None
    unc = hitmask & ~occ
    if not rem:
        return occ if unc == 0 else None
    if unc:
        if bin(unc).count("1") > sum(rem):
            return None
        h = (unc & -unc).bit_length() - 1
        cands = []
        seen = set()
        for i, L in enumerate(rem):
            if L in seen:
                continue
            seen.add(L)
            for m in cover[L][h]:
                if m & occ == 0:
                    cands.append((i, m))
        if not cands:
            return None
        random.shuffle(cands)
        for i, m in cands:
            nrem = rem[:i] + rem[i + 1:]
            res = _sample(nrem, occ | m, hitmask, cover, plist, budget)
            if res is not None:
                return res
            if budget[0] < 0:
                return None
        return None
    else:
        L = rem[0]
        lst = plist[L]
        if not lst:
            return None
        n = len(lst)
        tries = 0
        for _ in range(40):
            m = lst[random.randrange(n)]
            if m & occ == 0:
                tries += 1
                res = _sample(rem[1:], occ | m, hitmask, cover, plist, budget)
                if res is not None:
                    return res
                if budget[0] < 0 or tries >= 4:
                    return None
        avail = [m for m in lst if m & occ == 0]
        random.shuffle(avail)
        for m in avail[:4]:
            res = _sample(rem[1:], occ | m, hitmask, cover, plist, budget)
            if res is not None:
                return res
            if budget[0] < 0:
                return None
        return None


def _heuristic(board, plist, hitmask):
    heur = [0.0] * (N * N)
    for L in set(SHIP_LENGTHS):
        for m in plist[L]:
            h = bin(m & hitmask).count("1")
            w = 1.0 if h == 0 else float(min(10 ** h, 10 ** 6))
            mm = m
            while mm:
                low = mm & -mm
                idx = low.bit_length() - 1
                if board[idx // N][idx % N] == 0:
                    heur[idx] += w
                mm ^= low
    return heur


def policy(board):
    start = time.time()
    unknown = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknown:
        return (0, 0)

    hitmask = 0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                hitmask |= 1 << (r * N + c)

    plist, cover = _build_placements(board)
    counts = [0] * (N * N)
    samples = 0
    deadline = start + 0.45
    rem_base = sorted(SHIP_LENGTHS, reverse=True)
    max_samples = 6000
    try:
        while samples < max_samples and time.time() < deadline:
            budget = [1500]
            res = _sample(rem_base, 0, hitmask, cover, plist, budget)
            if res is None:
                continue
            samples += 1
            mm = res & ~hitmask
            while mm:
                low = mm & -mm
                idx = low.bit_length() - 1
                counts[idx] += 1
                mm ^= low
    except Exception:
        pass

    try:
        heur = _heuristic(board, plist, hitmask)
    except Exception:
        heur = [0.0] * (N * N)
    mh = max(heur) if heur else 0.0
    if mh <= 0:
        mh = 1.0

    best = None
    best_score = -1.0
    for (r, c) in unknown:
        idx = r * N + c
        score = counts[idx] + 0.5 * (heur[idx] / mh) + random.random() * 1e-6
        if score > best_score:
            best_score = score
            best = (r, c)

    if best is None or board[best[0]][best[1]] != 0:
        return unknown[0]
    return (int(best[0]), int(best[1]))
