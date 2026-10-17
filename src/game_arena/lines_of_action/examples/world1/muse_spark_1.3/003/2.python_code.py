
import time

INF = 100000
TIME_LIMIT = 0.88

class _Timeout(Exception):
    pass

_start = 0.0
_nodes = 0

def _time_up():
    return (time.perf_counter() - _start) > TIME_LIMIT

def _to_flat(board):
    flat = [0]*64
    try:
        for r in range(8):
            row = board[r]
            for c in range(8):
                flat[r*8+c] = int(row[c])
    except Exception:
        try:
            import numpy as np
            arr = np.array(board).reshape(-1)
            for i in range(min(64, len(arr))):
                flat[i] = int(arr[i])
        except Exception:
            pass
    return flat

def _gen_moves(b, side):
    row_c = [0]*8
    col_c = [0]*8
    d1 = [0]*15
    d2 = [0]*15
    for r in range(8):
        base = r*8
        for c in range(8):
            v = b[base+c]
            if v != 0:
                row_c[r] += 1
                col_c[c] += 1
                d1[r-c+7] += 1
                d2[r+c] += 1
    moves = []
    opp = -side
    for r in range(8):
        for c in range(8):
            idx = r*8+c
            if b[idx] != side:
                continue
            dh = row_c[r]
            dv = col_c[c]
            dd1 = d1[r-c+7]
            dd2 = d2[r+c]
            # (dr,dc,d)
            for dr, dc, d in ((0,1,dh),(0,-1,dh),(1,0,dv),(-1,0,dv),(1,1,dd1),(-1,-1,dd1),(1,-1,dd2),(-1,1,dd2)):
                if d <= 0:
                    continue
                r2 = r + dr*d
                c2 = c + dc*d
                if r2 < 0 or r2 > 7 or c2 < 0 or c2 > 7:
                    continue
                dst = r2*8+c2
                dest_v = b[dst]
                if dest_v == side:
                    continue
                blocked = False
                for k in range(1, d):
                    mid = (r+dr*k)*8 + (c+dc*k)
                    if b[mid] == opp:
                        blocked = True
                        break
                if blocked:
                    continue
                cap = 1 if dest_v == opp else 0
                moves.append((r,c,r2,c2,idx,dst,cap))
    return moves

def _is_connected(b, side):
    first = -1
    cnt = 0
    for i,v in enumerate(b):
        if v == side:
            cnt += 1
            if first == -1:
                first = i
    if cnt <= 1:
        return True if cnt==1 else False
    # BFS
    stack = [first]
    seen = {first}
    while stack:
        cur = stack.pop()
        r = cur // 8
        c = cur % 8
        for dr in (-1,0,1):
            nr = r+dr
            if nr < 0 or nr > 7:
                continue
            for dc in (-1,0,1):
                if dr==0 and dc==0:
                    continue
                nc = c+dc
                if nc < 0 or nc > 7:
                    continue
                ni = nr*8+nc
                if b[ni]==side and ni not in seen:
                    seen.add(ni)
                    stack.append(ni)
    return len(seen)==cnt

def _groups_and_stats(b, side):
    pos = []
    for i,v in enumerate(b):
        if v==side:
            pos.append(i)
    n = len(pos)
    if n==0:
        return 0,0,0.0,0.0
    s = set(pos)
    visited = set()
    groups = 0
    largest = 0
    for p in pos:
        if p in visited:
            continue
        groups+=1
        stack=[p]
        visited.add(p)
        sz=0
        while stack:
            cur=stack.pop()
            sz+=1
            r=cur//8; c=cur%8
            for dr in (-1,0,1):
                nr=r+dr
                if nr<0 or nr>7: continue
                for dc in (-1,0,1):
                    if dr==0 and dc==0: continue
                    nc=c+dc
                    if nc<0 or nc>7: continue
                    ni=nr*8+nc
                    if ni in s and ni not in visited:
                        visited.add(ni)
                        stack.append(ni)
        if sz>largest:
            largest=sz
    sr=0; sc=0
    for p in pos:
        sr+=p//8; sc+=p%8
    cr=sr/n; cc=sc/n
    disp=0.0; cent=0.0
    for p in pos:
        r=p//8; c=p%8
        disp+=(r-cr)*(r-cr)+(c-cc)*(c-cc)
        cent+=(r-3.5)*(r-3.5)+(c-3.5)*(c-3.5)
    avg_disp=disp/n
    avg_cent=cent/n
    return groups,largest,avg_disp,avg_cent

def _eval_side(b, side):
    global _nodes
    # counts
    n_my=0; n_opp=0
    opp=-side
    for v in b:
        if v==side: n_my+=1
        elif v==opp: n_opp+=1
    if n_opp==0:
        return INF
    if n_my==0:
        return -INF
    mg,ml,md,mc=_groups_and_stats(b, side)
    og,ol,od,oc=_groups_and_stats(b, opp)
    # both connected -> previous mover (opp) wins -> loss for side
    my_conn = (mg==1)
    opp_conn = (og==1)
    if opp_conn and my_conn:
        return -INF
    if opp_conn:
        return -INF
    if my_conn:
        return INF
    score = (og-mg)*50.0 + (ml-ol)*10.0 + (od-md)*2.0 + (oc-mc)*1.0 + (n_opp-n_my)*2.0
    if score>9000: score=9000
    if score<-9000: score=-9000
    return score

def _order_moves(moves):
    if not moves:
        return moves
    scored=[]
    for m in moves:
        fr,fc,tr,tc,si,di,cap=m
        src_c=(fr-3.5)*(fr-3.5)+(fc-3.5)*(fc-3.5)
        dst_c=(tr-3.5)*(tr-3.5)+(tc-3.5)*(tc-3.5)
        s=cap*120.0 + (src_c-dst_c)*2.0
        scored.append((s,m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _,m in scored]

def _negamax(b, side, depth, alpha, beta):
    global _nodes
    _nodes+=1
    if (_nodes & 255)==0 and _time_up():
        raise _Timeout()
    opp=-side
    # if opponent already connected, we lost
    # quick check via groups? use _is_connected for opp
    if _is_connected(b, opp):
        return -INF
    if depth==0:
        return _eval_side(b, side)
    moves=_gen_moves(b, side)
    if not moves:
        return -INF
    moves=_order_moves(moves)
    best=-INF
    for fr,fc,tr,tc,si,di,cap in moves:
        saved=b[di]
        b[di]=side
        b[si]=0
        # immediate win?
        if _is_connected(b, side):
            b[si]=side
            b[di]=saved
            return INF
        try:
            val=-_negamax(b, opp, depth-1, -beta, -alpha)
        except _Timeout:
            b[si]=side
            b[di]=saved
            raise
        b[si]=side
        b[di]=saved
        if val>best:
            best=val
        if best>alpha:
            alpha=best
        if alpha>=beta:
            break
        if _time_up():
            raise _Timeout()
    return best

def policy(board) -> str:
    global _start, _nodes
    _start=time.perf_counter()
    _nodes=0
    b=_to_flat(board)
    moves=_gen_moves(b, 1)
    if not moves:
        return "0,0:0,0"
    if len(moves)==1:
        m=moves[0]
        return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
    # immediate winning move
    for m in moves:
        fr,fc,tr,tc,si,di,cap=m
        saved=b[di]
        b[di]=1; b[si]=0
        win=_is_connected(b, 1)
        b[si]=1; b[di]=saved
        if win:
            return f"{fr},{fc}:{tr},{tc}"
        if _time_up():
            break
    ordered=_order_moves(moves)
    best_move=ordered[0]
    # static fallback: best 1-ply eval
    try:
        best_score=-1e18
        tmp_best=best_move
        for m in ordered:
            fr,fc,tr,tc,si,di,cap=m
            saved=b[di]
            b[di]=1; b[si]=0
            s=_eval_side(b, -1)
            # value for us = -s (s is for opponent)
            v=-s
            # capture bonus already in eval
            b[si]=1; b[di]=saved
            if v>best_score:
                best_score=v
                tmp_best=m
            if _time_up():
                break
        best_move=tmp_best
    except Exception:
        pass
    # iterative deepening
    max_depth=5
    # adapt depth to branching
    if len(ordered)>30:
        max_depth=4
    cur_order=list(ordered)
    # reorder cur_order to put best_move first
    try:
        cur_order.remove(best_move)
        cur_order=[best_move]+cur_order
    except Exception:
        pass
    for depth in range(1, max_depth+1):
        if _time_up():
            break
        try:
            scores=[]
            alpha=-INF
            beta=INF
            for m in cur_order:
                fr,fc,tr,tc,si,di,cap=m
                saved=b[di]
                b[di]=1; b[si]=0
                if _is_connected(b, 1):
                    b[si]=1; b[di]=saved
                    return f"{fr},{fc}:{tr},{tc}"
                val=-_negamax(b, -1, depth-1, -beta, -alpha)
                b[si]=1; b[di]=saved
                scores.append((val,m))
                if val>alpha:
                    alpha=val
                if _time_up():
                    raise _Timeout()
            scores.sort(key=lambda x: x[0], reverse=True)
            best_move=scores[0][1]
            cur_order=[m for _,m in scores]
            # if winning line found, stop
            if scores[0][0]>=INF-1000:
                break
        except _Timeout:
            break
        except Exception:
            break
    m=best_move
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
