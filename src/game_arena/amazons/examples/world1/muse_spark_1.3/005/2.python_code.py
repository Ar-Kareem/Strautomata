
import time
import numpy as np
from collections import deque

DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
INF = 10 ** 9

def gen_moves(board, player):
    moves = []
    amazons = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == player:
                amazons.append((r, c))
    for fr, fc in amazons:
        for dr, dc in DIRS:
            r = fr + dr
            c = fc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                tr = r
                tc = c
                for adr, adc in DIRS:
                    ar = tr + adr
                    ac = tc + adc
                    while 0 <= ar < 6 and 0 <= ac < 6:
                        if ar == fr and ac == fc:
                            moves.append((fr, fc, tr, tc, ar, ac))
                        elif board[ar, ac] != 0:
                            break
                        else:
                            moves.append((fr, fc, tr, tc, ar, ac))
                        ar += adr
                        ac += adc
                r += dr
                c += dc
    return moves

def apply_move(board, move):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    pv = nb[fr, fc]
    nb[fr, fc] = 0
    nb[tr, tc] = pv
    nb[ar, ac] = -1
    return nb

def king_dist(board, sources):
    dist = [[-1]*6 for _ in range(6)]
    q = deque()
    for r, c in sources:
        dist[r][c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and dist[nr][nc] == -1:
                if board[nr, nc] == 0:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
    return dist

def evaluate(board, to_move):
    my_pos = []
    opp_pos = []
    empty = 0
    for r in range(6):
        for c in range(6):
            v = board[r, c]
            if v == 0:
                empty += 1
            elif v == 1:
                my_pos.append((r, c))
            elif v == 2:
                opp_pos.append((r, c))
    my_mob = 0
    for fr, fc in my_pos:
        for dr, dc in DIRS:
            r = fr + dr
            c = fc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                my_mob += 1
                r += dr
                c += dc
    opp_mob = 0
    for fr, fc in opp_pos:
        for dr, dc in DIRS:
            r = fr + dr
            c = fc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                opp_mob += 1
                r += dr
                c += dc
    if to_move == 2 and opp_mob == 0:
        return INF
    if to_move == 1 and my_mob == 0:
        return -INF
    ds = king_dist(board, my_pos)
    do = king_dist(board, opp_pos)
    terr = 0
    for r in range(6):
        for c in range(6):
            if board[r, c] != 0:
                continue
            a = ds[r][c]
            b = do[r][c]
            if a == -1 and b == -1:
                continue
            elif a == -1:
                terr -= 1
            elif b == -1:
                terr += 1
            elif a < b:
                terr += 1
            elif b < a:
                terr -= 1
    fill = 1.0 - (empty / 36.0)
    w_terr = 0.8 + 1.2 * fill
    mob_diff = my_mob - opp_mob
    c_my = 0.0
    for r, c in my_pos:
        c_my += abs(r - 2.5) + abs(c - 2.5)
    c_opp = 0.0
    for r, c in opp_pos:
        c_opp += abs(r - 2.5) + abs(c - 2.5)
    center = (c_opp - c_my) * 0.15
    return mob_diff * 1.0 + terr * w_terr + center

def first_legal_move(board, player):
    for fr in range(6):
        for fc in range(6):
            if board[fr, fc] != player:
                continue
            for dr, dc in DIRS:
                r = fr + dr
                c = fc + dc
                while 0 <= r < 6 and 0 <= c < 6 and board[r, c] == 0:
                    tr, tc = r, c
                    for adr, adc in DIRS:
                        ar = tr + adr
                        ac = tc + adc
                        while 0 <= ar < 6 and 0 <= ac < 6:
                            if ar == fr and ac == fc:
                                return (fr, fc, tr, tc, ar, ac)
                            elif board[ar, ac] != 0:
                                break
                            else:
                                return (fr, fc, tr, tc, ar, ac)
                            ar += adr
                            ac += adc
                    r += dr
                    c += dc
    return None

def fmt(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"

def is_legal(board, m):
    try:
        fr, fc, tr, tc, ar, ac = m
        if not (0 <= fr < 6 and 0 <= fc < 6 and 0 <= tr < 6 and 0 <= tc < 6 and 0 <= ar < 6 and 0 <= ac < 6):
            return False
        if board[fr, fc] != 1:
            return False
        if board[tr, tc] != 0:
            return False
        dr = tr - fr
        dc = tc - fc
        if dr == 0 and dc == 0:
            return False
        if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
            return False
        sdr = (dr > 0) - (dr < 0)
        sdc = (dc > 0) - (dc < 0)
        r, c = fr + sdr, fc + sdc
        while (r, c) != (tr, tc):
            if board[r, c] != 0:
                return False
            r += sdr
            c += sdc
        # arrow check on board after move
        # path must be clear in tmp
        # tmp has from empty, to occupied
        dr2 = ar - tr
        dc2 = ac - tc
        if dr2 == 0 and dc2 == 0:
            return False
        if not (dr2 == 0 or dc2 == 0 or abs(dr2) == abs(dc2)):
            return False
        sdr2 = (dr2 > 0) - (dr2 < 0)
        sdc2 = (dc2 > 0) - (dc2 < 0)
        r, c = tr + sdr2, tc + sdc2
        while True:
            if r == ar and c == ac:
                # destination must be empty after move
                if (r == fr and c == fc):
                    return True
                if board[r, c] != 0:
                    return False
                return True
            # intermediate squares
            if (r == fr and c == fc):
                pass
            elif board[r, c] != 0:
                return False
            r += sdr2
            c += sdc2
            if not (0 <= r < 6 and 0 <= c < 6):
                return False
    except Exception:
        return False
    return False

def policy(board) -> str:
    try:
        start = time.time()
        limit = 0.90
        b = np.asarray(board)
        # ensure 6x6
        moves = gen_moves(b, 1)
        if not moves:
            return "0,0:0,0:0,0"
        if len(moves) == 1:
            m = moves[0]
            if is_legal(b, m):
                return fmt(m)
            fl = first_legal_move(b, 1)
            if fl is not None:
                return fmt(fl)
            return fmt(m)
        # 1-ply
        scored = []
        for m in moves:
            nb = apply_move(b, m)
            s = evaluate(nb, 2)
            scored.append((s, m, nb))
            if s >= INF // 2:
                return fmt(m)
            if time.time() - start > limit - 0.02:
                break
        # if timed out during 1-ply, return best so far
        if len(scored) != len(moves):
            # partial scoring, pick best among scored
            scored.sort(key=lambda x: x[0], reverse=True)
            bm = scored[0][1]
            if is_legal(b, bm):
                return fmt(bm)
            fl = first_legal_move(b, 1)
            if fl is not None:
                return fmt(fl)
            return fmt(moves[0])
        scored.sort(key=lambda x: x[0], reverse=True)
        best_static_move = scored[0][1]
        n = len(moves)
        time_left = limit - (time.time() - start)
        if time_left < 0.05:
            return fmt(best_static_move)
        # large branching: selective 2-ply
        if n > 50:
            if n > 200:
                K = 8
            elif n > 120:
                K = 12
            else:
                K = 15
            K = min(K, n)
            alpha = -10**18
            best_move = best_static_move
            for idx in range(K):
                if time.time() - start > limit - 0.05:
                    break
                _, m, b2 = scored[idx]
                opp_moves = gen_moves(b2, 2)
                if not opp_moves:
                    return fmt(m)
                # my positions in b2 for ordering
                my_p = []
                for r in range(6):
                    for c in range(6):
                        if b2[r, c] == 1:
                            my_p.append((r, c))
                # order / truncate
                if len(opp_moves) > 80:
                    tmp = []
                    for om in opp_moves:
                        ar, ac = om[4], om[5]
                        dmin = 20
                        for pr, pc in my_p:
                            d = abs(ar - pr)
                            dd = abs(ac - pc)
                            if dd > d:
                                d = dd
                            if d < dmin:
                                dmin = d
                                if dmin == 0:
                                    break
                        tmp.append((dmin, om))
                    tmp.sort(key=lambda x: x[0])
                    ordered = [om for _, om in tmp[:60]]
                else:
                    # order all by proximity
                    tmp = []
                    for om in opp_moves:
                        ar, ac = om[4], om[5]
                        dmin = 20
                        for pr, pc in my_p:
                            d = abs(ar - pr)
                            dd = abs(ac - pc)
                            if dd > d:
                                d = dd
                            if d < dmin:
                                dmin = d
                                if dmin == 0:
                                    break
                        tmp.append((dmin, om))
                    tmp.sort(key=lambda x: x[0])
                    ordered = [om for _, om in tmp]
                worst = 10**18
                cnt = 0
                for om in ordered:
                    b3 = apply_move(b2, om)
                    v = evaluate(b3, 1)
                    if v < worst:
                        worst = v
                        if worst <= alpha:
                            break
                    cnt += 1
                    if cnt % 16 == 0 and time.time() - start > limit - 0.02:
                        break
                if worst > alpha:
                    alpha = worst
                    best_move = m
            if is_legal(b, best_move):
                return fmt(best_move)
            fl = first_legal_move(b, 1)
            if fl is not None:
                return fmt(fl)
            return fmt(best_static_move)
        else:
            # small branching: full alpha-beta
            if n <= 12:
                depth = 4
            elif n <= 25:
                depth = 3
            else:
                depth = 2
            # root ordering already sorted (scored)
            # time-aware recursive search
            nodes = [0]
            def check_timeout():
                nodes[0] += 1
                if nodes[0] % 64 == 0 and time.time() - start > limit - 0.03:
                    raise TimeoutError()
            def alphabeta(cur, d, alpha_, beta_, to_move):
                check_timeout()
                if d == 0:
                    return evaluate(cur, to_move)
                player = 1 if to_move == 1 else 2
                ms = gen_moves(cur, player)
                if not ms:
                    return -INF if to_move == 1 else INF
                # positions for ordering
                if player == 1:
                    # opponent is 2
                    opp_p = []
                    for r in range(6):
                        for c in range(6):
                            if cur[r, c] == 2:
                                opp_p.append((r, c))
                else:
                    opp_p = []
                    for r in range(6):
                        for c in range(6):
                            if cur[r, c] == 1:
                                opp_p.append((r, c))
                if opp_p:
                    tmp2 = []
                    for om in ms:
                        ar, ac = om[4], om[5]
                        dmin = 20
                        for pr, pc in opp_p:
                            dd = abs(ar - pr)
                            dd2 = abs(ac - pc)
                            if dd2 > dd:
                                dd = dd2
                            if dd < dmin:
                                dmin = dd
                                if dmin == 0:
                                    break
                        tmp2.append((dmin, om))
                    tmp2.sort(key=lambda x: x[0])
                    ms = [om for _, om in tmp2]
                    # truncate deep levels if huge
                    if d > 2 and len(ms) > 40:
                        ms = ms[:40]
                if to_move == 1:
                    v = -INF
                    for om in ms:
                        b2 = apply_move(cur, om)
                        q = alphabeta(b2, d - 1, alpha_, beta_, 2)
                        if q > v:
                            v = q
                        if q > alpha_:
                            alpha_ = q
                        if alpha_ >= beta_:
                            break
                    return v
                else:
                    v = INF
                    for om in ms:
                        b2 = apply_move(cur, om)
                        q = alphabeta(b2, d - 1, alpha_, beta_, 1)
                        if q < v:
                            v = q
                        if q < beta_:
                            beta_ = q
                        if alpha_ >= beta_:
                            break
                    return v
            best_move = best_static_move
            alpha = -INF
            beta = INF
            try:
                # if depth==2 we already have static, but do full minimax for accuracy
                for _, m, b2 in scored:
                    if time.time() - start > limit - 0.05:
                        break
                    if depth == 1:
                        v = evaluate(b2, 2)
                    else:
                        v = alphabeta(b2, depth - 1, alpha, beta, 2)
                    if v > alpha:
                        alpha = v
                        best_move = m
                    # immediate win
                    if v >= INF // 2:
                        best_move = m
                        break
            except TimeoutError:
                pass
            if is_legal(b, best_move):
                return fmt(best_move)
            fl = first_legal_move(b, 1)
            if fl is not None:
                return fmt(fl)
            return fmt(best_static_move)
    except Exception:
        try:
            bb = np.asarray(board)
            fl = first_legal_move(bb, 1)
            if fl is not None:
                return fmt(fl)
        except Exception:
            pass
        return "0,0:0,1:0,2"
