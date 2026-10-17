
import time
import random

FILES = 'abcdefgh'
MATE = 100000
INF = 200000
EPF = 32768      # en-passant capture flag
DPF = 65536      # double pawn push flag
CSF = 131072     # castling flag

ORDER = 'PNBRQKpnbrqk'
PI = {c: i for i, c in enumerate(ORDER)}
PTV = (100, 320, 330, 500, 975, 0)
PHW = (0, 1, 1, 2, 4, 0, 0, 1, 1, 2, 4, 0)

_rng = random.Random(20240311)
def _r64():
    return _rng.getrandbits(64)

ZP = [[_r64() for _ in range(64)] for _ in range(12)]
ZSIDE = _r64()
ZC = [_r64() for _ in range(16)]
ZE = [_r64() for _ in range(8)]

KN = [None] * 64
KG = [None] * 64
ORT = [None] * 64
DIA = [None] * 64
RQ = [None] * 64

def _build():
    nd = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
    kd = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
    od = ((1, 0), (-1, 0), (0, 1), (0, -1))
    dd = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    for s in range(64):
        f = s & 7
        r = s >> 3
        l = []
        for df, dr in nd:
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                l.append(nr * 8 + nf)
        KN[s] = l
        l = []
        for df, dr in kd:
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                l.append(nr * 8 + nf)
        KG[s] = l
        ro = []
        for df, dr in od:
            ray = []
            nf = f + df
            nr = r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                ray.append(nr * 8 + nf)
                nf += df
                nr += dr
            ro.append(ray)
        ORT[s] = ro
        rd = []
        for df, dr in dd:
            ray = []
            nf = f + df
            nr = r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                ray.append(nr * 8 + nf)
                nf += df
                nr += dr
            rd.append(ray)
        DIA[s] = rd
        RQ[s] = ro + rd

_build()

P_MG_T = (
  0,  0,  0,  0,  0,  0,  0,  0,
 50, 50, 50, 50, 50, 50, 50, 50,
 10, 10, 20, 30, 30, 20, 10, 10,
  5,  5, 10, 25, 25, 10,  5,  5,
  0,  0,  0, 20, 20,  0,  0,  0,
  5, -5,-10,  0,  0,-10, -5,  5,
  5, 10, 10,-20,-20, 10, 10,  5,
  0,  0,  0,  0,  0,  0,  0,  0)
P_EG_T = (
  0,  0,  0,  0,  0,  0,  0,  0,
 70, 70, 70, 70, 70, 70, 70, 70,
 40, 40, 40, 45, 45, 40, 40, 40,
 20, 20, 25, 30, 30, 25, 20, 20,
 10, 10, 15, 20, 20, 15, 10, 10,
  5,  5, 10, 15, 15, 10,  5,  5,
  0,  0,  0,  5,  5,  0,  0,  0,
  0,  0,  0,  0,  0,  0,  0,  0)
N_T = (
-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,  0,  0,  0,  0,-20,-40,
-30,  0, 10, 15, 15, 10,  0,-30,
-30,  5, 15, 20, 20, 15,  5,-30,
-30,  0, 15, 20, 20, 15,  0,-30,
-30,  5, 10, 15, 15, 10,  5,-30,
-40,-20,  0,  5,  5,  0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50)
B_T = (
-20,-10,-10,-10,-10,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5, 10, 10,  5,  0,-10,
-10,  5,  5, 10, 10,  5,  5,-10,
-10,  0, 10, 10, 10, 10,  0,-10,
-10, 10, 10, 10, 10, 10, 10,-10,
-10,  5,  0,  0,  0,  0,  5,-10,
-20,-10,-10,-10,-10,-10,-10,-20)
R_T = (
 0,  0,  0,  0,  0,  0,  0,  0,
 5, 10, 10, 10, 10, 10, 10,  5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
 0,  0,  0,  5,  5,  0,  0,  0)
Q_T = (
-20,-10,-10, -5, -5,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5,  5,  5,  5,  0,-10,
 -5,  0,  5,  5,  5,  5,  0, -5,
  0,  0,  5,  5,  5,  5,  0, -5,
-10,  5,  5,  5,  5,  5,  0,-10,
-10,  0,  5,  0,  0,  0,  0,-10,
-20,-10,-10, -5, -5,-10,-10,-20)
K_MG_T = (
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-20,-30,-30,-40,-40,-30,-30,-20,
-10,-20,-20,-20,-20,-20,-20,-10,
 20, 20,  0,  0,  0,  0, 20, 20,
 20, 30, 10,  0,  0, 10, 30, 20)
K_EG_T = (
-50,-40,-30,-20,-20,-30,-40,-50,
-30,-20,-10,  0,  0,-10,-20,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-30,  0,  0,  0,  0,-30,-30,
-50,-30,-30,-30,-30,-30,-30,-50)

MAT = (100, 320, 330, 500, 975, 0)
TBM = (P_MG_T, N_T, B_T, R_T, Q_T, K_MG_T)
TBE = (P_EG_T, N_T, B_T, R_T, Q_T, K_EG_T)

MGV = [None] * 12
EGV = [None] * 12
for ci in range(12):
    t = ci % 6
    tmg = TBM[t]
    teg = TBE[t]
    mgrow = [0] * 64
    egrow = [0] * 64
    if ci < 6:
        for s in range(64):
            mgrow[s] = MAT[t] + tmg[s ^ 56]
            egrow[s] = MAT[t] + teg[s ^ 56]
    else:
        for s in range(64):
            mgrow[s] = -(MAT[t] + tmg[s])
            egrow[s] = -(MAT[t] + teg[s])
    MGV[ci] = mgrow
    EGV[ci] = egrow

# ---------------- global position state ----------------
B = ['.'] * 64
TURN = 0
CASTLE = 0
EP = -1
KINGS = [4, 60]
H = 0
MG = 0
EG = 0
PH = 0
CNT = [0] * 12
UNDO = []
HISTL = []
HIST_SET = set()
TT = {}
KILL1 = [0] * 128
KILL2 = [0] * 128
HISTT = [[0] * 4096, [0] * 4096]
NODES = 0
TSTART = 0.0
DEADLINE = 0.0
BUDGET = 0.85

INIT_B = ['.'] * 64
_back = 'RNBQKBNR'
for _i in range(8):
    INIT_B[_i] = _back[_i]
    INIT_B[56 + _i] = _back[_i].lower()
    INIT_B[8 + _i] = 'P'
    INIT_B[48 + _i] = 'p'

TRACK = {'on': False, 'snap': None}

class Abort(Exception):
    pass

def board_from(pieces):
    nb = ['.'] * 64
    for sq, pc in pieces.items():
        f = ord(sq[0]) - 97
        r = ord(sq[1]) - 49
        c = pc[1]
        nb[r * 8 + f] = c if pc[0] == 'w' else c.lower()
    return nb

def compute_hash():
    h = 0
    for s in range(64):
        p = B[s]
        if p != '.':
            h ^= ZP[PI[p]][s]
    if TURN == 1:
        h ^= ZSIDE
    h ^= ZC[CASTLE]
    if EP >= 0:
        h ^= ZE[EP & 7]
    return h

def recalc():
    global MG, EG, PH
    MG = 0
    EG = 0
    PH = 0
    for i in range(12):
        CNT[i] = 0
    for s in range(64):
        p = B[s]
        if p == '.':
            continue
        pi = PI[p]
        MG += MGV[pi][s]
        EG += EGV[pi][s]
        PH += PHW[pi]
        CNT[pi] += 1
        if p == 'K':
            KINGS[0] = s
        elif p == 'k':
            KINGS[1] = s

def restore(sn):
    global TURN, CASTLE, EP, H, MG, EG, PH
    B[:] = sn[0]
    TURN = sn[1]
    CASTLE = sn[2]
    EP = sn[3]
    H = sn[4]
    MG = sn[5]
    EG = sn[6]
    PH = sn[7]
    CNT[:] = sn[8]
    KINGS[0] = sn[9]
    KINGS[1] = sn[10]
    del UNDO[:]

def attacked(sq, by):
    b = B
    f = sq & 7
    if by == 0:
        if sq >= 8:
            if f > 0 and b[sq - 9] == 'P':
                return True
            if f < 7 and b[sq - 7] == 'P':
                return True
        for t in KN[sq]:
            if b[t] == 'N':
                return True
        for t in KG[sq]:
            if b[t] == 'K':
                return True
        for ray in ORT[sq]:
            for t in ray:
                p = b[t]
                if p != '.':
                    if p == 'R' or p == 'Q':
                        return True
                    break
        for ray in DIA[sq]:
            for t in ray:
                p = b[t]
                if p != '.':
                    if p == 'B' or p == 'Q':
                        return True
                    break
    else:
        if sq < 56:
            if f > 0 and b[sq + 7] == 'p':
                return True
            if f < 7 and b[sq + 9] == 'p':
                return True
        for t in KN[sq]:
            if b[t] == 'n':
                return True
        for t in KG[sq]:
            if b[t] == 'k':
                return True
        for ray in ORT[sq]:
            for t in ray:
                p = b[t]
                if p != '.':
                    if p == 'r' or p == 'q':
                        return True
                    break
        for ray in DIA[sq]:
            for t in ray:
                p = b[t]
                if p != '.':
                    if p == 'b' or p == 'q':
                        return True
                    break
    return False

def make(m):
    global TURN, CASTLE, EP, H, MG, EG, PH
    b = B
    fr = m & 63
    to = (m >> 6) & 63
    pr = (m >> 12) & 7
    pi = b[fr]
    cap = b[to]
    pii = PI[pi]
    UNDO.append((m, pi, cap, CASTLE, EP, H, KINGS[0], KINGS[1]))
    h = H ^ ZSIDE
    if EP >= 0:
        h ^= ZE[EP & 7]
    h ^= ZC[CASTLE]
    b[fr] = '.'
    h ^= ZP[pii][fr]
    MG -= MGV[pii][fr]
    EG -= EGV[pii][fr]
    if cap != '.':
        ci = PI[cap]
        h ^= ZP[ci][to]
        MG -= MGV[ci][to]
        EG -= EGV[ci][to]
        PH -= PHW[ci]
        CNT[ci] -= 1
    if m & EPF:
        capsq = to - 8 if TURN == 0 else to + 8
        cp = b[capsq]
        ci = PI[cp]
        b[capsq] = '.'
        h ^= ZP[ci][capsq]
        MG -= MGV[ci][capsq]
        EG -= EGV[ci][capsq]
        CNT[ci] -= 1
    if pr:
        nc = 'NBRQ'[pr - 1] if TURN == 0 else 'nbrq'[pr - 1]
        ni = PI[nc]
        b[to] = nc
        h ^= ZP[ni][to]
        MG += MGV[ni][to]
        EG += EGV[ni][to]
        PH += PHW[ni]
        CNT[pii] -= 1
        CNT[ni] += 1
    else:
        b[to] = pi
        h ^= ZP[pii][to]
        MG += MGV[pii][to]
        EG += EGV[pii][to]
    if m & CSF:
        if to == 6:
            rf, rt = 7, 5
        elif to == 2:
            rf, rt = 0, 3
        elif to == 62:
            rf, rt = 63, 61
        else:
            rf, rt = 56, 59
        rp = b[rf]
        ri = PI[rp]
        b[rf] = '.'
        b[rt] = rp
        h ^= ZP[ri][rf] ^ ZP[ri][rt]
        MG += MGV[ri][rt] - MGV[ri][rf]
        EG += EGV[ri][rt] - EGV[ri][rf]
    if pi == 'K':
        KINGS[0] = to
    elif pi == 'k':
        KINGS[1] = to
    ncst = CASTLE
    if pi == 'K':
        ncst &= 12
    elif pi == 'k':
        ncst &= 3
    if fr == 0 or to == 0:
        ncst &= 13
    if fr == 7 or to == 7:
        ncst &= 14
    if fr == 56 or to == 56:
        ncst &= 7
    if fr == 63 or to == 63:
        ncst &= 11
    CASTLE = ncst
    h ^= ZC[ncst]
    if m & DPF:
        EP = fr + 8 if TURN == 0 else fr - 8
        h ^= ZE[EP & 7]
    else:
        EP = -1
    H = h
    TURN ^= 1

def unmake():
    global TURN, CASTLE, EP, H, MG, EG, PH
    m, pi, cap, oc, oe, oh, owk, obk = UNDO.pop()
    TURN ^= 1
    b = B
    fr = m & 63
    to = (m >> 6) & 63
    pr = (m >> 12) & 7
    pii = PI[pi]
    if m & CSF:
        if to == 6:
            rf, rt = 7, 5
        elif to == 2:
            rf, rt = 0, 3
        elif to == 62:
            rf, rt = 63, 61
        else:
            rf, rt = 56, 59
        rp = b[rt]
        ri = PI[rp]
        b[rt] = '.'
        b[rf] = rp
        MG += MGV[ri][rf] - MGV[ri][rt]
        EG += EGV[ri][rf] - EGV[ri][rt]
    if pr:
        np = b[to]
        ni = PI[np]
        MG -= MGV[ni][to]
        EG -= EGV[ni][to]
        PH -= PHW[ni]
        CNT[ni] -= 1
        CNT[pii] += 1
    else:
        MG -= MGV[pii][to]
        EG -= EGV[pii][to]
    b[fr] = pi
    MG += MGV[pii][fr]
    EG += EGV[pii][fr]
    b[to] = cap
    if cap != '.':
        ci = PI[cap]
        MG += MGV[ci][to]
        EG += EGV[ci][to]
        PH += PHW[ci]
        CNT[ci] += 1
    if m & EPF:
        capsq = to - 8 if TURN == 0 else to + 8
        cp = 'p' if TURN == 0 else 'P'
        ci = PI[cp]
        b[capsq] = cp
        MG += MGV[ci][capsq]
        EG += EGV[ci][capsq]
        CNT[ci] += 1
    KINGS[0] = owk
    KINGS[1] = obk
    CASTLE = oc
    EP = oe
    H = oh

def gen_pseudo(caps=False):
    b = B
    mv = []
    ap = mv.append
    ep = EP
    if TURN == 0:
        for s in range(64):
            p = b[s]
            if p < 'A' or p > 'Z':
                continue
            if p == 'P':
                u = s + 8
                f = s & 7
                if b[u] == '.':
                    if s >= 48:
                        ap(s | (u << 6) | 16384)
                        ap(s | (u << 6) | 12288)
                        ap(s | (u << 6) | 8192)
                        ap(s | (u << 6) | 4096)
                    elif not caps:
                        ap(s | (u << 6))
                        if s < 16 and b[s + 16] == '.':
                            ap(s | ((s + 16) << 6) | DPF)
                if f > 0:
                    t = s + 7
                    q = b[t]
                    if q >= 'a':
                        if s >= 48:
                            ap(s | (t << 6) | 16384)
                            ap(s | (t << 6) | 12288)
                            ap(s | (t << 6) | 8192)
                            ap(s | (t << 6) | 4096)
                        else:
                            ap(s | (t << 6))
                    elif t == ep:
                        ap(s | (t << 6) | EPF)
                if f < 7:
                    t = s + 9
                    q = b[t]
                    if q >= 'a':
                        if s >= 48:
                            ap(s | (t << 6) | 16384)
                            ap(s | (t << 6) | 12288)
                            ap(s | (t << 6) | 8192)
                            ap(s | (t << 6) | 4096)
                        else:
                            ap(s | (t << 6))
                    elif t == ep:
                        ap(s | (t << 6) | EPF)
            elif p == 'N':
                for t in KN[s]:
                    q = b[t]
                    if q == '.':
                        if not caps:
                            ap(s | (t << 6))
                    elif q >= 'a':
                        ap(s | (t << 6))
            elif p == 'K':
                for t in KG[s]:
                    q = b[t]
                    if q == '.':
                        if not caps:
                            ap(s | (t << 6))
                    elif q >= 'a':
                        ap(s | (t << 6))
                if not caps and s == 4:
                    cst = CASTLE
                    if (cst & 1) and b[5] == '.' and b[6] == '.' and b[7] == 'R' \
                            and not attacked(4, 1) and not attacked(5, 1) and not attacked(6, 1):
                        ap(4 | (6 << 6) | CSF)
                    if (cst & 2) and b[3] == '.' and b[2] == '.' and b[1] == '.' and b[0] == 'R' \
                            and not attacked(4, 1) and not attacked(3, 1) and not attacked(2, 1):
                        ap(4 | (2 << 6) | CSF)
            else:
                if p == 'R':
                    rays = ORT[s]
                elif p == 'B':
                    rays = DIA[s]
                else:
                    rays = RQ[s]
                for ray in rays:
                    for t in ray:
                        q = b[t]
                        if q == '.':
                            if not caps:
                                ap(s | (t << 6))
                        else:
                            if q >= 'a':
                                ap(s | (t << 6))
                            break
    else:
        for s in range(64):
            p = b[s]
            if p < 'a':
                continue
            if p == 'p':
                u = s - 8
                f = s & 7
                if b[u] == '.':
                    if s < 16:
                        ap(s | (u << 6) | 16384)
                        ap(s | (u << 6) | 12288)
                        ap(s | (u << 6) | 8192)
                        ap(s | (u << 6) | 4096)
                    elif not caps:
                        ap(s | (u << 6))
                        if s >= 48 and b[s - 16] == '.':
                            ap(s | ((s - 16) << 6) | DPF)
                if f > 0:
                    t = s - 9
                    q = b[t]
                    if q != '.' and q <= 'Z':
                        if s < 16:
                            ap(s | (t << 6) | 16384)
                            ap(s | (t << 6) | 12288)
                            ap(s | (t << 6) | 8192)
                            ap(s | (t << 6) | 4096)
                        else:
                            ap(s | (t << 6))
                    elif t == ep:
                        ap(s | (t << 6) | EPF)
                if f < 7:
                    t = s - 7
                    q = b[t]
                    if q != '.' and q <= 'Z':
                        if s < 16:
                            ap(s | (t << 6) | 16384)
                            ap(s | (t << 6) | 12288)
                            ap(s | (t << 6) | 8192)
                            ap(s | (t << 6) | 4096)
                        else:
                            ap(s | (t << 6))
                    elif t == ep:
                        ap(s | (t << 6) | EPF)
            elif p == 'n':
                for t in KN[s]:
                    q = b[t]
                    if q == '.':
                        if not caps:
                            ap(s | (t << 6))
                    elif q <= 'Z':
                        ap(s | (t << 6))
            elif p == 'k':
                for t in KG[s]:
                    q = b[t]
                    if q == '.':
                        if not caps:
                            ap(s | (t << 6))
                    elif q <= 'Z':
                        ap(s | (t << 6))
                if not caps and s == 60:
                    cst = CASTLE
                    if (cst & 4) and b[61] == '.' and b[62] == '.' and b[63] == 'r' \
                            and not attacked(60, 0) and not attacked(61, 0) and not attacked(62, 0):
                        ap(60 | (62 << 6) | CSF)
                    if (cst & 8) and b[57] == '.' and b[58] == '.' and b[59] == '.' and b[56] == 'r' \
                            and not attacked(60, 0) and not attacked(59, 0) and not attacked(58, 0):
                        ap(60 | (58 << 6) | CSF)
            else:
                if p == 'r':
                    rays = ORT[s]
                elif p == 'b':
                    rays = DIA[s]
                else:
                    rays = RQ[s]
                for ray in rays:
                    for t in ray:
                        q = b[t]
                        if q == '.':
                            if not caps:
                                ap(s | (t << 6))
                        else:
                            if q <= 'Z':
                                ap(s | (t << 6))
                            break
    return mv

def legal_moves():
    res = []
    us = TURN
    them = us ^ 1
    for m in gen_pseudo():
        make(m)
        if not attacked(KINGS[us], them):
            res.append(m)
        unmake()
    return res

def evaluate():
    ph = PH if PH <= 24 else 24
    sc = (MG * ph + EG * (24 - ph)) // 24
    bp = (30 * ph + 50 * (24 - ph)) // 24
    if CNT[2] >= 2:
        sc += bp
    if CNT[8] >= 2:
        sc -= bp
    if ph <= 8 and (sc > 150 or sc < -150):
        k0 = KINGS[0]
        k1 = KINGS[1]
        md = abs((k0 & 7) - (k1 & 7)) + abs((k0 >> 3) - (k1 >> 3))
        lk = k1 if sc > 150 else k0
        f = lk & 7
        r = lk >> 3
        cmd = (3 - f if f < 4 else f - 4) + (3 - r if r < 4 else r - 4)
        bonus = 4 * cmd + 2 * (14 - md)
        if sc > 150:
            sc += bonus
        else:
            sc -= bonus
    if TURN == 0:
        return sc + 10
    return -sc + 10

def score_moves(moves, ttmove, ply):
    b = B
    out = []
    ap = out.append
    hk = HISTT[TURN]
    k1 = KILL1[ply]
    k2 = KILL2[ply]
    for m in moves:
        if m == ttmove:
            ap((1 << 26, m))
            continue
        to = (m >> 6) & 63
        cap = b[to]
        pr = (m >> 12) & 7
        if cap != '.' or (m & EPF):
            vi = PI[cap] % 6 if cap != '.' else 0
            sc = 1000000 + 10 * PTV[vi] - PTV[PI[b[m & 63]] % 6]
            if pr:
                sc += 9000
        elif pr:
            sc = 950000 + PTV[pr]
        elif m == k1 or m == k2:
            sc = 900000
        else:
            sc = hk[m & 4095]
            if sc > 800000:
                sc = 800000
        ap((sc, m))
    out.sort(reverse=True)
    return [x[1] for x in out]

def search(depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise Abort
    if ply > 0 and H in HIST_SET:
        return 0
    if ply >= 100:
        return evaluate()
    us = TURN
    them = us ^ 1
    incheck = attacked(KINGS[us], them)
    if incheck:
        depth += 1
    if depth <= 0:
        return qs(alpha, beta, ply)
    a0 = alpha
    ttmove = 0
    e = TT.get(H)
    if e is not None:
        ed, ef, es, em = e
        if ed >= depth:
            if es > MATE - 1000:
                ess = es - ply
            elif es < -MATE + 1000:
                ess = es + ply
            else:
                ess = es
            if ef == 0:
                return ess
            if ef == 1 and ess >= beta:
                return ess
            if ef == 2 and ess <= alpha:
                return ess
        ttmove = em
    moves = score_moves(gen_pseudo(), ttmove, ply)
    best = -INF
    bm = 0
    legal = 0
    for m in moves:
        cap = B[(m >> 6) & 63]
        iscap = cap != '.' or (m & EPF)
        pr = (m >> 12) & 7
        make(m)
        if attacked(KINGS[us], them):
            unmake()
            continue
        legal += 1
        if legal == 1:
            sc = -search(depth - 1, -beta, -alpha, ply + 1)
        else:
            if depth >= 3 and legal > 4 and not incheck and not iscap and not pr:
                sc = -search(depth - 2, -alpha - 1, -alpha, ply + 1)
                if sc > alpha:
                    sc = -search(depth - 1, -alpha - 1, -alpha, ply + 1)
            else:
                sc = -search(depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < sc < beta:
                sc = -search(depth - 1, -beta, -alpha, ply + 1)
        unmake()
        if sc > best:
            best = sc
            bm = m
        if sc > alpha:
            alpha = sc
            if alpha >= beta:
                if not iscap and not pr:
                    KILL2[ply] = KILL1[ply]
                    KILL1[ply] = m
                    HISTT[us][m & 4095] += depth * depth
                break
    if legal == 0:
        return (-MATE + ply) if incheck else 0
    if best <= a0:
        fl = 2
    elif best >= beta:
        fl = 1
    else:
        fl = 0
    ss = best
    if ss > MATE - 1000:
        ss += ply
    elif ss < -MATE + 1000:
        ss -= ply
    TT[H] = (depth, fl, ss, bm)
    return best

def qs(alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise Abort
    if ply >= 100:
        return evaluate()
    if H in HIST_SET:
        return 0
    us = TURN
    them = us ^ 1
    incheck = attacked(KINGS[us], them)
    stand = evaluate()
    if not incheck:
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
    moves = score_moves(gen_pseudo(caps=not incheck), 0, ply)
    legal = 0
    for m in moves:
        pr = (m >> 12) & 7
        if not incheck:
            cap = B[(m >> 6) & 63]
            gain = (PTV[PI[cap] % 6] if cap != '.' else (100 if (m & EPF) else 0)) + (PTV[pr] if pr else 0)
            if stand + gain + 150 <= alpha:
                continue
        make(m)
        if attacked(KINGS[us], them):
            unmake()
            continue
        legal += 1
        sc = -qs(-beta, -alpha, ply + 1)
        unmake()
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
    if incheck and legal == 0:
        return -MATE + ply
    return alpha

def root_search(depth, moves):
    alpha = -INF
    beta = INF
    best = moves[0]
    bs = -INF
    mi = 0
    for m in moves:
        make(m)
        mi += 1
        if mi == 1:
            sc = -search(depth - 1, -beta, -alpha, 1)
        else:
            sc = -search(depth - 1, -alpha - 1, -alpha, 1)
            if alpha < sc < beta:
                sc = -search(depth - 1, -beta, -alpha, 1)
        unmake()
        if sc > bs:
            bs = sc
            best = m
        if sc > alpha:
            alpha = sc
    return best, bs

def think():
    legal = legal_moves()
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]
    snap = (B[:], TURN, CASTLE, EP, H, MG, EG, PH, CNT[:], KINGS[0], KINGS[1])
    best = legal[0]
    legal = score_moves(legal, 0, 0)
    try:
        for depth in range(1, 60):
            if time.perf_counter() > DEADLINE:
                break
            bm, bs = root_search(depth, legal)
            best = bm
            legal.remove(bm)
            legal.insert(0, bm)
            if bs >= MATE - 100:
                break
            if time.perf_counter() - TSTART > BUDGET * 0.5:
                break
    except Abort:
        pass
    restore(snap)
    return best

def m2u(m):
    fr = m & 63
    to = (m >> 6) & 63
    s = FILES[fr & 7] + str((fr >> 3) + 1) + FILES[to & 7] + str((to >> 3) + 1)
    pr = (m >> 12) & 7
    if pr:
        s += 'nbrq'[pr - 1]
    return s

def setup_fresh(nb, turn):
    global TURN, CASTLE, EP, H
    B[:] = nb
    TURN = turn
    CASTLE = 0
    EP = -1
    KINGS[0] = -1
    KINGS[1] = -1
    recalc()
    H = compute_hash()

def setup(nb, turn):
    global TURN, CASTLE, EP, H, HISTL, HIST_SET
    synced = False
    if TRACK['on']:
        restore(TRACK['snap'])
        if TURN == (turn ^ 1):
            matches = []
            for m in legal_moves():
                make(m)
                if B == nb:
                    matches.append((m, CASTLE, EP))
                unmake()
            if matches:
                m0 = matches[0][0]
                cst = matches[0][1]
                epv = matches[0][2]
                for _, c, e in matches[1:]:
                    cst &= c
                    if e != epv:
                        epv = -1
                make(m0)
                CASTLE = cst
                EP = epv
                H = compute_hash()
                HISTL.append(H)
                HIST_SET = set(HISTL)
                synced = True
        if not synced:
            TRACK['on'] = False
    if synced:
        return
    if turn == 0 and nb == INIT_B:
        setup_fresh(nb, 0)
        CASTLE = 15
        H = compute_hash()
        HISTL = [H]
        HIST_SET = {H}
        return
    if turn == 1:
        setup_fresh(INIT_B, 0)
        CASTLE = 15
        H = compute_hash()
        hinit = H
        found = None
        for m in legal_moves():
            make(m)
            ok = (B == nb)
            unmake()
            if ok:
                found = m
                break
        if found is not None:
            make(found)
            HISTL = [hinit, H]
            HIST_SET = set(HISTL)
            return
    setup_fresh(nb, turn)
    HISTL = [H]
    HIST_SET = {H}

def commit(m):
    global HIST_SET
    make(m)
    TRACK['snap'] = (B[:], TURN, CASTLE, EP, H, MG, EG, PH, CNT[:], KINGS[0], KINGS[1])
    TRACK['on'] = True
    HISTL.append(H)
    HIST_SET = set(HISTL)

def policy(pieces: dict, to_play: str) -> str:
    global TSTART, DEADLINE, NODES
    TSTART = time.perf_counter()
    DEADLINE = TSTART + BUDGET
    NODES = 0
    turn = 0 if to_play == 'white' else 1
    try:
        nb = board_from(pieces)
        if len(TT) > 1500000:
            TT.clear()
        setup(nb, turn)
        best = think()
        if not best:
            return 'a1a1'
        commit(best)
        return m2u(best)
    except Exception:
        try:
            TRACK['on'] = False
            setup_fresh(board_from(pieces), turn)
            lm = legal_moves()
            if lm:
                return m2u(lm[0])
        except Exception:
            pass
        return 'a1a1'
