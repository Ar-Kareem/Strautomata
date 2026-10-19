
from __future__ import annotations

import random
import time

_N = 10
_CELLS = 100
_FLEET = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = (5, 4, 3, 2)
_MULT = {5: 1.0, 4: 1.0, 3: 2.0, 2: 1.0}
_HAS_BIT_COUNT = hasattr(int, "bit_count")

_ALL_PLACEMENTS = []
_PLACEMENTS_BY_LEN = {L: [] for L in _UNIQUE_LENGTHS}
_COVERING = {L: [[] for _ in range(_CELLS)] for L in _UNIQUE_LENGTHS}


def _bit_count(x: int) -> int:
    if _HAS_BIT_COUNT:
        return x.bit_count()
    return bin(x).count("1")


def _make_placement(L, cells, orient, r0, c0):
    mask = 0
    cells = tuple(cells)
    for i in cells:
        mask |= 1 << i
    p = (mask, cells, orient, r0, c0, L)
    _PLACEMENTS_BY_LEN[L].append(p)
    _ALL_PLACEMENTS.append(p)
    for i in cells:
        _COVERING[L][i].append(p)


for _L in _UNIQUE_LENGTHS:
    # Horizontal placements.
    for _r in range(_N):
        for _c in range(_N - _L + 1):
            _make_placement(_L, [_r * _N + _c + k for k in range(_L)], 0, _r, _c)

    # Vertical placements.
    for _r in range(_N - _L + 1):
        for _c in range(_N):
            _make_placement(_L, [(_r + k) * _N + _c for k in range(_L)], 1, _r, _c)


_CENTER = []
for _i in range(_CELLS):
    _r, _c = divmod(_i, _N)
    _CENTER.append(100.0 - ((_r - 4.5) * (_r - 4.5) + (_c - 4.5) * (_c - 4.5)))


def _indices(mask: int):
    out = []
    while mask:
        lsb = mask & -mask
        out.append(lsb.bit_length() - 1)
        mask ^= lsb
    return out


def _adj_hit_count(idx: int, hitmask: int) -> int:
    r, c = divmod(idx, _N)
    cnt = 0
    if r > 0 and (hitmask & (1 << (idx - _N))):
        cnt += 1
    if r < _N - 1 and (hitmask & (1 << (idx + _N))):
        cnt += 1
    if c > 0 and (hitmask & (1 << (idx - 1))):
        cnt += 1
    if c < _N - 1 and (hitmask & (1 << (idx + 1))):
        cnt += 1
    return cnt


def _target_ok(p, hmask: int, hitmask: int) -> bool:
    _, _, orient, r0, c0, L = p

    # Avoid treating a strict sub-run of contiguous hits as a separate ship unless forced.
    if orient == 0:  # horizontal
        row = r0
        start = c0
        end = c0 + L - 1
        if start > 0 and (hitmask & (1 << (row * _N + start - 1))):
            return False
        if end < _N - 1 and (hitmask & (1 << (row * _N + end + 1))):
            return False

        # If this is a single hit but it already has vertical neighbors, prefer vertical targeting.
        if (hmask & (hmask - 1)) == 0:
            idx = hmask.bit_length() - 1
            rr = idx // _N
            if rr > 0 and (hitmask & (1 << (idx - _N))):
                return False
            if rr < _N - 1 and (hitmask & (1 << (idx + _N))):
                return False

    else:  # vertical
        col = c0
        start = r0
        end = r0 + L - 1
        if start > 0 and (hitmask & (1 << ((start - 1) * _N + col))):
            return False
        if end < _N - 1 and (hitmask & (1 << ((end + 1) * _N + col))):
            return False

        # If this is a single hit but it already has horizontal neighbors, prefer horizontal targeting.
        if (hmask & (hmask - 1)) == 0:
            idx = hmask.bit_length() - 1
            cc = idx % _N
            if cc > 0 and (hitmask & (1 << (idx - 1))):
                return False
            if cc < _N - 1 and (hitmask & (1 << (idx + 1))):
                return False

    return True


def _score_maps(missmask: int, hitmask: int, unknownmask: int):
    target = [0.0] * _CELLS
    hunt = [0.0] * _CELLS

    for p in _ALL_PLACEMENTS:
        mask, cells, orient, _, _, L = p
        if mask & missmask:
            continue

        hmask = mask & hitmask
        mult = _MULT[L]

        if hmask == 0:
            # Pure hunt placement: no known misses and no known hits.
            for idx in cells:
                if unknownmask & (1 << idx):
                    hunt[idx] += mult
            continue

        umask = mask & unknownmask
        if umask == 0:
            continue

        if not _target_ok(p, hmask, hitmask):
            continue

        h = _bit_count(hmask)
        base = mult * (35.0 * h * h + 6.0 * L)

        hpos = []
        if orient == 0:
            for idx in cells:
                if hitmask & (1 << idx):
                    hpos.append(idx % _N)
        else:
            for idx in cells:
                if hitmask & (1 << idx):
                    hpos.append(idx // _N)

        for idx in cells:
            if not (unknownmask & (1 << idx)):
                continue
            pos = idx % _N if orient == 0 else idx // _N
            d = min(abs(pos - hp) for hp in hpos)
            if d < 1:
                d = 1
            adj = _adj_hit_count(idx, hitmask)
            target[idx] += base / (d * d) + 0.25 * base * adj

    return target, hunt


def _remove_one(rem, L):
    for k, x in enumerate(rem):
        if x == L:
            return rem[:k] + rem[k + 1 :]
    return rem


def _unique_lengths(rem):
    out = []
    last = None
    for L in rem:
        if L != last:
            out.append(L)
            last = L
    return out


def _sample_fleet(rem, occ: int, covered: int, hitmask: int, missmask: int, cands_by_len, rng):
    if not rem:
        return occ if covered == hitmask else None

    uncovered = hitmask & ~covered

    if uncovered:
        unique = _unique_lengths(rem)
        best_opts = None

        temp = uncovered
        while temp:
            lsb = temp & -temp
            cell = lsb.bit_length() - 1
            opts = []

            for L in unique:
                for p in _COVERING[L][cell]:
                    pmask = p[0]
                    if (pmask & missmask) == 0 and (pmask & occ) == 0:
                        opts.append((L, p))

            if not opts:
                return None

            if best_opts is None or len(opts) < len(best_opts):
                best_opts = opts

            temp ^= lsb

        rng.shuffle(best_opts)

        for L, p in best_opts:
            pmask = p[0]
            new_rem = _remove_one(rem, L)
            res = _sample_fleet(
                new_rem,
                occ | pmask,
                covered | (pmask & hitmask),
                hitmask,
                missmask,
                cands_by_len,
                rng,
            )
            if res is not None:
                return res

        return None

    # Once all hits are covered, randomly complete the rest of the fleet.
    L = rem[0]
    opts = []
    for p in cands_by_len[L]:
        if (p[0] & occ) == 0:
            opts.append(p)

    if not opts:
        return None

    rng.shuffle(opts)

    limit = len(opts)
    if len(rem) > 2 and limit > 70:
        limit = 70

    for p in opts[:limit]:
        res = _sample_fleet(
            rem[1:],
            occ | p[0],
            covered,
            hitmask,
            missmask,
            cands_by_len,
            rng,
        )
        if res is not None:
            return res

    return None


def _monte_carlo_scores(hitmask: int, missmask: int, unknownmask: int):
    cands_by_len = {}
    for L in _UNIQUE_LENGTHS:
        cands_by_len[L] = [p for p in _PLACEMENTS_BY_LEN[L] if (p[0] & missmask) == 0]

    seed = (
        hitmask
        ^ (hitmask >> 37)
        ^ (missmask << 1)
        ^ (missmask >> 29)
        ^ 0x9E3779B97F4A7C15
    ) & ((1 << 64) - 1)

    rng = random.Random(seed)
    mc = [0] * _CELLS
    samples = 0
    attempts = 0

    desired = 320
    if _bit_count(hitmask) >= 9:
        desired = 240

    deadline = time.perf_counter() + 0.16

    while samples < desired and attempts < desired * 12 and time.perf_counter() < deadline:
        attempts += 1
        occ = _sample_fleet(_FLEET, 0, 0, hitmask, missmask, cands_by_len, rng)
        if occ is None:
            continue

        samples += 1
        m = occ & unknownmask
        while m:
            lsb = m & -m
            idx = lsb.bit_length() - 1
            mc[idx] += 1
            m ^= lsb

    return mc, samples


def _choose_heuristic(unknowns, target, hunt):
    max_t = max(target[i] for i in unknowns)
    max_h = max(hunt[i] for i in unknowns)

    if max_t > 1e-9:
        best = unknowns[0]
        best_s = -1e100
        for i in unknowns:
            s = target[i] + 0.03 * hunt[i] + 1e-6 * _CENTER[i]
            if s > best_s:
                best_s = s
                best = i
        return best

    # Hunt mode: use checkerboard parity because all ships have length at least 2.
    candidates = [i for i in unknowns if (((i // _N) + (i % _N)) & 1) == 0]
    if not candidates:
        candidates = unknowns

    if max_h > 0:
        cand_max = max(hunt[i] for i in candidates)
        if cand_max <= 0:
            candidates = unknowns

    best = candidates[0]
    best_s = -1e100
    for i in candidates:
        s = hunt[i] + 1e-5 * _CENTER[i]
        if s > best_s:
            best_s = s
            best = i
    return best


def _choose_mc(unknowns, target, hunt, mc, samples: int):
    max_t = max(target[i] for i in unknowns)
    max_h = max(hunt[i] for i in unknowns)

    best_all = unknowns[0]
    best_all_s = -1e100
    best_even = None
    best_even_s = -1e100

    inv_samples = 1.0 / float(samples)

    for i in unknowns:
        s = mc[i] * inv_samples

        # Small deterministic bias toward finishing plausible hit-lines.
        if max_t > 1e-9:
            s += 0.14 * (target[i] / max_t)

        # Tiny density and center tie-breaks.
        if max_h > 1e-9:
            s += 0.025 * (hunt[i] / max_h)
        s += 1e-7 * _CENTER[i]

        if s > best_all_s:
            best_all_s = s
            best_all = i

        if (((i // _N) + (i % _N)) & 1) == 0 and s > best_even_s:
            best_even_s = s
            best_even = i

    # In pure hunt mode, keep parity unless the non-parity move is clearly better.
    if max_t <= 1e-9 and best_even is not None and best_even_s >= 0.85 * best_all_s:
        return best_even

    return best_all


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        missmask = 0
        hitmask = 0
        unknownmask = 0

        for r in range(_N):
            for c in range(_N):
                v = board[r][c]
                bit = 1 << (r * _N + c)

                if v == 0:
                    unknownmask |= bit
                elif v == 1:
                    hitmask |= bit
                elif v == -1:
                    missmask |= bit
                elif v > 0:
                    hitmask |= bit
                elif v < 0:
                    missmask |= bit
                else:
                    unknownmask |= bit

        if unknownmask == 0:
            return (0, 0)

        unknowns = _indices(unknownmask)
        target, hunt = _score_maps(missmask, hitmask, unknownmask)

        if hitmask:
            mc, samples = _monte_carlo_scores(hitmask, missmask, unknownmask)
            if samples >= 25:
                idx = _choose_mc(unknowns, target, hunt, mc, samples)
            else:
                idx = _choose_heuristic(unknowns, target, hunt)
        else:
            idx = _choose_heuristic(unknowns, target, hunt)

        return (idx // _N, idx % _N)

    except Exception:
        # Absolute safety fallback: return the first legal unshot cell if one exists.
        for r in range(_N):
            for c in range(_N):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
