
import numpy as np

SHIPS = [5, 4, 3, 3, 2]
N = 10


def _find_completed_segments(b):
    segs = []
    # horizontal runs
    for r in range(N):
        c = 0
        while c < N:
            if b[r][c] == 1:
                s = c
                while c < N and b[r][c] == 1:
                    c += 1
                L = c - s
                if L >= 2:
                    lb = (s == 0) or (b[r][s - 1] == -1)
                    rb = (c == N) or (b[r][c] == -1)
                    if lb and rb:
                        segs.append((L, [(r, x) for x in range(s, c)]))
            else:
                c += 1
    # vertical runs
    for c in range(N):
        r = 0
        while r < N:
            if b[r][c] == 1:
                s = r
                while r < N and b[r][c] == 1:
                    r += 1
                L = r - s
                if L >= 2:
                    tb = (s == 0) or (b[s - 1][c] == -1)
                    bb = (r == N) or (b[r][c] == -1)
                    if tb and bb:
                        segs.append((L, [(y, c) for y in range(s, r)]))
            else:
                r += 1
    return segs


def _density(b, dead, fleet, target_mode):
    score = np.zeros((N, N), dtype=float)
    any_added = False
    for L in fleet:
        for r in range(N):
            for c in range(N):
                # horizontal
                if c + L <= N:
                    ok = True
                    h = 0
                    for k in range(L):
                        v = b[r][c + k]
                        if v == -1 or dead[r][c + k]:
                            ok = False
                            break
                        if v == 1:
                            h += 1
                    if ok and (not target_mode or h > 0):
                        w = 1.0 if h == 0 else float(20 ** h)
                        for k in range(L):
                            if b[r][c + k] == 0:
                                score[r][c + k] += w
                                any_added = True
                # vertical
                if r + L <= N:
                    ok = True
                    h = 0
                    for k in range(L):
                        v = b[r + k][c]
                        if v == -1 or dead[r + k][c]:
                            ok = False
                            break
                        if v == 1:
                            h += 1
                    if ok and (not target_mode or h > 0):
                        w = 1.0 if h == 0 else float(20 ** h)
                        for k in range(L):
                            if b[r + k][c] == 0:
                                score[r + k][c] += w
                                any_added = True
    return score, any_added


def _pick_max(score, b):
    best = None
    best_val = -1.0
    for r in range(N):
        for c in range(N):
            if b[r][c] != 0:
                continue
            v = score[r][c]
            # parity tie-breaker and slight center preference
            v2 = v * 1000.0 + (1.0 if (r + c) % 2 == 0 else 0.0) \
                + 0.01 * (4.5 - abs(r - 4.5)) + 0.01 * (4.5 - abs(c - 4.5))
            if v2 > best_val:
                best_val = v2
                best = (r, c)
    return best


def _first_unknown(b):
    for r in range(N):
        for c in range(N):
            if b[r][c] == 0:
                return (r, c)
    return (0, 0)


def policy(board):
    try:
        b = [[int(board[r][c]) for c in range(N)] for r in range(N)]
        dead = [[False] * N for _ in range(N)]
        remaining = list(SHIPS)

        segs = _find_completed_segments(b)
        segs.sort(key=lambda s: -s[0])
        for L, cells in segs:
            if all(dead[r][c] for r, c in cells):
                continue
            removed_any = False
            rem = L
            while rem >= 2:
                cand = [s for s in remaining if s <= rem]
                if not cand:
                    break
                s = max(cand)
                remaining.remove(s)
                rem -= s
                removed_any = True
            if removed_any:
                for r, c in cells:
                    dead[r][c] = True

        fleet = remaining if remaining else [2, 3, 3, 4, 5]

        live_hits = [(r, c) for r in range(N) for c in range(N)
                     if b[r][c] == 1 and not dead[r][c]]
        target_mode = len(live_hits) > 0

        if target_mode:
            score, added = _density(b, dead, fleet, True)
            if not added:
                score, added = _density(b, dead, [2, 3, 3, 4, 5], True)
            if added:
                mv = _pick_max(score, b)
                if mv is not None and b[mv[0]][mv[1]] == 0:
                    return mv
            # fallback: unknown neighbors of live hits
            for r, c in live_hits:
                for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                        return (nr, nc)

        score, added = _density(b, dead, fleet, False)
        if not added:
            score, added = _density(b, [[False] * N for _ in range(N)],
                                    [2, 3, 3, 4, 5], False)
        mv = _pick_max(score, b)
        if mv is not None and b[mv[0]][mv[1]] == 0:
            return mv
        return _first_unknown(b)
    except Exception:
        try:
            for r in range(N):
                for c in range(N):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
