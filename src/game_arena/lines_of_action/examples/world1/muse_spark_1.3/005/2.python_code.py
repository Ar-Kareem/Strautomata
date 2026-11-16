
import time

INF = 100000
WIN = 10000
DIRS = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]

def _to_list(board):
    if hasattr(board, "tolist"):
        try:
            bl = board.tolist()
        except Exception:
            bl = [list(r) for r in board]
    else:
        bl = [list(r) for r in board]
    return [[int(x) for x in row] for row in bl]

def _gen_moves(board):
    row_c = [0]*8
    col_c = [0]*8
    d1_c = [0]*15
    d2_c = [0]*15
    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] != 0:
                row_c[r] += 1
                col_c[c] += 1
                d1_c[r-c+7] += 1
                d2_c[r+c] += 1
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue
            rc = row_c[r]
            cc = col_c[c]
            d1 = d1_c[r-c+7]
            d2 = d2_c[r+c]
            # (dr,dc,dist)
            for dr, dc in DIRS:
                if dr == 0:
                    dist = rc
                elif dc == 0:
                    dist = cc
                elif dr == dc:
                    dist = d1
                else:
                    dist = d2
                if dist <= 0:
                    continue
                tr = r + dr*dist
                tc = c + dc*dist
                if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                    continue
                if board[tr][tc] == 1:
                    continue
                blocked = False
                for k in range(1, dist):
                    if board[r+dr*k][c+dc*k] == -1:
                        blocked = True
                        break
                if blocked:
                    continue
                moves.append((r,c,tr,tc))
    return moves

def _is_connected(board, color):
    first = None
    cnt = 0
    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] == color:
                cnt += 1
                if first is None:
                    first = (r,c)
    if cnt == 0:
        return False
    if cnt == 1:
        return True
    stack = [first]
    seen = set()
    seen.add(first)
    while stack:
        r,c = stack.pop()
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0:
                    continue
                nr = r+dr
                nc = c+dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == color:
                    t = (nr,nc)
                    if t not in seen:
                        seen.add(t)
                        stack.append(t)
                        if len(seen) == cnt:
                            return True
    return len(seen) == cnt

def _evaluate(board):
    my_rs = 0
    my_cs = 0
    op_rs = 0
    op_cs = 0
    my_n = 0
    op_n = 0
    my_set = set()
    op_set = set()
    my_cdist = 0
    op_cdist = 0
    for r in range(8):
        br = board[r]
        for c in range(8):
            v = br[c]
            if v == 1:
                my_n += 1
                my_rs += r
                my_cs += c
                my_set.add((r,c))
                my_cdist += (r-3.5)*(r-3.5)+(c-3.5)*(c-3.5)
            elif v == -1:
                op_n += 1
                op_rs += r
                op_cs += c
                op_set.add((r,c))
                op_cdist += (r-3.5)*(r-3.5)+(c-3.5)*(c-3.5)
    if my_n == 0:
        return -WIN
    if op_n == 0:
        return WIN
    # components + largest
    def comp_largest(s):
        if len(s) <= 1:
            return 1, len(s)
        visited = set()
        comp = 0
        largest = 0
        for p in s:
            if p in visited:
                continue
            comp += 1
            stack = [p]
            visited.add(p)
            sz = 0
            while stack:
                r,c = stack.pop()
                sz += 1
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        if dr == 0 and dc == 0:
                            continue
                        nb = (r+dr,c+dc)
                        if nb in s and nb not in visited:
                            visited.add(nb)
                            stack.append(nb)
            if sz > largest:
                largest = sz
        return comp, largest
    my_comp, my_max = comp_largest(my_set)
    op_comp, op_max = comp_largest(op_set)
    # immediate connection (should have been caught, but reward strongly)
    if my_comp == 1 and op_comp != 1:
        # still heuristic, large bonus proportional to few pieces
        pass
    my_cr = my_rs / my_n
    my_cc = my_cs / my_n
    op_cr = op_rs / op_n
    op_cc = op_cs / op_n
    my_spread = 0.0
    op_spread = 0.0
    for (r,c) in my_set:
        my_spread += abs(r-my_cr)+abs(c-my_cc)
    for (r,c) in op_set:
        op_spread += abs(r-op_cr)+abs(c-op_cc)
    my_spread /= my_n
    op_spread /= op_n
    my_cdist /= my_n
    op_cdist /= op_n
    score = (op_comp - my_comp)*80.0
    score += (my_max/my_n - op_max/op_n)*80.0
    score += (op_spread - my_spread)*8.0
    score += (op_cdist - my_cdist)*3.0
    score += (op_n - my_n)*2.0
    return score

def _apply(board, m):
    nb = [row[:] for row in board]
    fr,fc,tr,tc = m
    nb[fr][fc] = 0
    nb[tr][tc] = 1
    return nb

def _flip(board):
    return [[-v for v in row] for row in board]

def _order(board, moves):
    scored = []
    for m in moves:
        fr,fc,tr,tc = m
        s = 0
        if board[tr][tc] == -1:
            s += 200
        # centralise destination
        s -= (tr-3.5)*(tr-3.5)+(tc-3.5)*(tc-3.5)
        # prefer moves from edge
        if fr == 0 or fr == 7 or fc == 0 or fc == 7:
            s += 5
        scored.append((s,m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _,m in scored]

class _Timeout(Exception):
    pass

def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90
    try:
        b = _to_list(board)
    except Exception:
        return "0,1:1,1"
    try:
        moves = _gen_moves(b)
        if not moves:
            return "0,0:0,1"
        if len(moves) == 1:
            m = moves[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        # quick static pick as fallback
        ordered0 = _order(b, moves)
        best = ordered0[0]
        # check immediate win first
        for m in ordered0:
            b2 = _apply(b, m)
            if _is_connected(b2, 1):
                return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        node_cnt = [0]
        def check_time():
            node_cnt[0] += 1
            if node_cnt[0] % 256 == 0 and time.perf_counter() > deadline:
                raise _Timeout()
        def negamax(cur, depth, alpha, beta):
            check_time()
            if depth == 0:
                return _evaluate(cur)
            ms = _gen_moves(cur)
            if not ms:
                return -WIN
            ms = _order(cur, ms)
            bestv = -INF
            for m in ms:
                b2 = _apply(cur, m)
                if _is_connected(b2, 1):
                    return WIN
                if _is_connected(b2, -1):
                    sc = -WIN
                else:
                    b2f = _flip(b2)
                    sc = -negamax(b2f, depth-1, -beta, -alpha)
                if sc > bestv:
                    bestv = sc
                if bestv > alpha:
                    alpha = bestv
                if alpha >= beta:
                    break
            return bestv
        # iterative deepening
        max_depth = 8
        for depth in range(1, max_depth+1):
            try:
                ordered = _order(b, moves)
                alpha = -INF
                local_best = best
                local_score = -INF
                for m in ordered:
                    if time.perf_counter() > deadline:
                        raise _Timeout()
                    b2 = _apply(b, m)
                    if _is_connected(b2, 1):
                        return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
                    if _is_connected(b2, -1):
                        sc = -WIN
                    else:
                        b2f = _flip(b2)
                        sc = -negamax(b2f, depth-1, -INF, -alpha) if depth > 1 else -_evaluate(b2f)
                    if sc > local_score:
                        local_score = sc
                        local_best = m
                    if sc > alpha:
                        alpha = sc
                best = local_best
                if local_score >= WIN-10:
                    break
                if time.perf_counter() > deadline:
                    break
                # if branching huge, don't go too deep
                if depth >= 4 and len(moves) > 25:
                    # allow one more if time remains plenty
                    if time.perf_counter() > start + 0.6:
                        break
                if depth >= 5:
                    break
            except _Timeout:
                break
        return f"{best[0]},{best[1]}:{best[2]},{best[3]}"
    except _Timeout:
        try:
            m = best
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        except Exception:
            pass
        try:
            m = moves[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        except Exception:
            return "0,1:1,1"
    except Exception:
        try:
            moves = _gen_moves(_to_list(board))
            if moves:
                m = moves[0]
                return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        except Exception:
            pass
        return "0,1:1,1"
