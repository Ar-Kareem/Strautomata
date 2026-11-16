
import time

WIDTH, HEIGHT = 7, 6
H1 = HEIGHT + 1
COL_MASK = [((1 << HEIGHT) - 1) << (H1 * c) for c in range(WIDTH)]
BOTTOM = sum(1 << (H1 * c) for c in range(WIDTH))
BOARD_MASK = BOTTOM * ((1 << HEIGHT) - 1)
ROW_MASK = [sum(1 << (H1 * c + r) for c in range(WIDTH)) for r in range(HEIGHT)]
ODD_ROWS = ROW_MASK[0] | ROW_MASK[2] | ROW_MASK[4]
EVEN_ROWS = ROW_MASK[1] | ROW_MASK[3] | ROW_MASK[5]
CENTER = COL_MASK[3]
ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 100000
TIME_LIMIT = 0.8

TT = {}
nodes = 0
deadline = 0.0
MY_GOOD = ODD_ROWS
OPP_GOOD = EVEN_ROWS


class Timeout(Exception):
    pass


try:
    (0).bit_count()
    def pc(x):
        return x.bit_count()
except AttributeError:
    def pc(x):
        return bin(x).count('1')


def winning_positions(pos, mask):
    r = (pos << 1) & (pos << 2) & (pos << 3)
    for s in (7, 6, 8):
        p = (pos << s) & (pos << (2 * s))
        r |= p & (pos << (3 * s))
        r |= p & (pos >> s)
        p = (pos >> s) & (pos >> (2 * s))
        r |= p & (pos << s)
        r |= p & (pos >> (3 * s))
    return r & (BOARD_MASK ^ mask)


def evaluate(pos, mask, ply):
    opp = pos ^ mask
    pw = winning_positions(pos, mask)
    ow = winning_positions(opp, mask)
    if ply % 2 == 0:
        pg, og = MY_GOOD, OPP_GOOD
    else:
        pg, og = OPP_GOOD, MY_GOOD
    s = 3 * (pc(pw) - pc(ow))
    s += 2 * (pc(pw & pg) - pc(ow & og))
    s += pc(pos & CENTER) - pc(opp & CENTER)
    return s


def negamax(pos, mask, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.perf_counter() > deadline:
        raise Timeout()
    possible = (mask + BOTTOM) & BOARD_MASK
    if possible == 0:
        return 0
    if winning_positions(pos, mask) & possible:
        return WIN - ply
    opp = pos ^ mask
    ow = winning_positions(opp, mask)
    forced = ow & possible
    if forced:
        if forced & (forced - 1):
            return -(WIN - ply - 1)
        possible = forced
    possible &= ~(ow >> 1)
    if possible == 0:
        return -(WIN - ply - 1)
    if depth <= 0:
        return evaluate(pos, mask, ply)
    key = (pos, mask)
    entry = TT.get(key)
    tt_move = -1
    if entry is not None:
        edepth, flag, val, tt_move = entry
        if edepth >= depth:
            if flag == 0:
                return val
            if flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
    a0 = alpha
    best = -10 * WIN
    best_col = -1
    if tt_move >= 0:
        cols = [tt_move] + [c for c in ORDER if c != tt_move]
    else:
        cols = ORDER
    for col in cols:
        cell = possible & COL_MASK[col]
        if not cell:
            continue
        v = -negamax(opp, mask | cell, depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            best_col = col
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best <= a0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, flag, best, best_col)
    return best


def root_search(pos, mask, possible, depth, first_col):
    opp = pos ^ mask
    cols = [first_col] + [c for c in ORDER if c != first_col] if first_col >= 0 else ORDER
    alpha = -10 * WIN
    beta = 10 * WIN
    best = -10 * WIN
    best_col = -1
    for col in cols:
        cell = possible & COL_MASK[col]
        if not cell:
            continue
        v = -negamax(opp, mask | cell, depth - 1, -beta, -alpha, 1)
        if v > best:
            best = v
            best_col = col
        if v > alpha:
            alpha = v
    return best, best_col


def policy(board):
    global TT, nodes, deadline, MY_GOOD, OPP_GOOD
    start = time.perf_counter()
    legal = [c for c in ORDER if board[0][c] == 0]
    if not legal:
        return 3
    fallback = legal[0]
    try:
        pos = 0
        mask = 0
        for r in range(6):
            for c in range(7):
                v = board[r][c]
                if v != 0:
                    bit = 1 << (H1 * c + (5 - r))
                    mask |= bit
                    if v == 1:
                        pos |= bit
        stones = pc(mask)
        if stones % 2 == 0:
            MY_GOOD, OPP_GOOD = ODD_ROWS, EVEN_ROWS
        else:
            MY_GOOD, OPP_GOOD = EVEN_ROWS, ODD_ROWS

        possible = (mask + BOTTOM) & BOARD_MASK
        mywin = winning_positions(pos, mask) & possible
        if mywin:
            for c in ORDER:
                if mywin & COL_MASK[c]:
                    return c
        opp = pos ^ mask
        ow = winning_positions(opp, mask)
        forced = ow & possible
        if forced:
            for c in ORDER:
                if forced & COL_MASK[c]:
                    return c
        safe = possible & ~(ow >> 1)
        if safe == 0:
            return fallback
        safe_cols = [c for c in ORDER if safe & COL_MASK[c]]
        if len(safe_cols) == 1:
            return safe_cols[0]
        fallback = safe_cols[0]

        TT = {}
        nodes = 0
        deadline = start + TIME_LIMIT
        best_col = fallback
        for depth in range(1, 43):
            try:
                score, col = root_search(pos, mask, safe, depth, best_col)
            except Timeout:
                break
            if col >= 0:
                best_col = col
            if abs(score) >= WIN - 100:
                break
            if time.perf_counter() - start > TIME_LIMIT * 0.5:
                break
        if board[0][best_col] != 0:
            return fallback
        return best_col
    except Exception:
        return fallback
