
import numpy as np
import time

FULL = (1 << 64) - 1
NA = 0xFEFEFEFEFEFEFEFE
NH = 0x7F7F7F7F7F7F7F7F

WEIGHTS = [
    120, -20, 20,  5,  5, 20, -20, 120,
    -20, -40, -5, -5, -5, -5, -40, -20,
     20,  -5, 15,  3,  3, 15,  -5,  20,
      5,  -5,  3,  3,  3,  3,  -5,   5,
      5,  -5,  3,  3,  3,  3,  -5,   5,
     20,  -5, 15,  3,  3, 15,  -5,  20,
    -20, -40, -5, -5, -5, -5, -40, -20,
    120, -20, 20,  5,  5, 20, -20, 120
]

def sN(x): return x >> 8
def sS(x): return (x << 8) & FULL
def sE(x): return (x << 1) & NA
def sW(x): return (x >> 1) & NH
def sNE(x): return (x >> 7) & NA
def sNW(x): return (x >> 9) & NH
def sSE(x): return (x << 9) & NA
def sSW(x): return (x << 7) & NH

SHIFTS = (sN, sS, sE, sW, sNE, sNW, sSE, sSW)

def gen_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    for sh in SHIFTS:
        c = sh(P) & O
        c |= sh(c) & O
        c |= sh(c) & O
        c |= sh(c) & O
        c |= sh(c) & O
        c |= sh(c) & O
        moves |= sh(c) & empty
    return moves

def get_flips(m, P, O):
    flips = 0
    for sh in SHIFTS:
        f = 0
        x = sh(m) & O
        while x != 0:
            f |= x
            nxt = sh(x)
            if nxt & P:
                flips |= f
                break
            if not (nxt & O):
                break
            x = nxt
    return flips

def apply_move(P, O, mb):
    m = 1 << mb
    flips = get_flips(m, P, O)
    return (P | m | flips), (O & ~flips)

CORNERS = (1<<0) | (1<<7) | (1<<56) | (1<<63)

def popcount(x):
    return bin(x).count('1')

def pos_score(P):
    s = 0
    x = P
    while x:
        b = x & -x
        s += WEIGHTS[b.bit_length() - 1]
        x ^= b
    return s

def evaluate(P, O):
    score = pos_score(P) - pos_score(O)
    pm = popcount(gen_moves(P, O))
    om = popcount(gen_moves(O, P))
    if pm + om:
        score += 6 * (pm - om)
    pc = popcount(P & CORNERS)
    oc = popcount(O & CORNERS)
    score += 80 * (pc - oc)
    return score

class TimeOut(Exception):
    pass

def alphabeta(P, O, depth, alpha, beta, passed, deadline):
    if time.time() > deadline:
        raise TimeOut()
    moves = gen_moves(P, O)
    if moves == 0:
        if passed:
            d = popcount(P) - popcount(O)
            if d > 0: return None, 1000000 + d
            if d < 0: return None, -1000000 + d
            return None, 0
        _, s = alphabeta(O, P, depth, -beta, -alpha, True, deadline)
        return None, -s
    if depth == 0:
        return None, evaluate(P, O)
    move_list = []
    x = moves
    while x:
        b = x & -x
        idx = b.bit_length() - 1
        move_list.append((WEIGHTS[idx], idx))
        x ^= b
    move_list.sort(reverse=True)
    best_move = move_list[0][1]
    best_score = -10**9
    for _, mb in move_list:
        nP, nO = apply_move(P, O, mb)
        _, s = alphabeta(nO, nP, depth - 1, -beta, -alpha, False, deadline)
        s = -s
        if s > best_score:
            best_score = s
            best_move = mb
        if s > alpha:
            alpha = s
        if alpha >= beta:
            break
    return best_move, best_score

def endgame_solve(P, O, alpha, beta, passed, deadline):
    if time.time() > deadline:
        raise TimeOut()
    moves = gen_moves(P, O)
    if moves == 0:
        if passed:
            return None, popcount(P) - popcount(O)
        _, s = endgame_solve(O, P, -beta, -alpha, True, deadline)
        return None, -s
    move_list = []
    x = moves
    while x:
        b = x & -x
        idx = b.bit_length() - 1
        move_list.append((WEIGHTS[idx], idx))
        x ^= b
    move_list.sort(reverse=True)
    best_move = move_list[0][1]
    best_score = -1000
    for _, mb in move_list:
        nP, nO = apply_move(P, O, mb)
        _, s = endgame_solve(nO, nP, -beta, -alpha, False, deadline)
        s = -s
        if s > best_score:
            best_score = s
            best_move = mb
        if s > alpha:
            alpha = s
        if alpha >= beta:
            break
    return best_move, best_score

def policy(you, opponent):
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            if you[r, c]:
                P |= 1 << (r * 8 + c)
            if opponent[r, c]:
                O |= 1 << (r * 8 + c)
    moves = gen_moves(P, O)
    if moves == 0:
        return "pass"
    empties = 64 - popcount(P | O)
    deadline = time.time() + 0.85
    # default fallback: first legal move
    fb = moves & -moves
    best_move = fb.bit_length() - 1

    try:
        if empties <= 10:
            bm, _ = endgame_solve(P, O, -1000, 1000, False, deadline)
            if bm is not None:
                best_move = bm
        else:
            for d in range(2, 20):
                bm, _ = alphabeta(P, O, d, -10**9, 10**9, False, deadline)
                if bm is not None:
                    best_move = bm
                if time.time() > deadline:
                    break
    except TimeOut:
        pass
    except Exception:
        pass

    r, c = divmod(best_move, 8)
    return "abcdefgh"[c] + str(r + 1)
