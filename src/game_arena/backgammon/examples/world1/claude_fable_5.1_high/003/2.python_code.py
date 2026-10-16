
import time

# ---------- precomputed hit tables ----------
DIRECT = [0] * 7
for _d in range(1, 7):
    _m = 0
    for _i in range(6):
        for _j in range(6):
            if _i + 1 == _d or _j + 1 == _d:
                _m |= 1 << (_i * 6 + _j)
    DIRECT[_d] = _m

# COMBOS[d]: list of (bits, any_offsets, all_offsets)
COMBOS = [[] for _ in range(25)]
for _d1 in range(1, 7):
    for _d2 in range(1, 7):
        if _d1 < _d2:
            _s = _d1 + _d2
            _bits = (1 << ((_d1 - 1) * 6 + (_d2 - 1))) | (1 << ((_d2 - 1) * 6 + (_d1 - 1)))
            COMBOS[_s].append((_bits, (_d1, _d2), ()))
for _dd in range(1, 7):
    _bit = 1 << ((_dd - 1) * 6 + (_dd - 1))
    for _k in (2, 3, 4):
        _s = _dd * _k
        if _s <= 24:
            COMBOS[_s].append((_bit, (), tuple(_dd * _i for _i in range(1, _k))))

try:
    (0).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

ROLLS = []
for _i in range(1, 7):
    for _j in range(_i, 7):
        ROLLS.append((_i, _j, 1 if _i == _j else 2))

PV = [1.0, 1.5, 2.5, 4.0, 5.0, 4.0, 4.5, 3.0, 2.0, 1.5, 1.5, 1.5,
      2.0, 1.0, 1.0, 1.0, 1.5, 2.0, 3.0, 4.0, 3.5, 2.5, 1.5, 1.0]


# ---------- move generation ----------
def single_moves(b, bar, d):
    moves = []
    if bar > 0:
        dst = 24 - d
        if b[dst] >= -1:
            moves.append((24, dst))
        return moves
    can_off = True
    for p in range(6, 24):
        if b[p] > 0:
            can_off = False
            break
    for p in range(24):
        if b[p] > 0:
            dst = p - d
            if dst >= 0:
                if b[dst] >= -1:
                    moves.append((p, dst))
            elif can_off:
                if dst == -1:
                    moves.append((p, -1))
                else:
                    ok = True
                    for q in range(p + 1, 6):
                        if b[q] > 0:
                            ok = False
                            break
                    if ok:
                        moves.append((p, -1))
    return moves


def apply_move(b, bar, obar, off, mv):
    b = b[:]
    src, dst = mv
    if src == 24:
        bar -= 1
    else:
        b[src] -= 1
    if dst == -1:
        off += 1
    else:
        if b[dst] == -1:
            b[dst] = 1
            obar += 1
        else:
            b[dst] += 1
    return b, bar, obar, off


def gen_actions(b, bar, obar, off, dice):
    if len(dice) == 0:
        return [([], (b, bar, obar, off))]
    if len(dice) == 1:
        d = dice[0]
        ms = single_moves(b, bar, d)
        if not ms:
            return [([], (b, bar, obar, off))]
        return [([(d, m[0])], apply_move(b, bar, obar, off, m)) for m in ms]
    d1, d2 = dice[0], dice[1]
    full = []
    partial = {d1: [], d2: []}
    orders = [(d1, d2)] if d1 == d2 else [(d1, d2), (d2, d1)]
    for a, c in orders:
        ms = single_moves(b, bar, a)
        for m in ms:
            s1 = apply_move(b, bar, obar, off, m)
            ms2 = single_moves(s1[0], s1[1], c)
            if ms2:
                for m2 in ms2:
                    s2 = apply_move(s1[0], s1[1], s1[2], s1[3], m2)
                    full.append(([(a, m[0]), (c, m2[0])], s2))
            else:
                partial[a].append(([(a, m[0])], s1))
    if full:
        return full
    hi = max(d1, d2)
    lo = min(d1, d2)
    if partial[hi]:
        return partial[hi]
    if partial[lo]:
        return partial[lo]
    return [([], (b, bar, obar, off))]


def encode(seq, dice):
    if not seq:
        return 'H:P,P'
    hi = max(dice) if dice else 0

    def tok(src):
        return 'B' if src == 24 else 'A%d' % src
    order = 'H' if seq[0][0] == hi else 'L'
    t1 = tok(seq[0][1])
    t2 = tok(seq[1][1]) if len(seq) > 1 else 'P'
    return '%s:%s,%s' % (order, t1, t2)


# ---------- evaluation ----------
def combo(b, q, d):
    m = 0
    for bits, anyo, allo in COMBOS[d]:
        if anyo:
            ok = False
            for o in anyo:
                if b[q + o] <= 1:
                    ok = True
                    break
        else:
            ok = True
            for o in allo:
                if b[q + o] > 1:
                    ok = False
                    break
        if ok:
            m |= bits
    return m


def hit_mask(b, p, o_pos, obar):
    mask = 0
    if obar >= 2:
        d = p + 1
        if d <= 6:
            mask |= DIRECT[d]
        return mask
    if obar == 1:
        d = p + 1
        if d <= 6:
            mask |= DIRECT[d]
        mask |= combo(b, -1, d)
        for q in o_pos:
            if q >= p:
                break
            d = p - q
            if d <= 6:
                mask |= DIRECT[d]
        return mask
    for q in o_pos:
        if q >= p:
            break
        d = p - q
        if d <= 6:
            mask |= DIRECT[d]
        mask |= combo(b, q, d)
    return mask


def side(b, bar, obar, off, opp_on_roll):
    score = 2.0 * off
    pips = 25 * bar
    x_pos = []
    o_pos = []
    for p in range(24):
        v = b[p]
        if v > 0:
            pips += (p + 1) * v
            x_pos.append(p)
        elif v < 0:
            o_pos.append(p)
    score -= pips
    if not x_pos and bar == 0:
        return score
    x_rear = 24 if bar > 0 else x_pos[-1]
    o_rear = -1 if obar > 0 else (o_pos[0] if o_pos else 99)
    if x_rear < o_rear:
        # pure race
        n_out = 0
        for p in x_pos:
            if p > 5:
                n_out += b[p]
        score -= 0.5 * n_out
        for p in range(6):
            if b[p] > 3:
                score -= 0.1 * (b[p] - 3)
        return score
    o_home = 0
    for p in range(18, 24):
        if b[p] <= -2:
            o_home += 1
    if bar:
        score -= bar * (3.0 + 1.5 * o_home + (8.0 if o_home >= 6 else 0.0))
    o_cum = [0] * 25
    c = obar
    for p in range(24):
        o_cum[p] = c
        v = b[p]
        if v < 0:
            c -= v
    o_cum[24] = c
    blot_w = 1.0 if opp_on_roll else 0.6
    base_hit = 2.0 + 2.0 * o_home
    n_back = bar
    for p in x_pos:
        v = b[p]
        if v == 1:
            if o_cum[p] > 0:
                m = hit_mask(b, p, o_pos, obar)
                if m:
                    score -= blot_w * (popcount(m) / 36.0) * (base_hit + 0.85 * (24 - p))
        else:
            nb = o_cum[p]
            f = 0.15 if nb == 0 else min(1.0, 0.5 + 0.25 * nb)
            score += PV[p] * f
            if v > 3:
                score -= 0.4 * (v - 3)
        if p >= 18:
            n_back += v
        if p >= 6:
            blk = 0
            for x in range(p - 6, p):
                if b[x] <= -2:
                    blk += 1
            if blk >= 2:
                score -= 0.3 * blk * min(v, 3)
    if n_back > 2:
        score -= 1.0 * (n_back - 2)
    dead = max(0, b[0] - 2) + max(0, b[1] - 2)
    score -= 0.7 * dead
    run = 0
    for p in range(14):
        if p < 13 and b[p] >= 2:
            run += 1
        else:
            if run >= 3:
                s = p - run
                nt = o_cum[s]
                if nt > 0:
                    score += 1.5 * ((run - 1) ** 1.5) * min(1.0, 0.5 * nt)
            run = 0
    return score


def flip(b):
    return [-b[23 - i] for i in range(24)]


def eval_after(b, bar, obar, off, ooff):
    # position after the mover's move; opponent is on roll
    return side(b, bar, obar, off, True) - side(flip(b), obar, bar, ooff, False)


def expected_opp(b, bar, obar, off, ooff, deadline):
    fb = flip(b)
    total = 0.0
    for d1, d2, w in ROLLS:
        acts = gen_actions(fb, obar, bar, ooff, [d1, d2])
        best = None
        seen = set()
        for seq, st in acts:
            key = (tuple(st[0]), st[1], st[2], st[3])
            if key in seen:
                continue
            seen.add(key)
            v = eval_after(st[0], st[1], st[2], st[3], off)
            if best is None or v > best:
                best = v
        total += w * best
        if time.time() > deadline:
            return None
    return total / 36.0


# ---------- policy ----------
def policy(state):
    start = time.time()
    try:
        my = [int(x) for x in state['my_pts']]
        op = [int(x) for x in state['opp_pts']]
        b = [my[i] - op[i] for i in range(24)]
        bar = int(state.get('my_bar', 0))
        obar = int(state.get('opp_bar', 0))
        off = int(state.get('my_off', 0))
        ooff = int(state.get('opp_off', 0))
        dice = [int(d) for d in (state.get('dice') or [])]
    except Exception:
        return 'H:P,P'
    if not dice:
        return 'H:P,P'
    try:
        acts = gen_actions(b, bar, obar, off, dice)
    except Exception:
        return 'H:P,P'
    if not acts:
        return 'H:P,P'
    fallback = encode(acts[0][0], dice)
    try:
        uniq = {}
        for seq, st in acts:
            key = (tuple(st[0]), st[1], st[2], st[3])
            if key not in uniq:
                uniq[key] = seq
        cands = []
        for key, seq in uniq.items():
            nb = list(key[0])
            v = eval_after(nb, key[1], key[2], key[3], ooff)
            cands.append((v, seq, nb, key[1], key[2], key[3]))
        cands.sort(key=lambda c: -c[0])
        best = cands[0]
        if len(cands) == 1:
            return encode(best[1], dice)
        deadline = start + 0.6
        top = cands[0][0]
        best2 = None
        for c in cands:
            if c[0] < top - 20.0:
                break
            if time.time() > deadline:
                break
            ev = expected_opp(c[2], c[3], c[4], c[5], ooff, deadline)
            if ev is None:
                break
            val = -ev
            if best2 is None or val > best2[0]:
                best2 = (val, c[1])
        if best2 is not None:
            return encode(best2[1], dice)
        return encode(best[1], dice)
    except Exception:
        return fallback
