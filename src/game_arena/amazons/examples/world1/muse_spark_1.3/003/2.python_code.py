
import time
from collections import deque
try:
    import numpy as np
except:
    np = None

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def _gen_moves(board, player):
    moves = []
    D = DIRS
    for fr, v in enumerate(board):
        if v != player:
            continue
        r = fr // 6
        c = fr % 6
        for dr, dc in D:
            nr = r + dr
            nc = c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                to = nr * 6 + nc
                if board[to] != 0:
                    break
                tr = nr
                tc = nc
                for adr, adc in D:
                    ar = tr + adr
                    ac = tc + adc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        ai = ar * 6 + ac
                        if ai == fr:
                            moves.append((fr, to, ai))
                            ar += adr
                            ac += adc
                            continue
                        if board[ai] != 0:
                            break
                        moves.append((fr, to, ai))
                        ar += adr
                        ac += adc
                nr += dr
                nc += dc
    return moves

def _mobility_counts(board):
    mob_my = 0
    mob_opp = 0
    trap_my = 0
    trap_opp = 0
    D = DIRS
    for i, v in enumerate(board):
        if v != 1 and v != 2:
            continue
        r = i // 6
        c = i % 6
        cnt = 0
        for dr, dc in D:
            nr = r + dr
            nc = c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr*6+nc] == 0:
                cnt += 1
                nr += dr
                nc += dc
        if v == 1:
            mob_my += cnt
            if cnt == 0:
                trap_my += 1
        else:
            mob_opp += cnt
            if cnt == 0:
                trap_opp += 1
    return mob_my, mob_opp, trap_my, trap_opp

def _king_dists(board, starts):
    INF = 999
    dist = [INF]*36
    q = deque()
    for s in starts:
        if dist[s] != 0:
            dist[s] = 0
            q.append(s)
    D = DIRS
    while q:
        cur = q.popleft()
        dc = dist[cur]
        nd = dc + 1
        r = cur // 6
        c = cur % 6
        for dr, dcc in D:
            nr = r + dr
            nc = c + dcc
            if 0 <= nr < 6 and 0 <= nc < 6:
                ni = nr*6+nc
                if board[ni] == -1:
                    continue
                if dist[ni] != INF:
                    continue
                dist[ni] = nd
                q.append(ni)
    return dist

def _queen_dists(board, starts):
    INF = 999
    dist = [INF]*36
    q = deque()
    for s in starts:
        if dist[s] != 0:
            dist[s] = 0
            q.append(s)
    D = DIRS
    while q:
        cur = q.popleft()
        dc = dist[cur]
        nd = dc + 1
        r = cur // 6
        c = cur % 6
        for dr, dcc in D:
            nr = r + dr
            nc = c + dcc
            while 0 <= nr < 6 and 0 <= nc < 6:
                ni = nr*6+nc
                if board[ni] == -1:
                    break
                if dist[ni] == INF:
                    dist[ni] = nd
                    q.append(ni)
                nr += dr
                nc += dcc
    return dist

def _split(board):
    my = []
    opp = []
    empty = []
    for i, v in enumerate(board):
        if v == 1:
            my.append(i)
        elif v == 2:
            opp.append(i)
        elif v == 0:
            empty.append(i)
    return my, opp, empty

def _fast_eval(board):
    mob_my, mob_opp, trap_my, trap_opp = _mobility_counts(board)
    my, opp, empty = _split(board)
    if not my or not opp:
        return float(mob_my - mob_opp)*1.0 + float(trap_opp - trap_my)*8.0
    dm = _king_dists(board, my)
    do = _king_dists(board, opp)
    terr = 0
    for i in empty:
        a = dm[i]; b = do[i]
        if a < b:
            terr += 1
        elif a > b:
            terr -= 1
    n = len(empty)
    if n > 20:
        WT = 3.0; WM = 0.3
    elif n > 12:
        WT = 2.0; WM = 0.8
    else:
        WT = 1.0; WM = 1.5
    return terr*WT + (mob_my-mob_opp)*WM + (trap_opp-trap_my)*8.0

def _full_eval(board):
    mob_my, mob_opp, trap_my, trap_opp = _mobility_counts(board)
    my, opp, empty = _split(board)
    n = len(empty)
    if not my or not opp:
        return float(mob_my - mob_opp)*2.0 + float(trap_opp - trap_my)*10.0 + float(len(my)-len(opp))*50.0
    if n > 14:
        dm = _queen_dists(board, my)
        do = _queen_dists(board, opp)
    else:
        dm = _king_dists(board, my)
        do = _king_dists(board, opp)
    terr = 0
    for i in empty:
        a = dm[i]; b = do[i]
        if a < b:
            terr += 1
        elif a > b:
            terr -= 1
    if n > 20:
        WT = 3.0; WM = 0.3
    elif n > 12:
        WT = 2.0; WM = 0.8
    else:
        WT = 1.0; WM = 1.5
    return terr*WT + (mob_my-mob_opp)*WM + (trap_opp-trap_my)*8.0

def _fmt(fr, to, ar):
    return f"{fr//6},{fr%6}:{to//6},{to%6}:{ar//6},{ar%6}"

def _first_legal(board):
    for fr, v in enumerate(board):
        if v != 1:
            continue
        r = fr//6; c = fr%6
        for dr, dc in DIRS:
            nr = r+dr; nc = c+dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                to = nr*6+nc
                if board[to] != 0:
                    break
                tr = nr; tc = nc
                for adr, adc in DIRS:
                    ar = tr+adr; ac = tc+adc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        ai = ar*6+ac
                        if ai == fr:
                            return _fmt(fr, to, ai)
                        if board[ai] != 0:
                            break
                        return _fmt(fr, to, ai)
                        ar += adr; ac += adc
                        break
                    else:
                        continue
                    break
                nr += dr; nc += dc
    return "0,0:0,1:0,2"

def policy(board) -> str:
    t0 = time.perf_counter()
    deadline = t0 + 0.88
    try:
        if np is not None and hasattr(board, "flatten"):
            try:
                flat = [int(x) for x in board.flatten().tolist()]
            except:
                flat = [int(board[r, c]) for r in range(6) for c in range(6)]
        else:
            try:
                flat = [int(board[r][c]) for r in range(6) for c in range(6)]
            except:
                flat = [int(x) for x in list(board)]
                if len(flat) != 36:
                    return "0,0:0,1:0,2"
        if len(flat) != 36:
            return "0,0:0,1:0,2"
        my_moves = _gen_moves(flat, 1)
        if not my_moves:
            return "0,0:0,1:0,2"
        if len(my_moves) == 1:
            fr, to, ar = my_moves[0]
            return _fmt(fr, to, ar)
        # order by fast eval
        scored = []
        for fr, to, ar in my_moves:
            nb = flat.copy()
            nb[fr] = 0
            nb[to] = 1
            nb[ar] = -1
            try:
                s = _fast_eval(nb)
            except:
                s = 0.0
            scored.append((s, fr, to, ar, nb))
            if time.perf_counter() > deadline - 0.35 and len(scored) < len(my_moves):
                # time pressure during ordering: break and use what we have + fallback
                # fill remaining with 0 score to avoid missing all moves
                # instead continue with cheap fallback ordering
                pass
        scored.sort(key=lambda x: x[0], reverse=True)
        L = len(scored)
        if L > 400:
            K = 12
        elif L > 250:
            K = 16
        elif L > 150:
            K = 20
        elif L > 80:
            K = 26
        elif L > 40:
            K = 32
        else:
            K = min(L, 40)
        cands = scored[:K]
        best = cands[0]
        best_move = (best[1], best[2], best[3])
        # quick immediate win check using full gen already? will be found in loop
        best_val = -1e18
        # if very little time, just return top fast move
        for s, fr, to, ar, nb in cands:
            if time.perf_counter() > deadline:
                break
            opp_moves = _gen_moves(nb, 2)
            if not opp_moves:
                return _fmt(fr, to, ar)
            cur_min = 1e18
            # iterate opponent moves
            for ofr, oto, oar in opp_moves:
                nb2 = nb.copy()
                nb2[ofr] = 0
                nb2[oto] = 2
                nb2[oar] = -1
                try:
                    v = _full_eval(nb2)
                except:
                    v = s
                if v < cur_min:
                    cur_min = v
                    if cur_min <= best_val:
                        break
                if time.perf_counter() > deadline:
                    break
            if cur_min > best_val:
                best_val = cur_min
                best_move = (fr, to, ar)
                # early exit if time low
                if time.perf_counter() > deadline:
                    break
        return _fmt(best_move[0], best_move[1], best_move[2])
    except Exception:
        try:
            if np is not None and hasattr(board, "flatten"):
                flat2 = [int(x) for x in board.flatten().tolist()]
            else:
                flat2 = [int(board[r][c]) for r in range(6) for c in range(6)]
            m = _gen_moves(flat2, 1)
            if m:
                return _fmt(m[0][0], m[0][1], m[0][2])
            return _first_legal(flat2)
        except:
            return "0,0:0,1:0,2"
