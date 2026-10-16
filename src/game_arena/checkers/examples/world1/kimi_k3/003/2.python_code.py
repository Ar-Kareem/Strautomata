
import time

_MASK64 = (1 << 64) - 1
_INF = 1 << 30
_MATE = 1 << 20
_MAN_VAL = 100
_KING_VAL = 300
_EXACT, _LOWER, _UPPER = 0, 1, 2


class _Timeout(Exception):
    pass


def _onboard(r, c):
    return 0 <= r < 8 and 0 <= c < 8


_KING_MOVES = [[] for _ in range(64)]
_KING_CAPS = [[] for _ in range(64)]
_MAN_MOVES_B = [[] for _ in range(64)]
_MAN_CAPS_B = [[] for _ in range(64)]
_MAN_MOVES_W = [[] for _ in range(64)]
_MAN_CAPS_W = [[] for _ in range(64)]

for _s in range(64):
    _r, _c = _s >> 3, _s & 7
    for _dr, _dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        _nr, _nc = _r + _dr, _c + _dc
        if _onboard(_nr, _nc):
            _KING_MOVES[_s].append((_nr << 3) | _nc)
        _mr, _mc = _r + _dr, _c + _dc
        _tr, _tc = _r + 2 * _dr, _c + 2 * _dc
        if _onboard(_mr, _mc) and _onboard(_tr, _tc):
            _KING_CAPS[_s].append(((_mr << 3) | _mc, (_tr << 3) | _tc))

    for _dr, _mv, _cp in (
        (-1, _MAN_MOVES_B, _MAN_CAPS_B),
        (1, _MAN_MOVES_W, _MAN_CAPS_W),
    ):
        for _dc in (-1, 1):
            _nr, _nc = _r + _dr, _c + _dc
            if _onboard(_nr, _nc):
                _mv[_s].append((_nr << 3) | _nc)
            _mr, _mc = _r + _dr, _c + _dc
            _tr, _tc = _r + 2 * _dr, _c + 2 * _dc
            if _onboard(_mr, _mc) and _onboard(_tr, _tc):
                _cp[_s].append(((_mr << 3) | _mc, (_tr << 3) | _tc))

_MAN_ADV = (0, 3, 8, 15, 25, 38, 60, 0)
_CENTER = [0] * 64
_MAN_EDGE = [0] * 64
_KING_SQUARE = [0] * 64
for _s in range(64):
    _r, _c = _s >> 3, _s & 7
    _cen = (
        (3 if 2 <= _r <= 5 else 0)
        + (3 if 2 <= _c <= 5 else 0)
        + (2 if _r in (3, 4) else 0)
        + (2 if _c in (3, 4) else 0)
    )
    _CENTER[_s] = _cen
    _MAN_EDGE[_s] = -5 if (_c == 0 or _c == 7) else 0
    _KING_SQUARE[_s] = 2 * _cen - (6 if (_r in (0, 7) or _c in (0, 7)) else 0)


def _bits(squares):
    b = 0
    for sq in squares:
        r, c = sq
        b |= 1 << ((int(r) << 3) | int(c))
    return b


def _gen_moves(bm, bk, wm, wk, side):
    occ = bm | bk | wm | wk
    if side == "b":
        men, kings = bm, bk
        opp = wm | wk
        man_moves, man_caps = _MAN_MOVES_B, _MAN_CAPS_B
    else:
        men, kings = wm, wk
        opp = bm | bk
        man_moves, man_caps = _MAN_MOVES_W, _MAN_CAPS_W

    caps = []
    x = men
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for over, to in man_caps[fr]:
            if ((opp >> over) & 1) and not ((occ >> to) & 1):
                caps.append((fr, to, over))
    x = kings
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for over, to in _KING_CAPS[fr]:
            if ((opp >> over) & 1) and not ((occ >> to) & 1):
                caps.append((fr, to, over))
    if caps:
        return caps

    moves = []
    x = men
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for to in man_moves[fr]:
            if not ((occ >> to) & 1):
                moves.append((fr, to, -1))
    x = kings
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for to in _KING_MOVES[fr]:
            if not ((occ >> to) & 1):
                moves.append((fr, to, -1))
    return moves


def _do_move(bm, bk, wm, wk, side, move):
    fr, to, over = move
    bit = 1 << fr
    dest = 1 << to
    if side == "b":
        if bk & bit:
            bk = (bk & ~bit) | dest
        else:
            bm &= ~bit
            if to < 8:
                bk |= dest
            else:
                bm |= dest
        if over >= 0:
            ob = 1 << over
            if wm & ob:
                wm &= ~ob
            else:
                wk &= ~ob
        return bm, bk, wm, wk, "w"

    if wk & bit:
        wk = (wk & ~bit) | dest
    else:
        wm &= ~bit
        if to >= 56:
            wk |= dest
        else:
            wm |= dest
    if over >= 0:
        ob = 1 << over
        if bm & ob:
            bm &= ~ob
        else:
            bk &= ~ob
    return bm, bk, wm, wk, "b"


def _evaluate(bm, bk, wm, wk, side):
    occ = bm | bk | wm | wk

    def color_score(men, kings, col):
        sc = 0
        if col == "b":
            man_moves = _MAN_MOVES_B
            x = men
            while x:
                lsb = x & -x
                s = lsb.bit_length() - 1
                x ^= lsb
                r = s >> 3
                adv = 7 - r
                sc += _MAN_VAL + _MAN_ADV[adv] + _CENTER[s] + _MAN_EDGE[s]
                if adv == 0:
                    sc += 5
                mob = 0
                for t in man_moves[s]:
                    if not ((occ >> t) & 1):
                        mob += 1
                sc += mob * 2
        else:
            man_moves = _MAN_MOVES_W
            x = men
            while x:
                lsb = x & -x
                s = lsb.bit_length() - 1
                x ^= lsb
                r = s >> 3
                sc += _MAN_VAL + _MAN_ADV[r] + _CENTER[s] + _MAN_EDGE[s]
                if r == 0:
                    sc += 5
                mob = 0
                for t in man_moves[s]:
                    if not ((occ >> t) & 1):
                        mob += 1
                sc += mob * 2

        x = kings
        while x:
            lsb = x & -x
            s = lsb.bit_length() - 1
            x ^= lsb
            sc += _KING_VAL + _KING_SQUARE[s]
            mob = 0
            for t in _KING_MOVES[s]:
                if not ((occ >> t) & 1):
                    mob += 1
            sc += mob * 5
        return sc

    black = color_score(bm, bk, "b")
    white = color_score(wm, wk, "w")
    return black - white + 3 if side == "b" else white - black + 3


def _move_score(bm, bk, wm, wk, side, move, history):
    fr, to, over = move
    if side == "b":
        king = (bk >> fr) & 1
        promo = (not king) and to < 8
        victim = 0
        if over >= 0:
            victim = _KING_VAL if ((wk >> over) & 1) else _MAN_VAL
        adv_delta = (fr >> 3) - (to >> 3)
    else:
        king = (wk >> fr) & 1
        promo = (not king) and to >= 56
        victim = 0
        if over >= 0:
            victim = _KING_VAL if ((bk >> over) & 1) else _MAN_VAL
        adv_delta = (to >> 3) - (fr >> 3)

    if over >= 0:
        attacker = _KING_VAL if king else _MAN_VAL
        return 100000 + victim * 12 + (5000 if promo else 0) - (attacker // 4) + _CENTER[to]

    score = history.get((fr, to), 0) + _CENTER[to] + adv_delta * 5
    if promo:
        score += 70000
    if king:
        score += _KING_SQUARE[to] - _KING_SQUARE[fr]
    return score


def _ordered_moves(moves, hint, history, bm, bk, wm, wk, side):
    return sorted(
        moves,
        key=lambda m: _move_score(bm, bk, wm, wk, side, m, history)
        + ((1 << 60) if m == hint else 0),
        reverse=True,
    )


def _negamax(
    bm,
    bk,
    wm,
    wk,
    side,
    depth,
    alpha,
    beta,
    ply,
    deadline,
    tt,
    history,
    counter,
):
    counter[0] += 1
    if (counter[0] & 255) == 0 and time.perf_counter() >= deadline:
        raise _Timeout

    alpha_orig, beta_orig = alpha, beta
    key = (bm, bk, wm, wk, side)
    tt_move = None
    if depth > 0:
        ent = tt.get(key)
        if ent is not None:
            ed, ev, ef, em = ent
            tt_move = em
            if ed >= depth:
                if ef == _EXACT:
                    return ev
                if ef == _LOWER:
                    if ev > alpha:
                        alpha = ev
                else:
                    if ev < beta:
                        beta = ev
                if alpha >= beta:
                    return ev

    moves = _gen_moves(bm, bk, wm, wk, side)
    if not moves:
        return -_MATE + ply

    if depth <= 0:
        if moves[0][2] != -1:
            best = -_INF
            for m in moves:
                nbm, nbk, nwm, nwk, nside = _do_move(bm, bk, wm, wk, side, m)
                val = -_negamax(
                    nbm,
                    nbk,
                    nwm,
                    nwk,
                    nside,
                    0,
                    -beta,
                    -alpha,
                    ply + 1,
                    deadline,
                    tt,
                    history,
                    counter,
                )
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        return _evaluate(bm, bk, wm, wk, side)

    moves = _ordered_moves(moves, tt_move, history, bm, bk, wm, wk, side)
    best = -_INF
    best_move = moves[0]
    for m in moves:
        nbm, nbk, nwm, nwk, nside = _do_move(bm, bk, wm, wk, side, m)
        val = -_negamax(
            nbm,
            nbk,
            nwm,
            nwk,
            nside,
            depth - 1,
            -beta,
            -alpha,
            ply + 1,
            deadline,
            tt,
            history,
            counter,
        )
        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            if m[2] < 0:
                history[(m[0], m[1])] = history.get((m[0], m[1]), 0) + depth * depth
            break

    if depth > 0:
        if best <= alpha_orig:
            flag = _UPPER
        elif best >= beta_orig:
            flag = _LOWER
        else:
            flag = _EXACT
        if len(tt) > 120000:
            tt.clear()
        tt[key] = (depth, best, flag, best_move)
    return best


def _coord_move(move):
    fr, to, _ = move
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    side = "b" if str(color).lower() == "b" else "w"
    if side == "b":
        bm = _bits(my_men)
        bk = _bits(my_kings)
        wm = _bits(opp_men)
        wk = _bits(opp_kings)
    else:
        wm = _bits(my_men)
        wk = _bits(my_kings)
        bm = _bits(opp_men)
        bk = _bits(opp_kings)

    root_moves = _gen_moves(bm, bk, wm, wk, side)
    if not root_moves:
        own = my_men or my_kings
        if own:
            r, c = int(own[0][0]), int(own[0][1])
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    start = time.perf_counter()
    deadline = start + 0.92
    tt = {}
    history = {}
    counter = [0]

    root_moves = _ordered_moves(root_moves, None, history, bm, bk, wm, wk, side)
    best_move = root_moves[0]
    if len(root_moves) == 1:
        return _coord_move(best_move)

    try:
        for depth in range(1, 13):
            if time.perf_counter() >= deadline:
                raise _Timeout
            ordered = _ordered_moves(root_moves, best_move, history, bm, bk, wm, wk, side)
            cur_best = None
            cur_score = -_INF
            alpha, beta = -_INF, _INF
            for m in ordered:
                if time.perf_counter() >= deadline:
                    raise _Timeout
                nbm, nbk, nwm, nwk, nside = _do_move(bm, bk, wm, wk, side, m)
                val = -_negamax(
                    nbm,
                    nbk,
                    nwm,
                    nwk,
                    nside,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                    deadline,
                    tt,
                    history,
                    counter,
                )
                if val > cur_score:
                    cur_score = val
                    cur_best = m
                if val > alpha:
                    alpha = val
            best_move = cur_best if cur_best is not None else best_move
            if cur_score >= _MATE - 1000:
                break
            if time.perf_counter() >= deadline - 0.02:
                break
    except _Timeout:
        pass

    return _coord_move(best_move)
