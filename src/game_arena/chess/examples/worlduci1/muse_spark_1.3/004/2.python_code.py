
import time
import random

VAL = [0,100,320,330,500,900,0]

STD_P = [0,0,0,0,0,0,0,0,50,50,50,50,50,50,50,50,10,10,20,30,30,20,10,10,5,5,10,25,25,10,5,5,0,0,0,20,20,0,0,0,5,-5,-10,0,0,-10,-5,5,5,10,10,-20,-20,10,10,5,0,0,0,0,0,0,0,0]
STD_N = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
STD_B = [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20]
STD_R = [0,0,0,0,0,0,0,0,5,10,10,10,10,10,10,5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,0,0,0,5,5,0,0,0]
STD_Q = [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20]
STD_KM = [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20]
STD_KE = [-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,10,-30,-30,-10,30,40,40,30,10,-30,-30,-10,30,40,40,30,10,-30,-30,-10,20,30,30,20,10,-30,-30,-30,0,0,0,0,-30,-30,-50,-30,-30,-30,-30,-30,-30,-50]

W_PST = [[0]*64 for _ in range(7)]
B_PST = [[0]*64 for _ in range(7)]
W_KM = [0]*64
B_KM = [0]*64
W_KE = [0]*64
B_KE = [0]*64

for _sq in range(64):
    _f = _sq & 7
    _r = _sq >> 3
    _wi = (7-_r)*8+_f
    _bi = _r*8+_f
    W_PST[1][_sq]=STD_P[_wi]; B_PST[1][_sq]=STD_P[_bi]
    W_PST[2][_sq]=STD_N[_wi]; B_PST[2][_sq]=STD_N[_bi]
    W_PST[3][_sq]=STD_B[_wi]; B_PST[3][_sq]=STD_B[_bi]
    W_PST[4][_sq]=STD_R[_wi]; B_PST[4][_sq]=STD_R[_bi]
    W_PST[5][_sq]=STD_Q[_wi]; B_PST[5][_sq]=STD_Q[_bi]
    W_KM[_sq]=STD_KM[_wi]; B_KM[_sq]=STD_KM[_bi]
    W_KE[_sq]=STD_KE[_wi]; B_KE[_sq]=STD_KE[_bi]

KNIGHT_TARGETS=[[] for _ in range(64)]
KING_TARGETS=[[] for _ in range(64)]
for _s in range(64):
    _f=_s&7; _r=_s>>3
    for _df,_dr in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        _nf=_f+_df; _nr=_r+_dr
        if 0<=_nf<8 and 0<=_nr<8:
            KNIGHT_TARGETS[_s].append(_nr*8+_nf)
    for _df,_dr in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
        _nf=_f+_df; _nr=_r+_dr
        if 0<=_nf<8 and 0<=_nr<8:
            KING_TARGETS[_s].append(_nr*8+_nf)

ROOK_DIRS=[(1,0),(-1,0),(0,1),(0,-1)]
BISHOP_DIRS=[(1,1),(1,-1),(-1,1),(-1,-1)]
QUEEN_DIRS=ROOK_DIRS+BISHOP_DIRS

MATE=100000
INF=1000000
PROMO_UCI={5:'q',4:'r',3:'b',2:'n'}
PROMO_FROM={'q':5,'r':4,'b':3,'n':2,'Q':5,'R':4,'B':3,'N':2}

class _TO(Exception):
    pass

def _sq_to_idx(s):
    return (ord(s[1])-49)*8+(ord(s[0])-97)

def _idx_to_sq(i):
    return chr((i&7)+97)+chr((i>>3)+49)

def _uci(fr,to,promo):
    s=_idx_to_sq(fr)+_idx_to_sq(to)
    if promo:
        s+=PROMO_UCI[promo]
    return s

def _is_attacked(board,sq,by_white):
    f=sq&7; r=sq>>3
    if by_white:
        if r>0:
            if f>0 and board[sq-9]==1:
                return True
            if f<7 and board[sq-7]==1:
                return True
    else:
        if r<7:
            if f>0 and board[sq+7]==-1:
                return True
            if f<7 and board[sq+9]==-1:
                return True
    for to in KNIGHT_TARGETS[sq]:
        p=board[to]
        if p==(2 if by_white else -2):
            return True
    for to in KING_TARGETS[sq]:
        p=board[to]
        if p==(6 if by_white else -6):
            return True
    for df,dr in ROOK_DIRS:
        ff=f+df; rr=r+dr
        while 0<=ff<8 and 0<=rr<8:
            p=board[rr*8+ff]
            if p!=0:
                if (p>0)==by_white and (p==4 or p==5 or p==-4 or p==-5):
                    return True
                break
            ff+=df; rr+=dr
    for df,dr in BISHOP_DIRS:
        ff=f+df; rr=r+dr
        while 0<=ff<8 and 0<=rr<8:
            p=board[rr*8+ff]
            if p!=0:
                if (p>0)==by_white and (abs(p)==3 or abs(p)==5):
                    return True
                break
            ff+=df; rr+=dr
    return False

def _evaluate(board):
    score=0
    wbf=0; bbf=0
    wq=False; bq=False
    tot=0
    wpf=[0]*8; bpf=[0]*8
    wk=-1; bk=-1
    for sq in range(64):
        p=board[sq]
        if p==0:
            continue
        if p>0:
            t=p
            if t==1:
                score+=100+W_PST[1][sq]
                wpf[sq&7]+=1
            elif t==2:
                score+=320+W_PST[2][sq]; tot+=320
            elif t==3:
                score+=330+W_PST[3][sq]; tot+=330; wbf+=1
            elif t==4:
                score+=500+W_PST[4][sq]; tot+=500
            elif t==5:
                score+=900+W_PST[5][sq]; tot+=900; wq=True
            elif t==6:
                wk=sq
        else:
            t=-p
            if t==1:
                score-=100+B_PST[1][sq]
                bpf[sq&7]+=1
            elif t==2:
                score-=320+B_PST[2][sq]; tot+=320
            elif t==3:
                score-=330+B_PST[3][sq]; tot+=330; bbf+=1
            elif t==4:
                score-=500+B_PST[4][sq]; tot+=500
            elif t==5:
                score-=900+B_PST[5][sq]; tot+=900; bq=True
            elif t==6:
                bk=sq
    endgame = (not wq or not bq) or (tot<2600)
    if wk!=-1:
        score+= W_KE[wk] if endgame else W_KM[wk]
    if bk!=-1:
        score-= B_KE[bk] if endgame else B_KM[bk]
    if wbf>=2:
        score+=30
    if bbf>=2:
        score-=30
    for f in range(8):
        c=wpf[f]
        if c>1:
            score-=12*(c-1)
        if c>0:
            left = wpf[f-1] if f>0 else 0
            right = wpf[f+1] if f<7 else 0
            if left==0 and right==0:
                score-=12
        c2=bpf[f]
        if c2>1:
            score+=12*(c2-1)
        if c2>0:
            left = bpf[f-1] if f>0 else 0
            right = bpf[f+1] if f<7 else 0
            if left==0 and right==0:
                score+=12
    for sq in range(64):
        p=board[sq]
        if p==4:
            f=sq&7
            if wpf[f]==0:
                if bpf[f]==0:
                    score+=15
                else:
                    score+=10
        elif p==-4:
            f=sq&7
            if bpf[f]==0:
                if wpf[f]==0:
                    score-=15
                else:
                    score-=10
    return score

def _gen_pseudo(board,wtm,caps_only):
    moves=[]
    ap=moves.append
    for fr in range(64):
        pc=board[fr]
        if pc==0:
            continue
        if (pc>0)!=wtm:
            continue
        t=pc if pc>0 else -pc
        f=fr&7; r=fr>>3
        if t==1:
            d=1 if wtm else -1
            sr=1 if wtm else 6
            pr=7 if wtm else 0
            nr=r+d
            if 0<=nr<8:
                to=nr*8+f
                if board[to]==0:
                    if nr==pr:
                        ap((fr,to,5)); ap((fr,to,4)); ap((fr,to,3)); ap((fr,to,2))
                    else:
                        if not caps_only:
                            ap((fr,to,0))
                            if r==sr:
                                to2=(r+2*d)*8+f
                                if board[to2]==0:
                                    ap((fr,to2,0))
                for df in (-1,1):
                    nf=f+df
                    if 0<=nf<8:
                        to2=nr*8+nf
                        cap=board[to2]
                        if cap!=0 and (cap>0)!=wtm and abs(cap)!=6:
                            if nr==pr:
                                ap((fr,to2,5)); ap((fr,to2,4)); ap((fr,to2,3)); ap((fr,to2,2))
                            else:
                                ap((fr,to2,0))
        elif t==2:
            for to in KNIGHT_TARGETS[fr]:
                cap=board[to]
                if cap==0:
                    if not caps_only:
                        ap((fr,to,0))
                elif (cap>0)!=wtm and abs(cap)!=6:
                    ap((fr,to,0))
        elif t==6:
            for to in KING_TARGETS[fr]:
                cap=board[to]
                if cap==0:
                    if not caps_only:
                        ap((fr,to,0))
                elif (cap>0)!=wtm and abs(cap)!=6:
                    ap((fr,to,0))
        else:
            if t==4:
                dirs=ROOK_DIRS
            elif t==3:
                dirs=BISHOP_DIRS
            else:
                dirs=QUEEN_DIRS
            for df,dr in dirs:
                ff=f+df; rr=r+dr
                while 0<=ff<8 and 0<=rr<8:
                    to=rr*8+ff
                    cap=board[to]
                    if cap==0:
                        if not caps_only:
                            ap((fr,to,0))
                    else:
                        if (cap>0)!=wtm and abs(cap)!=6:
                            ap((fr,to,0))
                        break
                    ff+=df; rr+=dr
    return moves

def _order(board,moves):
    if not moves:
        return moves
    scored=[]
    for fr,to,pr in moves:
        cap=board[to]
        s=0
        if cap!=0:
            av=VAL[cap if cap>0 else -cap]
            mv=VAL[board[fr] if board[fr]>0 else -board[fr]]
            s+=10000+10*av-mv
        if pr:
            s+=9000+VAL[pr]
            if cap!=0:
                s+=500
        else:
            if abs(board[fr])==1 and (to>>3==7 or to>>3==0):
                s+=8000
        scored.append((s,fr,to,pr))
    scored.sort(key=lambda x:-x[0])
    return [(f,t,p) for _,f,t,p in scored]

def _quiesce(board,alpha,beta,ply,wtm,wk,bk,deadline,nodes):
    nodes[0]+=1
    if (nodes[0]&1023)==0 and time.time()>deadline[0]:
        raise _TO()
    kpos=wk[0] if wtm else bk[0]
    in_check=False
    if kpos!=-1:
        in_check=_is_attacked(board,kpos,not wtm)
    if not in_check:
        stand=_evaluate(board)*(1 if wtm else -1)
        if stand>=beta:
            return beta
        if stand>alpha:
            alpha=stand
        if ply>=6:
            return alpha
        pseudo=_gen_pseudo(board,wtm,True)
        if not pseudo:
            return alpha
    else:
        if ply>=6:
            stand=_evaluate(board)*(1 if wtm else -1)
            return stand
        pseudo=_gen_pseudo(board,wtm,False)
        if not pseudo:
            return -MATE+ply
    ordered=_order(board,pseudo)
    legal=0
    for fr,to,pr in ordered:
        moving=board[fr]; captured=board[to]
        board[fr]=0
        if pr:
            board[to]=pr if wtm else -pr
        else:
            board[to]=moving
        ow=wk[0]; ob=bk[0]
        if abs(moving)==6:
            if wtm:
                wk[0]=to
            else:
                bk[0]=to
        kp=wk[0] if wtm else bk[0]
        if kp!=-1 and _is_attacked(board,kp,not wtm):
            board[fr]=moving; board[to]=captured
            wk[0]=ow; bk[0]=ob
            continue
        legal+=1
        sc=-_quiesce(board,-beta,-alpha,ply+1,not wtm,wk,bk,deadline,nodes)
        board[fr]=moving; board[to]=captured
        wk[0]=ow; bk[0]=ob
        if sc>=beta:
            return beta
        if sc>alpha:
            alpha=sc
    if in_check and legal==0:
        return -MATE+ply
    return alpha

def _negamax(board,depth,alpha,beta,ply,wtm,wk,bk,deadline,nodes):
    nodes[0]+=1
    if (nodes[0]&1023)==0 and time.time()>deadline[0]:
        raise _TO()
    if depth<=0:
        return _quiesce(board,alpha,beta,ply,wtm,wk,bk,deadline,nodes)
    pseudo=_gen_pseudo(board,wtm,False)
    if not pseudo:
        kpos=wk[0] if wtm else bk[0]
        if kpos!=-1 and _is_attacked(board,kpos,not wtm):
            return -MATE+ply
        return 0
    ordered=_order(board,pseudo)
    legal=0
    best=-INF
    for fr,to,pr in ordered:
        moving=board[fr]; captured=board[to]
        board[fr]=0
        if pr:
            board[to]=pr if wtm else -pr
        else:
            board[to]=moving
        ow=wk[0]; ob=bk[0]
        if abs(moving)==6:
            if wtm:
                wk[0]=to
            else:
                bk[0]=to
        kp=wk[0] if wtm else bk[0]
        if kp!=-1 and _is_attacked(board,kp,not wtm):
            board[fr]=moving; board[to]=captured
            wk[0]=ow; bk[0]=ob
            continue
        legal+=1
        sc=-_negamax(board,depth-1,-beta,-alpha,ply+1,not wtm,wk,bk,deadline,nodes)
        board[fr]=moving; board[to]=captured
        wk[0]=ow; bk[0]=ob
        if sc>best:
            best=sc
        if sc>alpha:
            alpha=sc
        if alpha>=beta:
            break
    if legal==0:
        kpos=wk[0] if wtm else bk[0]
        if kpos!=-1 and _is_attacked(board,kpos,not wtm):
            return -MATE+ply
        return 0
    return best

def _make_root(board,wk,bk,uci,wtm):
    fr=_sq_to_idx(uci[0:2])
    to=_sq_to_idx(uci[2:4])
    pr=0
    if len(uci)>4:
        pr=PROMO_FROM.get(uci[4],0)
    moving=board[fr]
    if moving==0:
        return
    is_king=abs(moving)==6
    is_pawn=abs(moving)==1
    ffr=fr&7; fto=to&7
    captured=board[to]
    if is_king and abs(fto-ffr)==2:
        board[to]=moving; board[fr]=0
        if fto>ffr:
            rf=fr+3; rt=fr+1
        else:
            rf=fr-4; rt=fr-1
        if 0<=rf<64 and 0<=rt<64:
            board[rt]=board[rf]; board[rf]=0
        if wtm:
            wk[0]=to
        else:
            bk[0]=to
        return
    if is_pawn and captured==0 and ffr!=fto:
        ep=to-8 if wtm else to+8
        if 0<=ep<64:
            board[ep]=0
    board[fr]=0
    if pr:
        board[to]=pr if wtm else -pr
    else:
        board[to]=moving
    if is_king:
        if wtm:
            wk[0]=to
        else:
            bk[0]=to

def _board_from_pieces(pieces):
    board=[0]*64
    wk=-1; bk=-1
    mp={'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6}
    for sq,code in pieces.items():
        try:
            idx=_sq_to_idx(sq)
        except:
            continue
        if not code or len(code)<2:
            continue
        white=code[0]=='w' or code[0]=='W'
        t=mp.get(code[1].upper(),0)
        if t==0:
            continue
        v=t if white else -t
        board[idx]=v
        if t==6:
            if white:
                wk=idx
            else:
                bk=idx
    return board,wk,bk

def policy(pieces, to_play, legal_moves=None, *args, **kwargs):
    try:
        if args:
            for a in args:
                if isinstance(a,list) and a and isinstance(a[0],str):
                    legal_moves=a
                    break
        if isinstance(to_play,str):
            wtm = to_play.lower().startswith('w')
        else:
            wtm = bool(to_play)
        board,wk0,bk0=_board_from_pieces(pieces)
        start=time.time()
        deadline=[start+0.85]
        if legal_moves is not None and len(legal_moves)==0:
            legal_moves=None
        if legal_moves is not None:
            cands=list(legal_moves)
        else:
            pseudo=_gen_pseudo(board,wtm,False)
            legal=[]
            wk_t=[wk0]; bk_t=[bk0]
            for fr,to,pr in pseudo:
                moving=board[fr]; captured=board[to]
                board[fr]=0
                if pr:
                    board[to]=pr if wtm else -pr
                else:
                    board[to]=moving
                ow=wk_t[0]; ob=bk_t[0]
                if abs(moving)==6:
                    if wtm:
                        wk_t[0]=to
                    else:
                        bk_t[0]=to
                kp=wk_t[0] if wtm else bk_t[0]
                ok=True
                if kp!=-1 and _is_attacked(board,kp,not wtm):
                    ok=False
                board[fr]=moving; board[to]=captured
                wk_t[0]=ow; bk_t[0]=ob
                if ok:
                    legal.append(_uci(fr,to,pr))
            cands=legal
            if not cands:
                if legal_moves is not None and len(legal_moves)>0:
                    return legal_moves[0]
                return '0000'
        if len(cands)==1:
            return cands[0]
        def _root_score_key(u):
            try:
                fr=_sq_to_idx(u[0:2]); to=_sq_to_idx(u[2:4])
                cap=board[to]
                s=0
                if cap!=0:
                    av=VAL[cap if cap>0 else -cap]
                    mv=board[fr]
                    mvv=VAL[mv if mv>0 else -mv] if mv!=0 else 0
                    s+=10000+10*av-mvv
                if len(u)>4:
                    s+=9000
                if abs(board[fr])==6 and abs(to-fr)==2:
                    s+=500
                cf=to&7; cr=to>>3
                if 2<=cf<=5 and 2<=cr<=5:
                    s+=50
            except:
                s=0
            return -s
        ordered=sorted(cands,key=_root_score_key)
        best_move=ordered[0]
        nodes=[0]
        max_depth=10
        for depth in range(1,max_depth+1):
            if time.time()>deadline[0]-0.08:
                break
            alpha=-INF
            new_scores=[]
            cur_best=best_move
            cur_best_score=-INF
            try:
                for mv in ordered:
                    bc=board[:]
                    wkc=[wk0]; bkc=[bk0]
                    _make_root(bc,wkc,bkc,mv,wtm)
                    sc=-_negamax(bc,depth-1,-INF,-alpha,1,not wtm,wkc,bkc,deadline,nodes)
                    new_scores.append((sc,mv))
                    if sc>cur_best_score:
                        cur_best_score=sc
                        cur_best=mv
                    if sc>alpha:
                        alpha=sc
                    if time.time()>deadline[0]-0.02:
                        raise _TO()
                new_scores.sort(key=lambda x:-x[0])
                ordered=[m for _,m in new_scores]
                best_move=cur_best
                if cur_best_score>=MATE-1000:
                    break
                if depth>=4 and time.time()-start>0.6:
                    pass
            except _TO:
                break
            except Exception:
                break
        if best_move not in cands:
            best_move=cands[0]
        return best_move
    except Exception:
        try:
            if legal_moves is not None and len(legal_moves)>0:
                return legal_moves[0]
            if isinstance(pieces,dict) and len(pieces)>0:
                mp={'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6}
                board2=[0]*64
                for sq,code in pieces.items():
                    try:
                        idx=_sq_to_idx(sq)
                        white=code[0]=='w'
                        t=mp.get(code[1].upper(),0)
                        board2[idx]=t if white else -t
                    except:
                        pass
                wtm2=to_play.lower().startswith('w') if isinstance(to_play,str) else True
                pm=_gen_pseudo(board2,wtm2,False)
                for fr,to,pr in pm:
                    moving=board2[fr]; captured=board2[to]
                    board2[fr]=0
                    if pr:
                        board2[to]=pr if wtm2 else -pr
                    else:
                        board2[to]=moving
                    kp=-1
                    for i,v in enumerate(board2):
                        if v==(6 if wtm2 else -6):
                            kp=i
                            break
                    ok=True
                    if kp!=-1 and _is_attacked(board2,kp,not wtm2):
                        ok=False
                    board2[fr]=moving; board2[to]=captured
                    if ok:
                        return _uci(fr,to,pr)
        except:
            pass
        return 'e2e4'
