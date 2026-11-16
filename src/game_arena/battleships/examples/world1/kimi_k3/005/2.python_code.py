
import random
import time

N = 10
SHIP_LENGTHS = (5, 4, 3, 3, 2)
_LENGTHS = (2, 3, 4, 5)


def _gen_placements(length):
    placements = []
    for r in range(N):
        for c in range(N - length + 1):
            placements.append(tuple(r * N + c + k for k in range(length)))
    for r in range(N - length + 1):
        for c in range(N):
            placements.append(tuple((r + k) * N + c for k in range(length)))
    return placements


# Precompute every placement (as cell tuples and as 100-bit masks),
# plus a per-cell index of which placements cover that cell.
_PLACEMENTS = {L: _gen_placements(L) for L in _LENGTHS}
_MASKS = {L: [sum(1 << cell for cell in cells) for cells in _PLACEMENTS[L]]
          for L in _LENGTHS}
_COVER = [[] for _ in range(N * N)]
for _L in _LENGTHS:
    for _i, _cells in enumerate(_PLACEMENTS[_L]):
        for _cell in _cells:
            _COVER[_cell].append((_L, _i))


def _hunt_cell(unknown, miss_mask, rng):
    """Exact probability density over all ship placements avoiding misses."""
    scores = [0] * (N * N)
    for L in _LENGTHS:
        mult = SHIP_LENGTHS.count(L)
        for m, cells in zip(_MASKS[L], _PLACEMENTS[L]):
            if m & miss_mask:
                continue
            for cell in cells:
                scores[cell] += mult
    best = -1
    best_cells = []
    for cell in unknown:
        s = scores[cell]
        if s > best:
            best = s
            best_cells = [cell]
        elif s == best:
            best_cells.append(cell)
    return rng.choice(best_cells)


def _fallback_cell(hit_mask, miss_mask, unknown, rng):
    """Deterministic hit-weighted placement density (backup plan)."""
    scores = [0] * (N * N)
    for L in _LENGTHS:
        for m, cells in zip(_MASKS[L], _PLACEMENTS[L]):
            if m & miss_mask:
                continue
            hh = bin(m & hit_mask).count("1")
            if hh == 0:
                continue
            w = hh * hh
            for cell in cells:
                scores[cell] += w
    best = 0
    best_cells = []
    for cell in unknown:
        s = scores[cell]
        if s > best:
            best = s
            best_cells = [cell]
        elif s == best and s > 0:
            best_cells.append(cell)
    if not best_cells:
        return rng.choice(unknown)
    return rng.choice(best_cells)


def _sample_fleet(hits, hit_mask, valid, cover, hc, rng):
    """Sample one full fleet consistent with all hits and misses."""
    remaining = [0, 0, 1, 2, 1, 1]  # index by ship length
    order = list(hits)
    rng.shuffle(order)
    used = 0
    covered = 0
    chosen = []

    # Phase 1: cover every hit with some ship placement.
    for h in order:
        if (covered >> h) & 1:
            continue
        d = cover[h]
        cands = []
        for L in _LENGTHS:
            if remaining[L] == 0:
                continue
            for pidx in d.get(L, ()):
                m = _MASKS[L][pidx]
                if m & used:
                    continue
                hh = hc[L][pidx]
                cands.append((1 + hh * hh, L, pidx, m))
        if not cands:
            return None
        total = sum(c[0] for c in cands)
        r = rng.random() * total
        w, L, pidx, m = cands[-1]
        acc = 0.0
        for w0, L0, p0, m0 in cands:
            acc += w0
            if r <= acc:
                w, L, pidx, m = w0, L0, p0, m0
                break
        remaining[L] -= 1
        used |= m
        covered |= m & hit_mask
        chosen.append((L, pidx))

    # Phase 2: place the leftover ships in free water.
    for L in (5, 4, 3, 2):
        for _ in range(remaining[L]):
            vs = valid[L]
            n = len(vs)
            placed = False
            for _try in range(25):
                pidx = vs[rng.randrange(n)]
                m = _MASKS[L][pidx]
                if (m & used) or (m & hit_mask):
                    continue
                used |= m
                chosen.append((L, pidx))
                placed = True
                break
            if not placed:
                for pidx in vs:
                    m = _MASKS[L][pidx]
                    if (m & used) or (m & hit_mask):
                        continue
                    used |= m
                    chosen.append((L, pidx))
                    placed = True
                    break
                if not placed:
                    return None
    return chosen


def _target_cell(hits, hit_mask, miss_mask, unknown, rng, t0):
    """Monte Carlo posterior over unknown cells given all hits/misses."""
    valid = {}
    hc = {}
    for L in _LENGTHS:
        valid[L] = [i for i, m in enumerate(_MASKS[L]) if not (m & miss_mask)]
        hc[L] = [bin(m & hit_mask).count("1") for m in _MASKS[L]]
    cover = {}
    for h in hits:
        d = {}
        for (L, idx) in _COVER[h]:
            if not (_MASKS[L][idx] & miss_mask):
                d.setdefault(L, []).append(idx)
        cover[h] = d

    tally = [0] * (N * N)
    success = 0
    attempts = 0
    while True:
        elapsed = time.time() - t0
        if success >= 40 and (success >= 600 or elapsed > 0.5):
            break
        if elapsed > 0.75 or attempts > 20000:
            break
        attempts += 1
        fleet = _sample_fleet(hits, hit_mask, valid, cover, hc, rng)
        if fleet is None:
            continue
        success += 1
        for (L, pidx) in fleet:
            for cell in _PLACEMENTS[L][pidx]:
                if not ((hit_mask >> cell) & 1):
                    tally[cell] += 1

    if success < 8:
        return _fallback_cell(hit_mask, miss_mask, unknown, rng)
    best = 0
    best_cells = []
    for cell in unknown:
        s = tally[cell]
        if s > best:
            best = s
            best_cells = [cell]
        elif s == best and s > 0:
            best_cells.append(cell)
    if not best_cells:
        return _fallback_cell(hit_mask, miss_mask, unknown, rng)
    return rng.choice(best_cells)


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        t0 = time.time()
        hits = []
        unknown = []
        hit_mask = 0
        miss_mask = 0
        for r in range(N):
            row = board[r]
            base = r * N
            for c in range(N):
                v = row[c]
                cell = base + c
                if v == 1:
                    hits.append(cell)
                    hit_mask |= 1 << cell
                elif v == -1:
                    miss_mask |= 1 << cell
                else:
                    unknown.append(cell)
        if not unknown:
            return (0, 0)
        rng = random.Random()
        if hits:
            cell = _target_cell(hits, hit_mask, miss_mask, unknown, rng, t0)
        else:
            cell = _hunt_cell(unknown, miss_mask, rng)
        return (cell // N, cell % N)
    except Exception:
        # Last-resort: always return a legal move.
        try:
            choices = [(r, c) for r in range(10) for c in range(10)
                       if board[r][c] == 0]
            if choices:
                return random.choice(choices)
        except Exception:
            pass
        return (0, 0)
