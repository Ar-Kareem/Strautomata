
import time

N = 10
SHIPS = [5, 4, 3, 3, 2]
LENS = (2, 3, 4, 5)

PLACE = {}
COVER = {}
for _L in LENS:
    _pl = []
    for _r in range(N):
        for _c in range(N):
            if _c + _L <= N:
                cells = [_r * N + _c + k for k in range(_L)]
                m = 0
                for ci in cells:
                    m |= 1 << ci
                _pl.append((m, cells))
            if _r + _L <= N:
                cells = [(_r + k) * N + _c for k in range(_L)]
                m = 0
                for ci in cells:
                    m |= 1 << ci
                _pl.append((m, cells))
    PLACE[_L] = _pl
    _cov = [[] for _ in range(N * N)]
    for m, cells in _pl:
        for ci in cells:
            _cov[ci].append((m, cells))
    COVER[_L] = _cov

CAP = 25000
TIME_LIMIT = 0.55


class _Abort(Exception):
    pass


def _popcount(x):
    return bin(x).count('1')


def policy(board):
    try:
        mv = _policy(board)
        r, c = mv
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            return (int(r), int(c))
    except Exception:
        pass
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def _policy(board):
    t0 = time.time()
    M = 0
    H = 0
    unknown = []
    for r in range(N):
        for c in range(N):
            v = board[r][c]
            idx = r * N + c
            if v == -1:
                M |= 1 << idx
            elif v == 1:
                H |= 1 << idx
            else:
                unknown.append(idx)
    if not unknown:
        return (0, 0)

    # free-ship placement counts/frequencies (avoid misses and hits)
    count = {}
    freq = {}
    MH = M | H
    for L in LENS:
        f = [0] * (N * N)
        cnt = 0
        for m, cells in PLACE[L]:
            if m & MH:
                continue
            cnt += 1
            for ci in cells:
                f[ci] += 1
        count[L] = cnt
        freq[L] = f

    T = [0.0] * (N * N)
    coef = {L: 0.0 for L in LENS}
    total = [0.0]
    w2free = [0.0]
    nodes = [0]

    def rec(occ, rem, avail, remlen, placed):
        nodes[0] += 1
        if nodes[0] > CAP or (nodes[0] & 255 == 0 and time.time() - t0 > TIME_LIMIT):
            raise _Abort()
        if rem == 0:
            W = 1.0
            for si in range(5):
                if (avail >> si) & 1:
                    W *= count[SHIPS[si]]
            if W <= 0:
                return
            total[0] += W
            for cells in placed:
                for ci in cells:
                    if not (H >> ci) & 1:
                        T[ci] += W
            for si in range(5):
                if (avail >> si) & 1:
                    L = SHIPS[si]
                    coef[L] += W
                    if L == 2:
                        w2free[0] += W
            return
        h = (rem & -rem).bit_length() - 1
        blocked = occ | M
        for si in range(5):
            if not (avail >> si) & 1:
                continue
            L = SHIPS[si]
            nrl = remlen - L
            for m, cells in COVER[L][h]:
                if m & blocked:
                    continue
                nrem = rem & ~m
                if _popcount(nrem) > nrl:
                    continue
                placed.append(cells)
                rec(occ | m, nrem, avail & ~(1 << si), nrl, placed)
                placed.pop()

    aborted = False
    try:
        rec(0, H, 0b11111, 17, [])
    except _Abort:
        aborted = True

    best = None
    bestscore = -1.0

    def centrality(ci):
        r, c = divmod(ci, N)
        return -(abs(r - 4.5) + abs(c - 4.5)) * 1e-9

    if not aborted and total[0] > 0:
        F = [0.0] * (N * N)
        for L in LENS:
            if coef[L] > 0 and count[L] > 0:
                k = coef[L] / count[L]
                fl = freq[L]
                for ci in range(N * N):
                    if fl[ci]:
                        F[ci] += k * fl[ci]
        use_par = w2free[0] > 0.5 * total[0]
        for ci in unknown:
            fac = 1.0
            if use_par and ((ci // N + ci % N) % 2 != 0):
                fac = 0.5
            s = T[ci] + F[ci] * fac + centrality(ci)
            if s > bestscore:
                bestscore = s
                best = ci
        if best is not None:
            return (best // N, best % N)

    # Fallback heuristic: hit-weighted placement density
    sc = [0.0] * (N * N)
    for L in LENS:
        for m, cells in PLACE[L]:
            if m & M:
                continue
            hc = _popcount(m & H)
            if hc == L:
                continue
            w = 1.0 if hc == 0 else 20.0 ** hc
            for ci in cells:
                if not (H >> ci) & 1:
                    sc[ci] += w
    target_mode = max(sc[ci] for ci in unknown) >= 20.0
    best = None
    bestscore = -1.0
    for ci in unknown:
        s = sc[ci]
        if not target_mode and ((ci // N + ci % N) % 2 != 0):
            s *= 0.5
        s += centrality(ci)
        if s > bestscore:
            bestscore = s
            best = ci
    if best is None:
        best = unknown[0]
    return (best // N, best % N)
