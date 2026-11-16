
import time

ROWS, COLS = 5, 6
N = ROWS * COLS

NEIGHBORS = [[] for _ in range(N)]
DIRS = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        for dname, dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                nidx = nr * COLS + nc
                NEIGHBORS[idx].append((dname, nidx, 1 << nidx))

def gen_moves(me, opp):
    moves = []
    m = me
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        m ^= lsb
        for dname, nidx, nbit in NEIGHBORS[idx]:
            if opp & nbit:
                moves.append((idx, nidx, dname, lsb, nbit))
    return moves

def count_moves(me, opp):
    cnt = 0
    m = me
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        m ^= lsb
        for _, _, nbit in NEIGHBORS[idx]:
            if opp & nbit:
                cnt += 1
    return cnt

def negamax(me, opp, depth, alpha, beta, deadline):
    if time.time() > deadline:
        return None
    moves = gen_moves(me, opp)
    if not moves:
        return -10000 - depth
    if depth == 0:
        opp_cnt = count_moves(opp, me)
        return len(moves) - opp_cnt
    best = -100000
    for idx, nidx, dname, mbit, nbit in moves:
        new_me = (me ^ mbit) | nbit
        new_opp = opp ^ nbit
        val = negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline)
        if val is None:
            return None
        val = -val
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
    for r in range(ROWS):
        for c in range(COLS):
            if you[r][c]:
                me |= 1 << (r * COLS + c)
            if opponent[r][c]:
                opp |= 1 << (r * COLS + c)

    moves = gen_moves(me, opp)
    if not moves:
        return "0,0,U"

    deadline = time.time() + 0.85

    idx0, nidx0, dname0, _, _ = moves[0]
    r0, c0 = idx0 // COLS, idx0 % COLS
    best_move_str = f"{r0},{c0},{dname0}"

    # Order moves at root by immediate opponent mobility (ascending)
    scored = []
    for mv in moves:
        idx, nidx, dname, mbit, nbit = mv
        new_me = (me ^ mbit) | nbit
        new_opp = opp ^ nbit
        scored.append((count_moves(new_opp, new_me), mv))
    scored.sort(key=lambda x: x[0])
    ordered_moves = [mv for _, mv in scored]

    for depth in range(1, 30):
        if time.time() > deadline:
            break
        best_val = -100000
        alpha = -100000
        beta = 100000
        current_best = best_move_str
        aborted = False
        best_mv_this_iter = None
        for idx, nidx, dname, mbit, nbit in ordered_moves:
            new_me = (me ^ mbit) | nbit
            new_opp = opp ^ nbit
            val = negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline)
            if val is None:
                aborted = True
                break
            val = -val
            if val > best_val:
                best_val = val
                r = idx // COLS
                c = idx % COLS
                current_best = f"{r},{c},{dname}"
                best_mv_this_iter = (idx, nidx, dname, mbit, nbit)
                if val > alpha:
                    alpha = val
        if not aborted:
            best_move_str = current_best
            # Move the best move to front for next iteration
            if best_mv_this_iter is not None and best_mv_this_iter in ordered_moves:
                ordered_moves.remove(best_mv_this_iter)
                ordered_moves.insert(0, best_mv_this_iter)
            if best_val >= 9000:
                break
        else:
            break

    return best_move_str
