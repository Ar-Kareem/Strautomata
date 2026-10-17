
import time

# ---------------- Bitboard constants ----------------
# Bit index for cell (col c, row r from bottom) = c*7 + r ; bit c*7+6 is a sentinel.
BOTTOM = 0
for _c in range(7):
    BOTTOM |= 1 << (_c * 7)
BOARD = BOTTOM * ((1 << 6) - 1)
COLMASK = [((1 << 6) - 1) << (c * 7) for c in range(7)]
COLWEIGHT = [1, 2, 3, 4, 3, 2, 1]
ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 100000
INF = 10 ** 9
TIME_BUDGET = 0.6

TT = {}
nodes = 0
deadline = 0.0


class Timeout(Exception):
    pass


def winning_pos(position, mask):
    """Bitmask of empty cells where `position` would complete a 4-line."""
    # vertical
    r = (position << 1) & (position << 2) & (position << 3)
    # horizontal (shift 7)
    p = (position << 7) & (position << 14)
    r |= p & (position << 21)
    r |= p & (position >> 7)
    p = (position >> 7) & (position >> 14)
    r |= p & (position << 7)
    r |= p & (position >> 21)
    # diagonal (shift 6)
    p = (position << 6) & (position << 12)
    r |= p & (position << 18)
    r |= p & (position >> 6)
    p = (position >> 6) & (position >> 12)
    r |= p & (position << 6)
    r |= p & (position >> 18)
    # diagonal (shift 8)
    p = (position << 8) & (position << 16)
    r |= p & (position << 24)
    r |= p & (position >> 8)
    p = (position >> 8) & (position >> 16)
    r |= p & (position << 8)
    r |= p & (position >> 24)
    return r & (BOARD ^ mask)


def popcount(x):
    return bin(x).count("1")


def evaluate(pos, opp, mw, ow):
    s = 40 * (popcount(mw) - popcount(ow))
    for c in (1, 2, 3, 4, 5):
        w = COLWEIGHT[c]
        s += w * (popcount(pos & COLMASK[c]) - popcount(opp & COLMASK[c]))
    return s


def ordered_moves(pos, mask, possible, ttmove, depth):
    moves = []
    for c in ORDER:
        bit = possible & COLMASK[c]
        if not bit:
            continue
        if c == ttmove:
            sc = 1000
        elif depth >= 2:
            sc = popcount(winning_pos(pos | bit, mask | bit)) * 10 + COLWEIGHT[c]
        else:
            sc = COLWEIGHT[c]
        moves.append((sc, c, bit))
    moves.sort(key=lambda t: -t[0])
    return moves


def negamax(pos, mask, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 2047) == 0 and time.time() > deadline:
        raise Timeout

    possible = (mask + BOTTOM) & BOARD
    if not possible:
        return 0
    opp = pos ^ mask
    mw = winning_pos(pos, mask)
    if mw & possible:
        return WIN - ply
    ow = winning_pos(opp, mask)
    forced = ow & possible
    if forced:
        if forced & (forced - 1):
            return -(WIN - ply - 1)
        possible = forced
    possible &= ~(ow >> 1)
    if not possible:
        return -(WIN - ply - 1)
    if depth <= 0:
        return evaluate(pos, opp, mw, ow)

    key = (pos, mask)
    ttmove = -1
    entry = TT.get(key)
    if entry is not None:
        edepth, eval_, eflag, emove = entry
        if edepth >= depth:
            if eflag == 0:
                return eval_
            elif eflag == 1:
                if eval_ > alpha:
                    alpha = eval_
            else:
                if eval_ < beta:
                    beta = eval_
            if alpha >= beta:
                return eval_
        ttmove = emove

    best = -INF
    bestmove = -1
    a = alpha
    for _sc, c, bit in ordered_moves(pos, mask, possible, ttmove, depth):
        val = -negamax(opp, mask | bit, depth - 1, -beta, -a, ply + 1)
        if val > best:
            best = val
            bestmove = c
        if best > a:
            a = best
        if a >= beta:
            break

    if best <= alpha:
        flag = 2  # upper bound
    elif best >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact
    TT[key] = (depth, best, flag, bestmove)
    return best


def policy(board):
    global TT, nodes, deadline
    start = time.time()
    deadline = start + TIME_BUDGET
    TT = {}
    nodes = 0

    legal = [c for c in range(7) if board[0][c] == 0]
    if not legal:
        return 0
    # default: most central legal column
    fallback = min(legal, key=lambda c: abs(c - 3))

    try:
        pos = 0
        mask = 0
        for r in range(6):
            row = board[r]
            for c in range(7):
                v = row[c]
                if v != 0:
                    bit = 1 << (c * 7 + (5 - r))
                    mask |= bit
                    if v == 1:
                        pos |= bit

        possible = (mask + BOTTOM) & BOARD
        if not possible:
            return fallback
        opp = pos ^ mask
        mw = winning_pos(pos, mask)
        if mw & possible:
            for c in ORDER:
                if mw & possible & COLMASK[c]:
                    return c
        ow = winning_pos(opp, mask)
        forced = ow & possible
        if forced:
            # must block (if several threats, we lose anyway; block one)
            for c in ORDER:
                if forced & COLMASK[c]:
                    return c
        safe = possible & ~(ow >> 1)
        if safe:
            possible = safe
        else:
            # every move gives opponent a win; pick center-most legal anyway
            return fallback

        cand = [c for c in ORDER if possible & COLMASK[c]]
        if len(cand) == 1:
            return cand[0]
        best_move = cand[0]

        # Iterative deepening
        order = list(cand)
        try:
            for depth in range(1, 43):
                scores = {}
                best_val = -INF
                cur_best = order[0]
                a = -INF
                for c in order:
                    bit = COLMASK[c] & possible
                    val = -negamax(opp, mask | bit, depth - 1, -INF, -a, 1)
                    scores[c] = val
                    if val > best_val:
                        best_val = val
                        cur_best = c
                    if val > a:
                        a = val
                best_move = cur_best
                order.sort(key=lambda c: -scores[c])
                if abs(best_val) >= WIN - 100:
                    break
                if time.time() - start > TIME_BUDGET * 0.5:
                    # Unlikely to finish another deeper iteration; stop early.
                    pass
        except Timeout:
            pass

        if board[0][best_move] == 0:
            return best_move
        return fallback
    except Exception:
        return fallback
