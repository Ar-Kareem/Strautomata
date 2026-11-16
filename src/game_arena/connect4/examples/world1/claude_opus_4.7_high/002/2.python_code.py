
import time

# Precompute all 69 four-in-a-row windows as bitboard masks
WINDOWS = []
for c in range(7):
    for r in range(6):
        if r <= 2:
            bb = 0
            for i in range(4):
                bb |= 1 << (c*7 + r+i)
            WINDOWS.append(bb)
        if c <= 3:
            bb = 0
            for i in range(4):
                bb |= 1 << ((c+i)*7 + r)
            WINDOWS.append(bb)
        if c <= 3 and r <= 2:
            bb = 0
            for i in range(4):
                bb |= 1 << ((c+i)*7 + r+i)
            WINDOWS.append(bb)
        if c <= 3 and r >= 3:
            bb = 0
            for i in range(4):
                bb |= 1 << ((c+i)*7 + r-i)
            WINDOWS.append(bb)

def popcount(x):
    return bin(x).count('1')

def is_win(bb):
    m = bb & (bb >> 7)
    if m & (m >> 14): return True
    m = bb & (bb >> 6)
    if m & (m >> 12): return True
    m = bb & (bb >> 8)
    if m & (m >> 16): return True
    m = bb & (bb >> 1)
    if m & (m >> 2): return True
    return False

def heuristic(my, op):
    score = 0
    for w in WINDOWS:
        mw = my & w
        ow = op & w
        if mw and ow:
            continue
        if mw:
            c = popcount(mw)
            if c == 3: score += 50
            elif c == 2: score += 10
            else: score += 1
        elif ow:
            c = popcount(ow)
            if c == 3: score -= 50
            elif c == 2: score -= 10
            else: score -= 1
    return score

ORDER = (3, 2, 4, 1, 5, 0, 6)

class TimeOut(Exception):
    pass

def negamax(my, op, heights, alpha, beta, depth, deadline):
    if time.time() > deadline:
        raise TimeOut()

    for c in ORDER:
        h = heights[c]
        if h < 6:
            bit = 1 << (c*7 + h)
            if is_win(my | bit):
                return 10000 + depth

    if depth == 0:
        return heuristic(my, op)

    best = -1000000
    any_move = False
    for c in ORDER:
        h = heights[c]
        if h >= 6:
            continue
        any_move = True
        bit = 1 << (c*7 + h)
        heights[c] = h + 1
        val = -negamax(op, my | bit, heights, -beta, -alpha, depth-1, deadline)
        heights[c] = h
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if not any_move:
        return 0
    return best

def policy(board):
    start = time.time()
    deadline = start + 0.85

    my_bb = 0
    op_bb = 0
    heights = [0]*7
    for c in range(7):
        count = 0
        for r in range(5, -1, -1):
            v = board[r][c]
            if v == 0:
                break
            bit = 1 << (c*7 + count)
            if v == 1:
                my_bb |= bit
            elif v == -1:
                op_bb |= bit
            count += 1
        heights[c] = count

    default = 3
    for c in ORDER:
        if heights[c] < 6:
            default = c
            break

    # Immediate winning move
    for c in ORDER:
        if heights[c] < 6:
            bit = 1 << (c*7 + heights[c])
            if is_win(my_bb | bit):
                return c

    # Block opponent's immediate win
    opp_wins = []
    for c in range(7):
        if heights[c] < 6:
            bit = 1 << (c*7 + heights[c])
            if is_win(op_bb | bit):
                opp_wins.append(c)
    if len(opp_wins) >= 1:
        return opp_wins[0]

    best_move = default

    # Iterative deepening
    for depth in range(2, 20):
        try:
            cur_best = -1000000
            cur_move = best_move
            alpha = -1000000
            beta = 1000000
            move_order = [best_move] + [c for c in ORDER if c != best_move]
            for c in move_order:
                h = heights[c]
                if h >= 6:
                    continue
                bit = 1 << (c*7 + h)
                heights[c] = h + 1
                val = -negamax(op_bb, my_bb | bit, heights, -beta, -alpha, depth-1, deadline)
                heights[c] = h
                if val > cur_best:
                    cur_best = val
                    cur_move = c
                if cur_best > alpha:
                    alpha = cur_best
            best_move = cur_move
            if cur_best >= 9000:
                break
        except TimeOut:
            break

    if heights[best_move] >= 6:
        for c in ORDER:
            if heights[c] < 6:
                return c
    return best_move
