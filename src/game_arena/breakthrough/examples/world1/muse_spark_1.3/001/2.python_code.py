
import time

INF = 100000

ROW = [i // 8 for i in range(64)]
COL = [i & 7 for i in range(64)]
CENTER_BONUS = [0, 2, 5, 8, 8, 5, 2, 0]

DEF_W = [0]*64
ATT_W = [0]*64
DEF_B = [0]*64
ATT_B = [0]*64
PASSED_W = [0]*64
PASSED_B = [0]*64

for _idx in range(64):
    _r = _idx >> 3
    _c = _idx & 7
    _m = 0
    if _r > 0:
        if _c > 0:
            _m |= 1 << (_idx - 9)
        if _c < 7:
            _m |= 1 << (_idx - 7)
    DEF_W[_idx] = _m
    ATT_B[_idx] = _m
    _m2 = 0
    if _r < 7:
        if _c > 0:
            _m2 |= 1 << (_idx + 7)
        if _c < 7:
            _m2 |= 1 << (_idx + 9)
    ATT_W[_idx] = _m2
    DEF_B[_idx] = _m2
    _mw = 0
    for _rr in range(_r+1, 8):
        _base = _rr << 3
        if _c > 0:
            _mw |= 1 << (_base + _c - 1)
        _mw |= 1 << (_base + _c)
        if _c < 7:
            _mw |= 1 << (_base + _c + 1)
    PASSED_W[_idx] = _mw
    _mb = 0
    for _rr in range(0, _r):
        _base = _rr << 3
        if _c > 0:
            _mb |= 1 << (_base + _c - 1)
        _mb |= 1 << (_base + _c)
        if _c < 7:
            _mb |= 1 << (_base + _c + 1)
    PASSED_B[_idx] = _mb

try:
    _ = (1).bit_count()
    def popcnt(x):
        return x.bit_count()
except AttributeError:
    def popcnt(x):
        return bin(x).count("1")

class _Timeout(Exception):
    pass

_START = 0.0
_BUDGET = 0.88
_NODES = 0

def eval_white(wbb, bbb):
    s = (popcnt(wbb) - popcnt(bbb)) * 100
    bb = wbb
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        r = idx >> 3
        c = idx & 7
        s += r * 12 + r * r * 2 + CENTER_BONUS[c]
        if (bbb & PASSED_W[idx]) == 0:
            s += 25 + r * 8
        att = bbb & ATT_W[idx]
        if att:
            if (wbb & DEF_W[idx]):
                s -= 4
            else:
                s -= 20 + r * 2
        else:
            if (wbb & DEF_W[idx]):
                s += 9
    bb = bbb
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        r = idx >> 3
        c = idx & 7
        adv = 7 - r
        s -= adv * 12 + adv * adv * 2 + CENTER_BONUS[c]
        if (wbb & PASSED_B[idx]) == 0:
            s -= 25 + adv * 8
        att = wbb & ATT_B[idx]
        if att:
            if (bbb & DEF_B[idx]):
                s += 4
            else:
                s += 20 + adv * 2
        else:
            if (bbb & DEF_B[idx]):
                s -= 9
    return s

def gen_moves(cur, opp, white):
    moves = []
    bb = cur
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb
        r = fr >> 3
        c = fr & 7
        nr = r + 1 if white else r - 1
        if nr < 0 or nr > 7:
            continue
        base = nr << 3
        to0 = base + c
        bit0 = 1 << to0
        if (bit0 & cur) == 0 and (bit0 & opp) == 0:
            moves.append((fr, to0, False))
        if c > 0:
            to1 = base + c - 1
            bit1 = 1 << to1
            if (bit1 & cur) == 0:
                if bit1 & opp:
                    moves.append((fr, to1, True))
                else:
                    moves.append((fr, to1, False))
        if c < 7:
            to2 = base + c + 1
            bit2 = 1 << to2
            if (bit2 & cur) == 0:
                if bit2 & opp:
                    moves.append((fr, to2, True))
                else:
                    moves.append((fr, to2, False))
    return moves

def _move_order_score(fr, to, cap, white):
    tr = to >> 3
    tc = to & 7
    if white:
        adv = tr
        if cap:
            return 1000 + (7 - tr) * 4 + adv * 5 + CENTER_BONUS[tc] * 2
        return adv * 5 + CENTER_BONUS[tc] * 2
    else:
        adv = 7 - tr
        if cap:
            return 1000 + tr * 4 + adv * 5 + CENTER_BONUS[tc] * 2
        return adv * 5 + CENTER_BONUS[tc] * 2

def _ordered(moves, white):
    if len(moves) <= 1:
        return moves
    scored = [(_move_order_score(fr, to, cap, white), fr, to, cap) for (fr, to, cap) in moves]
    scored.sort(reverse=True)
    return [(fr, to, cap) for _, fr, to, cap in scored]

def _negamax(cur, opp, white, depth, alpha, beta, ply):
    global _NODES, _START, _BUDGET
    _NODES += 1
    if (_NODES & 255) == 0 and (time.perf_counter() - _START) > _BUDGET:
        raise _Timeout()
    moves = gen_moves(cur, opp, white)
    if not moves:
        return -INF + ply
    promo = 7 if white else 0
    opp_n = popcnt(opp)
    # immediate win scan
    if opp_n == 1:
        for _, _, cap in moves:
            if cap:
                return INF - ply
    for _, to, _ in moves:
        if (to >> 3) == promo:
            return INF - ply
    if depth <= 0:
        if white:
            s = eval_white(cur, opp)
        else:
            s = -eval_white(opp, cur)
        s += 8
        return s
    ordered = _ordered(moves, white)
    best = -INF
    for fr, to, cap in ordered:
        new_cur = (cur ^ (1 << fr)) | (1 << to)
        if cap:
            new_opp = opp ^ (1 << to)
        else:
            new_opp = opp
        val = -_negamax(new_opp, new_cur, not white, depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(me, opp, color):
    global _START, _BUDGET, _NODES
    my_white = (color == 'w')
    my_bb = 0
    for r, c in me:
        try:
            my_bb |= 1 << (int(r) * 8 + int(c))
        except Exception:
            continue
    opp_bb = 0
    for r, c in opp:
        try:
            opp_bb |= 1 << (int(r) * 8 + int(c))
        except Exception:
            continue
    # fallback legal move helper
    def fallback():
        try:
            mv = gen_moves(my_bb, opp_bb, my_white)
            if mv:
                fr, to, _ = mv[0]
                return ((fr >> 3, fr & 7), (to >> 3, to & 7))
        except Exception:
            pass
        if me:
            try:
                f = (int(me[0][0]), int(me[0][1]))
                # try to find any legal from f
                return (f, f)
            except Exception:
                pass
        return ((0, 0), (1, 0))
    try:
        legal = gen_moves(my_bb, opp_bb, my_white)
        if not legal:
            return fallback()
        promo = 7 if my_white else 0
        opp_n = popcnt(opp_bb)
        # instant win
        for fr, to, cap in legal:
            if (to >> 3) == promo:
                return ((fr >> 3, fr & 7), (to >> 3, to & 7))
            if cap and opp_n == 1:
                return ((fr >> 3, fr & 7), (to >> 3, to & 7))
        _START = time.perf_counter()
        _BUDGET = 0.88
        _NODES = 0
        ordered = _ordered(legal, my_white)
        best_fr, best_to = ordered[0][0], ordered[0][1]
        # iterative deepening
        for depth in range(1, 15):
            # put current best first
            try:
                # move best to front for efficiency
                for i in range(len(ordered)):
                    if ordered[i][0] == best_fr and ordered[i][1] == best_to:
                        if i != 0:
                            ordered[0], ordered[i] = ordered[i], ordered[0]
                        break
                scored_moves = []
                alpha = -INF
                beta = INF
                cur_best_val = -INF
                cur_best = None
                for fr, to, cap in ordered:
                    new_cur = (my_bb ^ (1 << fr)) | (1 << to)
                    if cap:
                        new_opp = opp_bb ^ (1 << to)
                    else:
                        new_opp = opp_bb
                    # root instant win already handled, but check again
                    if (to >> 3) == promo or new_opp == 0:
                        return ((fr >> 3, fr & 7), (to >> 3, to & 7))
                    val = -_negamax(new_opp, new_cur, not my_white, depth - 1, -beta, -alpha, 1)
                    scored_moves.append((val, fr, to, cap))
                    if val > cur_best_val:
                        cur_best_val = val
                        cur_best = (fr, to)
                    if val > alpha:
                        alpha = val
                # sort for next iteration
                scored_moves.sort(reverse=True)
                ordered = [(fr, to, cap) for _, fr, to, cap in scored_moves]
                best_fr, best_to = ordered[0][1], ordered[0][2] if False else (ordered[0][0], ordered[0][1])
                # unpack correctly
                best_fr = ordered[0][0]
                best_to = ordered[0][1]
                if cur_best_val >= INF - 1000:
                    break
                if (time.perf_counter() - _START) > 0.75 and depth >= 3:
                    # leave margin, stop if deep enough
                    # continue only if little time used
                    pass
                if (time.perf_counter() - _START) > _BUDGET - 0.05:
                    break
            except _Timeout:
                break
        return ((best_fr >> 3, best_fr & 7), (best_to >> 3, best_to & 7))
    except Exception:
        try:
            return fallback()
        except Exception:
            if me and opp is not None:
                try:
                    return ((int(me[0][0]), int(me[0][1])), (int(me[0][0]), int(me[0][1])))
                except Exception:
                    pass
            return ((1, 0), (2, 0))
