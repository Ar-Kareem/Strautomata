
import time

COLS = 7
ROWS = 6
H1 = 7
MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]

def check_win(bb):
    m = bb & (bb >> 7)
    if m & (m >> 14): return True
    m = bb & (bb >> 6)
    if m & (m >> 12): return True
    m = bb & (bb >> 8)
    if m & (m >> 16): return True
    m = bb & (bb >> 1)
    if m & (m >> 2): return True
    return False

def popcount(x):
    return bin(x).count('1')

class Timeout(Exception):
    pass

def evaluate(me, opp):
    center_mask = ((1 << 6) - 1) << (3 * 7)
    return 4 * popcount(me & center_mask) - 4 * popcount(opp & center_mask)

def negamax(me, opp, heights, depth, alpha, beta, deadline, tt):
    if time.time() > deadline:
        raise Timeout()
    total_moves = popcount(me | opp)
    for col in MOVE_ORDER:
        if heights[col] >= ROWS: continue
        bit = 1 << (col * H1 + heights[col])
        if check_win(me | bit):
            return 10000 - total_moves
    if total_moves == 42: return 0
    if depth <= 0: return evaluate(me, opp)
    key = (me, opp)
    if key in tt:
        ttd, ttv, ttflag = tt[key]
        if ttd >= depth:
            if ttflag == 0: return ttv
            if ttflag == 1:
                if ttv > alpha: alpha = ttv
            elif ttflag == 2:
                if ttv < beta: beta = ttv
            if alpha >= beta: return ttv
    original_alpha = alpha
    best = -100000
    for col in MOVE_ORDER:
        if heights[col] >= ROWS: continue
        bit = 1 << (col * H1 + heights[col])
        new_me = me | bit
        heights[col] += 1
        score = -negamax(opp, new_me, heights, depth-1, -beta, -alpha, deadline, tt)
        heights[col] -= 1
        if score > best: best = score
        if best > alpha: alpha = best
        if alpha >= beta: break
    if best <= original_alpha: flag = 2
    elif best >= beta: flag = 1
    else: flag = 0
    tt[key] = (depth, best, flag)
    return best

def policy(board):
    me = 0
    opp = 0
    heights = [0]*COLS
    for c in range(COLS):
        h = 0
        for r in range(ROWS-1, -1, -1):
            val = board[r][c]
            if val == 0: break
            bit = 1 << (c * H1 + h)
            if val == 1: me |= bit
            elif val == -1: opp |= bit
            h += 1
        heights[c] = h
    default_move = 3
    for col in MOVE_ORDER:
        if heights[col] < ROWS:
            default_move = col
            break
    for col in MOVE_ORDER:
        if heights[col] < ROWS:
            bit = 1 << (col * H1 + heights[col])
            if check_win(me | bit): return col
    block_moves = []
    for col in MOVE_ORDER:
        if heights[col] < ROWS:
            bit = 1 << (col * H1 + heights[col])
            if check_win(opp | bit):
                block_moves.append(col)
    if block_moves:
        return block_moves[0]
    deadline = time.time() + 0.85
    tt = {}
    best_move = default_move
    for depth in range(2, 43):
        try:
            best_score = -100000
            alpha = -100000
            beta = 100000
            current_best_move = -1
            for col in MOVE_ORDER:
                if heights[col] >= ROWS: continue
                bit = 1 << (col * H1 + heights[col])
                new_me = me | bit
                heights[col] += 1
                score = -negamax(opp, new_me, heights, depth-1, -beta, -alpha, deadline, tt)
                heights[col] -= 1
                if score > best_score:
                    best_score = score
                    current_best_move = col
                    if score > alpha: alpha = score
            if current_best_move != -1:
                best_move = current_best_move
            if best_score > 9000: break
        except Timeout:
            break
    return best_move
