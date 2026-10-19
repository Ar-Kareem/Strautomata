
import numpy as np
import time

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

# precompute neighbours and rays for 6x6, flat index 0..35
NEIGH = [[] for _ in range(36)]
RAYS = [[[] for _ in range(8)] for _ in range(36)]
for s in range(36):
    r = s // 6
    c = s % 6
    for di,(dr,dc) in enumerate(DIRS):
        nr = r + dr
        nc = c + dc
        lst = []
        while 0 <= nr < 6 and 0 <= nc < 6:
            ni = nr*6+nc
            lst.append(ni)
            if len(lst) == 1:
                NEIGH[s].append(ni)
            nr += dr
            nc += dc
        RAYS[s][di] = lst

POW2 = [0.5**i for i in range(40)]

WIN = 100000.0

def _gen_moves(b, player):
    moves = []
    # b is flat list len 36
    for f in range(36):
        if b[f] != player:
            continue
        fr = f // 6
        fc = f % 6
        for di in range(8):
            ray = RAYS[f][di]
            for t in ray:
                if b[t] != 0:
                    break
                tr = t // 6
                tc = t % 6
                # arrows from t, f is now empty
                for adi in range(8):
                    aray = RAYS[t][adi]
                    for a in aray:
                        if a == f:
                            ar = a // 6
                            ac = a % 6
                            moves.append((fr,fc,tr,tc,ar,ac))
                            continue
                        if b[a] != 0:
                            break
                        ar = a // 6
                        ac = a % 6
                        moves.append((fr,fc,tr,tc,ar,ac))
    return moves

def _eval_board(b):
    # b flat list, perspective player 1
    d1 = [-1]*36
    d2 = [-1]*36
    q1 = []
    q2 = []
    mob1_pos = []
    mob2_pos = []
    empties = 0
    for i,v in enumerate(b):
        if v == 1:
            d1[i]=0
            q1.append(i)
            mob1_pos.append(i)
        elif v == 2:
            d2[i]=0
            q2.append(i)
            mob2_pos.append(i)
        elif v == 0:
            empties += 1
    # bfs1
    h = 0
    while h < len(q1):
        cur = q1[h]; h+=1
        nd = d1[cur]+1
        # small optimisation: if nd > 10 still continue (pow tiny but count matters)
        for nb in NEIGH[cur]:
            if d1[nb]==-1 and b[nb]==0:
                d1[nb]=nd
                q1.append(nb)
    h = 0
    while h < len(q2):
        cur = q2[h]; h+=1
        nd = d2[cur]+1
        for nb in NEIGH[cur]:
            if d2[nb]==-1 and b[nb]==0:
                d2[nb]=nd
                q2.append(nb)
    terr_count = 0
    terr_pow = 0.0
    for i,v in enumerate(b):
        if v != 0:
            continue
        a = d1[i]
        cc = d2[i]
        pa = 0.0 if a==-1 else (POW2[a] if a < 40 else 0.0)
        pb = 0.0 if cc==-1 else (POW2[cc] if cc < 40 else 0.0)
        terr_pow += pa - pb
        if a==-1 and cc==-1:
            pass
        elif a==-1:
            terr_count -= 1
        elif cc==-1:
            terr_count += 1
        else:
            if a < cc:
                terr_count += 1
            elif cc < a:
                terr_count -= 1
    # mobility (queen destinations)
    mob1 = 0
    for f in mob1_pos:
        for di in range(8):
            for t in RAYS[f][di]:
                if b[t]!=0:
                    break
                mob1+=1
    mob2 = 0
    for f in mob2_pos:
        for di in range(8):
            for t in RAYS[f][di]:
                if b[t]!=0:
                    break
                mob2+=1
    if mob2==0 and mob1==0:
        # no moves for both? treat as drawish, but after our move mob1>0 normally
        return 0.0
    if mob2==0:
        return WIN
    if mob1==0:
        return -WIN
    # phase weights
    if empties > 24:
        wc, wp, wm = 1.0, 2.0, 1.5
    elif empties > 16:
        wc, wp, wm = 2.0, 4.0, 1.0
    elif empties > 10:
        wc, wp, wm = 4.0, 5.0, 0.7
    else:
        wc, wp, wm = 8.0, 6.0, 0.5
    return terr_count*wc + terr_pow*wp + (mob1-mob2)*wm

def _apply(b, m):
    nb = b[:]
    fr,fc,tr,tc,ar,ac = m
    nb[fr*6+fc]=0
    nb[tr*6+tc]=1
    nb[ar*6+ac]=-1
    return nb

def _apply_inplace_copy(b, m):
    # same as _apply
    return _apply(b,m)

def _fmt(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"

def _find_any(board_np):
    # brute fallback to guarantee legality
    try:
        n = board_np.shape[0]
    except:
        n = 6
    b2d = board_np
    for fr in range(n):
        for fc in range(n):
            if b2d[fr,fc]!=1:
                continue
            for dr,dc in DIRS:
                nr=fr+dr; nc=fc+dc
                while 0<=nr<n and 0<=nc<n and b2d[nr,nc]==0:
                    tr=nr; tc=nc
                    # try arrows
                    # simulate board after move for blocker check
                    for adr,adc in DIRS:
                        ar=tr+adr; ac=tc+adc
                        while 0<=ar<n and 0<=ac<n:
                            if ar==fr and ac==fc:
                                return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
                            if not (b2d[ar,ac]==0):
                                break
                            # check that arrow path from tr didn't cross blocked except fr
                            # since we break on blocked, this cell is reachable
                            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
                            # only need first
                        # continue while? we returned already
                    nr+=dr; nc+=dc
    return "0,0:0,1:0,2"

def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90
    try:
        arr = np.asarray(board)
        if arr.shape != (6,6):
            # general fallback for other sizes (should not happen)
            return _find_any(arr)
        b = arr.reshape(-1).tolist()
        my_moves = _gen_moves(b, 1)
        if len(my_moves)==0:
            return _find_any(arr)
        if len(my_moves)==1:
            return _fmt(my_moves[0])
        # static evaluation of all moves
        scored = []  # (val, move, board_after)
        best_val = -1e18
        best_move = my_moves[0]
        # to save time if huge branching, we still eval all (usually <1000)
        for m in my_moves:
            if time.perf_counter() > deadline - 0.05:
                break
            b2 = _apply(b, m)
            v = _eval_board(b2)
            scored.append((v,m,b2))
            if v > best_val:
                best_val = v
                best_move = m
                if v >= WIN-1:
                    return _fmt(m)
        if len(scored)==0:
            return _fmt(best_move)
        # if we timed out during static phase, return best so far
        if time.perf_counter() > deadline - 0.15:
            return _fmt(best_move)
        scored.sort(key=lambda x: -x[0])
        n = len(scored)
        if n > 400:
            K = 6
        elif n > 200:
            K = 8
        elif n > 100:
            K = 10
        elif n > 50:
            K = 12
        else:
            K = min(n, 16)
        K = min(K, n)
        overall_best = best_move
        overall_best_val = -1e18
        alpha = -1e18
        # pre-collect for quick win check: if best static already winning, returned above
        for idx in range(K):
            if time.perf_counter() > deadline - 0.05:
                break
            v0,m0,b_after = scored[idx]
            opp_moves = _gen_moves(b_after, 2)
            if len(opp_moves)==0:
                return _fmt(m0)
            # cheap ordering: arrows close to our amazons first
            # our positions in b_after
            our_rs = []
            our_cs = []
            for ii,vv in enumerate(b_after):
                if vv==1:
                    our_rs.append(ii//6)
                    our_cs.append(ii%6)
            # if too many opp moves, truncate to closest 200 to bound time
            if len(opp_moves) > 350:
                # compute keys
                tmp=[]
                for om in opp_moves:
                    ar=om[4]; ac=om[5]
                    dmin=100
                    for k in range(len(our_rs)):
                        d = abs(ar-our_rs[k])+abs(ac-our_cs[k])
                        if d<dmin:
                            dmin=d
                            if dmin==0:
                                break
                    tmp.append((dmin,om))
                tmp.sort(key=lambda x: x[0])
                opp_moves = [x[1] for x in tmp[:220]]
            else:
                # sort by closeness
                def _key(om):
                    ar=om[4]; ac=om[5]
                    dmin=100
                    for k in range(len(our_rs)):
                        d = abs(ar-our_rs[k])+abs(ac-our_cs[k])
                        if d<dmin:
                            dmin=d
                    return dmin
                opp_moves.sort(key=_key)
            cur_min = 1e18
            # iterate opponent replies
            for om in opp_moves:
                # time check periodically
                # apply opponent move: need board with player 2 move
                # _apply assumes moving piece is 1, fix for player 2
                fr,fc,tr,tc,ar,ac = om
                b3 = b_after[:]
                b3[fr*6+fc]=0
                b3[tr*6+tc]=2
                b3[ar*6+ac]=-1
                vv = _eval_board(b3)
                if vv < cur_min:
                    cur_min = vv
                    if cur_min <= alpha:
                        break
                # occasional time check
                # check every 64? use counter
            # cur_min is value of m0 (opponent best reply)
            if cur_min > overall_best_val:
                overall_best_val = cur_min
                overall_best = m0
                if overall_best_val > alpha:
                    alpha = overall_best_val
        return _fmt(overall_best)
    except Exception:
        try:
            return _find_any(np.asarray(board))
        except Exception:
            return "0,0:0,1:0,2"
