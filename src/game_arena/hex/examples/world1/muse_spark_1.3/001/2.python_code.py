
from collections import deque
import time

N = 11
N2 = 121

_NEIGH = [[] for _ in range(N2)]
for _r in range(N):
    for _c in range(N):
        _i = _r * N + _c
        for _dr, _dc in ((0,-1),(0,1),(-1,0),(1,0),(-1,1),(1,-1)):
            _nr, _nc = _r+_dr, _c+_dc
            if 0 <= _nr < N and 0 <= _nc < N:
                _NEIGH[_i].append(_nr*N+_nc)

_START_B = [0*N+c for c in range(N)]
_TMASK_B = [False]*N2
for c in range(N):
    _TMASK_B[10*N+c]=True
_START_W = [r*N+0 for r in range(N)]
_TMASK_W = [False]*N2
for r in range(N):
    _TMASK_W[r*N+10]=True

_INF = 1000

def _dist(board, own, blocked, starts, tmask):
    dist = [_INF]*N2
    dq = deque()
    for s in starts:
        v = board[s]
        if v == blocked:
            continue
        c = 0 if v == own else 1
        if c < dist[s]:
            dist[s]=c
            if c==0:
                dq.appendleft(s)
            else:
                dq.append(s)
    if not dq:
        return _INF
    neigh = _NEIGH
    while dq:
        u = dq.popleft()
        du = dist[u]
        if tmask[u]:
            return du
        for w in neigh[u]:
            bw = board[w]
            if bw == blocked:
                continue
            cw = 0 if bw == own else 1
            nd = du + cw
            if nd < dist[w]:
                dist[w]=nd
                if cw==0:
                    dq.appendleft(w)
                else:
                    dq.append(w)
    return _INF

def _has_won(board, own, starts, tmask):
    seen = [False]*N2
    stack = []
    for s in starts:
        if board[s]==own and not seen[s]:
            seen[s]=True
            stack.append(s)
    neigh = _NEIGH
    while stack:
        u = stack.pop()
        if tmask[u]:
            return True
        for w in neigh[u]:
            if not seen[w] and board[w]==own:
                seen[w]=True
                stack.append(w)
    return False

def policy(me, opp, color):
    try:
        t0 = time.time()
        board = [0]*N2
        for r,c in me:
            if 0<=r<N and 0<=c<N:
                board[r*N+c]=1
        for r,c in opp:
            if 0<=r<N and 0<=c<N:
                board[r*N+c]=2
        empties = [i for i,v in enumerate(board) if v==0]
        if not empties:
            return (0,0)
        if len(empties)==N2:
            return (5,5)
        # color
        me_is_black = True
        try:
            if isinstance(color,str):
                me_is_black = color.lower().startswith('b')
            else:
                me_is_black = (color=='b')
        except:
            me_is_black = True
        if me_is_black:
            me_starts=_START_B; me_tmask=_TMASK_B
            opp_starts=_START_W; opp_tmask=_TMASK_W
        else:
            me_starts=_START_W; me_tmask=_TMASK_W
            opp_starts=_START_B; opp_tmask=_TMASK_B

        # quick center if very early and center free
        if len(empties)>=119:
            cen = 5*N+5
            if board[cen]==0:
                # if opp took center, play adjacent
                return (5,5)
            else:
                # play neighbour of center
                for cand in [5*N+4,4*N+5,6*N+5,5*N+6]:
                    if board[cand]==0:
                        return (cand//N, cand%N)

        cur_me = _dist(board,1,2,me_starts,me_tmask)
        cur_opp = _dist(board,2,1,opp_starts,opp_tmask)
        if cur_me==0 or cur_opp==0:
            # game already decided, play best empty by heuristic below, fallback
            pass

        # immediate win / block using exact flood fill, only if distance 1
        if cur_me==1:
            for e in empties:
                board[e]=1
                if _has_won(board,1,me_starts,me_tmask):
                    board[e]=0
                    return (e//N, e%N)
                board[e]=0
        if cur_opp==1:
            first_block = None
            # find all opp winning cells, if one block it
            for e in empties:
                board[e]=2
                if _has_won(board,2,opp_starts,opp_tmask):
                    board[e]=0
                    if first_block is None:
                        first_block=e
                        # check if there are two distinct wins -> still need to block one
                        # continue to count
                    else:
                        # double threat: we cannot block both, fall through to heuristic
                        # but remember first
                        pass
                    # don't return yet, need count; store
                else:
                    board[e]=0
            # recount correctly: need to reset board correctly above
            # board already reset in both branches? in win branch we did reset, ok
            if first_block is not None:
                # count wins
                cnt=0
                for e in empties:
                    board[e]=2
                    w=_has_won(board,2,opp_starts,opp_tmask)
                    board[e]=0
                    if w:
                        cnt+=1
                        if cnt>1:
                            break
                if cnt==1:
                    return (first_block//N, first_block%N)
                else:
                    # multiple threats, block first as fallback but try heuristic search below
                    # if heuristic fails we will block first
                    pass

        # 1-ply evaluation
        raw = {}
        epsd = {}
        scored = {}
        neigh = _NEIGH
        for e in empties:
            if time.time()-t0>0.55:
                break
            board[e]=1
            md = _dist(board,1,2,me_starts,me_tmask)
            if md==0:
                board[e]=0
                return (e//N, e%N)
            od = _dist(board,2,1,opp_starts,opp_tmask)
            board[e]=0
            if od>=_INF:
                od=100
            if md>=_INF:
                md=100
            r = e//N; c = e%N
            dc = abs(r-5)+abs(c-5)
            eps = (10-dc)*0.02
            # adjacency bonus
            oc=0
            for w in neigh[e]:
                if board[w]==1:
                    oc+=1
            eps += oc*0.015
            # slight edge penalty for corners? keep central
            s = (od-md)+eps
            raw[e]=od-md
            epsd[e]=eps
            scored[e]=s

        # if timed out early, fill missing with low score
        order = sorted([e for e in scored], key=lambda x: scored[x], reverse=True)
        if not order:
            e=empties[0]
            return (e//N, e%N)
        # add any unevaluated empties at end
        if len(order)<len(empties):
            missing=[e for e in empties if e not in scored]
            order.extend(missing)
            for e in missing:
                raw[e]=-100
                epsd[e]=0
                scored[e]=-100

        n=len(empties)
        if n>70:
            K1,K2=6,6
        elif n>40:
            K1,K2=8,8
        elif n>20:
            K1,K2=10,10
        else:
            K1=min(n,12); K2=min(n,12)

        K1=min(K1,len(order))
        top1=order[:K1]

        best_move=top1[0]
        best_val=-10000

        # 2-ply alpha-beta
        for m in top1:
            if time.time()-t0>0.88:
                break
            # opp candidates: best by 1-ply excluding m
            opp_cands=[]
            for x in order:
                if x!=m:
                    opp_cands.append(x)
                    if len(opp_cands)>=K2:
                        break
            board[m]=1
            worst=10000
            # if no opp cands (last move), evaluate directly
            if not opp_cands:
                md=_dist(board,1,2,me_starts,me_tmask)
                od=_dist(board,2,1,opp_starts,opp_tmask)
                if od>=_INF: od=100
                if md>=_INF: md=100
                worst=od-md
            else:
                for o in opp_cands:
                    board[o]=2
                    md=_dist(board,1,2,me_starts,me_tmask)
                    if md>=_INF:
                        worst=-100
                        board[o]=0
                        break
                    od=_dist(board,2,1,opp_starts,opp_tmask)
                    board[o]=0
                    if od>=_INF: od=100
                    if md>=_INF: md=100
                    val=od-md
                    if val<worst:
                        worst=val
                    if worst<=best_val:
                        break
                    if time.time()-t0>0.90:
                        break
            board[m]=0
            # tie break with 1-ply score
            if worst>best_val or (worst==best_val and scored.get(m,-999)>scored.get(best_move,-999)):
                best_val=worst
                best_move=m

        return (best_move//N, best_move%N)
    except Exception:
        try:
            occ=set(me)|set(opp)
            for r in range(11):
                for c in range(11):
                    if (r,c) not in occ:
                        return (r,c)
        except:
            pass
        return (5,5)
