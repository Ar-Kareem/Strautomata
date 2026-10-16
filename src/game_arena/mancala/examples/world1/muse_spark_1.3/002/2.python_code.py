
import time

_INF = 10 ** 9
_TT = {}
_deadline = 0.0
_nodes = 0

class _Timeout(Exception):
    pass

def _apply_move(my_pits, my_store, opp_pits, opp_store, turn_mine, move):
    # returns n_my_pits, n_my_store, n_opp_pits, n_opp_store, n_turn_mine, over, extra
    if turn_mine:
        b0 = my_pits[0]; b1 = my_pits[1]; b2 = my_pits[2]; b3 = my_pits[3]; b4 = my_pits[4]; b5 = my_pits[5]
        o0 = opp_pits[0]; o1 = opp_pits[1]; o2 = opp_pits[2]; o3 = opp_pits[3]; o4 = opp_pits[4]; o5 = opp_pits[5]
        board = [b0,b1,b2,b3,b4,b5,my_store,o0,o1,o2,o3,o4,o5]
        seeds = board[move]
        board[move] = 0
        full = seeds // 13
        rem = seeds - full * 13
        if full:
            for k in range(13):
                board[k] += full
        if rem:
            pos = move + 1
            if pos >= 13:
                pos -= 13
            last = pos
            for _ in range(rem):
                if pos == 13:
                    pos = 0
                board[pos] += 1
                last = pos
                pos += 1
                if pos == 13 and _ != rem - 1:
                    pass
        else:
            last = move
        extra = (last == 6)
        if last >= 0 and last <= 5 and board[last] == 1:
            oi = 12 - last
            if board[oi] > 0:
                board[6] += board[oi] + 1
                board[last] = 0
                board[oi] = 0
        n_my_pits = board[0:6]
        n_my_store = board[6]
        n_opp_pits = board[7:13]
        n_opp_store = opp_store
    else:
        b0 = opp_pits[0]; b1 = opp_pits[1]; b2 = opp_pits[2]; b3 = opp_pits[3]; b4 = opp_pits[4]; b5 = opp_pits[5]
        o0 = my_pits[0]; o1 = my_pits[1]; o2 = my_pits[2]; o3 = my_pits[3]; o4 = my_pits[4]; o5 = my_pits[5]
        board = [b0,b1,b2,b3,b4,b5,opp_store,o0,o1,o2,o3,o4,o5]
        seeds = board[move]
        board[move] = 0
        full = seeds // 13
        rem = seeds - full * 13
        if full:
            for k in range(13):
                board[k] += full
        if rem:
            pos = move + 1
            if pos >= 13:
                pos -= 13
            last = pos
            for _ in range(rem):
                if pos == 13:
                    pos = 0
                board[pos] += 1
                last = pos
                pos += 1
        else:
            last = move
        extra = (last == 6)
        if last >= 0 and last <= 5 and board[last] == 1:
            oi = 12 - last
            if board[oi] > 0:
                board[6] += board[oi] + 1
                board[last] = 0
                board[oi] = 0
        n_opp_pits = board[0:6]
        n_opp_store = board[6]
        n_my_pits = board[7:13]
        n_my_store = my_store
    # game over ?
    over = False
    if n_my_pits[0]==0 and n_my_pits[1]==0 and n_my_pits[2]==0 and n_my_pits[3]==0 and n_my_pits[4]==0 and n_my_pits[5]==0:
        over = True
    elif n_opp_pits[0]==0 and n_opp_pits[1]==0 and n_opp_pits[2]==0 and n_opp_pits[3]==0 and n_opp_pits[4]==0 and n_opp_pits[5]==0:
        over = True
    if over:
        s1 = n_my_pits[0]+n_my_pits[1]+n_my_pits[2]+n_my_pits[3]+n_my_pits[4]+n_my_pits[5]
        s2 = n_opp_pits[0]+n_opp_pits[1]+n_opp_pits[2]+n_opp_pits[3]+n_opp_pits[4]+n_opp_pits[5]
        n_my_store += s1
        n_opp_store += s2
        n_my_pits = [0,0,0,0,0,0]
        n_opp_pits = [0,0,0,0,0,0]
        n_turn = turn_mine
    else:
        n_turn = turn_mine if extra else (not turn_mine)
    return n_my_pits, n_my_store, n_opp_pits, n_opp_store, n_turn, over, extra

def _evaluate(my_pits, my_store, opp_pits, opp_store, turn_mine):
    s_diff = my_store - opp_store
    my_sum = my_pits[0]+my_pits[1]+my_pits[2]+my_pits[3]+my_pits[4]+my_pits[5]
    opp_sum = opp_pits[0]+opp_pits[1]+opp_pits[2]+opp_pits[3]+opp_pits[4]+opp_pits[5]
    total = my_sum + opp_sum
    total_all = total + my_store + opp_store
    if total_all == 0:
        return float(s_diff)
    progress = (my_store + opp_store) / total_all
    w = 0.2 + 0.8 * progress
    score = float(s_diff) + w * float(my_sum - opp_sum) * 0.9
    # positional: seeds near store slightly better
    pos = (my_pits[1]+2*my_pits[2]+3*my_pits[3]+4*my_pits[4]+5*my_pits[5]) - (opp_pits[1]+2*opp_pits[2]+3*opp_pits[3]+4*opp_pits[4]+5*opp_pits[5])
    score += pos * 0.015
    # extra move opportunities
    me = 0
    oe = 0
    if my_pits[0]>0 and (my_pits[0]-6)%13==0: me+=1
    if my_pits[1]>0 and (my_pits[1]-5)%13==0: me+=1
    if my_pits[2]>0 and (my_pits[2]-4)%13==0: me+=1
    if my_pits[3]>0 and (my_pits[3]-3)%13==0: me+=1
    if my_pits[4]>0 and (my_pits[4]-2)%13==0: me+=1
    if my_pits[5]>0 and (my_pits[5]-1)%13==0: me+=1
    if opp_pits[0]>0 and (opp_pits[0]-6)%13==0: oe+=1
    if opp_pits[1]>0 and (opp_pits[1]-5)%13==0: oe+=1
    if opp_pits[2]>0 and (opp_pits[2]-4)%13==0: oe+=1
    if opp_pits[3]>0 and (opp_pits[3]-3)%13==0: oe+=1
    if opp_pits[4]>0 and (opp_pits[4]-2)%13==0: oe+=1
    if opp_pits[5]>0 and (opp_pits[5]-1)%13==0: oe+=1
    score += (me - oe) * 0.35
    # mobility
    mm = 0
    om = 0
    for v in my_pits:
        if v>0: mm+=1
    for v in opp_pits:
        if v>0: om+=1
    score += (mm - om) * 0.06
    score += 0.12 if turn_mine else -0.12
    return score

def _terminal_value(n_my_store, n_opp_store):
    d = n_my_store - n_opp_store
    if d > 0:
        return 100000.0 + float(d)
    elif d < 0:
        return -100000.0 + float(d)
    else:
        return 0.0

def _search(my_pits, my_store, opp_pits, opp_store, turn_mine, alpha, beta, depth, ply):
    global _nodes, _deadline, _TT
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()
    if ply >= 64:
        return _evaluate(my_pits, my_store, opp_pits, opp_store, turn_mine)
    if depth <= 0:
        return _evaluate(my_pits, my_store, opp_pits, opp_store, turn_mine)
    key = (tuple(my_pits), my_store, tuple(opp_pits), opp_store, turn_mine)
    ent = _TT.get(key)
    if ent is not None and ent[0] >= depth:
        v, fl = ent[1], ent[2]
        if fl == 0:
            return v
        elif fl == 1:
            if v > alpha:
                alpha = v
        else:
            if v < beta:
                beta = v
        if alpha >= beta:
            return v
    if turn_mine:
        cur = my_pits
    else:
        cur = opp_pits
    moves = []
    for i in range(6):
        if cur[i] > 0:
            moves.append(i)
    if not moves:
        s1 = my_pits[0]+my_pits[1]+my_pits[2]+my_pits[3]+my_pits[4]+my_pits[5]
        s2 = opp_pits[0]+opp_pits[1]+opp_pits[2]+opp_pits[3]+opp_pits[4]+opp_pits[5]
        return _terminal_value(my_store+s1, opp_store+s2)
    # build children
    children = []
    for m in moves:
        nmp, nms, nop, nos, nturn, over, extra = _apply_move(my_pits, my_store, opp_pits, opp_store, turn_mine, m)
        if over:
            tv = _terminal_value(nms, nos)
            # order wins first
            if turn_mine:
                order = tv
            else:
                order = -tv
            children.append((order, m, nmp, nms, nop, nos, nturn, over, extra, tv))
        else:
            if turn_mine:
                gain = nms - my_store
            else:
                gain = nos - opp_store
                gain = -gain
            o = gain * 10.0
            if extra:
                o += 50.0
            # prefer larger sow (rough)
            o += cur[m] * 0.1
            children.append((o, m, nmp, nms, nop, nos, nturn, over, extra, None))
    if turn_mine:
        children.sort(key=lambda x: x[0], reverse=True)
        best = -_INF
        a0 = alpha
        for _, m, nmp, nms, nop, nos, nturn, over, extra, tv in children:
            if over:
                val = tv
            else:
                nd = depth if extra else depth - 1
                val = _search(nmp, nms, nop, nos, nturn, alpha, beta, nd, ply+1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        # store TT
        if best <= a0:
            fl = 2
        elif best >= beta:
            fl = 1
        else:
            fl = 0
        _TT[key] = (depth, best, fl)
        return best
    else:
        children.sort(key=lambda x: x[0])
        best = _INF
        b0 = beta
        for _, m, nmp, nms, nop, nos, nturn, over, extra, tv in children:
            if over:
                val = tv
            else:
                nd = depth if extra else depth - 1
                val = _search(nmp, nms, nop, nos, nturn, alpha, beta, nd, ply+1)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        if best >= b0:
            fl = 1
        elif best <= alpha:
            fl = 2
        else:
            fl = 0
        _TT[key] = (depth, best, fl)
        return best

def policy(you: list[int], opponent: list[int]) -> int:
    try:
        my_pits = [int(you[0]),int(you[1]),int(you[2]),int(you[3]),int(you[4]),int(you[5])]
        my_store = int(you[6])
        opp_pits = [int(opponent[0]),int(opponent[1]),int(opponent[2]),int(opponent[3]),int(opponent[4]),int(opponent[5])]
        opp_store = int(opponent[6])
    except Exception:
        try:
            for i in range(6):
                if you[i] > 0:
                    return i
        except Exception:
            return 0
        return 0
    legal = [i for i in range(6) if my_pits[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]
    # quick greedy fallback
    def greedy():
        best_m = legal[0]
        best_s = -1e18
        for m in legal:
            try:
                nmp,nms,nop,nos,nturn,over,extra = _apply_move(my_pits,my_store,opp_pits,opp_store,True,m)
            except Exception:
                continue
            if over:
                d = nms - nos
                s = 100000 + d if d>0 else (float(d) if d==0 else -100000+d)
            else:
                s = (nms - my_store)*10.0
                if extra:
                    s += 20.0
                # capture bonus approx
                s += (nms - my_store)*2.0
                s += my_pits[m]*0.05 + m*0.02
            if s > best_s:
                best_s = s
                best_m = m
        return best_m
    fallback = greedy()
    global _deadline, _nodes, _TT
    start = time.perf_counter()
    limit = 0.85
    _deadline = start + limit
    _nodes = 0
    _TT = {}
    # initial ordering by greedy-like score
    scored = []
    for m in legal:
        try:
            nmp,nms,nop,nos,nturn,over,extra = _apply_move(my_pits,my_store,opp_pits,opp_store,True,m)
            if over:
                tv = _terminal_value(nms,nos)
                scored.append((tv+1000000, m))
            else:
                s = (nms-my_store)*10.0 + (20.0 if extra else 0.0)
                scored.append((s, m))
        except Exception:
            scored.append((-1e18, m))
    scored.sort(reverse=True)
    ordered = [m for _,m in scored]
    best_move = ordered[0]
    # check immediate winning move
    try:
        for m in ordered:
            nmp,nms,nop,nos,nturn,over,extra = _apply_move(my_pits,my_store,opp_pits,opp_store,True,m)
            if over and nms > nos:
                # biggest win
                pass
    except Exception:
        pass
    try:
        max_depth = 14
        for depth in range(1, max_depth+1):
            if time.perf_counter() > _deadline - 0.02:
                break
            alpha = -_INF
            beta = _INF
            scores = {}
            # search each root move
            for idx, m in enumerate(ordered):
                if time.perf_counter() > _deadline:
                    raise _Timeout()
                nmp,nms,nop,nos,nturn,over,extra = _apply_move(my_pits,my_store,opp_pits,opp_store,True,m)
                if over:
                    val = _terminal_value(nms,nos)
                else:
                    nd = depth if extra else depth-1
                    if nd < 0:
                        nd = 0
                    val = _search(nmp,nms,nop,nos,nturn,alpha,beta,nd,1)
                scores[m] = val
                if val > alpha:
                    alpha = val
            # update ordering and best
            ordered = sorted(ordered, key=lambda x: scores[x], reverse=True)
            best_move = ordered[0]
            # if winning found and depth large, can stop early
            bv = scores[best_move]
            if bv > 90000 and depth >= 6:
                break
            # if time low, stop
            if time.perf_counter() > _deadline - 0.05:
                break
    except _Timeout:
        pass
    except Exception:
        pass
    if best_move in legal:
        return int(best_move)
    return int(fallback if fallback in legal else legal[0])
