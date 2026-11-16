
import time
import numpy as np

ROWS = 5
COLS = 6

_DIRS = [(-1,0,'U'),(0,1,'R'),(1,0,'D'),(0,-1,'L')]
_NEIGHBORS = []
for r in range(ROWS):
    for c in range(COLS):
        nb = []
        for dr,dc,d in _DIRS:
            nr,nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS:
                nb.append((nr*COLS+nc, d))
        _NEIGHBORS.append(nb)

def _gen_moves(me, opp):
    moves = []
    m = me
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        for nidx, d in _NEIGHBORS[idx]:
            if (opp >> nidx) & 1:
                moves.append((idx, nidx, d))
        m ^= lsb
    return moves

class _TO(Exception):
    pass

def policy(you, opponent):
    you_a = np.asarray(you)
    opp_a = np.asarray(opponent)
    me = 0
    opp = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r*COLS + c
            if you_a[r][c]:
                me |= 1 << idx
            if opp_a[r][c]:
                opp |= 1 << idx

    legal = _gen_moves(me, opp)
    if not legal:
        return "0,0,U"

    deadline = time.time() + 0.85
    best_move = legal[0]
    tt = {}

    def negamax(me, opp, depth, alpha, beta):
        alpha0 = alpha
        key = (me, opp)
        if key in tt:
            td, tv, tf = tt[key]
            if td >= depth:
                if tf == 0:
                    return tv
                elif tf == 1:
                    if tv > alpha: alpha = tv
                else:
                    if tv < beta: beta = tv
                if alpha >= beta:
                    return tv
        if time.time() > deadline:
            raise _TO
        moves = _gen_moves(me, opp)
        if not moves:
            return -10000
        if depth == 0:
            opp_m = _gen_moves(opp, me)
            return len(moves) - len(opp_m)

        best = -99999
        for src, dst, _d in moves:
            nm = (me ^ (1<<src)) | (1<<dst)
            no = opp ^ (1<<dst)
            v = -negamax(no, nm, depth-1, -beta, -alpha)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best <= alpha0:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        tt[key] = (depth, best, flag)
        return best

    move_scores = {mv: 0 for mv in legal}

    try:
        for depth in range(1, 40):
            current_best = None
            best_val = -99999
            alpha = -99999
            beta = 99999
            ordered = sorted(legal, key=lambda m: -move_scores.get(m, 0))
            new_scores = {}
            for mv in ordered:
                src, dst, _d = mv
                nm = (me ^ (1<<src)) | (1<<dst)
                no = opp ^ (1<<dst)
                v = -negamax(no, nm, depth-1, -beta, -alpha)
                new_scores[mv] = v
                if v > best_val:
                    best_val = v
                    current_best = mv
                if best_val > alpha:
                    alpha = best_val
            if current_best is not None:
                best_move = current_best
                move_scores = new_scores
            if best_val >= 9000 or best_val <= -9000:
                break
    except _TO:
        pass

    src, dst, d = best_move
    r, c = src // COLS, src % COLS
    return f"{r},{c},{d}"
