
import time

COLS = 6
ROWS = 5
N = ROWS * COLS
ALL = (1 << N) - 1

_row_bits = [sum(1 << (r*COLS+c) for c in range(COLS)) for r in range(ROWS)]
_col_bits = [sum(1 << (r*COLS+c) for r in range(ROWS)) for c in range(COLS)]
NOT_TOP = ALL ^ _row_bits[0]
NOT_BOT = ALL ^ _row_bits[ROWS-1]
NOT_LEFT = ALL ^ _col_bits[0]
NOT_RIGHT = ALL ^ _col_bits[COLS-1]

def gen_moves(me, opp):
    moves = []
    x = me & (opp << COLS) & NOT_TOP
    while x:
        b = x & -x; moves.append((b, b >> COLS)); x ^= b
    x = me & (opp >> COLS) & NOT_BOT
    while x:
        b = x & -x; moves.append((b, b << COLS)); x ^= b
    x = me & (opp << 1) & NOT_LEFT
    while x:
        b = x & -x; moves.append((b, b >> 1)); x ^= b
    x = me & (opp >> 1) & NOT_RIGHT
    while x:
        b = x & -x; moves.append((b, b << 1)); x ^= b
    return moves

def count_moves(me, opp):
    return (bin(me & (opp << COLS) & NOT_TOP).count('1') +
            bin(me & (opp >> COLS) & NOT_BOT).count('1') +
            bin(me & (opp << 1) & NOT_LEFT).count('1') +
            bin(me & (opp >> 1) & NOT_RIGHT).count('1'))

_deadline = [0.0]

def negamax(me, opp, depth, alpha, beta):
    if time.time() > _deadline[0]:
        return None
    moves = gen_moves(me, opp)
    if not moves:
        return -10000 - depth
    if depth <= 0:
        return len(moves) - count_moves(opp, me)
    best = -1000000
    for src, dst in moves:
        new_me = (me ^ src) | dst
        new_opp = opp ^ dst
        v = negamax(new_opp, new_me, depth-1, -beta, -alpha)
        if v is None:
            return None
        v = -v
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you, opponent):
    start = time.time()
    _deadline[0] = start + 0.85
    me = 0
    opp = 0
    for r in range(ROWS):
        for c in range(COLS):
            if you[r][c]:
                me |= 1 << (r*COLS + c)
            if opponent[r][c]:
                opp |= 1 << (r*COLS + c)

    moves = gen_moves(me, opp)

    def move_to_str(src, dst):
        sp = src.bit_length() - 1
        dp = dst.bit_length() - 1
        sr, sc = divmod(sp, COLS)
        dr, dc = divmod(dp, COLS)
        if dr < sr: d = 'U'
        elif dr > sr: d = 'D'
        elif dc < sc: d = 'L'
        else: d = 'R'
        return f"{sr},{sc},{d}"

    if not moves:
        return "0,0,U"

    best_move = moves[0]

    for depth in range(1, 30):
        if time.time() > _deadline[0]:
            break
        alpha = -1000000
        beta = 1000000
        local_best = None
        local_val = -1000000
        timed_out = False
        for src, dst in moves:
            new_me = (me ^ src) | dst
            new_opp = opp ^ dst
            v = negamax(new_opp, new_me, depth-1, -beta, -alpha)
            if v is None:
                timed_out = True
                break
            v = -v
            if v > local_val:
                local_val = v
                local_best = (src, dst)
            if v > alpha:
                alpha = v
        if not timed_out and local_best is not None:
            best_move = local_best
            try:
                moves.remove(local_best)
                moves.insert(0, local_best)
            except ValueError:
                pass
            if local_val > 5000:
                break
        else:
            break

    return move_to_str(*best_move)
