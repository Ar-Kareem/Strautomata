
import time

WIN_MASKS = []
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (r*4 + c)
    WIN_MASKS.append(m)
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (r*4 + c)
    WIN_MASKS.append(m)
m = 0
for i in range(4):
    m |= 1 << (i*4 + i)
WIN_MASKS.append(m)
m = 0
for i in range(4):
    m |= 1 << (i*4 + (3-i))
WIN_MASKS.append(m)

CENTER = (1<<5) | (1<<6) | (1<<9) | (1<<10)
VALS = [0, 1, 10, 80, 10000]

def check_win(bb):
    for m in WIN_MASKS:
        if (bb & m) == m:
            return True
    return False

def evaluate(my_bb, op_bb):
    score = 0
    for m in WIN_MASKS:
        mm = my_bb & m
        om = op_bb & m
        if mm and om:
            continue
        if mm:
            score += VALS[bin(mm).count('1')]
        elif om:
            score -= VALS[bin(om).count('1')]
    return score

def negamax(my_bb, op_bb, depth, alpha, beta, deadline):
    if check_win(op_bb):
        return -100000 - depth
    empty = 0xFFFF & ~(my_bb | op_bb)
    if empty == 0:
        return 0
    if depth == 0:
        return evaluate(my_bb, op_bb)
    if time.time() > deadline:
        return evaluate(my_bb, op_bb)
    moves = []
    mask = empty
    while mask:
        b = mask & -mask
        priority = 1 if (b & CENTER) else 0
        moves.append((priority, b))
        mask ^= b
    moves.sort(reverse=True)
    best = -1000000
    for _, b in moves:
        v = -negamax(op_bb, my_bb | b, depth-1, -beta, -alpha, deadline)
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(board):
    my_bb = 0
    op_bb = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1:
                my_bb |= 1 << (r*4 + c)
            elif board[r][c] == -1:
                op_bb |= 1 << (r*4 + c)
    empty = 0xFFFF & ~(my_bb | op_bb)
    empty_count = bin(empty).count('1')
    if empty_count == 16:
        return (1, 1)
    if empty_count == 0:
        return (0, 0)
    start = time.time()
    deadline = start + 0.75
    best_move = empty & -empty
    max_depth = min(empty_count, 12)
    for depth in range(2, max_depth + 1):
        if time.time() > deadline - 0.05:
            break
        alpha = -1000000
        beta = 1000000
        current_best = -1000000
        current_move = None
        moves = []
        mask = empty
        while mask:
            b = mask & -mask
            priority = 1 if (b & CENTER) else 0
            moves.append((priority, b))
            mask ^= b
        moves.sort(reverse=True)
        completed = True
        for _, b in moves:
            if time.time() > deadline:
                completed = False
                break
            v = -negamax(op_bb, my_bb | b, depth-1, -beta, -alpha, deadline)
            if v > current_best:
                current_best = v
                current_move = b
            if current_best > alpha:
                alpha = current_best
        if current_move is not None and completed:
            best_move = current_move
            if current_best >= 100000:
                break
        elif current_move is not None and current_best > -50000:
            best_move = current_move
    idx = best_move.bit_length() - 1
    return (idx // 4, idx % 4)
