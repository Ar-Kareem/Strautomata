
import time

_DIRS_ALL = [(-1,-1),(-1,1),(1,-1),(1,1)]
_FWD_B = [(-1,-1),(-1,1)]
_FWD_W = [(1,-1),(1,1)]

_LAST_POST = None
_LAST_DEST = None

_MATE = 100000
_MAN_V = 100
_KING_V = 140

_deadline = 0.0
_nodes = 0

# global board sets for search
_bM = set()
_bK = set()
_wM = set()
_wK = set()

class _Timeout(Exception):
    pass

def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0:
        if time.time() > _deadline:
            raise _Timeout()

def _gen_moves(turn):
    # returns (moves, is_capture)
    # move = (fr:int, to:int, cap:int(-1 none), promo:bool, is_king:bool)
    global _bM,_bK,_wM,_wK
    if turn == 'b':
        myM = _bM; myK = _bK; oppM = _wM; oppK = _wK
        promo_row = 0
        fwd = _FWD_B
    else:
        myM = _wM; myK = _wK; oppM = _bM; oppK = _bK
        promo_row = 7
        fwd = _FWD_W
    occupied = _bM | _bK | _wM | _wK
    opp_occ = oppM | oppK
    king_caps = []
    fwd_caps = []
    bwd_caps = []
    # men captures
    # forward captures
    for pos in myM:
        r = pos // 8; c = pos % 8
        for dr, dc in _DIRS_ALL:
            mr = r+dr; mc = c+dc; lr = r+2*dr; lc = c+2*dc
            if lr < 0 or lr > 7 or lc < 0 or lc > 7:
                continue
            if mr < 0 or mr > 7 or mc < 0 or mc > 7:
                continue
            mid = mr*8+mc; land = lr*8+lc
            if mid not in opp_occ:
                continue
            if land in occupied:
                continue
            promo = (lr == promo_row)
            mv = (pos, land, mid, promo, False)
            # forward if dr matches fwd direction
            is_fwd = False
            for fdr, fdc in fwd:
                if dr == fdr and dc == fdc:
                    is_fwd = True
                    break
            if is_fwd:
                fwd_caps.append(mv)
            else:
                bwd_caps.append(mv)
    for pos in myK:
        r = pos // 8; c = pos % 8
        for dr, dc in _DIRS_ALL:
            mr = r+dr; mc = c+dc; lr = r+2*dr; lc = c+2*dc
            if lr < 0 or lr > 7 or lc < 0 or lc > 7:
                continue
            mid = mr*8+mc; land = lr*8+lc
            if mid not in opp_occ:
                continue
            if land in occupied:
                continue
            mv = (pos, land, mid, False, True)
            king_caps.append(mv)
    # compatibility: if any forward/king capture exists, ignore backward men captures
    # (any capture satisfies mandatory under both rule sets)
    if king_caps or fwd_caps:
        caps = king_caps + fwd_caps
        return caps, True
    if bwd_caps:
        return bwd_caps, True
    # no captures -> simple moves
    simples = []
    for pos in myM:
        r = pos // 8; c = pos % 8
        for dr, dc in fwd:
            nr = r+dr; nc = c+dc
            if nr < 0 or nr > 7 or nc < 0 or nc > 7:
                continue
            land = nr*8+nc
            if land in occupied:
                continue
            promo = (nr == promo_row)
            simples.append((pos, land, -1, promo, False))
    for pos in myK:
        r = pos // 8; c = pos % 8
        for dr, dc in _DIRS_ALL:
            nr = r+dr; nc = c+dc
            if nr < 0 or nr > 7 or nc < 0 or nc > 7:
                continue
            land = nr*8+nc
            if land in occupied:
                continue
            simples.append((pos, land, -1, False, True))
    return simples, False

def _do_move(turn, mv):
    global _bM,_bK,_wM,_wK
    fr, to, cap, promo, is_king = mv
    if turn == 'b':
        if is_king:
            _bM.discard(fr)
            _bK.discard(fr)
            _bK.add(to)
        else:
            _bM.discard(fr)
            _bK.discard(fr)
            if promo:
                _bK.add(to)
            else:
                _bM.add(to)
        if cap != -1:
            _wM.discard(cap)
            _wK.discard(cap)
    else:
        if is_king:
            _wM.discard(fr)
            _wK.discard(fr)
            _wK.add(to)
        else:
            _wM.discard(fr)
            _wK.discard(fr)
            if promo:
                _wK.add(to)
            else:
                _wM.add(to)
        if cap != -1:
            _bM.discard(cap)
            _bK.discard(cap)

def _undo_move(turn, mv):
    global _bM,_bK,_wM,_wK
    fr, to, cap, promo, is_king = mv
    if turn == 'b':
        if is_king:
            _bK.discard(to)
            _bK.add(fr)
        else:
            if promo:
                _bK.discard(to)
            else:
                _bM.discard(to)
            _bM.add(fr)
        if cap != -1:
            cr = cap // 8
            # restore as man or king? need to know victim type.
            # We stored only cap pos; recover type from saved info.
            # To avoid extra storage, caller must restore; we handle via extra stack.
            pass
    else:
        if is_king:
            _wK.discard(to)
            _wK.add(fr)
        else:
            if promo:
                _wK.discard(to)
            else:
                _wM.discard(to)
            _wM.add(fr)
        if cap != -1:
            pass

# We need victim type for undo. Store in move extended tuple during search.
# Instead use do/undo with explicit victim type.
def _do_move2(turn, mv):
    # mv = (fr,to,cap,promo,is_king, victim_is_king, victim_is_man)
    global _bM,_bK,_wM,_wK
    fr, to, cap, promo, is_king, vic_k, vic_m = mv
    if turn == 'b':
        if is_king:
            _bK.remove(fr)
            _bK.add(to)
        else:
            _bM.remove(fr)
            if promo:
                _bK.add(to)
            else:
                _bM.add(to)
        if cap != -1:
            if vic_k:
                _wK.remove(cap)
            else:
                _wM.remove(cap)
    else:
        if is_king:
            _wK.remove(fr)
            _wK.add(to)
        else:
            _wM.remove(fr)
            if promo:
                _wK.add(to)
            else:
                _wM.add(to)
        if cap != -1:
            if vic_k:
                _bK.remove(cap)
            else:
                _bM.remove(cap)

def _undo_move2(turn, mv):
    global _bM,_bK,_wM,_wK
    fr, to, cap, promo, is_king, vic_k, vic_m = mv
    if turn == 'b':
        if is_king:
            _bK.remove(to)
            _bK.add(fr)
        else:
            if promo:
                _bK.remove(to)
            else:
                _bM.remove(to)
            _bM.add(fr)
        if cap != -1:
            if vic_k:
                _wK.add(cap)
            else:
                _wM.add(cap)
    else:
        if is_king:
            _wK.remove(to)
            _wK.add(fr)
        else:
            if promo:
                _wK.remove(to)
            else:
                _wM.remove(to)
            _wM.add(fr)
        if cap != -1:
            if vic_k:
                _bK.add(cap)
            else:
                _bM.add(cap)

def _evaluate(turn):
    global _bM,_bK,_wM,_wK
    # score for turn to move
    if turn == 'b':
        myM = _bM; myK = _bK; opM = _wM; opK = _wK
        col = 'b'
    else:
        myM = _wM; myK = _wK; opM = _bM; opK = _bK
        col = 'w'
    s = 0
    # my pieces
    for pos in myM:
        r = pos // 8; c = pos % 8
        adv = (7 - r) if col == 'b' else r
        s += _MAN_V + adv * 5
        if 2 <= r <= 5 and 2 <= c <= 5:
            s += 6
        elif 1 <= r <= 6 and 1 <= c <= 6:
            s += 2
        if c == 0 or c == 7:
            s += 3
        if col == 'b':
            if r >= 6:
                s += 4
            if r == 7:
                s += 3
        else:
            if r <= 1:
                s += 4
            if r == 0:
                s += 3
    for pos in myK:
        r = pos // 8; c = pos % 8
        s += _KING_V
        if 2 <= r <= 5 and 2 <= c <= 5:
            s += 6
        elif 1 <= r <= 6 and 1 <= c <= 6:
            s += 2
        else:
            s -= 2
        if c == 0 or c == 7:
            s -= 2
    # opp pieces
    ocol = 'w' if col == 'b' else 'b'
    for pos in opM:
        r = pos // 8; c = pos % 8
        adv = (7 - r) if ocol == 'b' else r
        s -= _MAN_V + adv * 5
        if 2 <= r <= 5 and 2 <= c <= 5:
            s -= 6
        elif 1 <= r <= 6 and 1 <= c <= 6:
            s -= 2
        if c == 0 or c == 7:
            s -= 3
        if ocol == 'b':
            if r >= 6:
                s -= 4
            if r == 7:
                s -= 3
        else:
            if r <= 1:
                s -= 4
            if r == 0:
                s -= 3
    for pos in opK:
        r = pos // 8; c = pos % 8
        s -= _KING_V
        if 2 <= r <= 5 and 2 <= c <= 5:
            s -= 6
        elif 1 <= r <= 6 and 1 <= c <= 6:
            s -= 2
        else:
            s += 2
        if c == 0 or c == 7:
            s += 2
    # piece count trade bonus: when ahead, encourage trade
    my_n = len(myM) + len(myK)
    op_n = len(opM) + len(opK)
    if my_n + op_n < 8:
        # endgame: centralise kings already done
        pass
    return s

def _order_moves(moves, turn):
    global _bM,_bK,_wM,_wK
    # decorate with victim info and score
    if turn == 'b':
        oppK = _wK
    else:
        oppK = _bK
    dec = []
    for (fr, to, cap, promo, is_king) in moves:
        vic_k = False
        vic_m = False
        sc = 0
        if cap != -1:
            if cap in oppK:
                vic_k = True
                sc += 200
            else:
                vic_m = True
                sc += 100
            sc += 500  # captures first
        if promo:
            sc += 300
        # advancement
        fr_r = fr // 8; to_r = to // 8
        if not is_king:
            if turn == 'w':
                sc += (to_r - fr_r) * 10
            else:
                sc += (fr_r - to_r) * 10
        # centre
        tr = to // 8; tc = to % 8
        if 2 <= tr <= 5 and 2 <= tc <= 5:
            sc += 20
        dec.append((sc, (fr, to, cap, promo, is_king, vic_k, vic_m)))
    dec.sort(key=lambda x: -x[0])
    return [m for _, m in dec]

def _negamax(turn, depth, alpha, beta, qdepth):
    _check_time()
    moves_raw, is_cap = _gen_moves(turn)
    if not moves_raw:
        return -_MATE - depth  # loss, prefer delay (larger depth remaining = faster loss? adjust)
    if depth <= 0:
        if is_cap and qdepth > 0:
            # quiescence: search captures only
            ordered = _order_moves(moves_raw, turn)
            best = _evaluate(turn)
            # stand pat with alpha improvement
            if best >= beta:
                return best
            if best > alpha:
                alpha = best
            for mv in ordered:
                _do_move2(turn, mv)
                nxt = 'w' if turn == 'b' else 'b'
                sc = -_negamax(nxt, 0, -beta, -alpha, qdepth-1)
                _undo_move2(turn, mv)
                if sc >= beta:
                    return sc
                if sc > alpha:
                    alpha = sc
            return alpha
        else:
            return _evaluate(turn)
    ordered = _order_moves(moves_raw, turn)
    best = -10**9
    nxt = 'w' if turn == 'b' else 'b'
    for mv in ordered:
        _do_move2(turn, mv)
        sc = -_negamax(nxt, depth-1, -beta, -alpha, qdepth)
        _undo_move2(turn, mv)
        if sc > best:
            best = sc
        if best >= beta:
            return best
        if best > alpha:
            alpha = best
    return best

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _bM,_bK,_wM,_wK,_deadline,_nodes,_LAST_POST,_LAST_DEST
    try:
        # convert to sets of ints
        def to_set(lst):
            s = set()
            for sq in lst:
                try:
                    r, c = int(sq[0]), int(sq[1])
                except Exception:
                    continue
                if 0 <= r <= 7 and 0 <= c <= 7:
                    s.add(r*8+c)
            return s
        myM0 = to_set(my_men)
        myK0 = to_set(my_kings)
        opM0 = to_set(opp_men)
        opK0 = to_set(opp_kings)
        # install global board
        if color == 'b':
            _bM = set(myM0); _bK = set(myK0); _wM = set(opM0); _wK = set(opK0)
        else:
            _wM = set(myM0); _wK = set(myK0); _bM = set(opM0); _bK = set(opK0)
        moves_raw, is_cap = _gen_moves(color)
        if not moves_raw:
            # no moves: return dummy (game over) - must return something
            # try any own piece
            allown = list(myM0 | myK0)
            if allown:
                fr = allown[0]; r = fr//8; c = fr%8
                # find empty neighbour
                for dr, dc in _DIRS_ALL:
                    nr = r+dr; nc = c+dc
                    if 0 <= nr <= 7 and 0 <= nc <= 7:
                        if (nr*8+nc) not in (_bM|_bK|_wM|_wK):
                            return ((r,c),(nr,nc))
                return ((r,c),(r,c))
            return ((0,1),(1,2))
        # continuation detection: if board equals last post-board, restrict to same piece
        if _LAST_POST is not None and _LAST_DEST is not None:
            try:
                lp_myM, lp_myK, lp_opM, lp_opK, lp_col = _LAST_POST
                if lp_col == color and lp_myM == myM0 and lp_myK == myK0 and lp_opM == opM0 and lp_opK == opK0:
                    filt = [m for m in moves_raw if m[0] == _LAST_DEST]
                    if filt:
                        moves_raw = filt
                        is_cap = True
            except Exception:
                pass
        if len(moves_raw) == 1:
            fr, to, cap, promo, is_king = moves_raw[0]
            # update last post
            try:
                _do_move(color, (fr,to,cap,promo,is_king)) if False else None
            except Exception:
                pass
            # compute post board for continuation tracking
            # simulate quickly
            nmM = set(myM0); nmK = set(myK0); noM = set(opM0); noK = set(opK0)
            if is_king:
                nmK.discard(fr); nmK.add(to)
            else:
                nmM.discard(fr)
                if promo:
                    nmK.add(to)
                else:
                    nmM.add(to)
            if cap != -1:
                noM.discard(cap); noK.discard(cap)
            _LAST_POST = (nmM, nmK, noM, noK, color)
            _LAST_DEST = to
            return ((fr//8, fr%8),(to//8, to%8))
        # iterative deepening search
        _deadline = time.time() + 0.88
        _nodes = 0
        ordered = _order_moves(moves_raw, color)
        best_mv = ordered[0]
        # quick evaluation for immediate win / avoid loss: will be refined
        # iterative deepening
        max_depth = 12
        # adapt depth by piece count
        total = len(myM0)+len(myK0)+len(opM0)+len(opK0)
        if total > 16:
            max_depth = 7
        elif total > 10:
            max_depth = 9
        else:
            max_depth = 12
        nxt = 'w' if color == 'b' else 'b'
        try:
            for depth in range(1, max_depth+1):
                alpha = -10**9; beta = 10**9
                cur_best = None
                cur_best_sc = -10**9
                # use previous best first
                # reorder: put best_mv first
                if best_mv in ordered:
                    ordered.remove(best_mv)
                    ordered = [best_mv] + ordered
                for mv in ordered:
                    _do_move2(color, mv)
                    sc = -_negamax(nxt, depth-1, -beta, -alpha, 4)
                    _undo_move2(color, mv)
                    if sc > cur_best_sc:
                        cur_best_sc = sc
                        cur_best = mv
                    if sc > alpha:
                        alpha = sc
                best_mv = cur_best
                # reorder by score for next iteration? re-generate ordering with scores
                # simple: keep order but move best first (done next loop)
                if time.time() > _deadline - 0.05:
                    break
                # early stop if mate found
                if cur_best_sc > _MATE - 100:
                    break
        except _Timeout:
            pass
        fr, to, cap, promo, is_king, vic_k, vic_m = best_mv
        # update continuation memory
        nmM = set(myM0); nmK = set(myK0); noM = set(opM0); noK = set(opK0)
        if is_king:
            nmK.discard(fr); nmK.add(to)
        else:
            nmM.discard(fr)
            if promo:
                nmK.add(to)
            else:
                nmM.add(to)
        if cap != -1:
            noM.discard(cap); noK.discard(cap)
        _LAST_POST = (nmM, nmK, noM, noK, color)
        _LAST_DEST = to
        return ((fr//8, fr%8),(to//8, to%8))
    except Exception:
        # guaranteed legal fallback
        try:
            # rebuild simple legal list ignoring search state
            occ = set()
            for sq in list(my_men)+list(my_kings)+list(opp_men)+list(opp_kings):
                try:
                    occ.add(int(sq[0])*8+int(sq[1]))
                except Exception:
                    pass
            opp_set = set()
            for sq in list(opp_men)+list(opp_kings):
                try:
                    opp_set.add(int(sq[0])*8+int(sq[1]))
                except Exception:
                    pass
            fwd = _FWD_B if color == 'b' else _FWD_W
            promo_row = 0 if color == 'b' else 7
            # forward captures first
            for lst, isK in [(my_kings, True),(my_men, False)]:
                for sq in lst:
                    try:
                        r, c = int(sq[0]), int(sq[1])
                    except Exception:
                        continue
                    dirs = _DIRS_ALL if isK else fwd
                    for dr, dc in dirs:
                        mr=r+dr; mc=c+dc; lr=r+2*dr; lc=c+2*dc
                        if 0<=lr<=7 and 0<=lc<=7 and 0<=mr<=7 and 0<=mc<=7:
                            if (mr*8+mc) in opp_set and (lr*8+lc) not in occ:
                                return ((r,c),(lr,lc))
            # backward men captures
            if color == 'b':
                bwd = [(1,-1),(1,1)]
            else:
                bwd = [(-1,-1),(-1,1)]
            for sq in my_men:
                try:
                    r,c = int(sq[0]), int(sq[1])
                except Exception:
                    continue
                for dr,dc in bwd:
                    mr=r+dr; mc=c+dc; lr=r+2*dr; lc=c+2*dc
                    if 0<=lr<=7 and 0<=lc<=7 and 0<=mr<=7 and 0<=mc<=7:
                        if (mr*8+mc) in opp_set and (lr*8+lc) not in occ:
                            return ((r,c),(lr,lc))
            # simples
            for lst, isK in [(my_men, False),(my_kings, True)]:
                for sq in lst:
                    try:
                        r,c = int(sq[0]), int(sq[1])
                    except Exception:
                        continue
                    dirs = _DIRS_ALL if isK else fwd
                    for dr,dc in dirs:
                        nr=r+dr; nc=c+dc
                        if 0<=nr<=7 and 0<=nc<=7:
                            if (nr*8+nc) not in occ:
                                return ((r,c),(nr,nc))
        except Exception:
            pass
        return ((2,1),(3,0))
