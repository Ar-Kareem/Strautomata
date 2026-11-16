
import time
import random

_ALL = (1 << 100) - 1
_TOTAL_SPENT = 0.0


def _build_masks():
    """All placement bitmasks (100-bit boards) for each ship length."""
    masks = {}
    for L in (2, 3, 4, 5):
        ms = []
        for r in range(10):
            base = r * 10
            for c in range(11 - L):
                m = 0
                for k in range(L):
                    m |= 1 << (base + c + k)
                ms.append(m)
        for c in range(10):
            for r in range(11 - L):
                m = 0
                for k in range(L):
                    m |= 1 << ((r + k) * 10 + c)
                ms.append(m)
        masks[L] = ms
    return masks


_MASKS = _build_masks()
_FLEET = ((5, 1), (4, 1), (3, 2), (2, 1))


def _policy(board, t0):
    global _TOTAL_SPENT

    # ---- parse board into flat list + bitmasks ----
    flat = [0] * 100
    miss = 0
    hit = 0
    for r in range(10):
        row = board[r]
        base = r * 10
        for c in range(10):
            v = row[c]
            j = base + c
            if v == -1:
                miss |= 1 << j
                flat[j] = -1
            elif v == 1:
                hit |= 1 << j
                flat[j] = 1

    if not miss and not hit:
        _TOTAL_SPENT = 0.0  # first move of a new game -> reset budget

    # adaptive time budget (hedges against any global time accounting)
    if _TOTAL_SPENT > 12.0:
        budget = 0.06
    elif _TOTAL_SPENT > 6.0:
        budget = 0.15
    else:
        budget = 0.35
    deadline = t0 + budget
    perf = time.perf_counter

    unknown_mask = ~(miss | hit) & _ALL
    unknown = [i for i in range(100) if (unknown_mask >> i) & 1]
    if not unknown:
        return (0, 0)

    rng = random.Random()
    randrange = rng.randrange

    # placements per length that avoid all misses
    avail = {}
    for L, ms in _MASKS.items():
        avail[L] = ms if not miss else [m for m in ms if not (m & miss)]

    # for each hit cell: miss-free placements (per length) covering it
    through = {}
    if hit:
        for L, ms in avail.items():
            for m in ms:
                mh = m & hit
                if mh:
                    while mh:
                        b = mh & -mh
                        mh ^= b
                        t = b.bit_length() - 1
                        d = through.get(t)
                        if d is None:
                            d = through[t] = {}
                        lst = d.get(L)
                        if lst is None:
                            d[L] = [m]
                        else:
                            lst.append(m)

    counts = [0] * 100
    n_ok = 0
    attempts = 0

    while n_ok < 25000 and (attempts < 30 or perf() < deadline):
        attempts += 1
        used = 0
        unc = hit
        remaining = {5: 1, 4: 1, 3: 2, 2: 1}
        ok = True

        # ---- phase 1: stochastically cover every hit with remaining ships ----
        while unc:
            ts = []
            u = unc
            while u:
                b = u & -u
                u ^= b
                ts.append(b.bit_length() - 1)
            t = ts[randrange(len(ts))]
            td = through.get(t)
            tot = 0
            opts = []
            if td is not None:
                for L, cnt in remaining.items():
                    if cnt <= 0:
                        continue
                    cl0 = td.get(L)
                    if cl0:
                        cl = [m for m in cl0 if not (m & used)]
                        if cl:
                            n = cnt * len(cl)
                            tot += n
                            opts.append((n, L, cl))
            if tot == 0:
                ok = False
                break
            x = randrange(tot)
            pick_L = -1
            pick_m = -1
            for n, L, cl in opts:
                if x < n:
                    pick_L = L
                    pick_m = cl[randrange(len(cl))]
                    break
                x -= n
            if pick_L < 0:
                ok = False
                break
            used |= pick_m
            unc &= ~pick_m
            remaining[pick_L] -= 1

        # ---- phase 2: place remaining ships uniformly among legal spots ----
        if ok:
            rest = []
            for L, cnt in remaining.items():
                if cnt > 0:
                    rest.extend([L] * cnt)
            rng.shuffle(rest)
            for L in rest:
                cands = [m for m in avail[L] if not (m & used)]
                if not cands:
                    ok = False
                    break
                used |= cands[randrange(len(cands))]

        # ---- tally occupancy of unknown cells ----
        if ok:
            occ = used & unknown_mask
            while occ:
                b = occ & -occ
                occ ^= b
                counts[b.bit_length() - 1] += 1
            n_ok += 1

    # ---- decision: highest posterior occupancy among unknown cells ----
    if n_ok > 0:
        best = -1
        for i in unknown:
            ci = counts[i]
            if ci > best:
                best = ci
        cand = [i for i in unknown if counts[i] == best]
        i = cand[randrange(len(cand))]
        return (i // 10, i % 10)

    # ---- fallback heuristic: adjacency to hits, then placement density ----
    dens = [0] * 100
    for L, cnt in _FLEET:
        for m in avail[L]:
            mm = m
            while mm:
                b = mm & -mm
                mm ^= b
                dens[b.bit_length() - 1] += cnt
    best_score = -1
    cand = []
    for i in unknown:
        s = dens[i]
        r, c = divmod(i, 10)
        if r > 0 and flat[i - 10] == 1:
            s += 1000000
        if r < 9 and flat[i + 10] == 1:
            s += 1000000
        if c > 0 and flat[i - 1] == 1:
            s += 1000000
        if c < 9 and flat[i + 1] == 1:
            s += 1000000
        if s > best_score:
            best_score = s
            cand = [i]
        elif s == best_score:
            cand.append(i)
    i = cand[randrange(len(cand))]
    return (i // 10, i % 10)


def policy(board):
    """Public API. Always returns a legal (row, col) for an unknown cell."""
    global _TOTAL_SPENT
    t0 = time.perf_counter()
    try:
        return _policy(board, t0)
    except Exception:
        # emergency fallback: scan for any legal cell
        try:
            for r in range(10):
                row = board[r]
                for c in range(10):
                    if row[c] == 0:
                        return (r, c)
        except Exception:
            return (0, 0)
        return (0, 0)
    finally:
        _TOTAL_SPENT += time.perf_counter() - t0
