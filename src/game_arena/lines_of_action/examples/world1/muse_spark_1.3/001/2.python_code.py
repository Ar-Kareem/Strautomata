
import numpy as np
import time

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
INF = 10000.0
_TT = {}

def _gen_moves(board):
    # board: 8x8 np int8, 1 to move
    rows = np.count_nonzero(board, axis=1)
    cols = np.count_nonzero(board, axis=0)
    occ = np.argwhere(board != 0)
    d1 = [0]*15
    d2 = [0]*15
    for k in range(len(occ)):
        r = int(occ[k][0]); c = int(occ[k][1])
        d1[r-c+7] += 1
        d2[r+c] += 1
    own = np.argwhere(board == 1)
    moves = []
    for k in range(len(own)):
        r = int(own[k][0]); c = int(own[k][1])
        n_row = int(rows[r]); n_col = int(cols[c])
        n_d1 = d1[r-c+7]; n_d2 = d2[r+c]
        for dr, dc in DIRS:
            if dr == 0:
                n = n_row
            elif dc == 0:
                n = n_col
            elif dr == dc:
                n = n_d1
            else:
                n = n_d2
            if n <= 0:
                continue
            tr = r + dr*n
            tc = c + dc*n
            if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                continue
            if board[tr, tc] == 1:
                continue
            blocked = False
            for s in range(1, n):
                rr = r + dr*s
                cc = c + dc*s
                if board[rr, cc] == -1:
                    blocked = True
                    break
            if blocked:
                continue
            moves.append((r, c, tr, tc))
    return moves

def _is_connected(board, color):
    pos = np.argwhere(board == color)
    n = len(pos)
    if n == 0:
        return False
    if n == 1:
        return True
    s = set()
    for k in range(n):
        s.add((int(pos[k][0]), int(pos[k][1])))
    start = next(iter(s))
    visited = set()
    visited.add(start)
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr in (-1, 0, 1):
            nr = r + dr
            if nr < 0 or nr >= 8:
                continue
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nc = c + dc
                if nc < 0 or nc >= 8:
                    continue
                nb = (nr, nc)
                if nb in s and nb not in visited:
                    visited.add(nb)
                    stack.append(nb)
                    if len(visited) == n:
                        return True
    return len(visited) == n

def _count_comp(pos):
    n = len(pos)
    if n == 0:
        return 0
    if n == 1:
        return 1
    s = set()
    for k in range(n):
        s.add((int(pos[k][0]), int(pos[k][1])))
    visited = set()
    comp = 0
    for p in list(s):
        if p in visited:
            continue
        comp += 1
        if comp > 12:
            return comp
        stack = [p]
        visited.add(p)
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                nr = r + dr
                if nr < 0 or nr >= 8:
                    continue
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nc = c + dc
                    if nc < 0 or nc >= 8:
                        continue
                    nb = (nr, nc)
                    if nb in s and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
    return comp

def _evaluate(board):
    own = np.argwhere(board == 1)
    opp = np.argwhere(board == -1)
    n_own = len(own)
    n_opp = len(opp)
    if n_own == 0:
        return -INF
    if n_opp == 0:
        return INF
    if n_own == 1:
        comp_own = 1
    else:
        comp_own = _count_comp(own)
    if n_opp == 1:
        comp_opp = 1
    else:
        comp_opp = _count_comp(opp)
    own_conn = (comp_own == 1)
    opp_conn = (comp_opp == 1)
    if own_conn and not opp_conn:
        return INF
    if opp_conn and not own_conn:
        return -INF
    if own_conn and opp_conn:
        return -INF
    # spread / centralization
    try:
        mo = own.mean(axis=0)
        var_o = float(((own - mo)**2).sum(axis=1).mean())
        cd_o = float(((mo - 3.5)**2).sum())
    except Exception:
        var_o = 0.0
        cd_o = 0.0
    try:
        mp = opp.mean(axis=0)
        var_p = float(((opp - mp)**2).sum(axis=1).mean())
        cd_p = float(((mp - 3.5)**2).sum())
    except Exception:
        var_p = 0.0
        cd_p = 0.0
    score = 120.0*(comp_opp - comp_own) + 8.0*(var_p - var_o) + 4.0*(cd_p - cd_o) + 3.0*(n_opp - n_own)
    return score

_nodes = [0]
_deadline = [0.0]

def _negamax(board, depth, alpha, beta):
    _nodes[0] += 1
    if (_nodes[0] & 255) == 0:
        if time.perf_counter() > _deadline[0]:
            raise TimeoutError()
    key = board.tobytes()
    hit = _TT.get(key)
    if hit is not None and hit[0] >= depth:
        _, sc, fl = hit
        if fl == 0:
            return sc
        if fl == 1 and sc >= beta:
            return sc
        if fl == -1 and sc <= alpha:
            return sc
    if depth == 0:
        v = _evaluate(board)
        if len(_TT) < 60000:
            _TT[key] = (0, v, 0)
        return v
    # terminal check: opponent already connected -> loss
    if _is_connected(board, -1):
        return -INF
    if _is_connected(board, 1):
        return INF
    moves = _gen_moves(board)
    if not moves:
        return -INF + 1
    # order moves
    scored = []
    for r0, c0, r1, c1 in moves:
        cap = 10.0 if board[r1, c1] == -1 else 0.0
        fd = abs(r0-3.5)+abs(c0-3.5)
        td = abs(r1-3.5)+abs(c1-3.5)
        scored.append((cap + (fd - td), (r0, c0, r1, c1)))
    scored.sort(key=lambda x: x[0], reverse=True)
    best = -INF - 1
    orig_alpha = alpha
    for _, m in scored:
        r0, c0, r1, c1 = m
        nb = board.copy()
        nb[r0, c0] = 0
        nb[r1, c1] = 1
        # mover wins even if both connect
        if _is_connected(nb, 1):
            if len(_TT) < 60000:
                _TT[key] = (depth, INF, 0)
            return INF
        nb *= -1
        try:
            val = -_negamax(nb, depth-1, -beta, -alpha)
        except TimeoutError:
            raise
        except RecursionError:
            val = _evaluate(board)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    if len(_TT) < 60000:
        if best <= orig_alpha:
            fl = -1
        elif best >= beta:
            fl = 1
        else:
            fl = 0
        _TT[key] = (depth, best, fl)
    return best

def policy(board) -> str:
    try:
        b = np.array(board, dtype=np.int8).reshape(8, 8)
    except Exception:
        try:
            b = np.array(board, dtype=np.int8)
            b = b.reshape(8, 8)
        except Exception:
            return "0,1:0,2"
    try:
        moves = _gen_moves(b)
    except Exception:
        moves = []
    if not moves:
        # brute fallback search for any legal move
        try:
            for r in range(8):
                for c in range(8):
                    if b[r, c] != 1:
                        continue
                    for dr, dc in DIRS:
                        # count line
                        cnt = 0
                        if dr == 0:
                            for cc in range(8):
                                if b[r, cc] != 0:
                                    cnt += 1
                        elif dc == 0:
                            for rr in range(8):
                                if b[rr, c] != 0:
                                    cnt += 1
                        elif dr == dc:
                            for k in range(-7, 8):
                                rr = r+k; cc = c+k
                                if 0 <= rr < 8 and 0 <= cc < 8 and b[rr, cc] != 0:
                                    cnt += 1
                        else:
                            for k in range(-7, 8):
                                rr = r+k; cc = c-k
                                # use dr direction line r+c constant
                                if 0 <= rr < 8 and 0 <= cc < 8 and b[rr, cc] != 0:
                                    cnt += 1
                        tr = r+dr*cnt; tc = c+dc*cnt
                        if 0 <= tr < 8 and 0 <= tc < 8 and b[tr, tc] != 1:
                            ok = True
                            for s in range(1, cnt):
                                if b[r+dr*s, c+dc*s] == -1:
                                    ok = False
                                    break
                            if ok:
                                return f"{r},{c}:{tr},{tc}"
        except Exception:
            pass
        return "0,0:0,0"
    if len(moves) == 1:
        r0, c0, r1, c1 = moves[0]
        return f"{r0},{c0}:{r1},{c1}"
    # immediate winning move
    try:
        for r0, c0, r1, c1 in moves:
            nb = b.copy()
            nb[r0, c0] = 0
            nb[r1, c1] = 1
            if _is_connected(nb, 1):
                return f"{r0},{c0}:{r1},{c1}"
    except Exception:
        pass
    start = time.perf_counter()
    _deadline[0] = start + 0.88
    _nodes[0] = 0
    # order root moves centrally first
    def _ord(m):
        r0, c0, r1, c1 = m
        cap = 10.0 if b[r1, c1] == -1 else 0.0
        fd = abs(r0-3.5)+abs(c0-3.5)
        td = abs(r1-3.5)+abs(c1-3.5)
        return cap + (fd - td)
    try:
        moves_sorted = sorted(moves, key=_ord, reverse=True)
    except Exception:
        moves_sorted = moves
    best_move = moves_sorted[0]
    try:
        # iterative deepening 1..4
        for depth in (1, 2, 3, 4):
            if time.perf_counter() > _deadline[0] - 0.05:
                break
            alpha = -INF - 1
            beta = INF + 1
            scored_root = []
            cur_best = best_move
            cur_alpha = alpha
            for m in moves_sorted:
                if time.perf_counter() > _deadline[0]:
                    raise TimeoutError()
                r0, c0, r1, c1 = m
                nb = b.copy()
                nb[r0, c0] = 0
                nb[r1, c1] = 1
                # already checked win, but re-check for safety
                if _is_connected(nb, 1):
                    return f"{r0},{c0}:{r1},{c1}"
                nb *= -1
                val = -_negamax(nb, depth-1, -beta, -cur_alpha) if depth > 1 else -_evaluate(nb)
                scored_root.append((val, m))
                if val > cur_alpha:
                    cur_alpha = val
                    cur_best = m
            # sort for next iteration
            scored_root.sort(key=lambda x: x[0], reverse=True)
            moves_sorted = [m for _, m in scored_root]
            best_move = cur_best
            if cur_alpha >= INF - 1:
                break
            # if depth 4 done, stop
            if depth == 4:
                break
    except TimeoutError:
        pass
    except Exception:
        pass
    try:
        r0, c0, r1, c1 = best_move
        # final legality sanity: verify
        if b[r0, c0] != 1 or (b[r1, c1] == 1):
            # fallback to first legal
            r0, c0, r1, c1 = moves[0]
        return f"{r0},{c0}:{r1},{c1}"
    except Exception:
        r0, c0, r1, c1 = moves[0]
        return f"{r0},{c0}:{r1},{c1}"
