
import time
import numpy as np

NEIGHBORS = [0]*30
for r in range(5):
    for c in range(6):
        i = r*6+c
        m = 0
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc = r+dr,c+dc
            if 0<=nr<5 and 0<=nc<6:
                m |= 1<<(nr*6+nc)
        NEIGHBORS[i] = m

def gen_moves(me, opp):
    moves = []
    m = me
    while m:
        b = m & -m
        i = b.bit_length() - 1
        n = NEIGHBORS[i] & opp
        while n:
            b2 = n & -n
            j = b2.bit_length() - 1
            moves.append((i, j))
            n ^= b2
        m ^= b
    return moves

def count_moves(me, opp):
    c = 0
    m = me
    while m:
        b = m & -m
        i = b.bit_length() - 1
        c += bin(NEIGHBORS[i] & opp).count('1')
        m ^= b
    return c

INF = 10**9
class TO(Exception): pass
_state = {'deadline': 0, 'nodes': 0}

def negamax(me, opp, depth, alpha, beta):
    _state['nodes'] += 1
    if (_state['nodes'] & 2047) == 0:
        if time.time() > _state['deadline']:
            raise TO
    moves = gen_moves(me, opp)
    if not moves:
        return -INF + 1
    if depth == 0:
        return len(moves) - count_moves(opp, me)
    best = -INF
    for (i, j) in moves:
        new_me = me ^ (1<<i) ^ (1<<j)
        new_opp = opp ^ (1<<j)
        val = -negamax(new_opp, new_me, depth-1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you, opponent):
    y = np.asarray(you).reshape(5,6)
    o = np.asarray(opponent).reshape(5,6)
    me = 0
    opp = 0
    for r in range(5):
        for c in range(6):
            idx = r*6+c
            if y[r][c]:
                me |= 1 << idx
            if o[r][c]:
                opp |= 1 << idx

    moves = gen_moves(me, opp)
    if not moves:
        return "0,0,U"

    start = time.time()
    _state['deadline'] = start + 0.85
    _state['nodes'] = 0
    best_move = moves[0]

    try:
        for depth in range(1, 30):
            alpha = -INF
            beta = INF
            local_best = None
            local_score = -INF
            for (i, j) in moves:
                new_me = me ^ (1<<i) ^ (1<<j)
                new_opp = opp ^ (1<<j)
                val = -negamax(new_opp, new_me, depth-1, -beta, -alpha)
                if val > local_score:
                    local_score = val
                    local_best = (i, j)
                if val > alpha:
                    alpha = val
            if local_best is not None:
                best_move = local_best
                if best_move in moves:
                    moves.remove(best_move)
                    moves.insert(0, best_move)
            if local_score >= INF - 100:
                break
            if local_score <= -INF + 100:
                break
    except TO:
        pass

    i, j = best_move
    r1, c1 = divmod(i, 6)
    r2, c2 = divmod(j, 6)
    if r2 == r1 - 1: d = 'U'
    elif r2 == r1 + 1: d = 'D'
    elif c2 == c1 - 1: d = 'L'
    else: d = 'R'
    return f"{r1},{c1},{d}"
