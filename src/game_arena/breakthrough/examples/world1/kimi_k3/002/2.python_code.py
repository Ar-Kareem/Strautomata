
from __future__ import annotations

import time

# ----------------------------- constants -----------------------------

FULL = (1 << 64) - 1
ROW0 = 0xFF
ROW7 = 0xFF << 56
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

WIN = 1 << 21
INF = 1 << 30

PIECE_VAL = 100
ADV = (0, 3, 8, 18, 35, 60, 100, 0)       # bonus by rows advanced
PASSED = (0, 5, 12, 25, 45, 80, 140, 0)   # extra bonus for passed pieces
DEF_BONUS = 12                            # bonus per defended piece

VW = tuple(PIECE_VAL + ADV[r] for r in range(8))        # white piece on row r
VB = tuple(PIECE_VAL + ADV[7 - r] for r in range(8))    # black piece on row r
PW = tuple(PASSED[r] for r in range(8))
PB = tuple(PASSED[7 - r] for r in range(8))

SQ_UP = tuple(PIECE_VAL + ADV[sq >> 3] for sq in range(64))
SQ_DN = tuple(PIECE_VAL + ADV[7 - (sq >> 3)] for sq in range(64))

try:
    _popcount = int.bit_count
except AttributeError:  # pragma: no cover
    def _popcount(x):
        return bin(x).count("1")

POP8 = tuple(_popcount(i) for i in range(256))

MAX_DEPTH = 14
MAX_PLY = 40
QMAX = 30
TIME_LIMIT = 0.85

TT = {}
killers = [[None, None] for _ in range(MAX_PLY)]
nodes = 0
deadline = 0.0


# --------------------------- evaluation ---------------------------

def eval_white(w, b):
    """Static score from White's perspective (White moves to higher rows)."""
    p8 = POP8
    # Black flood-fill downward -> squares where black can block/capture white.
    x = b | (b >> 8)
    x |= x >> 16
    x |= x >> 32
    y = x | ((x & NOT_H) << 1) | ((x & NOT_A) >> 1)
    zone_w = (y >> 8) & FULL
    # White flood-fill upward -> squares where white can block/capture black.
    x = w | (w << 8)
    x |= x << 16
    x |= x << 32
    x &= FULL
    y = x | ((x & NOT_H) << 1) | ((x & NOT_A) >> 1)
    zone_b = (y << 8) & FULL
    pw = w & (FULL ^ zone_w)   # white passed pieces
    pb = b & (FULL ^ zone_b)   # black passed pieces
    s = 0
    for r in range(8):
        sh = 8 * r
        m = 255 << sh
        s += p8[(w & m) >> sh] * VW[r] - p8[(b & m) >> sh] * VB[r]
        s += p8[(pw & m) >> sh] * PW[r] - p8[(pb & m) >> sh] * PB[r]
    # defended pieces (guarded by a friendly piece one row behind diagonally)
    wdef = ((w & NOT_A) << 7) | ((w & NOT_H) << 9)
    bdef = ((b & NOT_A) >> 9) | ((b & NOT_H) >> 7)
    s += DEF_BONUS * (_popcount(w & wdef) - _popcount(b & bdef))
    return s


def evaluate(me, opp, up):
    if up:
        return eval_white(me, opp)
    return -eval_white(opp, me)


# ------------------------- move generation -------------------------

def gen_moves(me, opp, up, tt_move, killer):
    """Generate pseudo-ordered legal moves: (score, from, to, is_capture)."""
    empty = FULL ^ (me | opp)
    if up:
        sv = SQ_UP
        osv = SQ_DN
        groups = (
            (((me & NOT_A) << 7) & opp, 7, True),
            (((me & NOT_H) << 9) & opp, 9, True),
            ((me << 8) & empty, 8, False),
            (((me & NOT_A) << 7) & empty, 7, False),
            (((me & NOT_H) << 9) & empty, 9, False),
        )
        d = -1
    else:
        sv = SQ_DN
        osv = SQ_UP
        groups = (
            (((me & NOT_A) >> 9) & opp, 9, True),
            (((me & NOT_H) >> 7) & opp, 7, True),
            ((me >> 8) & empty, 8, False),
            (((me & NOT_A) >> 9) & empty, 9, False),
            (((me & NOT_H) >> 7) & empty, 7, False),
        )
        d = 1
    moves = []
    apnd = moves.append
    tt0 = tt1 = None
    if tt_move is not None:
        tt0, tt1 = tt_move
    k0 = k1 = None
    if killer is not None:
        k0, k1 = killer
    for bb, sh, cap in groups:
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            to = lsb.bit_length() - 1
            frm = to + d * sh
            if tt0 is not None and frm == tt0 and to == tt1:
                s = 1 << 22
            elif cap:
                s = (1 << 20) + osv[to]
            else:
                s = sv[to] - (sv[frm] >> 2)
                if (k0 is not None and frm == k0[0] and to == k0[1]) or \
                   (k1 is not None and frm == k1[0] and to == k1[1]):
                    s += 1 << 19
            apnd((s, frm, to, cap))
    moves.sort(reverse=True)
    return moves


# ---------------------------- search ----------------------------

def qsearch(me, opp, up, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 255) == 0 and time.time() >= deadline:
        raise TimeoutError
    if up:
        if opp & ROW0:
            return -WIN + ply
    elif opp & ROW7:
        return -WIN + ply
    if me == 0:
        return -WIN + ply
    stand = evaluate(me, opp, up)
    if stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand
    if ply >= QMAX:
        return alpha
    empty = FULL ^ (me | opp)
    if up:
        goal = ROW7
        groups = (
            (((me & NOT_A) << 7) & opp, 7),
            (((me & NOT_H) << 9) & opp, 9),
            ((me << 8) & empty & goal, 8),
            (((me & NOT_A) << 7) & empty & goal, 7),
            (((me & NOT_H) << 9) & empty & goal, 9),
        )
        d = -1
    else:
        goal = ROW0
        groups = (
            (((me & NOT_A) >> 9) & opp, 9),
            (((me & NOT_H) >> 7) & opp, 7),
            ((me >> 8) & empty & goal, 8),
            (((me & NOT_A) >> 9) & empty & goal, 9),
            (((me & NOT_H) >> 7) & empty & goal, 7),
        )
        d = 1
    nup = not up
    for bb, sh in groups:
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            to = lsb.bit_length() - 1
            frm = to + d * sh
            bit = 1 << to
            me2 = (me ^ (1 << frm)) | bit
            opp2 = (opp ^ bit) if (opp & bit) else opp
            if (me2 & goal) or opp2 == 0:
                return WIN - ply
            score = -qsearch(opp2, me2, nup, -beta, -alpha, ply + 1)
            if score >= beta:
                return score
            if score > alpha:
                alpha = score
    return alpha


def negamax(me, opp, up, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 255) == 0 and time.time() >= deadline:
        raise TimeoutError
    if up:
        if opp & ROW0:
            return -WIN + ply
        key = me | (opp << 64)
    else:
        if opp & ROW7:
            return -WIN + ply
        key = opp | (me << 64) | (1 << 128)
    if me == 0:
        return -WIN + ply
    tt_move = None
    ent = TT.get(key)
    if ent is not None:
        if ent[0] >= depth:
            ef = ent[2]
            ev = ent[1]
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        tt_move = ent[3]
    if depth <= 0:
        return qsearch(me, opp, up, alpha, beta, ply)
    goal = ROW7 if up else ROW0
    moves = gen_moves(me, opp, up, tt_move,
                      killers[ply] if ply < MAX_PLY else None)
    if not moves:
        return -WIN + ply
    best = -INF
    best_move = None
    a0 = alpha
    nup = not up
    d1 = depth - 1
    first = True
    for i in range(len(moves)):
        s, frm, to, cap = moves[i]
        bit = 1 << to
        me2 = (me ^ (1 << frm)) | bit
        opp2 = (opp ^ bit) if cap else opp
        if (me2 & goal) or opp2 == 0:
            score = WIN - ply
        elif first:
            score = -negamax(opp2, me2, nup, d1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -negamax(opp2, me2, nup, d1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -negamax(opp2, me2, nup, d1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
            best_move = (frm, to)
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    if not cap and ply < MAX_PLY:
                        kl = killers[ply]
                        if kl[0] != best_move:
                            kl[1] = kl[0]
                            kl[0] = best_move
                    break
    if best <= a0:
        ef = 2
    elif best >= beta:
        ef = 1
    else:
        ef = 0
    TT[key] = (depth, best, ef, best_move)
    return best


def search_root(me, opp, up, depth):
    if up:
        key = me | (opp << 64)
    else:
        key = opp | (me << 64) | (1 << 128)
    tt_move = None
    ent = TT.get(key)
    if ent is not None:
        tt_move = ent[3]
    moves = gen_moves(me, opp, up, tt_move, killers[0])
    if not moves:
        return -WIN, None
    goal = ROW7 if up else ROW0
    best = -INF
    best_move = None
    alpha = -INF
    nup = not up
    d1 = depth - 1
    for s, frm, to, cap in moves:
        bit = 1 << to
        me2 = (me ^ (1 << frm)) | bit
        opp2 = (opp ^ bit) if cap else opp
        if (me2 & goal) or opp2 == 0:
            score = WIN
        else:
            score = -negamax(opp2, me2, nup, d1, -INF, -alpha, 1)
        if score > best:
            best = score
            best_move = (frm, to)
            if score > alpha:
                alpha = score
    TT[key] = (depth, best, 0, best_move)
    return best, best_move


# ---------------------------- policy ----------------------------

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]],
           color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global nodes, deadline, killers
    me_bb = 0
    for (r, c) in me:
        me_bb |= 1 << (r * 8 + c)
    opp_bb = 0
    for (r, c) in opp:
        opp_bb |= 1 << (r * 8 + c)
    up = (color == 'w') or (color == 'W')

    legal = gen_moves(me_bb, opp_bb, up, None, None)
    if not legal:
        # No legal move exists (should not happen); return a harmless move.
        if me_bb:
            sq = (me_bb & -me_bb).bit_length() - 1
            r, c = divmod(sq, 8)
            dr = 1 if up else -1
            nr = r + dr
            if 0 <= nr <= 7:
                return ((r, c), (nr, c))
        return ((0, 0), (0, 0))
    if len(legal) == 1:
        _, frm, to, _ = legal[0]
        return ((frm >> 3, frm & 7), (to >> 3, to & 7))

    if len(TT) > 1000000:
        TT.clear()
    killers = [[None, None] for _ in range(MAX_PLY)]
    nodes = 0
    deadline = time.time() + TIME_LIMIT
    best_move = (legal[0][1], legal[0][2])

    try:
        t_prev = 0.0
        for depth in range(1, MAX_DEPTH + 1):
            t0 = time.time()
            val, mv = search_root(me_bb, opp_bb, up, depth)
            t_prev = time.time() - t0
            if mv is not None:
                best_move = mv
            if val >= WIN - 64 or val <= -WIN + 64:
                break
            if time.time() + max(4.0 * t_prev, 0.03) >= deadline:
                break
    except TimeoutError:
        pass
    except Exception:
        pass

    frm, to = best_move
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))
