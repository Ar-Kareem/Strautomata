
from typing import List, Tuple

W_PIP = 4.0
W_OFF = 30.0
LOOKAHEAD_K = 6

# Point values are for a player moving 23 -> 0 whose home board is 0..5.
POINT_VAL = [
     7.0,  9.0, 13.0, 18.0, 30.0, 24.0,
    10.0, 11.0, 12.0, 13.0, 12.0, 11.0,
     8.0,  8.0,  7.0,  7.0,  6.0,  6.0,
    15.0, 26.0, 22.0, 14.0,  9.0,  6.0,
]
PRIME_BONUS = {2: 7.0, 3: 17.0, 4: 36.0, 5: 68.0, 6: 112.0}

# (low, high, probability)
_ROLLS = []
for _a in range(1, 7):
    for _b in range(_a, 7):
        _ROLLS.append((_a, _b, (1.0 / 36.0) if _a == _b else (1.0 / 18.0)))

# A move state is (points, foe_points, bar, foe_bar, off), in the mover's
# own forward coordinates: home is 0..5 and movement is toward lower indices.
MoveState = Tuple[List[int], List[int], int, int, int]


def _as24(v) -> List[int]:
    try:
        xs = list(v)
    except Exception:
        xs = []
    xs = (xs + [0] * 24)[:24]
    out = []
    for x in xs:
        try:
            n = int(x)
        except Exception:
            n = 0
        out.append(n if n > 0 else 0)
    return out


def _as_int(v) -> int:
    try:
        n = int(v)
    except Exception:
        n = 0
    return n if n > 0 else 0


def _all_home(p: List[int], bar: int) -> bool:
    return bar == 0 and sum(p[6:]) == 0


def _moves_for_die(st: MoveState, d: int):
    p, o, bp, bo, off = st
    res = []

    if bp > 0:
        dest = 24 - d
        if 0 <= dest < 24 and o[dest] < 2:
            np = p.copy()
            no = o.copy()
            nbp = bp - 1
            nbo = bo
            if no[dest] == 1:
                no[dest] = 0
                nbo += 1
            np[dest] += 1
            res.append((-1, (np, no, nbp, nbo, off)))
        return res

    home = _all_home(p, bp)
    for i, c in enumerate(p):
        if c <= 0:
            continue
        dest = i - d
        if dest >= 0:
            if o[dest] < 2:
                np = p.copy()
                no = o.copy()
                nbo = bo
                np[i] -= 1
                if no[dest] == 1:
                    no[dest] = 0
                    nbo += 1
                np[dest] += 1
                res.append((i, (np, no, bp, nbo, off)))
        else:
            if home:
                dist = i + 1
                if d == dist or (d > dist and not any(p[i + 1:6])):
                    np = p.copy()
                    no = o.copy()
                    np[i] -= 1
                    res.append((i, (np, no, bp, bo, off + 1)))
    return res


def _gen_sequences(st: MoveState, dice_order: Tuple[int, ...]):
    out = []

    def rec(cur: MoveState, idx: int, seq: List[int]):
        if idx == len(dice_order):
            out.append((seq, cur))
            return
        moves = _moves_for_die(cur, dice_order[idx])
        if not moves:
            out.append((seq, cur))
            return
        for src, nst in moves:
            rec(nst, idx + 1, seq + [src])

    rec(st, 0, [])
    return out


def _pips(p: List[int], bar: int) -> int:
    return sum((i + 1) * c for i, c in enumerate(p)) + 25 * bar


def _side_score(p: List[int], foe: List[int], bar_p: int, bar_foe: int) -> float:
    # p and foe are each in their own forward coordinates.  The shot formula
    # below maps a p-point i to the foe's coordinate 23-i.
    sc = 0.0

    for i, n in enumerate(p):
        if n >= 2:
            factor = 1.0 + 0.03 * min(n - 2, 3) - 0.02 * max(0, n - 5)
            sc += POINT_VAL[i] * factor

    i = 0
    while i < 24:
        if p[i] >= 2:
            j = i + 1
            while j < 24 and p[j] >= 2:
                j += 1
            L = j - i
            if L >= 2:
                sc += PRIME_BONUS[min(L, 6)] + max(0, L - 6) * 15.0
            i = j
        else:
            i += 1

    if bar_foe > 0:
        blocked = sum(1 for x in p[:6] if x >= 2)
        sc += 15.0 * blocked * min(bar_foe, 2)
        if blocked == 6:
            sc += 160.0 + 50.0 * (bar_foe - 1)

    sc -= 7.0 * bar_p

    for i, n in enumerate(p):
        if n != 1:
            continue
        hitmask = 0
        base = 23 - i
        md = 6 if i >= 6 else i
        for d in range(1, md + 1):
            if foe[base + d] > 0:
                hitmask |= 1 << d
        if bar_foe > 0 and i < 6:
            hitmask |= 1 << (i + 1)
        k = bin(hitmask).count("1")
        if k:
            prob = 1.0 - ((6 - k) * (6 - k)) / 36.0
            race_cost = W_PIP * (24 - i)
            strategic = 4.0 + 0.35 * POINT_VAL[i]
            sc -= prob * (race_cost + strategic)
        sc -= 0.08 * (24 - i)

    return sc


def _eval_board(my: List[int], opp: List[int], my_bar: int, opp_bar: int,
                my_off: int, opp_off: int) -> float:
    if my_off >= 15:
        return 1.0e9 + 1000.0 * (my_off - opp_off) - 10.0 * opp_bar
    if opp_off >= 15:
        return -1.0e9 + 1000.0 * (my_off - opp_off) - 10.0 * my_bar

    opp_fwd = [opp[23 - i] for i in range(24)]
    my_pips = _pips(my, my_bar)
    opp_pips = _pips(opp_fwd, opp_bar)

    return (W_PIP * (opp_pips - my_pips)
            + W_OFF * (my_off - opp_off)
            + _side_score(my, opp_fwd, my_bar, opp_bar)
            - _side_score(opp_fwd, my, opp_bar, my_bar))


def _candidates(my: List[int], opp: List[int], my_bar: int, opp_bar: int,
                my_off: int, dice: List[int]):
    st = (my, opp, my_bar, opp_bar, my_off)
    cands = []

    if not dice:
        return [("H", [], st, 0)]

    if len(dice) == 1:
        d = dice[0]
        for seq, fin in _gen_sequences(st, (d,)):
            cands.append(("H", seq, fin, d))
    else:
        hi = max(dice)
        lo = min(dice)
        orders = [(hi, lo, "H")] if hi == lo else [(hi, lo, "H"), (lo, hi, "L")]
        for d1, d2, oc in orders:
            for seq, fin in _gen_sequences(st, (d1, d2)):
                cands.append((oc, seq, fin, d1))

    maxlen = max(len(seq) for _, seq, _, _ in cands)
    if len(dice) == 2:
        hi = max(dice)
        if maxlen == 2:
            cands = [c for c in cands if len(c[1]) == 2]
        elif maxlen == 1:
            high_first = [c for c in cands if len(c[1]) == 1 and c[3] == hi]
            cands = high_first if high_first else [c for c in cands if len(c[1]) == 1]
        else:
            cands = [c for c in cands if len(c[1]) == 0]
    else:
        if maxlen == 1:
            cands = [c for c in cands if len(c[1]) == 1]
        else:
            cands = [c for c in cands if len(c[1]) == 0]

    return cands


def _best_reply_value(my: List[int], opp: List[int], my_bar: int, opp_bar: int,
                      my_off: int, opp_off: int) -> float:
    if my_off >= 15 or opp_off >= 15:
        return _eval_board(my, opp, my_bar, opp_bar, my_off, opp_off)

    opp_fwd = [opp[23 - i] for i in range(24)]
    my_as_seen_by_opp = [my[23 - i] for i in range(24)]
    total = 0.0

    for lo, hi, prob in _ROLLS:
        orders = [(hi, lo)] if hi == lo else [(hi, lo), (lo, hi)]
        cand = []
        st = (opp_fwd, my_as_seen_by_opp, opp_bar, my_bar, opp_off)
        for order in orders:
            for seq, fin in _gen_sequences(st, order):
                cand.append((order[0], seq, fin))

        if cand:
            maxlen = max(len(seq) for _, seq, _ in cand)
            if maxlen == 2:
                cand = [c for c in cand if len(c[1]) == 2]
            elif maxlen == 1:
                high_first = [c for c in cand if len(c[1]) == 1 and c[0] == hi]
                cand = high_first if high_first else [c for c in cand if len(c[1]) == 1]
            else:
                cand = [c for c in cand if len(c[1]) == 0]

        best = None
        for _, _, fin in cand:
            q2, r2, ob2, mb2, oo2 = fin
            my2 = [r2[23 - i] for i in range(24)]
            opp2 = [q2[23 - i] for i in range(24)]
            val = _eval_board(my2, opp2, mb2, ob2, my_off, oo2)
            if best is None or val < best:
                best = val

        total += prob * (best if best is not None else
                         _eval_board(my, opp, my_bar, opp_bar, my_off, opp_off))

    return total


def _encode(order: str, seq: List[int]) -> str:
    toks = [("B" if s == -1 else "A%d" % s) for s in seq]
    if len(toks) == 0:
        return order + ":P,P"
    if len(toks) == 1:
        return order + ":" + toks[0] + ",P"
    return order + ":" + toks[0] + "," + toks[1]


def _choose(state: dict) -> str:
    my = _as24(state.get("my_pts"))
    opp = _as24(state.get("opp_pts"))
    my_bar = _as_int(state.get("my_bar"))
    opp_bar = _as_int(state.get("opp_bar"))
    my_off = _as_int(state.get("my_off"))
    opp_off = _as_int(state.get("opp_off"))

    raw_dice = state.get("dice") or []
    dice = []
    for x in list(raw_dice)[:2]:
        try:
            d = int(x)
        except Exception:
            d = 0
        if 1 <= d <= 6:
            dice.append(d)

    cands = _candidates(my, opp, my_bar, opp_bar, my_off, dice)
    if not cands:
        return "H:P,P"
    if all(len(seq) == 0 for _, seq, _, _ in cands):
        return _encode(cands[0][0], cands[0][1])

    scored = []
    for c in cands:
        p, o, bp, bo, offp = c[2]
        val = _eval_board(p, o, bp, bo, offp, opp_off)
        scored.append((val, c))
    scored.sort(key=lambda x: x[0], reverse=True)

    best_c = scored[0][1]
    if best_c[2][4] >= 15:
        return _encode(best_c[0], best_c[1])

    best_key = None
    for imm, c in scored[:LOOKAHEAD_K]:
        p, o, bp, bo, offp = c[2]
        if offp >= 15:
            val = imm
        else:
            val = _best_reply_value(p, o, bp, bo, offp, opp_off)
        key = (val, imm, len(c[1]))
        if best_key is None or key > best_key:
            best_key = key
            best_c = c

    return _encode(best_c[0], best_c[1])


def policy(state: dict) -> str:
    try:
        return _choose(state)
    except Exception:
        # Last-resort legal move generation; evaluation is skipped here.
        try:
            my = _as24(state.get("my_pts"))
            opp = _as24(state.get("opp_pts"))
            my_bar = _as_int(state.get("my_bar"))
            opp_bar = _as_int(state.get("opp_bar"))
            my_off = _as_int(state.get("my_off"))
            raw_dice = state.get("dice") or []
            dice = []
            for x in list(raw_dice)[:2]:
                try:
                    d = int(x)
                except Exception:
                    d = 0
                if 1 <= d <= 6:
                    dice.append(d)
            cands = _candidates(my, opp, my_bar, opp_bar, my_off, dice)
            if cands:
                return _encode(cands[0][0], cands[0][1])
        except Exception:
            pass
        return "H:P,P"
