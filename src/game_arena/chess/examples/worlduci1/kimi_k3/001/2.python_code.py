
import time
import random

FILES = 'abcdefgh'
VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
MATE = 100000
INF = 10 ** 9

KNIGHT_D = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))
KING_D = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_D = ((1, 0), (-1, 0), (0, 1), (0, -1))
BISHOP_D = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _jump_table(deltas):
    tbl = []
    for sq in range(64):
        r, f = sq >> 3, sq & 7
        lst = []
        for dr, df in deltas:
            nr, nf = r + dr, f + df
            if 0 <= nr < 8 and 0 <= nf < 8:
                lst.append(nr * 8 + nf)
        tbl.append(lst)
    return tbl


def _ray_table(deltas):
    tbl = []
    for sq in range(64):
        r, f = sq >> 3, sq & 7
        rays = []
        for dr, df in deltas:
            ray = []
            nr, nf = r + dr, f + df
            while 0 <= nr < 8 and 0 <= nf < 8:
                ray.append(nr * 8 + nf)
                nr += dr
                nf += df
            if ray:
                rays.append(ray)
        tbl.append(rays)
    return tbl


KNIGHT_MOVES = _jump_table(KNIGHT_D)
KING_MOVES = _jump_table(KING_D)
ROOK_RAYS = _ray_table(ROOK_D)
BISHOP_RAYS = _ray_table(BISHOP_D)
QUEEN_RAYS = _ray_table(KING_D)

# Piece-square tables, listed rank 8 -> rank 1 from White's perspective.
_PAWN = (
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0)
_KNIGHT = (
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50)
_BISHOP = (
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20)
_ROOK = (
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0)
_QUEEN = (
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20)
_KING_MG = (
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20)
_KING_EG = (
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50)


def _conv(t):
    arr = [0] * 64
    for i in range(64):
        arr[(7 - (i >> 3)) * 8 + (i & 7)] = t[i]
    return arr


PST = {'P': _conv(_PAWN), 'N': _conv(_KNIGHT), 'B': _conv(_BISHOP),
       'R': _conv(_ROOK), 'Q': _conv(_QUEEN), 'K': _conv(_KING_MG)}
KING_EG = _conv(_KING_EG)
PASSED = (0, 10, 20, 35, 60, 100, 160, 0)

# Zobrist hashing
_rng = random.Random(20240521)
_PIECES12 = ('wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK')
PI = {p: i for i, p in enumerate(_PIECES12)}
Z = [[_rng.getrandbits(64) for _ in range(64)] for _ in range(12)]
Z_SIDE = _rng.getrandbits(64)

TT = {}
KILLERS = [[None, None] for _ in range(80)]
HH = [[0] * 64 for _ in range(64)]
NODES = 0
DEADLINE = 0.0


class SearchTimeout(Exception):
    pass


def _tick():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()


def move_uci(m):
    frm, to, promo = m
    s = FILES[frm & 7] + str((frm >> 3) + 1) + FILES[to & 7] + str((to >> 3) + 1)
    if promo:
        s += promo
    return s


def is_attacked(board, sq, by_white):
    own = 'w' if by_white else 'b'
    r = sq >> 3
    f = sq & 7
    if by_white:
        if r > 0:
            if f > 0 and board[sq - 9] == 'wP':
                return True
            if f < 7 and board[sq - 7] == 'wP':
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == 'bP':
                return True
            if f < 7 and board[sq + 9] == 'bP':
                return True
    nc = own + 'N'
    for tsq in KNIGHT_MOVES[sq]:
        if board[tsq] == nc:
            return True
    kc = own + 'K'
    for tsq in KING_MOVES[sq]:
        if board[tsq] == kc:
            return True
    bc = own + 'B'
    qc = own + 'Q'
    for ray in BISHOP_RAYS[sq]:
        for tsq in ray:
            p = board[tsq]
            if p:
                if p == bc or p == qc:
                    return True
                break
    rc = own + 'R'
    for ray in ROOK_RAYS[sq]:
        for tsq in ray:
            p = board[tsq]
            if p:
                if p == rc or p == qc:
                    return True
                break
    return False


def gen_moves(board, white, captures_only=False):
    moves = []
    app = moves.append
    own = 'w' if white else 'b'
    opp = 'b' if white else 'w'
    for sq in range(64):
        p = board[sq]
        if not p or p[0] != own:
            continue
        t = p[1]
        r = sq >> 3
        f = sq & 7
        if t == 'P':
            step = 8 if white else -8
            last = 6 if white else 1
            start = 1 if white else 6
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    tsq = sq + step + df
                    if 0 <= tsq < 64:
                        cp = board[tsq]
                        if cp and cp[0] == opp:
                            if r == last:
                                app((sq, tsq, 'q'))
                                if not captures_only:
                                    app((sq, tsq, 'r'))
                                    app((sq, tsq, 'b'))
                                    app((sq, tsq, 'n'))
                            else:
                                app((sq, tsq, ''))
            tsq = sq + step
            if 0 <= tsq < 64 and not board[tsq]:
                if r == last:
                    app((sq, tsq, 'q'))
                    if not captures_only:
                        app((sq, tsq, 'r'))
                        app((sq, tsq, 'b'))
                        app((sq, tsq, 'n'))
                elif not captures_only:
                    app((sq, tsq, ''))
                    if r == start:
                        tsq2 = tsq + step
                        if 0 <= tsq2 < 64 and not board[tsq2]:
                            app((sq, tsq2, ''))
        elif t == 'N':
            for tsq in KNIGHT_MOVES[sq]:
                cp = board[tsq]
                if not cp:
                    if not captures_only:
                        app((sq, tsq, ''))
                elif cp[0] == opp:
                    app((sq, tsq, ''))
        elif t == 'K':
            for tsq in KING_MOVES[sq]:
                cp = board[tsq]
                if not cp:
                    if not captures_only:
                        app((sq, tsq, ''))
                elif cp[0] == opp:
                    app((sq, tsq, ''))
            if not captures_only:
                if white and sq == 4:
                    if (board[7] == 'wR' and not board[5] and not board[6]
                            and not is_attacked(board, 4, False)
                            and not is_attacked(board, 5, False)
                            and not is_attacked(board, 6, False)):
                        app((4, 6, ''))
                    if (board[0] == 'wR' and not board[1] and not board[2] and not board[3]
                            and not is_attacked(board, 4, False)
                            and not is_attacked(board, 3, False)
                            and not is_attacked(board, 2, False)):
                        app((4, 2, ''))
                elif (not white) and sq == 60:
                    if (board[63] == 'bR' and not board[61] and not board[62]
                            and not is_attacked(board, 60, True)
                            and not is_attacked(board, 61, True)
                            and not is_attacked(board, 62, True)):
                        app((60, 62, ''))
                    if (board[56] == 'bR' and not board[57] and not board[58] and not board[59]
                            and not is_attacked(board, 60, True)
                            and not is_attacked(board, 59, True)
                            and not is_attacked(board, 58, True)):
                        app((60, 58, ''))
        else:
            if t == 'B':
                rays = BISHOP_RAYS[sq]
            elif t == 'R':
                rays = ROOK_RAYS[sq]
            else:
                rays = QUEEN_RAYS[sq]
            for ray in rays:
                for tsq in ray:
                    cp = board[tsq]
                    if not cp:
                        if not captures_only:
                            app((sq, tsq, ''))
                    else:
                        if cp[0] == opp:
                            app((sq, tsq, ''))
                        break
    return moves


def make_move(board, move, h):
    frm, to, promo = move
    piece = board[frm]
    captured = board[to]
    h ^= Z[PI[piece]][frm]
    if captured:
        h ^= Z[PI[captured]][to]
    rook_from = -1
    rook_to = -1
    if piece[1] == 'K' and (frm - to == 2 or to - frm == 2):
        if to == 6:
            rook_from, rook_to = 7, 5
        elif to == 2:
            rook_from, rook_to = 0, 3
        elif to == 62:
            rook_from, rook_to = 63, 61
        elif to == 58:
            rook_from, rook_to = 56, 59
        if rook_from >= 0:
            rp = board[rook_from]
            board[rook_to] = rp
            board[rook_from] = ''
            h ^= Z[PI[rp]][rook_from] ^ Z[PI[rp]][rook_to]
    if promo:
        np_ = piece[0] + promo.upper()
        board[to] = np_
        h ^= Z[PI[np_]][to]
    else:
        board[to] = piece
        h ^= Z[PI[piece]][to]
    board[frm] = ''
    return (captured, rook_from, rook_to), h


def unmake_move(board, move, undo):
    frm, to, promo = move
    captured, rook_from, rook_to = undo
    piece = board[to]
    if promo:
        piece = piece[0] + 'P'
    board[frm] = piece
    board[to] = captured
    if rook_from >= 0:
        board[rook_from] = board[rook_to]
        board[rook_to] = ''


def order_moves(board, moves, killers=None, tt_move=None):
    scored = []
    for m in moves:
        s = 0
        if tt_move is not None and m == tt_move:
            s = 1000000
        else:
            victim = board[m[1]]
            if victim:
                s = 100000 + 10 * VAL[victim[1]] - VAL[board[m[0]][1]]
            if m[2]:
                s += 120000 + VAL[m[2].upper()]
            if s == 0:
                if killers is not None and m == killers[0]:
                    s = 80000
                elif killers is not None and m == killers[1]:
                    s = 79000
                else:
                    s = HH[m[0]][m[1]]
        scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]


def evaluate(board):
    score = 0
    mat = 0
    wb = 0
    bb = 0
    w_files = [0] * 8
    b_files = [0] * 8
    w_min = [8] * 8
    b_max = [-1] * 8
    wpawns = []
    bpawns = []
    wrooks = []
    brooks = []
    wk = -1
    bk = -1
    for sq in range(64):
        p = board[sq]
        if not p:
            continue
        t = p[1]
        c = p[0]
        r = sq >> 3
        f = sq & 7
        if c == 'w':
            bsq = sq
            sgn = 1
        else:
            bsq = ((7 - r) << 3) | f
            sgn = -1
        if t == 'K':
            if c == 'w':
                wk = sq
            else:
                bk = sq
            continue
        v = VAL[t]
        if t == 'P':
            if c == 'w':
                w_files[f] += 1
                if r < w_min[f]:
                    w_min[f] = r
                wpawns.append(sq)
            else:
                b_files[f] += 1
                if r > b_max[f]:
                    b_max[f] = r
                bpawns.append(sq)
        else:
            mat += v
            if t == 'B':
                if c == 'w':
                    wb += 1
                else:
                    bb += 1
            elif t == 'R':
                if c == 'w':
                    wrooks.append(sq)
                else:
                    brooks.append(sq)
        score += sgn * (v + PST[t][bsq])
    eg = mat <= 2400
    ktab = KING_EG if eg else PST['K']
    if wk >= 0:
        score += ktab[wk]
    if bk >= 0:
        score -= ktab[((7 - (bk >> 3)) << 3) | (bk & 7)]
    for sq in wpawns:
        r = sq >> 3
        f = sq & 7
        passed = True
        for ff in (f - 1, f, f + 1):
            if 0 <= ff < 8 and b_max[ff] > r:
                passed = False
                break
        if passed:
            score += PASSED[r]
        if w_files[f] > 1:
            score -= 10
        if (f == 0 or w_files[f - 1] == 0) and (f == 7 or w_files[f + 1] == 0):
            score -= 8
    for sq in bpawns:
        r = sq >> 3
        f = sq & 7
        passed = True
        for ff in (f - 1, f, f + 1):
            if 0 <= ff < 8 and w_min[ff] < r:
                passed = False
                break
        if passed:
            score -= PASSED[7 - r]
        if b_files[f] > 1:
            score += 10
        if (f == 0 or b_files[f - 1] == 0) and (f == 7 or b_files[f + 1] == 0):
            score += 8
    for sq in wrooks:
        f = sq & 7
        if w_files[f] == 0:
            score += 22 if b_files[f] == 0 else 10
    for sq in brooks:
        f = sq & 7
        if b_files[f] == 0:
            score -= 22 if w_files[f] == 0 else 10
    if wb >= 2:
        score += 30
    if bb >= 2:
        score -= 30
    if eg and wk >= 0 and bk >= 0:
        dist = abs((wk >> 3) - (bk >> 3)) + abs((wk & 7) - (bk & 7))
        prox = (14 - dist) * 4
        if score > 150:
            score += prox
        elif score < -150:
            score -= prox
    return score


def quiesce(board, white, alpha, beta, ply):
    _tick()
    ownK = 'wK' if white else 'bK'
    ksq = board.index(ownK)
    in_check = is_attacked(board, ksq, not white)
    stand = 0
    if not in_check:
        stand = evaluate(board)
        if not white:
            stand = -stand
        if stand >= beta:
            return stand
        if alpha < stand:
            alpha = stand
        if ply >= 48:
            return alpha
        moves = order_moves(board, gen_moves(board, white, True))
    else:
        if ply >= 48:
            ev = evaluate(board)
            return ev if white else -ev
        moves = order_moves(board, gen_moves(board, white, False))
    legal = 0
    prune_ok = (not in_check) and alpha > -MATE + 1000
    for m in moves:
        if prune_ok and not m[2]:
            victim = board[m[1]]
            if victim and stand + VAL[victim[1]] + 200 <= alpha:
                continue
        undo, _ = make_move(board, m, 0)
        if is_attacked(board, board.index(ownK), not white):
            unmake_move(board, m, undo)
            continue
        legal += 1
        score = -quiesce(board, not white, -beta, -alpha, ply + 1)
        unmake_move(board, m, undo)
        if score >= beta:
            return score
        if score > alpha:
            alpha = score
    if in_check and legal == 0:
        return -MATE + ply
    return alpha


def negamax(board, h, depth, alpha, beta, white, ply):
    _tick()
    key = h if white else (h ^ Z_SIDE)
    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        ed, ev, ef, em = entry
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        tt_move = em
    if depth <= 0:
        return quiesce(board, white, alpha, beta, ply)
    alpha_orig = alpha
    moves = order_moves(board, gen_moves(board, white), KILLERS[ply], tt_move)
    best = -INF
    best_move = None
    legal = 0
    ownK = 'wK' if white else 'bK'
    for m in moves:
        quiet = (not board[m[1]]) and (not m[2])
        undo, h2 = make_move(board, m, h)
        if is_attacked(board, board.index(ownK), not white):
            unmake_move(board, m, undo)
            continue
        legal += 1
        if legal == 1:
            score = -negamax(board, h2, depth - 1, -beta, -alpha, not white, ply + 1)
        else:
            if quiet and depth >= 3 and legal > 4:
                score = -negamax(board, h2, depth - 2, -alpha - 1, -alpha, not white, ply + 1)
                if score > alpha:
                    score = -negamax(board, h2, depth - 1, -alpha - 1, -alpha, not white, ply + 1)
            else:
                score = -negamax(board, h2, depth - 1, -alpha - 1, -alpha, not white, ply + 1)
            if alpha < score < beta:
                score = -negamax(board, h2, depth - 1, -beta, -alpha, not white, ply + 1)
        unmake_move(board, m, undo)
        if score > best:
            best = score
            best_move = m
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    if quiet:
                        kl = KILLERS[ply]
                        if kl[0] != m:
                            kl[1] = kl[0]
                            kl[0] = m
                        hh = HH[m[0]]
                        hh[m[1]] += depth * depth
                        if hh[m[1]] > 40000:
                            hh[m[1]] = 40000
                    break
    if legal == 0:
        if is_attacked(board, board.index(ownK), not white):
            return -MATE + ply
        return 0
    if best <= alpha_orig:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, best_move)
    return best


def search_root(board, h, moves, white, depth, prev_best):
    ordered = order_moves(board, moves, None, prev_best)
    alpha = -INF
    best_score = -INF
    best_move = ordered[0]
    for m in ordered:
        undo, h2 = make_move(board, m, h)
        score = -negamax(board, h2, depth - 1, -INF, -alpha, not white, 1)
        unmake_move(board, m, undo)
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
    return best_score, best_move


def _policy_impl(pieces, to_play):
    global TT, KILLERS, HH, NODES, DEADLINE
    board = [''] * 64
    for sqname, pc in pieces.items():
        board[(ord(sqname[1]) - 49) * 8 + (ord(sqname[0]) - 97)] = pc
    white = (to_play == 'white')
    ownK = 'wK' if white else 'bK'
    h = 0
    for i in range(64):
        p = board[i]
        if p:
            h ^= Z[PI[p]][i]
    pseudo = gen_moves(board, white)
    legal = []
    for m in pseudo:
        undo, _ = make_move(board, m, h)
        if not is_attacked(board, board.index(ownK), not white):
            legal.append(m)
        unmake_move(board, m, undo)
    if not legal:
        if pseudo:
            return move_uci(pseudo[0])
        return 'a1a1'
    if len(legal) == 1:
        return move_uci(legal[0])
    TT = {}
    KILLERS = [[None, None] for _ in range(80)]
    HH = [[0] * 64 for _ in range(64)]
    NODES = 0
    start = time.perf_counter()
    DEADLINE = start + 0.83
    best = legal[0]
    for depth in range(1, 13):
        try:
            score, mv = search_root(board, h, legal, white, depth, best)
        except SearchTimeout:
            break
        best = mv
        if score > MATE - 300 or score < -MATE + 300:
            break
        if time.perf_counter() > DEADLINE - 0.06:
            break
    return move_uci(best)


def _fallback(pieces, to_play):
    board = [''] * 64
    for sqname, pc in pieces.items():
        board[(ord(sqname[1]) - 49) * 8 + (ord(sqname[0]) - 97)] = pc
    moves = gen_moves(board, to_play == 'white')
    if moves:
        return move_uci(moves[0])
    return 'a1a1'


def policy(pieces, to_play):
    try:
        return _policy_impl(pieces, to_play)
    except Exception:
        try:
            return _fallback(pieces, to_play)
        except Exception:
            return 'a1a1'
