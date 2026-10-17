
import time

ROW_MASK = [0]*64
COL_MASK = [0]*64
D1_MASK = [0]*64
D2_MASK = [0]*64
NEIGHBORS = [0]*64
for _r in range(8):
    for _c in range(8):
        _s = _r*8+_c
        for cc in range(8):
            ROW_MASK[_s] |= 1<<(_r*8+cc)
        for rr in range(8):
            COL_MASK[_s] |= 1<<(rr*8+_c)
        for k in range(-7,8):
            rr,cc=_r+k,_c+k
            if 0<=rr<8 and 0<=cc<8: D1_MASK[_s] |= 1<<(rr*8+cc)
        for k in range(-7,8):
            rr,cc=_r+k,_c-k
            if 0<=rr<8 and 0<=cc<8: D2_MASK[_s] |= 1<<(rr*8+cc)
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==0 and dc==0: continue
                rr,cc=_r+dr,_c+dc
                if 0<=rr<8 and 0<=cc<8: NEIGHBORS[_s] |= 1<<(rr*8+cc)

DIR_DATA = [(0,1,ROW_MASK),(1,0,COL_MASK),(1,1,D1_MASK),(1,-1,D2_MASK)]

def popcount(x): return bin(x).count('1')

def gen_moves(me, opp):
    moves = []
    all_p = me | opp
    m = me
    while m:
        lsb = m & -m
        s = lsb.bit_length()-1
        r, c = s>>3, s&7
        for dr, dc, masks in DIR_DATA:
            cnt = popcount(masks[s] & all_p)
            for sign in (1,-1):
                nr = r + sign*dr*cnt
                nc = c + sign*dc*cnt
                if 0<=nr<8 and 0<=nc<8:
                    tbit = 1 << (nr*8+nc)
                    if tbit & me: continue
                    blocked = False
                    for i in range(1, cnt):
                        ir = r + sign*dr*i
                        ic = c + sign*dc*i
                        if (1 << (ir*8+ic)) & opp:
                            blocked = True; break
                    if not blocked:
                        moves.append((s, nr*8+nc))
        m &= m-1
    return moves

def is_connected(bb):
    if bb == 0: return True
    lsb = bb & -bb
    visited = lsb; frontier = lsb
    while frontier:
        new_f = 0; f = frontier
        while f:
            b = f & -f
            new_f |= NEIGHBORS[b.bit_length()-1]
            f &= f-1
        new_f &= bb & ~visited
        visited |= new_f; frontier = new_f
    return visited == bb

def count_components(bb):
    if bb == 0: return 0
    count = 0; remaining = bb
    while remaining:
        lsb = remaining & -remaining
        visited = lsb; frontier = lsb
        while frontier:
            new_f = 0; f = frontier
            while f:
                b = f & -f
                new_f |= NEIGHBORS[b.bit_length()-1]
                f &= f-1
            new_f &= bb & ~visited
            visited |= new_f; frontier = new_f
        remaining &= ~visited; count += 1
    return count

def concentration(bb):
    if bb == 0: return 0
    n=0; sr=0; sc=0; sqs=[]
    t = bb
    while t:
        b = t & -t
        s = b.bit_length()-1
        sqs.append(s); sr += s>>3; sc += s&7; n+=1
        t &= t-1
    cr = sr/n; cc = sc/n
    tot = 0.0
    for s in sqs:
        r,c = s>>3, s&7
        tot += (r-cr)*(r-cr) + (c-cc)*(c-cc)
    return tot

def evaluate(me, opp):
    my_c = count_components(me)
    op_c = count_components(opp)
    my_n = popcount(me); op_n = popcount(opp)
    my_k = concentration(me); op_k = concentration(opp)
    return (op_c - my_c)*80 + (op_k - my_k)*1.5 + (my_n - op_n)*15

def negamax(me, opp, depth, alpha, beta):
    op_win = opp != 0 and is_connected(opp)
    me_win = me != 0 and is_connected(me)
    if op_win:
        if me_win: return 0
        return -100000 - depth
    if me_win:
        return 100000 + depth
    if depth == 0:
        return evaluate(me, opp)
    moves = gen_moves(me, opp)
    if not moves:
        return -100000
    moves.sort(key=lambda m: 0 if (1<<m[1]) & opp else 1)
    best = -10**9
    for frm, to in moves:
        new_me = (me & ~(1<<frm)) | (1<<to)
        new_opp = opp & ~(1<<to)
        val = -negamax(new_opp, new_me, depth-1, -beta, -alpha)
        if val > best: best = val
        if val > alpha: alpha = val
        if alpha >= beta: break
    return best

def policy(board):
    me = 0; opp = 0
    for r in range(8):
        row = board[r]
        for c in range(8):
            v = row[c]
            if v == 1: me |= 1 << (r*8+c)
            elif v == -1: opp |= 1 << (r*8+c)
    moves = gen_moves(me, opp)
    if not moves:
        return "0,0:0,0"
    # Immediate win?
    for frm, to in moves:
        new_me = (me & ~(1<<frm)) | (1<<to)
        new_opp = opp & ~(1<<to)
        if is_connected(new_me) and not (is_connected(new_opp) and new_opp != 0):
            return f"{frm>>3},{frm&7}:{to>>3},{to&7}"
    # Order: captures first
    moves.sort(key=lambda m: 0 if (1<<m[1]) & opp else 1)
    start = time.time()
    best_move = moves[0]
    # Depth 2 baseline
    best_val = -10**9
    alpha = -10**9; beta = 10**9
    for frm, to in moves:
        new_me = (me & ~(1<<frm)) | (1<<to)
        new_opp = opp & ~(1<<to)
        val = -negamax(new_opp, new_me, 1, -beta, -alpha)
        if val > best_val:
            best_val = val; best_move = (frm, to)
        if val > alpha: alpha = val
    # Try depth 3 if we have time
    if time.time() - start < 0.3:
        bm3 = best_move
        bv3 = -10**9
        a = -10**9; b = 10**9
        try:
            # Put current best first
            moves2 = [best_move] + [m for m in moves if m != best_move]
            for frm, to in moves2:
                if time.time() - start > 0.75:
                    raise TimeoutError
                new_me = (me & ~(1<<frm)) | (1<<to)
                new_opp = opp & ~(1<<to)
                val = -negamax(new_opp, new_me, 2, -b, -a)
                if val > bv3:
                    bv3 = val; bm3 = (frm, to)
                if val > a: a = val
            best_move = bm3
        except TimeoutError:
            pass
    frm, to = best_move
    return f"{frm>>3},{frm&7}:{to>>3},{to&7}"
