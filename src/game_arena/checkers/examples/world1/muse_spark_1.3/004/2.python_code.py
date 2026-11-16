
import time
import random

# piece codes: 0 empty, 1 b_man, 2 b_king, 3 w_man, 4 w_king
W_MAN_T = [0]*64
B_MAN_T = [0]*64
KING_T = [0]*64
for _idx in range(64):
    _r = _idx // 8
    _c = _idx % 8
    _dist = abs(_r-3.5)+abs(_c-3.5)
    _central_man = (7.0-_dist)*1.5
    _back_w = 6 if _r==0 else (3 if _r==1 else 0)
    _back_b = 6 if _r==7 else (3 if _r==6 else 0)
    W_MAN_T[_idx] = _r*4 + _central_man + _back_w
    B_MAN_T[_idx] = (7-_r)*4 + _central_man + _back_b
    KING_T[_idx] = (7.0-_dist)*4.0

class _TO(Exception):
    pass

def _opp(turn):
    return 'w' if turn=='b' else 'b'

def _gen_moves(board, turn):
    caps = []
    quiets = []
    is_black = (turn=='b')
    for idx in range(64):
        p = board[idx]
        if p==0:
            continue
        if is_black:
            if p!=1 and p!=2:
                continue
            is_king = (p==2)
        else:
            if p!=3 and p!=4:
                continue
            is_king = (p==4)
        r = idx >> 3
        c = idx & 7
        if is_king:
            # 4 dirs
            # unrolled for speed
            # dr,dc = -1,-1
            if r>0 and c>0:
                nidx = idx-9
                npiece = board[nidx]
                if npiece==0:
                    quiets.append((idx,nidx,-1))
                elif (npiece==3 or npiece==4) if is_black else (npiece==1 or npiece==2):
                    if r>1 and c>1 and board[idx-18]==0:
                        caps.append((idx,idx-18,idx-9))
            if r>0 and c<7:
                nidx = idx-7
                npiece = board[nidx]
                if npiece==0:
                    quiets.append((idx,nidx,-1))
                elif (npiece==3 or npiece==4) if is_black else (npiece==1 or npiece==2):
                    if r>1 and c<6 and board[idx-14]==0:
                        caps.append((idx,idx-14,idx-7))
            if r<7 and c>0:
                nidx = idx+7
                npiece = board[nidx]
                if npiece==0:
                    quiets.append((idx,nidx,-1))
                elif (npiece==3 or npiece==4) if is_black else (npiece==1 or npiece==2):
                    if r<6 and c>1 and board[idx+14]==0:
                        caps.append((idx,idx+14,idx+7))
            if r<7 and c<7:
                nidx = idx+9
                npiece = board[nidx]
                if npiece==0:
                    quiets.append((idx,nidx,-1))
                elif (npiece==3 or npiece==4) if is_black else (npiece==1 or npiece==2):
                    if r<6 and c<6 and board[idx+18]==0:
                        caps.append((idx,idx+18,idx+9))
        else:
            if is_black: # dr=-1
                if r>0:
                    if c>0:
                        nidx = idx-9
                        npiece = board[nidx]
                        if npiece==0:
                            quiets.append((idx,nidx,-1))
                        elif npiece==3 or npiece==4:
                            if r>1 and c>1 and board[idx-18]==0:
                                caps.append((idx,idx-18,idx-9))
                    if c<7:
                        nidx = idx-7
                        npiece = board[nidx]
                        if npiece==0:
                            quiets.append((idx,nidx,-1))
                        elif npiece==3 or npiece==4:
                            if r>1 and c<6 and board[idx-14]==0:
                                caps.append((idx,idx-14,idx-7))
            else: # white dr=+1
                if r<7:
                    if c>0:
                        nidx = idx+7
                        npiece = board[nidx]
                        if npiece==0:
                            quiets.append((idx,nidx,-1))
                        elif npiece==1 or npiece==2:
                            if r<6 and c>1 and board[idx+14]==0:
                                caps.append((idx,idx+14,idx+7))
                    if c<7:
                        nidx = idx+9
                        npiece = board[nidx]
                        if npiece==0:
                            quiets.append((idx,nidx,-1))
                        elif npiece==1 or npiece==2:
                            if r<6 and c<6 and board[idx+18]==0:
                                caps.append((idx,idx+18,idx+9))
    if caps:
        return caps
    return quiets

def _static_white(board):
    s = 0.0
    # manual loop
    for idx,p in enumerate(board):
        if p==1:
            s -= 100 + B_MAN_T[idx]
        elif p==2:
            s -= 140 + KING_T[idx]
        elif p==3:
            s += 100 + W_MAN_T[idx]
        elif p==4:
            s += 140 + KING_T[idx]
    return s

def _move_score(board, m):
    f,t,cap = m
    s = 0
    if cap != -1:
        v = board[cap]
        if v==1 or v==3:
            s += 100
        elif v==2 or v==4:
            s += 150
        s += 1000
        a = board[f]
        if a==2 or a==4:
            s -= 14
        else:
            s -= 10
    moving = board[f]
    # promotion bonus
    if moving==1 and (t>>3)==0:
        s += 900
    elif moving==3 and (t>>3)==7:
        s += 900
    # positional gain small
    if moving==2 or moving==4:
        s += (KING_T[t]-KING_T[f])*0.5
    else:
        if moving==1:
            s += (B_MAN_T[t]-B_MAN_T[f])*0.5
        elif moving==3:
            s += (W_MAN_T[t]-W_MAN_T[f])*0.5
    return s

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        board = [0]*64
        if color=='b':
            for r,c in my_men:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=1
            for r,c in my_kings:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=2
            for r,c in opp_men:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=3
            for r,c in opp_kings:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=4
        else:
            for r,c in my_men:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=3
            for r,c in my_kings:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=4
            for r,c in opp_men:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=1
            for r,c in opp_kings:
                if 0<=r<8 and 0<=c<8:
                    board[r*8+c]=2

        moves = _gen_moves(board, color)
        if not moves:
            # no moves: return any own piece move (will lose but must return tuple)
            if my_men:
                r,c = my_men[0]
                # try to find empty neighbour
                for dr,dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
                    nr,nc = r+dr,c+dc
                    if 0<=nr<8 and 0<=nc<8 and board[nr*8+nc]==0:
                        return ((r,c),(nr,nc))
                return ((r,c),(r,c))
            if my_kings:
                r,c = my_kings[0]
                return ((r,c),(r,c))
            return ((2,2),(3,3))
        if len(moves)==1:
            f,t,_ = moves[0]
            return ((f>>3,f&7),(t>>3,t&7))

        # order initial
        scored = [(_move_score(board,m)+random.random()*1e-3, m) for m in moves]
        scored.sort(key=lambda x: -x[0])
        moves = [m for _,m in scored]
        best = moves[0]

        deadline = time.perf_counter() + 0.85
        nodes = [0]
        INF = 10**9

        # closures for speed
        bmt = B_MAN_T
        wmt = W_MAN_T
        kt = KING_T

        def static_rel(bd, turn):
            s = 0.0
            for idx,p in enumerate(bd):
                if p==1:
                    s -= 100 + bmt[idx]
                elif p==2:
                    s -= 140 + kt[idx]
                elif p==3:
                    s += 100 + wmt[idx]
                elif p==4:
                    s += 140 + kt[idx]
            if turn=='b':
                return -s
            return s

        def qsearch(bd, turn, alpha, beta, ply, qd):
            nodes[0]+=1
            if (nodes[0] & 511)==0 and time.perf_counter()>deadline:
                raise _TO()
            stand = static_rel(bd, turn)
            if stand>=beta:
                return beta
            if stand>alpha:
                alpha=stand
            if qd>=8:
                return alpha
            ms = _gen_moves(bd, turn)
            if not ms:
                return -10000+ply
            if ms[0][2]==-1:
                return stand
            # order caps
            ms.sort(key=lambda m: _move_score(bd,m), reverse=True)
            nturn = 'w' if turn=='b' else 'b'
            for f,t,cap in ms:
                orig = bd[f]
                captured = bd[cap]
                bd[f]=0
                nm = orig
                if orig==1 and (t>>3)==0:
                    nm=2
                elif orig==3 and (t>>3)==7:
                    nm=4
                bd[t]=nm
                bd[cap]=0
                val = -qsearch(bd, nturn, -beta, -alpha, ply+1, qd+1)
                bd[f]=orig
                bd[t]=0
                bd[cap]=captured
                if val>alpha:
                    alpha=val
                if alpha>=beta:
                    break
            return alpha

        def negamax(bd, turn, depth, alpha, beta, ply):
            nodes[0]+=1
            if (nodes[0] & 511)==0 and time.perf_counter()>deadline:
                raise _TO()
            ms = _gen_moves(bd, turn)
            if not ms:
                return -10000+ply
            if depth<=0:
                if ms[0][2]!=-1:
                    return qsearch(bd, turn, alpha, beta, ply, 0)
                return static_rel(bd, turn)
            # order
            ms.sort(key=lambda m: _move_score(bd,m), reverse=True)
            nturn = 'w' if turn=='b' else 'b'
            bestv = -INF
            for f,t,cap in ms:
                orig = bd[f]
                captured = bd[cap] if cap!=-1 else 0
                bd[f]=0
                nm = orig
                if orig==1 and (t>>3)==0:
                    nm=2
                elif orig==3 and (t>>3)==7:
                    nm=4
                bd[t]=nm
                if cap!=-1:
                    bd[cap]=0
                val = -negamax(bd, nturn, depth-1, -beta, -alpha, ply+1)
                bd[f]=orig
                bd[t]=0
                if cap!=-1:
                    bd[cap]=captured
                if val>bestv:
                    bestv=val
                if val>alpha:
                    alpha=val
                if alpha>=beta:
                    break
            return bestv

        # iterative deepening
        # estimate max depth by piece count
        cnt = sum(1 for x in board if x!=0)
        max_depth = 12 if cnt<8 else (8 if cnt<14 else 6)
        try:
            for depth in range(1, max_depth+1):
                # put current best first
                try:
                    moves.remove(best)
                    moves.insert(0,best)
                except:
                    pass
                alpha = -INF
                beta = INF
                cur_best = best
                cur_best_val = -INF
                nturn = _opp(color)
                # root move loop with alpha-beta
                for m in list(moves):
                    f,t,cap = m
                    orig = board[f]
                    captured = board[cap] if cap!=-1 else 0
                    board[f]=0
                    nm = orig
                    if orig==1 and (t>>3)==0:
                        nm=2
                    elif orig==3 and (t>>3)==7:
                        nm=4
                    board[t]=nm
                    if cap!=-1:
                        board[cap]=0
                    val = -negamax(board, nturn, depth-1, -beta, -alpha, 1)
                    board[f]=orig
                    board[t]=0
                    if cap!=-1:
                        board[cap]=captured
                    if val>cur_best_val:
                        cur_best_val=val
                        cur_best= m
                    if val>alpha:
                        alpha=val
                    if alpha>=beta:
                        break
                    if time.perf_counter()>deadline:
                        raise _TO()
                best = cur_best
                # reorder moves by last search value for next depth (simple: best first, rest ordered)
                # keep best at front
                # early exit if winning
                if cur_best_val>9000:
                    break
                if time.perf_counter()>deadline-0.05:
                    break
        except _TO:
            pass

        f,t,_ = best
        return ((f>>3,f&7),(t>>3,t&7))
    except Exception:
        try:
            # emergency fallback: try capture else quiet forward
            is_b = (color=='b')
            all_my = list(my_men)+list(my_kings)
            menset = set(map(tuple,my_men))
            occ = set(map(tuple,my_men))|set(map(tuple,my_kings))|set(map(tuple,opp_men))|set(map(tuple,opp_kings))
            oppset = set(map(tuple,opp_men))|set(map(tuple,opp_kings))
            # captures first
            for r,c in all_my:
                is_king = (r,c) not in menset
                if is_king:
                    dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]
                else:
                    dirs=[(-1,-1),(-1,1)] if is_b else [(1,-1),(1,1)]
                for dr,dc in dirs:
                    mr, mc = r+dr, c+dc
                    lr, lc = r+2*dr, c+2*dc
                    if 0<=lr<8 and 0<=lc<8 and (mr,mc) in oppset and (lr,lc) not in occ:
                        return ((r,c),(lr,lc))
            for r,c in all_my:
                is_king = (r,c) not in menset
                if is_king:
                    dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]
                else:
                    dirs=[(-1,-1),(-1,1)] if is_b else [(1,-1),(1,1)]
                for dr,dc in dirs:
                    nr,nc = r+dr,c+dc
                    if 0<=nr<8 and 0<=nc<8 and (nr,nc) not in occ:
                        return ((r,c),(nr,nc))
            if all_my:
                r,c = all_my[0]
                return ((r,c),(r,c))
        except Exception:
            pass
        return ((2,1),(3,2)) if color=='w' else ((5,0),(4,1))
