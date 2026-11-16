
import time

MASK = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = MASK ^ FILE_A
NOT_H = MASK ^ FILE_H

W_VAL = (10, 15, 22, 32, 45, 65, 100, 200)
B_VAL = (200, 100, 65, 45, 32, 22, 15, 10)
ROW_MASKS = tuple(0xFF << (r*8) for r in range(8))

_deadline = [0]


def evaluate(w, b):
    s = 0
    for r in range(8):
        rm = ROW_MASKS[r]
        s += bin(w & rm).count('1') * W_VAL[r]
        s -= bin(b & rm).count('1') * B_VAL[r]
    return s


def gen_w(w, b):
    occ = w | b
    empty = (~occ) & MASK
    caps = []
    quiets = []
    t = (w << 8) & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to >= 56:
            return [(to - 8, to)], True
        quiets.append((to - 8, to))
        t ^= lsb
    base = ((w & NOT_A) << 7) & MASK
    t = base & b
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to >= 56:
            return [(to - 7, to)], True
        caps.append((to - 7, to))
        t ^= lsb
    t = base & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to >= 56:
            return [(to - 7, to)], True
        quiets.append((to - 7, to))
        t ^= lsb
    base = ((w & NOT_H) << 9) & MASK
    t = base & b
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to >= 56:
            return [(to - 9, to)], True
        caps.append((to - 9, to))
        t ^= lsb
    t = base & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to >= 56:
            return [(to - 9, to)], True
        quiets.append((to - 9, to))
        t ^= lsb
    return caps + quiets, False


def gen_b(b, w):
    occ = w | b
    empty = (~occ) & MASK
    caps = []
    quiets = []
    t = (b >> 8) & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to < 8:
            return [(to + 8, to)], True
        quiets.append((to + 8, to))
        t ^= lsb
    base = (b & NOT_A) >> 9
    t = base & w
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to < 8:
            return [(to + 9, to)], True
        caps.append((to + 9, to))
        t ^= lsb
    t = base & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to < 8:
            return [(to + 9, to)], True
        quiets.append((to + 9, to))
        t ^= lsb
    base = (b & NOT_H) >> 7
    t = base & w
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to < 8:
            return [(to + 7, to)], True
        caps.append((to + 7, to))
        t ^= lsb
    t = base & empty
    while t:
        lsb = t & -t
        to = lsb.bit_length() - 1
        if to < 8:
            return [(to + 7, to)], True
        quiets.append((to + 7, to))
        t ^= lsb
    return caps + quiets, False


def negamax(w, b, color, depth, alpha, beta):
    if time.time() > _deadline[0]:
        return 0
    if color == 'w':
        moves, win = gen_w(w, b)
    else:
        moves, win = gen_b(b, w)
    if win:
        return 99000 + depth
    if not moves:
        return -99000 - depth
    if depth <= 0:
        s = evaluate(w, b)
        return s if color == 'w' else -s
    best = -1000000
    oc = 'b' if color == 'w' else 'w'
    for frm, to in moves:
        fb = 1 << frm
        tb = 1 << to
        if color == 'w':
            nw = (w ^ fb) | tb
            nb = b & ~tb
        else:
            nb = (b ^ fb) | tb
            nw = w & ~tb
        v = -negamax(nw, nb, oc, depth - 1, -beta, -alpha)
        if v > best:
            best = v
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    return best


def policy(me, opp, color):
    w = 0
    b = 0
    if color == 'w':
        for r, c in me: w |= 1 << (r * 8 + c)
        for r, c in opp: b |= 1 << (r * 8 + c)
    else:
        for r, c in me: b |= 1 << (r * 8 + c)
        for r, c in opp: w |= 1 << (r * 8 + c)

    if color == 'w':
        moves, win = gen_w(w, b)
    else:
        moves, win = gen_b(b, w)

    if not moves:
        if me:
            r, c = me[0]
            if color == 'w' and r < 7:
                return ((r, c), (r + 1, c))
            if color == 'b' and r > 0:
                return ((r, c), (r - 1, c))
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    if win:
        frm, to = moves[0]
        return ((frm // 8, frm % 8), (to // 8, to % 8))

    start = time.time()
    _deadline[0] = start + 0.85
    best_move = moves[0]
    oc = 'b' if color == 'w' else 'w'

    for depth in range(1, 10):
        if time.time() > start + 0.45:
            break
        alpha = -1000000
        beta = 1000000
        best_val = -1000000
        current_best = None
        scored = []
        aborted = False
        for frm, to in moves:
            if time.time() > _deadline[0]:
                aborted = True
                break
            fb = 1 << frm
            tb = 1 << to
            if color == 'w':
                nw = (w ^ fb) | tb
                nb = b & ~tb
            else:
                nb = (b ^ fb) | tb
                nw = w & ~tb
            v = -negamax(nw, nb, oc, depth - 1, -beta, -alpha)
            scored.append((v, (frm, to)))
            if v > best_val:
                best_val = v
                current_best = (frm, to)
            if v > alpha:
                alpha = v
        if not aborted and current_best is not None:
            best_move = current_best
            scored.sort(reverse=True, key=lambda x: x[0])
            moves = [m for _, m in scored]
            if best_val >= 99000:
                break

    frm, to = best_move
    return ((frm // 8, frm % 8), (to // 8, to % 8))
