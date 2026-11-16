
import numpy as np
import time
from functools import lru_cache

BOX_MASKS = []
EDGE_TO_BOXES = [[] for _ in range(40)]
BIT_TO_MOVE = [None]*40
for _br in range(4):
    for _bc in range(4):
        _top = _br*4+_bc
        _bottom = (_br+1)*4+_bc
        _left = 20+_br*5+_bc
        _right = 20+_br*5+_bc+1
        _mask = (1<<_top)|(1<<_bottom)|(1<<_left)|(1<<_right)
        BOX_MASKS.append(_mask)
        for _b in (_top,_bottom,_left,_right):
            EDGE_TO_BOXES[_b].append(_br*4+_bc)
for _bit in range(20):
    _r = _bit//4
    _c = _bit%4
    BIT_TO_MOVE[_bit]=(_r,_c,'H')
for _bit in range(20,40):
    _vi = _bit-20
    _r = _vi//5
    _c = _vi%5
    BIT_TO_MOVE[_bit]=(_r,_c,'V')
FULL_MASK = (1<<40)-1

def _first_legal_fallback(horizontal, vertical):
    try:
        h = horizontal
        v = vertical
        for r in range(5):
            for c in range(4):
                if r< h.shape[0] and c < h.shape[1] and h[r,c]==0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if r< v.shape[0] and c < v.shape[1] and v[r,c]==0:
                    return f"{r},{c},V"
        for r in range(5):
            for c in range(5):
                if h[r,c]==0:
                    return f"{r},{c},H"
                if v[r,c]==0:
                    return f"{r},{c},V"
    except Exception:
        pass
    return "0,0,H"

def _adj_boxes(r,c,d):
    boxes=[]
    if d=='H':
        if r>0 and r-1<4 and c<4 and c>=0:
            if 0<=r-1<4 and 0<=c<4:
                boxes.append((r-1,c))
        if r<4 and c<4 and r>=0 and c>=0:
            if 0<=r<4 and 0<=c<4:
                boxes.append((r,c))
    else:
        if c>0 and r<4 and r>=0:
            if 0<=r<4 and 0<=c-1<4:
                boxes.append((r,c-1))
        if c<4 and r<4 and r>=0 and c>=0:
            if 0<=r<4 and 0<=c<4:
                boxes.append((r,c))
    return boxes

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        h = horizontal
        v = vertical
        cap = capture
        # legal moves restricted to real geometry
        legal=[]
        for r in range(5):
            for c in range(4):
                try:
                    if h[r,c]==0:
                        legal.append((r,c,'H'))
                except Exception:
                    continue
        for r in range(4):
            for c in range(5):
                try:
                    if v[r,c]==0:
                        legal.append((r,c,'V'))
                except Exception:
                    continue
        if len(legal)==0:
            return _first_legal_fallback(h,v)

        # sides per box 4x4
        sides = np.zeros((4,4), dtype=int)
        for br in range(4):
            for bc in range(4):
                s=0
                if h[br,bc]!=0: s+=1
                if h[br+1,bc]!=0: s+=1
                if v[br,bc]!=0: s+=1
                if v[br,bc+1]!=0: s+=1
                sides[br,bc]=s

        # capture moves
        cap_moves=[]
        cap_k={}
        for m in legal:
            r,c,d=m
            boxes=_adj_boxes(r,c,d)
            k=0
            for (br,bc) in boxes:
                if sides[br,bc]==3:
                    k+=1
            if k>0:
                cap_moves.append(m)
                cap_k[m]=k

        remaining=len(legal)
        SEARCH_LIMIT=16

        # ---- exact search helper ----
        def run_exact():
            # build occ and empty bits
            occ=0
            empty_bits=[]
            for r in range(5):
                for c in range(4):
                    bit=r*4+c
                    if h[r,c]!=0:
                        occ|=(1<<bit)
                    else:
                        empty_bits.append(bit)
            for r in range(4):
                for c in range(5):
                    bit=20+r*5+c
                    if v[r,c]!=0:
                        occ|=(1<<bit)
                    else:
                        empty_bits.append(bit)
            empty_t=tuple(empty_bits)
            start_t=time.time()
            counter=[0]
            @lru_cache(maxsize=None)
            def F(state, turn):
                counter[0]+=1
                if (counter[0]&1023)==0:
                    if time.time()-start_t>0.85:
                        raise TimeoutError()
                if state==FULL_MASK:
                    return 0
                # quick check if no moves
                has=False
                for b in empty_t:
                    if ((state>>b)&1)==0:
                        has=True
                        break
                if not has:
                    return 0
                if turn==0:
                    best=-1000
                    for b in empty_t:
                        if ((state>>b)&1)!=0:
                            continue
                        nstate=state|(1<<b)
                        k=0
                        for bx in EDGE_TO_BOXES[b]:
                            bm=BOX_MASKS[bx]
                            if (nstate & bm)==bm and (state & bm)!=bm:
                                k+=1
                                if k>=2:
                                    break
                        if k>0:
                            val=k+F(nstate,turn)
                        else:
                            val=F(nstate,1-turn)
                        if val>best:
                            best=val
                    return best
                else:
                    best=1000
                    for b in empty_t:
                        if ((state>>b)&1)!=0:
                            continue
                        nstate=state|(1<<b)
                        k=0
                        for bx in EDGE_TO_BOXES[b]:
                            bm=BOX_MASKS[bx]
                            if (nstate & bm)==bm and (state & bm)!=bm:
                                k+=1
                                if k>=2:
                                    break
                        if k>0:
                            val=-k+F(nstate,turn)
                        else:
                            val=F(nstate,1-turn)
                        if val<best:
                            best=val
                    return best
            # root choice
            best_val=-10000
            best_bit=empty_t[0]
            for b in empty_t:
                nstate=occ|(1<<b)
                k=0
                for bx in EDGE_TO_BOXES[b]:
                    bm=BOX_MASKS[bx]
                    if (nstate & bm)==bm and (occ & bm)!=bm:
                        k+=1
                        if k>=2:
                            break
                if k>0:
                    val=k+F(nstate,0)
                else:
                    val=F(nstate,1)
                if val>best_val:
                    best_val=val
                    best_bit=b
            rr,cc,dd=BIT_TO_MOVE[best_bit]
            return f"{rr},{cc},{dd}"

        if len(cap_moves)>0:
            if remaining<=SEARCH_LIMIT:
                try:
                    return run_exact()
                except Exception:
                    pass
            # heuristic: prefer double capture
            cap_moves_sorted=sorted(cap_moves, key=lambda m: -cap_k[m])
            return f"{cap_moves_sorted[0][0]},{cap_moves_sorted[0][1]},{cap_moves_sorted[0][2]}"

        # no captures: find safe moves
        safe=[]
        for m in legal:
            r,c,d=m
            boxes=_adj_boxes(r,c,d)
            ok=True
            for (br,bc) in boxes:
                if sides[br,bc]>=2:
                    ok=False
                    break
            if ok:
                safe.append(m)

        if len(safe)>0:
            if remaining<=SEARCH_LIMIT:
                try:
                    return run_exact()
                except Exception:
                    pass
            # heuristic scoring for safe
            twos_pos=[(br,bc) for br in range(4) for bc in range(4) if sides[br,bc]==2]
            best=None
            best_key=None
            for m in safe:
                r,c,d=m
                boxes=_adj_boxes(r,c,d)
                num_twos=0
                tot=0
                for (br,bc) in boxes:
                    s=sides[br,bc]
                    if s==1:
                        num_twos+=1
                    tot+=s+1
                # distance to nearest 2-sided box (larger is better)
                if len(twos_pos)==0 or len(boxes)==0:
                    mind=100
                else:
                    mind=100
                    for (br,bc) in boxes:
                        for (tr,tc) in twos_pos:
                            dd2=abs(br-tr)+abs(bc-tc)
                            if dd2<mind:
                                mind=dd2
                key=(num_twos, -mind, tot, r, c, d)
                if best_key is None or key<best_key:
                    best_key=key
                    best=m
            return f"{best[0]},{best[1]},{best[2]}"
        else:
            # loony: must sacrifice
            if remaining<=SEARCH_LIMIT:
                try:
                    return run_exact()
                except Exception:
                    pass
            # minimal chain sacrifice via greedy simulation
            def greedy_take(rm,cm,dm):
                h2=h.copy()
                v2=v.copy()
                if dm=='H':
                    h2[rm,cm]=1
                else:
                    v2[rm,cm]=1
                take=0
                # loop until no 3-sided
                for _ in range(40):
                    # compute sides
                    found=None
                    for br in range(4):
                        for bc in range(4):
                            s2=(1 if h2[br,bc]!=0 else 0)+(1 if h2[br+1,bc]!=0 else 0)+(1 if v2[br,bc]!=0 else 0)+(1 if v2[br,bc+1]!=0 else 0)
                            if s2==3:
                                found=(br,bc)
                                break
                        if found is not None:
                            break
                    if found is None:
                        break
                    br,bc=found
                    if h2[br,bc]==0:
                        h2[br,bc]=-1
                    elif h2[br+1,bc]==0:
                        h2[br+1,bc]=-1
                    elif v2[br,bc]==0:
                        v2[br,bc]=-1
                    elif v2[br,bc+1]==0:
                        v2[br,bc+1]=-1
                    else:
                        break
                    take+=1
                return take
            best=None
            best_key=None
            for m in legal:
                r,c,d=m
                boxes=_adj_boxes(r,c,d)
                imm=0
                for (br,bc) in boxes:
                    if sides[br,bc]==2:
                        imm+=1
                try:
                    tk=greedy_take(r,c,d)
                except Exception:
                    tk=imm
                key=(tk,imm,r,c)
                if best_key is None or key<best_key:
                    best_key=key
                    best=m
            return f"{best[0]},{best[1]},{best[2]}"
    except Exception:
        try:
            return _first_legal_fallback(horizontal, vertical)
        except Exception:
            return "0,0,H"
