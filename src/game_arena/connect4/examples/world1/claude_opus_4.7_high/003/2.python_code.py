
import time

H = 6
W = 7
H1 = 7
BOTTOM = 0
for _c in range(W):
    BOTTOM |= 1 << (_c * H1)
BOARD_MASK = BOTTOM * ((1 << H) - 1)
COL_MASK = [((1 << H) - 1) << (c * H1) for c in range(W)]
TOP_BIT = [1 << (c * H1 + H - 1) for c in range(W)]
ORDER = [3, 2, 4, 1, 5, 0, 6]

def alignment(pos):
    m = pos & (pos >> 1)
    if m & (m >> 2): return True
    m = pos & (pos >> 7)
    if m & (m >> 14): return True
    m = pos & (pos >> 6)
    if m & (m >> 12): return True
    m = pos & (pos >> 8)
    if m & (m >> 16): return True
    return False

class TO(Exception): pass

def policy(board):
    start = time.time()
    LIMIT = 0.85

    my_pos = 0
    mask = 0
    for r in range(6):
        for c in range(7):
            v = board[r][c]
            if v != 0:
                bit = 1 << (c * 7 + (5 - r))
                mask |= bit
                if v == 1:
                    my_pos |= bit

    opp_pos = my_pos ^ mask
    valid = [c for c in ORDER if not (mask & TOP_BIT[c])]
    if not valid:
        return 0

    for c in valid:
        bit = (mask + (1 << (c * H1))) & COL_MASK[c]
        if alignment(my_pos | bit):
            return c

    for c in valid:
        bit = (mask + (1 << (c * H1))) & COL_MASK[c]
        if alignment(opp_pos | bit):
            return c

    tt = {}

    def ab(pos, mask_, alpha, beta, depth):
        if time.time() - start > LIMIT:
            raise TO

        key = (pos, mask_, depth)
        if key in tt:
            return tt[key]

        moves_bb = (mask_ + BOTTOM) & BOARD_MASK
        if moves_bb == 0:
            return 0

        for c in ORDER:
            bit = moves_bb & COL_MASK[c]
            if bit and alignment(pos | bit):
                v = 1000 + depth
                tt[key] = v
                return v

        if depth <= 0:
            return 0

        opp = pos ^ mask_
        best = -10000
        for c in ORDER:
            bit = moves_bb & COL_MASK[c]
            if not bit:
                continue
            new_mask = mask_ | bit
            score = -ab(opp, new_mask, -beta, -alpha, depth - 1)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    best_move = valid[0]
    try:
        for depth in range(2, 43):
            alpha = -10000
            beta = 10000
            cur_best = best_move
            cur_score = -10000
            # Try best_move first for better pruning
            ordered = [best_move] + [c for c in valid if c != best_move]
            for c in ordered:
                bit = (mask + (1 << (c * H1))) & COL_MASK[c]
                new_mask = mask | bit
                if alignment(my_pos | bit):
                    return c
                score = -ab(opp_pos, new_mask, -beta, -alpha, depth - 1)
                if score > cur_score:
                    cur_score = score
                    cur_best = c
                if score > alpha:
                    alpha = score
            best_move = cur_best
            if cur_score >= 900:
                break
            if cur_score <= -900:
                break
    except TO:
        pass

    return best_move
