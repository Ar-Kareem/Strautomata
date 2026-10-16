
import time
import random

VALS = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':0}

P_PST = [0,0,0,0,0,0,0,0,50,50,50,50,50,50,50,50,10,10,20,30,30,20,10,10,5,5,10,25,25,10,5,5,0,0,0,20,20,0,0,0,5,-5,-10,0,0,-10,-5,5,5,10,10,-20,-20,10,10,5,0,0,0,0,0,0,0,0]
N_PST = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
B_PST = [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20]
R_PST = [0,0,0,0,0,0,0,0,5,10,10,10,10,10,10,5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,0,0,0,5,5,0,0,0]
Q_PST = [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20]
K_MID = [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20]
K_END = [-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,20,30,30,20,-10,-30,-30,-30,0,0,0,0,-30,-30,-50,-30,-30,-30,-30,-30,-30,-50]
PSTS = {'P':P_PST,'N':N_PST,'B':B_PST,'R':R_PST,'Q':Q_PST}

KN_OFF = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
K_OFF = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
DIAG = [(1,1),(1,-1),(-1,1),(-1,-1)]
STRA = [(1,0),(-1,0),(0,1),(0,-1)]

MATE = 100000
INF = 10**9

def _sq_to_idx(sq):
    return (ord(sq[0])-97) + (int(sq[1])-1)*8
def _idx_to_sq(i):
    return chr((i%8)+97)+str((i//8)+1)
def _uci(fr,to,promo):
    s=_idx_to_sq(fr)+_idx_to_sq(to)
    if promo:
        s+=promo
    return s

def _parse(pieces):
    b=[None]*64
    wk=None; bk=None
    for sq,pc in pieces.items():
        try:
            f=ord(sq[0])-97; r=int(sq[1])-1
            if not (0<=f<8 and 0<=r<8): continue
            i=r*8+f
            b[i]=pc
            if pc=='wK': wk=i
            elif pc=='bK': bk=i
        except: continue
    return b,wk,bk

def _attacked(b, sq, by_w):
    f=sq%8; r=sq//8
    # pawns
    if by_w:
        pr=r-1
        if pr>=0:
            if f>0 and b[pr*8+f-1]=='wP': return True
            if f<7 and b[pr*8+f+1]=='wP': return True
    else:
        pr=r+1
        if pr<8:
            if f>0 and b[pr*8+f-1]=='bP': return True
            if f<7 and b[pr*8+f+1]=='bP': return True
    # knights
    for df,dr in KN_OFF:
        nf=f+df; nr=r+dr
        if 0<=nf<8 and 0<=nr<8:
            p=b[nr*8+nf]
            if p is not None and ((p=='wN' and by_w) or (p=='bN' and not by_w)):
                return True
    # king
    for df,dr in K_OFF:
        nf=f+df; nr=r+dr
        if 0<=nf<8 and 0<=nr<8:
            p=b[nr*8+nf]
            if p is not None and ((p=='wK' and by_w) or (p=='bK' and not by_w)):
                return True
    # sliders diag
    for df,dr in DIAG:
        nf=f+df; nr=r+dr
        while 0<=nf<8 and 0<=nr<8:
            p=b[nr*8+nf]
            if p is not None:
                if by_w:
                    if p=='wB' or p=='wQ': return True
                else:
                    if p=='bB' or p=='bQ': return True
                break
            nf+=df; nr+=dr
    for df,dr in STRA:
        nf=f+df; nr=r+dr
        while 0<=nf<8 and 0<=nr<8:
            p=b[nr*8+nf]
            if p is not None:
                if by_w:
                    if p=='wR' or p=='wQ': return True
                else:
                    if p=='bR' or p=='bQ': return True
                break
            nf+=df; nr+=dr
    return False

def _in_check(b, wk, bk, white_to_move):
    if white_to_move:
        if wk is None: return False
        return _attacked(b, wk, False)
    else:
        if bk is None: return False
        return _attacked(b, bk, True)

def _gen_pseudo(b, white_to_move):
    moves=[]
    for i,p in enumerate(b):
        if p is None: continue
        is_w = p[0]=='w'
        if is_w != white_to_move: continue
        t=p[1]
        f=i%8; r=i//8
        if t=='P':
            d=1 if is_w else -1
            start=1 if is_w else 6
            promo_rank=7 if is_w else 0
            nr=r+d
            if 0<=nr<8:
                ni=nr*8+f
                if b[ni] is None:
                    if nr==promo_rank:
                        for pr in ('q','r','b','n'):
                            moves.append((i,ni,pr))
                    else:
                        moves.append((i,ni,None))
                        if r==start:
                            nr2=r+2*d
                            ni2=nr2*8+f
                            if b[ni2] is None:
                                moves.append((i,ni2,None))
                for df in (-1,1):
                    nf=f+df
                    if 0<=nf<8:
                        ci=nr*8+nf
                        cp=b[ci]
                        if cp is not None and (cp[0]!=p[0]) and cp[1]!='K':
                            if nr==promo_rank:
                                for pr in ('q','r','b','n'):
                                    moves.append((i,ci,pr))
                            else:
                                moves.append((i,ci,None))
        elif t=='N':
            for df,dr in KN_OFF:
                nf=f+df; nr=r+dr
                if 0<=nf<8 and 0<=nr<8:
                    ci=nr*8+nf
                    cp=b[ci]
                    if cp is None or (cp[0]!=p[0] and cp[1]!='K'):
                        moves.append((i,ci,None))
        elif t=='B' or t=='R' or t=='Q':
            dirs=[]
            if t=='B' or t=='Q': dirs+=DIAG
            if t=='R' or t=='Q': dirs+=STRA
            for df,dr in dirs:
                nf=f+df; nr=r+dr
                while 0<=nf<8 and 0<=nr<8:
                    ci=nr*8+nf
                    cp=b[ci]
                    if cp is None:
                        moves.append((i,ci,None))
                    else:
                        if cp[0]!=p[0] and cp[1]!='K':
                            moves.append((i,ci,None))
                        break
                    nf+=df; nr+=dr
        elif t=='K':
            for df,dr in K_OFF:
                nf=f+df; nr=r+dr
                if 0<=nf<8 and 0<=nr<8:
                    ci=nr*8+nf
                    cp=b[ci]
                    if cp is None or (cp[0]!=p[0] and cp[1]!='K'):
                        moves.append((i,ci,None))
    return moves

def _do_move(b, wk, bk, mv):
    fr,to,promo = mv
    pc=b[fr]
    cap=b[to]
    # en passant detection: pawn diagonal to empty
    ep_cap=-1; ep_pc=None
    is_w = pc[0]=='w' if pc else True
    if pc is not None and pc[1]=='P' and cap is None and (fr%8)!=(to%8):
        # diagonal to empty -> en passant capture
        cap_sq = (to//8 - (1 if is_w else -1))*8 + (to%8)
        if 0<=cap_sq<64:
            epp=b[cap_sq]
            if epp is not None and epp[1]=='P' and epp[0]!=pc[0]:
                ep_cap=cap_sq; ep_pc=epp
                b[cap_sq]=None
    # castling detection: king moves 2
    cast_rook_from=-1; cast_rook_to=-1; cast_pc=None
    if pc is not None and pc[1]=='K' and abs((to%8)-(fr%8))==2:
        r=fr//8
        if to%8==6:
            cast_rook_from=r*8+7; cast_rook_to=r*8+5
        else:
            cast_rook_from=r*8+0; cast_rook_to=r*8+3
        cast_pc=b[cast_rook_from]
        b[cast_rook_to]=cast_pc
        b[cast_rook_from]=None
    b[to]=pc
    b[fr]=None
    if promo is not None and pc is not None and pc[1]=='P':
        b[to]=pc[0]+promo.upper()
    nwk=wk; nbk=bk
    if pc=='wK': nwk=to
    elif pc=='bK': nbk=to
    undo=(cap,ep_cap,ep_pc,cast_rook_from,cast_rook_to,cast_pc,pc)
    return nwk,nbk,undo

def _undo_move(b, wk, bk, mv, undo):
    fr,to,promo = mv
    cap,ep_cap,ep_pc,crf,crt,crpc,pc = undo
    b[fr]=pc
    b[to]=cap
    if ep_cap!=-1:
        b[ep_cap]=ep_pc
    if crf!=-1:
        b[crf]=crpc
        b[crt]=None
    return wk if pc!='wK' else fr, bk if pc!='bK' else fr

def _gen_legal(b, wk, bk, white_to_move):
    pseud=_gen_pseudo(b, white_to_move)
    legal=[]
    for mv in pseud:
        fr,to,promo=mv
        nwk,nbk,undo=_do_move(b,wk,bk,mv)
        ok=True
        if white_to_move:
            if nwk is not None and _attacked(b,nwk,False):
                ok=False
        else:
            if nbk is not None and _attacked(b,nbk,True):
                ok=False
        wkr,bkr=_undo_move(b,nwk,nbk,mv,undo)
        # restore wk,bk implicitly via caller vars (b restored)
        if ok:
            legal.append(mv)
    return legal

def _evaluate(b):
    # white perspective
    score=0
    mat_nopawn=0
    hasQ=False
    for i,p in enumerate(b):
        if p is None: continue
        c=p[0]; t=p[1]
        f=i%8; r=i//8
        v=VALS[t]
        if t!='P' and t!='K':
            mat_nopawn+=v
        if t=='Q':
            hasQ=True
        if t=='P' or t=='N' or t=='B' or t=='R' or t=='Q':
            tbl=PSTS[t]
            # tbl is a8-first: idx=(7-r)*8+f
            ti=(7-r)*8+f
            pv=tbl[ti]
            if c=='w':
                score+=v+pv
            else:
                # mirror: r*8+f
                mi=r*8+f
                score-=v+tbl[mi]
        elif t=='K':
            pass
    # king pst with phase
    endgame = (not hasQ) or (mat_nopawn<1300)
    KT = K_END if endgame else K_MID
    for i,p in enumerate(b):
        if p is None or p[1]!='K': continue
        f=i%8; r=i//8
        if p[0]=='w':
            score+=KT[(7-r)*8+f]
        else:
            score-=KT[r*8+f]
    return score

class _Searcher:
    def __init__(self, deadline):
        self.deadline=deadline
        self.nodes=0
        self.timed_out=False
    def check(self):
        self.nodes+=1
        if self.nodes & 1023 ==0:
            if time.perf_counter()>self.deadline:
                self.timed_out=True
                raise TimeoutError()

def _order(moves, b):
    scored=[]
    for mv in moves:
        fr,to,promo=mv
        tgt=b[to]
        s=0
        if tgt is not None:
            vv=VALS.get(tgt[1],0)
            av=VALS.get(b[fr][1],0) if b[fr] else 0
            s=10000+vv*10-av
        if promo:
            if promo=='q': s+=9000
            elif promo=='r': s+=5000
            elif promo=='b': s+=3000
            else: s+=3000
            # promotion captures already high
            if tgt is not None: s+=5000
        # central moves slight bonus? keep 0
        scored.append((s,mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _,m in scored]

def policy(pieces, to_play, legal_moves=None):
    try:
        t0=time.perf_counter()
        deadline=t0+0.88
        white = (to_play=='white' or to_play=='w' or to_play=='W')
        b,wk,bk=_parse(pieces if isinstance(pieces,dict) else {})
        # gather root moves
        use_external = isinstance(legal_moves,(list,tuple)) and len(legal_moves)>0
        ext_list=None
        if use_external:
            ext_list=list(legal_moves)
        else:
            # also check kwargs style? ignore
            pass
        own_legal=_gen_legal(b,wk,bk,white)
        own_uci={_uci(fr,to,pr):(fr,to,pr) for fr,to,pr in own_legal}
        root_moves=[]
        root_uci=[]
        if ext_list is not None:
            # build internal moves for each external uci, handling castling/ep
            for u in ext_list:
                try:
                    if not isinstance(u,str) or len(u)<4: continue
                    fr=_sq_to_idx(u[0:2]); to=_sq_to_idx(u[2:4])
                    pr=u[4].lower() if len(u)>4 else None
                    if pr not in (None,'q','r','b','n'):
                        pr=None
                    # validate piece ownership loosely
                    root_moves.append((fr,to,pr))
                    root_uci.append(u[:4]+(pr if pr else ''))
                except: continue
            if not root_moves:
                # fallback to own
                root_moves=own_legal
                root_uci=[_uci(*m) if len(m)==3 else _uci(m[0],m[1],m[2]) for m in root_moves]
                # fix uci strings
                root_uci=[_uci(fr,to,pr) for fr,to,pr in root_moves]
            else:
                # normalize uci strings to lowercase promo
                tmp=[]
                for u in root_uci:
                    tmp.append(u.lower())
                root_uci=tmp
        else:
            root_moves=own_legal
            root_uci=[_uci(fr,to,pr) for fr,to,pr in root_moves]
        if not root_moves:
            # no moves: return something (should not happen)
            # try any pseudo
            return "a2a3"
        if len(root_moves)==1:
            return root_uci[0]
        # immediate mate in 1?
        # order root by captures/promotions first for mate check speed
        # quick mate search
        ordered_idx=sorted(range(len(root_moves)), key=lambda k: (root_moves[k][2] is not None, b[root_moves[k][1]] is not None), reverse=True)
        # use searcher
        S=_Searcher(deadline)
        # helper closures
        def quies(b_,wk_,bk_,alpha,beta,wtm,ply):
            S.check()
            if ply>6:
                ev=_evaluate(b_)
                return ev if wtm else -ev
            # stand pat
            ev=_evaluate(b_)
            sc=ev if wtm else -ev
            if sc>=beta: return beta
            if sc>alpha: alpha=sc
            # generate captures/promotions only
            pseud=_gen_pseudo(b_,wtm)
            caps=[m for m in pseud if (b_[m[1]] is not None or m[2] is not None)]
            caps=_order(caps,b_)
            for mv in caps:
                nwk,nbk,undo=_do_move(b_,wk_,bk_,mv)
                # legality
                ill=False
                if wtm:
                    if nwk is not None and _attacked(b_,nwk,False): ill=True
                else:
                    if nbk is not None and _attacked(b_,nbk,True): ill=True
                if ill:
                    _undo_move(b_,nwk,nbk,mv,undo)
                    continue
                val=-quies(b_,nwk,nbk,-beta,-alpha,not wtm,ply+1)
                _undo_move(b_,nwk,nbk,mv,undo)
                if S.timed_out: raise TimeoutError()
                if val>=beta: return beta
                if val>alpha: alpha=val
            return alpha
        def negamax(b_,wk_,bk_,depth,alpha,beta,wtm,ply):
            S.check()
            in_chk=_in_check(b_,wk_,bk_,wtm)
            if depth<=0:
                return quies(b_,wk_,bk_,alpha,beta,wtm,ply)
            legal=_gen_legal(b_,wk_,bk_,wtm)
            if not legal:
                if in_chk:
                    return -MATE+ply
                else:
                    return 0
            legal=_order(legal,b_)
            best=-INF
            for mv in legal:
                nwk,nbk,undo=_do_move(b_,wk_,bk_,mv)
                val=-negamax(b_,nwk,nbk,depth-1,-beta,-alpha,not wtm,ply+1)
                _undo_move(b_,nwk,nbk,mv,undo)
                if S.timed_out: raise TimeoutError()
                if val>best: best=val
                if val>alpha: alpha=val
                if alpha>=beta: break
            return best
        # iterative deepening at root
        # initial ordering: captures first
        order=[ordered_idx[i] for i in range(len(ordered_idx))]
        best_idx=order[0]
        # try depth 1..4/5
        max_depth=4
        # adjust by branching
        if len(root_moves)<12: max_depth=5
        if len(root_moves)>35: max_depth=3
        try:
            for depth in range(1,max_depth+1):
                alpha=-INF; beta=INF
                scores={}
                # move ordering from previous iteration (best first)
                # order list already best-first after first iter
                cur_best=None; cur_best_score=-INF
                a= -INF
                for k in order:
                    mv=root_moves[k]
                    nwk,nbk,undo=_do_move(b,wk,bk,mv)
                    # check illegal (for external castling moves, need legality check)
                    ill=False
                    if white:
                        if nwk is not None and _attacked(b,nwk,False): ill=True
                    else:
                        if nbk is not None and _attacked(b,nbk,True): ill=True
                    if ill:
                        _undo_move(b,nwk,nbk,mv,undo)
                        scores[k]=-INF+1
                        continue
                    # if immediate mate, return instantly
                    # quick check: opponent has no moves and in check
                    opp_legal=_gen_legal(b,nwk,nbk,not white)
                    if not opp_legal:
                        opp_in=_in_check(b,nwk,nbk,not white)
                        _undo_move(b,nwk,nbk,mv,undo)
                        if opp_in:
                            return root_uci[k]
                        else:
                            scores[k]=0
                            if 0>cur_best_score:
                                cur_best_score=0; cur_best=k
                            # update alpha for root? continue searching for mate
                            continue
                    val=-negamax(b,nwk,nbk,depth-1,-beta,-a,not white,1)
                    _undo_move(b,nwk,nbk,mv,undo)
                    scores[k]=val
                    if val>cur_best_score:
                        cur_best_score=val; cur_best=k
                    if val>a: a=val
                    if S.timed_out: raise TimeoutError()
                    if time.perf_counter()>deadline-0.05:
                        raise TimeoutError()
                if cur_best is not None:
                    best_idx=cur_best
                    # reorder for next depth
                    order=sorted(order,key=lambda k: scores.get(k,-INF),reverse=True)
                if time.perf_counter()>deadline-0.08:
                    break
                # if mate found, break
                if cur_best_score>MATE-1000:
                    break
        except TimeoutError:
            pass
        return root_uci[best_idx]
    except Exception:
        try:
            # fallback: return first legalish
            white2=(to_play=='white' or to_play=='w')
            if isinstance(legal_moves,(list,tuple)) and len(legal_moves)>0:
                return str(legal_moves[0])
            b2,wk2,bk2=_parse(pieces)
            m2=_gen_pseudo(b2,white2)
            # filter king safety quickly
            for mv in m2:
                fr,to,pr=mv
                # basic ownership already
                tgt=b2[to]
                if tgt is not None and tgt[1]=='K': continue
                nwk,nbk,undo=_do_move(b2,wk2,bk2,mv)
                ok=True
                if white2:
                    if nwk is not None and _attacked(b2,nwk,False): ok=False
                else:
                    if nbk is not None and _attacked(b2,nbk,True): ok=False
                _undo_move(b2,nwk,nbk,mv,undo)
                if ok:
                    return _uci(fr,to,pr)
            # last resort
            if m2:
                return _uci(*m2[0])
        except Exception:
            pass
        return "e2e3"
