
import time

WIN = 100000

class TimeUp(Exception):
    pass

def gen_moves(my_bb, op_bb, is_white):
    occ = my_bb | op_bb
    moves = []
    bb = my_bb
    while bb:
        lsb = bb & -bb
        from_sq = lsb.bit_length() - 1
        bb ^= lsb
        r = from_sq >> 3
        c = from_sq & 7
        nr = r + 1 if is_white else r - 1
        if nr < 0 or nr > 7:
            continue
        base = nr * 8
        # forward (empty only)
        to_sq = base + c
        if not (occ >> to_sq) & 1:
            moves.append((from_sq, to_sq))
        # diag left
        if c > 0:
            to_sq = base + c - 1
            if not (my_bb >> to_sq) & 1:
                moves.append((from_sq, to_sq))
        # diag right
        if c < 7:
            to_sq = base + c + 1
            if not (my_bb >> to_sq) & 1:
                moves.append((from_sq, to_sq))
    return moves

def evaluate(my_bb, op_bb, is_white):
    score = 0
    bb = my_bb
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        r = sq >> 3
        adv = r if is_white else 7 - r
        score += 100 + adv * adv * 3 + adv * 2
    bb = op_bb
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        r = sq >> 3
        adv = (7 - r) if is_white else r
        score -= 100 + adv * adv * 3 + adv * 2
    return score

def negamax(my_bb, op_bb, is_white, depth, alpha, beta, end_time):
    if time.time() > end_time:
        raise TimeUp()
    if op_bb == 0:
        return WIN
    moves = gen_moves(my_bb, op_bb, is_white)
    if not moves:
        return -WIN
    goal_row = 7 if is_white else 0
    for fs, ts in moves:
        if (ts >> 3) == goal_row:
            return WIN - (20 - depth)
    if depth == 0:
        return evaluate(my_bb, op_bb, is_white)
    # Move ordering: captures and advancement
    scored = []
    for m in moves:
        fs, ts = m
        cap = 1 if (op_bb >> ts) & 1 else 0
        r = ts >> 3
        adv = r if is_white else 7 - r
        scored.append((-(cap * 100 + adv), m))
    scored.sort()
    best = -WIN - 1
    for _, (fs, ts) in scored:
        to_mask = 1 << ts
        from_mask = 1 << fs
        new_my = (my_bb ^ from_mask) | to_mask
        new_op = op_bb & ~to_mask
        score = -negamax(new_op, new_my, not is_white, depth - 1, -beta, -alpha, end_time)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def search_root(my_bb, op_bb, is_white, depth, prev_best, end_time):
    moves = gen_moves(my_bb, op_bb, is_white)
    goal_row = 7 if is_white else 0
    for m in moves:
        if (m[1] >> 3) == goal_row:
            return WIN, m
    # Order: prev best first, then captures/advance
    scored = []
    for m in moves:
        fs, ts = m
        cap = 1 if (op_bb >> ts) & 1 else 0
        r = ts >> 3
        adv = r if is_white else 7 - r
        pri = cap * 100 + adv
        if prev_best is not None and m == prev_best:
            pri += 10000
        scored.append((-pri, m))
    scored.sort()
    best = -WIN - 1
    best_move = scored[0][1]
    alpha = -WIN - 1
    beta = WIN + 1
    for _, m in scored:
        fs, ts = m
        to_mask = 1 << ts
        from_mask = 1 << fs
        new_my = (my_bb ^ from_mask) | to_mask
        new_op = op_bb & ~to_mask
        score = -negamax(new_op, new_my, not is_white, depth - 1, -beta, -alpha, end_time)
        if score > best:
            best = score
            best_move = m
        if best > alpha:
            alpha = best
    return best, best_move

def policy(me, opp, color):
    end_time = time.time() + 0.85
    my_bb = 0
    op_bb = 0
    for r, c in me:
        my_bb |= 1 << (r * 8 + c)
    for r, c in opp:
        op_bb |= 1 << (r * 8 + c)
    is_white = (color == 'w')
    moves = gen_moves(my_bb, op_bb, is_white)
    if not moves:
        # forced no-op (should not happen)
        r, c = me[0]
        return ((r, c), (r, c))
    goal_row = 7 if is_white else 0
    for m in moves:
        if (m[1] >> 3) == goal_row:
            fs, ts = m
            return ((fs >> 3, fs & 7), (ts >> 3, ts & 7))
    best_move = moves[0]
    for depth in range(2, 20):
        try:
            score, mv = search_root(my_bb, op_bb, is_white, depth, best_move, end_time)
            if mv is not None:
                best_move = mv
            if score >= WIN - 100 or score <= -WIN + 100:
                break
        except TimeUp:
            break
    fs, ts = best_move
    return ((fs >> 3, fs & 7), (ts >> 3, ts & 7))
