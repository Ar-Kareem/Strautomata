
import numpy as np
import time

MASK = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE  # c != 0
NOT_H = 0x7F7F7F7F7F7F7F7F  # c != 7

def sn(x): return x >> 8
def ss(x): return (x << 8) & MASK
def se(x): return (x & NOT_H) << 1
def sw(x): return (x & NOT_A) >> 1
def sne(x): return (x & NOT_H) >> 7
def snw(x): return (x & NOT_A) >> 9
def sse(x): return ((x & NOT_H) << 9) & MASK
def ssw(x): return ((x & NOT_A) << 7) & MASK

SHIFTS = (sn, ss, se, sw, sne, snw, sse, ssw)

def popcount(x):
    return bin(x).count('1')

def gen_moves(me, opp):
    empty = (~(me | opp)) & MASK
    moves = 0
    for shift in SHIFTS:
        x = shift(me) & opp
        x |= shift(x) & opp
        x |= shift(x) & opp
        x |= shift(x) & opp
        x |= shift(x) & opp
        x |= shift(x) & opp
        moves |= shift(x) & empty
    return moves

def apply_move(me, opp, mv):
    flipped = 0
    for shift in SHIFTS:
        x = shift(mv) & opp
        captured = 0
        while x:
            captured |= x
            nx = shift(x)
            if nx & me:
                flipped |= captured
                break
            if not (nx & opp):
                break
            x = nx
    return (me | mv | flipped), (opp & ~flipped)

WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

def evaluate(me, opp):
    score = 0
    m = me
    while m:
        lsb = m & -m
        score += WEIGHTS[lsb.bit_length() - 1]
        m ^= lsb
    m = opp
    while m:
        lsb = m & -m
        score -= WEIGHTS[lsb.bit_length() - 1]
        m ^= lsb
    my_mv = popcount(gen_moves(me, opp))
    op_mv = popcount(gen_moves(opp, me))
    score += 8 * (my_mv - op_mv)
    # corner bonus
    score += 25 * (popcount(me & CORNERS) - popcount(opp & CORNERS))
    return score

class TimeOut(Exception): pass

def negamax(me, opp, depth, alpha, beta, deadline, passed=False):
    if time.time() > deadline:
        raise TimeOut()
    moves = gen_moves(me, opp)
    if moves == 0:
        if passed:
            my_c = popcount(me); op_c = popcount(opp)
            if my_c > op_c: return 100000 + (my_c - op_c)
            if my_c < op_c: return -100000 + (my_c - op_c)
            return 0
        return -negamax(opp, me, depth-1, -beta, -alpha, deadline, True)
    if depth == 0:
        return evaluate(me, opp)
    best = -10**9
    # order moves: prefer corners
    move_list = []
    m = moves
    while m:
        lsb = m & -m
        m ^= lsb
        idx = lsb.bit_length() - 1
        priority = WEIGHTS[idx]
        move_list.append((priority, lsb))
    move_list.sort(reverse=True)
    for _, lsb in move_list:
        me2, opp2 = apply_move(me, opp, lsb)
        val = -negamax(opp2, me2, depth-1, -beta, -alpha, deadline, False)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def endgame(me, opp, alpha, beta, passed=False):
    moves = gen_moves(me, opp)
    if moves == 0:
        if passed:
            return popcount(me) - popcount(opp)
        return -endgame(opp, me, -beta, -alpha, True)
    best = -100
    move_list = []
    m = moves
    while m:
        lsb = m & -m
        m ^= lsb
        idx = lsb.bit_length() - 1
        move_list.append((WEIGHTS[idx], lsb))
    move_list.sort(reverse=True)
    for _, lsb in move_list:
        me2, opp2 = apply_move(me, opp, lsb)
        val = -endgame(opp2, me2, -beta, -alpha, False)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you, opponent):
    me = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r*8 + c)
            if you[r][c]: me |= bit
            if opponent[r][c]: opp |= bit

    moves = gen_moves(me, opp)
    if moves == 0:
        return "pass"

    # Fallback: first legal move
    first = moves & -moves
    best_move = first

    empty = 64 - popcount(me | opp)
    start = time.time()
    deadline = start + 0.80

    # Gather move list with priorities
    move_list = []
    m = moves
    while m:
        lsb = m & -m
        m ^= lsb
        idx = lsb.bit_length() - 1
        move_list.append((WEIGHTS[idx], lsb))
    move_list.sort(reverse=True)

    try:
        if empty <= 10:
            # exact endgame solve
            best = -1000
            for _, lsb in move_list:
                if time.time() > deadline + 5:  # allow more time for endgame
                    break
                me2, opp2 = apply_move(me, opp, lsb)
                val = -endgame(opp2, me2, -1000, -best)
                if val > best:
                    best = val
                    best_move = lsb
        else:
            # iterative deepening
            max_depth = 8
            for depth in range(1, max_depth + 1):
                current_score = -10**9
                current_best = None
                alpha = -10**9
                beta = 10**9
                new_order = []
                for _, lsb in move_list:
                    me2, opp2 = apply_move(me, opp, lsb)
                    val = -negamax(opp2, me2, depth-1, -beta, -alpha, deadline, False)
                    new_order.append((val, lsb))
                    if val > current_score:
                        current_score = val
                        current_best = lsb
                    if current_score > alpha:
                        alpha = current_score
                if current_best is not None:
                    best_move = current_best
                # reorder for next iteration
                new_order.sort(reverse=True)
                move_list = new_order
                if time.time() > deadline * 0.7 + start * 0.3:
                    # not enough time for next iteration
                    if time.time() > deadline - (time.time() - start):
                        break
    except TimeOut:
        pass

    idx = best_move.bit_length() - 1
    r, c = idx // 8, idx % 8
    return chr(ord('a') + c) + str(r + 1)
