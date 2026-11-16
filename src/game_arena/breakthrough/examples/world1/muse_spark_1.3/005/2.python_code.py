
import time

INF = 1000000
ADV_W = [0, 15, 35, 60, 90, 130, 500, 0]
CENT = [-8, -2, 4, 8, 8, 4, -2, -8]

_deadline = 0.0
_nodes = 0

class _Timeout(Exception):
    pass

def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0:
        if time.perf_counter() > _deadline:
            raise _Timeout()

def _gen_moves(white, black, white_set, black_set, turn):
    if turn == 'w':
        my_list = white
        my_set = white_set
        opp_set = opp_set_ = black_set
        occ = white_set | black_set
        # to avoid building occ each time, use combined check
        moves = []
        for f in my_list:
            r = f >> 3
            c = f & 7
            if r >= 7:
                continue
            nr = r + 1
            base = nr << 3
            # straight
            t = base + c
            if t not in white_set and t not in black_set:
                moves.append((f, t, False))
            # diag left c-1
            if c > 0:
                t2 = base + c - 1
                if t2 not in my_set:
                    if t2 in opp_set_:
                        moves.append((f, t2, True))
                    elif t2 not in occ:
                        moves.append((f, t2, False))
            if c < 7:
                t3 = base + c + 1
                if t3 not in my_set:
                    if t3 in opp_set_:
                        moves.append((f, t3, True))
                    elif t3 not in occ:
                        moves.append((f, t3, False))
        return moves
    else:
        my_list = black
        my_set = black_set
        opp_set_ = white_set
        occ = white_set | black_set
        moves = []
        for f in my_list:
            r = f >> 3
            c = f & 7
            if r <= 0:
                continue
            nr = r - 1
            base = nr << 3
            t = base + c
            if t not in white_set and t not in black_set:
                moves.append((f, t, False))
            if c > 0:
                t2 = base + c - 1
                if t2 not in my_set:
                    if t2 in opp_set_:
                        moves.append((f, t2, True))
                    elif t2 not in occ:
                        moves.append((f, t2, False))
            if c < 7:
                t3 = base + c + 1
                if t3 not in my_set:
                    if t3 in opp_set_:
                        moves.append((f, t3, True))
                    elif t3 not in occ:
                        moves.append((f, t3, False))
        return moves

def _evaluate(white, black, white_set, black_set):
    # white perspective
    lw = len(white)
    lb = len(black)
    if lw == 0 and lb == 0:
        return 0
    if lw == 0:
        return -90000
    if lb == 0:
        return 90000
    score = (lw - lb) * 100
    # advancement + centre
    for sq in white:
        r = sq >> 3
        c = sq & 7
        if r == 7:
            return 90000
        score += ADV_W[r] + CENT[c]
    for sq in black:
        r = sq >> 3
        c = sq & 7
        if r == 0:
            return -90000
        score -= (ADV_W[7 - r] + CENT[c])
    # hanging / defended
    # white pieces attacked by black from above
    for sq in white:
        r = sq >> 3
        c = sq & 7
        if r < 7:
            attacked = False
            if c > 0 and (sq + 7) in black_set:
                attacked = True
            elif c < 7 and (sq + 9) in black_set:
                attacked = True
            if attacked:
                defended = False
                if r > 0:
                    if c > 0 and (sq - 9) in white_set:
                        defended = True
                    elif c < 7 and (sq - 7) in white_set:
                        defended = True
                if defended:
                    score -= 6
                else:
                    # more penalty for advanced hanging pawns
                    score -= (30 + (r * 3))
            else:
                # small bonus for defended even if not attacked
                if r > 0:
                    if (c > 0 and (sq - 9) in white_set) or (c < 7 and (sq - 7) in white_set):
                        score += 4
    for sq in black:
        r = sq >> 3
        c = sq & 7
        attacked = False
        if r > 0:
            if c > 0 and (sq - 9) in white_set:
                attacked = True
            elif c < 7 and (sq - 7) in white_set:
                attacked = True
        if attacked:
            defended = False
            if r < 7:
                if c > 0 and (sq + 7) in black_set:
                    defended = True
                elif c < 7 and (sq + 9) in black_set:
                    defended = True
            ar = 7 - r
            if defended:
                score += 6
            else:
                score += (30 + ar * 3)
        else:
            if r < 7:
                if (c > 0 and (sq + 7) in black_set) or (c < 7 and (sq + 9) in black_set):
                    score -= 4
    return score

def _order_moves(moves, turn):
    # score: capture huge, promotion huge, advancement, centre
    scored = []
    for f, t, cap in moves:
        tr = t >> 3
        tc = t & 7
        s = 0
        if cap:
            # victim value approx, plus advancement
            s += 1000
            # capturing advanced pawn better: use destination rank
            if turn == 'w':
                s += ADV_W[tr] * 0.5 if tr < 7 else 2000
            else:
                s += ADV_W[7 - tr] * 0.5 if tr > 0 else 2000
        # promotion (non-capture diagonal/straight to last rank is win)
        if turn == 'w' and tr == 7:
            s += 10000
        if turn == 'b' and tr == 0:
            s += 10000
        # advancement
        if turn == 'w':
            s += tr * 10
        else:
            s += (7 - tr) * 10
        # centre
        s += CENT[tc]
        # forward vs diagonal: slight prefer forward? keep neutral
        scored.append((s, f, t, cap))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(f, t, cap) for _, f, t, cap in scored]

def _negamax(white, black, white_set, black_set, turn, depth, alpha, beta, qdepth=0):
    _check_time()
    # terminal by promotion already handled by caller, but check safety
    # if side to move has no pieces -> loss
    if turn == 'w' and len(white) == 0:
        return -INF
    if turn == 'b' and len(black) == 0:
        return -INF

    if depth <= 0:
        # quiescence: if winning move exists, win
        # generate only tactical moves
        moves = _gen_moves(white, black, white_set, black_set, turn)
        if not moves:
            return -INF + 1
        # immediate win?
        if turn == 'w':
            for _, t, _ in moves:
                if (t >> 3) == 7:
                    return INF - 1 - qdepth
        else:
            for _, t, _ in moves:
                if (t >> 3) == 0:
                    return INF - 1 - qdepth
        if qdepth <= 0:
            v = _evaluate(white, black, white_set, black_set)
            return v if turn == 'w' else -v
        # quiescence search captures only
        caps = [m for m in moves if m[2]]
        if not caps:
            v = _evaluate(white, black, white_set, black_set)
            return v if turn == 'w' else -v
        caps = _order_moves(caps, turn)
        best = -INF
        # stand pat
        stand = _evaluate(white, black, white_set, black_set)
        stand = stand if turn == 'w' else -stand
        if stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        best = stand
        nxt = 'b' if turn == 'w' else 'w'
        for f, t, cap in caps:
            # make
            if turn == 'w':
                nw = white.copy()
                nb = black.copy()
                nws = white_set.copy()
                nbs = black_set.copy()
                # remove f
                try:
                    nw.remove(f)
                except ValueError:
                    continue
                nws.remove(f)
                # capture
                if t in nbs:
                    try:
                        nb.remove(t)
                    except ValueError:
                        pass
                    nbs.remove(t)
                nw.append(t)
                nws.add(t)
                # win already checked (promotion)
                val = -_negamax(nw, nb, nws, nbs, nxt, 0, -beta, -alpha, qdepth - 1)
            else:
                nw = white.copy()
                nb = black.copy()
                nws = white_set.copy()
                nbs = black_set.copy()
                try:
                    nb.remove(f)
                except ValueError:
                    continue
                nbs.remove(f)
                if t in nws:
                    try:
                        nw.remove(t)
                    except ValueError:
                        pass
                    nws.remove(t)
                nb.append(t)
                nbs.add(t)
                val = -_negamax(nw, nb, nws, nbs, nxt, 0, -beta, -alpha, qdepth - 1)
            if val > best:
                best = val
            if best >= beta:
                return best
            if best > alpha:
                alpha = best
        return best

    moves = _gen_moves(white, black, white_set, black_set, turn)
    if not moves:
        return -INF + (6 - depth)
    # immediate win shortcut
    if turn == 'w':
        for _, t, _ in moves:
            if (t >> 3) == 7:
                return INF + depth
    else:
        for _, t, _ in moves:
            if (t >> 3) == 0:
                return INF + depth

    moves = _order_moves(moves, turn)
    nxt = 'b' if turn == 'w' else 'w'
    best = -INF
    for f, t, cap in moves:
        if turn == 'w':
            nw = white.copy()
            nb = black.copy()
            nws = white_set.copy()
            nbs = black_set.copy()
            try:
                nw.remove(f)
            except ValueError:
                continue
            nws.remove(f)
            if t in nbs:
                try:
                    nb.remove(t)
                except ValueError:
                    pass
                nbs.remove(t)
                if len(nb) == 0:
                    return INF + depth
            nw.append(t)
            nws.add(t)
            # promotion win
            if (t >> 3) == 7:
                return INF + depth
            val = -_negamax(nw, nb, nws, nbs, nxt, depth - 1, -beta, -alpha, 2)
        else:
            nw = white.copy()
            nb = black.copy()
            nws = white_set.copy()
            nbs = black_set.copy()
            try:
                nb.remove(f)
            except ValueError:
                continue
            nbs.remove(f)
            if t in nws:
                try:
                    nw.remove(t)
                except ValueError:
                    pass
                nws.remove(t)
                if len(nw) == 0:
                    return INF + depth
            nb.append(t)
            nbs.add(t)
            if (t >> 3) == 0:
                return INF + depth
            val = -_negamax(nw, nb, nws, nbs, nxt, depth - 1, -beta, -alpha, 2)
        if val > best:
            best = val
        if best >= beta:
            return best
        if best > alpha:
            alpha = best
    return best

def policy(me, opp, color):
    global _deadline, _nodes
    start = time.perf_counter()
    _deadline = start + 0.88
    _nodes = 0
    try:
        my_sq = [r * 8 + c for (r, c) in me]
        op_sq = [r * 8 + c for (r, c) in opp]
        if color == 'w':
            white = my_sq
            black = op_sq
            turn = 'w'
        else:
            white = op_sq
            black = my_sq
            turn = 'b'
        white_set = set(white)
        black_set = set(black)

        moves = _gen_moves(white, black, white_set, black_set, turn)
        if not moves:
            # no legal moves: return dummy (should not happen)
            return ((0, 0), (0, 0))
        # instant win
        win_move = None
        for f, t, cap in moves:
            tr = t >> 3
            if turn == 'w' and tr == 7:
                win_move = (f, t)
                break
            if turn == 'b' and tr == 0:
                win_move = (f, t)
                break
        if win_move is not None:
            f, t = win_move
            return ((f >> 3, f & 7), (t >> 3, t & 7))

        if len(moves) == 1:
            f, t, _ = moves[0]
            return ((f >> 3, f & 7), (t >> 3, t & 7))

        ordered = _order_moves(moves, turn)
        # default best: first ordered (captures first)
        bf, bt, _ = ordered[0]
        best_move = (bf, bt)

        # iterative deepening
        # choose max depth by piece count
        total = len(white) + len(black)
        if total > 24:
            max_depth = 4
        elif total > 16:
            max_depth = 5
        elif total > 10:
            max_depth = 6
        else:
            max_depth = 8

        nxt = 'b' if turn == 'w' else 'w'
        try:
            for depth in range(1, max_depth + 1):
                # time check
                if time.perf_counter() > _deadline - 0.05:
                    break
                alpha = -INF
                beta = INF
                local_best = best_move
                local_best_val = -INF
                # search root moves in ordered order; reorder by previous iteration?
                for f, t, cap in ordered:
                    if turn == 'w':
                        nw = white.copy()
                        nb = black.copy()
                        nws = white_set.copy()
                        nbs = black_set.copy()
                        nw.remove(f)
                        nws.remove(f)
                        if t in nbs:
                            nb.remove(t)
                            nbs.remove(t)
                        nw.append(t)
                        nws.add(t)
                    else:
                        nw = white.copy()
                        nb = black.copy()
                        nws = white_set.copy()
                        nbs = black_set.copy()
                        nb.remove(f)
                        nbs.remove(f)
                        if t in nws:
                            nw.remove(t)
                            nws.remove(t)
                        nb.append(t)
                        nbs.add(t)
                    val = -_negamax(nw, nb, nws, nbs, nxt, depth - 1, -beta, -alpha, 2)
                    if val > local_best_val:
                        local_best_val = val
                        local_best = (f, t)
                    if val > alpha:
                        alpha = val
                    # early exit on forced win
                    if local_best_val >= INF - 1000:
                        break
                best_move = local_best
                # reorder for next iteration: put best first
                ordered = [(best_move[0], best_move[1], False)] + [m for m in ordered if not (m[0] == best_move[0] and m[1] == best_move[1])]
                # if found forced win, stop
                if local_best_val >= INF - 1000:
                    break
                # if time low, stop
                if time.perf_counter() > _deadline - 0.08:
                    break
        except _Timeout:
            pass

        f, t = best_move
        return ((f >> 3, f & 7), (t >> 3, t & 7))
    except Exception:
        # fallback: return first legal move by brute force
        try:
            d = 1 if color == 'w' else -1
            me_set = set(me)
            opp_set = set(opp)
            occ = me_set | opp_set
            for (r, c) in me:
                nr = r + d
                if 0 <= nr < 8:
                    if (nr, c) not in occ:
                        return ((r, c), (nr, c))
                    for dc in (-1, 1):
                        nc = c + dc
                        if 0 <= nc < 8:
                            dest = (nr, nc)
                            if dest not in me_set and (dest in opp_set or dest not in occ):
                                return ((r, c), dest)
            # last resort scan
            for (r, c) in me:
                nr = r + d
                if 0 <= nr < 8:
                    for dc in (-1, 0, 1):
                        nc = c + dc
                        if 0 <= nc < 8:
                            dest = (nr, nc)
                            # validate roughly
                            if dc == 0:
                                if dest not in occ:
                                    return ((r, c), dest)
                            else:
                                if dest not in me_set:
                                    return ((r, c), dest)
        except Exception:
            pass
        # ultimate dummy
        try:
            if len(me) > 0:
                return (me[0], me[0])
        except Exception:
            pass
        return ((0, 0), ((1, 0) if color == 'w' else (-1, 0)))
