
import time

INF = 10**9
WIN = 1000000

ROW_W = [0, 10, 30, 60, 100, 150, 250, 0]
FILE_B = [-5, 0, 3, 6, 6, 3, 0, -5]
PASS_ROW = [0, 0, 20, 80, 180, 350, 600, 0]

ADV_W = [0]*64
ADV_B = [0]*64
CENT = [0]*64
PASS_W_BONUS = [0]*64
PASS_B_BONUS = [0]*64
DEF_W_MASK = [0]*64
ATK_W_MASK = [0]*64
DEF_B_MASK = [0]*64
ATK_B_MASK = [0]*64
PASS_W_MASK = [0]*64
PASS_B_MASK = [0]*64
FWD_W_MASK = [0]*64
FWD_B_MASK = [0]*64

for _s in range(64):
    _r = _s >> 3
    _c = _s & 7
    ADV_W[_s] = ROW_W[_r]
    ADV_B[_s] = ROW_W[7-_r]
    CENT[_s] = FILE_B[_c]
    PASS_W_BONUS[_s] = PASS_ROW[_r]
    PASS_B_BONUS[_s] = PASS_ROW[7-_r]
    if _r < 7:
        FWD_W_MASK[_s] = 1 << (_s + 8)
    if _r > 0:
        FWD_B_MASK[_s] = 1 << (_s - 8)
    m = 0
    if _r > 0:
        if _c > 0:
            m |= 1 << (_s - 9)
        if _c < 7:
            m |= 1 << (_s - 7)
    DEF_W_MASK[_s] = m
    m = 0
    if _r < 7:
        if _c > 0:
            m |= 1 << (_s + 7)
        if _c < 7:
            m |= 1 << (_s + 9)
    ATK_W_MASK[_s] = m
    DEF_B_MASK[_s] = ATK_W_MASK[_s]
    ATK_B_MASK[_s] = DEF_W_MASK[_s]

for _s in range(64):
    _r = _s >> 3
    _c = _s & 7
    mw = 0
    mb = 0
    for _t in range(64):
        _ro = _t >> 3
        _co = _t & 7
        if _ro > _r and abs(_co - _c) <= (_ro - _r + 1):
            mw |= 1 << _t
        if _ro < _r and abs(_co - _c) <= (_r - _ro + 1):
            mb |= 1 << _t
    PASS_W_MASK[_s] = mw
    PASS_B_MASK[_s] = mb


class _Timeout(Exception):
    pass

_NODES = 0
_DEADLINE = 0.0


def _evaluate(me_bb, opp_bb, white_to_move):
    if white_to_move:
        wbb = me_bb
        bbb = opp_bb
    else:
        wbb = opp_bb
        bbb = me_bb
    occ = wbb | bbb
    diff = 0
    bb = wbb
    while bb:
        lsb = bb & -bb
        s = lsb.bit_length() - 1
        bb ^= lsb
        diff += 100 + ADV_W[s] + CENT[s]
        dw = DEF_W_MASK[s]
        aw = ATK_W_MASK[s]
        if wbb & dw:
            diff += 12
            if bbb & aw:
                diff -= 5
        else:
            if bbb & aw:
                diff -= 25
        fw = FWD_W_MASK[s]
        if fw and (occ & fw):
            diff -= 8
        pb = PASS_W_BONUS[s]
        if pb and (bbb & PASS_W_MASK[s]) == 0:
            diff += pb
    bb = bbb
    while bb:
        lsb = bb & -bb
        s = lsb.bit_length() - 1
        bb ^= lsb
        diff -= 100 + ADV_B[s] + CENT[s]
        db = DEF_B_MASK[s]
        ab = ATK_B_MASK[s]
        if bbb & db:
            diff -= 12
            if wbb & ab:
                diff += 5
        else:
            if wbb & ab:
                diff += 25
        fb = FWD_B_MASK[s]
        if fb and (occ & fb):
            diff += 8
        pb = PASS_B_BONUS[s]
        if pb and (wbb & PASS_B_MASK[s]) == 0:
            diff -= pb
    if white_to_move:
        return diff
    else:
        return -diff


def _gen_moves(me_bb, opp_bb, white_to_move):
    occ = me_bb | opp_bb
    moves = []
    is_single = opp_bb != 0 and (opp_bb & (opp_bb - 1)) == 0
    last = 7 if white_to_move else 0
    dr = 1 if white_to_move else -1
    bb = me_bb
    while bb:
        lsb = bb & -bb
        s = lsb.bit_length() - 1
        bb ^= lsb
        r = s >> 3
        c = s & 7
        nr = r + dr
        if nr < 0 or nr > 7:
            continue
        base = nr << 3
        ns = base | c
        bit = 1 << ns
        if not (occ & bit):
            is_win = (nr == last)
            if white_to_move:
                o = ADV_W[ns] + CENT[ns]
            else:
                o = ADV_B[ns] + CENT[ns]
            if is_win:
                o += 100000
            moves.append((s, ns, False, is_win, o))
        if c > 0:
            ns2 = base | (c - 1)
            bit2 = 1 << ns2
            if not (me_bb & bit2):
                if opp_bb & bit2:
                    is_win = (nr == last) or is_single
                    if white_to_move:
                        o = 500 + ADV_W[ns2] + CENT[ns2]
                    else:
                        o = 500 + ADV_B[ns2] + CENT[ns2]
                    if nr == last:
                        o += 100000
                    moves.append((s, ns2, True, is_win, o))
                else:
                    is_win = (nr == last)
                    if white_to_move:
                        o = ADV_W[ns2] + CENT[ns2]
                    else:
                        o = ADV_B[ns2] + CENT[ns2]
                    if is_win:
                        o += 100000
                    moves.append((s, ns2, False, is_win, o))
        if c < 7:
            ns2 = base | (c + 1)
            bit2 = 1 << ns2
            if not (me_bb & bit2):
                if opp_bb & bit2:
                    is_win = (nr == last) or is_single
                    if white_to_move:
                        o = 500 + ADV_W[ns2] + CENT[ns2]
                    else:
                        o = 500 + ADV_B[ns2] + CENT[ns2]
                    if nr == last:
                        o += 100000
                    moves.append((s, ns2, True, is_win, o))
                else:
                    is_win = (nr == last)
                    if white_to_move:
                        o = ADV_W[ns2] + CENT[ns2]
                    else:
                        o = ADV_B[ns2] + CENT[ns2]
                    if is_win:
                        o += 100000
                    moves.append((s, ns2, False, is_win, o))
    moves.sort(key=lambda x: x[4], reverse=True)
    return moves


def _quiescence(me_bb, opp_bb, white_to_move, alpha, beta, ply):
    global _NODES, _DEADLINE
    _NODES += 1
    if (_NODES & 1023) == 0 and time.monotonic() >= _DEADLINE:
        raise _Timeout()
    stand = _evaluate(me_bb, opp_bb, white_to_move)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if ply >= 10:
        return alpha
    moves = _gen_moves(me_bb, opp_bb, white_to_move)
    first = True
    for fr, to, is_cap, is_win, _o in moves:
        if not (is_cap or is_win):
            continue
        first = False
        if is_cap:
            new_opp = opp_bb ^ (1 << to)
        else:
            new_opp = opp_bb
        new_me = (me_bb ^ (1 << fr)) | (1 << to)
        to_rank = to >> 3
        if (white_to_move and to_rank == 7) or ((not white_to_move) and to_rank == 0) or new_opp == 0:
            score = WIN - ply
        else:
            score = -_quiescence(new_opp, new_me, not white_to_move, -beta, -alpha, ply + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def _negamax(me_bb, opp_bb, white_to_move, depth, alpha, beta, ply):
    global _NODES, _DEADLINE
    _NODES += 1
    if (_NODES & 255) == 0 and time.monotonic() >= _DEADLINE:
        raise _Timeout()
    if depth <= 0:
        return _quiescence(me_bb, opp_bb, white_to_move, alpha, beta, ply)
    moves = _gen_moves(me_bb, opp_bb, white_to_move)
    if not moves:
        return -WIN + ply
    best = -INF
    for fr, to, is_cap, is_win, _o in moves:
        if is_cap:
            new_opp = opp_bb ^ (1 << to)
        else:
            new_opp = opp_bb
        new_me = (me_bb ^ (1 << fr)) | (1 << to)
        to_rank = to >> 3
        if (white_to_move and to_rank == 7) or ((not white_to_move) and to_rank == 0) or new_opp == 0:
            score = WIN - ply
        else:
            score = -_negamax(new_opp, new_me, not white_to_move, depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def policy(me, opp, color):
    try:
        global _NODES, _DEADLINE
        start = time.monotonic()
        _DEADLINE = start + 0.88
        _NODES = 0
        white = (color == 'w')
        me_bb = 0
        opp_bb = 0
        for r, c in me:
            me_bb |= 1 << (r * 8 + c)
        for r, c in opp:
            opp_bb |= 1 << (r * 8 + c)
        moves = _gen_moves(me_bb, opp_bb, white)
        if not moves:
            if me:
                f = me[0]
                return (f, f)
            return ((0, 0), (0, 0))
        for fr, to, is_cap, is_win, _o in moves:
            if is_win:
                return ((fr >> 3, fr & 7), (to >> 3, to & 7))
        if len(moves) == 1:
            fr, to, _, _, _ = moves[0]
            return ((fr >> 3, fr & 7), (to >> 3, to & 7))
        ordered = moves
        best_move = ordered[0]
        try:
            for depth in range(1, 8):
                if time.monotonic() >= _DEADLINE - 0.05:
                    break
                alpha_cur = -INF
                beta = INF
                best_this = ordered[0]
                best_score = -INF
                scored = []
                for mv in ordered:
                    if time.monotonic() >= _DEADLINE - 0.02:
                        raise _Timeout()
                    fr, to, is_cap, is_win, _o = mv
                    if is_cap:
                        new_opp = opp_bb ^ (1 << to)
                    else:
                        new_opp = opp_bb
                    new_me = (me_bb ^ (1 << fr)) | (1 << to)
                    to_rank = to >> 3
                    if (white and to_rank == 7) or ((not white) and to_rank == 0) or new_opp == 0:
                        score = WIN
                    else:
                        score = -_negamax(new_opp, new_me, not white, depth - 1, -beta, -alpha_cur, 1)
                    scored.append((score, mv))
                    if score > best_score:
                        best_score = score
                        best_this = mv
                    if score > alpha_cur:
                        alpha_cur = score
                best_move = best_this
                scored.sort(key=lambda x: x[0], reverse=True)
                ordered = [m for _, m in scored]
                if best_score >= WIN - 1000:
                    break
                if time.monotonic() >= _DEADLINE - 0.05:
                    break
        except _Timeout:
            pass
        fr, to, _, _, _ = best_move
        return ((fr >> 3, fr & 7), (to >> 3, to & 7))
    except Exception:
        try:
            me_s = set((int(r), int(c)) for r, c in me)
            opp_s = set((int(r), int(c)) for r, c in opp)
            occ = me_s | opp_s
            w = (color == 'w')
            dr = 1 if w else -1
            last = 7 if w else 0
            for r, c in me:
                nr = r + dr
                if 0 <= nr < 8:
                    if (nr, c) in opp_s:
                        pass
                    if (nr, c) not in occ:
                        if nr == last:
                            return ((r, c), (nr, c))
            for r, c in me:
                nr = r + dr
                if 0 <= nr < 8:
                    for dc in (-1, 1):
                        nc = c + dc
                        if 0 <= nc < 8 and (nr, nc) in opp_s:
                            return ((r, c), (nr, nc))
            for r, c in me:
                nr = r + dr
                if 0 <= nr < 8:
                    if (nr, c) not in occ:
                        return ((r, c), (nr, c))
                    for dc in (-1, 1):
                        nc = c + dc
                        if 0 <= nc < 8 and (nr, nc) not in occ and (nr, nc) not in me_s:
                            return ((r, c), (nr, nc))
            if me:
                f = (int(me[0][0]), int(me[0][1]))
                return (f, f)
        except Exception:
            pass
        return ((0, 0), ((1, 0) if color == 'w' else (-1, 0)))
