
import time

LINES = [
    (0,1,2,3),(4,5,6,7),(8,9,10,11),(12,13,14,15),
    (0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15),
    (0,5,10,15),(3,6,9,12)
]

LINES_THROUGH = [[] for _ in range(16)]
for _ln in LINES:
    for _i in _ln:
        LINES_THROUGH[_i].append(_ln)

ORDER = [5,6,9,10,0,3,12,15,1,2,4,7,8,11,13,14]
ORDER_POS = {v:i for i,v in enumerate(ORDER)}

INF = 10**9
WIN = 100000

def _is_win(flat, idx, p):
    for a,b,c,d in LINES_THROUGH[idx]:
        if flat[a]==p and flat[b]==p and flat[c]==p and flat[d]==p:
            return True
    return False

def _evaluate(flat):
    s = 0
    for a,b,c,d in LINES:
        fa = flat[a]; fb = flat[b]; fc = flat[c]; fd = flat[d]
        n1 = (fa==1)+(fb==1)+(fc==1)+(fd==1)
        if n1>0:
            nm = (fa==-1)+(fb==-1)+(fc==-1)+(fd==-1)
            if nm>0:
                continue
            if n1==3:
                s += 1000
            elif n1==2:
                s += 50
            elif n1==1:
                s += 1
        else:
            nm = (fa==-1)+(fb==-1)+(fc==-1)+(fd==-1)
            if nm==3:
                s -= 1200
            elif nm==2:
                s -= 80
            elif nm==1:
                s -= 2
    return s

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        flat = [0]*16
        for r in range(4):
            row = board[r]
            for c in range(4):
                v = row[c]
                flat[r*4+c] = 1 if v==1 else (-1 if v==-1 else 0)
        empties = [i for i in range(16) if flat[i]==0]
        if not empties:
            return (0,0)
        if len(empties)==1:
            return (empties[0]//4, empties[0]%4)
        # immediate win
        for m in empties:
            flat[m]=1
            w = _is_win(flat, m, 1)
            flat[m]=0
            if w:
                return (m//4, m%4)
        # immediate block (4-in-row threat)
        threats = []
        for m in empties:
            flat[m]=-1
            w = _is_win(flat, m, -1)
            flat[m]=0
            if w:
                threats.append(m)
        if len(threats)==1:
            m = threats[0]
            return (m//4, m%4)
        if len(threats)>=2:
            # double threat: cannot block both, pick one but let search try to find better
            # return first threat as fallback, search may override
            fallback_block = threats[0]
        else:
            fallback_block = None

        if len(empties)==16:
            return (1,1)

        start = time.time()
        limit = 0.88

        # static order
        empties_sorted = sorted(empties, key=lambda x: ORDER_POS[x])

        # 1-ply heuristic fallback
        best_fallback = empties_sorted[0]
        best_fallback_score = -INF
        for m in empties_sorted:
            flat[m]=1
            sc = _evaluate(flat)
            # small positional bonus
            if m in (5,6,9,10):
                sc += 3
            flat[m]=0
            if sc > best_fallback_score:
                best_fallback_score = sc
                best_fallback = m
        if fallback_block is not None:
            # keep block as strong candidate if heuristic missed
            pass

        best_move = best_fallback
        # if only few empties we can try full depth, else iterative deepening will timeout
        max_depth = len(empties)
        # cap max_depth for opening to avoid useless deep iterations
        # iterative deepening handles it via timeout

        nodes = 0

        def alphabeta(depth, alpha, beta, turn):
            nonlocal nodes
            nodes += 1
            if (nodes & 1023)==0:
                if time.time()-start > limit:
                    raise _Timeout()
            # generate empties in ORDER
            # quick draw check: find any empty
            has_empty = False
            for i in range(16):
                if flat[i]==0:
                    has_empty = True
                    break
            if not has_empty:
                return 0
            if depth<=0:
                return _evaluate(flat)
            if turn==1:
                best = -INF
                # iterate in ORDER for good pruning
                for m in ORDER:
                    if flat[m]!=0:
                        continue
                    flat[m]=1
                    if _is_win(flat, m, 1):
                        flat[m]=0
                        return WIN+depth
                    val = alphabeta(depth-1, alpha, beta, -1)
                    flat[m]=0
                    if val>best:
                        best=val
                    if val>alpha:
                        alpha=val
                    if alpha>=beta:
                        break
                return best
            else:
                best = INF
                for m in ORDER:
                    if flat[m]!=0:
                        continue
                    flat[m]=-1
                    if _is_win(flat, m, -1):
                        flat[m]=0
                        return -WIN-depth
                    val = alphabeta(depth-1, alpha, beta, 1)
                    flat[m]=0
                    if val<best:
                        best=val
                    if val<beta:
                        beta=val
                    if alpha>=beta:
                        break
                return best

        ordered = empties_sorted[:]
        # iterative deepening
        try:
            for depth in range(1, max_depth+1):
                # time check
                if time.time()-start > limit:
                    break
                cur_scores = []
                alpha = -INF
                beta = INF
                # search each root move
                for m in ordered:
                    if time.time()-start > limit:
                        raise _Timeout()
                    flat[m]=1
                    if _is_win(flat, m, 1):
                        flat[m]=0
                        return (m//4, m%4)
                    val = alphabeta(depth-1, alpha, beta, -1)
                    flat[m]=0
                    cur_scores.append((val, m))
                    if val>alpha:
                        alpha=val
                # sort for next iteration (best first)
                cur_scores.sort(key=lambda x: x[0], reverse=True)
                ordered = [m for _,m in cur_scores]
                best_move = ordered[0]
                best_val = cur_scores[0][0]
                if best_val >= WIN-1000:
                    break
                # if depth equals remaining, we solved exactly
                if depth==max_depth:
                    break
                # early exit if little time left
                if time.time()-start > limit*0.9 and depth>=4:
                    break
        except _Timeout:
            pass

        # validate
        r, c = best_move//4, best_move%4
        if flat[best_move]!=0:
            # illegal, fallback
            for m in empties:
                return (m//4, m%4)
        return (r, c)
    except Exception:
        try:
            for r in range(4):
                for c in range(4):
                    if board[r][c]==0:
                        return (r,c)
        except Exception:
            pass
        return (0,0)
