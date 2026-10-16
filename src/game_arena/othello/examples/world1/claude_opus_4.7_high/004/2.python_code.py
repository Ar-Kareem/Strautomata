
import numpy as np
import time

MASK = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xfefefefefefefefe
NOT_H = 0x7f7f7f7f7f7f7f7f

def sN(x): return x >> 8
def sS(x): return (x << 8) & MASK
def sE(x): return (x & NOT_H) << 1
def sW(x): return (x & NOT_A) >> 1
def sNE(x): return (x & NOT_H) >> 7
def sNW(x): return (x & NOT_A) >> 9
def sSE(x): return ((x & NOT_H) << 9) & MASK
def sSW(x): return ((x & NOT_A) << 7) & MASK
SHIFTS = (sN, sS, sE, sW, sNE, sNW, sSE, sSW)

_W = [
    100,-20, 10,  5,  5, 10,-20,100,
    -20,-50, -2, -2, -2, -2,-50,-20,
     10, -2,  1,  1,  1,  1, -2, 10,
      5, -2,  1,  1,  1,  1, -2,  5,
      5, -2,  1,  1,  1,  1, -2,  5,
     10, -2,  1,  1,  1,  1, -2, 10,
    -20,-50, -2, -2, -2, -2,-50,-20,
    100,-20, 10,  5,  5, 10,-20,100,
]
_WM = {}
for _i in range(64):
    _WM[_W[_i]] = _WM.get(_W[_i], 0) | (1 << _i)
WEIGHT_ITEMS = tuple(_WM.items())

def popcount(x): return bin(x).count('1')

class Timeout(Exception): pass
_deadline = 0
_nodes = 0

def get_moves(P, O):
    empty = ~(P | O) & MASK
    m = 0
    for s in SHIFTS:
        x = s(P) & O
        x |= s(x) & O
        x |= s(x) & O
        x |= s(x) & O
        x |= s(x) & O
        x |= s(x) & O
        m |= s(x) & empty
    return m

def make_move(P, O, mb):
    flips = 0
    for s in SHIFTS:
        x = 0
        cur = s(mb)
        while cur and (cur & O):
            x |= cur
            cur = s(cur)
        if cur & P:
            flips |= x
    return P | mb | flips, O & ~flips & MASK

def eval_pos(P, O, mm, om):
    sc = 0
    for w, mask in WEIGHT_ITEMS:
        sc += w * (popcount(P & mask) - popcount(O & mask))
    sc += 8 * (popcount(mm) - popcount(om))
    return sc

def final_score(P, O):
    return (popcount(P) - popcount(O)) * 1000

def alphabeta(P, O, depth, alpha, beta, endgame=False):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0:
        if time.time() > _deadline:
            raise Timeout()
    mm = get_moves(P, O)
    if mm == 0:
        om = get_moves(O, P)
        if om == 0:
            return final_score(P, O), None
        s, _ = alphabeta(O, P, depth if endgame else depth - 1, -beta, -alpha, endgame)
        return -s, None
    if depth == 0:
        om = get_moves(O, P)
        return eval_pos(P, O, mm, om), None
    mbs = []
    m = mm
    while m:
        b = m & -m
        mbs.append(b); m ^= b
    mbs.sort(key=lambda b: -_W[b.bit_length() - 1])
    best_move = mbs[0]
    best = -10**18
    for b in mbs:
        nP, nO = make_move(P, O, b)
        s, _ = alphabeta(nO, nP, depth - 1, -beta, -alpha, endgame)
        s = -s
        if s > best:
            best = s; best_move = b
            if s > alpha: alpha = s
        if alpha >= beta: break
    return best, best_move

def to_bitboard(arr):
    bb = 0
    for r in range(8):
        row = arr[r]
        for c in range(8):
            if row[c]:
                bb |= 1 << (r*8 + c)
    return bb

def bit_to_move(b):
    idx = b.bit_length() - 1
    return chr(ord('a') + (idx % 8)) + str((idx // 8) + 1)

def policy(you, opponent):
    global _deadline, _nodes
    P = to_bitboard(you)
    O = to_bitboard(opponent)
    moves = get_moves(P, O)
    if moves == 0:
        return "pass"
    empties = 64 - popcount(P | O)
    _deadline = time.time() + 0.85
    _nodes = 0
    best_move = moves & -moves
    CORNERS = (1<<0)|(1<<7)|(1<<56)|(1<<63)
    cm = moves & CORNERS
    if cm:
        best_move = cm & -cm
    if empties <= 10:
        try:
            _, bm = alphabeta(P, O, empties + 2, -10**18, 10**18, endgame=True)
            if bm is not None:
                best_move = bm
        except Timeout:
            pass
        return bit_to_move(best_move)
    for d in range(2, 20):
        try:
            _, bm = alphabeta(P, O, d, -10**18, 10**18)
            if bm is not None:
                best_move = bm
        except Timeout:
            break
    return bit_to_move(best_move)
