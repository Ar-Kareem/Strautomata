
import time

INF = 10 ** 9
LOSS = -10 ** 6


class _Timeout(Exception):
    pass


_DEADLINE = [0.0]
_nodes = [0]
_memory = {'st': None, 'color': None, 'move': None, 'cont': None}


def _in_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _jumps_from(st, color, sq):
    """All jumps available for the piece at sq (works for men and kings)."""
    wm, wk, bm, bk = st
    om, ok = (bm, bk) if color == 'w' else (wm, wk)
    opp = om | ok
    occ = wm | wk | bm | bk
    r, c = sq
    res = []
    for dr in (-1, 1):
        for dc in (-1, 1):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if _in_board(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                res.append((sq, (tr, tc), (mr, mc)))
    return res


def _gen(st, color):
    """Returns (jumps, quiets). st = (wm, wk, bm, bk) absolute."""
    wm, wk, bm, bk = st
    if color == 'w':
        mym, myk, om, ok = wm, wk, bm, bk
        d = 1
    else:
        mym, myk, om, ok = bm, bk, wm, wk
        d = -1
    opp = om | ok
    occ = mym | myk | opp
    quiets = []
    jumps = []
    # men
    for r, c in mym:
        for dc in (-1, 1):
            tr, tc = r + d, c + dc
            if _in_board(tr, tc) and (tr, tc) not in occ:
                quiets.append(((r, c), (tr, tc), None))
        for dr in (d, -d):
            for dc in (-1, 1):
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if _in_board(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                    jumps.append(((r, c), (tr, tc), (mr, mc)))
    # kings
    for r, c in myk:
        for dr in (-1, 1):
            for dc in (-1, 1):
                tr, tc = r + dr, c + dc
                if _in_board(tr, tc):
                    if (tr, tc) not in occ:
                        quiets.append(((r, c), (tr, tc), None))
                    jr, jc = r + 2 * dr, c + 2 * dc
                    if (tr, tc) in opp and _in_board(jr, jc) and (jr, jc) not in occ:
                        jumps.append(((r, c), (jr, jc), (tr, tc)))
    return jumps, quiets


def _apply(st, color, move):
    """Apply move. Returns (new_state, forced_continuation_square_or_None)."""
    frm, to, cap = move
    wm = set(st[0]); wk = set(st[1]); bm = set(st[2]); bk = set(st[3])
    if color == 'w':
        mym, myk, om, ok = wm, wk, bm, bk
        last = 7
    else:
        mym, myk, om, ok = bm, bk, wm, wk
        last = 0
    if frm in mym:
        mym.remove(frm)
        is_man = True
    else:
        myk.remove(frm)
        is_man = False
    if cap is not None:
        if cap in om:
            om.remove(cap)
        elif cap in ok:
            ok.remove(cap)
    promoted = is_man and to[0] == last
    if promoted:
        myk.add(to)
    elif is_man:
        mym.add(to)
    else:
        myk.add(to)
    nst = (wm, wk, bm, bk)
    cont = None
    # a jump chain continues with the same piece unless it was just promoted
    if cap is not None and not promoted:
        if _jumps_from(nst, color, to):
            cont = to
    return nst, cont


def _evaluate(st):
    """Evaluation from White's perspective."""
    wm, wk, bm, bk = st
    s = 0
    for r, c in wm:
        s += 100 + 5 * r
        if 2 <= c <= 5:
            s += 2
        if r == 0:
            s += 6  # back-row guard
    for r, c in wk:
        s += 175
        if 2 <= c <= 5 and 2 <= r <= 5:
            s += 4
    for r, c in bm:
        s -= 100 + 5 * (7 - r)
        if 2 <= c <= 5:
            s -= 2
        if r == 7:
            s -= 6
    for r, c in bk:
        s -= 175
        if 2 <= c <= 5 and 2 <= r <= 5:
            s -= 4
    return s


def _search(st, color, depth, alpha, beta, forced):
    _nodes[0] += 1
    if (_nodes[0] & 255) == 0 and time.time() > _DEADLINE[0]:
        raise _Timeout()
    jumps, quiets = _gen(st, color)
    if forced is not None:
        jumps = [m for m in jumps if m[0] == forced]
        quiets = []
    if not jumps and not quiets:
        return LOSS  # side to move has no moves -> loses
    if jumps:
        moves = jumps  # captures are mandatory; quiescence continues naturally
    elif depth <= 0:
        return _evaluate(st) * (1 if color == 'w' else -1)
    else:
        moves = quiets
    best = -INF
    opp_c = 'b' if color == 'w' else 'w'
    for m in moves:
        nst, cont = _apply(st, color, m)
        if cont is not None:
            # same player keeps moving (forced chain), don't burn depth
            v = _search(nst, color, depth, alpha, beta, cont)
        else:
            v = -_search(nst, opp_c, depth - 1, -beta, -alpha, None)
        if v > best:
            best = v
            if v > alpha:
                alpha = v
        if alpha >= beta:
            break
    return best


def _same(st1, st2):
    return all(set(a) == set(b) for a, b in zip(st1, st2))


def _remember(st, color, move):
    try:
        cont = _apply(st, color, move)[1]
        _memory['st'] = (set(st[0]), set(st[1]), set(st[2]), set(st[3]))
        _memory['color'] = color
        _memory['move'] = move
        _memory['cont'] = cont
    except Exception:
        _memory['cont'] = None


def policy(my_men, my_kings, opp_men, opp_kings, color):
    color = str(color).lower()
    my_m = {tuple(p) for p in my_men}
    my_k = {tuple(p) for p in my_kings}
    op_m = {tuple(p) for p in opp_men}
    op_k = {tuple(p) for p in opp_kings}
    if color == 'w':
        st = (my_m, my_k, op_m, op_k)
    else:
        st = (op_m, op_k, my_m, my_k)

    # Detect if we are mid-capture-chain (engine re-called us for continuation):
    # current state must exactly equal the state right after our last jump.
    forced_sq = None
    mem = _memory
    if mem['cont'] is not None and mem['color'] == color:
        try:
            exp_st, exp_cont = _apply(mem['st'], color, mem['move'])
            if exp_cont is not None and _same(exp_st, st):
                forced_sq = mem['move'][1]
        except Exception:
            forced_sq = None

    jumps, quiets = _gen(st, color)
    if forced_sq is not None:
        cand = [m for m in jumps if m[0] == forced_sq]
        legal = cand if cand else (jumps if jumps else quiets)
    else:
        legal = jumps if jumps else quiets  # captures mandatory

    if not legal:
        # no legal moves at all (we have lost); return placeholder
        return ((0, 1), (1, 2))

    if len(legal) == 1:
        _remember(st, color, legal[0])
        return (legal[0][0], legal[0][1])

    _DEADLINE[0] = time.time() + 0.80
    _nodes[0] = 0
    best_move = legal[0]
    opp_c = 'b' if color == 'w' else 'w'
    try:
        for depth in range(2, 15):
            if time.time() > _DEADLINE[0] - 0.05:
                break
            alpha = -INF
            cur_best = None
            ordered = [best_move] + [m for m in legal if m != best_move]
            for m in ordered:
                nst, cont = _apply(st, color, m)
                if cont is not None:
                    v = _search(nst, color, depth, alpha, INF, cont)
                else:
                    v = -_search(nst, opp_c, depth - 1, -INF, -alpha, None)
                if v > alpha:
                    alpha = v
                    cur_best = m
            if cur_best is not None:
                best_move = cur_best
    except _Timeout:
        pass
    except Exception:
        pass

    _remember(st, color, best_move)
    return (best_move[0], best_move[1])
