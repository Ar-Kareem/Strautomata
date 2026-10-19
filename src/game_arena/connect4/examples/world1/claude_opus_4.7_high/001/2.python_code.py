
import time

if hasattr(int, 'bit_count'):
    _popcount = int.bit_count
else:
    def _popcount(x): return bin(x).count('1')

# Precompute 4-in-a-row line masks
_LINES = []
for _r in range(6):
    for _c in range(4):
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c+_i)*7 + _r)
        _LINES.append(_m)
for _c in range(7):
    for _r in range(3):
        _m = 0
        for _i in range(4):
            _m |= 1 << (_c*7 + _r + _i)
        _LINES.append(_m)
for _r in range(3):
    for _c in range(4):
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c+_i)*7 + _r+_i)
        _LINES.append(_m)
for _r in range(3, 6):
    for _c in range(4):
        _m = 0
        for _i in range(4):
            _m |= 1 << ((_c+_i)*7 + _r-_i)
        _LINES.append(_m)

_COL_ORDER = (3, 2, 4, 1, 5, 0, 6)

def policy(board):
    start = time.time()
    TIME_LIMIT = 0.85
    deadline = start + TIME_LIMIT

    my_bb = 0
    opp_bb = 0
    heights = [0]*7
    for c in range(7):
        for r in range(6):
            val = board[5-r][c]
            if val != 0:
                bit = 1 << (c*7 + r)
                if val == 1:
                    my_bb |= bit
                else:
                    opp_bb |= bit
                heights[c] = r+1

    def has_won(bb):
        m = bb & (bb >> 7)
        if m & (m >> 14): return True
        m = bb & (bb >> 1)
        if m & (m >> 2): return True
        m = bb & (bb >> 8)
        if m & (m >> 16): return True
        m = bb & (bb >> 6)
        if m & (m >> 12): return True
        return False

    def evaluate(my, opp):
        score = 0
        for mask in _LINES:
            m = my & mask
            o = opp & mask
            if m:
                if not o:
                    cnt = _popcount(m)
                    if cnt == 3: score += 50
                    elif cnt == 2: score += 10
                    else: score += 1
            elif o:
                cnt = _popcount(o)
                if cnt == 3: score -= 50
                elif cnt == 2: score -= 10
                else: score -= 1
        return score

    nodes = [0]
    class TO(Exception): pass

    def negamax(my, opp, h, depth, alpha, beta):
        nodes[0] += 1
        if (nodes[0] & 4095) == 0 and time.time() > deadline:
            raise TO()

        total = _popcount(my | opp)
        win_score = 100000 - total
        for c in _COL_ORDER:
            if h[c] < 6:
                bit = 1 << (c*7 + h[c])
                if has_won(my | bit):
                    return win_score

        if depth == 0:
            return evaluate(my, opp)
        if total == 42:
            return 0

        best = -999999
        for c in _COL_ORDER:
            if h[c] >= 6:
                continue
            bit = 1 << (c*7 + h[c])
            new_my = my | bit
            h[c] += 1
            try:
                score = -negamax(opp, new_my, h, depth-1, -beta, -alpha)
            except TO:
                h[c] -= 1
                raise
            h[c] -= 1
            if score > best:
                best = score
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        break
        return best

    legal = [c for c in _COL_ORDER if heights[c] < 6]
    if not legal:
        return 0
    best_move = legal[0]

    for c in _COL_ORDER:
        if heights[c] < 6:
            bit = 1 << (c*7 + heights[c])
            if has_won(my_bb | bit):
                return c

    prev_best = best_move
    for depth in range(2, 43):
        if time.time() > deadline - 0.05:
            break
        try:
            order = [prev_best] + [c for c in _COL_ORDER if c != prev_best]
            best_score = -999999
            alpha = -999999
            beta = 999999
            cur_best = prev_best
            for c in order:
                if heights[c] >= 6:
                    continue
                bit = 1 << (c*7 + heights[c])
                new_my = my_bb | bit
                if has_won(new_my):
                    return c
                heights[c] += 1
                try:
                    score = -negamax(opp_bb, new_my, heights, depth-1, -beta, -alpha)
                except TO:
                    heights[c] -= 1
                    raise
                heights[c] -= 1
                if score > best_score:
                    best_score = score
                    cur_best = c
                    if score > alpha:
                        alpha = score
            best_move = cur_best
            prev_best = cur_best
            if best_score >= 90000:
                return best_move
        except TO:
            break

    return best_move
