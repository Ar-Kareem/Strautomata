
import time

WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1
BOTTOM = 0
for _c in range(WIDTH):
    BOTTOM |= 1 << (_c * H1)
BOARD_MASK = BOTTOM * ((1 << HEIGHT) - 1)
COL_MASK = [((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH)]
TOP_MASK = [1 << (HEIGHT - 1 + c * H1) for c in range(WIDTH)]
ROW_MASK = [BOTTOM << r for r in range(HEIGHT)]
ODD_ROWS = ROW_MASK[0] | ROW_MASK[2] | ROW_MASK[4]
EVEN_ROWS = ROW_MASK[1] | ROW_MASK[3] | ROW_MASK[5]
CENTER_W = [1, 2, 3, 4, 3, 2, 1]
ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 1000000
INF = 10 ** 9
TIME_LIMIT = 0.72

try:
    (0).bit_count()

    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')


class Timeout(Exception):
    pass


TT = {}
NODES = 0
DEADLINE = 0.0


def winning(position, mask):
    # vertical
    r = (position << 1) & (position << 2) & (position << 3)
    # horizontal
    p = (position << H1) & (position << (2 * H1))
    r |= p & (position << (3 * H1))
    r |= p & (position >> H1)
    p = (position >> H1) & (position >> (2 * H1))
    r |= p & (position << H1)
    r |= p & (position >> (3 * H1))
    # diagonal 1
    p = (position << HEIGHT) & (position << (2 * HEIGHT))
    r |= p & (position << (3 * HEIGHT))
    r |= p & (position >> HEIGHT)
    p = (position >> HEIGHT) & (position >> (2 * HEIGHT))
    r |= p & (position << HEIGHT)
    r |= p & (position >> (3 * HEIGHT))
    # diagonal 2
    s = HEIGHT + 2
    p = (position << s) & (position << (2 * s))
    r |= p & (position << (3 * s))
    r |= p & (position >> s)
    p = (position >> s) & (position >> (2 * s))
    r |= p & (position << s)
    r |= p & (position >> (3 * s))
    return r & (BOARD_MASK ^ mask)


def evaluate(pos, opp, mask, my_win, opp_win):
    n = popcount(mask)
    if (n & 1) == 0:
        my_good, opp_good = ODD_ROWS, EVEN_ROWS
    else:
        my_good, opp_good = EVEN_ROWS, ODD_ROWS
    s = 8 * popcount(my_win) + 8 * popcount(my_win & my_good)
    s -= 8 * popcount(opp_win) + 8 * popcount(opp_win & opp_good)
    for c in range(WIDTH):
        cm = COL_MASK[c]
        s += CENTER_W[c] * (popcount(pos & cm) - popcount(opp & cm))
    return s


def negamax(pos, mask, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if not (NODES & 255):
        if time.perf_counter() > DEADLINE:
            raise Timeout()
    possible = (mask + BOTTOM) & BOARD_MASK
    my_win = winning(pos, mask)
    if my_win & possible:
        return WIN - ply
    if mask == BOARD_MASK:
        return 0
    opp = pos ^ mask
    opp_win = winning(opp, mask)
    forced = possible & opp_win
    if forced:
        if forced & (forced - 1):
            return -(WIN - ply - 1)
        moves = forced
    else:
        moves = possible & ~(opp_win >> 1)
        if not moves:
            return -(WIN - ply - 1)
    if depth <= 0:
        return evaluate(pos, opp, mask, my_win, opp_win)

    key = pos | (mask + BOTTOM)
    entry = TT.get(key)
    tt_move = 0
    if entry is not None:
        edepth, evalue, eflag, emove = entry
        if edepth >= depth:
            if eflag == 0:
                return evalue
            if eflag == 1:
                if evalue > alpha:
                    alpha = evalue
            else:
                if evalue < beta:
                    beta = evalue
            if alpha >= beta:
                return evalue
        tt_move = emove

    if not (moves & (moves - 1)):
        move_list = [moves]
    else:
        scored = []
        for c in ORDER:
            m = moves & COL_MASK[c]
            if m:
                if depth >= 3:
                    sc = 4 * popcount(winning(pos | m, mask | m)) + CENTER_W[c]
                else:
                    sc = CENTER_W[c]
                if m == tt_move:
                    sc += 1000
                scored.append((sc, m))
        scored.sort(key=lambda t: t[0], reverse=True)
        move_list = [m for _, m in scored]

    orig_alpha = alpha
    best = -INF
    best_move = 0
    for m in move_list:
        v = -negamax(opp, mask | m, depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            best_move = m
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, best_move)
    return best


def root_search(pos, mask, depth, first_col):
    possible = (mask + BOTTOM) & BOARD_MASK
    opp = pos ^ mask
    opp_win = winning(opp, mask)
    moves = possible & ~(opp_win >> 1)
    if not moves:
        moves = possible
    cols = [c for c in ORDER if moves & COL_MASK[c]]
    if first_col in cols:
        cols.remove(first_col)
        cols.insert(0, first_col)
    alpha = -INF
    beta = INF
    best_col = cols[0]
    for c in cols:
        m = moves & COL_MASK[c]
        v = -negamax(opp, mask | m, depth - 1, -beta, -alpha, 1)
        if v > alpha:
            alpha = v
            best_col = c
    return alpha, best_col


def bit_to_col(b):
    return (b.bit_length() - 1) // H1


def policy(board):
    global TT, NODES, DEADLINE
    start = time.perf_counter()
    DEADLINE = start + TIME_LIMIT
    # legal fallback first
    legal = [c for c in ORDER if board[0][c] == 0]
    if not legal:
        return 0
    fallback = legal[0]
    try:
        pos = 0
        mask = 0
        for r in range(HEIGHT):
            rb = HEIGHT - 1 - r
            row = board[r]
            for c in range(WIDTH):
                v = row[c]
                if v != 0:
                    b = 1 << (c * H1 + rb)
                    mask |= b
                    if v == 1:
                        pos |= b
        possible = (mask + BOTTOM) & BOARD_MASK
        my_win = winning(pos, mask) & possible
        if my_win:
            c = bit_to_col(my_win & -my_win)
            if c in legal:
                return c
        opp = pos ^ mask
        opp_win = winning(opp, mask)
        forced = opp_win & possible
        if forced:
            c = bit_to_col(forced & -forced)
            if c in legal:
                return c
        # prefer safe fallback
        safe = possible & ~(opp_win >> 1)
        if safe:
            for c in ORDER:
                if safe & COL_MASK[c]:
                    fallback = c
                    break
        TT = {}
        NODES = 0
        best_col = fallback
        try:
            for depth in range(1, 43):
                val, col = root_search(pos, mask, depth, best_col)
                best_col = col
                if abs(val) >= WIN - 100:
                    break
        except Timeout:
            pass
        if best_col in legal:
            return best_col
        return fallback
    except Exception:
        return fallback
