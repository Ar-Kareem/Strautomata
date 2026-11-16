
import time

_DIRS = []
for _dx in (-1,0,1):
    for _dy in (-1,0,1):
        for _dz in (-1,0,1):
            if _dx==0 and _dy==0 and _dz==0:
                continue
            _DIRS.append((_dx,_dy,_dz))

_LINES_SET = set()
for _x in range(3):
    for _y in range(3):
        for _z in range(3):
            for _dx,_dy,_dz in _DIRS:
                _x2=_x+_dx; _y2=_y+_dy; _z2=_z+_dz
                _x3=_x+2*_dx; _y3=_y+2*_dy; _z3=_z+2*_dz
                if 0<=_x2<3 and 0<=_y2<3 and 0<=_z2<3 and 0<=_x3<3 and 0<=_y3<3 and 0<=_z3<3:
                    _a=_x*9+_y*3+_z
                    _b=_x2*9+_y2*3+_z2
                    _c=_x3*9+_y3*3+_z3
                    _t=tuple(sorted((_a,_b,_c)))
                    _LINES_SET.add(_t)
LINES = list(_LINES_SET)
NLINES = len(LINES)
CELL_LINES = [[] for _ in range(27)]
for _li, (_a,_b,_c) in enumerate(LINES):
    CELL_LINES[_a].append(_li)
    CELL_LINES[_b].append(_li)
    CELL_LINES[_c].append(_li)
CELL_COUNT = [len(c) for c in CELL_LINES]

INF = 1000000

class _Timeout(Exception):
    pass

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        start = time.time()
        TIME_LIMIT = 0.85
        flat = [0]*27
        for i in range(3):
            bi = board[i]
            for j in range(3):
                bj = bi[j]
                base = i*9+j*3
                flat[base+0] = bj[0]
                flat[base+1] = bj[1]
                flat[base+2] = bj[2]
        empties_init = [idx for idx, v in enumerate(flat) if v == 0]
        n_empty = len(empties_init)
        if n_empty == 0:
            return (0,0,0)
        if n_empty == 27:
            return (1,1,1)
        if flat[13] == 0:
            return (1,1,1)
        # second player vs center opening: take a corner
        if n_empty == 26 and flat[13] == -1:
            return (0,0,0)

        # immediate win / block via line sums
        # sum 2 => 1,1,0 ; sum -2 => -1,-1,0
        win_us = []
        win_opp = []
        # also build line counts for search
        lu = [0]*NLINES
        lo = [0]*NLINES
        for li, (a,b,c) in enumerate(LINES):
            va = flat[a]; vb = flat[b]; vc = flat[c]
            cu = (va==1)+(vb==1)+(vc==1)
            co = (va==-1)+(vb==-1)+(vc==-1)
            lu[li]=cu
            lo[li]=co
            s = va+vb+vc
            if s == 2:
                # find empty
                if va==0: win_us.append(a)
                elif vb==0: win_us.append(b)
                else: win_us.append(c)
            elif s == -2:
                if va==0: win_opp.append(a)
                elif vb==0: win_opp.append(b)
                else: win_opp.append(c)
        if win_us:
            idx = win_us[0]
            return (idx//9, (idx%9)//3, idx%3)
        if win_opp:
            # if single cell blocks all, block it; if multiple, lost but block one
            # dedup
            uniq = list(dict.fromkeys(win_opp))
            idx = uniq[0]
            # if only one distinct cell, that's forced block
            # if more than one, still return one (no single block saves)
            return (idx//9, (idx%9)//3, idx%3)

        # fallback legal
        fallback_idx = empties_init[0]

        _cell_lines = CELL_LINES
        _cell_count = CELL_COUNT
        nodes = [0]

        def check_timeout():
            if nodes[0] % 2048 == 0:
                if time.time() - start > TIME_LIMIT:
                    raise _Timeout()

        def evaluate():
            s = 0
            # line potentials
            for li in range(NLINES):
                u = lu[li]; o = lo[li]
                if u:
                    if o:
                        continue
                    if u == 2:
                        s += 100
                    elif u == 1:
                        s += 1
                    else:
                        s += 10000
                else:
                    if o:
                        if o == 2:
                            s -= 120
                        elif o == 1:
                            s -= 2
                        else:
                            s -= 10000
            # small positional bonus
            # iterate flat
            for idx, v in enumerate(flat):
                if v == 1:
                    s += _cell_count[idx]*0.05
                elif v == -1:
                    s -= _cell_count[idx]*0.05
            return s

        def ordered_indices(turn, max_depth_cur, depth_left):
            scored = []
            for idx in empties_init:
                if flat[idx] != 0:
                    continue
                sc = 0
                cls = _cell_lines[idx]
                if turn == 1:
                    for li in cls:
                        u = lu[li]; o = lo[li]
                        if u and o:
                            continue
                        if o == 0:
                            if u == 2:
                                sc += 1000
                            elif u == 1:
                                sc += 12
                            else:
                                sc += 2
                        else:
                            # u==0
                            if o == 2:
                                sc += 900
                            elif o == 1:
                                sc += 6
                            else:
                                sc += 0
                else:
                    for li in cls:
                        u = lu[li]; o = lo[li]
                        if u and o:
                            continue
                        if u == 0:
                            if o == 2:
                                sc += 1000
                            elif o == 1:
                                sc += 12
                            else:
                                sc += 2
                        else:
                            if u == 2:
                                sc += 900
                            elif u == 1:
                                sc += 6
                sc += _cell_count[idx]*0.2
                scored.append((sc, idx))
            scored.sort(key=lambda x: x[0], reverse=True)
            # beam pruning for large branching, keep full in endgame
            if n_empty > 10 and len(scored) > 12 and depth_left < max_depth_cur:
                # keep top 12, but keep a bit more near root
                if depth_left < max_depth_cur - 1:
                    scored = scored[:10]
                else:
                    scored = scored[:12]
            return [idx for _, idx in scored]

        # recursive alpha-beta, score from perspective of us (1)
        def search(depth, alpha, beta, turn):
            nodes[0] += 1
            check_timeout()
            if depth == 0:
                return evaluate()
            moves = ordered_indices(turn, cur_depth, depth)
            if not moves:
                return evaluate()
            if turn == 1:
                best = -INF
                for idx in moves:
                    flat[idx] = 1
                    win = False
                    for li in _cell_lines[idx]:
                        lu[li] += 1
                        if lu[li] == 3:
                            win = True
                    if win:
                        for li in _cell_lines[idx]:
                            lu[li] -= 1
                        flat[idx] = 0
                        return INF - (cur_depth - depth)
                    val = search(depth-1, alpha, beta, -1)
                    for li in _cell_lines[idx]:
                        lu[li] -= 1
                    flat[idx] = 0
                    if val > best:
                        best = val
                    if best >= beta:
                        return best
                    if best > alpha:
                        alpha = best
                return best
            else:
                best = INF
                for idx in moves:
                    flat[idx] = -1
                    win = False
                    for li in _cell_lines[idx]:
                        lo[li] += 1
                        if lo[li] == 3:
                            win = True
                    if win:
                        for li in _cell_lines[idx]:
                            lo[li] -= 1
                        flat[idx] = 0
                        return -INF + (cur_depth - depth)
                    val = search(depth-1, alpha, beta, 1)
                    for li in _cell_lines[idx]:
                        lo[li] -= 1
                    flat[idx] = 0
                    if val < best:
                        best = val
                    if best <= alpha:
                        return best
                    if best < beta:
                        beta = best
                return best

        # root ordering
        root_moves = ordered_indices(1, 100, 100)
        if not root_moves:
            idx = fallback_idx
            return (idx//9, (idx%9)//3, idx%3)
        best_move = root_moves[0]

        # decide max depth to attempt
        # early game: limit, endgame: allow deep solve
        if n_empty > 20:
            max_try = 3
        elif n_empty > 14:
            max_try = 4
        elif n_empty > 10:
            max_try = 5
        else:
            max_try = n_empty

        # iterative deepening
        cur_depth = 1
        try:
            for d in range(1, max_try+1):
                cur_depth = d
                alpha = -INF
                beta = INF
                local_best = best_move
                local_best_score = -INF
                # re-order root each iteration? keep order but update
                # try moves in order of previous best first
                # move current best to front
                if local_best in root_moves:
                    root_moves.remove(local_best)
                    root_moves.insert(0, local_best)
                for idx in root_moves:
                    check_timeout()
                    flat[idx] = 1
                    win = False
                    for li in _cell_lines[idx]:
                        lu[li] += 1
                        if lu[li] == 3:
                            win = True
                    if win:
                        for li in _cell_lines[idx]:
                            lu[li] -= 1
                        flat[idx] = 0
                        return (idx//9, (idx%9)//3, idx%3)
                    if d == 1:
                        val = evaluate()
                        # quick tie-break by ordering already
                    else:
                        val = search(d-1, alpha, beta, -1)
                    for li in _cell_lines[idx]:
                        lu[li] -= 1
                    flat[idx] = 0
                    if val > local_best_score:
                        local_best_score = val
                        local_best = idx
                    if val > alpha:
                        alpha = val
                    if time.time() - start > TIME_LIMIT:
                        raise _Timeout()
                best_move = local_best
                # if found forced win, stop
                if local_best_score >= INF - 100:
                    break
                if time.time() - start > TIME_LIMIT:
                    break
                # update root order by scores? simple: keep best first for next iter
                # re-compute ordering for next depth
                # (keep best_move front)
        except _Timeout:
            pass

        idx = best_move
        if flat[idx] != 0:
            # safety: pick first empty
            for e in empties_init:
                if flat[e]==0:
                    idx=e
                    break
        return (idx//9, (idx%9)//3, idx%3)
    except Exception:
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k]==0:
                            return (i,j,k)
        except Exception:
            pass
        return (0,0,0)
