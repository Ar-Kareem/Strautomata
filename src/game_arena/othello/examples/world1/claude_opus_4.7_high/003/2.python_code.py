
import numpy as np
import time

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xfefefefefefefefe
NOT_H = 0x7f7f7f7f7f7f7f7f

def sN(b):  return b >> 8
def sS(b):  return (b << 8) & FULL
def sE(b):  return (b << 1) & NOT_A
def sW(b):  return (b >> 1) & NOT_H
def sNE(b): return (b >> 7) & NOT_A
def sNW(b): return (b >> 9) & NOT_H
def sSE(b): return (b << 9) & NOT_A
def sSW(b): return (b << 7) & NOT_H

SHIFTS = (sN, sS, sE, sW, sNE, sNW, sSE, sSW)

def legal_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    for sh in SHIFTS:
        x = sh(P) & O
        x |= sh(x) & O
        x |= sh(x) & O
        x |= sh(x) & O
        x |= sh(x) & O
        x |= sh(x) & O
        moves |= sh(x) & empty
    return moves

def get_flips(P, O, sq):
    flips = 0
    for sh in SHIFTS:
        f = 0
        x = sh(sq)
        while x & O:
            f |= x
            x = sh(x)
        if x & P:
            flips |= f
    return flips

def play(P, O, sq):
    f = get_flips(P, O, sq)
    return (P | f | sq, O & ~f)

WEIGHTS_LIST = [
    120, -20, 20,  5,  5, 20, -20, 120,
    -20, -40, -5, -5, -5, -5, -40, -20,
     20,  -5, 15,  3,  3, 15,  -5,  20,
      5,  -5,  3,  3,  3,  3,  -5,   5,
      5,  -5,  3,  3,  3,  3,  -5,   5,
     20,  -5, 15,  3,  3, 15,  -5,  20,
    -20, -40, -5, -5, -5, -5, -40, -20,
    120, -20, 20,  5,  5, 20, -20, 120,
]
WEIGHT_MASKS = {}
for i, w in enumerate(WEIGHTS_LIST):
    WEIGHT_MASKS[w] = WEIGHT_MASKS.get(w, 0) | (1 << i)
WEIGHT_ITEMS = list(WEIGHT_MASKS.items())

CORNER_MASK = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

def popcount(x):
    return bin(x).count('1')

def evaluate(P, O, empty_count):
    s = 0
    for w, m in WEIGHT_ITEMS:
        s += w * (popcount(P & m) - popcount(O & m))
    pm = popcount(legal_moves(P, O))
    om = popcount(legal_moves(O, P))
    if pm + om > 0:
        s += 15 * (pm - om)
    s += 30 * (popcount(P & CORNER_MASK) - popcount(O & CORNER_MASK))
    if empty_count < 12:
        s += 8 * (popcount(P) - popcount(O))
    return s

INF = 10**9

class Timeout(Exception): pass

def alphabeta(P, O, depth, alpha, beta, passed, deadline):
    if time.time() > deadline:
        raise Timeout
    if depth <= 0:
        return evaluate(P, O, 64 - popcount(P | O))
    moves = legal_moves(P, O)
    if moves == 0:
        if passed:
            pc = popcount(P); oc = popcount(O)
            if pc > oc: return 100000 + pc - oc
            if pc < oc: return -100000 - (oc - pc)
            return 0
        return -alphabeta(O, P, depth - 1, -beta, -alpha, True, deadline)
    mv = []
    m = moves
    while m:
        sq = m & -m
        m ^= sq
        mv.append(sq)
    if depth >= 3 and len(mv) > 1:
        scored = []
        for sq in mv:
            P2, O2 = play(P, O, sq)
            om_cnt = popcount(legal_moves(O2, P2))
            bonus = -500 if (sq & CORNER_MASK) else 0
            scored.append((bonus + om_cnt, sq))
        scored.sort()
        mv = [s for _, s in scored]
    best = -INF
    for sq in mv:
        P2, O2 = play(P, O, sq)
        v = -alphabeta(O2, P2, depth - 1, -beta, -alpha, False, deadline)
        if v > best:
            best = v
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    return best

def endgame_solve(P, O, alpha, beta, passed, deadline):
    if time.time() > deadline:
        raise Timeout
    moves = legal_moves(P, O)
    if moves == 0:
        if passed:
            return popcount(P) - popcount(O)
        return -endgame_solve(O, P, -beta, -alpha, True, deadline)
    mv = []
    m = moves
    while m:
        sq = m & -m
        m ^= sq
        mv.append(sq)
    if len(mv) > 1:
        scored = []
        for sq in mv:
            P2, O2 = play(P, O, sq)
            om_cnt = popcount(legal_moves(O2, P2))
            bonus = -500 if (sq & CORNER_MASK) else 0
            scored.append((bonus + om_cnt, sq))
        scored.sort()
        mv = [s for _, s in scored]
    best = -INF
    for sq in mv:
        P2, O2 = play(P, O, sq)
        v = -endgame_solve(O2, P2, -beta, -alpha, False, deadline)
        if v > best:
            best = v
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    return best

def policy(you, opponent):
    P = 0; O = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                P |= 1 << (r * 8 + c)
            elif opponent[r][c]:
                O |= 1 << (r * 8 + c)
    moves_bb = legal_moves(P, O)
    if moves_bb == 0:
        return "pass"
    moves = []
    m = moves_bb
    while m:
        sq = m & -m
        m ^= sq
        moves.append(sq)
    best_move = moves[0]
    if len(moves) == 1:
        idx = best_move.bit_length() - 1
        return chr(ord('a') + (idx % 8)) + str((idx // 8) + 1)
    empty_count = 64 - popcount(P | O)
    deadline = time.time() + 0.82
    scored = []
    for sq in moves:
        P2, O2 = play(P, O, sq)
        om_cnt = popcount(legal_moves(O2, P2))
        bonus = -1000 if (sq & CORNER_MASK) else 0
        scored.append((bonus + om_cnt, sq))
    scored.sort()
    ordered = [s for _, s in scored]
    best_move = ordered[0]
    try:
        if empty_count <= 12:
            alpha = -INF
            local_best = ordered[0]
            for sq in ordered:
                P2, O2 = play(P, O, sq)
                v = -endgame_solve(O2, P2, -INF, -alpha, False, deadline)
                if v > alpha:
                    alpha = v
                    local_best = sq
            best_move = local_best
        else:
            for depth in range(2, 12):
                try:
                    if best_move in ordered and ordered[0] != best_move:
                        ordered.remove(best_move)
                        ordered.insert(0, best_move)
                    alpha = -INF
                    local_best = ordered[0]
                    completed = True
                    for sq in ordered:
                        P2, O2 = play(P, O, sq)
                        v = -alphabeta(O2, P2, depth - 1, -INF, -alpha, False, deadline)
                        if v > alpha:
                            alpha = v
                            local_best = sq
                    if completed:
                        best_move = local_best
                except Timeout:
                    break
    except Timeout:
        pass
    idx = best_move.bit_length() - 1
    return chr(ord('a') + (idx % 8)) + str((idx // 8) + 1)
