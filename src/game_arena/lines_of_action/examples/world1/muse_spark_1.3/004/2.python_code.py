
import time
try:
    import numpy as np
    _HAS_NP = True
except Exception:
    _HAS_NP = False

WIN = 10000
INF = 10**9

_START = 0.0
_LIMIT = 0.9
_NODES = 0

class _Timeout(Exception):
    pass

def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0:
        if time.perf_counter() - _START > _LIMIT:
            raise _Timeout()

DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))

def _gen_moves_np(b):
    # b is 8x8 np array, 1 to move
    row_cnt = np.count_nonzero(b, axis=1)
    col_cnt = np.count_nonzero(b, axis=0)
    d1 = [0]*15
    d2 = [0]*15
    for r in range(8):
        for c in range(8):
            if b[r, c] != 0:
                d1[r-c+7] += 1
                d2[r+c] += 1
    moves = []
    for r in range(8):
        for c in range(8):
            if b[r, c] != 1:
                continue
            rc = int(row_cnt[r]); cc = int(col_cnt[c])
            d1c = d1[r-c+7]; d2c = d2[r+c]
            for dr, dc in DIRS:
                if dr == 0:
                    d = rc
                elif dc == 0:
                    d = cc
                elif dr == dc:
                    d = d1c
                else:
                    d = d2c
                if d == 0:
                    continue
                tr = r + dr*d
                tc = c + dc*d
                if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                    continue
                if b[tr, tc] == 1:
                    continue
                blocked = False
                for k in range(1, d):
                    if b[r+dr*k, c+dc*k] == -1:
                        blocked = True
                        break
                if blocked:
                    continue
                cap = bool(b[tr, tc] == -1)
                moves.append((r, c, tr, tc, cap))
    return moves

def _gen_moves_list(board):
    # board 8x8 list
    row_cnt = [0]*8
    col_cnt = [0]*8
    d1 = [0]*15
    d2 = [0]*15
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v != 0:
                row_cnt[r] += 1
                col_cnt[c] += 1
                d1[r-c+7] += 1
                d2[r+c] += 1
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue
            for dr, dc in DIRS:
                if dr == 0:
                    d = row_cnt[r]
                elif dc == 0:
                    d = col_cnt[c]
                elif dr == dc:
                    d = d1[r-c+7]
                else:
                    d = d2[r+c]
                tr = r+dr*d; tc = c+dc*d
                if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                    continue
                if board[tr][tc] == 1:
                    continue
                blocked = False
                for k in range(1, d):
                    if board[r+dr*k][c+dc*k] == -1:
                        blocked = True
                        break
                if blocked:
                    continue
                cap = (board[tr][tc] == -1)
                moves.append((r, c, tr, tc, cap))
    return moves

def _positions_np(b, color):
    rs, cs = np.where(b == color)
    return list(zip(rs.tolist(), cs.tolist()))

def _analyze_pos(pos):
    n = len(pos)
    if n == 0:
        return 0, 0, 0.0, 0
    if n == 1:
        r, c = pos[0]
        cen = (r-3.5)*(r-3.5)+(c-3.5)*(c-3.5)
        return 1, 0, cen, 1
    # components via adjacency Chebyshev==1
    visited = [False]*n
    comp = 0
    for i in range(n):
        if visited[i]:
            continue
        comp += 1
        stack = [i]
        visited[i] = True
        while stack:
            u = stack.pop()
            ru, cu = pos[u]
            for v in range(n):
                if not visited[v]:
                    rv, cv = pos[v]
                    if abs(ru-rv) <= 1 and abs(cu-cv) <= 1:
                        visited[v] = True
                        stack.append(v)
    # MST Prim with Chebyshev distance
    INFd = 10**9
    mind = [INFd]*n
    used = [False]*n
    mind[0] = 0
    total = 0
    for _ in range(n):
        u = -1
        best = INFd
        for i in range(n):
            if not used[i] and mind[i] < best:
                best = mind[i]; u = i
        used[u] = True
        total += best
        ru, cu = pos[u]
        for v in range(n):
            if not used[v]:
                rv, cv = pos[v]
                d = abs(ru-rv)
                dc = abs(cu-cv)
                if dc > d:
                    d = dc
                if d < mind[v]:
                    mind[v] = d
    cen = 0.0
    for r, c in pos:
        cen += (r-3.5)*(r-3.5)+(c-3.5)*(c-3.5)
    return comp, total, cen, n

def _is_connected_np(b, color):
    # fast BFS
    found = None
    cnt = 0
    for r in range(8):
        for c in range(8):
            if b[r, c] == color:
                cnt += 1
                if found is None:
                    found = (r, c)
    if cnt <= 1:
        return True
    # set for lookup
    s = set()
    for r in range(8):
        for c in range(8):
            if b[r, c] == color:
                s.add(r*8+c)
    stack = [found[0]*8+found[1]]
    seen = {stack[0]}
    while stack:
        cur = stack.pop()
        r = cur // 8; c = cur % 8
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = r+dr; nc = c+dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    k = nr*8+nc
                    if k in s and k not in seen:
                        seen.add(k)
                        stack.append(k)
    return len(seen) == cnt

def _static_eval_np(b):
    own = _positions_np(b, 1)
    opp = _positions_np(b, -1)
    on = len(own); pn = len(opp)
    if on <= 1:
        return WIN
    if pn <= 1:
        return -WIN
    oc, om, ocen, _ = _analyze_pos(own)
    pc, pm, pcen, _ = _analyze_pos(opp)
    if oc == 1:
        return WIN
    if pc == 1:
        return -WIN
    score = 80.0*(pc - oc) + 8.0*(pm - om) + 0.4*(pcen - ocen) + 5.0*(pn - on)
    return score

def _order_moves_np(b, moves):
    if not moves:
        return moves
    # centroid of own
    sr = 0; sc = 0; n = 0
    for r in range(8):
        for c in range(8):
            if b[r, c] == 1:
                sr += r; sc += c; n += 1
    if n == 0:
        return moves
    cr = sr / n; cc = sc / n
    scored = []
    for m in moves:
        fr, fc, tr, tc, cap = m
        d = abs(tr-cr)+abs(tc-cc)
        if cap:
            d += 4.0
        # prefer moves from edge? slight bonus for moving edge pieces
        if fr == 0 or fr == 7 or fc == 0 or fc == 7:
            d -= 0.5
        scored.append((d, m))
    scored.sort(key=lambda x: x[0])
    return [m for _, m in scored]

def _do_move_np(b, m):
    nb = b.copy()
    fr, fc, tr, tc, _ = m
    nb[fr, fc] = 0
    nb[tr, tc] = 1
    return nb

def _negamax(b, depth, alpha, beta):
    _check_time()
    moves = _gen_moves_np(b)
    if not moves:
        return -WIN
    moves = _order_moves_np(b, moves)
    if len(moves) > 15 and depth > 1:
        moves = moves[:15]
    best = -INF
    for m in moves:
        nb = _do_move_np(b, m)
        if _is_connected_np(nb, 1):
            score = WIN + depth
        elif _is_connected_np(nb, -1):
            score = -WIN - depth
        else:
            if depth <= 1:
                # static eval from opponent view then negate
                # inline to avoid extra call overhead: compute negated?
                # we flip board
                nb2 = -nb
                s = _static_eval_np(nb2)
                # win-in-1 quiescence for side to move if close
                # quick check: if s is high for opponent but not WIN, see if opponent wins in 1
                # only if components small to save time: check via cheap condition
                # we approximate by checking if s > 0 and opponent close
                # To keep fast, only do extra win check when s > -200 (not losing badly)
                # Actually check win in 1 when opponent seemingly close: we detect via s?
                # Simpler: if nb2 close (we can check own comp<=2 via analyze? too heavy)
                # Do direct win-in-1 search limited:
                if s > -500 and s < WIN:
                    # quick win-in-1: generate opponent winning move?
                    # generate moves for nb2 and test connection (only if few pieces?)
                    # limit cost: only if number of opponent pieces <=12 (always) but check comp?
                    # We do a cheap attempt: generate moves and test
                    try:
                        omoves = _gen_moves_np(nb2)
                        for om in omoves:
                            ob = _do_move_np(nb2, om)
                            if _is_connected_np(ob, 1):
                                s = WIN
                                break
                    except Exception:
                        pass
                score = -s
            else:
                nb2 = -nb
                score = -_negamax(nb2, depth-1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _first_legal_fallback(board):
    # board as given (list or np), return string or None
    try:
        if _HAS_NP:
            import numpy as _np
            if isinstance(board, _np.ndarray):
                b = board
                ms = _gen_moves_np(b)
                if ms:
                    m = ms[0]
                    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        # list path
        bl = board.tolist() if hasattr(board, "tolist") else board
        ms = _gen_moves_list(bl)
        if ms:
            m = ms[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
    except Exception:
        pass
    return None

def policy(board) -> str:
    global _START, _LIMIT, _NODES
    _START = time.perf_counter()
    _LIMIT = 0.88
    _NODES = 0
    # convert to np
    b = None
    use_np = False
    if _HAS_NP:
        try:
            import numpy as _np
            if isinstance(board, _np.ndarray):
                b = board.astype(_np.int8, copy=False)
                if b.shape != (8, 8):
                    b = _np.array(board, dtype=_np.int8).reshape(8, 8)
            else:
                b = _np.array(board, dtype=_np.int8).reshape(8, 8)
            use_np = True
        except Exception:
            use_np = False
            b = None
    if not use_np:
        # pure list path: greedy + return
        try:
            bl = board.tolist() if hasattr(board, "tolist") else board
            # ensure 8x8 list
            bl = [[int(bl[r][c]) for c in range(8)] for r in range(8)]
            ms = _gen_moves_list(bl)
            if not ms:
                return "0,0:0,0"
            # greedy: evaluate after move with simple heuristic (components/center)
            # quick order: prefer central destinations, non-captures
            def heur(m):
                fr, fc, tr, tc, cap = m
                return abs(tr-3.5)+abs(tc-3.5) + (5 if cap else 0)
            ms_sorted = sorted(ms, key=heur)
            # check immediate win
            for m in ms_sorted:
                nb = [row[:] for row in bl]
                nb[m[0]][m[1]] = 0
                nb[m[2]][m[3]] = 1
                # connectivity check pure
                cnt = sum(1 for r in range(8) for c in range(8) if nb[r][c] == 1)
                if cnt <= 1:
                    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
                # BFS
                sr = sc = -1
                for r in range(8):
                    for c in range(8):
                        if nb[r][c] == 1:
                            sr, sc = r, c
                            break
                    if sr != -1:
                        break
                seen = {(sr, sc)}
                stack = [(sr, sc)]
                sset = {(r, c) for r in range(8) for c in range(8) if nb[r][c] == 1}
                while stack:
                    r, c = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r+dr, c+dc
                            if (nr, nc) in sset and (nr, nc) not in seen:
                                seen.add((nr, nc))
                                stack.append((nr, nc))
                if len(seen) == cnt:
                    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
            m = ms_sorted[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        except Exception:
            try:
                fb = _first_legal_fallback(board)
                if fb:
                    return fb
            except Exception:
                pass
            return "0,0:0,0"
    # numpy path
    try:
        moves = _gen_moves_np(b)
        if not moves:
            return "0,0:0,0"
        if len(moves) == 1:
            m = moves[0]
            return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        moves_ord = _order_moves_np(b, moves)
        # immediate win check first
        for m in moves_ord:
            nb = _do_move_np(b, m)
            if _is_connected_np(nb, 1):
                return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        best_move = moves_ord[0]
        # iterative deepening 1..4
        for depth in (1, 2, 3, 4):
            try:
                alpha = -INF
                beta = INF
                cur_best = best_move
                cur_best_score = -INF
                # re-order each iteration? keep moves_ord
                for m in moves_ord:
                    _check_time()
                    nb = _do_move_np(b, m)
                    if _is_connected_np(nb, 1):
                        return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
                    if _is_connected_np(nb, -1):
                        score = -WIN
                    else:
                        if depth == 1:
                            s = _static_eval_np(-nb)
                            # win-in-1 for opponent penalty
                            if s > -500 and s < WIN:
                                omoves = _gen_moves_np(-nb)
                                for om in omoves:
                                    ob = _do_move_np(-nb, om)
                                    if _is_connected_np(ob, 1):
                                        s = WIN
                                        break
                            score = -s
                        else:
                            score = -_negamax(-nb, depth-1, -beta, -alpha)
                    if score > cur_best_score:
                        cur_best_score = score
                        cur_best = m
                    if score > alpha:
                        alpha = score
                    if alpha >= beta:
                        break
                    if time.perf_counter() - _START > _LIMIT - 0.05:
                        raise _Timeout()
                best_move = cur_best
                # if winning found, return
                if cur_best_score >= WIN - 10:
                    break
                if time.perf_counter() - _START > _LIMIT - 0.15:
                    break
                # reorder for next depth by scores? simple: move best to front
                # re-sort moves_ord putting best first
                if best_move in moves_ord:
                    moves_ord.remove(best_move)
                    moves_ord = [best_move] + moves_ord
            except _Timeout:
                break
        return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
    except _Timeout:
        try:
            fb = _first_legal_fallback(board)
            if fb:
                return fb
        except Exception:
            pass
        return "0,0:0,0"
    except Exception:
        try:
            fb = _first_legal_fallback(board)
            if fb:
                return fb
        except Exception:
            pass
        # last resort: brute scan for any legal via list gen
        try:
            bl = b.tolist() if hasattr(b, "tolist") else board
            ms = _gen_moves_list(bl)
            if ms:
                m = ms[0]
                return f"{m[0]},{m[1]}:{m[2]},{m[3]}"
        except Exception:
            pass
        return "0,0:0,0"
