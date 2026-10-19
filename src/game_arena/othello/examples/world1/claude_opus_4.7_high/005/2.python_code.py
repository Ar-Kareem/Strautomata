
import numpy as np
import time

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
CORNERS = 0x8100000000000081

WEIGHTS = (
    120, -20, 20,  5,  5, 20, -20, 120,
    -20, -40, -5, -5, -5, -5, -40, -20,
     20,  -5, 15,  3,  3, 15,  -5,  20,
      5,  -5,  3,  3,  3,  3,  -5,   5,
      5,  -5,  3,  3,  3,  3,  -5,   5,
     20,  -5, 15,  3,  3, 15,  -5,  20,
    -20, -40, -5, -5, -5, -5, -40, -20,
    120, -20, 20,  5,  5, 20, -20, 120,
)

class TimeOut(Exception): pass
_deadline = [0.0]

def popcount(x):
    return bin(x).count('1')

def get_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    c = (P >> 8) & O
    for _ in range(5): c |= (c >> 8) & O
    moves |= (c >> 8) & empty
    c = ((P << 8) & FULL) & O
    for _ in range(5): c |= ((c << 8) & FULL) & O
    moves |= ((c << 8) & FULL) & empty
    c = (P << 1) & NOT_A & O
    for _ in range(5): c |= (c << 1) & NOT_A & O
    moves |= (c << 1) & NOT_A & empty
    c = (P >> 1) & NOT_H & O
    for _ in range(5): c |= (c >> 1) & NOT_H & O
    moves |= (c >> 1) & NOT_H & empty
    c = (P >> 7) & NOT_A & O
    for _ in range(5): c |= (c >> 7) & NOT_A & O
    moves |= (c >> 7) & NOT_A & empty
    c = (P >> 9) & NOT_H & O
    for _ in range(5): c |= (c >> 9) & NOT_H & O
    moves |= (c >> 9) & NOT_H & empty
    c = (P << 9) & NOT_A & O
    for _ in range(5): c |= (c << 9) & NOT_A & O
    moves |= (c << 9) & NOT_A & empty
    c = (P << 7) & NOT_H & O
    for _ in range(5): c |= (c << 7) & NOT_H & O
    moves |= (c << 7) & NOT_H & empty
    return moves

def make_move(P, O, mv):
    flips = 0
    sq = mv >> 8; line = 0
    while sq & O: line |= sq; sq = sq >> 8
    if sq & P: flips |= line
    sq = (mv << 8) & FULL; line = 0
    while sq & O: line |= sq; sq = (sq << 8) & FULL
    if sq & P: flips |= line
    sq = (mv << 1) & NOT_A; line = 0
    while sq & O: line |= sq; sq = (sq << 1) & NOT_A
    if sq & P: flips |= line
    sq = (mv >> 1) & NOT_H; line = 0
    while sq & O: line |= sq; sq = (sq >> 1) & NOT_H
    if sq & P: flips |= line
    sq = (mv >> 7) & NOT_A; line = 0
    while sq & O: line |= sq; sq = (sq >> 7) & NOT_A
    if sq & P: flips |= line
    sq = (mv >> 9) & NOT_H; line = 0
    while sq & O: line |= sq; sq = (sq >> 9) & NOT_H
    if sq & P: flips |= line
    sq = (mv << 9) & NOT_A; line = 0
    while sq & O: line |= sq; sq = (sq << 9) & NOT_A
    if sq & P: flips |= line
    sq = (mv << 7) & NOT_H; line = 0
    while sq & O: line |= sq; sq = (sq << 7) & NOT_H
    if sq & P: flips |= line
    return (P | mv | flips), (O & ~flips)

def weighted_score(P, O):
    s = 0
    x = P
    while x:
        b = x & -x
        s += WEIGHTS[b.bit_length() - 1]
        x ^= b
    x = O
    while x:
        b = x & -x
        s -= WEIGHTS[b.bit_length() - 1]
        x ^= b
    return s

def evaluate(P, O):
    score = weighted_score(P, O)
    pm = popcount(get_moves(P, O))
    om = popcount(get_moves(O, P))
    score += 8 * (pm - om)
    return score

def negamax(P, O, depth, alpha, beta, passed):
    if time.time() > _deadline[0]:
        raise TimeOut()
    moves = get_moves(P, O)
    if moves == 0:
        if passed:
            return (popcount(P) - popcount(O)) * 10000
        return -negamax(O, P, depth, -beta, -alpha, True)
    if depth <= 0:
        return evaluate(P, O)
    move_list = []
    x = moves
    while x:
        b = x & -x
        x ^= b
        move_list.append(b)
    move_list.sort(key=lambda b: -WEIGHTS[b.bit_length() - 1])
    best = -10**18
    for b in move_list:
        nP, nO = make_move(P, O, b)
        v = -negamax(nO, nP, depth - 1, -beta, -alpha, False)
        if v > best:
            best = v
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    return best

def policy(you, opponent):
    _deadline[0] = time.time() + 0.85
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if you[r, c]:
                P |= bit
            elif opponent[r, c]:
                O |= bit
    moves = get_moves(P, O)
    if moves == 0:
        return "pass"
    move_list = []
    x = moves
    while x:
        b = x & -x
        x ^= b
        move_list.append(b)
    move_list.sort(key=lambda b: -WEIGHTS[b.bit_length() - 1])
    best_move = move_list[0]
    empty = 64 - popcount(P | O)
    max_depth = empty if empty <= 12 else 8
    try:
        for depth in range(1, max_depth + 1):
            best_v = -10**18
            alpha = -10**18
            beta = 10**18
            new_order = []
            current_best = move_list[0]
            for b in move_list:
                nP, nO = make_move(P, O, b)
                v = -negamax(nO, nP, depth - 1, -beta, -alpha, False)
                new_order.append((v, b))
                if v > best_v:
                    best_v = v
                    current_best = b
                    if v > alpha:
                        alpha = v
            best_move = current_best
            new_order.sort(key=lambda x: -x[0])
            move_list = [b for _, b in new_order]
    except TimeOut:
        pass
    i = best_move.bit_length() - 1
    r = i // 8
    c = i % 8
    return "abcdefgh"[c] + str(r + 1)
