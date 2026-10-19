
import sys
import time
import random

sys.setrecursionlimit(100000)

INF = 10 ** 9
MATE = 100000
CASTLE = 1 << 17

KNIGHT_OFFS = (31, 33, 14, 18, -14, -18, -31, -33)
KING_OFFS = (15, 16, 17, 1, -1, -15, -16, -17)
DIAG_DIRS = (15, 17, -15, -17)
ORTH_DIRS = (16, -16, 1, -1)

PT = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
PROMO_CH = {2: 'n', 3: 'b', 4: 'r', 5: 'q'}

# Piece-square tables, listed from rank 8 down to rank 1 (white perspective).
PAWN_MG = (
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
)
KNIGHT_MG = (
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  5,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
)
BISHOP_MG = (
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
)
ROOK_MG = (
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
)
QUEEN_MG = (
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
)
KING_MG = (
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
)
KING_EG = (
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
)
PAWN_EG = (
     0,  0,  0,  0,  0,  0,  0,  0,
    80, 80, 80, 80, 80, 80, 80, 80,
    45, 45, 45, 45, 45, 45, 45, 45,
    25, 25, 25, 25, 25, 25, 25, 25,
    12, 12, 12, 12, 12, 12, 12, 12,
     6,  6,  6,  6,  6,  6,  6,  6,
     3,  3,  3,  3,  3,  3,  3,  3,
     0,  0,  0,  0,  0,  0,  0,  0,
)

MG_PST = (None, PAWN_MG, KNIGHT_MG, BISHOP_MG, ROOK_MG, QUEEN_MG, KING_MG)
EG_PST = (None, PAWN_EG, KNIGHT_MG, BISHOP_MG, ROOK_MG, QUEEN_MG, KING_EG)
MG_VAL = (0, 100, 320, 330, 500, 900, 0)
EG_VAL = (0, 120, 320, 330, 510, 900, 0)
PHASE_V = (0, 0, 1, 1, 2, 4, 0)
MVV = (0, 100, 320, 330, 500, 900, 2000)
LVA = (0, 100, 320, 330, 500, 900, 2000)

S64N = tuple((((s >> 4) << 3) | (s & 7)) for s in range(128))
S64F = tuple((S64N[s] ^ 56) for s in range(128))

_rng = random.Random(0xC0FFEE)
Z = tuple(tuple(_rng.getrandbits(64) for _ in range(16)) for _ in range(128))
Z_SIDE = _rng.getrandbits(64)

TT = {}
KILLERS = [[0, 0] for _ in range(128)]
HIST = [[0] * 16384, [0] * 16384]

nodes = 0
deadline = 0.0


class Timeout(Exception):
    pass


class Pos(object):
    __slots__ = ('b', 'pl', 'ksq', 'turn', 'hash')

    def __init__(self, b, pl, ksq, turn, h):
        self.b = b
        self.pl = pl
        self.ksq = ksq
        self.turn = turn
        self.hash = h


def check_time():
    if time.perf_counter() >= deadline:
        raise Timeout()


def sq_from_str(s):
    return ((ord(s[1]) - 49) << 4) | (ord(s[0]) - 97)


def sq_to_str(sq):
    return chr((sq & 7) + 97) + chr((sq >> 4) + 49)


def move_to_uci(m):
    s = sq_to_str(m & 127) + sq_to_str((m >> 7) & 127)
    promo = (m >> 14) & 7
    if promo:
        s += PROMO_CH[promo]
    return s


def build_pos(pieces, to_play):
    b = [0] * 128
    pl = ([[], [], [], [], [], [], []], [[], [], [], [], [], [], []])
    ksq = [4, 116]
    h = 0
    for s, pc in pieces.items():
        sq = sq_from_str(s.lower())
        color = 0 if pc[0].lower() == 'w' else 1
        pt = PT[pc[1].upper()]
        v = pt | (color << 3)
        b[sq] = v
        pl[color][pt].append(sq)
        if pt == 6:
            ksq[color] = sq
        h ^= Z[sq][v]
    turn = 0 if str(to_play).lower() in ('white', 'w') else 1
    if turn:
        h ^= Z_SIDE
    return Pos(b, pl, ksq, turn, h)


def attacked(pos, sq, by_color):
    b = pos.b
    if by_color == 0:
        t = sq - 15
        if not (t & 0x88) and b[t] == 1:
            return True
        t = sq - 17
        if not (t & 0x88) and b[t] == 1:
            return True
    else:
        t = sq + 15
        if not (t & 0x88) and b[t] == 9:
            return True
        t = sq + 17
        if not (t & 0x88) and b[t] == 9:
            return True
    nval = 2 | (by_color << 3)
    for off in KNIGHT_OFFS:
        t = sq + off
        if not (t & 0x88) and b[t] == nval:
            return True
    kval = 6 | (by_color << 3)
    for off in KING_OFFS:
        t = sq + off
        if not (t & 0x88) and b[t] == kval:
            return True
    bval = 3 | (by_color << 3)
    rval = 4 | (by_color << 3)
    qval = 5 | (by_color << 3)
    for d in DIAG_DIRS:
        t = sq + d
        while not (t & 0x88):
            p = b[t]
            if p:
                if p == bval or p == qval:
                    return True
                break
            t += d
    for d in ORTH_DIRS:
        t = sq + d
        while not (t & 0x88):
            p = b[t]
            if p:
                if p == rval or p == qval:
                    return True
                break
            t += d
    return False


def make(pos, move):
    b = pos.b
    frm = move & 127
    to = (move >> 7) & 127
    promo = (move >> 14) & 7
    piece = b[frm]
    color = piece >> 3
    captured = b[to]
    h = pos.hash ^ Z_SIDE ^ Z[frm][piece] ^ Z[to][piece]
    if captured:
        h ^= Z[to][captured]
        pos.pl[color ^ 1][captured & 7].remove(to)
    if promo:
        np = promo | (color << 3)
        b[frm] = 0
        b[to] = np
        pos.pl[color][1].remove(frm)
        pos.pl[color][promo].append(to)
        h ^= Z[to][piece] ^ Z[to][np]
    else:
        b[frm] = 0
        b[to] = piece
        plst = pos.pl[color][piece & 7]
        plst.remove(frm)
        plst.append(to)
        if (piece & 7) == 6:
            pos.ksq[color] = to
    if move & CASTLE:
        if to > frm:
            rfrm = (frm & 112) | 7
            rto = (frm & 112) | 5
        else:
            rfrm = frm & 112
            rto = (frm & 112) | 3
        rook = b[rfrm]
        b[rfrm] = 0
        b[rto] = rook
        rl = pos.pl[color][4]
        rl.remove(rfrm)
        rl.append(rto)
        h ^= Z[rfrm][rook] ^ Z[rto][rook]
    pos.hash = h
    pos.turn = color ^ 1
    return captured


def unmake(pos, move, captured):
    b = pos.b
    frm = move & 127
    to = (move >> 7) & 127
    promo = (move >> 14) & 7
    color = pos.turn ^ 1
    if promo:
        b[frm] = 1 | (color << 3)
        b[to] = captured
        pos.pl[color][promo].remove(to)
        pos.pl[color][1].append(frm)
    else:
        piece = b[to]
        b[frm] = piece
        b[to] = captured
        plst = pos.pl[color][piece & 7]
        plst.remove(to)
        plst.append(frm)
        if (piece & 7) == 6:
            pos.ksq[color] = frm
    if captured:
        pos.pl[color ^ 1][captured & 7].append(to)
    if move & CASTLE:
        if to > frm:
            rfrm = (frm & 112) | 7
            rto = (frm & 112) | 5
        else:
            rfrm = frm & 112
            rto = (frm & 112) | 3
        rook = b[rto]
        b[rto] = 0
        b[rfrm] = rook
        rl = pos.pl[color][4]
        rl.remove(rto)
        rl.append(rfrm)
    pos.turn = color


def gen_pseudo(pos, captures_only):
    b = pos.b
    color = pos.turn
    ecolor = color ^ 1
    own = pos.pl[color]
    moves = []
    ap = moves.append
    if color == 0:
        step, c1, c2, pr, sr = 16, 15, 17, 6, 1
    else:
        step, c1, c2, pr, sr = -16, -17, -15, 1, 6
    for sq in own[1]:
        rank = sq >> 4
        if rank == pr:
            for off in (c1, c2):
                t1 = sq + off
                if not (t1 & 0x88):
                    t = b[t1]
                    if t and (t >> 3) == ecolor:
                        m = sq | (t1 << 7)
                        ap(m | (5 << 14)); ap(m | (2 << 14))
                        ap(m | (3 << 14)); ap(m | (4 << 14))
            to = sq + step
            if b[to] == 0:
                m = sq | (to << 7)
                ap(m | (5 << 14)); ap(m | (2 << 14))
                ap(m | (3 << 14)); ap(m | (4 << 14))
            continue
        for off in (c1, c2):
            t1 = sq + off
            if not (t1 & 0x88):
                t = b[t1]
                if t and (t >> 3) == ecolor:
                    ap(sq | (t1 << 7))
        if captures_only:
            continue
        to = sq + step
        if b[to] == 0:
            ap(sq | (to << 7))
            if rank == sr and b[to + step] == 0:
                ap(sq | ((to + step) << 7))
    for sq in own[2]:
        for off in KNIGHT_OFFS:
            to = sq + off
            if to & 0x88:
                continue
            t = b[to]
            if t:
                if (t >> 3) == ecolor:
                    ap(sq | (to << 7))
            elif not captures_only:
                ap(sq | (to << 7))
    for sq in own[3]:
        for d in DIAG_DIRS:
            to = sq + d
            while not (to & 0x88):
                t = b[to]
                if t:
                    if (t >> 3) == ecolor:
                        ap(sq | (to << 7))
                    break
                if not captures_only:
                    ap(sq | (to << 7))
                to += d
    for sq in own[4]:
        for d in ORTH_DIRS:
            to = sq + d
            while not (to & 0x88):
                t = b[to]
                if t:
                    if (t >> 3) == ecolor:
                        ap(sq | (to << 7))
                    break
                if not captures_only:
                    ap(sq | (to << 7))
                to += d
    for sq in own[5]:
        for d in KING_OFFS:
            to = sq + d
            while not (to & 0x88):
                t = b[to]
                if t:
                    if (t >> 3) == ecolor:
                        ap(sq | (to << 7))
                    break
                if not captures_only:
                    ap(sq | (to << 7))
                to += d
    ksq = own[6][0]
    for off in KING_OFFS:
        to = ksq + off
        if to & 0x88:
            continue
        t = b[to]
        if t:
            if (t >> 3) == ecolor:
                ap(ksq | (to << 7))
        elif not captures_only:
            ap(ksq | (to << 7))
    if not captures_only:
        if color == 0:
            if ksq == 4:
                if b[7] == 4 and b[5] == 0 and b[6] == 0 and \
                   not attacked(pos, 4, 1) and not attacked(pos, 5, 1) and not attacked(pos, 6, 1):
                    ap(4 | (6 << 7) | CASTLE)
                if b[0] == 4 and b[1] == 0 and b[2] == 0 and b[3] == 0 and \
                   not attacked(pos, 4, 1) and not attacked(pos, 3, 1) and not attacked(pos, 2, 1):
                    ap(4 | (2 << 7) | CASTLE)
        else:
            if ksq == 116:
                if b[119] == 12 and b[117] == 0 and b[118] == 0 and \
                   not attacked(pos, 116, 0) and not attacked(pos, 117, 0) and not attacked(pos, 118, 0):
                    ap(116 | (118 << 7) | CASTLE)
                if b[112] == 12 and b[113] == 0 and b[114] == 0 and b[115] == 0 and \
                   not attacked(pos, 116, 0) and not attacked(pos, 115, 0) and not attacked(pos, 114, 0):
                    ap(116 | (114 << 7) | CASTLE)
    return moves


def gen_legal(pos):
    color = pos.turn
    ecolor = color ^ 1
    res = []
    for m in gen_pseudo(pos, False):
        oh = pos.hash
        cap = make(pos, m)
        if not attacked(pos, pos.ksq[color], ecolor):
            res.append(m)
        unmake(pos, m, cap)
        pos.hash = oh
    return res


def evaluate(pos):
    mg = 0
    eg = 0
    phase = 0
    pl = pos.pl
    for pt in (1, 2, 3, 4, 5, 6):
        mgt = MG_PST[pt]
        egt = EG_PST[pt]
        mgv = MG_VAL[pt]
        egv = EG_VAL[pt]
        ph = PHASE_V[pt]
        for sq in pl[0][pt]:
            i = S64F[sq]
            mg += mgv + mgt[i]
            eg += egv + egt[i]
            phase += ph
        for sq in pl[1][pt]:
            i = S64N[sq]
            mg -= mgv + mgt[i]
            eg -= egv + egt[i]
            phase += ph
    if phase > 24:
        phase = 24
    s = (mg * phase + eg * (24 - phase)) // 24
    return s if pos.turn == 0 else -s


def order_moves(pos, moves, tt_move, ply):
    b = pos.b
    killers = KILLERS[ply]
    hist = HIST[pos.turn]
    scored = []
    ap = scored.append
    for m in moves:
        if m == tt_move:
            s = 20000000
        else:
            frm = m & 127
            to = (m >> 7) & 127
            t = b[to]
            promo = (m >> 14) & 7
            if t:
                s = 5000000 + MVV[t & 7] * 32 - LVA[b[frm] & 7]
                if promo:
                    s += 6000000 + MVV[promo] * 32
            elif promo:
                s = 6000000 + MVV[promo] * 32
            elif m == killers[0]:
                s = 3000000
            elif m == killers[1]:
                s = 2900000
            else:
                s = hist[(frm << 7) | to]
        ap((s, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for s, m in scored]


def score_to_tt(score, ply):
    if score > MATE - 1000:
        return score + ply
    if score < -MATE + 1000:
        return score - ply
    return score


def score_from_tt(score, ply):
    if score > MATE - 1000:
        return score - ply
    if score < -MATE + 1000:
        return score + ply
    return score


def quiesce(pos, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0:
        check_time()
    if ply >= 90:
        return evaluate(pos)
    color = pos.turn
    ecolor = color ^ 1
    in_check = attacked(pos, pos.ksq[color], ecolor)
    if in_check:
        moves = order_moves(pos, gen_pseudo(pos, False), 0, ply)
    else:
        stand = evaluate(pos)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        moves = order_moves(pos, gen_pseudo(pos, True), 0, ply)
    legal = 0
    for m in moves:
        oh = pos.hash
        cap = make(pos, m)
        if attacked(pos, pos.ksq[color], ecolor):
            unmake(pos, m, cap)
            pos.hash = oh
            continue
        legal += 1
        score = -quiesce(pos, -beta, -alpha, ply + 1)
        unmake(pos, m, cap)
        pos.hash = oh
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    if in_check and legal == 0:
        return -MATE + ply
    return alpha


def search(pos, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0:
        check_time()
    color = pos.turn
    if ply:
        mda = -MATE + ply
        if mda > alpha:
            alpha = mda
        mdb = MATE - ply - 1
        if mdb < beta:
            beta = mdb
        if alpha >= beta:
            return alpha
    if ply >= 90:
        return evaluate(pos)
    key = pos.hash
    tt_move = 0
    ent = TT.get(key)
    if ent is not None:
        if ent[0] >= depth:
            es = score_from_tt(ent[2], ply)
            ef = ent[1]
            if ef == 0:
                return es
            if ef == 1:
                if es >= beta:
                    return es
            elif es <= alpha:
                return es
        tt_move = ent[3]
    in_check = attacked(pos, pos.ksq[color], color ^ 1)
    if in_check:
        depth += 1
    if depth <= 0:
        return quiesce(pos, alpha, beta, ply)
    if depth >= 3 and not in_check and beta < MATE - 1000:
        own = pos.pl[color]
        if own[2] or own[3] or own[4] or own[5]:
            pos.turn = color ^ 1
            pos.hash = key ^ Z_SIDE
            nm = -search(pos, depth - 3, -beta, -beta + 1, ply + 1)
            pos.turn = color
            pos.hash = key
            if nm >= beta:
                return nm
    moves = order_moves(pos, gen_pseudo(pos, False), tt_move, ply)
    killers = KILLERS[ply]
    hist = HIST[color]
    ecolor = color ^ 1
    legal = 0
    best_score = -INF
    best_move = 0
    alpha0 = alpha
    for m in moves:
        oh = pos.hash
        cap = make(pos, m)
        if attacked(pos, pos.ksq[color], ecolor):
            unmake(pos, m, cap)
            pos.hash = oh
            continue
        legal += 1
        if legal == 1:
            score = -search(pos, depth - 1, -beta, -alpha, ply + 1)
        else:
            if depth >= 3 and not in_check and cap == 0 and (m >> 14) == 0 and legal > 3:
                score = -search(pos, depth - 2, -alpha - 1, -alpha, ply + 1)
            else:
                score = -search(pos, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -search(pos, depth - 1, -beta, -alpha, ply + 1)
        unmake(pos, m, cap)
        pos.hash = oh
        if score > best_score:
            best_score = score
            best_move = m
            if score > alpha:
                alpha = score
                if score >= beta:
                    if cap == 0:
                        if killers[0] != m:
                            killers[1] = killers[0]
                            killers[0] = m
                        hist[((m & 127) << 7) | ((m >> 7) & 127)] += depth * depth
                    TT[key] = (depth, 1, score_to_tt(score, ply), m)
                    return score
    if legal == 0:
        return -MATE + ply if in_check else 0
    TT[key] = (depth, 0 if best_score > alpha0 else 2, score_to_tt(best_score, ply), best_move)
    return best_score


def root_search(pos, legal_list, depth):
    ent = TT.get(pos.hash)
    tt_move = ent[3] if ent is not None else 0
    moves = order_moves(pos, legal_list, tt_move, 0)
    alpha = -INF
    beta = INF
    best_move = 0
    best_score = -INF
    first = True
    for m in moves:
        oh = pos.hash
        cap = make(pos, m)
        if first:
            score = -search(pos, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -search(pos, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -search(pos, depth - 1, -beta, -alpha, 1)
        unmake(pos, m, cap)
        pos.hash = oh
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
    if best_move:
        TT[pos.hash] = (depth, 0, score_to_tt(best_score, 0), best_move)
    return best_score, best_move


def iterative_search(pos, legal_list):
    global deadline, nodes
    deadline = time.perf_counter() + 0.80
    nodes = 0
    best = legal_list[0]
    for depth in range(1, 64):
        try:
            score, mv = root_search(pos, legal_list, depth)
        except Timeout:
            break
        if mv:
            best = mv
        if score >= MATE - 1000:
            break
        if time.perf_counter() >= deadline - 0.02:
            break
    return best


def pick_from_list(pos, legal, legal_moves):
    allowed = set(legal_moves)
    best_u = None
    best_s = -INF
    for m in legal:
        u = move_to_uci(m)
        if u in allowed:
            oh = pos.hash
            cap = make(pos, m)
            sc = -evaluate(pos)
            unmake(pos, m, cap)
            pos.hash = oh
            if sc > best_s:
                best_s = sc
                best_u = u
    if best_u is not None:
        return best_u
    return legal_moves[0]


def emergency(pieces, to_play, legal_moves=None):
    try:
        pos = build_pos(pieces, to_play)
        ms = gen_pseudo(pos, False)
        color = pos.turn
        for m in ms:
            try:
                oh = pos.hash
                cap = make(pos, m)
                ok = True
                if pos.pl[color][6]:
                    if attacked(pos, pos.ksq[color], color ^ 1):
                        ok = False
                unmake(pos, m, cap)
                pos.hash = oh
            except Exception:
                ok = False
            if ok:
                u = move_to_uci(m)
                if legal_moves is None or u in legal_moves:
                    return u
    except Exception:
        pass
    try:
        if legal_moves:
            return legal_moves[0]
    except Exception:
        pass
    return 'a2a3'


def policy(pieces, to_play, legal_moves=None):
    global TT
    try:
        if len(TT) > 400000:
            TT = {}
        pos = build_pos(pieces, to_play)
        legal = gen_legal(pos)
        if not legal:
            raise ValueError('no legal moves')
        if len(legal) == 1:
            uci = move_to_uci(legal[0])
            if legal_moves is not None and uci not in legal_moves:
                return pick_from_list(pos, legal, legal_moves)
            return uci
        best = iterative_search(pos, legal)
        uci = move_to_uci(best)
        if legal_moves is not None and uci not in legal_moves:
            return pick_from_list(pos, legal, legal_moves)
        return uci
    except Exception:
        return emergency(pieces, to_play, legal_moves)


if __name__ == '__main__':
    # Quick self-check: perft(3) from the initial position must be 8902.
    start = {
        'a1': 'wR', 'b1': 'wN', 'c1': 'wB', 'd1': 'wQ', 'e1': 'wK',
        'f1': 'wB', 'g1': 'wN', 'h1': 'wR',
        'a2': 'wP', 'b2': 'wP', 'c2': 'wP', 'd2': 'wP',
        'e2': 'wP', 'f2': 'wP', 'g2': 'wP', 'h2': 'wP',
        'a8': 'bR', 'b8': 'bN', 'c8': 'bB', 'd8': 'bQ', 'e8': 'bK',
        'f8': 'bB', 'g8': 'bN', 'h8': 'bR',
        'a7': 'bP', 'b7': 'bP', 'c7': 'bP', 'd7': 'bP',
        'e7': 'bP', 'f7': 'bP', 'g7': 'bP', 'h7': 'bP',
    }

    def perft(pos, d):
        if d == 0:
            return 1
        n = 0
        color = pos.turn
        for m in gen_pseudo(pos, False):
            oh = pos.hash
            cap = make(pos, m)
            if not attacked(pos, pos.ksq[color], color ^ 1):
                n += perft(pos, d - 1)
            unmake(pos, m, cap)
            pos.hash = oh
        return n

    p = build_pos(start, 'white')
    assert perft(p, 3) == 8902, perft(p, 3)
    print('perft ok; sample move:', policy(start, 'white'))
