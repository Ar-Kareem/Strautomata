
import time

_WIN = 10000
_INF = 1000000

_NEIGHBORS = [[] for _ in range(30)]
_ADJ_MASK = [0]*30
_CENTRAL = [0.0]*30
_ROW = [0]*30
_COL = [0]*30
for _r in range(5):
    for _c in range(6):
        _i = _r*6+_c
        _ROW[_i]=_r
        _COL[_i]=_c
        if _r>0:
            _nb=(_r-1)*6+_c
            _NEIGHBORS[_i].append((_nb,'U'))
            _ADJ_MASK[_i]|=1<<_nb
        if _c<5:
            _nb=_r*6+_c+1
            _NEIGHBORS[_i].append((_nb,'R'))
            _ADJ_MASK[_i]|=1<<_nb
        if _r<4:
            _nb=(_r+1)*6+_c
            _NEIGHBORS[_i].append((_nb,'D'))
            _ADJ_MASK[_i]|=1<<_nb
        if _c>0:
            _nb=_r*6+_c-1
            _NEIGHBORS[_i].append((_nb,'L'))
            _ADJ_MASK[_i]|=1<<_nb
        _CENTRAL[_i]=-(abs(_r-2)+abs(_c-2.5))

class _Timeout(Exception):
    pass

_nodes = 0
_deadline = 0.0

def _pop(n):
    try:
        return n.bit_count()
    except Exception:
        return bin(n).count("1")

def _to_bits(board):
    bits=0
    try:
        import numpy as np
        arr=np.asarray(board).reshape(-1)
        for i,v in enumerate(arr):
            if int(v)==1:
                if 0<=i<30:
                    bits|=1<<i
        # if board was 5x6 this mapping i=r*6+c is correct
        # if board was flat length 30 same mapping
        return bits
    except Exception:
        pass
    # fallback pure python
    try:
        # try nested 5x6 list
        if isinstance(board,(list,tuple)) and len(board)==5 and isinstance(board[0],(list,tuple)):
            for r in range(5):
                for c in range(6):
                    try:
                        if int(board[r][c])==1:
                            bits|=1<<(r*6+c)
                    except Exception:
                        continue
            return bits
        # flat
        flat=list(board)
        # if nested deeper flatten
        tmp=[]
        for v in flat:
            if isinstance(v,(list,tuple)):
                tmp.extend(list(v))
            else:
                tmp.append(v)
        for i,v in enumerate(tmp):
            if i>=30:
                break
            if int(v)==1:
                bits|=1<<i
        return bits
    except Exception:
        return 0

def _gen_moves(you, opp):
    moves=[]
    y=you
    while y:
        lsb=y & -y
        s=(lsb.bit_length()-1)
        y^=lsb
        for nb,ch in _NEIGHBORS[s]:
            if (opp>>nb)&1:
                moves.append((s,nb,ch))
    return moves

def _count_moves(you, opp):
    cnt=0
    y=you
    while y:
        lsb=y & -y
        s=(lsb.bit_length()-1)
        y^=lsb
        inter=_ADJ_MASK[s] & opp
        if inter:
            cnt+=_pop(inter)
    return cnt

def _evaluate(you, opp):
    my_mob=_count_moves(you,opp)
    opp_mob=_count_moves(opp,you)
    my_cnt=_pop(you)
    opp_cnt=_pop(opp)
    # central sum
    mc=0.0
    oc=0.0
    y=you
    while y:
        lsb=y & -y
        s=(lsb.bit_length()-1)
        y^=lsb
        mc+=_CENTRAL[s]
    o=opp
    while o:
        lsb=o & -o
        s=(lsb.bit_length()-1)
        o^=lsb
        oc+=_CENTRAL[s]
    return (my_mob-opp_mob)*15 + (my_cnt-opp_cnt)*5 + (mc-oc)*1.0

def _order_full(you, opp, moves):
    scored=[]
    for s,d,ch in moves:
        you_after=(you & ~(1<<s)) | (1<<d)
        opp_after=opp & ~(1<<d)
        om=_count_moves(opp_after, you_after)
        sc=-om*10.0+_CENTRAL[d]
        scored.append((sc,(s,d,ch)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _,m in scored]

def _order_cheap(moves):
    return sorted(moves, key=lambda m: _CENTRAL[m[1]], reverse=True)

def _negamax(you, opp, depth, alpha, beta, ply):
    global _nodes, _deadline
    _nodes+=1
    if (_nodes & 255)==0:
        if time.perf_counter()>_deadline:
            raise _Timeout()
    moves=_gen_moves(you, opp)
    if not moves:
        return -_WIN+ply
    if depth<=0:
        return _evaluate(you, opp)
    if ply<2:
        ordered=_order_full(you, opp, moves)
    else:
        ordered=_order_cheap(moves)
    best=-_INF
    for s,d,ch in ordered:
        you_after=(you & ~(1<<s)) | (1<<d)
        opp_after=opp & ~(1<<d)
        score=-_negamax(opp_after, you_after, depth-1, -beta, -alpha, ply+1)
        if score>best:
            best=score
            if best>alpha:
                alpha=best
                if alpha>=beta:
                    break
    return best

def policy(you, opponent):
    global _nodes, _deadline
    start=time.perf_counter()
    _deadline=start+0.85
    _nodes=0
    try:
        you_bits=_to_bits(you)
        opp_bits=_to_bits(opponent)
        moves=_gen_moves(you_bits, opp_bits)
        if not moves:
            return "0,0,U"
        if len(moves)==1:
            s,d,ch=moves[0]
            return f"{_ROW[s]},{_COL[s]},{ch}"
        # initial ordering
        try:
            ordered=_order_full(you_bits, opp_bits, moves)
        except Exception:
            ordered=moves
        best_move=ordered[0]
        # total pieces for max depth
        total=_pop(you_bits)+_pop(opp_bits)
        max_depth=total if total<30 else 30
        # iterative deepening
        for depth in range(1, max_depth+1):
            # time check
            if time.perf_counter()>_deadline-0.05:
                break
            alpha=-_INF
            beta=_INF
            # put best first
            try:
                # move best to front
                if best_move in ordered:
                    ordered.remove(best_move)
                    ordered=[best_move]+ordered
            except Exception:
                pass
            cur_best_move=best_move
            cur_best=-_INF
            # root loop with alpha beta
            for s,d,ch in ordered:
                you_after=(you_bits & ~(1<<s)) | (1<<d)
                opp_after=opp_bits & ~(1<<d)
                try:
                    score=-_negamax(opp_after, you_after, depth-1, -beta, -alpha, 1)
                except _Timeout:
                    raise _Timeout()
                if score>cur_best:
                    cur_best=score
                    cur_best_move=(s,d,ch)
                    if score>alpha:
                        alpha=score
            # completed depth
            best_move=cur_best_move
            # reorder for next iteration: best first, rest ordered by previous heuristic
            # simple bubble best to front already
            ordered=[best_move]+[m for m in ordered if m!=best_move]
            if cur_best>=_WIN-50:
                break
            # if depth large and branching tiny, continue; otherwise timeout will stop
            if depth>=6 and total>12:
                # in opening with many pieces depth 6 is already very strong; check time
                if time.perf_counter()>_deadline-0.15:
                    break
        s,d,ch=best_move
        return f"{_ROW[s]},{_COL[s]},{ch}"
    except _Timeout:
        try:
            # return best found so far if exists
            s,d,ch=best_move
            return f"{_ROW[s]},{_COL[s]},{ch}"
        except Exception:
            pass
    except Exception:
        pass
    # ultimate fallback: find any legal move by scanning board
    try:
        you_bits=_to_bits(you)
        opp_bits=_to_bits(opponent)
        moves=_gen_moves(you_bits, opp_bits)
        if moves:
            s,d,ch=moves[0]
            return f"{_ROW[s]},{_COL[s]},{ch}"
    except Exception:
        pass
    # try brute scan of input arrays
    try:
        import numpy as np
        ya=np.asarray(you)
        oa=np.asarray(opponent)
        # ensure 5x6
        ya=ya.reshape(5,6)
        oa=oa.reshape(5,6)
        for r in range(5):
            for c in range(6):
                if int(ya[r,c])==1:
                    if r>0 and int(oa[r-1,c])==1:
                        return f"{r},{c},U"
                    if c<5 and int(oa[r,c+1])==1:
                        return f"{r},{c},R"
                    if r<4 and int(oa[r+1,c])==1:
                        return f"{r},{c},D"
                    if c>0 and int(oa[r,c-1])==1:
                        return f"{r},{c},L"
    except Exception:
        pass
    return "0,0,U"
