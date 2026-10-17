
import time
import random

_rng = random.Random(987654321)
ZOB = [[0, _rng.getrandbits(64), _rng.getrandbits(64)] for _ in range(64)]
SIDE_KEY = _rng.getrandbits(64)

ADV1 = [0, 2, 5, 9, 15, 24, 40, 0]
ADV2 = [0, 40, 24, 15, 9, 5, 2, 0]

WIN = 100000
RACE = 20000
INF = 10 ** 9

WIN_MASK = [[0] * 8 for _ in range(8)]
for _lim in range(8):
    for _c in range(8):
        _m = 0
        for _x in range(max(0, _c - _lim), min(7, _c + _lim) + 1):
            _m |= 1 << _x
        WIN_MASK[_lim][_c] = _m
DIAG_MASK = [0] * 8
for _c in range(8):
    _m = 0
    if _c > 0:
        _m |= 1 << (_c - 1)
    if _c < 7:
        _m |= 1 << (_c + 1)
    DIAG_MASK[_c] = _m


class TimeUp(Exception):
    pass


def policy(me, opp, color):
    start = time.perf_counter()
    deadline = start + 0.72
    flip = (color == 'b')
    board = [0] * 64
    for r, c in me:
        if flip:
            r = 7 - r
        board[r * 8 + c] = 1
    for r, c in opp:
        if flip:
            r = 7 - r
        board[r * 8 + c] = 2
    cnt = [0, len(me), len(opp)]

    def to_move(m):
        f, t = m
        fr, fc = f >> 3, f & 7
        tr, tc = t >> 3, t & 7
        if flip:
            fr = 7 - fr
            tr = 7 - tr
        return ((fr, fc), (tr, tc))

    def gen_moves(side):
        moves = []
        if side == 1:
            for sq in range(56):
                if board[sq] == 1:
                    c = sq & 7
                    t = sq + 8
                    if board[t] == 0:
                        moves.append((sq, t))
                    if c > 0 and board[t - 1] != 1:
                        moves.append((sq, t - 1))
                    if c < 7 and board[t + 1] != 1:
                        moves.append((sq, t + 1))
        else:
            for sq in range(8, 64):
                if board[sq] == 2:
                    c = sq & 7
                    t = sq - 8
                    if board[t] == 0:
                        moves.append((sq, t))
                    if c > 0 and board[t - 1] != 2:
                        moves.append((sq, t - 1))
                    if c < 7 and board[t + 1] != 2:
                        moves.append((sq, t + 1))
        return moves

    root_moves = gen_moves(1)
    if not root_moves:
        if me:
            r, c = me[0]
            return ((r, c), (r + (1 if color == 'w' else -1), c))
        return ((0, 0), (1, 0))
    for m in root_moves:
        if m[1] >= 56:
            return to_move(m)
        if board[m[1]] == 2 and cnt[2] == 1:
            return to_move(m)
    if len(root_moves) == 1:
        return to_move(root_moves[0])

    def evaluate(side):
        rm1 = [0] * 8
        rm2 = [0] * 8
        my = []
        op = []
        for sq in range(64):
            p = board[sq]
            if p == 1:
                my.append(sq)
                rm1[sq >> 3] |= 1 << (sq & 7)
            elif p == 2:
                op.append(sq)
                rm2[sq >> 3] |= 1 << (sq & 7)
        s = (len(my) - len(op)) * 100
        my_d = 99
        op_d = 99
        hang_me = 60 if side == 2 else 25
        hang_op = 60 if side == 1 else 25
        for sq in my:
            r = sq >> 3
            c = sq & 7
            s += ADV1[r]
            prot = r > 0 and ((c > 0 and board[sq - 9] == 1) or (c < 7 and board[sq - 7] == 1))
            att = r < 7 and ((c > 0 and board[sq + 7] == 2) or (c < 7 and board[sq + 9] == 2))
            if att and not prot:
                s -= hang_me
            if prot:
                s += 5
            if r == 0:
                s += 6
            if r < 7 and board[sq + 8] != 1 and 7 - r < my_d:
                free = True
                if side == 1:
                    for R in range(r + 1, 8):
                        if rm2[R] & WIN_MASK[(R - r) >> 1][c]:
                            free = False
                            break
                else:
                    if rm2[r + 1] & DIAG_MASK[c]:
                        free = False
                    else:
                        for R in range(r + 2, 8):
                            if rm2[R] & WIN_MASK[((R - r - 1) >> 1) + 1][c]:
                                free = False
                                break
                if free:
                    my_d = 7 - r
        for sq in op:
            r = sq >> 3
            c = sq & 7
            s -= ADV2[r]
            prot = r < 7 and ((c > 0 and board[sq + 7] == 2) or (c < 7 and board[sq + 9] == 2))
            att = r > 0 and ((c > 0 and board[sq - 9] == 1) or (c < 7 and board[sq - 7] == 1))
            if att and not prot:
                s += hang_op
            if prot:
                s -= 5
            if r == 7:
                s -= 6
            if r > 0 and board[sq - 8] != 2 and r < op_d:
                free = True
                if side == 2:
                    for R in range(r - 1, -1, -1):
                        if rm1[R] & WIN_MASK[(r - R) >> 1][c]:
                            free = False
                            break
                else:
                    if rm1[r - 1] & DIAG_MASK[c]:
                        free = False
                    else:
                        for R in range(r - 2, -1, -1):
                            if rm1[R] & WIN_MASK[((r - R - 1) >> 1) + 1][c]:
                                free = False
                                break
                if free:
                    op_d = r
        if my_d < 99 or op_d < 99:
            if side == 1:
                if my_d <= op_d:
                    s += RACE - my_d * 100
                else:
                    s -= RACE - op_d * 100
            else:
                if op_d <= my_d:
                    s -= RACE - op_d * 100
                else:
                    s += RACE - my_d * 100
        return s if side == 1 else -s

    TT = {}
    nodes = [0]
    h0 = 0
    for sq in range(64):
        if board[sq]:
            h0 ^= ZOB[sq][board[sq]]
    hsh = [h0]

    def negamax(depth, alpha, beta, side, ply):
        nodes[0] += 1
        if (nodes[0] & 255) == 0 and time.perf_counter() > deadline:
            raise TimeUp
        h = hsh[0] ^ (SIDE_KEY if side == 2 else 0)
        tt = TT.get(h)
        ttm = None
        if tt is not None:
            td, ts, tf, ttm = tt
            if td >= depth:
                if tf == 0:
                    return ts
                if tf == 1 and ts >= beta:
                    return ts
                if tf == 2 and ts <= alpha:
                    return ts
        moves = gen_moves(side)
        if not moves:
            return -WIN + ply
        if side == 1:
            for m in moves:
                if m[1] >= 56:
                    return WIN - ply
        else:
            for m in moves:
                if m[1] < 8:
                    return WIN - ply
        if depth <= 0:
            return evaluate(side)
        opp_side = 3 - side
        scored = []
        for m in moves:
            t = m[1]
            tr = t >> 3
            adv = tr if side == 1 else 7 - tr
            if board[t] == opp_side:
                k = 1000 + adv * 10
            else:
                k = adv
            if m == ttm:
                k += 100000
            scored.append((k, m))
        scored.sort(reverse=True)
        best = -INF
        bestm = None
        a = alpha
        for k, m in scored:
            f, t = m
            cap = board[t]
            board[f] = 0
            board[t] = side
            hh = hsh[0]
            nh = hh ^ ZOB[f][side] ^ ZOB[t][side]
            if cap:
                nh ^= ZOB[t][cap]
            hsh[0] = nh
            if cap:
                cnt[cap] -= 1
                if cnt[cap] == 0:
                    sc = WIN - ply
                else:
                    sc = -negamax(depth - 1, -beta, -a, opp_side, ply + 1)
                cnt[cap] += 1
            else:
                sc = -negamax(depth - 1, -beta, -a, opp_side, ply + 1)
            board[f] = side
            board[t] = cap
            hsh[0] = hh
            if sc > best:
                best = sc
                bestm = m
                if sc > a:
                    a = sc
                    if a >= beta:
                        break
        if best <= alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        TT[h] = (depth, best, flag, bestm)
        return best

    # initial root ordering: captures first, then advancement
    def root_key(m):
        t = m[1]
        k = t >> 3
        if board[t] == 2:
            k += 1000
        return k

    ordered = sorted(root_moves, key=root_key, reverse=True)
    best_move = ordered[0]
    try:
        for depth in range(1, 40):
            scores = []
            a = -INF
            cur_best = None
            cur_score = -INF
            for m in ordered:
                f, t = m
                cap = board[t]
                board[f] = 0
                board[t] = 1
                hh = hsh[0]
                nh = hh ^ ZOB[f][1] ^ ZOB[t][1]
                if cap:
                    nh ^= ZOB[t][cap]
                hsh[0] = nh
                if cap:
                    cnt[cap] -= 1
                    if cnt[cap] == 0:
                        sc = WIN - 1
                    else:
                        try:
                            sc = -negamax(depth - 1, -INF, -a, 2, 1)
                        finally:
                            cnt[cap] += 1
                            board[f] = 1
                            board[t] = cap
                            hsh[0] = hh
                else:
                    try:
                        sc = -negamax(depth - 1, -INF, -a, 2, 1)
                    finally:
                        board[f] = 1
                        board[t] = cap
                        hsh[0] = hh
                scores.append((sc, m))
                if sc > cur_score:
                    cur_score = sc
                    cur_best = m
                    best_move = m
                    if sc > a:
                        a = sc
            scores.sort(reverse=True)
            ordered = [m for sc, m in scores]
            best_move = ordered[0]
            if cur_score >= WIN - 100 or cur_score <= -WIN + 100:
                break
            if time.perf_counter() > deadline:
                break
    except TimeUp:
        pass
    except Exception:
        pass

    # final legality safeguard
    if best_move not in root_moves:
        best_move = root_moves[0]
    return to_move(best_move)
