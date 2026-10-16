
import time
import numpy as np

ROWS, COLS = 5, 6
N = ROWS * COLS

# Precompute neighbors: for each cell index, list of (neighbor_index, dir_char)
NEIGHBORS = []
for r in range(ROWS):
    for c in range(COLS):
        nb = []
        for dr, dc, d in [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                nb.append((nr * COLS + nc, d))
        NEIGHBORS.append(tuple(nb))

def gen_moves(me, opp):
    moves = []
    m = me
    while m:
        b = m & -m
        i = b.bit_length() - 1
        m ^= b
        for j, d in NEIGHBORS[i]:
            if opp & (1 << j):
                moves.append((i, j, d))
    return moves

def count_moves(me, opp):
    cnt = 0
    m = me
    while m:
        b = m & -m
        i = b.bit_length() - 1
        m ^= b
        for j, d in NEIGHBORS[i]:
            if opp & (1 << j):
                cnt += 1
    return cnt

class TimeUp(Exception):
    pass

def negamax(me, opp, depth, alpha, beta, deadline, ply):
    if time.time() > deadline:
        raise TimeUp
    moves = gen_moves(me, opp)
    if not moves:
        # current player has no moves -> loses
        return -10000 + ply
    if depth == 0:
        opp_cnt = count_moves(opp, me)
        return len(moves) - opp_cnt
    best = -99999
    for i, j, d in moves:
        bi = 1 << i
        bj = 1 << j
        new_me = (me ^ bi) | bj
        new_opp = opp ^ bj
        val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline, ply + 1)
        if val > best:
            best = val
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    return best

def policy(you, opponent):
    start = time.time()
    deadline = start + 0.85

    ya = np.asarray(you).reshape(ROWS, COLS)
    oa = np.asarray(opponent).reshape(ROWS, COLS)

    me = 0
    opp = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if ya[r, c]:
                me |= 1 << idx
            if oa[r, c]:
                opp |= 1 << idx

    moves = gen_moves(me, opp)
    if not moves:
        # No legal moves - we've lost, return any string (will be illegal)
        return "0,0,U"

    best_move = moves[0]

    # Order moves by shallow evaluation first
    scored = []
    for mv in moves:
        i, j, d = mv
        bi = 1 << i
        bj = 1 << j
        new_me = (me ^ bi) | bj
        new_opp = opp ^ bj
        # opponent's response count (less = better for us)
        opp_cnt = count_moves(new_opp, new_me)
        my_cnt = count_moves(new_me, new_opp)
        scored.append((my_cnt - opp_cnt, mv))
    scored.sort(key=lambda x: -x[0])
    ordered_moves = [mv for _, mv in scored]

    try:
        for depth in range(1, 30):
            local_best = None
            local_score = -99999
            alpha = -99999
            beta = 99999
            new_order = []
            move_scores = []
            for mv in ordered_moves:
                i, j, d = mv
                bi = 1 << i
                bj = 1 << j
                new_me = (me ^ bi) | bj
                new_opp = opp ^ bj
                val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline, 1)
                move_scores.append((val, mv))
                if val > local_score:
                    local_score = val
                    local_best = mv
                if val > alpha:
                    alpha = val
            if local_best is not None:
                best_move = local_best
                move_scores.sort(key=lambda x: -x[0])
                ordered_moves = [mv for _, mv in move_scores]
            # Early exit if forced win/loss discovered
            if local_score >= 9000 or local_score <= -9000:
                break
            # Time check - don't start deeper if little time remains
            if time.time() > start + 0.6:
                break
    except TimeUp:
        pass

    i, j, d = best_move
    r, c = i // COLS, i % COLS
    return f"{r},{c},{d}"
