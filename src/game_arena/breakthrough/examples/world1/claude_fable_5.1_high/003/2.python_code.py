
import time
import random

WIN = 100000
INF = 10 ** 9
TIME_BUDGET = 0.65

_rng = random.Random(20240607)
ZW = [_rng.getrandbits(64) for _ in range(64)]
ZB = [_rng.getrandbits(64) for _ in range(64)]
ZSIDE = _rng.getrandbits(64)

WADV = [0, 2, 5, 9, 15, 26, 50, 0]
BADV = [0, 50, 26, 15, 9, 5, 2, 0]
WRUN = [0, 0, 0, 25, 45, 80, 0, 0]
BRUN = [0, 0, 80, 45, 25, 0, 0, 0]


class _Timeout(Exception):
    pass


_nodes = 0
_deadline = 0.0
_TT = {}
_HIST = [0] * 4096


def gen_moves(board, side):
    moves = []
    if side == 1:
        for i in range(56):
            if board[i] == 1:
                c = i & 7
                t = i + 8
                if board[t] == 0:
                    moves.append((i, t))
                if c > 0 and board[t - 1] != 1:
                    moves.append((i, t - 1))
                if c < 7 and board[t + 1] != 1:
                    moves.append((i, t + 1))
    else:
        for i in range(8, 64):
            if board[i] == -1:
                c = i & 7
                t = i - 8
                if board[t] == 0:
                    moves.append((i, t))
                if c > 0 and board[t - 1] != -1:
                    moves.append((i, t - 1))
                if c < 7 and board[t + 1] != -1:
                    moves.append((i, t + 1))
    return moves


def gen_captures(board, side):
    caps = []
    if side == 1:
        for i in range(56):
            if board[i] == 1:
                c = i & 7
                t = i + 8
                if c > 0 and board[t - 1] == -1:
                    caps.append((i, t - 1))
                if c < 7 and board[t + 1] == -1:
                    caps.append((i, t + 1))
    else:
        for i in range(8, 64):
            if board[i] == -1:
                c = i & 7
                t = i - 8
                if c > 0 and board[t - 1] == 1:
                    caps.append((i, t - 1))
                if c < 7 and board[t + 1] == 1:
                    caps.append((i, t + 1))
    return caps


def evaluate(board, side, ply):
    ws = 0
    bs = 0
    w6 = 0
    b1 = 0
    wl = []
    bl = []
    for i in range(64):
        p = board[i]
        if p == 0:
            continue
        r = i >> 3
        c = i & 7
        if p == 1:
            wl.append(i)
            if r == 6:
                w6 += 1
            v = 100 + WADV[r]
            att = False
            if r < 7:
                if c > 0 and board[i + 7] == -1:
                    att = True
                elif c < 7 and board[i + 9] == -1:
                    att = True
            dfd = False
            if r > 0:
                if c > 0 and board[i - 9] == 1:
                    dfd = True
                elif c < 7 and board[i - 7] == 1:
                    dfd = True
            if att:
                if dfd:
                    v -= 4
                else:
                    v -= 10 if side == 1 else 25
            if dfd:
                v += 5
            if r == 0:
                v += 6
            ws += v
        else:
            bl.append(i)
            if r == 1:
                b1 += 1
            v = 100 + BADV[r]
            att = False
            if r > 0:
                if c > 0 and board[i - 9] == 1:
                    att = True
                elif c < 7 and board[i - 7] == 1:
                    att = True
            dfd = False
            if r < 7:
                if c > 0 and board[i + 7] == -1:
                    dfd = True
                elif c < 7 and board[i + 9] == -1:
                    dfd = True
            if att:
                if dfd:
                    v -= 4
                else:
                    v -= 10 if side == -1 else 25
            if dfd:
                v += 5
            if r == 7:
                v += 6
            bs += v

    if side == 1:
        if w6:
            return WIN - ply - 1
        if b1 >= 2:
            return -(WIN - ply - 2)
        if b1 == 1:
            for i in bl:
                if (i >> 3) == 1:
                    c = i & 7
                    capturable = (c > 0 and board[i - 9] == 1) or (c < 7 and board[i - 7] == 1)
                    if not capturable:
                        return -(WIN - ply - 2)
                    bs += 40
                    break
    else:
        if b1:
            return WIN - ply - 1
        if w6 >= 2:
            return -(WIN - ply - 2)
        if w6 == 1:
            for i in wl:
                if (i >> 3) == 6:
                    c = i & 7
                    capturable = (c > 0 and board[i + 7] == -1) or (c < 7 and board[i + 9] == -1)
                    if not capturable:
                        return -(WIN - ply - 2)
                    ws += 40
                    break

    # free runners
    for i in wl:
        r = i >> 3
        if 3 <= r <= 5:
            c = i & 7
            free = True
            for j in bl:
                rb = j >> 3
                if rb > r:
                    d = (j & 7) - c
                    if d < 0:
                        d = -d
                    if d <= rb - r + 1:
                        free = False
                        break
            if free:
                ws += WRUN[r]
    for i in bl:
        r = i >> 3
        if 2 <= r <= 4:
            c = i & 7
            free = True
            for j in wl:
                rw = j >> 3
                if rw < r:
                    d = (j & 7) - c
                    if d < 0:
                        d = -d
                    if d <= r - rw + 1:
                        free = False
                        break
            if free:
                bs += BRUN[r]

    score = ws - bs
    return score if side == 1 else -score


def qsearch(board, side, alpha, beta, ply, qd, wc, bc):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise _Timeout()
    stand = evaluate(board, side, ply)
    if qd <= 0 or stand >= beta or stand >= WIN // 2 or stand <= -(WIN // 2):
        return stand
    if stand > alpha:
        alpha = stand
    best = stand
    caps = gen_captures(board, side)
    for frm, to in caps:
        cap = board[to]
        board[to] = side
        board[frm] = 0
        if side == 1:
            nbc = bc - 1
            nwc = wc
            win = to >= 56 or nbc == 0
        else:
            nwc = wc - 1
            nbc = bc
            win = to < 8 or nwc == 0
        if win:
            score = WIN - ply - 1
        else:
            score = -qsearch(board, -side, -beta, -alpha, ply + 1, qd - 1, nwc, nbc)
        board[frm] = side
        board[to] = cap
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best


def negamax(board, side, depth, alpha, beta, ply, h, wc, bc):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise _Timeout()
    alpha0 = alpha
    tt_move = None
    e = _TT.get(h)
    if e is not None:
        edepth, escore, eflag, emove = e
        if edepth >= depth:
            if eflag == 0:
                return escore
            if eflag == 1:
                if escore > alpha:
                    alpha = escore
            else:
                if escore < beta:
                    beta = escore
            if alpha >= beta:
                return escore
        tt_move = emove
    if depth <= 0:
        return qsearch(board, side, alpha, beta, ply, 4, wc, bc)
    moves = gen_moves(board, side)
    if not moves:
        return evaluate(board, side, ply)
    scored = []
    for m in moves:
        frm, to = m
        if m == tt_move:
            k = 3000000
        elif (to >= 56) if side == 1 else (to < 8):
            k = 2000000
        elif board[to] != 0:
            k = 1000000 + (BADV[to >> 3] if side == 1 else WADV[to >> 3])
        else:
            k = _HIST[(frm << 6) | to]
        scored.append((k, m))
    scored.sort(reverse=True)
    best = -INF
    best_move = None
    for k, m in scored:
        frm, to = m
        cap = board[to]
        board[to] = side
        board[frm] = 0
        if side == 1:
            nh = h ^ ZW[frm] ^ ZW[to] ^ ZSIDE
            nwc = wc
            nbc = bc
            if cap:
                nh ^= ZB[to]
                nbc -= 1
            win = to >= 56 or nbc == 0
        else:
            nh = h ^ ZB[frm] ^ ZB[to] ^ ZSIDE
            nwc = wc
            nbc = bc
            if cap:
                nh ^= ZW[to]
                nwc -= 1
            win = to < 8 or nwc == 0
        if win:
            score = WIN - ply - 1
        else:
            score = -negamax(board, -side, depth - 1, -beta, -alpha, ply + 1, nh, nwc, nbc)
        board[frm] = side
        board[to] = cap
        if score > best:
            best = score
            best_move = m
        if score > alpha:
            alpha = score
        if alpha >= beta:
            if cap == 0:
                _HIST[(frm << 6) | to] += depth * depth
            break
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[h] = (depth, best, flag, best_move)
    return best


def root_search(board, side, depth, h, wc, bc, root_moves):
    alpha = -INF
    beta = INF
    best = -INF
    best_move = root_moves[0]
    scores = []
    for frm, to in root_moves:
        cap = board[to]
        board[to] = side
        board[frm] = 0
        if side == 1:
            nh = h ^ ZW[frm] ^ ZW[to] ^ ZSIDE
            nwc = wc
            nbc = bc
            if cap:
                nh ^= ZB[to]
                nbc -= 1
            win = to >= 56 or nbc == 0
        else:
            nh = h ^ ZB[frm] ^ ZB[to] ^ ZSIDE
            nwc = wc
            nbc = bc
            if cap:
                nh ^= ZW[to]
                nwc -= 1
            win = to < 8 or nwc == 0
        if win:
            score = WIN - 1
        else:
            score = -negamax(board, -side, depth - 1, -beta, -alpha, 1, nh, nwc, nbc)
        board[frm] = side
        board[to] = cap
        scores.append((score, (frm, to)))
        if score > best:
            best = score
            best_move = (frm, to)
        if score > alpha:
            alpha = score
    scores.sort(key=lambda x: -x[0])
    return best, best_move, [m for s, m in scores]


def _to_move(m):
    frm, to = m
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def policy(me, opp, color):
    global _deadline, _nodes, _TT, _HIST
    start = time.time()
    side = 1 if color == 'w' else -1
    board = [0] * 64
    for r, c in me:
        board[r * 8 + c] = side
    for r, c in opp:
        board[r * 8 + c] = -side
    moves = gen_moves(board, side)
    if not moves:
        # No legal move exists; return something well-formed.
        if me:
            r, c = me[0]
            nr = r + side
            return ((r, c), (max(0, min(7, nr)), c))
        return ((0, 0), (1, 0))

    # Fallback: win > capture > first
    fallback = moves[0]
    for frm, to in moves:
        if (side == 1 and to >= 56) or (side == -1 and to < 8):
            fallback = (frm, to)
            break
    else:
        for frm, to in moves:
            if board[to] != 0:
                fallback = (frm, to)
                break

    best_move = fallback
    try:
        _deadline = start + TIME_BUDGET
        _nodes = 0
        _TT = {}
        _HIST = [0] * 4096
        h = 0
        wc = 0
        bc = 0
        for i in range(64):
            if board[i] == 1:
                h ^= ZW[i]
                wc += 1
            elif board[i] == -1:
                h ^= ZB[i]
                bc += 1
        if side == -1:
            h ^= ZSIDE
        root_moves = list(moves)
        # put fallback first initially
        if fallback in root_moves:
            root_moves.remove(fallback)
            root_moves.insert(0, fallback)
        for depth in range(1, 40):
            score, mv, root_moves = root_search(board, side, depth, h, wc, bc, root_moves)
            best_move = mv
            if score >= WIN // 2 or score <= -(WIN // 2):
                break
            if time.time() - start > TIME_BUDGET * 0.5:
                # not enough time for another full iteration most likely
                pass
    except _Timeout:
        pass
    except Exception:
        best_move = fallback

    # final legality guard
    if best_move not in moves:
        best_move = fallback
    return _to_move(best_move)
